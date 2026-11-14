"""Draw classified synthetic telemetry and real Vulkan output in both HUD modes."""
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import main
from claw_modular import encode_native, load_layout

ICD = sorted(Path(os.environ.get('CLAW_TEST_ICD_DIR', '/usr/share/vulkan/icd.d')).glob('lvp_icd*.json'))[0]
RESULT = re.compile(r'CLAW_FRAMEGEN_GRAPH game=([\d.-]+) fg=([\d.-]+) output=([\d.-]+) game_points=(\d+) output_points=(\d+)')


def feed(relay, stopped):
    with relay.open('r+b', buffering=0) as file:
        sequence = 0
        start = time.monotonic()
        while not stopped.is_set():
            sequence += 1
            file.seek(4)
            file.write(struct.pack('<I', 2 * sequence - 1))
            file.seek(16 + ((sequence - 1) % 256) * 24)
            kind = 1 if sequence % 2 else 2
            file.write(struct.pack('<QQII', time.time_ns(), sequence, kind, 0))
            file.seek(8)
            file.write(struct.pack('<Q', sequence))
            file.seek(4)
            file.write(struct.pack('<I', 2 * sequence))
            stopped.wait(max(0, start + sequence / 60 - time.monotonic()))


with tempfile.TemporaryDirectory() as directory:
    tmp = Path(directory)
    main.BASE = tmp / 'profile'
    main.install_font()
    main.install_condensed_fonts()
    config = tmp / 'MangoHud.conf'
    relay = tmp / 'frames'
    relay.write_bytes(struct.pack('<I', 0x31474643) + bytes(6156))
    name = 'VK_LAYER_CLAW_METRICS_framegen_ci'
    manifest = {'file_format_version':'1.0.0','layer':{
        'name': name, 'type':'GLOBAL', 'api_version':'1.3.0', 'implementation_version':'1',
        'description':'Frame Gen CI', 'library_path': str(ROOT/'native64/libMangoHud.so'),
        'functions': {'vkGetInstanceProcAddr':'overlay_GetInstanceProcAddr',
                      'vkGetDeviceProcAddr':'overlay_GetDeviceProcAddr'}}}
    (tmp/'ClawMetrics.json').write_text(json.dumps(manifest))
    layout = load_layout((ROOT/'assets/modular/graph-focus.json').read_text())
    def set_graph(node):
        if node['token'] == 'graph':
            node['token'] = 'graph.framegen'
        for child in node['children']:
            set_graph(child)
    set_graph(layout['root'])
    transport = main.BASE / 'modular.layout'
    transport.write_text(encode_native(layout))
    env = {**os.environ, 'VK_LAYER_PATH':str(tmp), 'VK_INSTANCE_LAYERS':name,
           'VK_ICD_FILENAMES':str(ICD), 'DISABLE_MANGOHUD':'1', 'CLAW_METRICS_VERIFY':'1',
           'MANGOHUD_CONFIGFILE':str(config)}

    for mode in ('classic', 'modular', 'output-only'):
        modular = mode == 'modular'
        settings = main.normalize({
            'modular_enabled':modular, 'modular_layout':layout, 'hud_position':'top-left',
            'metrics':{'fps_game':True,'fps_generated':True,'fps_output':True,
                       'graph':False,'framegen_graph':True}})
        config.write_text(main.mango_config(settings, native_spacing=True) + 'fps_limit=60\n')
        transport.with_suffix('.layout.enabled').write_text('1\n' if modular else '0\n')
        stopped = threading.Event()
        worker = None
        if mode != 'output-only':
            with relay.open('r+b') as file:
                file.seek(4)
                file.write(bytes(6156))
            worker = threading.Thread(target=feed, args=(relay, stopped))
            worker.start()
        try:
            result = subprocess.run(
                ['xvfb-run','-a','-s','-screen 0 1920x1080x24',
                 'vkcube','--c','185','--width','1280','--height','720'],
                env={**env, **({'CLAW_FRAMEGEN_FILE':str(relay)} if worker else {})},
                text=True, capture_output=True, timeout=40)
        finally:
            stopped.set()
            if worker:
                worker.join()
        log = result.stdout + result.stderr
        assert result.returncode == 0, log
        rows = RESULT.findall(log)
        assert rows, log
        if modular:
            assert 'CLAW_MODULAR nodes=' in log, log
        if worker:
            assert any(25 < float(game) < 35 and 25 < float(fg) < 35 and float(out) > 30
                       and int(g) > 5 and int(o) > 10 for game, fg, out, g, o in rows), log
        else:
            assert any(float(game) < 0 and float(fg) < 0 and float(out) > 30 and
                       int(g) == 0 and int(o) > 10 for game, fg, out, g, o in rows), log
        print(f'PASS Frame Gen Vulkan {mode}: measured output present cadence, synthetic classification and real ImGui draw')
