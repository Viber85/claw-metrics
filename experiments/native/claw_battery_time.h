#pragma once
#include <cmath>
#include <cstdio>
#include <string>
#include <fstream>
#include <dirent.h>
namespace claw_modular {
// Called by the existing battery sampler, never by per-frame drawing.
inline bool external_power_online(const std::string& root="/sys/class/power_supply"){
    DIR* directory=opendir(root.c_str());if(!directory)return false;
    bool connected=false;
    while(auto* entry=readdir(directory)){
        if(entry->d_name[0]=='.')continue;
        const auto base=root+"/"+entry->d_name;
        std::ifstream type_file(base+"/type");std::string type;
        if(!std::getline(type_file,type)||type=="Battery")continue;
        std::ifstream online(base+"/online");int value=0;
        if(online>>value&&value==1){connected=true;break;}
    }
    closedir(directory);return connected;
}
struct BatteryTime { std::string text="--"; bool plugged=false; };
inline BatteryTime battery_time(int count,const std::string& status,double hours,bool online=false){
    if(count<=0)return {};
    // Full/charge-limit states still indicate external power. Unknown is not proof.
    if(online||status=="Charging"||status=="Full"||status=="Not charging")return {"",true};
    // Validate BEFORE a float-to-integer conversion (infinity previously became INT_MIN).
    if(status!="Discharging"||!std::isfinite(hours)||hours<=0||hours>=100)return {};
    const int total=static_cast<int>(std::floor(hours*60));
    if(total<1)return {};
    char text[16];std::snprintf(text,sizeof(text),"%02d:%02d",total/60,total%60);
    return {text,false};
}
}
