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
    def test_short_launcher_execs_unmodified_args_and_environment(self):
        # Paths deliberately contain both whitespace and a single quote.
        with tempfile.TemporaryDirectory(prefix="Claw's test ") as folder:
            base = Path(folder) / "my config"
            binary = Path(folder) / "libMangoHud.so"
            binary.write_bytes(b"x" * 110001)
            with patch.object(main, "BASE", base), \
                 patch.object(main, "experimental_library", return_value=binary):
                self.assertTrue(main.native_renderer_available())
                main.install_short_launcher()
                launcher = main.short_launcher_path()
                self.assertTrue(main.short_launcher_ready())
                self.assertEqual(stat.S_IMODE(launcher.stat().st_mode), 0o755)
                self.assertTrue(launcher.read_bytes().startswith(b"#!/bin/sh\n"))
                self.assertIn('exec "$@"', launcher.read_text())
                probe = ("import json,os,sys;"
                         "print(json.dumps({'args':sys.argv[1:],"
                         "'layer':os.environ.get('VK_INSTANCE_LAYERS'),"
                         "'path':os.environ.get('VK_ADD_LAYER_PATH'),"
                         "'disabled':os.environ.get('DISABLE_MANGOHUD'),"
                         "'config':os.environ.get('MANGOHUD_CONFIGFILE')}))")
                result = subprocess.run(
                    [str(launcher), sys.executable, "-c", probe, "hello world", "it's ok", "$(not-executed)"],
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

    def test_native_binary_absent_means_no_short_command(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(main, "BASE", Path(folder)), \
                 patch.object(main, "native_renderer_available", return_value=False):
                main.install_short_launcher()
                self.assertFalse(main.short_launcher_path().exists())
                self.assertFalse(main.short_launcher_ready())


if __name__ == "__main__":
    unittest.main()
