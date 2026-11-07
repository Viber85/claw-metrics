import unittest
import main


class TdpStyles(unittest.TestCase):
    def test_independent_tdp_styles_survive_settings_and_presets(self):
        styles={'token_colors':{'tdp.label':'FFAC12','tdp.value':'DDEEFF'},
                'token_weights':{'tdp.label':'bold','tdp.value':'light'}}
        normalized=main.normalize({**styles,'style_presets':{'1':styles}})
        for key in styles:
            self.assertEqual(normalized[key],styles[key])
            self.assertEqual(normalized['style_presets']['1'][key],styles[key])
        config=dict(line.split('=',1) for line in main.mango_config(normalized,True).splitlines() if '=' in line)
        colors=config['claw_color_map'].split(':');weights=config['claw_weight_map']
        self.assertEqual(main.TOKEN_SLOTS[27],'tdp.value')
        self.assertEqual(main.TOKEN_SLOTS[32],'tdp.label')
        self.assertEqual((colors[32],colors[27]),('FFAC12','DDEEFF'))
        self.assertEqual((weights[32],weights[27]),('4','1'))
        changed=main.normalize({**normalized,'token_colors':{'tdp.label':'00FF00','tdp.value':'DDEEFF'}})
        self.assertEqual(changed['token_colors']['tdp.value'],'DDEEFF')

    def test_old_value_overrides_keep_their_original_token(self):
        old=main.normalize({'token_colors':{'tdp.value':'ABCDEF'},'token_weights':{'tdp.value':'semibold'}})
        self.assertEqual(old['token_colors'],{'tdp.value':'ABCDEF'})
        self.assertEqual(old['token_weights'],{'tdp.value':'semibold'})
        config=dict(line.split('=',1) for line in main.mango_config(old,True).splitlines() if '=' in line)
        self.assertEqual(config['claw_color_map'].split(':')[32],old['colors']['tdp'])
        self.assertEqual(config['claw_weight_map'][32],'0')
