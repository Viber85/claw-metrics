import copy
import importlib.util
import json
from pathlib import Path
import unittest
import main

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('modular_schema', ROOT / 'experiments/modular/schema.py')
schema = importlib.util.module_from_spec(spec)
spec.loader.exec_module(schema)


class ModularSchemaTests(unittest.TestCase):
    def setUp(self):
        self.layout = json.loads((ROOT / 'experiments/modular/two-rows.json').read_text())

    def test_devlab_presets_are_migrated_without_losing_fields(self):
        for name in ('two-rows', 'graph-focus'):
            original = json.loads((ROOT / ('experiments/modular/' + name + '.json')).read_text())
            migrated = schema.validate_layout(original)
            def strip_default_alignment(node):
                self.assertEqual(node.pop('selfAlign'), 'auto')
                for child in node['children']:
                    strip_default_alignment(child)
            strip_default_alignment(migrated['root'])
            self.assertEqual(migrated, original)

    def test_group_padding_removed_and_wide_spacing_retained(self):
        original = copy.deepcopy(self.layout)
        def update(node):
            if node['kind'] == 'group':node.update(padding=73, gap=240)
            for child in node['children']:update(child)
        update(original['root'])
        out = schema.validate_layout(original)
        def check(node):
            if node['kind'] == 'group':
                self.assertEqual(node['padding'], 0)
                self.assertEqual(node['gap'], 240)
            for child in node['children']:check(child)
        check(out['root'])
        self.assertEqual(original['root']['padding'], 73)
        self.assertEqual(schema.load_layout(json.dumps(out)), out)
        self.assertIn('240 0', schema.encode_native(out))
        original['root']['gap'] = 241
        with self.assertRaises(ValueError):schema.validate_layout(original)
        del original['root']['padding']
        original['root']['gap'] = 0
        self.assertEqual(schema.validate_layout(original)['root']['padding'], 0)

    def test_overlay_insets_roundtrip_and_invalid_limits(self):
        self.layout.update(paddingX=27,paddingY=13)
        out=schema.validate_layout(self.layout)
        self.assertEqual((out['paddingX'],out['paddingY']),(27,13))
        self.assertEqual(schema.load_layout(json.dumps(out)),out)
        self.assertEqual(schema.encode_native(out).splitlines()[2],'27 13')
        for invalid in (-1,161,True,float('inf')):
            with self.assertRaises(ValueError):schema.validate_layout({**self.layout,'paddingX':invalid})

    def test_group_padding_and_outline_persist_and_reject_bad_values(self):
        group=self.layout['root']['children'][0]
        group.update(paddingX=19,paddingY=7,outline=True,outlineWidth=4,outlineColor='#FFAACC',outlineOpacity=35)
        group['children'][0].update(paddingX=3,paddingY=4)
        out=schema.validate_layout(self.layout)
        self.assertEqual(out['root']['children'][0]['children'][0]['paddingX'],3)
        self.assertEqual(out['root']['children'][0]['children'][0]['paddingY'],4)
        for key in ('paddingX','paddingY','outline','outlineWidth','outlineColor','outlineOpacity'):
            self.assertEqual(out['root']['children'][0][key],group[key])
        self.assertEqual(schema.load_layout(json.dumps(out)),out)
        for key,bad in (('paddingX',161),('paddingY',-1),('outlineWidth',13),('outlineOpacity',101),('outlineColor','#xyz123')):
            broken=copy.deepcopy(self.layout);broken['root']['children'][0][key]=bad
            with self.assertRaises(ValueError):schema.validate_layout(broken)

    def test_input_is_not_mutated_or_referenced(self):
        out = schema.validate_layout(self.layout)
        out['root']['children'].clear()
        self.assertTrue(self.layout['root']['children'])

    def test_bad_geometry_and_duplicate_ids_rejected(self):
        for invalid in (True, float('nan'), float('inf'), -1, 2001, '50'):
            with self.subTest(invalid=invalid):
                value = copy.deepcopy(self.layout)
                value['x'] = invalid
                with self.assertRaises(ValueError): schema.validate_layout(value)
        self.layout['root']['children'][0]['id'] = self.layout['root']['id']
        with self.assertRaises(ValueError): schema.validate_layout(self.layout)

    def test_hidden_invalid_metric_is_still_rejected(self):
        item = self.layout['root']['children'][0]['children'][0]
        item.update(visible=False, token='arbitrary-config-line')
        with self.assertRaises(ValueError): schema.validate_layout(self.layout)

    def test_node_depth_and_count_limits(self):
        value = copy.deepcopy(self.layout)
        value['root']['children'] = []
        for index in range(96):
            child = copy.deepcopy(self.layout['root']['children'][0]['children'][0])
            child['id'] = str(index)
            value['root']['children'].append(child)
        with self.assertRaises(ValueError): schema.validate_layout(value)
        value = copy.deepcopy(self.layout)
        value['root']['children'] = []
        current = value['root']
        for index in range(9):
            child = copy.deepcopy(current)
            child.update(id='depth'+str(index), children=[])
            current['children'] = [child]
            current = child
        with self.assertRaises(ValueError): schema.validate_layout(value)

    def test_native_transport_preserves_fields_and_unicode_ids(self):
        self.layout['root']['id'] = 'čćž' * 20
        self.layout['root'].update(background='#112233', opacity=44, outline=True)
        text = schema.encode_native(self.layout)
        self.assertTrue(text.startswith('CLAW_MODULAR_V6\n'))
        self.assertIn(self.layout['root']['id'].encode().hex(), text)
        self.assertIn('112233 44 1', text)
        with self.assertRaises(ValueError): schema.encode_native({'schema': 'unknown'})

    def test_element_alignment_is_validated_and_persisted(self):
        child = self.layout['root']['children'][0]
        child['selfAlign'] = 'end'
        out = schema.validate_layout(self.layout)
        self.assertEqual(out['root']['children'][0]['selfAlign'], 'end')
        self.assertIn('CLAW_MODULAR_V6', schema.encode_native(out))
        child['selfAlign'] = 'diagonal'
        with self.assertRaises(ValueError): schema.validate_layout(self.layout)

    def test_separate_tdp_label_and_reading_roundtrip(self):
        doc=copy.deepcopy(self.layout)
        parent=doc['root']['children'][0]
        example=copy.deepcopy(parent['children'][0])
        label=copy.deepcopy(example);label.update(id='tdp-test-label',name='TDP label',token='tdp.label',fontWeight='light',color='#AA1133')
        reading=copy.deepcopy(example);reading.update(id='tdp-test-reading',name='TDP reading',token='tdp.reading',fontWeight='bold',color='#44DD22')
        parent['children'].extend((label,reading))
        normalized=schema.validate_layout(doc)
        self.assertEqual(normalized['root']['children'][0]['children'][-2]['token'],'tdp.label')
        self.assertEqual(normalized['root']['children'][0]['children'][-1]['token'],'tdp.reading')
        self.assertEqual(schema.load_layout(json.dumps(normalized)),normalized)
        encoded=schema.encode_native(normalized)
        self.assertIn('tdp.label',encoded)
        self.assertIn('tdp.reading',encoded)
        self.assertIn('AA1133',encoded)
        self.assertIn('44DD22',encoded)
        self.assertIn('tdp.label', (ROOT / 'claw_modular.py').read_text())

    def test_separator_is_validated_and_has_no_sensor_source(self):
        separator = copy.deepcopy(self.layout['root']['children'][0]['children'][0])
        separator.update(id='line', token='separator', name='Separator line', axis='column', width=18, height=2, color='#ABCDEF', cornerRadius=1, separatorOpacity=0)
        self.layout['root']['children'].append(separator)
        out = schema.validate_layout(self.layout)
        self.assertEqual(out['root']['children'][-1]['height'], 2)
        self.assertEqual(out['root']['children'][-1]['axis'], 'column')
        self.assertEqual(out['root']['children'][-1]['separatorOpacity'], 0)
        self.assertIn('separator', schema.encode_native(out))
        separator['separatorOpacity'] = 101
        with self.assertRaises(ValueError): schema.validate_layout(self.layout)
        separator['separatorOpacity'] = 0
        separator['height'] = 0
        with self.assertRaises(ValueError): schema.validate_layout(self.layout)

    def test_graph_can_match_its_vertical_parent_width(self):
        def find_graph(node):
            if node.get('kind') == 'metric' and node.get('token') == 'graph': return node
            for child in node.get('children', []):
                found = find_graph(child)
                if found: return found
        graph = find_graph(self.layout['root'])
        graph['width'] = 0
        out = schema.validate_layout(self.layout)
        self.assertEqual(find_graph(out['root'])['width'], 0)

    def test_only_graph_accepts_auto_width(self):
        item = self.layout['root']['children'][0]['children'][0]
        item.update(token='cpu.load', width=0)
        with self.assertRaises(ValueError): schema.validate_layout(self.layout)

    def test_modular_graph_style_uses_builder_choice_for_both_orientations(self):
        for orientation in ('horizontal', 'vertical'):
            settings = main.normalize({'modular_enabled': True, 'modular_layout': self.layout,
                                       'hud_orientation': orientation, 'graph_style': 'bars',
                                       'vertical_graph_style': 'smooth'})
            config = main.mango_config(settings, native_spacing=True)
            self.assertIn('claw_graph_style=2\n', config)
            self.assertNotIn('separator=1\n', config)

    def test_unknown_fields_do_not_become_renderer_parameters(self):
        self.layout['exec'] = 'ignored'
        self.layout['root']['unsupported'] = 'ignored'
        out = schema.validate_layout(self.layout)
        self.assertNotIn('exec', out)
        self.assertNotIn('unsupported', out['root'])
        with self.assertRaises(ValueError): schema.load_layout(' ' * (1024 * 1024 + 1))

    def test_center_edge_anchors_preserve_signed_offsets_and_old_ids(self):
        self.assertEqual(schema.ANCHORS[:6], ('top-left','top-center','top-right','bottom-left','bottom-center','bottom-right'))
        for index, anchor in enumerate(('center-left','center-right'),6):
            for offset in (-40,0,40):
                doc=copy.deepcopy(self.layout);doc.update(anchor=anchor,y=offset)
                out=schema.load_layout(json.dumps(doc))
                self.assertEqual(out['y'],offset)
                self.assertEqual(schema.encode_native(out).splitlines()[1].split()[0],str(index))
                settings=main.normalize({'modular_enabled':True,'modular_layout':out,'style_presets':{'1':{'modular_enabled':True,'modular_layout':out}}})
                self.assertEqual(settings['modular_layout'],out)
                self.assertEqual(settings['style_presets']['1']['modular_layout'],out)
        bad=copy.deepcopy(self.layout);bad.update(anchor='top-left',y=-1)
        with self.assertRaises(ValueError):schema.validate_layout(bad)


class ElementAppearanceTests(unittest.TestCase):
    def test_radius_and_weight_survive_roundtrip_and_reject_invalid_values(self):
        doc=schema.load_layout((ROOT/'assets/modular/vertical.json').read_text())
        group=doc['root']['children'][0];group.update(cornerRadius=1000,fontWeight='light')
        reading=group['children'][0];reading['fontWeight']='bold'
        result=schema.validate_layout(doc)
        self.assertEqual(result,doc)
        self.assertIn('1000 1',schema.encode_native(result))
        self.assertEqual(schema.load_layout(json.dumps(result)),result)
        for key,value in [('cornerRadius',-1),('cornerRadius',1001),('fontWeight','heavy'),('fontWeight',4)]:
            broken=copy.deepcopy(doc);broken['root']['children'][0][key]=value
            with self.assertRaises(ValueError):schema.validate_layout(broken)
