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


if __name__ == '__main__':
    unittest.main()
