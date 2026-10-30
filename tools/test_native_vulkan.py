"""Load the actual private Vulkan layer and exercise rendering via lavapipe/Xvfb."""
import base64, gzip, json, os, pathlib, re, subprocess, tempfile
root=pathlib.Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as folder:
    tmp=pathlib.Path(folder)
    font=tmp/'ClawSans.ttf'
    font.write_bytes(gzip.decompress(base64.b64decode((root/'assets/ClawSans.ttf.gz.b64').read_bytes())))
    config=tmp/'MangoHud.conf'
    config.write_text(f'''legacy_layout=0
horizontal=1
horizontal_stretch=0
hud_compact=0
position=top-left
claw_renderer=1
claw_center=1
claw_auto_fit=1
claw_fps_size=34
claw_padding_x=18
claw_padding_y=10
offset_x=0
offset_y=8
font_file={font}
font_file_text={font}
font_size=18
table_columns=64
fps=1
frametime=1
frame_timing=1
cpu_stats=1
cpu_temp=1
cpu_mhz=1
gpu_stats=1
gpu_temp=1
ram=1
vram=1
round_corners=12
background_alpha=0.8
''')
    manifest={'file_format_version':'1.0.0','layer':{'name':'VK_LAYER_CLAW_METRICS_overlay','type':'GLOBAL','api_version':'1.3.0','implementation_version':'1','description':'Claw Metrics private test renderer','library_path':str(root/'native-dist/libMangoHud.so'),'functions':{'vkGetInstanceProcAddr':'overlay_GetInstanceProcAddr','vkGetDeviceProcAddr':'overlay_GetDeviceProcAddr'}}}
    (tmp/'ClawMetrics.json').write_text(json.dumps(manifest))
    env=dict(os.environ, VK_LAYER_PATH=str(tmp), VK_INSTANCE_LAYERS='VK_LAYER_CLAW_METRICS_overlay', DISABLE_MANGOHUD='1', MANGOHUD_CONFIGFILE=str(config), CLAW_METRICS_VERIFY='1', VK_ICD_FILENAMES='/usr/share/vulkan/icd.d/lvp_icd.x86_64.json')
    result=subprocess.run(['xvfb-run','-a','-s','-screen 0 1920x1080x24','vkcube','--c','180','--width','1280','--height','720'],env=env,text=True,capture_output=True,timeout=120)
    log=result.stdout+'\n'+result.stderr
    print(log[-18000:])
    if result.returncode != 0:
        debug=subprocess.run(['xvfb-run','-a','-s','-screen 0 1920x1080x24','gdb','--batch','-ex','run','-ex','thread apply all bt','-ex','info proc mappings','--args','vkcube','--c','180','--width','1280','--height','720'],env=env,text=True,capture_output=True,timeout=120)
        print('DEBUG_BACKTRACE\n'+debug.stdout[-24000:]+'\n'+debug.stderr[-8000:])
    assert result.returncode == 0, result.returncode
    match=re.search(r'CLAW_RENDER screen=([\d.]+) x=([\d.-]+) y=([\d.-]+) width=([\d.]+) height=([\d.]+) fps_font=([\d.]+) scale=([\d.]+)',log)
    assert match, 'Private renderer did not report a rendered frame'
    screen,x,y,width,height,fps,scale=map(float,match.groups())
    assert fps==34 and y==8 and 0<scale<=1, match.group()
    assert abs(x-(screen-width)/2)<2, match.group()
    assert width<=screen-8 and x>=0 and height>20, match.group()
    fps_draw=re.search(r'CLAW_FPS actual=([\d.]+) normal=([\d.]+)',log)
    assert fps_draw and abs(float(fps_draw[1])/float(fps_draw[2])-34/18)<0.01, 'FPS font was not used in the actual draw branch'
    print('PASS actual Vulkan private layer: loaded, rendered, independent FPS font, measured centering and fit-to-width.')
