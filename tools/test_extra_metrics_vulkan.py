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
            'fps':True,'frametime':False,'cpu':False,'gpu':False,'ram':True,'vram':False,
            'battery':False,'time':False,'draw':False,'tdp':False,
            'hud_orientation':'vertical' if mode==1 else 'horizontal',
            'hud_position':'top-center' if mode==2 else 'top-left',
            'inline_metrics':mode!=2,'fontsize':26 if mode==1 else 18,
            'fps_scale':200 if mode==1 else 100,
            'metrics':{'fps_average':True,'fps_low1':True,'ram_game':True,'ram_swap':True}})
        staging=config.with_suffix('.tmp')
        staging.write_text(main.mango_config(settings,native_spacing=True)+'fps_limit=60\n')
        os.replace(staging,config)
    write(0)
    stop=threading.Event()
    errors=[]
    def switch():
        try:
            # Warm up >100 frames in each initial layout before switching.
            for mode in (1,2,0):
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
    readings=re.findall(r'CLAW_EXTRA mode=(\d+) token=(\d+) value=([\d.]+) x=([\d.-]+) y=([\d.-]+)',log)
    for mode in range(3):
        for token in range(28,32):
            matches=[r for r in readings if int(r[0])==mode and int(r[1])==token]
            assert matches,('Missing native reading',mode,token)
            for _,_,value,x,y in matches:
                assert float(value)>=0
                assert 0<=float(x)<1280 and 0<=float(y)<720,('Out-of-bounds reading',matches)
                if token in (28,29,30): assert float(value)>0
    print('PASS actual Vulkan: all 4 readings drawn in horizontal, vertical and non-inline layouts; atomic live transitions and clean process exit.')
