"""Check real ImGui window geometry with fixture metrics, not a device screenshot.

MangoHud v0.8.1 pins ImGui v1.89.9. Fetch immutable-hash-verified sources,
compile the layout probe, install the actual bundled font and check the result.
"""
import argparse
import hashlib
import pathlib
import re
import subprocess
import sys
import tempfile
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import main

HASHES = {
    "imgui_tables.cpp": "39200172f9f17e59035255f967d59b337997fab377049a06da25dda4a05ce68e",
    "imgui_internal.h": "ac4f4d2d2c4ec507c47ea614081c899382a9b64df284c6f82a015764de81d5bb",
    "imstb_textedit.h": "3f4cf71a2b771d938f62ce4225df3ebe429b334fcdb3b89f1fedf43eeb0a3e1e",
    "imgui_widgets.cpp": "6222dcc6479447730ce84abb7cbcf0374c4218e7b54a5a7c553c7313b3d0b1bf",
    "imstb_truetype.h": "5b7693f174b0458c7bec5522c8d6be4fe606d3f5da5082351959c14e59269b53",
    "imgui.cpp": "e9ace04202abf7be4fb565602c2820e2bd727bd8abd3e5ea4381f847b69ceb1e",
    "imconfig.h": "e1a10ba1fa942005454c9700694439e2550a0617cb05fc34ec87311d228d6f5a",
    "imgui.h": "343936ee8a51af3e2557706e9474dab4a943e10cae7b12e2b9ff2e68e7d8f07a",
    "imstb_rectpack.h": "2efa3d5f7d003c19743b15155dad9f46d9f9fc783a18893d703b431d3c990972",
    "imgui_draw.cpp": "78b28b352941f088ed854764ed37398e85199bb33c2beaa74cbf370cb8d4fa64"
}


def run(imgui_dir=None):
    root = pathlib.Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory() as folder:
        tmp = pathlib.Path(folder)
        dest = tmp / 'imgui'
        dest.mkdir()
        for name, expected in HASHES.items():
            if imgui_dir:
                data = (pathlib.Path(imgui_dir) / name).read_bytes()
            else:
                url = f'https://raw.githubusercontent.com/ocornut/imgui/v1.89.9/{name}'
                with urllib.request.urlopen(url, timeout=60) as response:
                    data = response.read()
            data = (data.decode('utf-8').rstrip() + '\n').encode('utf-8')
            assert hashlib.sha256(data).hexdigest() == expected, name
            (dest / name).write_bytes(data)
        main.BASE = tmp / 'profile'
        main.install_font()
        config = main.mango_config(main.normalize({}))
        assert 'horizontal_stretch=0\n' in config
        assert 'position=top-center\n' in config
        assert 'hud_compact=0\n' in config
        assert 'round_corners=10\n' in config
        assert 'font_size=18\n' in config
        assert f'font_file={main.font_path()}\n' in config
        target = tmp / 'probe'
        sources = [str(dest / name) for name in HASHES if name.endswith('.cpp')]
        # render_check.cpp includes imgui/imgui.h relative to this temporary root.
        source = tmp / 'render_check.cpp'
        source.write_bytes((root / 'tools/render_check.cpp').read_bytes())
        subprocess.run(['g++', '-O1', '-I', str(dest), str(source), *sources, '-o', str(target)], check=True)
        for mode in ('0', '1'):
            output = subprocess.check_output([str(target), str(main.font_path()), '0', '1920', mode], cwd=tmp, text=True)
            glyph = re.search(r'glyph I=([\d.]+) W=([\d.]+)', output)
            assert glyph and float(glyph[1]) != float(glyph[2]), 'Font is not proportional'
            geom = re.search(r'window x=([\d.-]+) y=([\d.-]+) w=([\d.-]+) h=([\d.-]+)', output)
            assert geom, output
            x, y, width, height = map(float, geom.groups())
            assert x > 0 and x + width < 1920, output
            assert abs(x + width / 2 - 960) < 20, output
            assert y == 8 and 20 <= height < 60, output
            spans = re.findall(r'label .*? at ([\d.-]+)\.\.([\d.-]+)', output)
            assert spans and all(x <= float(a) < float(b) <= x + width for a, b in spans), output
            assert all(float(spans[i][1]) <= float(spans[i+1][0]) + 0.01 for i in range(len(spans)-1)), output
            print(f'PASS native ImGui fixture ({mode}): font proportional, row x={x:g}, y={y:g}, width={width:g}, height={height:g}; all labels inside row.')
        print('Scope: actual ImGui layout operations with fixture metrics; native game injection and device visuals remain untested.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--imgui-dir')
    run(parser.parse_args().imgui_dir)
