"""Compile/test the exact production FPS accumulator and verify native integration."""
from pathlib import Path
import os
import subprocess
import sys
import tempfile

source = Path(sys.argv[1])
code = r'''
#include "claw_frame_metrics.h"
#include <cassert>
#include <limits>
#include <iostream>
int main() {
    ClawFrameMetrics stats;
    stats.add(0, 0); stats.add(0, -5);
    stats.add(0, std::numeric_limits<double>::quiet_NaN());
    stats.add(0, std::numeric_limits<double>::infinity());
    assert(stats.count()==0);
    for (int i=0; i<99; ++i) stats.add((i+1)*10000000ULL,10);
    assert(!stats.low1_ready && stats.low1==0);
    stats.add(1100000000ULL,100);
    assert(stats.count()==100 && stats.low1_ready);
    assert(std::abs(stats.average-100000.0/1090.0)<0.0001);
    assert(std::abs(stats.low1-10.0)<0.0001);
    // A long stall must remain in the statistics rather than being filtered out.
    stats.add(7000000000ULL,5900);
    assert(stats.average<20);
    stats.add(68000000000ULL,10);
    assert(stats.count()==1 && !stats.low1_ready && std::abs(stats.average-100)<0.0001);
    stats.reset();
    for (int i=0; i<200; ++i) stats.add((i+1)*10000000ULL,i<198?10:(i==198?100:300));
    assert(std::abs(stats.low1-5.0)<0.0001); // mean of two worst frame times is 200ms
    stats.add(1,20); // clock rollback resets the old window
    assert(stats.count()==1 && stats.average==50);
    stats.reset();
    for (int i=0; i<30100; ++i) stats.add(i*1000000ULL,1);
    assert(stats.count()==30000 && std::abs(stats.average-1000)<0.0001);
    std::cout << "Native FPS accumulator: average, slowest-1% mean, warm-up, 60s expiry, stalls, cap and reset passed\n";
}
'''
with tempfile.TemporaryDirectory() as directory:
    root=Path(directory)
    (root/'test.cpp').write_text(code)
    binary=root/'check'
    subprocess.run(['g++','-std=c++17','-O1','-g','-fsanitize=address,undefined',
                    '-I',str(source),str(root/'test.cpp'),'-o',str(binary)],check=True)
    subprocess.run([str(binary)],check=True,timeout=30,env={**os.environ,'ASAN_OPTIONS':'detect_leaks=0'})
hud=(source/'hud_elements.cpp').read_text()
assert 'ClawSupplementalReading("AVG",28' in hud
assert 'ClawSupplementalReading("1% LOW",29' in hud
assert hud.count('ClawSupplementalReading("GAME",30')==2  # compact and non-inline
assert hud.count('ClawSupplementalReading("SWAP",31')==2
fps=hud.split('void HudElements::fps(){',1)[1].split('void HudElements::fps_only()',1)[0]
assert fps.count('ClawFpsSummaries();')==2
assert 'proc_mem_resident / 1073741824.0,claw_proc_mem_valid' in hud
assert 'params.claw_ram_game' in (source/'overlay.cpp').read_text()
assert 'sw_stats.claw_frames.add(now, frametime_ms);' in (source/'overlay.cpp').read_text()
print('Native metric configuration, sampler and both layout branches connected')
