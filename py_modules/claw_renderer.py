"""Install an isolated, checksum-verified native bundle inside the profile directory."""
import hashlib
import json
import os
from pathlib import Path
import shlex
import tempfile
import re
import subprocess

LAYER = 'VK_LAYER_CLAW_METRICS_overlay'
LIBS = ('libMangoHud.so', 'libMangoHud_opengl.so', 'libMangoHud_shim.so')
EXPECTED = {f'{arch}/{name}': cls for arch, cls in [('x86_64', 2), ('i386', 1)] for name in LIBS}


def write(path, data, mode=0o644):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.parent.chmod(0o755)
    fd, temporary = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            os.fchmod(stream.fileno(), mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def link(path, target):
    if path.is_symlink():
        if os.readlink(path) == target:
            return
        path.unlink()
    if path.exists():
        raise ValueError(f'Unexpected file at renderer alias: {path.name}')
    path.symlink_to(target)


def generic_lib_arch():
    # glibc $LIB differs between Arch/SteamOS and Debian containers. Keep the
    # explicit Debian/lib64/lib32 aliases and resolve the host's generic lib.
    candidates = [
        ('x86_64', '/lib64/ld-linux-x86-64.so.2'),
        ('x86_64', '/usr/lib/ld-linux-x86-64.so.2'),
        ('i386', '/lib/ld-linux.so.2'),
        ('i386', '/usr/lib32/ld-linux.so.2'),
    ]
    for arch, loader in candidates:
        if not Path(loader).is_file():
            continue
        try:
            result = subprocess.run([loader, '--list-diagnostics'], capture_output=True, text=True, timeout=1)
            token = re.search(r'^dl_dst_lib="([^"]+)"', result.stdout, re.MULTILINE)
            if result.returncode == 0 and token and token[1] == 'lib':
                return arch
        except (OSError, subprocess.TimeoutExpired):
            pass
    return 'x86_64'


def install(base, source):
    index_path = source / 'index.json'
    if not index_path.is_file():
        return False, 'Nativni paket nije pronađen. Instaliraj puni ZIP i ponovno pokreni Decky.'
    index = json.loads(index_path.read_text())
    if index.get('version') != 'claw-native-1' or set(index.get('files', {})) != set(EXPECTED):
        raise ValueError('Invalid native renderer index')
    verified = {}
    for relative, elf_class in EXPECTED.items():
        data = (source / relative).read_bytes()
        if len(data) < 1000 or data[:4] != b'\x7fELF' or data[4] != elf_class:
            raise ValueError(f'Invalid renderer architecture: {relative}')
        if hashlib.sha256(data).hexdigest() != index['files'][relative]:
            raise ValueError(f'Renderer checksum failed: {relative}')
        verified[relative] = data
    base.mkdir(parents=True, exist_ok=True)
    base.chmod(0o755)
    destination = base / 'renderer'
    destination.mkdir(exist_ok=True)
    destination.chmod(0o755)
    for relative, data in verified.items():
        write(destination / relative, data)
    (destination / 'lib').mkdir(exist_ok=True)
    (destination / 'lib').chmod(0o755)
    link(destination / 'lib64', 'x86_64')
    link(destination / 'lib32', 'i386')
    link(destination / 'lib/x86_64-linux-gnu', '../x86_64')
    link(destination / 'lib/i386-linux-gnu', '../i386')
    generic_arch = generic_lib_arch()
    for name in LIBS:
        link(destination / 'lib' / name, '../' + generic_arch + '/' + name)
    manifest = {'file_format_version': '1.0.0', 'layer': {
        'name': LAYER, 'type': 'GLOBAL', 'api_version': '1.3.0',
        'implementation_version': '1', 'description': 'Claw Metrics private renderer',
        'library_path': str(destination / '$LIB/libMangoHud.so'),
        'functions': {'vkGetInstanceProcAddr': 'overlay_GetInstanceProcAddr', 'vkGetDeviceProcAddr': 'overlay_GetDeviceProcAddr'},
    }}
    write(destination / 'layers/ClawMetrics.json', json.dumps(manifest, indent=2).encode())
    script = '''#!/bin/sh
set -eu
if [ "$#" -eq 0 ]; then echo "Claw Metrics: missing game command" >&2; exit 2; fi
ROOT=ROOT_PLACEHOLDER
export MANGOHUD_CONFIGFILE=CONFIG_PLACEHOLDER
# Keep the system implicit layer off; this explicit private layer is separate.
export DISABLE_MANGOHUD=1
export VK_LAYER_PATH="$ROOT/layers${VK_LAYER_PATH:+:$VK_LAYER_PATH}:/usr/share/vulkan/explicit_layer.d:/etc/vulkan/explicit_layer.d"
case ":${VK_INSTANCE_LAYERS-}:" in
  *:VK_LAYER_CLAW_METRICS_overlay:*) ;;
  *) export VK_INSTANCE_LAYERS="VK_LAYER_CLAW_METRICS_overlay${VK_INSTANCE_LAYERS:+:$VK_INSTANCE_LAYERS}" ;;
esac
CLAW_LIBDIR="$ROOT/"'$LIB'
export LD_PRELOAD="$CLAW_LIBDIR/libMangoHud_shim.so${LD_PRELOAD:+:$LD_PRELOAD}"
export MANGOHUD_OPENGL_LIBS="$CLAW_LIBDIR/libMangoHud_opengl.so"
exec "$@"
'''.replace('ROOT_PLACEHOLDER', shlex.quote(str(destination))).replace('CONFIG_PLACEHOLDER', shlex.quote(str(base / 'MangoHud.conf')))
    write(destination / 'launch.sh', script.encode(), 0o755)
    return True, 'Claw renderer · 64-bit + 32-bit · datoteke provjerene'
