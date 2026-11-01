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

    def test_pdc_actual_bundled_binary_path_and_nonzero_valid_stdout(self):
        with tempfile.TemporaryDirectory() as temp:
            plugin_root = pathlib.Path(temp) / "plugins"
            binary = plugin_root / "Panel de Control" / "bin" / "ryzenadj"
            binary.parent.mkdir(parents=True)
            binary.write_text("#!/bin/sh\nexit 0\n")
            binary.chmod(0o755)
            with patch.object(main.shutil, "which", return_value=None):
                self.assertEqual(main.resolve_ryzenadj([plugin_root]), str(binary))
            def readback(argv, **kwargs):
                return SimpleNamespace(returncode=2,
                    stdout="| STAPM LIMIT | 25.000 |", stderr="unrelated probe unavailable")
            self.assertEqual(main.read_tdp_limit(root=pathlib.Path(temp),
                binary=str(binary), runner=readback, panel_roots=[]),
                (25, "RyzenAdj STAPM"))

    def test_kernel_read_block_yields_unknown_without_guess(self):
        def runner(argv, **kwargs):
            return SimpleNamespace(returncode=1, stdout="", stderr="cannot open /dev/mem")
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(main.read_tdp_limit(root=pathlib.Path(temp),
                             binary="ryzenadj", runner=runner, panel_roots=[pathlib.Path(temp)]), (None, "Unavailable"))
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
                             runner=runner, panel_roots=[root]), (18, "MSI firmware PL1"))
            node.write_text("0\n")
            self.assertEqual(main.read_tdp_limit(root=root, binary="ryzenadj",
                             runner=runner, panel_roots=[root]), (None, "Unavailable"))

    def test_panel_configured_setpoint_used_when_hw_readback_blocked(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            pdc = root / "Panel de Control"
            pdc.mkdir()
            (pdc / "tdp_profiles.json").write_text(
                '{"global":{"pl1":23,"mode":"estable"}, "games":{}}')
            (pdc / "state.json").write_text('{"tdp_control_enabled":true}')
            def denied(argv, **kwargs):
                return SimpleNamespace(returncode=1, stdout="", stderr="dev/mem denied")
            value, source = main.read_tdp_limit(root=root, binary="ryzenadj",
                runner=denied, panel_roots=[root])
            self.assertEqual(value, 23)
            self.assertIn("configured", source)
            self.assertIn("not hardware-verified", source)

    def test_panel_profiles_do_not_misreport_game_or_auto_mode(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            pdc = root / "Panel de Control"
            pdc.mkdir()
            path = pdc / "tdp_profiles.json"
            path.write_text('{"global":{"pl1":23}, "games":{"123":{"pl1":30}}}')
            value, reason = main.read_panel_setpoint([root])
            self.assertIsNone(value)
            self.assertIn("game profiles", reason)
            path.write_text('{"global":{"pl1":23,"auto_tdp":true}, "games":{}}')
            self.assertIsNone(main.read_panel_setpoint([root])[0])
            path.write_text('{"global":{"pl1":23}, "games":{}}')
            (pdc / "state.json").write_text('{"tdp_control_enabled":false}')
            self.assertIsNone(main.read_panel_setpoint([root])[0])


    def test_diagnostics_show_pdc_global_while_game_profiles_block_readback(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            node = root / "fw/msi-wmi-platform.0/attributes/ppt_pl1_spl/current_value"
            node.parent.mkdir(parents=True)
            node.write_text("0\n")
            pdc = root / "settings/Panel de Control"
            pdc.mkdir(parents=True)
            (pdc / "tdp_profiles.json").write_text(
                '{"global":{"pl1":23},"games":{"123":{"pl1":30}}}')
            (pdc / "state.json").write_text('{"tdp_control_enabled":true}')
            with patch.object(main.shutil, "which", return_value=None):
                report = main.tdp_source_diagnostics(
                    firmware_root=root / "fw", plugin_roots=[root / "plugins"],
                    settings_roots=[root / "settings"])
            self.assertIn("MSI firmware PL1: unreadable", report)
            self.assertIn("RyzenAdj: executable not found", report)
            self.assertIn("PDC: global 23W", report)
            self.assertIn("game overrides 1", report)
            self.assertIn("različiti game profiles", report)
            self.assertNotIn('"123"', report)

    def test_diagnostics_ryzenadj_read_is_non_mutating(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            binpath = root / "plugins/Panel de Control/bin/ryzenadj"
            binpath.parent.mkdir(parents=True)
            binpath.write_text("#!/bin/sh\nexit 0\n")
            binpath.chmod(0o755)
            calls = []
            def reader(argv, **kwargs):
                calls.append(argv)
                return SimpleNamespace(returncode=2, stdout="| STAPM LIMIT | 19.000 |")
            with patch.object(main.shutil, "which", return_value=None):
                report = main.tdp_source_diagnostics(
                    firmware_root=root / "fw", plugin_roots=[root / "plugins"],
                    settings_roots=[root / "settings"], runner=reader)
            self.assertIn("RyzenAdj: 19W, exit code 2", report)
            self.assertEqual(calls, [[str(binpath), "-i"]])


    def test_current_game_specific_tdp_and_global_follow(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            pdc = root / "Panel de Control"
            pdc.mkdir()
            (pdc / "tdp_profiles.json").write_text(
                '{"global":{"pl1":18},"games":{"123":{"pl1":25},'
                '"456":{"pl1":30,"follow_global":true},'
                '"ns:my game":{"pl1":29},"789":{"pl1":20,"auto_tdp":true}}}')
            (pdc / "state.json").write_text('{"tdp_control_enabled":true}')
            self.assertIsNone(main.read_panel_setpoint([root])[0])
            for appid, expected in (("123", 25), ("456", 18),
                                    ("ns:my game", 29), ("unsaved", 18)):
                self.assertEqual(main.read_panel_setpoint(
                    [root], appid=appid, context_known=True)[0], expected)
            self.assertEqual(main.read_panel_setpoint(
                [root], context_known=True)[0], 18)
            self.assertIsNone(main.read_panel_setpoint(
                [root], appid="789", context_known=True)[0])
            (pdc / "power_ownership.json").write_text(
                '{"games":{"123":{"owner":"steam"}}}')
            self.assertIsNone(main.read_panel_setpoint(
                [root], appid="123", context_known=True)[0])
            (pdc / "state.json").write_text('{"tdp_control_enabled":false}')
            self.assertIsNone(main.read_panel_setpoint(
                [root], appid="456", context_known=True)[0])

    def test_read_limit_uses_running_game_not_other_saved_games(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            pdc = root / "Panel de Control"
            pdc.mkdir()
            (pdc / "tdp_profiles.json").write_text(
                '{"global":{"pl1":18},"games":{"111":{"pl1":26},"222":{"pl1":31}}}')
            def denied(argv, **kwargs):
                return SimpleNamespace(returncode=1, stdout="", stderr="denied")
            self.assertEqual(main.read_tdp_limit(
                root=root, binary="ryzenadj", runner=denied,
                panel_roots=[root], appid="222", context_known=True)[0], 31)
            self.assertIsNone(main.read_tdp_limit(
                root=root, binary="ryzenadj", runner=denied,
                panel_roots=[root], context_known=False)[0])

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

    def test_native_draw_tdp_use_regular_hud_font_in_horizontal_mode(self):
        code = (pathlib.Path(__file__).resolve().parents[1] /
                "experiments/apply_token_styles.py").read_text()
        self.assertIn("const bool claw_exec_small_font", code)
        self.assertIn("if (claw_exec_small_font) ImGui::PushFont", code)
        self.assertIn("if (claw_exec_small_font) ImGui::PopFont", code)
        self.assertIn("ClawText(27,", code)
        self.assertIn("ClawText(25,", code)

    def test_source_never_requests_tdp_writes(self):
        # No --stapm, --fast-limit, --slow-limit, --tctl-temp flags permitted.
        source = pathlib.Path(main.__file__).read_text()
        for forbidden in ("--stapm", "--fast-limit", "--slow-limit", "--tctl-temp"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
