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
        self.assertEqual(len(main.TOKEN_SLOTS), 27)
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
        self.assertEqual(len(weights), 27)
        self.assertEqual(len(colors), 27)
        for slot, weight in d["token_weights"].items():
            self.assertEqual(weights[main.TOKEN_SLOTS.index(slot)], main.FONT_DIGITS[weight])
        self.assertEqual(colors[main.TOKEN_SLOTS.index("cpu.temp")], "FFAC12")
        self.assertEqual(colors[main.TOKEN_SLOTS.index("gpu.load")], "00BBEE")
        self.assertEqual(colors[main.TOKEN_SLOTS.index("fps.value")], "------")
        stock = main.mango_config(d)
        self.assertNotIn("claw_weight_map=", stock)
        self.assertNotIn("claw_color_map=", stock)

    def test_style_presets_validate_before_reuse(self):
        payload = {"style_presets": {
            "1": {"font_weight": "semibold", "fps_bold": False,
                   "token_weights": {"cpu.power": "bold", "bogus": "bold"},
                   "token_colors": {"cpu.power": "#AABBCC"},
                   "colors": {"separator": "12ABEF"}},
            "2": {"font_weight": "invalid", "colors": {"text": "BAD"}},
            "4": {"font_weight": "bold"},
        }}
        d = main.normalize(payload)
        self.assertEqual(sorted(d["style_presets"]), ["1", "2"])
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
