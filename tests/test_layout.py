"""Regression for MangoHud battery_time resetting the horizontal cursor to column 0."""
import unittest
import main


def options(settings):
    return dict(line.split('=', 1) if '=' in line else (line, '1')
                for line in main.mango_config(settings).splitlines()
                if line and not line.startswith('#'))


class HorizontalLayout(unittest.TestCase):
    def test_remaining_time_never_uses_compact_column_zero_path(self):
        for battery in (False, True):
            for clock in (False, True):
                with self.subTest(battery=battery, clock=clock):
                    settings = dict(main.DEFAULTS, battery=battery, time=clock)
                    config = options(settings)
                    # MangoHud's battery renderer resets column zero only with
                    # hud_compact; retain battery_time without that condition.
                    self.assertEqual(config['hud_compact'], '0')
                    self.assertEqual(config['horizontal'], '1')
                    self.assertEqual(config['battery_time'], str(int(battery)))
                    self.assertEqual(config['time'], str(int(clock)))
                    self.assertEqual(config['fps'], '1')
                    self.assertEqual(config['frame_timing'], '1')


class VerticalHudPreview(unittest.TestCase):
    def test_legacy_settings_remain_horizontal_by_default(self):
        self.assertEqual(main.normalize({})["hud_orientation"], "horizontal")
        self.assertEqual(main.normalize({"hud_orientation": "bad"})["hud_orientation"], "horizontal")
        self.assertEqual(main.normalize({"hud_orientation": False})["hud_orientation"], "horizontal")
        self.assertEqual(main.normalize({"hud_orientation": "vertical"})["hud_orientation"], "vertical")
        for native in (False, True):
            cfg = options_for({"fps": True, "cpu": True}, native)
            self.assertEqual(cfg["horizontal"], "1")
            self.assertEqual(cfg["table_columns"], "64")

    def test_vertical_is_real_mangohud_multi_row_layout(self):
        for native in (False, True):
            for anchor in main.HUD_POSITIONS:
                with self.subTest(native=native, anchor=anchor):
                    cfg = options_for({
                        "hud_orientation": "vertical", "hud_position": anchor,
                        "fps": True, "cpu": True, "gpu": True, "battery": True,
                        "padding_x": 8, "padding_y": 4,
                    }, native)
                    self.assertEqual(cfg["horizontal"], "0")
                    self.assertEqual(cfg["table_columns"], "2" if native else "3")
                    self.assertEqual(cfg["position"], anchor)
                    self.assertEqual(cfg["hud_compact"], "0")
                    self.assertEqual(cfg["fps"], "1")
                    self.assertEqual(cfg["cpu_stats"], "1")
                    self.assertEqual(cfg["gpu_stats"], "1")
                    self.assertEqual(cfg["battery"], "1")
                    if native:
                        self.assertEqual(cfg["claw_padding_x"], "8")
                        self.assertIn("claw_weight_map", cfg)
                    else:
                        self.assertNotIn("claw_weight_map", cfg)

    def test_vertical_width_is_optional_bounded_and_orientation_specific(self):
        self.assertEqual(main.normalize({})["vertical_width"], 0)
        for raw, normalized in ((-1, 0), (10, 160), (160, 160), (280, 280), (999, 420)):
            with self.subTest(width=raw):
                self.assertEqual(main.normalize({"vertical_width": raw})["vertical_width"], normalized)
        self.assertEqual(main.normalize({"vertical_width": "240"})["vertical_width"], 0)
        for native in (False, True):
            baseline = options_for({"hud_orientation": "horizontal"}, native)
            horizontal = options_for({"hud_orientation": "horizontal", "vertical_width": 300}, native)
            self.assertEqual(baseline, horizontal)
            self.assertNotIn("width", baseline)
            self.assertEqual(options_for({"hud_orientation": "vertical"}, native).get("width"),
                             "270" if native else None)
            cfg = options_for({"hud_orientation": "vertical", "vertical_width": 280}, native)
            self.assertEqual(cfg["width"], "280")
            self.assertEqual(cfg["horizontal"], "0")
            self.assertEqual(cfg["table_columns"], "2" if native else "3")
            for edge in main.HUD_POSITIONS:
                cfg = options_for({"hud_orientation": "vertical",
                                   "vertical_width": 280, "hud_position": edge}, native)
                self.assertEqual(cfg["width"], "280")
                self.assertEqual(cfg["position"], edge)

    def test_native_vertical_stack_and_stock_fallback(self):
        d = {"hud_orientation": "vertical", "vertical_width": 0}
        native = options_for(d, True)
        stock = options_for(d, False)
        self.assertEqual(native["claw_vertical_stack"], "1")
        self.assertEqual(native["claw_inline_metrics"], "1")
        self.assertEqual(native["table_columns"], "2")
        self.assertEqual(native["width"], "270")
        self.assertEqual(stock["table_columns"], "3")
        self.assertNotIn("claw_vertical_stack", stock)
        self.assertNotIn("width", stock)
        horizontal = options_for({"hud_orientation": "horizontal"}, True)
        self.assertEqual(horizontal["claw_vertical_stack"], "0")
        self.assertEqual(horizontal["table_columns"], "64")

    def test_native_vertical_fps_at_front_and_graph_at_end(self):
        payload = {"hud_orientation": "vertical", "order": [
            "gpu", "frametime", "cpu", "fps", "ram", "vram",
            "battery", "tdp", "draw", "time"]}
        native = main.mango_config(payload, native_spacing=True)
        stock = main.mango_config(payload, native_spacing=False)
        self.assertLess(native.index("\nfps=1\n"), native.index("\ngpu_stats=1\n"))
        self.assertGreater(native.index("\nframe_timing=1\n"), native.index("\ntime=1\n"))
        self.assertLess(stock.index("\ngpu_stats=1\n"), stock.index("\nfps=1\n"))

    def test_native_vertical_graph_and_inline_gap_remain_configurable(self):
        for style, index in (("line", "0"), ("area", "1"), ("bars", "2"), ("dual", "3")):
            native = options_for({"hud_orientation": "vertical",
                                  "graph_style": style, "inner_gap": 12}, True)
            self.assertEqual(native["claw_graph_style"], index)
            self.assertEqual(native["claw_inner_gap"], "12")
        self.assertNotIn("claw_graph_style", options_for({"hud_orientation": "vertical"}, False))

    def test_vertical_fps_scale_native_and_horizontal_isolation(self):
        native = options_for({"hud_orientation":"vertical","fps_scale":160},True)
        self.assertEqual(native["claw_fps_scale"],"160")
        self.assertEqual(native["claw_vertical_stack"],"1")
        self.assertNotIn("claw_fps_scale",
                         options_for({"hud_orientation":"vertical","fps_scale":160},False))
        # Test 54 does not change the generated horizontal renderer profile.
        a = options_for({"hud_orientation":"horizontal","fps_scale":160},True)
        self.assertEqual(a["claw_fps_scale"],"160")
        self.assertEqual(a["claw_vertical_stack"],"0")

    def test_wrapping_keeps_native_vertical_width_and_existing_metric_flags(self):
        config = options_for({"hud_orientation":"vertical","vertical_width":260,
                              "gpu":True,"cpu":True,
                              "metrics":{"gpu_junction_temp":True,
                                         "gpu_power":True,
                                         "gpu_core_clock":True}}, True)
        self.assertEqual(config["width"],"260")
        self.assertEqual(config["table_columns"],"2")
        self.assertEqual(config["claw_vertical_stack"],"1")
        self.assertEqual(config["gpu_junction_temp"],"1")
        self.assertEqual(config["gpu_core_clock"],"1")
        self.assertEqual(config["gpu_power"],"1")

    def test_vertical_dimensions_and_spacing_are_persistent_and_isolated(self):
        self.assertEqual(main.normalize({})["vertical_value_gap"], 8)
        self.assertEqual(main.normalize({})["vertical_graph_width"], 0)
        self.assertEqual(main.normalize({})["vertical_graph_height"], 28)
        for raw, expected in ((-5, 0), (20, 80), (120, 120), (999, 420)):
            self.assertEqual(main.normalize({"vertical_graph_width":raw})["vertical_graph_width"],expected)
        self.assertEqual(main.normalize({"vertical_graph_height":5})["vertical_graph_height"],16)
        self.assertEqual(main.normalize({"vertical_graph_height":999})["vertical_graph_height"],72)
        cfg=options_for({"hud_orientation":"vertical","vertical_value_gap":11,
                         "vertical_graph_width":185,"vertical_graph_height":46},True)
        self.assertEqual(cfg["claw_vertical_value_gap"],"11")
        self.assertEqual(cfg["claw_vertical_graph_width"],"185")
        self.assertEqual(cfg["claw_vertical_graph_height"],"46")
        for native in (False, True):
            old=options_for({"hud_orientation":"horizontal"},native)
            new=options_for({"hud_orientation":"horizontal",
               "vertical_value_gap":15,"vertical_graph_width":300,
               "vertical_graph_height":70},native)
            # Vertical-only settings should not mutate the horizontal renderer.
            for key in ("claw_vertical_value_gap","claw_vertical_graph_width","claw_vertical_graph_height"):
                new.pop(key,None);old.pop(key,None)
            self.assertEqual(old,new)

    def test_saved_styles_keep_orientation_and_legacy_styles_do_not_override(self):
        slots = main.normalize({"hud_orientation":"vertical", "style_presets": {
            "1": {"version": 3, "hud_orientation": "vertical", "vertical_width": 290, "vertical_value_gap": 13, "vertical_graph_width": 190, "vertical_graph_height": 40, "fontsize": 20},
            "2": {"version": 2, "fontsize": 17}
        }})["style_presets"]
        self.assertEqual(slots["1"]["hud_orientation"], "vertical")
        self.assertEqual(slots["1"]["vertical_width"], 290)
        self.assertEqual(slots["1"]["vertical_value_gap"],13)
        self.assertEqual(slots["1"]["vertical_graph_width"],190)
        self.assertEqual(slots["1"]["vertical_graph_height"],40)
        self.assertNotIn("vertical_width", slots["2"])
        self.assertNotIn("hud_orientation", slots["2"])
        self.assertNotIn("hud_orientation", main.normalize({"style_presets":{
            "1": {"hud_orientation":"sideways"}
        }})["style_presets"]["1"])

def options_for(settings, native):
    return dict(line.split("=", 1) if "=" in line else (line, "1")
                for line in main.mango_config(settings, native_spacing=native).splitlines()
                if line and not line.startswith("#"))

if __name__ == '__main__':
    unittest.main()
