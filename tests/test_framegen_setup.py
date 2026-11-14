import asyncio
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import framegen_setup as setup
import main


class FrameGenSetupTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="Claw's Steam ")
        self.addCleanup(temp.cleanup)
        self.home = Path(temp.name)
        primary = self.home / '.local/share/Steam/steamapps'
        primary.mkdir(parents=True)
        library = self.home / 'SD card'
        (primary / 'libraryfolders.vdf').write_text(
            f'"libraryfolders" {{ "1" {{ "path" "{library}" "apps" {{ "{setup.APP_ID}" "1" }} }} }}')
        apps = library / 'steamapps'
        self.folder = apps / 'common/Expedition 33/Sandfall/Binaries/Win64'
        self.folder.mkdir(parents=True)
        (self.folder / setup.GAME_EXE).touch()
        self.manifest = apps / f'appmanifest_{setup.APP_ID}.acf'
        self.manifest.write_text(f'"AppState" {{ "appid" "{setup.APP_ID}" "installdir" "Expedition 33" }}')
        self.original = self.folder / setup.DLL
        self.original.write_bytes(b'MZ original AMD DLL')
        self.backup = self.folder / setup.BACKUP
        self.adapter = self.home / 'adapter.dll'
        self.adapter.write_bytes(b'MZ current adapter')
        stopper = patch.object(setup, 'game_running', return_value=False)
        self.running = stopper.start()
        self.addCleanup(stopper.stop)

    def test_enable_roll_back_and_capture_steam_update(self):
        self.assertEqual(setup.find_game(self.home), self.folder)
        self.assertEqual(setup.game_bridge(self.folder, self.adapter, 'status'), 'ready')
        self.assertEqual(setup.game_bridge(self.folder, self.adapter, 'enable'), 'enabled')
        self.assertEqual(self.original.read_bytes(), self.adapter.read_bytes())
        self.assertEqual(self.backup.read_bytes(), b'MZ original AMD DLL')
        setup.game_bridge(self.folder, self.adapter, 'enable')
        self.original.unlink()  # Steam atomically replaces game files.
        self.original.write_bytes(b'MZ updated AMD DLL')
        self.assertEqual(setup.game_bridge(self.folder, self.adapter, 'status'), 'update')
        setup.game_bridge(self.folder, self.adapter, 'enable')
        setup.game_bridge(self.folder, self.adapter, 'disable')
        self.assertEqual(self.original.read_bytes(), b'MZ updated AMD DLL')
        self.assertFalse(self.backup.exists())

    def test_refuses_running_game_symlink_and_invalid_manifest(self):
        self.running.return_value = True
        with self.assertRaisesRegex(ValueError, 'Close Clair Obscur'):
            setup.game_bridge(self.folder, self.adapter, 'enable')
        self.assertFalse(self.backup.exists())
        self.running.return_value = False
        self.original.unlink()
        self.original.symlink_to(self.adapter)
        with self.assertRaisesRegex(ValueError, 'regular file'):
            setup.game_bridge(self.folder, self.adapter, 'enable')
        self.manifest.write_text(f'"AppState" {{ "appid" "{setup.APP_ID}" "installdir" "../Expedition 33" }}')
        with self.assertRaisesRegex(ValueError, 'not found'):
            setup.find_game(self.home)

    def test_adopts_rc1_install_and_keeps_original_if_activation_fails(self):
        self.backup.write_bytes(self.original.read_bytes())
        self.original.write_bytes(b'MZ prior proxy')
        with patch.object(setup, 'RC1_PROXY_SHA256', setup.dll_digest(self.original)):
            with patch.object(setup.os, 'replace', side_effect=OSError('read-only')):
                with self.assertRaisesRegex(OSError, 'read-only'):
                    setup.game_bridge(self.folder, self.adapter, 'enable')
            self.assertEqual(self.original.read_bytes(), b'MZ prior proxy')
            setup.game_bridge(self.folder, self.adapter, 'enable')
        setup.game_bridge(self.folder, self.adapter, 'disable')
        self.assertEqual(self.original.read_bytes(), b'MZ original AMD DLL')

    def test_decky_action_and_existing_launch_command_create_relay_only_for_clair_obscur(self):
        plugin = main.Plugin()
        with patch.object(main, 'BASE', self.home / 'config'), \
             patch.object(main, 'user_home', return_value=self.home), \
             patch.object(main, 'experimental_library', return_value=self.adapter), \
             patch.object(main, 'framegen_adapter', return_value=self.adapter), \
             patch.object(main, 'opengl_library', return_value=self.home / 'missing'):
            main.experimental_manifest().parent.mkdir(parents=True)
            main.experimental_manifest().touch()
            main.native_hud_path().touch()
            launcher = main.short_launcher_path()
            launcher.write_text(main.short_launcher_script())
            launcher.chmod(0o755)
            self.assertEqual(asyncio.run(plugin.get_framegen_status())['state'], 'ready')
            self.assertEqual(asyncio.run(plugin.set_framegen_enabled(True))['state'], 'enabled')
            probe = ("import os,pathlib; relay=os.getenv('CLAW_FRAMEGEN_FILE'); "
                     "print(relay or 'off'); assert not relay or pathlib.Path(relay).stat().st_size==6160")
            env = {'PATH': '/usr/bin:/bin', 'HOME': str(self.home), 'SteamAppId': setup.APP_ID}
            cmd = [str(launcher), sys.executable, '-c', probe]
            relay = Path(subprocess.check_output(cmd, env=env, text=True).strip())
            self.assertEqual(relay.parent, self.home / '.cache/claw-framegen')
            self.assertFalse(relay.exists())
            with_other_app = {**env, 'SteamAppId': '999'}
            self.assertEqual(subprocess.check_output(cmd, env=with_other_app, text=True).strip(), 'off')
            self.assertEqual(asyncio.run(plugin.set_framegen_enabled(False))['state'], 'ready')
            self.assertEqual(subprocess.check_output(cmd, env=env, text=True).strip(), 'off')
