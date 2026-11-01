import tempfile
import unittest
from pathlib import Path
import main
from sensors import draw


class Settings(unittest.TestCase):
    def test_old_settings_keep_power_and_visibility(self):
        d = main.normalize({'power': False, 'gpu': False, 'fontsize': 22})
        self.assertFalse(d['gpu'])
        self.assertEqual(d['fontsize'], 22)
        self.assertFalse(d['metrics']['cpu_power'])
        self.assertFalse(d['metrics']['gpu_power'])

    def test_reorder_survives_and_rejects_unknown_duplicates(self):
        d = main.normalize({'order': ['time', 'gpu', 'time', 'bogus', {}]})
        self.assertEqual(d['order'][:2], ['time', 'gpu'])
        self.assertEqual(set(d['order']), set(main.ORDER))
        self.assertEqual(len(d['order']), len(main.ORDER))
        c = main.mango_config(d)
        self.assertLess(c.index('\ntime=1'), c.index('\ngpu_stats=1'))
        self.assertLess(c.index('\ngpu_stats=1'), c.index('\nfps=1'))

    def test_normalization_isolated_from_defaults(self):
        a = main.normalize({})
        a['metrics']['gpu_temp'] = False
        a['order'].reverse()
        self.assertTrue(main.normalize({})['metrics']['gpu_temp'])
        self.assertEqual(main.normalize({})['order'], main.ORDER)

    def test_manual_position_and_legacy_top_margin(self):
        config = main.mango_config(main.normalize({'margin': 24}))
        self.assertIn('offset_x=8\n', config)
        self.assertIn('offset_y=24\n', config)
        self.assertIn('horizontal_stretch=0\n', config)
        self.assertIn('position=top-left\n', config)
        self.assertIn('hud_compact=0\n', config)
        self.assertIn('round_corners=10\n', config)

    def test_zero_vertical_padding_is_default_and_legacy_is_preserved(self):
        self.assertEqual(main.normalize({})["padding_y"], 0)
        for native in (False, True):
            config = main.mango_config(main.normalize({}), native_spacing=native)
            self.assertIn("cellpadding_y=0.000000\n", config)
            self.assertIn("hud_compact=0\n", config)
            self.assertNotIn("claw_padding_y=", config)
        # Previously saved profiles or style slots keep the user's actual value.
        self.assertEqual(main.normalize({"padding_y": 11})["padding_y"], 11)
        self.assertEqual(main.normalize({"style_presets":{
            "1":{"version":2,"padding_y":13}
        }})["style_presets"]["1"]["padding_y"], 13)
        self.assertEqual(main.normalize({"padding_y":-999})["padding_y"], 0)
        self.assertEqual(main.normalize({"padding_y":999})["padding_y"], 24)

    def test_padding_is_in_pixels_at_each_font_size(self):
        for font in (12, 18, 28):
            c = main.mango_config(main.normalize({'fontsize': font, 'padding_y': 12, 'offset_x': -100, 'offset_y': 60}))
            opts = dict(line.split('=', 1) for line in c.splitlines() if '=' in line)
            self.assertAlmostEqual(float(opts['cellpadding_y']) * font / 2, 12, places=4)
            self.assertEqual(opts['offset_x'], '-100')
            self.assertEqual(opts['offset_y'], '60')

    def test_future_spacing_settings_are_bounded_and_keep_stock_renderer_safe(self):
        # Stock MangoHud does not support adjustable horizontal padding or gap.
        settings = main.normalize({'padding_x': 999, 'element_gap': -20})
        self.assertEqual(settings['padding_x'], 24)
        self.assertEqual(settings['element_gap'], 0)
        options = main.mango_config(settings)
        self.assertNotIn('claw_padding_x=', options)
        self.assertNotIn('claw_element_gap=', options)
        self.assertNotIn('fps_text=FPS*', options)
        self.assertIn('hud_compact=0\n', options)
        self.assertEqual(main.normalize({})['padding_x'], 5)
        self.assertEqual(main.normalize({})['element_gap'], 8)
        self.assertEqual(main.normalize({})['table_gap'], 4)
        self.assertEqual(main.normalize({})['graph_width'], 150)
        self.assertEqual(main.normalize({})['inner_gap'], 4)
        self.assertTrue(main.normalize({})['inline_metrics'])
        self.assertTrue(main.normalize({})['fps_bold'])
        self.assertEqual(main.normalize({'inner_gap': 99})['inner_gap'], 16)
        self.assertEqual(main.normalize({'table_gap': -2, 'graph_width': 1})['graph_width'], 80)
        patched = main.mango_config(main.normalize({'padding_x': 3, 'element_gap': 2}), native_spacing=True)
        self.assertIn('claw_padding_x=3\n', patched)
        self.assertIn('claw_element_gap=2\n', patched)
        self.assertIn('claw_table_padding_x=4\n', patched)
        self.assertIn('claw_graph_width=150\n', patched)
        self.assertIn('claw_inner_gap=4\n', patched)
        self.assertIn('claw_inline_metrics=1\n', patched)
        self.assertIn('claw_fps_bold=1\n', patched)
        safe = main.mango_config(main.normalize({}))
        self.assertNotIn('claw_inner_gap=', safe)
        self.assertNotIn('claw_inline_metrics=', safe)
        self.assertNotIn('claw_fps_bold=', safe)
        off = main.mango_config(main.normalize({'inline_metrics': False, 'fps_bold': False}), native_spacing=True)
        self.assertIn('claw_inline_metrics=0\n', off)
        self.assertIn('claw_fps_bold=0\n', off)
        self.assertIn('fps_text=FPS*\n', patched)

    def test_custom_colors_are_validated_and_persist_in_both_profiles(self):
        overrides = {
            'separator': '#ff0099', 'text': '0123ab', 'cpu': 'A1B2C3',
            'gpu': 'bad;color', 'ram': 'fff', 'fps_value': 'AABBCC',
            'unknown': '000000', 'battery': 1234,
        }
        d = main.normalize({'colors': overrides})
        self.assertEqual(d['colors']['separator'], 'FF0099')
        self.assertEqual(d['colors']['text'], '0123AB')
        self.assertEqual(d['colors']['cpu'], 'A1B2C3')
        self.assertEqual(d['colors']['gpu'], main.COLORS['gpu'])
        self.assertEqual(d['colors']['ram'], main.COLORS['ram'])
        self.assertEqual(d['colors']['battery'], main.COLORS['battery'])
        self.assertNotIn('unknown', d['colors'])
        for native in (False, True):
            cfg = main.mango_config(d, native_spacing=native)
            for line in ('text_color=0123AB', 'cpu_color=A1B2C3',
                         'horizontal_separator_color=FF0099',
                         'fps_color=AABBCC,AABBCC,AABBCC'):
                self.assertIn(line + '\n', cfg)
        first = main.normalize({})
        first['colors']['separator'] = 'FFFFFF'
        self.assertEqual(main.normalize({})['colors']['separator'], '777C87')

    def test_condensed_font_weights_and_native_bold_configuration(self):
        import hashlib
        from unittest.mock import patch
        self.assertEqual(main.normalize({})['font_weight'], 'regular')
        self.assertEqual(main.normalize({'font_weight': 'light'})['font_weight'], 'light')
        self.assertEqual(main.normalize({'font_weight': 'bold'})['font_weight'], 'bold')
        self.assertEqual(main.normalize({'font_weight': 'semibold'})['font_weight'], 'semibold')
        self.assertEqual(main.normalize({'font_weight': 'invalid'})['font_weight'], 'regular')
        dummy = bytes([0, 1, 0, 0]) + bytes(range(256)) * 100
        digest = hashlib.sha1(b'blob ' + str(len(dummy)).encode() +
                              bytes([0]) + dummy).hexdigest()
        self.assertTrue(main.valid_git_font(dummy, digest))
        self.assertFalse(main.valid_git_font(dummy, '0' * 40))
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(main, 'BASE', Path(folder)):
                with patch.object(main, 'BARLOW_BLOBS', {
                    'light': ('Light', digest),
                    'regular': ('Regular', digest),
                    'semibold': ('SemiBold', digest),
                    'bold': ('Bold', digest),
                }):
                    for weight in ('light', 'regular', 'semibold', 'bold'):
                        main.write_atomic(main.condensed_font_path(weight), dummy)
                    self.assertTrue(main.condensed_fonts_ready())
                    medium = main.mango_config(main.normalize({'font_weight': 'semibold'}))
                    self.assertIn('font_file=' + str(main.condensed_font_path('semibold')) + '\n', medium)
                    native = main.mango_config(main.normalize({
                        'font_weight': 'light'}), native_spacing=True)
                    self.assertIn('font_file=' + str(main.condensed_font_path('light')) + '\n', native)
                    self.assertIn('claw_bold_font_file=' + str(main.condensed_font_path('bold')) + '\n', native)
                    normal = main.mango_config(main.normalize({'font_weight': 'bold'}))
                    self.assertIn('font_file=' + str(main.condensed_font_path('bold')) + '\n', normal)
                    self.assertNotIn('claw_bold_font_file=', normal)

    def test_embedded_font_installation_works_offline(self):
        import hashlib
        from unittest.mock import patch
        dummy = bytes([0, 1, 0, 0]) + bytes(range(256)) * 100
        digest = hashlib.sha1(b'blob ' + str(len(dummy)).encode() +
                              bytes([0]) + dummy).hexdigest()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            assets = root / 'package' / 'assets' / 'fonts'
            assets.mkdir(parents=True)
            fake_weights = {
                'light': ('Light', digest), 'regular': ('Regular', digest),
                'semibold': ('SemiBold', digest), 'bold': ('Bold', digest)
            }
            for name, (suffix, _) in fake_weights.items():
                (assets / ('BarlowSemiCondensed-' + suffix + '.ttf')).write_bytes(dummy)
            with patch.object(main, 'BASE', root / 'config'), patch.object(main, 'BARLOW_BLOBS', fake_weights), patch.object(main, 'bundled_font_path', side_effect=lambda weight: assets / ('BarlowSemiCondensed-' + fake_weights[weight][0] + '.ttf')):
                main.install_condensed_fonts()
                self.assertTrue(main.condensed_fonts_ready())
                # Invalid local font is replaced by a valid packaged copy.
                main.condensed_font_path('semibold').write_bytes(b'corrupt')
                main.install_condensed_fonts()
                self.assertTrue(main.condensed_fonts_ready())
                # No file requires network access during startup.

    def test_per_metric_colors_weights_persist_and_are_bounded(self):
        self.assertEqual(len(main.TOKEN_SLOTS), 28)
        config = {
            "token_weights": {
                "cpu.label": "semibold", "cpu.load": "bold",
                "gpu.temp": "light", "unknown": "bold", "ram.label": "invalid"
            },
            "token_colors": {
                "cpu.temp": "#ffac12", "gpu.load": "00bbee",
                "cpu.clock": "not-a-color", "unknown": "000000"
            },
        }
        d = main.normalize(config)
        self.assertEqual(d["token_weights"], {
            "cpu.label": "semibold", "cpu.load": "bold", "gpu.temp": "light"
        })
        self.assertEqual(d["token_colors"], {"cpu.temp": "FFAC12", "gpu.load": "00BBEE"})
        native = main.mango_config(d, native_spacing=True)
        options = dict(line.split("=", 1) for line in native.splitlines() if "=" in line)
        weights = options["claw_weight_map"]
        colors = options["claw_color_map"].split(":")
        self.assertEqual(len(weights), 28)
        self.assertEqual(len(colors), 28)
        for slot, weight in d["token_weights"].items():
            self.assertEqual(weights[main.TOKEN_SLOTS.index(slot)], main.FONT_DIGITS[weight])
        self.assertEqual(colors[main.TOKEN_SLOTS.index("cpu.temp")], "FFAC12")
        self.assertEqual(colors[main.TOKEN_SLOTS.index("gpu.load")], "00BBEE")
        self.assertEqual(colors[main.TOKEN_SLOTS.index("fps.value")], "------")
        stock = main.mango_config(d)
        self.assertNotIn("claw_weight_map=", stock)
        self.assertNotIn("claw_color_map=", stock)

    def test_fps_scale_and_center_are_bounded_and_native_only(self):
        d = main.normalize({"fps_scale": 170, "center_horizontal": True, "offset_x": -37})
        self.assertEqual(d["fps_scale"], 170)
        self.assertTrue(d["center_horizontal"])
        self.assertEqual(d["offset_x"], -37)
        native = main.mango_config(d, native_spacing=True)
        self.assertIn("claw_fps_scale=170\n", native)
        self.assertIn("claw_center_horizontal=1\n", native)
        self.assertIn("offset_x=-37\n", native)
        stock = main.mango_config(d)
        self.assertNotIn("claw_fps_scale=", stock)
        self.assertNotIn("claw_center_horizontal=", stock)
        self.assertEqual(main.normalize({"fps_scale": 300})["fps_scale"], 200)
        self.assertEqual(main.normalize({"fps_scale": 40})["fps_scale"], 100)
        self.assertFalse(main.normalize({"center_horizontal": "yes"})["center_horizontal"])

    def test_six_edge_hud_anchors_and_legacy_center_migration(self):
        self.assertEqual(main.normalize({})["hud_position"], "top-left")
        legacy = main.normalize({"center_horizontal": True, "offset_x": -25})
        self.assertEqual(legacy["hud_position"], "top-center")
        self.assertEqual(legacy["offset_x"], -25)
        self.assertIn("claw_center_horizontal=1\n", main.mango_config(legacy, native_spacing=True))
        self.assertIn("position=top-left\n", main.mango_config(legacy, native_spacing=True))
        for anchor, position, x, y, right in (
            ("top-left", "top-left", "8", "14", "0"),
            ("top-right", "top-right", "-8", "14", "1"),
            ("bottom-left", "bottom-left", "8", "-14", "0"),
            ("bottom-right", "bottom-right", "-8", "-14", "1"),
        ):
            with self.subTest(anchor=anchor):
                d = main.normalize({"hud_position": anchor, "center_horizontal": True,
                                    "offset_x": 8, "offset_y": 14})
                self.assertFalse(d["center_horizontal"])
                config = main.mango_config(d, native_spacing=True)
                self.assertIn(f"position={position}\n", config)
                self.assertIn(f"offset_x={x}\n", config)
                self.assertIn(f"offset_y={y}\n", config)
                self.assertIn(f"claw_align_right={right}\n", config)
                self.assertIn("claw_center_horizontal=0\n", config)
        for anchor, native_position, expected_y in (
            ("top-center", "top-left", "14"),
            ("bottom-center", "bottom-left", "-14"),
        ):
            with self.subTest(anchor=anchor):
                d = main.normalize({"hud_position": anchor, "offset_x": 8, "offset_y": 14})
                self.assertTrue(d["center_horizontal"])
                cfg = main.mango_config(d, native_spacing=True)
                self.assertIn(f"position={native_position}\n", cfg)
                self.assertIn("offset_x=8\n", cfg)  # Preserved but ignored by renderer.
                self.assertIn(f"offset_y={expected_y}\n", cfg)
                self.assertIn("claw_center_horizontal=1\n", cfg)
                self.assertIn("claw_align_right=0\n", cfg)
        self.assertEqual(main.normalize({"hud_position": "invalid"})["hud_position"], "top-left")

    def test_style_slot_retains_hud_corner_and_legacy_center(self):
        saved = {"1":{"version":2,"hud_position":"bottom-center","offset_x":12},
                 "2":{"version":2,"center_horizontal":True}}
        slots = main.normalize({"style_presets":saved})["style_presets"]
        self.assertEqual(slots["1"]["hud_position"], "bottom-center")
        self.assertTrue(slots["1"]["center_horizontal"])
        self.assertEqual(slots["1"]["offset_x"], 12)
        self.assertEqual(slots["2"]["hud_position"], "top-center")
        self.assertTrue(slots["2"]["center_horizontal"])

    def test_style_slot_retains_fps_size_and_manual_position(self):
        saved = {"1":{"version":2,"fps_scale":160,"center_horizontal":True,"offset_x":-25}}
        style = main.normalize({"style_presets":saved,"active_style":"1"})["style_presets"]["1"]
        self.assertEqual(style["fps_scale"], 160)
        self.assertTrue(style["center_horizontal"])
        self.assertEqual(style["offset_x"], -25)

    def test_frametime_graph_styles_native_selection(self):
        self.assertEqual(main.normalize({})["graph_style"], "line")
        self.assertEqual(main.normalize({"graph_style":"invalid"})["graph_style"], "line")
        for name, idx in (("area",1),("line",0),("bars",2),("dual",3)):
            with self.subTest(name=name):
                settings=main.normalize({"graph_style":name})
                native=main.mango_config(settings,native_spacing=True)
                stock=main.mango_config(settings)
                self.assertIn(f"claw_graph_style={idx}\n",native)
                self.assertNotIn("claw_graph_style=",stock)

    def test_graph_style_presets_and_old_style_compatibility(self):
        settings=main.normalize({"style_presets":{
            "1":{"version":2,"graph_style":"area"},
            "2":{"version":2,"graph_style":"dual"}}})
        self.assertEqual(settings["style_presets"]["1"]["graph_style"],"area")
        self.assertEqual(settings["style_presets"]["2"]["graph_style"],"dual")
        self.assertNotIn("graph_style",main.normalize({"style_presets":{
            "1":{"version":2,"graph_style":"invalid"}}})["style_presets"]["1"])


    def test_native_fps_scale_from_100_to_200_by_tens(self):
        for scale in range(100, 201, 10):
            with self.subTest(scale=scale):
                d = main.normalize({"fps_scale": scale})
                self.assertEqual(d["fps_scale"], scale)
                self.assertIn(f"claw_fps_scale={scale}\n",
                              main.mango_config(d, native_spacing=True))
                self.assertNotIn("claw_fps_scale=",
                                 main.mango_config(d, native_spacing=False))

    def test_style_presets_validate_before_reuse(self):
        payload = {"style_presets": {
            "1": {"font_weight": "semibold", "fps_bold": False,
                   "token_weights": {"cpu.power": "bold", "bogus": "bold"},
                   "token_colors": {"cpu.power": "#AABBCC"},
                   "colors": {"separator": "12ABEF"}},
            "2": {"font_weight": "invalid", "colors": {"text": "BAD"}},
            "3": {"font_weight": "bold"},
            "4": {"font_weight": "bold"},
        }}
        d = main.normalize(payload)
        self.assertEqual(sorted(d["style_presets"]), ["1", "2"])
        self.assertNotIn("3", d["style_presets"])
        self.assertIsNone(main.normalize({"style_presets": payload["style_presets"], "active_style": "3"})["active_style"])
        self.assertEqual(d["style_presets"]["1"]["token_weights"], {"cpu.power": "bold"})
        self.assertEqual(d["style_presets"]["1"]["token_colors"], {"cpu.power": "AABBCC"})
        self.assertFalse(d["style_presets"]["1"]["fps_bold"])
        self.assertEqual(d["style_presets"]["1"]["colors"]["separator"], "12ABEF")
        self.assertEqual(d["style_presets"]["2"]["font_weight"], "regular")
        self.assertEqual(d["style_presets"]["2"]["colors"]["text"], main.COLORS["text"])
        d["style_presets"]["1"]["token_weights"]["cpu.power"] = "light"
        self.assertEqual(main.normalize({})["style_presets"], {})

    def test_experimental_layer_manifest_is_explicit(self):
        from unittest.mock import patch
        import json
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            binary = root / "libMangoHud.so"
            binary.write_bytes(b"X" * 110000)
            manifest = root / "layers" / "ClawMetrics.x86_64.json"
            fallback = root / ".local/share/vulkan/explicit_layer.d/ClawMetrics.test3.x86_64.json"
            with patch.object(main, "BASE", root), patch.object(main, "user_home", return_value=root), patch.object(main, "experimental_library", return_value=binary), patch.object(main, "experimental_manifest", return_value=manifest), patch.object(main, "user_vulkan_manifest", return_value=fallback):
                main.install_native_manifest()
                layer = json.loads(manifest.read_text())["layer"]
                self.assertEqual(layer["name"], main.EXPERIMENTAL_LAYER_NAME)
                self.assertEqual(layer["name"], "VK_LAYER_CLAW_METRICS_overlay_x86_64")
                self.assertEqual(layer["library_path"], str(binary))
                self.assertEqual(layer, json.loads(fallback.read_text())["layer"])
                self.assertNotIn("enable_environment", layer)
                self.assertNotIn("disable_environment", layer)

    def test_corrupt_bundled_font_is_rejected(self):
        from unittest.mock import patch
        import base64, gzip
        with patch.object(Path, 'read_bytes', return_value=base64.b64encode(gzip.compress(b'wrong font'))):
            with self.assertRaisesRegex(ValueError, 'checksum'):
                main.install_font()

    def test_draw_has_no_game_runtime_python_dependency(self):
        config = main.mango_config(main.normalize({}))
        self.assertIn('exec=cat ', config)
        self.assertNotIn('/usr/bin/python3', config)

    def test_submetrics_and_hidden_group(self):
        d = main.normalize({'gpu': False, 'metrics': {'gpu_power': True}})
        c = main.mango_config(d)
        self.assertIn('gpu_power=0\n', c)
        self.assertIn('gpu_stats=0\n', c)
        self.assertIn('hud_compact=0\n', c)
        self.assertIn('battery_time=1\n', c)

    def test_draw_is_battery_discharge_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            b = Path(tmp) / 'BAT0'; b.mkdir()
            for name, value in {'type': 'Battery', 'status': 'Discharging', 'power_now': '24600000'}.items():
                (b/name).write_text(value)
            self.assertEqual(draw(Path(tmp)), 'DRAW 24.6W')
            (b/'status').write_text('Charging')
            self.assertEqual(draw(Path(tmp)), 'DRAW --')
            (b/'status').write_text('Discharging'); (b/'power_now').unlink()
            (b/'current_now').write_text('-2000000'); (b/'voltage_now').write_text('12000000')
            self.assertEqual(draw(Path(tmp)), 'DRAW 24.0W')


