"""Regression test for the *real* Decky Loader sandbox import semantics.

Decky imports <plugin>/main.py via importlib.spec_from_file_location and adds
ONLY <plugin>/py_modules to sys.path (not the plugin root). test.40 mistakenly
shipped updates.py in root, making all QAM controls disabled while the
already-running native overlay stayed visible.
"""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

# Matches upstream SteamDeckHomebrew/decky-loader:
# backend/decky_loader/plugin/sandboxed_plugin.py (sys.path.append(py_modules),
# importlib.util.spec_from_file_location + exec_module).
IMPORT_SCRIPT = """
import importlib.util, pathlib, sys
folder = pathlib.Path(sys.argv[1])
sys.path.append(str(folder / "py_modules"))
spec = importlib.util.spec_from_file_location("_", str(folder / "main.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
assert hasattr(module, "Plugin")
assert hasattr(module.Plugin, "get_settings")
assert hasattr(module.Plugin, "save_settings")
assert hasattr(module.Plugin, "check_updates")
assert hasattr(module.Plugin, "validate_github_releases")
print("DECKY_SANDBOX_IMPORT_OK")
"""


class DeckySandboxImportTests(unittest.TestCase):
    def setup_fake_install(self, folder, include_py_modules):
        shutil.copyfile(ROOT / "main.py", folder / "main.py")
        # Recreate precisely the broken test.40 root-only updater packaging.
        shutil.copyfile(ROOT / "updates.py", folder / "updates.py")
        if include_py_modules:
            p = folder / "py_modules"
            p.mkdir()
            shutil.copyfile(ROOT / "updates.py", p / "updates.py")

    def decky_import(self, folder):
        return subprocess.run(
            [sys.executable, "-I", "-c", IMPORT_SCRIPT, str(folder)],
            cwd="/",
            capture_output=True, text=True, timeout=10,
            check=False,
        )

    def test_correct_py_modules_install_loads_every_backend_callable(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            self.setup_fake_install(folder, include_py_modules=True)
            result = self.decky_import(folder)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("DECKY_SANDBOX_IMPORT_OK", result.stdout)

    def test_missing_optional_updater_does_not_disable_all_controls(self):
        # Regress test.40: optional update code must not break Decky backend
        # startup, even if the ZIP's updater file is missing or misplaced.
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            self.setup_fake_install(folder, include_py_modules=False)
            result = self.decky_import(folder)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("DECKY_SANDBOX_IMPORT_OK", result.stdout)

    def test_missing_updater_returns_clean_error_after_backend_import(self):
        script = IMPORT_SCRIPT + """
import asyncio
result = asyncio.run(module.Plugin().check_updates())
assert result["ok"] is False
assert "missing" in result["error"].lower() or "module" in result["error"].lower()
print("OPTIONAL_UPDATER_ERROR_OK")
"""
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            self.setup_fake_install(folder, include_py_modules=False)
            result = subprocess.run(
                [sys.executable, "-I", "-c", script, str(folder)],
                cwd="/", capture_output=True, text=True, timeout=10,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("OPTIONAL_UPDATER_ERROR_OK", result.stdout)

    def test_installer_zip_and_version_match_runtime_import_requirements(self):
        workflow = (ROOT / ".github/workflows/layout-experiment.yml").read_text()
        self.assertIn("cp updates.py artifact/ClawMetrics/py_modules/updates.py", workflow)
        self.assertIn("'py_modules/updates.py'", workflow)
        self.assertNotIn("cp plugin.json package.json main.py sensors.py updates.py", workflow)
        version = json.loads((ROOT / "package.json").read_text())["version"]
        self.assertEqual(version, "0.2.4-test.60")


if __name__ == "__main__":
    unittest.main()
