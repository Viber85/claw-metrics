import hashlib,json,tempfile,unittest
from pathlib import Path
import main
import claw_renderer


class NativeBundle(unittest.TestCase):
    def fixture(self, folder):
        source=Path(folder)/'assets';source.mkdir()
        checks={}
        for relative,cls in claw_renderer.EXPECTED.items():
            data=b'\x7fELF'+bytes([cls])+b'\0'*1100
            path=source/relative;path.parent.mkdir(exist_ok=True);path.write_bytes(data)
            checks[relative]=hashlib.sha256(data).hexdigest()
        (source/'index.json').write_text(json.dumps({'version':'claw-native-1','files':checks}))
        return source

    def test_private_install_aliases_and_wrapper(self):
        with tempfile.TemporaryDirectory() as folder:
            source=self.fixture(folder);base=Path(folder)/'profile'
            ready,_=claw_renderer.install(base,source)
            self.assertTrue(ready)
            self.assertEqual((base/'renderer/lib64/libMangoHud.so').read_bytes(),(source/'x86_64/libMangoHud.so').read_bytes())
            self.assertEqual((base/'renderer/lib/i386-linux-gnu/libMangoHud.so').read_bytes(),(source/'i386/libMangoHud.so').read_bytes())
            self.assertEqual((base/'renderer/lib/libMangoHud.so').read_bytes(),(source/'i386/libMangoHud.so').read_bytes())
            manifest=json.loads((base/'renderer/layers/ClawMetrics.json').read_text())
            self.assertIn('$LIB',manifest['layer']['library_path'])
            self.assertEqual(manifest['layer']['name'],claw_renderer.LAYER)
            script=(base/'renderer/launch.sh').read_text()
            self.assertIn('DISABLE_MANGOHUD=1',script)
            self.assertIn('VK_LAYER_PATH=',script)
            self.assertTrue((base/'renderer/launch.sh').stat().st_mode & 0o111)

    def test_corrupt_bundle_refused_before_copy(self):
        with tempfile.TemporaryDirectory() as folder:
            source=self.fixture(folder)
            (source/'i386/libMangoHud.so').write_bytes(b'wrong')
            with self.assertRaises(ValueError):claw_renderer.install(Path(folder)/'profile',source)
            self.assertFalse((Path(folder)/'profile/renderer').exists())

    def test_new_fields_migrate_without_activating_custom_renderer(self):
        settings=main.normalize({'fontsize':22,'margin':12})
        self.assertFalse(settings['renderer'])
        self.assertEqual(settings['fontsize'],22)
        self.assertEqual(settings['offset_y'],12)
        cfg=main.mango_config(settings)
        self.assertNotIn('claw_renderer=1',cfg)
        settings.update(renderer=True,fps_fontsize=40,padding_x=20,center=True)
        cfg=main.mango_config(settings)
        self.assertIn('claw_fps_size=40\n',cfg)
        self.assertIn('claw_padding_x=20\n',cfg)
        self.assertIn('claw_center=1\n',cfg)
        self.assertIn('font_size=22\n',cfg)
