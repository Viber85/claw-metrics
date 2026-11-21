#!/usr/bin/env python3
"""Run the production launcher with real ELF32 and ELF64 Vulkan applications."""
import os
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import main
from claw_modular import load_layout

GRAPH = re.compile(r'CLAW_FRAMEGEN_GRAPH game=([\d.-]+) fg=([\d.-]+) output=([\d.-]+) game_points=(\d+) output_points=(\d+)')
executables = {
    '32': ROOT / 'test32/vulkan-present',
    '64': Path('/usr/bin/vkcube'),
}
for bits, executable in executables.items():
    assert executable.read_bytes()[:5] == b'\x7fELF' + bytes([1 if bits == '32' else 2]), executable

with tempfile.TemporaryDirectory(prefix="Claw's multilib ") as directory:
    home = Path(directory)
    main.BASE = home / '.config/ClawMetrics'
    main.user_home = lambda: home
    main.install_font()
    main.install_condensed_fonts()
    layout = load_layout((ROOT / 'assets/modular/graph-focus.json').read_text())

    def framegen_graph(node):
        if node['token'] == 'graph':
            node['token'] = 'graph.framegen'
        for child in node['children']:
            framegen_graph(child)

    framegen_graph(layout['root'])
    for mode in ('classic', 'modular'):
        settings = main.normalize({
            'modular_layout': layout, 'modular_enabled': mode == 'modular',
            'metrics': {'fps_output': True, 'graph': False, 'framegen_graph': True},
        })
        main.publish_modular(settings)
        main.publish_native_hud(settings)
        config = main.native_hud_path()
        config.write_text(config.read_text() + 'fps_limit=60\n')
        for bits, executable in executables.items():
            triplet = 'i386-linux-gnu' if bits == '32' else 'x86_64-linux-gnu'
            driver = Path('/usr/lib') / triplet / 'libvulkan_lvp.so'
            assert driver.is_file(), driver
            icd = home / f'llvmpipe-{bits}.json'
            icd.write_text(json.dumps({'file_format_version':'1.0.0', 'ICD':{
                'library_path':str(driver), 'api_version':'1.3.0', 'library_arch':bits,
            }}))
            env = {**os.environ, 'HOME': str(home), 'CLAW_METRICS_VERIFY': '1',
                   'VK_ICD_FILENAMES': str(icd)}
            for key in ('CLAW_FRAMEGEN', 'CLAW_FRAMEGEN_FILE', 'MANGOHUD_CONFIG',
                        'VK_LAYER_PATH', 'VK_INSTANCE_LAYERS'):
                env.pop(key, None)
            result = subprocess.run(
                ['xvfb-run', '-a', str(main.short_launcher_path()), str(executable),
                 '--c', '185', '--width', '1280', '--height', '720'],
                env=env, capture_output=True, text=True, timeout=40)
            log = result.stdout + result.stderr
            assert result.returncode == 0, log[-12000:]
            rows = GRAPH.findall(log)
            assert any(float(out) > 20 and int(points) > 10 for _, _, out, _, points in rows), log[-12000:]
            if mode == 'modular':
                assert 'CLAW_MODULAR nodes=' in log, log[-12000:]
            print(f'PASS production launcher: {bits}-bit Vulkan {mode}, actual ImGui drawing and output FPS.')
