"""Package both architectures with explicit hashes; no system installation."""
from pathlib import Path
import hashlib,json,shutil
root=Path(__file__).resolve().parents[1]
out=root/'assets/native';out.mkdir(parents=True,exist_ok=True)
files={}
for arch,elf_class in [('x86_64',2),('i386',1)]:
    source=root/'native-packages'/f'native-{arch}'
    for name in ('libMangoHud.so','libMangoHud_opengl.so','libMangoHud_shim.so'):
        data=(source/name).read_bytes()
        assert data[:4]==b'\x7fELF' and data[4]==elf_class, (arch,name)
        destination=out/arch/name;destination.parent.mkdir(exist_ok=True)
        destination.write_bytes(data)
        files[f'{arch}/{name}']=hashlib.sha256(data).hexdigest()
shutil.copy2(root/'native-packages/native-x86_64/MANGOHUD-LICENSE.txt',out/'MANGOHUD-LICENSE.txt')
shutil.copytree(root/'renderer/licenses',out/'licenses',dirs_exist_ok=True)
(out/'index.json').write_text(json.dumps({'version':'claw-native-1','upstream':'fea4292519a3085881d567a18ad3e1fee37078d8','files':files},indent=2)+'\n')
print('Prepared isolated 64-bit and 32-bit renderer bundle')
