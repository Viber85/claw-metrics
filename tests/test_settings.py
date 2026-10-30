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
                    self.assertIn(str(main.font_path()), main.HUD.read_text())
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
