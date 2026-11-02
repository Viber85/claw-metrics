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
