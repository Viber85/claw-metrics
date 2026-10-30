"""Exercise the packaged launcher, dynamic arch aliases, Vulkan and OpenGL."""
import asyncio, os, pathlib, re, subprocess, sys, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import main


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
            env=dict(os.environ,CLAW_METRICS_VERIFY='1',VK_ICD_FILENAMES='/usr/share/vulkan/icd.d/lvp_icd.x86_64.json',LIBGL_ALWAYS_SOFTWARE='1')
            result=subprocess.run(['xvfb-run','-a','-s','-screen 0 1920x1080x24',wrapper,'vkcube','--c','180','--width','1280','--height','720'],env=env,text=True,capture_output=True,timeout=120)
            log=result.stdout+'\n'+result.stderr
            assert result.returncode==0, log[-18000:]
            verify(log,'PACKAGED VULKAN')
            result=subprocess.run(['xvfb-run','-a','-s','-screen 0 1920x1080x24',wrapper,'timeout','8','glxgears','-geometry','1280x720'],env=env,text=True,capture_output=True,timeout=30)
            assert result.returncode in (0,124), result.stdout+'\n'+result.stderr
            verify(result.stdout+'\n'+result.stderr,'PACKAGED OPENGL')
        finally:
            await plugin._unload()
    print('PASS packaged launcher: private Vulkan and OpenGL, architecture dispatch, FPS draw ratio and centering.')


asyncio.run(run())
