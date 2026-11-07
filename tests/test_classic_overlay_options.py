import copy
import unittest
import main

class ClassicOverlayOptions(unittest.TestCase):
    def test_classic_options_roundtrip_in_both_orientations_and_styles(self):
        for orientation in ('horizontal','vertical'):
            for edge in ('center-left','center-right'):
                raw={'hud_orientation':orientation,'hud_position':edge,'unit_superscript':True,
                     'group_gap_x':24,'vertical_category_gap':14,'offset_x':16,'offset_y':-25}
                saved=main.normalize({**raw,'style_presets':{'1':copy.deepcopy(raw)}})
                self.assertEqual(main.normalize(saved),saved)
                for key in raw:self.assertEqual(saved['style_presets']['1'][key],raw[key])
                config=main.mango_config(saved,native_spacing=True)
                self.assertIn('claw_unit_superscript=1\n',config)
                self.assertIn('claw_center_vertical=1\n',config)
                self.assertIn('claw_group_gap_x=24\n',config)
                self.assertIn('position='+('top-left' if edge.endswith('left') else 'top-right')+'\n',config)
                self.assertIn('offset_x='+('16' if edge.endswith('left') else '-16')+'\n',config)
                self.assertIn('offset_y=-25\n',config)
                self.assertIn('hud_compact=0\n',config)
                fallback=main.mango_config(saved,native_spacing=False)
                for name in ('claw_unit_superscript','claw_center_vertical','claw_group_gap_x'):
                    self.assertNotIn(name+'=',fallback)

    def test_existing_spacing_and_anchor_defaults_are_preserved(self):
        old=main.normalize({'table_gap':7,'inner_gap':9,'vertical_category_gap':12})
        self.assertEqual(old['group_gap_x'],0)
        self.assertEqual((old['table_gap'],old['inner_gap'],old['vertical_category_gap']),(7,9,12))
        self.assertFalse(old['unit_superscript'])
        self.assertEqual(main.normalize({'group_gap_x':999})['group_gap_x'],60)
        self.assertEqual(main.normalize({'group_gap_x':-10})['group_gap_x'],0)
