import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import main


class EditorStyleSave(unittest.IsolatedAsyncioTestCase):
    async def test_draft_style_persists_without_touching_live_renderer(self):
        plugin=main.Plugin()
        layout=json.loads((Path(main.__file__).parent/'assets/modular/horizontal.json').read_text())
        current=main.normalize({'modular_layout':layout,'modular_enabled':False,'opacity':80})
        plugin._current_settings=current
        draft=json.loads(json.dumps(layout));draft['root']['name']='Saved editor draft'
        def graph(node):
            if node['token']=='graph':return node
            for child in node['children']:
                found=graph(child)
                if found is not None:return found
        graph(draft['root'])['color']='#FF00FF'
        preset={'version':3,'modular_layout':draft,'modular_enabled':True,'opacity':55,
                'token_colors':{'tdp.label':'FFAC12','tdp.value':'DDEEFF'}}
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'settings.json'
            with patch.object(main,'BASE',Path(directory)),patch.object(main,'CONFIG',target),patch.object(main,'publish_modular') as publish,patch.object(main,'mango_config') as config,patch.object(main,'install_native_manifest') as install:
                result=await plugin.save_style_settings({**current,'style_presets':{'2':preset},'style_names':{'2':'From editor'},'modular_enabled':True,'opacity':55})
                self.assertTrue(result['ok'])
                publish.assert_not_called();config.assert_not_called();install.assert_not_called()
                saved=await main.Plugin().get_settings()
            self.assertEqual(saved['style_names']['2'],'From editor')
            self.assertEqual(saved['style_presets']['2']['modular_layout']['root']['name'],'Saved editor draft')
            self.assertEqual(saved['style_presets']['2']['opacity'],55)
            self.assertEqual(graph(saved['style_presets']['2']['modular_layout']['root'])['color'],'#FF00FF')
            self.assertEqual(saved['modular_layout'],current['modular_layout'])
            self.assertEqual(saved['opacity'],80)
            self.assertFalse(saved['modular_enabled'])
            self.assertEqual(current['style_presets'],{})

    async def test_failed_disk_save_does_not_claim_success_or_mutate_current(self):
        plugin=main.Plugin();plugin._current_settings=main.normalize({})
        before=plugin._current_settings
        with patch.object(main,'write_atomic',side_effect=OSError('disk unavailable')):
            with self.assertRaises(OSError):
                await plugin.save_style_settings({'style_presets':{'1':{}},'style_names':{'1':'Retry'}})
        self.assertIs(plugin._current_settings,before)
