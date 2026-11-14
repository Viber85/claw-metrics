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
icds=sorted(Path(os.environ.get('CLAW_TEST_ICD_DIR', '/usr/share/vulkan/icd.d')).glob('lvp_icd*.json'));assert icds
with tempfile.TemporaryDirectory() as directory:
    tmp=Path(directory);main.BASE=tmp/'profile';main.install_font();main.install_condensed_fonts()
    main.tdp_path().write_text('Power Limit 20W\n')
    config=tmp/'MangoHud.conf';transport=main.BASE/'modular.layout'
    manifest={'file_format_version':'1.0.0','layer':{'name':'VK_LAYER_CLAW_METRICS_modular_ci','type':'GLOBAL','api_version':'1.3.0','implementation_version':'1','description':'Modular renderer CI','library_path':str(ROOT/'native64/libMangoHud.so'),'functions':{'vkGetInstanceProcAddr':'overlay_GetInstanceProcAddr','vkGetDeviceProcAddr':'overlay_GetDeviceProcAddr'}}}
    (tmp/'modular.json').write_text(json.dumps(manifest))
    def atomic(path,text):
        staging=path.with_suffix('.tmp');staging.write_text(text);os.replace(staging,path)
    def settings(size=24, style="line", background="linear", enabled=True, units=False):
        value=main.normalize({'unit_superscript':units,'token_colors':{'tdp.label':'FFAC12','tdp.value':'DDEEFF'},'token_weights':{'tdp.label':'bold','tdp.value':'light'},'modular_enabled':enabled,'modular_layout':docs['two-rows'],'graph_style':style,'background':{'mode':background,'outline_enabled':True,'outline_width':2,'outline_opacity':60},'rounding':1000,'opacity':0 if background=='solid' else 80,'fontsize':size,'fps':True,'cpu':True,'gpu':True,'ram':True,'vram':True,'battery':True,'tdp':True,'draw':True,'frametime':True,'time':True,'hud_position':'top-left','metrics':{'graph':True,'fps_average':True,'fps_low1':True,'ram_game':True,'ram_swap':True}})
        atomic(config,main.mango_config(value,native_spacing=True)+'fps_limit=60\n')
        # Match the production Apply layout contract: the native loader watches
        # modular.layout.enabled, not modular_enabled in MangoHud.conf.
        atomic(transport.with_name(transport.name+'.enabled'), '1\n' if enabled else '0\n')
    docs={name:schema.load_layout((ROOT/f'experiments/modular/{name}.json').read_text()) for name in ('two-rows','graph-focus')}
    for document in docs.values():document.update(paddingX=7,paddingY=5)
    for document in docs.values():
        document['root'].update(outline=True,outlineWidth=2,outlineColor='#AA66FF',outlineOpacity=40)
        document['root']['children'][0].update(paddingX=5,paddingY=3,outline=True,outlineWidth=3,outlineColor='#22CC88',outlineOpacity=40)
    docs['graph-focus'].update(anchor='center-left',x=16,y=-12)
    stress=copy.deepcopy(docs['two-rows']);stress['root'].update(id='stress-root',axis='column',children=[])
    metric=copy.deepcopy(docs['two-rows']['root']['children'][1]['children'][1]['children'][-1])
    for row in range(4):
        group=copy.deepcopy(stress['root']);group.update(id=f'stress-row-{row}',axis='row',padding=2,gap=4,children=[])
        for column in range(8):
            child=copy.deepcopy(metric);child.update(id=f'stress-graph-{row}-{column}',width=80,height=32)
            group['children'].append(child)
        stress['root']['children'].append(group)
    def set_graph_color(node,color):
        if node['token']=='graph':node['color']=color
        for child in node['children']:set_graph_color(child,color)
    for document in docs.values():set_graph_color(document['root'],'#FF00FF')
    stress['x']=0
    docs['two-rows']['x']=0
    settings();atomic(transport,schema.encode_native(docs['two-rows']))
    stop=threading.Event();errors=[]
    def transitions():
        try:
            if stop.wait(2):return
            atomic(transport,'CLAW_MODULAR_V1\ntruncated')
            if stop.wait(2):return
            atomic(transport,schema.encode_native(docs['graph-focus']));settings(24,'area','radial',units=True)
            if stop.wait(2):return
            settings(26,'bars','solid',units=True)
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
            docs['graph-focus']['anchor']='center-right'
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
    positions=re.findall(r'CLAW_MODULAR .*? width=([\d.]+) height=([\d.]+) screen=([\d.]+)x([\d.]+).*? anchor=([67]) x=([\d.-]+) y=([\d.-]+)',log)
    assert {int(p[4]) for p in positions}=={6,7},('Both center edges were not drawn',positions)
    for w,h,sw,sh,anchor,x,y in positions:
        w,h,sw,sh,x,y=map(float,(w,h,sw,sh,x,y))
        assert abs(y+h/2-sh/2+12)<.3,('Not centered after layout/font changes',positions)
        assert abs(x-(16 if anchor=='6' else sw-w-16))<.3,('Wrong edge margin',positions)
    assert len({p[1] for p in positions if p[4]=='6'})>1,'Center anchor did not survive a height/font change'
    assert 'CLAW_EXTRA mode=0' in log,'Legacy fallback was not exercised'
    styles={int(x) for x in re.findall(r'CLAW_MODULAR .*? style=(\d+)',log)}
    assert styles==set(range(6)),('Missing graph style',styles)
    assert {int(x) for x in re.findall(r'CLAW_MODULAR .*? units=(\d+)',log)}=={0,1},'Normal/superscript live modes not both drawn'
    for mode in (1,2): assert f'CLAW_BACKGROUND mode={mode}' in log,('Missing modular gradient',mode)
    assert 'CLAW_OUTLINE mode=0' in log,'Transparent solid background lost its outline'
    print('PASS actual Vulkan: live FPS/text/graph geometry, two imported layouts, rejected partial file, font reload, restored layout and clean exit. Sensors are lavapipe/host fixtures, not handheld validation.')

    tdp=re.findall(r'CLAW_TDP_MODULAR raised=(\d) label_color=([0-9a-f]+) value_color=([0-9a-f]+) label_ok=(\d) value_ok=(\d) separate_fonts=(\d) label_vertices=(\d+) value_vertices=(\d+)',log)
    for raised in ('0','1'):
        matches=[item for item in tdp if item[0]==raised and int(item[-1])>=12]
        assert matches,('Missing modular TDP style evidence',raised,tdp)
        assert all(item[1:6]==('ff12acff','ffffeedd','1','1','1') for item in matches),('Modular TDP label/value styles leaked',matches)
    print('PASS modular TDP: independent title/value glyph colors and fonts with units off/on; existing layout nodes retained.')

    graph_colors=re.findall(r'CLAW_MODULAR_GRAPH_COLOR style=(\d+) override=(\d) expected=([0-9a-f]+) vertices=(\d+) rgb_ok=(\d)',log)
    custom=[row for row in graph_colors if row[1]=='1' and int(row[3])>0]
    assert {int(row[0]) for row in custom}==set(range(6)),('Missing graph override style',custom)
    assert all(row[2]=='ffff00ff' and row[4]=='1' for row in custom),('Saved graph color ignored by native primitives',custom)
    inherited=[row for row in graph_colors if row[1]=='0' and int(row[3])>0]
    assert inherited and all(row[4]=='1' for row in inherited),('Global graph fallback failed',inherited)
    print('PASS actual Vulkan graph colors: saved/imported magenta override on all six styles, including fills/layers; independent plugin-color fallback.')
