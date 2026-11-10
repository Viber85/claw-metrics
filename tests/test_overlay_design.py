"""Portable design boundary and safe preview/backup behavior."""
import asyncio
import copy
import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch
import main
from claw_design import export_design, load_design

ROOT = pathlib.Path(__file__).resolve().parents[1]

class OverlayDesignTests(unittest.TestCase):
    def setUp(self):
        self.layout = json.loads((ROOT/'assets/modular/horizontal.json').read_text())
        self.settings = main.normalize({'modular_layout':self.layout,'modular_enabled':True,'fontsize':24,'colors':{'time':'112233'},'token_weights':{'cpu.temp':'bold'}})
    def test_complete_round_trip(self):
        value = load_design(json.dumps(export_design(self.settings)))
        self.assertEqual(value['appearance']['fontsize'],24)
        self.assertEqual(value['appearance']['token_weights']['cpu.temp'],'bold')
        self.assertEqual(value['appearance']['colors']['time'],'112233')
        self.assertEqual(export_design(main.normalize({**self.settings,**value['appearance'],'modular_layout':value['layout']})),value)
    def test_legacy_keeps_device_appearance(self):
        self.assertEqual(load_design(json.dumps(self.layout))['appearance'],{})
    def test_rejects_malformed_and_future_versions(self):
        good=export_design(self.settings)
        for field,value in [('version',2),('appearance',None),('layout',{})]:
            bad=copy.deepcopy(good);bad[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):load_design(json.dumps(bad))
        for key,value in [('fontsize',float('nan')),('opacity',101),('sans',1),('colors',{'text':'bad'}),('token_weights',{'fps.value':'heavy'}),('custom_labels',{'cpu':'CPU\nhud=0'})]:
            bad=copy.deepcopy(good);bad['appearance'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):load_design(json.dumps(bad))
        with self.assertRaises(ValueError):load_design(' '* (1024*1024+1))
    def test_only_visual_settings_imported(self):
        value=export_design({**self.settings,'command':'oops','config_path':'/tmp/x','enabled':False,'style_presets':{'1':{}}})
        for key in ('command','config_path','enabled','style_presets'):
            self.assertNotIn(key,value['appearance'])
    def test_import_is_read_only_and_commit_preserves_previous(self):
        async def run(folder):
            plugin=main.Plugin();plugin._current_settings=copy.deepcopy(self.settings)
            draft=copy.deepcopy(self.settings);draft['fontsize']=26
            source=folder/'import.json';source.write_text(json.dumps(export_design(draft)))
            parsed=await plugin.import_overlay_design(str(source))
            self.assertEqual(plugin._current_settings['fontsize'],24)
            self.assertFalse((folder/'overlay-design-previous.json').exists())
            with patch.object(main,'BASE',folder),patch.object(main,'CONFIG',folder/'settings.json'),patch.object(main,'HUD',folder/'hud.conf'),patch.object(main,'draw_path',return_value=folder/'draw'),patch.object(main,'tdp_path',return_value=folder/'tdp'),patch.object(main,'draw_text',return_value='DRAW'),patch.object(main,'native_renderer_available',return_value=False):
                await plugin.save_settings({**self.settings,**parsed['appearance'],'modular_layout':parsed['layout']})
                before=await plugin.get_previous_overlay_design()
                self.assertEqual(before['fontsize'],24)
                backup=(folder/'overlay-design-previous.json').read_text()
                await plugin.save_settings(plugin._current_settings)
                self.assertEqual((folder/'overlay-design-previous.json').read_text(),backup)
                await plugin.save_settings({**plugin._current_settings,**before})
                self.assertEqual(plugin._current_settings['fontsize'],24)
                self.assertEqual((await plugin.get_previous_overlay_design())['fontsize'],26)
        with tempfile.TemporaryDirectory() as folder:asyncio.run(run(pathlib.Path(folder)))
