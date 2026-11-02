"""Actual software Vulkan draw + live horizontal/vertical/non-inline transitions.

No hardware sensor validation: uses lavapipe and Xvfb, not a handheld.
"""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import threading

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
import main
icds=sorted(Path('/usr/share/vulkan/icd.d').glob('lvp_icd*.json'))
assert icds,'Lavapipe test driver missing'
with tempfile.TemporaryDirectory() as directory:
    tmp=Path(directory)
    main.BASE=tmp/'profile'
    main.install_font()
    main.install_condensed_fonts()
    config=tmp/'MangoHud.conf'
    manifest={'file_format_version':'1.0.0','layer':{
        'name':'VK_LAYER_CLAW_METRICS_ci','type':'GLOBAL','api_version':'1.3.0',
        'implementation_version':'1','description':'Claw Metrics CI private layer',
        'library_path':str(root/'native64/libMangoHud.so'),
        'functions':{'vkGetInstanceProcAddr':'overlay_GetInstanceProcAddr','vkGetDeviceProcAddr':'overlay_GetDeviceProcAddr'}}}
    (tmp/'ClawMetrics.json').write_text(json.dumps(manifest))
    def write(mode):
        settings=main.normalize({
            'fps':True,'frametime':True,'cpu':False,'gpu':False,'ram':True,'vram':False,
            'battery':False,'time':False,'draw':False,'tdp':False,
            'hud_orientation':'vertical' if mode in (1,3) else 'horizontal',
            'hud_position':'top-center' if mode==2 else 'top-left',
            'inline_metrics':mode!=2,'fontsize':26 if mode==1 else 18,
            'fps_scale':200 if mode==1 else 100,
            'graph_style':'area' if mode in (0,1) else 'dual',
            'vertical_graph_style':'area' if mode in (0,1) else 'dual',
            'metrics':{'graph':True,'fps_average':True,'fps_low1':True,'ram_game':True,'ram_swap':True}})
        staging=config.with_suffix('.tmp')
        staging.write_text(main.mango_config(settings,native_spacing=True)+'fps_limit=60\n')
        os.replace(staging,config)
    write(0)
    stop=threading.Event()
    errors=[]
    def switch():
        try:
            # Warm up >100 frames in each initial layout before switching.
            for mode in (1,2,3):
                if stop.wait(3): return
                write(mode)
        except Exception as error:
            errors.append(error)
    worker=threading.Thread(target=switch)
    env={**os.environ,'VK_LAYER_PATH':str(tmp),'VK_INSTANCE_LAYERS':'VK_LAYER_CLAW_METRICS_ci',
         'VK_ICD_FILENAMES':str(icds[0]),'DISABLE_MANGOHUD':'1',
         'MANGOHUD_CONFIGFILE':str(config),'CLAW_METRICS_VERIFY':'1'}
    worker.start()
    try:
        result=subprocess.run(['xvfb-run','-a','-s','-screen 0 1920x1080x24',
                               'vkcube','--c','900','--width','1280','--height','720'],
                              env=env,text=True,capture_output=True,timeout=100)
    finally:
        stop.set();worker.join()
    log=result.stdout+'\n'+result.stderr
    print(log[-18000:])
    assert not errors,errors
    assert result.returncode==0,('Vulkan process failed',result.returncode)
    readings=re.findall(r'CLAW_EXTRA mode=(\d+) token=(\d+) value=([\d.]+) x=([\d.-]+) y=([\d.-]+) right=([\d.-]+) bottom=([\d.-]+) vertices=(\d+)',log)
    for mode in range(3):
        for token in range(28,32):
            matches=[r for r in readings if int(r[0])==mode and int(r[1])==token]
            assert matches,('Missing native reading',mode,token)
            for _,_,value,x,y,right,bottom,vertices in matches:
                assert float(value)>=0
                assert int(vertices)>=36,('Reading has clipped or missing glyphs',matches)
                assert 0<=float(x)<float(right)<=1280 and 0<=float(y)<float(bottom)<=720,('Out-of-bounds reading',matches)
                if token in (28,29,30): assert float(value)>0
    print('PASS actual Vulkan: all 4 readings drawn in horizontal, vertical and non-inline layouts; atomic live transitions and clean process exit.')

    graphs=re.findall(r'CLAW_GRAPH layout=(horizontal|vertical) style=(\d+) fill_alpha=(\d+)',log)
    for layout in ('horizontal','vertical'):
        filled=[int(alpha) for orient,style,alpha in graphs if orient==layout and style=='1']
        translucent=[int(alpha) for orient,style,alpha in graphs if orient==layout and style=='3']
        assert filled and all(alpha==255 for alpha in filled),(layout,'Filled area alpha',graphs)
        assert translucent and all(0<alpha<255 for alpha in translucent),(layout,'Line + fill alpha',graphs)
    print('PASS actual Vulkan graph vertices: Filled area alpha=255; Line + fill remains translucent in both layouts.')
