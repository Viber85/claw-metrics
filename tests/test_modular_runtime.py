import asyncio
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import main
import claw_modular as modular

ROOT=Path(__file__).resolve().parents[1]
class ModularRuntimeTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.doc=modular.load_layout((ROOT/'assets/modular/two-rows.json').read_text())

    def test_schema_and_packaged_presets_match_development_contract(self):
        self.assertEqual((ROOT/'claw_modular.py').read_bytes(),(ROOT/'experiments/modular/schema.py').read_bytes())
        for name in ('two-rows','graph-focus'):
            self.assertEqual((ROOT/f'assets/modular/{name}.json').read_bytes(),(ROOT/f'experiments/modular/{name}.json').read_bytes())

    def test_legacy_settings_and_styles_keep_legacy_renderer(self):
        self.assertFalse(main.normalize({})['modular_enabled'])
        self.assertFalse(main.normalize({'modular_enabled':True})['modular_enabled'])
        styles=main.normalize({'style_presets':{'1':{'colors':{'text':'ABCDEF'}}}})['style_presets']
        self.assertFalse(styles['1']['modular_enabled'])

    def test_modular_style_roundtrip_and_deep_copy(self):
        saved={'modular_enabled':True,'modular_layout':self.doc}
        d=main.normalize({**saved,'style_presets':{'1':saved}})
        self.assertEqual(d['modular_layout'],self.doc)
        self.assertEqual(d['style_presets']['1']['modular_layout'],self.doc)
        self.assertTrue(d['style_presets']['1']['modular_enabled'])
        self.assertEqual(main.normalize(d),d)
        d['modular_layout']['root']['children'].clear()
        self.assertTrue(self.doc['root']['children'])
        self.assertTrue(d['style_presets']['1']['modular_layout']['root']['children'])

    def test_modular_tree_requests_its_sources_without_mutating_settings(self):
        raw={'modular_enabled':True,'modular_layout':self.doc,'cpu':False,'gpu':False,'tdp':False,'draw':False}
        before=copy.deepcopy(raw)
        config=main.mango_config(raw,native_spacing=True)
        self.assertIn('claw_modular_file='+str(main.BASE/'modular.layout')+'\n',config)
        self.assertIn('cpu_stats=1\n',config)
        self.assertIn('gpu_stats=1\n',config)
        self.assertIn('tdp.txt',config)
        self.assertEqual(raw,before)
        self.assertNotIn('claw_modular_file=',main.mango_config(raw))

    async def test_presets_import_export_and_invalid_import_preserve_file(self):
        plugin=main.Plugin()
        self.assertEqual(await plugin.get_modular_preset('two-rows'),self.doc)
        with self.assertRaises(ValueError):await plugin.get_modular_preset('../bad')
        with tempfile.TemporaryDirectory() as directory,patch.object(main,'BASE',Path(directory)):
            incoming=Path(directory)/'incoming.json';incoming.write_text(json.dumps(self.doc))
            self.assertEqual(await plugin.import_modular_layout(str(incoming)),self.doc)
            main.publish_modular({'modular_layout':self.doc})
            native=Path(directory)/'modular.layout';before=native.read_bytes()
            plugin._current_settings=main.normalize({'modular_layout':self.doc,'modular_enabled':True})
            result=await plugin.export_modular_layout(self.doc)
            self.assertEqual(modular.load_layout(Path(result['path']).read_text()),self.doc)
            incoming.write_text('{broken')
            with self.assertRaises(ValueError):await plugin.import_modular_layout(str(incoming))
            self.assertEqual(native.read_bytes(),before)
            self.assertEqual(plugin._current_settings['modular_layout'],self.doc)
            with self.assertRaises(ValueError):await plugin.import_modular_layout(directory)

    def test_invalid_layout_is_rejected_before_settings_save(self):
        broken=copy.deepcopy(self.doc);broken['root']['children'][0]['id']=broken['root']['id']
        with self.assertRaises(ValueError):main.normalize({'modular_layout':broken,'modular_enabled':True})
