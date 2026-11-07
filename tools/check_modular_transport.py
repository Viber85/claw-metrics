"""Cross-language DevLab document -> bounded transport -> native snapshot tests."""
from pathlib import Path
import importlib.util
import os
import subprocess
import tempfile
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('schema', ROOT/'experiments/modular/schema.py')
schema = importlib.util.module_from_spec(spec)
spec.loader.exec_module(schema)
with tempfile.TemporaryDirectory() as directory:
    tmp=Path(directory);binary=tmp/'transport'
    subprocess.run(['g++','-std=c++14','-Wall','-Wextra','-Werror','-O1','-pthread',
                    '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                    '-I',str(ROOT/'experiments/native'),str(ROOT/'tools/modular_transport_probe.cpp'),'-o',str(binary)],check=True)
    for name in ('two-rows','graph-focus','center-left','center-right'):
        source='graph-focus' if name.startswith('center-') else name
        doc=schema.load_layout((ROOT/f'experiments/modular/{source}.json').read_text())
        if name.startswith('center-'):doc.update(anchor=name,y=-22)
        doc['root'].update(id='čćž'*20,background='#112233',opacity=44,outline=True)
        last=doc['root']
        while last['children']:last=last['children'][-1]
        last['color']='#ABCDEF'
        doc['root']['children'][0]['selfAlign']='end'
        encoded=tmp/(name+'.layout');encoded.write_text(schema.encode_native(doc))
        subprocess.run([str(binary),str(encoded)],check=True,env={**os.environ,'ASAN_OPTIONS':'detect_leaks=0'})
