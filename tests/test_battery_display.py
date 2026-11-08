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
int main(int argc,char**argv){
 assert(argc==3);
 assert(external_power_online(argv[1]));assert(!external_power_online(argv[2]));
 assert(battery_time(1,"Unknown",std::numeric_limits<double>::infinity(),true).plugged);
 assert(battery_time(1,"Discharging",2.25,true).plugged);
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
            connected=pathlib.Path(directory)/'connected';disconnected=pathlib.Path(directory)/'disconnected'
            for root,online in ((connected,'1'),(disconnected,'0')):
                ac=root/'AC';ac.mkdir(parents=True);(ac/'type').write_text('Mains\n');(ac/'online').write_text(online)
                battery=root/'BAT0';battery.mkdir();(battery/'type').write_text('Battery\n');(battery/'online').write_text('1')
            subprocess.run([str(binary),str(connected),str(disconnected)],check=True)
