import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import main


class RendererStatusTests(unittest.TestCase):
    def test_unrelated_opengl_process_cannot_mark_current_game_loaded(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            vk64 = root / 'native64/libMangoHud.so'
            vk32 = root / 'native32/libMangoHud.so'
            gl = root / 'native64/libMangoHud_opengl.so'
            proc = root / 'proc'
            proc.mkdir()

            def process(pid, appid, elfclass, library=None):
                folder = proc / str(pid)
                folder.mkdir()
                (folder / 'environ').write_bytes(b'SteamAppId=' + appid.encode() + b'\0')
                (folder / 'exe').write_bytes(b'\x7fELF' + bytes([elfclass]))
                (folder / 'maps').write_text(f'1-2 r-xp 0 00:01 1 {library}\n' if library else '')
                return folder

            game = process(101, '667720', 1)
            process(102, '999', 2, gl)
            with patch.object(main, 'experimental_library', return_value=vk64), \
                 patch.object(main, 'vulkan32_library', return_value=vk32), \
                 patch.object(main, 'opengl_library', return_value=gl):
                status = main.renderer_status('667720', proc)
                self.assertFalse(status['native_loaded'])
                self.assertEqual(status['opengl_processes'], 0)
                self.assertEqual(status['processes_seen'], 1)
                self.assertEqual(status['processes_32bit'], 1)
                self.assertIn('no 32-bit Vulkan renderer', status['reason'])
                vk32.parent.mkdir()
                vk32.touch()
                (game / 'maps').write_text(f'1-2 r-xp 0 00:01 1 {vk32}\n')
                status = main.renderer_status('667720', proc)
                self.assertTrue(status['native_loaded'])
                self.assertEqual(status['native_processes'], 1)
                self.assertIn('drawing is not verified', status['reason'])
                self.assertFalse(main.renderer_status(None, proc)['native_loaded'])

    def test_both_vulkan_manifests_select_the_matching_architecture(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            library32 = home / 'native32/libMangoHud.so'
            library32.parent.mkdir()
            library32.write_bytes(b'\x7fELF\x01' + bytes(110000))
            with patch.object(main, 'BASE', home / 'config'), \
                 patch.object(main, 'user_home', return_value=home), \
                 patch.object(main, 'vulkan32_library', return_value=library32), \
                 patch.object(main, 'native_renderer_available', return_value=True):
                main.install_native_manifest()
                manifest64 = json.loads(main.experimental_manifest().read_text())
                manifest32_path = main.experimental_manifest().with_name('ClawMetrics.x86.json')
                manifest32 = json.loads(manifest32_path.read_text())
                self.assertEqual(manifest64['layer']['name'], manifest32['layer']['name'])
                self.assertEqual(manifest64['layer']['library_arch'], '64')
                self.assertEqual(manifest32['layer']['library_arch'], '32')
                self.assertEqual(manifest32['layer']['library_path'], str(library32))
                library32.unlink()
                main.install_native_manifest()
                self.assertFalse(manifest32_path.exists())
