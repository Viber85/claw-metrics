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
            'opacity':0 if mode==4 else 80,
            'background':{'mode':'solid' if mode==4 else 'linear' if mode in (0,3) else 'radial', 'angle':45,
                'outline_enabled':True,'outline_color':'FFFFFF','outline_width':2,'outline_opacity':60,
                'stops':[{'position':0,'color':'FF0000'},{'position':50,'color':'00FF00'},{'position':100,'color':'0000FF'}]},
            'graph_style':'area' if mode in (0,1) else 'dual',
            'vertical_graph_style':'area' if mode in (0,1) else 'dual',
            'metrics':{'graph':True,'fps_average':True,'fps_low1':True,'ram_game':True,'ram_swap':True}})
        staging=config.with_suffix('.tmp')
        staging.write_text(main.mango_config(settings,native_spacing=True)+'fps_limit=60\n')
        os.replace(staging,config)
    write(0)
    stop=threading.Event()
    observed={mode:threading.Event() for mode in range(5)}
    errors=[]
    def switch():
        try:
            # Startup and shader compilation vary widely on shared CI runners.
            # Wait for real drawn readings before advancing each live mode.
            if not observed[0].wait(60):
                raise RuntimeError('Initial Vulkan reading did not appear')
            for mode in (1,2,3,4,0):
                if stop.wait(2): return
                write(mode)
                if mode!=0 and not observed[mode].wait(15):
                    raise RuntimeError(f'Vulkan reading for mode {mode} did not appear')
        except Exception as error:
            errors.append(error)
    worker=threading.Thread(target=switch)
    env={**os.environ,'VK_LAYER_PATH':str(tmp),'VK_INSTANCE_LAYERS':'VK_LAYER_CLAW_METRICS_ci',
         'VK_ICD_FILENAMES':str(icds[0]),'DISABLE_MANGOHUD':'1',
         'MANGOHUD_CONFIGFILE':str(config),'CLAW_METRICS_VERIFY':'1'}
    worker.start()
    lines=[]
    def collect(stream):
        for line in stream:
            lines.append(line)
            match=re.search(r'CLAW_EXTRA mode=(\d+) token=28',line)
            if match: observed[int(match.group(1))].set()
            if 'CLAW_GRAPH layout=vertical style=3' in line: observed[3].set()
            if 'CLAW_OUTLINE mode=0 vertical=0' in line: observed[4].set()
    try:
        process=subprocess.Popen(['xvfb-run','-a','-s','-screen 0 1920x1080x24',
                                  'vkcube','--c','6000','--width','1280','--height','720'],
                                 env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,bufsize=1)
        reader=threading.Thread(target=collect,args=(process.stdout,))
        reader.start()
        try: returncode=process.wait(timeout=180)
        except subprocess.TimeoutExpired:
            process.kill();process.wait();raise
        reader.join()
    finally:
        stop.set();worker.join()
    log=''.join(lines)
    print(log[-18000:])
    assert not errors,errors
    assert returncode==0,('Vulkan process failed',returncode)
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

    backgrounds=re.findall(r'CLAW_BACKGROUND mode=(\d+) vertical=(\d+) stops=(\d+) alpha=([\d.]+) vertices=(\d+) max_alpha=(\d+) colors=(\d+)',log)
    for mode in (1,2):
        for vertical in (0,1):
            matches=[item for item in backgrounds if int(item[0])==mode and int(item[1])==vertical]
            assert matches,('Missing gradient rendering evidence',mode,vertical)
            for _,_,stops,alpha,vertices,max_alpha,colors in matches:
                assert int(stops)==3 and abs(float(alpha)-.8)<.01
                assert int(vertices)>1000 and int(max_alpha)==204 and int(colors)>3
    print('PASS native multistop backgrounds: linear and radial gradients in both layouts, rounded mesh, shared 80% opacity and clean Vulkan exit.')

    outlines=re.findall(r'CLAW_OUTLINE mode=(\d+) vertical=(\d+) width=([\d.]+) alpha=(\d+) vertices=(\d+) inside=(\d+) background_alpha=([\d.]+)',log)
    for mode,vertical in ((1,0),(1,1),(2,0),(2,1),(0,0)):
        matches=[item for item in outlines if int(item[0])==mode and int(item[1])==vertical]
        assert matches,('Missing outline evidence',mode,vertical)
        for _,_,width,alpha,vertices,inside,background_alpha in matches:
            assert float(width)==2 and int(alpha)==153 and int(vertices)>8 and int(inside)==1,matches
            if mode==0: assert float(background_alpha)==0,'Outline must survive fully transparent background'
    print('PASS native rounded outlines: color/width/opacity, both layouts, all backgrounds including 0% fill, vertices inside HUD bounds.')
