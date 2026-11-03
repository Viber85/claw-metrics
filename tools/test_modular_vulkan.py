"""Opt-in native path in actual software Vulkan. No handheld sensor validation."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import threading

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import main
spec=importlib.util.spec_from_file_location('schema',ROOT/'experiments/modular/schema.py')
schema=importlib.util.module_from_spec(spec);spec.loader.exec_module(schema)
icds=sorted(Path('/usr/share/vulkan/icd.d').glob('lvp_icd*.json'));assert icds
with tempfile.TemporaryDirectory() as directory:
    tmp=Path(directory);main.BASE=tmp/'profile';main.install_font();main.install_condensed_fonts()
    config=tmp/'MangoHud.conf';transport=main.BASE/'modular.layout'
    manifest={'file_format_version':'1.0.0','layer':{'name':'VK_LAYER_CLAW_METRICS_modular_ci','type':'GLOBAL','api_version':'1.3.0','implementation_version':'1','description':'Modular renderer CI','library_path':str(ROOT/'native64/libMangoHud.so'),'functions':{'vkGetInstanceProcAddr':'overlay_GetInstanceProcAddr','vkGetDeviceProcAddr':'overlay_GetDeviceProcAddr'}}}
    (tmp/'modular.json').write_text(json.dumps(manifest))
    def atomic(path,text):
        staging=path.with_suffix('.tmp');staging.write_text(text);os.replace(staging,path)
    def settings(size=24, style="line", background="linear", enabled=True):
        value=main.normalize({'modular_enabled':enabled,'modular_layout':docs['two-rows'],'graph_style':style,'background':{'mode':background,'outline_enabled':True,'outline_width':2,'outline_opacity':60},'opacity':0 if background=='solid' else 80,'fontsize':size,'fps':True,'cpu':True,'gpu':True,'ram':True,'vram':True,'battery':True,'tdp':True,'draw':True,'frametime':True,'time':True,'hud_position':'top-left','metrics':{'graph':True,'fps_average':True,'fps_low1':True,'ram_game':True,'ram_swap':True}})
        atomic(config,main.mango_config(value,native_spacing=True)+'fps_limit=60\n')
    docs={name:schema.load_layout((ROOT/f'experiments/modular/{name}.json').read_text()) for name in ('two-rows','graph-focus')}
    stress=copy.deepcopy(docs['two-rows']);stress['root'].update(id='stress-root',axis='column',children=[])
    metric=copy.deepcopy(docs['two-rows']['root']['children'][1]['children'][1]['children'][-1])
    for row in range(4):
        group=copy.deepcopy(stress['root']);group.update(id=f'stress-row-{row}',axis='row',padding=2,gap=4,children=[])
        for column in range(8):
            child=copy.deepcopy(metric);child.update(id=f'stress-graph-{row}-{column}',width=80,height=32)
            group['children'].append(child)
        stress['root']['children'].append(group)
    stress['x']=0
    for doc in docs.values():doc['x']=0
    settings();atomic(transport,schema.encode_native(docs['two-rows']))
    stop=threading.Event();errors=[]
    def transitions():
        try:
            if stop.wait(2):return
            atomic(transport,'CLAW_MODULAR_V1\ntruncated')
            if stop.wait(2):return
            atomic(transport,schema.encode_native(docs['graph-focus']));settings(24,'area','radial')
            if stop.wait(2):return
            settings(26,'bars','solid')
            if stop.wait(2):return
            settings(26,'dual','linear')
            if stop.wait(2):return
            settings(26,'smooth','radial')
            if stop.wait(2):return
            atomic(transport,schema.encode_native(docs['two-rows']));settings(24,'dual_layer','linear')
            if stop.wait(2):return
            settings(24,'line','solid',False)
            if stop.wait(2):return
            atomic(transport,schema.encode_native(docs['graph-focus']));settings(24,'line','radial')
            if stop.wait(2):return
            atomic(transport,schema.encode_native(stress));settings(24,'dual_layer','radial')
            if stop.wait(2):return
            atomic(transport,schema.encode_native(docs['graph-focus']));settings(24,'line','radial')
        except Exception as error:errors.append(error)
    worker=threading.Thread(target=transitions);worker.start()
    env={**os.environ,'VK_LAYER_PATH':str(tmp),'VK_INSTANCE_LAYERS':'VK_LAYER_CLAW_METRICS_modular_ci','VK_ICD_FILENAMES':str(icds[0]),'DISABLE_MANGOHUD':'1','MANGOHUD_CONFIGFILE':str(config),'CLAW_METRICS_VERIFY':'1'}
    try:result=subprocess.run(['xvfb-run','-a','-s','-screen 0 1920x1080x24','vkcube','--c','1440','--width','1280','--height','720'],env=env,text=True,capture_output=True,timeout=100)
    finally:stop.set();worker.join()
    log=result.stdout+'\n'+result.stderr;print(log[-20000:])
    assert not errors,errors
    assert result.returncode==0,('Vulkan process failed',result.returncode)
    matches=re.findall(r'CLAW_MODULAR nodes=(\d+) root=(\S+) fps=([\d.]+) vertices=(\d+) outside=(\d+) frame=(\d+)',log)
    assert matches,'Modular path never drew'
    assert {int(m[0]) for m in matches}=={23,28,37},matches
    for count,key,fps,vertices,outside,frame in matches:
        assert float(fps)>0 and int(vertices)>100 and outside=='0',matches
    first=docs['two-rows']['root']['id'];second=docs['graph-focus']['root']['id']
    assert any(k==first and 150<=int(f)<=240 for _,k,_,_,_,f in matches),('Invalid import displaced active layout',matches)
    assert any(k==second and int(f)>400 for _,k,_,_,_,f in matches),('Active modular draw did not survive font reload',matches)
    assert any(k=='stress-root' and int(v)>65535 for _,k,_,v,_,_ in matches),('Large-mesh path not exercised',matches)
    assert matches[-1][1]==second,('Did not re-enable modular rendering',matches)
    assert 'CLAW_EXTRA mode=0' in log,'Legacy fallback was not exercised'
    styles={int(x) for x in re.findall(r'CLAW_MODULAR .*? style=(\d+)',log)}
    assert styles==set(range(6)),('Missing graph style',styles)
    for mode in (1,2): assert f'CLAW_BACKGROUND mode={mode}' in log,('Missing modular gradient',mode)
    assert 'CLAW_OUTLINE mode=0' in log,'Transparent solid background lost its outline'
    print('PASS actual Vulkan: live FPS/text/graph geometry, two imported layouts, rejected partial file, font reload, restored layout and clean exit. Sensors are lavapipe/host fixtures, not handheld validation.')
