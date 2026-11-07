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
    main.tdp_path().write_text('Power Limit 20W\n')
    config=tmp/'MangoHud.conf'
    manifest={'file_format_version':'1.0.0','layer':{
        'name':'VK_LAYER_CLAW_METRICS_ci','type':'GLOBAL','api_version':'1.3.0',
        'implementation_version':'1','description':'Claw Metrics CI private layer',
        'library_path':str(root/'native64/libMangoHud.so'),
        'functions':{'vkGetInstanceProcAddr':'overlay_GetInstanceProcAddr','vkGetDeviceProcAddr':'overlay_GetDeviceProcAddr'}}}
    (tmp/'ClawMetrics.json').write_text(json.dumps(manifest))
    def write(mode):
        settings=main.normalize({
            'fps':True,'frametime':True,'cpu':True,'gpu':False,'ram':True,'vram':False,
            'battery':False,'time':False,'draw':False,'tdp':True,
            'token_colors':{'tdp.label':'FFAC12','tdp.value':'DDEEFF'},
            'token_weights':{'tdp.label':'bold','tdp.value':'light'},
            'hud_orientation':'vertical' if mode in (1,3) else 'horizontal',
            'hud_position':'top-center' if mode==2 else 'center-right' if mode in (1,4) else 'center-left',
            'offset_x':8,'offset_y':0,'unit_superscript':mode in (1,2,7,8),
            'group_gap_x':24 if mode==5 else 0,
            'inline_metrics':mode!=2,'fontsize':26 if mode==1 else 18,
            'fps_scale':200 if mode in (1,5,6,8) else 100,
            'opacity':0 if mode==4 else 80,
            'background':{'mode':'solid' if mode==4 else 'linear' if mode in (0,3,5,6) else 'radial', 'angle':45,
                'outline_enabled':True,'outline_color':'FFFFFF','outline_width':2,'outline_opacity':60,
                'stops':[{'position':0,'color':'FF0000'},{'position':50,'color':'00FF00'},{'position':100,'color':'0000FF'}]},
            'graph_style':'area' if mode in (0,1,5,6) else 'dual',
            'vertical_graph_style':'area' if mode in (0,1,5,6) else 'dual',
            'metrics':{'cpu_temp':False,'cpu_mhz':False,'cpu_power':False,'graph':True,'fps_average':True,'fps_low1':True,'ram_game':True,'ram_swap':True}})
        staging=config.with_suffix('.tmp')
        staging.write_text(main.mango_config(settings,native_spacing=True)+'fps_limit=60\n')
        os.replace(staging,config)
    write(0)
    stop=threading.Event()
    observed={mode:threading.Event() for mode in range(9)}
    errors=[]
    def switch():
        try:
            # Startup and shader compilation vary widely on shared CI runners.
            # Wait for real drawn readings before advancing each live mode.
            if not observed[0].wait(60):
                raise RuntimeError('Initial Vulkan reading did not appear')
            for mode in (1,2,3,4,6,5,7,8,0):
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
            if 'CLAW_CLASSIC vertical=0 units=0 center=1 right=0 gap=24.0 inline=1' in line: observed[5].set()
            if 'CLAW_CLASSIC vertical=0 units=0 center=1 right=0 gap=0.0 inline=1' in line and 'scale=200' in line: observed[6].set()
            if 'CLAW_CLASSIC_BASELINE ' in line and 'vertical=0 raised=1' in line and 'kind=number' in line:
                observed[8 if 'scale=200' in line else 7].set()
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

    boxes=re.findall(r'CLAW_CLASSIC vertical=(\d) units=(\d) center=(\d) right=(\d) gap=([\d.]+) inline=(\d) x=([\d.-]+) y=([\d.-]+) w=([\d.]+) h=([\d.]+) sw=([\d.]+) sh=([\d.]+) ox=(-?\d+) oy=(-?\d+)',log)
    assert boxes,'Classic native branch did not report its actual windows'
    settled=[]
    for vertical,units,center,right,gap,inline,x,y,w,h,sw,sh,ox,oy in boxes:
        x,y,w,h,sw,sh,ox,oy=map(float,(x,y,w,h,sw,sh,ox,oy))
        if center=='1':
            assert abs(y+h/2-sh/2-oy)<2,('Classic vertical centering drift',boxes)
            assert abs(x-(sw-w+ox if right=='1' else ox))<2,('Classic edge anchor drift',boxes)
            settled.append((vertical,right))
    assert set(settled)=={('0','0'),('0','1'),('1','0'),('1','1')},('Both center edges in both orientations were not drawn',settled)
    assert 'CLAW_CLASSIC_UNIT vertical=0 raised=0' in log and 'CLAW_CLASSIC_UNIT vertical=1 raised=1' in log
    assert 'CLAW_CLASSIC_LEGACY unit=' in log,'Non-inline superscript unit path was not drawn'
    widths={}
    for b in boxes:
        if b[0]=='0' and b[1]=='0' and b[2]=='1' and b[3]=='0' and b[5]=='1':widths.setdefault(float(b[4]),[]).append(float(b[8]))
    assert 0 in widths and 24 in widths and max(widths[24])>min(widths[0])+20,('Horizontal group spacing did not change native width',widths)
    print('PASS classic native options: normal/superscript, non-inline units, both center edges in both orientations and independent group spacing.')

    alignment={}
    for frame,token,scale,top,bottom in re.findall(r'CLAW_CLASSIC_ALIGN frame=(\d+) token=(\d+) scale=(\d+) top=([\d.-]+) bottom=([\d.-]+)',log):
        alignment.setdefault((int(frame),int(scale)),{})[int(token)]=(float(top)+float(bottom))/2
    compared=[]
    for (frame,scale),labels in alignment.items():
        if {3,28,29}<=labels.keys():
            assert max(labels.values())-min(labels.values())<=2,('AVG/1% LOW are not centered with CPU',frame,scale,labels)
            compared.append(scale)
    assert 200 in compared,('No large-FPS alignment evidence',alignment)
    print('PASS actual glyph geometry: AVG, 1% LOW and CPU share a vertical center at 100% and 200% FPS scale.')

    # The previous check compared labels only. Also compare the separately
    # captured production number/unit ink against each label in the same frame.
    baselines={}
    pattern=r'CLAW_CLASSIC_BASELINE frame=(\d+) token=(\d+) vertical=(\d) raised=(\d) scale=(\d+) kind=(label|number|unit) top=([\d.-]+) bottom=([\d.-]+)'
    for frame,token,vertical,raised,scale,kind,top,bottom in re.findall(pattern,log):
        baselines.setdefault((int(frame),int(vertical),int(raised),int(scale)),{})[(int(token),kind)]=(float(top),float(bottom))
    checked=set()
    for (_,vertical,raised,scale),ink in baselines.items():
        if not all((token,kind) in ink for token in (28,29) for kind in ('label','number','unit')) or (3,'label') not in ink or (4,'number') not in ink:continue
        for label_token,number_token in ((3,4),(28,28),(29,29)):
            label=ink[(label_token,'label')];number=ink[(number_token,'number')]
            assert abs(label[1]-number[1])<=1,('Classic label and number baselines differ',vertical,raised,scale,label_token,label,number)
            if raised:
                unit=ink[(number_token,'unit')]
                assert unit[1]<number[1],('Superscript unit baseline was not raised',label_token,unit,number)
        checked.add((vertical,raised,scale))
    assert {(0,0,100),(0,0,200),(0,1,100),(0,1,200)}<=checked,('Missing normal/superscript baseline comparisons',checked)
    print('PASS production glyph baselines: classic labels and numbers align with units off/on at FPS 100/200%; only unit baselines are raised.')
    tdp=re.findall(r'CLAW_TDP_STYLE vertical=(\d) raised=(\d) token=(\d+) color=([0-9a-f]+) color_ok=(\d) custom_font=(\d) separate_fonts=(\d) vertices=(\d+)',log)
    for vertical,raised in (('0','0'),('0','1'),('1','1')):
        for token,color in (('32','ff12acff'),('27','ffffeedd')):
            matches=[item for item in tdp if item[:3]==(vertical,raised,token) and int(item[-1])>=12]
            assert matches,('Missing separately styled native TDP',vertical,raised,token,tdp)
            assert all(item[3]==color and item[4:7]==('1','1','1') for item in matches),('TDP color/font leaked between label and value',matches)
    print('PASS classic TDP: independent label/value glyph colors and different selected fonts in horizontal/vertical and normal/superscript modes.')
