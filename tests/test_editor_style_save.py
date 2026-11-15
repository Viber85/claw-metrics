import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import main


class EditorStyleSave(unittest.IsolatedAsyncioTestCase):
    async def test_live_save_skips_identical_files_and_repairs_unreadable_config(self):
        plugin = main.Plugin()
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            base = home / '.config/ClawMetrics'
            config = base / 'settings.json'
            hud = base / 'MangoHud.conf'
            settings = main.normalize({'offset_x': 20})
            with patch.object(main, 'BASE', base), patch.object(main, 'CONFIG', config), \
                 patch.object(main, 'HUD', hud), patch.object(main, 'user_home', return_value=home), \
                 patch.object(main, 'native_renderer_available', return_value=True), \
                 patch.object(main, 'draw_text', return_value='DRAW --'), \
                 patch.object(main, 'write_atomic', wraps=main.write_atomic) as write:
                await plugin.save_settings(settings)
                write.reset_mock()
                await plugin.save_settings(settings)
                write.assert_not_called()

                framegen_config = main.native_framegen_hud_path()
                framegen_config.chmod(0o600)
                await plugin.save_settings(settings)
                self.assertEqual([call.args[0] for call in write.call_args_list], [framegen_config])
                self.assertEqual(framegen_config.stat().st_mode & 0o777, 0o644)

                write.reset_mock()
                changed = await plugin.save_settings({**settings, 'offset_x': 21, 'opacity': 70})
                self.assertTrue(changed['ok'])
                previous = base / 'overlay-design-previous.json'
                self.assertCountEqual([call.args[0] for call in write.call_args_list], [
                    previous, config, hud, main.native_hud_path(), framegen_config,
                ])
                self.assertEqual(json.loads(previous.read_text())['offset_x'], 20)
                self.assertEqual(json.loads(config.read_text())['offset_x'], 21)
                self.assertIn('offset_x=21\n', framegen_config.read_text())

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
