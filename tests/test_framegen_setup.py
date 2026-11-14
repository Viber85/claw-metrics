import asyncio
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import framegen_setup as setup
import main


STEAM_ID = '314159'
SHORTCUT_ID = '4026531851'
WRAPPER_ID = '4026531852'


def amd_dll(marker, exports=setup.REQUIRED_EXPORTS, machine=0x8664):
    """Minimal PE64 export table for testing install/restore with distinct files."""
    data = bytearray(1024)
    data[:2] = b'MZ'
    struct.pack_into('<I', data, 60, 128)
    data[128:132] = b'PE\0\0'
    struct.pack_into('<HH', data, 132, machine, 1)
    struct.pack_into('<HH', data, 148, 240, 0x2000)
    struct.pack_into('<H', data, 152, 0x20b)
    struct.pack_into('<II', data, 264, 0x1000, 40)
    struct.pack_into('<IIII', data, 400, 512, 0x1000, 512, 512)
    struct.pack_into('<I', data, 536, len(exports))
    struct.pack_into('<I', data, 544, 0x1040)
    offset = 0x1080
    for index, name in enumerate(sorted(exports)):
        struct.pack_into('<I', data, 576 + index * 4, offset)
        start = 512 + offset - 0x1000
        data[start:start + len(name)] = name
        offset += len(name) + 1
    return bytes(data) + marker


def shortcut_record(index, appid, name, exe):
    return (b'\0' + str(index).encode() + b'\0\x02appid\0' + struct.pack('<I', int(appid))
            + b'\x01AppName\0' + name.encode() + b'\0\x01Exe\0' + f'"{exe}"'.encode()
            + b'\0\x00tags\0\x08\x08')


class FrameGenSetupTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="Claw's Steam ")
        self.addCleanup(temp.cleanup)
        self.home = Path(temp.name)
        root = self.home / '.local/share/Steam'
        primary = root / 'steamapps'
        primary.mkdir(parents=True)
        library = self.home / 'SD card'
        (primary / 'libraryfolders.vdf').write_text(
            f'"libraryfolders" {{ "1" {{ "path" "{library}" "apps" {{ "{STEAM_ID}" "1" }} }} }}')
        apps = library / 'steamapps'
        self.folder = apps / 'common/Example Game/Game/Binaries/Win64'
        self.folder.mkdir(parents=True)
        (self.folder / 'Example.exe').touch()
        self.manifest = apps / f'appmanifest_{STEAM_ID}.acf'
        self.manifest.write_text(f'"AppState" {{ "appid" "{STEAM_ID}" "installdir" "Example Game" }}')
        self.original = self.folder / setup.DLL
        self.original_dll = amd_dll(b'original AMD DLL')
        self.original.write_bytes(self.original_dll)
        self.backup = self.folder / setup.BACKUP
        self.adapter = self.home / 'adapter.dll'
        self.adapter.write_bytes(amd_dll(b'current adapter'))
        self.shortcut_root = self.home / 'Other game'
        self.shortcut_folder = self.shortcut_root / 'Data/Win64'
        self.shortcut_folder.mkdir(parents=True)
        shortcut_exe = self.shortcut_root / 'Other Game.exe'
        shortcut_exe.touch()
        (self.shortcut_folder / setup.DLL).write_bytes(self.original_dll)
        config = root / 'userdata/128/config'
        config.mkdir(parents=True)
        (config / 'shortcuts.vdf').write_bytes(
            b'\0shortcuts\0' + shortcut_record(0, SHORTCUT_ID, 'Other Game', shortcut_exe)
            + shortcut_record(1, WRAPPER_ID, 'Game from a launcher', '/usr/bin/flatpak') + b'\x08\x08')
        stopper = patch.object(setup, 'game_running', return_value=False)
        self.running = stopper.start()
        self.addCleanup(stopper.stop)

    def test_discovers_steam_library_and_multiple_kinds_of_shortcuts(self):
        games = {game.appid: game for game in setup.discover_games(self.home)}
        self.assertEqual(set(games), {STEAM_ID, SHORTCUT_ID, WRAPPER_ID})
        self.assertEqual(setup.find_dll_folder(games[STEAM_ID].path, True, self.home), self.folder)
        self.assertEqual(setup.find_dll_folder(games[SHORTCUT_ID].path, True, self.home), self.shortcut_folder)
        self.assertEqual(games[SHORTCUT_ID].source, 'Non-Steam')
        self.assertIsNone(games[WRAPPER_ID].path)
        self.manifest.write_text(f'"AppState" {{ "appid" "{STEAM_ID}" "installdir" "../Example Game" }}')
        self.assertNotIn(STEAM_ID, {game.appid for game in setup.discover_games(self.home)})

    def test_enable_roll_back_and_capture_game_update(self):
        self.assertEqual(setup.game_bridge(self.folder, self.adapter, 'status', STEAM_ID), 'ready')
        self.assertEqual(setup.game_bridge(self.folder, self.adapter, 'enable', STEAM_ID), 'enabled')
        self.assertEqual(self.original.read_bytes(), self.adapter.read_bytes())
        self.assertEqual(self.backup.read_bytes(), self.original_dll)
        setup.game_bridge(self.folder, self.adapter, 'enable', STEAM_ID)
        updated_dll = amd_dll(b'updated AMD DLL')
        self.original.unlink()  # Steam atomically replaces game files.
        self.original.write_bytes(updated_dll)
        self.assertEqual(setup.game_bridge(self.folder, self.adapter, 'status', STEAM_ID), 'update')
        setup.game_bridge(self.folder, self.adapter, 'enable', STEAM_ID)
        setup.game_bridge(self.folder, self.adapter, 'disable', STEAM_ID)
        self.assertEqual(self.original.read_bytes(), updated_dll)
        self.assertFalse(self.backup.exists())

    def test_refuses_running_game_symlink_and_incompatible_dll(self):
        self.running.return_value = True
        with self.assertRaisesRegex(ValueError, 'Close the game'):
            setup.game_bridge(self.folder, self.adapter, 'enable', STEAM_ID)
        self.assertFalse(self.backup.exists())
        self.running.return_value = False
        for incompatible in (amd_dll(b'x86', machine=0x14c), amd_dll(b'missing exports', {b'ffxConfigure'})):
            with self.subTest(incompatible=incompatible[-16:]):
                self.original.write_bytes(incompatible)
                with self.assertRaisesRegex(ValueError, 'supported AMD DX12'):
                    setup.game_bridge(self.folder, self.adapter, 'enable', STEAM_ID)
                self.assertFalse(self.backup.exists())
        self.original.unlink()
        self.original.symlink_to(self.adapter)
        with self.assertRaisesRegex(ValueError, 'regular file'):
            setup.game_bridge(self.folder, self.adapter, 'enable', STEAM_ID)

    def test_adopts_prior_install_and_keeps_original_if_activation_fails(self):
        self.backup.write_bytes(self.original_dll)
        prior_dll = amd_dll(b'prior proxy')
        self.original.write_bytes(prior_dll)
        with patch.object(setup, 'PREVIOUS_PROXIES', {setup.dll_digest(self.original)}):
            with patch.object(setup.os, 'replace', side_effect=OSError('read-only')):
                with self.assertRaisesRegex(OSError, 'read-only'):
                    setup.game_bridge(self.folder, self.adapter, 'enable', STEAM_ID)
            self.assertEqual(self.original.read_bytes(), prior_dll)
            setup.game_bridge(self.folder, self.adapter, 'enable', STEAM_ID)
        setup.game_bridge(self.folder, self.adapter, 'disable', STEAM_ID)
        self.assertEqual(self.original.read_bytes(), self.original_dll)

    def test_decky_activation_and_original_launcher_are_per_game(self):
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
            listed = asyncio.run(plugin.list_framegen_games())['games']
            self.assertEqual({game['appid'] for game in listed}, {STEAM_ID, SHORTCUT_ID, WRAPPER_ID})
            self.assertEqual(asyncio.run(plugin.get_framegen_status(STEAM_ID))['state'], 'ready')
            self.assertEqual(asyncio.run(plugin.get_framegen_status(SHORTCUT_ID))['state'], 'ready')
            self.assertEqual(asyncio.run(plugin.get_framegen_status(WRAPPER_ID))['state'], 'unavailable')
            self.assertEqual(asyncio.run(plugin.set_framegen_enabled(True, STEAM_ID))['state'], 'enabled')
            self.assertEqual(asyncio.run(plugin.set_framegen_enabled(True, SHORTCUT_ID))['state'], 'enabled')
            self.assertEqual(asyncio.run(plugin.get_framegen_status(WRAPPER_ID, str(self.shortcut_folder / setup.DLL)))
                             ['state'], 'setup')

            probe = ("import os,pathlib; relay=os.getenv('CLAW_FRAMEGEN_FILE'); "
                     "print(relay or 'off'); assert not relay or pathlib.Path(relay).stat().st_size==6160")
            env = {'PATH': '/usr/bin:/bin', 'HOME': str(self.home)}
            cmd = [str(launcher), sys.executable, '-c', probe]

            def run(k, appid):
                return subprocess.check_output(cmd, env={**env, k: appid}, text=True).strip()

            steam_launch = Path(run('SteamAppId', STEAM_ID))
            self.assertEqual(steam_launch.parent, self.home / '.cache/claw-framegen')
            self.assertFalse(steam_launch.exists())
            for key, appid in zip(('SteamAppId', 'STEAM_COMPAT_APP_ID', 'SteamGameId'), setup.launch_ids(SHORTCUT_ID)):
                self.assertEqual(Path(run(key, appid)).parent, steam_launch.parent)
            self.assertEqual(run('SteamAppId', '999'), 'off')
            self.assertEqual(asyncio.run(plugin.set_framegen_enabled(False, STEAM_ID))['state'], 'ready')
            self.assertEqual(run('SteamAppId', STEAM_ID), 'off')
            self.assertNotEqual(run('SteamAppId', SHORTCUT_ID), 'off')
            self.assertEqual(asyncio.run(plugin.set_framegen_enabled(False, SHORTCUT_ID))['state'], 'ready')
            self.assertEqual(run('SteamAppId', SHORTCUT_ID), 'off')

            dll = str(self.shortcut_folder / setup.DLL)
            self.assertEqual(asyncio.run(plugin.set_framegen_enabled(True, WRAPPER_ID, dll))['state'], 'enabled')
            self.assertNotEqual(run('SteamAppId', WRAPPER_ID), 'off')
            self.assertEqual(asyncio.run(plugin.set_framegen_enabled(False, WRAPPER_ID))['state'], 'ready')
            self.assertEqual(run('SteamAppId', WRAPPER_ID), 'off')
