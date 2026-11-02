"""Compile and exercise the experimental geometry engine under sanitizers."""
from pathlib import Path
import os
import subprocess
import tempfile
ROOT = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as directory:
    binary = Path(directory) / 'modular-layout'
    subprocess.run(['g++', '-std=c++14', '-Wall', '-Wextra', '-Werror', '-O1',
                    '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                    '-I', str(ROOT / 'experiments/native'),
                    str(ROOT / 'tests/native_modular_layout.cpp'), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True, env={**os.environ, 'ASAN_OPTIONS': 'detect_leaks=0'})