class BackendLifecycle(unittest.IsolatedAsyncioTestCase):
    async def test_host_draw_persistence_permissions_and_unload(self):
        from unittest.mock import patch
        import stat
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder) / 'ClawMetrics'
            with patch.object(main, 'BASE', base), patch.object(main, 'CONFIG', base/'settings.json'), patch.object(main, 'HUD', base/'MangoHud.conf'), patch.object(main, 'battery_draw', return_value='DRAW 24.6W'):
                plugin = main.Plugin()
                await plugin._main()
                try:
                    self.assertEqual(main.draw_path().read_text(), 'DRAW 24.6W\n')
                    self.assertTrue((await plugin.get_info())['font_ready'])
                    self.assertEqual(stat.S_IMODE(main.font_path().stat().st_mode), 0o644)
                    self.assertIn("font_file=" + main.sans_font("regular") + "\n", main.HUD.read_text())
                    self.assertEqual(stat.S_IMODE(main.draw_path().stat().st_mode), 0o644)
                    self.assertEqual(stat.S_IMODE(main.HUD.stat().st_mode), 0o644)
                    settings = await plugin.get_settings()
                    settings['order'].reverse()
                    settings['metrics']['gpu_junction_temp'] = True
                    await plugin.save_settings(settings)
                finally:
                    await plugin._unload()
                self.assertTrue(plugin._draw_task.cancelled())
                reloaded = main.Plugin()
                await reloaded._main()
                try:
                    self.assertEqual(await reloaded.get_settings(), settings)
                finally:
                    await reloaded._unload()
