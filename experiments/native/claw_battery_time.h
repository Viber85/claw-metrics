#pragma once
#include <cmath>
#include <cstdio>
#include <string>
namespace claw_modular {
struct BatteryTime { std::string text="--"; bool plugged=false; };
inline BatteryTime battery_time(int count,const std::string& status,double hours){
    if(count<=0)return {};
    // Full/charge-limit states still indicate external power. Unknown is not proof.
    if(status=="Charging"||status=="Full"||status=="Not charging")return {"",true};
    // Validate BEFORE a float-to-integer conversion (infinity previously became INT_MIN).
    if(status!="Discharging"||!std::isfinite(hours)||hours<=0||hours>=100)return {};
    const int total=static_cast<int>(std::floor(hours*60));
    if(total<1)return {};
    char text[16];std::snprintf(text,sizeof(text),"%02d:%02d",total/60,total%60);
    return {text,false};
}
}
