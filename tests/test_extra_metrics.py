import unittest
import main

KEYS=('fps_average','fps_low1','ram_game','ram_swap')
class ExtraMetricsTests(unittest.TestCase):
    def test_migration_defaults_and_style_roundtrip(self):
        old=main.normalize({'fontsize':24,'style_presets':{'1':{'version':3,'metrics':{'cpu_power':False}}}})
        for key in KEYS:
            self.assertFalse(old['metrics'][key])
        self.assertNotIn('fps_average',old['style_presets']['1']['metrics'])
        data=main.normalize({'metrics':{k:True for k in KEYS},
            'style_presets':{'1':{'version':3,'metrics':{k:True for k in KEYS}}}})
        for key in KEYS:
            self.assertTrue(data['metrics'][key])
            self.assertTrue(data['style_presets']['1']['metrics'][key])

    def test_private_config_flags_and_hidden_groups(self):
        for orientation in ('horizontal','vertical'):
            data=main.normalize({'hud_orientation':orientation,'metrics':{k:True for k in KEYS}})
            cfg=main.mango_config(data,native_spacing=True)
            for option in ('claw_fps_average','claw_fps_low1','claw_ram_game','swap'):
                self.assertIn(option+'=1\n',cfg)
            hidden=main.mango_config(main.normalize({**data,'fps':False,'ram':False}),native_spacing=True)
            for option in ('claw_fps_average','claw_fps_low1','claw_ram_game','swap'):
                self.assertIn(option+'=0\n',hidden)
            self.assertNotIn('claw_fps_average=',main.mango_config(data))
            self.assertIn('hud_compact=0\n',cfg)

    def test_append_only_font_color_token_migration(self):
        self.assertEqual(main.TOKEN_SLOTS[27],'tdp.value')
        self.assertEqual(main.TOKEN_SLOTS[28:],['fps.average','fps.low1','ram.game','ram.swap'])
        data=main.normalize({'token_weights':{'fps.average':'bold','ram.game':'light'},
                             'token_colors':{'fps.low1':'AA1122','ram.swap':'00FF00'}})
        cfg=main.mango_config(data,native_spacing=True)
        options=dict(line.split('=',1) for line in cfg.splitlines() if '=' in line)
        self.assertEqual(options['claw_weight_map'][28],'4')
        self.assertEqual(options['claw_weight_map'][30],'1')
        self.assertEqual(options['claw_color_map'].split(':')[29],'AA1122')
        self.assertEqual(options['claw_color_map'].split(':')[31],'00FF00')
