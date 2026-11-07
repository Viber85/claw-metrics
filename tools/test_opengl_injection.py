#!/usr/bin/env python3
"""Smoke-test the packaged GLX path with software OpenGL, not a device game."""
import os
import pathlib
import subprocess
import tempfile
import time

root = pathlib.Path(__file__).resolve().parents[1]
library = (root / 'native64/libMangoHud_opengl.so').resolve()
shim = (root / 'native64/libMangoHud_shim.so').resolve()
assert library.is_file() and shim.is_file()

with tempfile.TemporaryDirectory(prefix='claw-opengl-ci-') as folder:
    config = pathlib.Path(folder) / 'MangoHud.conf'
    config.write_text('fps=1\nbackground_alpha=0.8\n', encoding='utf-8')
    env = {**os.environ, 'MANGOHUD_CONFIGFILE': str(config),
           'MANGOHUD_OPENGL_LIBS': str(library),
           'LD_PRELOAD': (os.environ.get('LD_PRELOAD', '') + ':' + str(shim)).strip(':')}
    process = subprocess.Popen(['glxgears', '-info'], env=env,
                               stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        loaded = False
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            assert process.poll() is None, 'GLX process exited before library loaded'
            try:
                maps = pathlib.Path(f'/proc/{process.pid}/maps').read_text()
            except OSError:
                maps = ''
            if str(library) in maps:
                loaded = True
                break
            time.sleep(.1)
        assert loaded, 'OpenGL shim did not load the modified renderer'
        time.sleep(2)
        assert process.poll() is None, 'OpenGL renderer crashed after loading'
        print('PASS GLX: modified OpenGL renderer loaded through isolated shim and stayed running')
    finally:
        process.terminate()
        try:
            process.communicate(timeout=4)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
