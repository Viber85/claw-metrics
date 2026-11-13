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

    def test_legacy_group_padding_migrates_in_layout_and_saved_styles(self):
        doc = json.loads((ROOT/'assets/modular/two-rows.json').read_text())
        def update(node):
            if node['kind'] == 'group':node.update(padding=61, gap=240)
            for child in node['children']:update(child)
        update(doc['root'])
        settings = {'modular_enabled':True, 'modular_layout':doc}
        result = main.normalize({**settings,'style_presets':{'1':settings}})
        for layout in (result['modular_layout'],result['style_presets']['1']['modular_layout']):
            self.assertEqual(layout['root']['padding'],0)
            self.assertEqual(layout['root']['gap'],240)
            self.assertEqual(modular.load_layout(json.dumps(layout)),layout)
        self.assertEqual(main.normalize(result),result)
        self.assertEqual(doc['root']['padding'],61)
        self.assertTrue(result['modular_enabled'])
        self.assertIn('240 0',modular.encode_native(result['modular_layout']))

    def test_overlay_insets_and_pill_roundtrip_in_saved_styles(self):
        doc={**self.doc,'paddingX':27,'paddingY':13}
        payload={'modular_enabled':True,'modular_layout':doc,'rounding':1000}
        value=main.normalize({**payload,'style_presets':{'1':payload}})
        self.assertEqual(value['modular_layout'],doc)
        self.assertEqual(value['rounding'],1000)
        self.assertEqual(value['style_presets']['1']['modular_layout'],doc)
        self.assertEqual(value['style_presets']['1']['rounding'],1000)
        self.assertEqual(main.normalize(value),value)
        self.assertIn('round_corners=1000',main.mango_config(value,True))

    def test_group_outline_and_insets_roundtrip_with_saved_styles(self):
        doc=copy.deepcopy(self.doc)
        doc['root']['children'][0].update(paddingX=19,paddingY=7,outline=True,outlineWidth=4,outlineColor='#FFAACC',outlineOpacity=35)
        payload={'modular_enabled':True,'modular_layout':doc}
        result=main.normalize({**payload,'style_presets':{'1':payload}})
        self.assertEqual(result['modular_layout'],doc)
        self.assertEqual(result['style_presets']['1']['modular_layout'],doc)
        self.assertEqual(main.normalize(result),result)

    def test_element_radius_and_weight_in_saved_style(self):
        doc=copy.deepcopy(self.doc);doc['root']['fontWeight']='light'
        group=doc['root']['children'][0];group.update(cornerRadius=1000,fontWeight='semibold')
        group['children'][0]['fontWeight']='bold'
        payload={'modular_enabled':True,'modular_layout':doc}
        settings=main.normalize({**payload,'style_presets':{'1':payload}})
        self.assertEqual(settings['modular_layout'],doc)
        self.assertEqual(settings['style_presets']['1']['modular_layout'],doc)
        self.assertEqual(main.normalize(settings),settings)

    def test_unit_superscript_defaults_and_style_roundtrip(self):
        self.assertFalse(main.normalize({})['unit_superscript'])
        raw={'modular_enabled':True,'modular_layout':self.doc,'unit_superscript':True,
             'style_presets':{'1':{'unit_superscript':True},'2':{'unit_superscript':'yes'}}}
        saved=main.normalize(raw)
        self.assertTrue(saved['unit_superscript'])
        self.assertTrue(saved['style_presets']['1']['unit_superscript'])
        self.assertNotIn('unit_superscript',saved['style_presets']['2'])
        self.assertIn('claw_unit_superscript=1\n',main.mango_config(saved,native_spacing=True))
        self.assertNotIn('claw_unit_superscript=',main.mango_config(saved,native_spacing=False))
        self.assertEqual(main.normalize(saved),saved)

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
        for name,axis in (('horizontal','row'),('vertical','column')):
            expected=modular.load_layout((ROOT/f'assets/modular/{name}.json').read_text())
            self.assertEqual(await plugin.get_modular_preset(name),expected)
            self.assertEqual(expected['root']['axis'],axis)
        with self.assertRaises(ValueError):await plugin.get_modular_preset('two-rows')
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

    def test_live_style_state_flag_tracks_apply_without_restarting_game(self):
        # A game may be launched with Classic selected. Its experimental HUD
        # must already know where future modular documents are published.
        native=main.mango_config({'modular_enabled':False,'modular_layout':self.doc},native_spacing=True)
        self.assertIn('claw_modular_file='+str(main.BASE/'modular.layout')+chr(10),native)
        self.assertNotIn('claw_modular_file=',main.mango_config({'modular_enabled':False,'modular_layout':self.doc}))
        with tempfile.TemporaryDirectory() as directory,patch.object(main,'BASE',Path(directory)):
            flag=Path(directory)/'modular.layout.enabled'
            doc=copy.deepcopy(self.doc)
            main.publish_modular({'modular_layout':doc,'modular_enabled':False})
            self.assertEqual(flag.read_text(),'0\n')
            self.assertTrue((Path(directory)/'modular.layout').is_file())
            main.publish_modular({'modular_layout':doc,'modular_enabled':True})
            self.assertEqual(flag.read_text(),'1\n')
            doc['root']['name']='Live after Apply'
            main.publish_modular({'modular_layout':doc,'modular_enabled':True})
            self.assertEqual(flag.read_text(),'1\n')
            self.assertEqual((Path(directory)/'modular-layout-backup.json').is_file(),True)
            main.publish_modular({'modular_layout':doc,'modular_enabled':False})
            self.assertEqual(flag.read_text(),'0\n')

    async def test_apply_activates_file_but_draft_style_does_not(self):
        plugin=main.Plugin()
        with tempfile.TemporaryDirectory() as directory,patch.object(main,'BASE',Path(directory)),patch.object(main,'CONFIG',Path(directory)/'settings.json'),patch.object(main,'HUD',Path(directory)/'MangoHud.conf'),patch.object(main,'native_renderer_available',return_value=False):
            inactive=main.normalize({'modular_layout':self.doc,'modular_enabled':False})
            plugin._current_settings=inactive
            main.publish_modular(inactive)
            flag=Path(directory)/'modular.layout.enabled'
            self.assertEqual(flag.read_text(),'0\n')
            draft=copy.deepcopy(self.doc)
            draft['root']['name']='Saved named style'
            style={'version':3,'modular_enabled':True,'modular_layout':draft}
            result=await plugin.save_style_settings({**inactive,'style_presets':{'2':style},'style_names':{'2':'Custom'}})
            self.assertTrue(result['ok'])
            self.assertEqual(flag.read_text(),'0\n','Save style alone must not activate the running HUD')
            activated=await plugin.save_settings({**inactive,'modular_enabled':True,'modular_layout':draft,'active_style':'2','style_presets':{'2':style},'style_names':{'2':'Custom'}})
            self.assertTrue(activated['ok'])
            self.assertEqual(flag.read_text(),'1\n')
            self.assertEqual((Path(directory)/'modular-layout-backup.json').is_file(),True)
            self.assertEqual(main.normalize(json.loads((Path(directory)/'settings.json').read_text()))['modular_layout']['root']['name'],'Saved named style')

    def test_invalid_layout_is_rejected_before_settings_save(self):
        broken=copy.deepcopy(self.doc);broken['root']['children'][0]['id']=broken['root']['id']
        with self.assertRaises(ValueError):main.normalize({'modular_layout':broken,'modular_enabled':True})
