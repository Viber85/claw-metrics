"""Read-only TDP limit and battery DRAW tests for SteamOS Claw A8."""
import pathlib
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import main


class TdpReadOnlyTests(unittest.TestCase):
    def test_ryzenadj_stapm_is_observed_only_without_writes(self):
        calls = []
        def runner(argv, **kwargs):
            calls.append((argv, kwargs))
            return SimpleNamespace(returncode=0, stdout="| STAPM LIMIT | 25.000 |", stderr="")
        # STAPM appears in the pipe-delimited column under RyzenAdj's -i output.
        with tempfile.TemporaryDirectory() as temp:
            value, source = main.read_tdp_limit(
                root=pathlib.Path(temp), binary="/usr/bin/ryzenadj", runner=runner)
        self.assertEqual((value, source), (25, "RyzenAdj STAPM"))
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], ["/usr/bin/ryzenadj", "-i"])
        self.assertEqual(calls[0][1]["timeout"], 2)

    def test_kernel_read_block_yields_unknown_without_guess(self):
        def runner(argv, **kwargs):
            return SimpleNamespace(returncode=1, stdout="", stderr="cannot open /dev/mem")
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(main.read_tdp_limit(root=pathlib.Path(temp),
                             binary="ryzenadj", runner=runner), (None, "Nije dostupno"))
        self.assertEqual(main.valid_tdp_w(0), None)
        self.assertEqual(main.valid_tdp_w("garbage"), None)
        self.assertEqual(main.valid_tdp_w(500), None)

    def test_msi_firmware_pl1_readback_fallback(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            node = root / "msi-wmi-platform.0/attributes/ppt_pl1_spl/current_value"
            node.parent.mkdir(parents=True)
            node.write_text("18\n")
            def runner(argv, **kwargs):
                return SimpleNamespace(returncode=1, stdout="", stderr="")
            self.assertEqual(main.read_tdp_limit(root=root, binary="ryzenadj",
                             runner=runner), (18, "MSI firmware PL1"))
            node.write_text("0\n")
            self.assertEqual(main.read_tdp_limit(root=root, binary="ryzenadj",
                             runner=runner), (None, "Nije dostupno"))

    def test_native_config_and_styles_ordered_independently(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(main, "BASE", pathlib.Path(temp)):
                d = main.normalize({"tdp": True, "draw": True,
                    "order": ["fps", "tdp", "draw", "time"],
                    "colors": {"tdp": "ABCD12", "draw": "112233"},
                    "token_weights": {"tdp.value": "semibold"},
                    "custom_labels": {"tdp": "LIMIT", "draw": "SYSTEM"}})
                cfg = main.mango_config(d, native_spacing=True)
                self.assertIn("exec=cat " + str(main.tdp_path()), cfg)
                self.assertIn("exec=cat " + str(main.draw_path()), cfg)
                self.assertLess(cfg.index(str(main.tdp_path())), cfg.index(str(main.draw_path())))
                self.assertEqual(main.tdp_text(d, 25), "LIMIT 25W")
                self.assertEqual(main.tdp_text(d, None), "LIMIT --")
                options = dict(x.split("=", 1) for x in cfg.splitlines() if "=" in x)
                self.assertEqual(len(options["claw_weight_map"]), 28)
                self.assertEqual(options["claw_weight_map"][-1], "3")
                self.assertEqual(options["claw_color_map"].split(":")[-1], "ABCD12")
                self.assertEqual(options["claw_color_map"].split(":")[25], "112233")

    def test_old_settings_migrate_tdp_near_draw_without_enabling(self):
        previous = ["fps", "cpu", "draw", "time"]
        d = main.normalize({"order": previous, "tdp": False})
        self.assertFalse(d["tdp"])
        self.assertEqual(d["order"][d["order"].index("draw")-1], "tdp")
        self.assertEqual(d["colors"]["tdp"], "FFBD69")

    def test_source_never_requests_tdp_writes(self):
        # No --stapm, --fast-limit, --slow-limit, --tctl-temp flags permitted.
        source = pathlib.Path(main.__file__).read_text()
        for forbidden in ("--stapm", "--fast-limit", "--slow-limit", "--tctl-temp"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
