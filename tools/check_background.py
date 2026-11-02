"""Compile the production gradient sampler: stops, projection and circular distance."""
from pathlib import Path
import os,subprocess,sys,tempfile
source=Path(sys.argv[1])
code=r'''
#include "claw_background.h"
#include <cassert>
#include <iostream>
int main() {
 ClawBackgroundRamp ramp;
 ramp.configure("100:0000FF/0:FF0000/50:00FF00");
 assert(ramp.stops.size()==3);
 auto a=ramp.color(-1),b=ramp.color(.5),c=ramp.color(2),d=ramp.color(.25);
 assert(a.r==1 && c.b==1 && b.g==1);
 assert(std::abs(d.r-.5)<.001 && std::abs(d.g-.5)<.001);
 assert(std::abs(ClawBackgroundRamp::position(0,25,200,50,1,0,50,50,70))<.001);
 assert(std::abs(ClawBackgroundRamp::position(200,25,200,50,1,0,50,50,70)-1)<.001);
 assert(std::abs(ClawBackgroundRamp::position(100,0,200,50,1,90,50,50,70))<.001);
 assert(ClawBackgroundRamp::position(100,25,200,50,2,0,50,50,70)==0);
 // Radial distances are circular in pixel space, even for a wide HUD.
 auto x=ClawBackgroundRamp::position(120,25,200,50,2,0,50,50,70);
 auto y=ClawBackgroundRamp::position(100,45,200,50,2,0,50,50,70);
 assert(std::abs(x-y)<.001);
 ramp.configure("0:FF0000/50:00FF00/50:0000FF/100:FFFFFF");
 assert(ramp.color(.5).b==1); // coincident stops give a defined hard transition
 ramp.configure("invalid"); assert(ramp.stops.size()==2);
 for(int i=0;i<100000;++i) { auto rgb=ramp.color(float(i)/10000); assert(std::isfinite(rgb.r)); }
 std::cout<<"Production gradient sampler: multiple stops, boundaries, hard transitions, linear projection and circular radial distance passed\n";
}
'''
with tempfile.TemporaryDirectory() as folder:
 p=Path(folder);(p/'test.cpp').write_text(code)
 subprocess.run(['g++','-std=c++14','-O1','-fsanitize=address,undefined','-I',str(source),str(p/'test.cpp'),'-o',str(p/'test')],check=True)
 subprocess.run([str(p/'test')],check=True,env={**os.environ,'ASAN_OPTIONS':'detect_leaks=0'})
