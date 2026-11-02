"""Opt-in native path in actual software Vulkan. No handheld sensor validation."""
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
    config=tmp/'MangoHud.conf';transport=tmp/'modular.layout'
    manifest={'file_format_version':'1.0.0','layer':{'name':'VK_LAYER_CLAW_METRICS_modular_ci','type':'GLOBAL','api_version':'1.3.0','implementation_version':'1','description':'Modular renderer CI','library_path':str(ROOT/'native64/libMangoHud.so'),'functions':{'vkGetInstanceProcAddr':'overlay_GetInstanceProcAddr','vkGetDeviceProcAddr':'overlay_GetDeviceProcAddr'}}}
    (tmp/'modular.json').write_text(json.dumps(manifest))
    def atomic(path,text):
        staging=path.with_suffix('.tmp');staging.write_text(text);os.replace(staging,path)
    def settings(size=24):
        value=main.normalize({'fontsize':size,'fps':True,'cpu':True,'gpu':True,'ram':True,'vram':True,'battery':True,'tdp':True,'draw':True,'frametime':True,'time':True,'hud_position':'top-left','metrics':{'graph':True,'fps_average':True,'fps_low1':True,'ram_game':True,'ram_swap':True}})
        atomic(config,main.mango_config(value,native_spacing=True)+'fps_limit=60\n')
    docs={name:schema.load_layout((ROOT/f'experiments/modular/{name}.json').read_text()) for name in ('two-rows','graph-focus')}
    for doc in docs.values():doc['x']=0
    settings();atomic(transport,schema.encode_native(docs['two-rows']))
    stop=threading.Event();errors=[]
    def transitions():
        try:
            if stop.wait(3):return
            atomic(transport,'CLAW_MODULAR_V1\ntruncated')
            if stop.wait(3):return
            atomic(transport,schema.encode_native(docs['graph-focus']))
            if stop.wait(3):return
            settings(26) # exercise real font atlas reload with active modular drawing
            if stop.wait(3):return
            atomic(transport,schema.encode_native(docs['two-rows']))
        except Exception as error:errors.append(error)
    worker=threading.Thread(target=transitions);worker.start()
    env={**os.environ,'VK_LAYER_PATH':str(tmp),'VK_INSTANCE_LAYERS':'VK_LAYER_CLAW_METRICS_modular_ci','VK_ICD_FILENAMES':str(icds[0]),'DISABLE_MANGOHUD':'1','MANGOHUD_CONFIGFILE':str(config),'CLAW_METRICS_VERIFY':'1','CLAW_MODULAR_LAYOUT_FILE':str(transport)}
    try:result=subprocess.run(['xvfb-run','-a','-s','-screen 0 1920x1080x24','vkcube','--c','1000','--width','1280','--height','720'],env=env,text=True,capture_output=True,timeout=100)
    finally:stop.set();worker.join()
    log=result.stdout+'\n'+result.stderr;print(log[-20000:])
    assert not errors,errors
    assert result.returncode==0,('Vulkan process failed',result.returncode)
    matches=re.findall(r'CLAW_MODULAR nodes=(\d+) root=(\S+) fps=([\d.]+) vertices=(\d+) outside=(\d+) frame=(\d+)',log)
    assert matches,'Modular path never drew'
    assert {int(m[0]) for m in matches}=={23,28},matches
    for count,key,fps,vertices,outside,frame in matches:
        assert float(fps)>0 and int(vertices)>100 and outside=='0',matches
    first=docs['two-rows']['root']['id'];second=docs['graph-focus']['root']['id']
    assert any(k==first and 240<=int(f)<=360 for _,k,_,_,_,f in matches),('Invalid import displaced active layout',matches)
    assert any(k==second and int(f)>540 for _,k,_,_,_,f in matches),('Active modular draw did not survive font reload',matches)
    assert matches[-1][1]==first,('Did not restore first layout',matches)
    print('PASS actual Vulkan: live FPS/text/graph geometry, two imported layouts, rejected partial file, font reload, restored layout and clean exit. Sensors are lavapipe/host fixtures, not handheld validation.')
