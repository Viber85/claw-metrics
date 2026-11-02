import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('modular_schema', ROOT / 'experiments/modular/schema.py')
schema = importlib.util.module_from_spec(spec)
spec.loader.exec_module(schema)


class ModularSchemaTests(unittest.TestCase):
    def setUp(self):
        self.layout = json.loads((ROOT / 'experiments/modular/two-rows.json').read_text())

    def test_devlab_presets_are_accepted_without_changes(self):
        for name in ('two-rows', 'graph-focus'):
            original = json.loads((ROOT / ('experiments/modular/' + name + '.json')).read_text())
            self.assertEqual(schema.validate_layout(original), original)

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
        self.assertTrue(text.startswith('CLAW_MODULAR_V1\n'))
        self.assertIn(self.layout['root']['id'].encode().hex(), text)
        self.assertIn('112233 44 1', text)
        with self.assertRaises(ValueError): schema.encode_native({'schema': 'unknown'})

    def test_unknown_fields_do_not_become_renderer_parameters(self):
        self.layout['exec'] = 'ignored'
        self.layout['root']['unsupported'] = 'ignored'
        out = schema.validate_layout(self.layout)
        self.assertNotIn('exec', out)
        self.assertNotIn('unsupported', out['root'])
        with self.assertRaises(ValueError): schema.load_layout(' ' * (1024 * 1024 + 1))
