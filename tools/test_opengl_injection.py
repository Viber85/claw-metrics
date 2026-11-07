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


def process_error(process, stage, env):
    details = process.stderr.read().decode(errors='replace')
    if process.returncode == -11:
        try:
            debug = subprocess.run(
                ['gdb', '--batch', '-ex', 'set pagination off', '-ex', 'run',
                 '-ex', 'thread apply all bt 15', '--args', 'glxgears', '-info'],
                env=env, capture_output=True, text=True, timeout=25,
            )
            details += '\nGDB trace:\n' + (debug.stdout + debug.stderr)[-16000:]
        except (OSError, subprocess.TimeoutExpired) as error:
            details += f'\nGDB unavailable: {error}'
    raise AssertionError(f'OpenGL process exited {stage} (code {process.returncode}): {details}')

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
            if process.poll() is not None:
                process_error(process, 'before library loaded', env)
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
        if process.poll() is not None:
            process_error(process, 'after library loaded', env)
        print('PASS GLX: modified OpenGL renderer loaded through isolated shim and stayed running')
    finally:
        process.terminate()
        try:
            process.communicate(timeout=4)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
