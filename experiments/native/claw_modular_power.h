#pragma once
#include <cmath>
#include <locale>
#include <sstream>
#include <string>
namespace claw_modular {
inline std::string power_text(const std::string& value,const std::string& label){
    const auto unavailable=label+" --";
    if(value.empty()||value.size()>128)return unavailable;
    for(unsigned char c:value)if(c<32||c==127)return unavailable;
    const auto split=value.find_last_of(' ');
    if(split!=std::string::npos&&value.substr(split+1)=="--")return value;
    if(value.back()!='W')return unavailable;
    auto numeric=value.substr(0,value.size()-1);
    while(!numeric.empty()&&numeric.back()==' ')numeric.pop_back();
    const auto start=numeric.find_last_of(' ');
    numeric=numeric.substr(start==std::string::npos?0:start+1);
    std::istringstream input(numeric);input.imbue(std::locale::classic());
    double watts=0;
    if(!(input>>watts)||!input.eof()||!std::isfinite(watts)||watts< -100||watts>1000)return unavailable;
    return value;
}
}
