#pragma once
#include <cmath>
#include <locale>
#include <sstream>
#include <string>
#include <utility>
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
inline std::pair<std::string,std::string> power_parts(const std::string& value,const std::string& fallback){
    auto text=power_text(value,fallback);
    // A unit may be attached or separated, and labels may contain spaces.
    if(text.size()>2&&text.compare(text.size()-2,2," W")==0)text.erase(text.size()-2,1);
    const auto split=text.find_last_of(' ');
    return split==std::string::npos?std::make_pair(fallback,text):std::make_pair(text.substr(0,split),text.substr(split+1));
}
}
