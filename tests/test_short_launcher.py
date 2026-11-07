"""Short launcher compatibility tests: no SteamOS or real game needed."""
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import main


class ShortLauncherTests(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.TemporaryDirectory(prefix="legion-user-")
        self.addCleanup(self.home.cleanup)
        patcher = patch.object(main, "user_home", return_value=Path(self.home.name))
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_short_launcher_execs_unmodified_args_and_environment(self):
        # Paths deliberately contain both whitespace and a single quote.
        with tempfile.TemporaryDirectory(prefix="Claw's test ") as folder:
            base = Path(folder) / "my config"
            binary = Path(folder) / "libMangoHud.so"
            binary.write_bytes(b"x" * 110001)
            with patch.object(main, "BASE", base), \
                 patch.object(main, "experimental_library", return_value=binary):
                self.assertTrue(main.native_renderer_available())
                main.experimental_manifest().parent.mkdir(parents=True, exist_ok=True)
                main.write_atomic(main.experimental_manifest(), "{}")
                main.write_atomic(main.native_hud_path(), "fps=1\n")
                main.install_short_launcher()
                launcher = main.short_launcher_path()
                self.assertTrue(main.short_launcher_ready())
                self.assertTrue(main.home_launcher_ready())
                self.assertEqual(main.short_launch_option(), '~/claw-metrics %command%')
                self.assertEqual(stat.S_IMODE(launcher.stat().st_mode), 0o755)
                with patch.object(main.os, "replace", wraps=os.replace) as replace_call:
                    main.install_short_launcher()
                    replace_call.assert_not_called()
                self.assertTrue(launcher.read_bytes().startswith(b"#!/bin/sh\n"))
                self.assertIn('exec "$@"', launcher.read_text())
                probe = ("import json,os,sys;"
                         "print(json.dumps({'args':sys.argv[1:],"
                         "'layer':os.environ.get('VK_INSTANCE_LAYERS'),"
                         "'path':os.environ.get('VK_ADD_LAYER_PATH'),"
                         "'disabled':os.environ.get('DISABLE_MANGOHUD'),"
                         "'config':os.environ.get('MANGOHUD_CONFIGFILE')}))")
                result = subprocess.run(
                    [str(main.home_launcher_path()), sys.executable, "-c", probe, "hello world", "it's ok", "$(not-executed)"],
                    capture_output=True, text=True, check=True, env={**os.environ, "VK_INSTANCE_LAYERS": "old"}
                )
                payload = json.loads(result.stdout)
                self.assertEqual(payload["args"], ["hello world", "it's ok", "$(not-executed)"])
                self.assertEqual(payload["layer"], main.EXPERIMENTAL_LAYER_NAME)
                self.assertEqual(payload["path"], str(main.experimental_manifest().parent))
                self.assertEqual(payload["disabled"], "1")
                self.assertEqual(payload["config"], str(main.native_hud_path()))
                exit_status = subprocess.run(
                    [str(launcher), sys.executable, "-c", "import sys;sys.exit(17)"],
                    capture_output=True, text=True
                )
                self.assertEqual(exit_status.returncode, 17)
                # An accidental change or loss of executable permission is detectable.
                launcher.chmod(0o644)
                self.assertFalse(main.short_launcher_ready())
                main.install_short_launcher()
                self.assertTrue(main.short_launcher_ready())
                launcher.write_text("corrupted")
                self.assertFalse(main.short_launcher_ready())
                main.install_short_launcher()
                self.assertTrue(main.short_launcher_ready())
                binary.unlink()
                fallback_env = {**os.environ}
                for key in ("VK_INSTANCE_LAYERS", "VK_ADD_LAYER_PATH",
                            "DISABLE_MANGOHUD", "MANGOHUD_CONFIGFILE"):
                    fallback_env.pop(key, None)
                fallback_result = subprocess.run(
                    [str(launcher), sys.executable, "-c", probe, "fallback"],
                    capture_output=True, text=True, check=True, env=fallback_env,
                )
                fallback = json.loads(fallback_result.stdout)
                self.assertEqual(fallback["args"], ["fallback"])
                for key in ("layer", "path", "disabled", "config"):
                    self.assertIsNone(fallback[key])
                self.assertIn("missing renderer assets", fallback_result.stderr)
                self.assertFalse(main.short_launcher_ready())

    def test_one_launcher_adds_opengl_shim_without_losing_vulkan_or_existing_preloads(self):
        with tempfile.TemporaryDirectory(prefix="Claw's GL test ") as folder:
            base = Path(folder)
            binary = base / "libMangoHud.so"
            binary.write_bytes(b"x" * 110001)
            gl = base / "libMangoHud_opengl.so"
            shim = base / "libMangoHud_shim.so"
            gl.write_bytes(b"x" * 110001)
            shim.write_bytes(b"x" * 11001)
            with patch.object(main, "BASE", base), \
                 patch.object(main, "experimental_library", return_value=binary), \
                 patch.object(main, "opengl_library", return_value=gl), \
                 patch.object(main, "opengl_shim", return_value=shim):
                self.assertTrue(main.opengl_renderer_available())
                main.experimental_manifest().parent.mkdir(parents=True)
                main.write_atomic(main.experimental_manifest(), "{}")
                main.write_atomic(main.native_hud_path(), "fps=1\n")
                main.install_short_launcher()
                probe = ("import json,os;print(json.dumps({"
                         "'gl':os.getenv('MANGOHUD_OPENGL_LIBS'),"
                         "'preload':os.getenv('LD_PRELOAD'),"
                         "'vk':os.getenv('VK_INSTANCE_LAYERS'),"
                         "'config':os.getenv('MANGOHUD_CONFIGFILE')}))")
                env = {**os.environ, "LD_PRELOAD": "/existing/library.so"}
                result = subprocess.run([str(main.short_launcher_path()), sys.executable,
                                         "-c", probe], capture_output=True, text=True,
                                        check=True, env=env)
                payload = json.loads(result.stdout)
                self.assertEqual(payload["gl"], str(gl))
                self.assertEqual(payload["preload"], "/existing/library.so:" + str(shim))
                self.assertEqual(payload["vk"], main.EXPERIMENTAL_LAYER_NAME)
                self.assertEqual(payload["config"], str(main.native_hud_path()))
                # Repeated wrapper invocation must not prepend the shim twice.
                nested = subprocess.run([str(main.short_launcher_path()),
                                         str(main.short_launcher_path()), sys.executable,
                                         "-c", probe], capture_output=True, text=True,
                                        check=True, env=env)
                self.assertEqual(json.loads(nested.stdout)["preload"], payload["preload"])
                gl.unlink()
                no_gl = subprocess.run([str(main.short_launcher_path()), sys.executable,
                                        "-c", probe], capture_output=True, text=True,
                                       check=True, env={**os.environ, "LD_PRELOAD": ""})
                self.assertIsNone(json.loads(no_gl.stdout)["gl"])
                self.assertEqual(json.loads(no_gl.stdout)["vk"], main.EXPERIMENTAL_LAYER_NAME)

    def test_existing_home_file_is_preserved(self):
        alias = main.home_launcher_path()
        alias.write_text('user file')
        main.install_home_launcher()
        self.assertEqual(alias.read_text(), 'user file')
        self.assertFalse(main.home_launcher_ready())

    def test_existing_foreign_symlink_is_preserved(self):
        alias = main.home_launcher_path()
        alias.symlink_to('/missing/user/target')
        main.install_home_launcher()
        self.assertEqual(os.readlink(alias), '/missing/user/target')
        self.assertFalse(main.home_launcher_ready())

    def test_native_binary_absent_means_no_short_command(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(main, "BASE", Path(folder)), \
                 patch.object(main, "native_renderer_available", return_value=False):
                main.install_short_launcher()
                self.assertFalse(main.short_launcher_path().exists())
                self.assertFalse(main.short_launcher_ready())


if __name__ == "__main__":
    unittest.main()
