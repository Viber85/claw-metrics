import pathlib
import subprocess
import tempfile
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
class BatteryDisplayTests(unittest.TestCase):
    def test_charge_states_and_invalid_estimates_before_integer_conversion(self):
        source=r'''
#include "claw_battery_time.h"
#include <cassert>
#include <limits>
using namespace claw_modular;
int main(){
 for(const auto status:{"Charging","Full","Not charging"})for(double h:{0.,-1.,2.25,std::numeric_limits<double>::infinity(),std::numeric_limits<double>::quiet_NaN()}){
  auto r=battery_time(1,status,h);assert(r.plugged&&r.text.empty());
 }
 for(const auto status:{"Discharging","Unknown",""})for(double h:{0.,-1.,100.,1e30,std::numeric_limits<double>::infinity(),std::numeric_limits<double>::quiet_NaN()}){
  auto r=battery_time(1,status,h);assert(!r.plugged&&r.text=="--");
 }
 assert(battery_time(1,"Discharging",2.25).text=="02:15");
 assert(battery_time(1,"Discharging",99.99).text=="99:59");
 assert(battery_time(1,"Unknown",2.25).text=="--");
 assert(!battery_time(0,"Charging",2.25).plugged);
 assert(battery_time(0,"Discharging",2.25).text=="--");
 assert(battery_time(1,"Discharging",.001).text=="--");
}
'''
        with tempfile.TemporaryDirectory() as directory:
            src=pathlib.Path(directory)/'probe.cpp';src.write_text(source)
            binary=pathlib.Path(directory)/'probe'
            subprocess.run(['g++','-std=c++14','-fsanitize=undefined,float-cast-overflow','-fno-sanitize-recover=all','-I',str(ROOT/'experiments/native'),str(src),'-o',str(binary)],check=True)
            subprocess.run([str(binary)],check=True)
