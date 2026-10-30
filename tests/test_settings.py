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
