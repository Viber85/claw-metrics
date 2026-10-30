"""Exercise the packaged launcher, dynamic arch aliases, Vulkan and OpenGL."""
import asyncio, os, pathlib, re, subprocess, sys, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import main
icds=sorted(pathlib.Path('/usr/share/vulkan/icd.d').glob('lvp_icd*.json'), key=lambda p: ('x86_64' not in p.name, p.name))
assert icds, 'Lavapipe test driver is missing'
TEST_ICD=str(icds[0])



def verify(log, label):
    print(label+'\n'+log[-18000:])
    match=re.search(r'CLAW_RENDER screen=([\d.]+) x=([\d.-]+) y=([\d.-]+) width=([\d.]+) height=([\d.]+) fps_font=([\d.]+) scale=([\d.]+)',log)
    draw=re.search(r'CLAW_FPS actual=([\d.]+) normal=([\d.]+)',log)
    assert match and draw, label+' did not render with the private library'
    screen,x,y,width,height,fps,scale=map(float,match.groups())
    assert fps==34 and 0<scale<=1 and width<=screen-8 and x>=0, match.group()
    assert abs(x-(screen-width)/2)<2, match.group()
    assert abs(float(draw[1])/float(draw[2])-34/18)<0.01, draw.group()


async def run():
    with tempfile.TemporaryDirectory() as folder:
        main.BASE=pathlib.Path(folder)/'profile';main.CONFIG=main.BASE/'settings.json';main.HUD=main.BASE/'MangoHud.conf'
        plugin=main.Plugin();await plugin._main()
        try:
            assert (await plugin.get_info())['renderer_ready']
            settings=await plugin.get_settings();settings.update(renderer=True,center=True,auto_fit=True,offset_x=0,offset_y=8,fps_fontsize=34,padding_x=18,padding_y=10)
            await plugin.save_settings(settings)
            wrapper=str(main.BASE/'renderer/launch.sh')
            env=dict(os.environ,CLAW_METRICS_VERIFY='1',VK_ICD_FILENAMES=TEST_ICD,LIBGL_ALWAYS_SOFTWARE='1')
            result=subprocess.run(['xvfb-run','-a','-s','-screen 0 1920x1080x24',wrapper,'vkcube','--c','180','--width','1280','--height','720'],env=env,text=True,capture_output=True,timeout=120)
            log=result.stdout+'\n'+result.stderr
            assert result.returncode==0, log[-18000:]
            verify(log,'PACKAGED VULKAN')
            narrow=subprocess.run(['xvfb-run','-a','-s','-screen 0 1920x1080x24',wrapper,'vkcube','--c','180','--width','640','--height','480'],env=env,text=True,capture_output=True,timeout=120)
            assert narrow.returncode==0, narrow.stdout+'\n'+narrow.stderr
            narrow_log=narrow.stdout+'\n'+narrow.stderr
            verify(narrow_log,'PACKAGED VULKAN NARROW')
            fitted=re.search(r'scale=([\d.]+)',narrow_log)
            assert fitted and float(fitted[1])<1, 'Narrow render did not exercise fit-to-width'

            glx=main.BASE/'glx-fixture'
            subprocess.run(['gcc',str(pathlib.Path(__file__).with_name('glx_fixture.c')),'-lX11','-lGL','-o',str(glx)],check=True)
            result=subprocess.run(['xvfb-run','-a','-s','-screen 0 1920x1080x24',wrapper,str(glx)],env=env,text=True,capture_output=True,timeout=60)
            if result.returncode != 0:
                debug=subprocess.run(['xvfb-run','-a','-s','-screen 0 1920x1080x24','gdb','--batch','-ex','set exec-wrapper '+wrapper,'-ex','run','-ex','thread apply all bt','-ex','info proc mappings','--args',str(glx)],env=env,text=True,capture_output=True,timeout=120)
                print('OPENGL_DEBUG\n'+debug.stdout[:24000]+'\nMAP_TAIL\n'+debug.stdout[-6000:]+'\n'+debug.stderr[-8000:])
            assert result.returncode==0, result.stdout+'\n'+result.stderr
            verify(result.stdout+'\n'+result.stderr,'PACKAGED OPENGL')
            glx32=main.BASE/'glx-fixture32'
            subprocess.run(['gcc','-m32',str(pathlib.Path(__file__).with_name('glx_fixture.c')),'-lX11','-lGL','-o',str(glx32)],check=True)
            result=subprocess.run(['xvfb-run','-a','-s','-screen 0 1920x1080x24',wrapper,str(glx32)],env=env,text=True,capture_output=True,timeout=60)
            assert result.returncode==0, result.stdout+'\n'+result.stderr
            verify(result.stdout+'\n'+result.stderr,'PACKAGED OPENGL 32-BIT')
        finally:
            await plugin._unload()
    print('PASS packaged launcher: private Vulkan and OpenGL, architecture dispatch, FPS draw ratio and centering.')


asyncio.run(run())
