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

    def test_floating_hud_is_centered_and_not_stretched(self):
        config = main.mango_config(main.normalize({'margin': 24}))
        self.assertIn('offset_x=0\n', config)
        self.assertIn('offset_y=24\n', config)
        self.assertIn('horizontal_stretch=0\n', config)
        self.assertIn('position=top-center\n', config)
        self.assertIn('hud_compact=0\n', config)
        self.assertIn('round_corners=10\n', config)

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
