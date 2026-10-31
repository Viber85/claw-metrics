"""Claw DevLab style and native-display sync contracts."""
import unittest
from unittest.mock import patch
import main


class DevLabSyncTests(unittest.TestCase):
    def test_styles_round_trip_with_layout_and_active_slot(self):
        payload = {
            "fontsize": 24, "offset_x": 132, "padding_x": 9,
            "style_presets": {
                "1": {
                    "version": 2, "fontsize": 24, "offset_x": 132, "offset_y": 12,
                    "padding_y": 11, "padding_x": 9, "element_gap": 10,
                    "table_gap": 5, "inner_gap": 2, "graph_width": 170,
                    "opacity": 70, "rounding": 5, "sans": True, "inline_metrics": True,
                    "colors": {"time": "#112233", "draw": "44aabb", "text": "F0F2F5"},
                    "font_weight": "light", "token_weights": {"cpu.temp": "bold"},
                    "token_colors": {"gpu.temp": "334455"}
                },
                "2": {"colors": {"text": "ABCDEF"}, "font_weight": "bold"},
            },
            "active_style": "1",
            "custom_labels": {"fps": "Frame rate", "battery": "Remaining", "draw": "DISCHARGE"},
        }
        d = main.normalize(payload)
        self.assertEqual(d["active_style"], "1")
        self.assertEqual(d["style_presets"]["1"]["fontsize"], 24)
        self.assertEqual(d["style_presets"]["1"]["padding_x"], 9)
        self.assertEqual(d["style_presets"]["1"]["colors"]["draw"], "44AABB")
        self.assertEqual(d["style_presets"]["1"]["token_colors"]["gpu.temp"], "334455")
        self.assertEqual(d["style_presets"]["2"]["colors"]["time"], "ABCDEF")
        self.assertNotIn("fontsize", d["style_presets"]["2"])
        self.assertEqual(d["custom_labels"]["draw"], "DISCHARGE")
        self.assertEqual(main.normalize(d), d)

    def test_old_colors_migrate_clock_draw_and_keep_active_slot_safe(self):
        d = main.normalize({"colors": {"text": "112233"}, "active_style": "7"})
        self.assertEqual(d["colors"]["time"], "112233")
        self.assertEqual(d["colors"]["draw"], "112233")
        self.assertIsNone(d["active_style"])

    def test_label_sanitization_and_injection_in_native_config(self):
        d = main.normalize({"custom_labels": {
            "fps": "Rate\nhacked=1", "cpu": "Main CPU", "gpu": "Radeon",
            "ram": "System", "vram": "Graphics", "battery": "Charge",
            "draw": "Total draw", "unused": "ignore",
        }})
        self.assertNotIn("=", d["custom_labels"]["fps"])
        self.assertNotIn("\n", d["custom_labels"]["fps"])
        self.assertNotIn("unused", d["custom_labels"])
        conf = main.mango_config(d, native_spacing=True)
        for expected in ["fps_text=" + d["custom_labels"]["fps"],
                         "cpu_text=Main CPU", "gpu_text=Radeon",
                         "claw_ram_label=System", "claw_vram_label=Graphics",
                         "claw_battery_label=Charge"]:
            self.assertIn(expected + "\n", conf)
        self.assertNotIn("claw_ram_label=", main.mango_config(d))

    def test_independent_colors_feed_correct_native_tokens(self):
        d = main.normalize({"colors": {"time": "AABBCC", "draw": "667788"},
                            "token_colors": {"time.value": "99FF00"}})
        conf = main.mango_config(d, native_spacing=True)
        cmap = next(x.split("=", 1)[1] for x in conf.splitlines()
                    if x.startswith("claw_color_map=")).split(":")
        self.assertEqual(cmap[main.TOKEN_SLOTS.index("time.value")], "99FF00")
        self.assertEqual(cmap[main.TOKEN_SLOTS.index("battery.power")], "667788")
        with patch.object(main, "battery_draw", return_value="DRAW 24.6W"):
            self.assertEqual(main.draw_text(main.normalize(
                {"custom_labels": {"draw": "TOTAL"}})), "TOTAL 24.6W")

    def test_native_renderer_has_label_and_draw_render_hooks(self):
        from pathlib import Path
        code = (Path(__file__).resolve().parents[1] /
                "experiments/apply_token_styles.py").read_text()
        for key in ("claw_ram_label", "claw_vram_label", "claw_battery_label",
                    "native DRAW and TDP token style"):
            self.assertIn(key, code)


if __name__ == "__main__":
    unittest.main()
