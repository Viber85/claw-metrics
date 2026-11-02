import unittest
import main

class BackgroundTests(unittest.TestCase):
    def test_legacy_settings_and_styles_keep_existing_appearance(self):
        data=main.normalize({})
        self.assertEqual(data['background']['mode'],'solid')
        self.assertEqual(data['background']['color'],'161820')
        data['background']['stops'][0]['color']='000000'
        self.assertEqual(main.normalize({})['background']['stops'][0]['color'],'101A2C')
        old=main.normalize({'style_presets':{'1':{'colors':{}}}})
        self.assertNotIn('background',old['style_presets']['1'])

    def test_background_validation_and_style_roundtrip(self):
        bg={'mode':'radial','color':'#aabbcc','radius':999,'center_x':-10,'angle':-20,
            'stops':[{'position':100,'color':'ff0000'},{'position':0,'color':'00ff00'},
                     {'position':30,'color':'evil=code'},{'position':True,'color':'FFFFFF'}]}
        data=main.normalize({'background':bg,'style_presets':{'1':{'background':bg}}})
        self.assertEqual(data['background']['color'],'AABBCC')
        self.assertEqual(data['background']['radius'],200)
        self.assertEqual(data['background']['center_x'],0)
        self.assertEqual([s['position'] for s in data['background']['stops']],[0,100])
        self.assertEqual(data['background'],data['style_presets']['1']['background'])
        self.assertEqual(main.normalize_background({'stops':[]})['stops'],main.BACKGROUND_DEFAULT['stops'])

    def test_native_config_and_solid_stock_fallback(self):
        data=main.normalize({'background':{'mode':'linear','color':'112233','angle':45},'opacity':37})
        native=main.mango_config(data,native_spacing=True)
        self.assertIn('claw_background_mode=1\n',native)
        self.assertIn('claw_background_angle=45\n',native)
        self.assertIn('background_alpha=0.37\n',native)
        self.assertIn('claw_background_stops=0:101A2C/100:30204D\n',native)
        stock=main.mango_config(data)
        self.assertIn('background_color=112233\n',stock)
        self.assertNotIn('claw_background_',stock)

    def test_outline_migration_validation_and_style_persistence(self):
        self.assertFalse(main.normalize({'background':{'mode':'radial'}})['background']['outline_enabled'])
        outline={'outline_enabled':True,'outline_color':'#a1b2c3','outline_width':99,'outline_opacity':-20}
        data=main.normalize({'background':outline,'style_presets':{'1':{'background':outline}}})
        b=data['background']
        self.assertEqual(b['outline_color'],'A1B2C3')
        self.assertEqual(b['outline_width'],6)
        self.assertEqual(b['outline_opacity'],0)
        self.assertEqual(b,data['style_presets']['1']['background'])
        self.assertFalse(main.normalize_background({'outline_enabled':1})['outline_enabled'])
        self.assertEqual(main.normalize_background({'outline_color':'bad=code'})['outline_color'],'6B7E99')

    def test_outline_is_independent_of_fill_and_native_only(self):
        data=main.normalize({'opacity':0,'background':{'outline_enabled':True,'outline_color':'AABBCC','outline_width':3,'outline_opacity':60}})
        cfg=main.mango_config(data,native_spacing=True)
        for line in ('background_alpha=0.0','claw_outline_enabled=1','claw_outline_color=AABBCC','claw_outline_width=3','claw_outline_opacity=60'):
            self.assertIn(line+'\n',cfg)
        self.assertNotIn('claw_outline_',main.mango_config(data))
