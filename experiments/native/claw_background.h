#pragma once
#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <string>
#include <vector>

struct ClawBackgroundRGB { float r,g,b; };
struct ClawBackgroundStop { float at; ClawBackgroundRGB color; };
class ClawBackgroundRamp {
    std::string encoded;
public:
    std::vector<ClawBackgroundStop> stops;
    void configure(const std::string& value) {
        if (encoded==value && stops.size()>=2) return;
        encoded=value; stops.clear();
        size_t start=0;
        while(start<value.size() && stops.size()<8) {
            size_t end=value.find('/',start);
            const std::string item=value.substr(start,end==std::string::npos?end:end-start);
            const auto colon=item.find(':');
            if(colon!=std::string::npos && item.size()-colon-1==6) {
                const auto pos=item.substr(0,colon), hex=item.substr(colon+1);
                char *tail=nullptr,*color_tail=nullptr;
                const float at=std::strtof(pos.c_str(),&tail);
                const unsigned rgb=std::strtoul(hex.c_str(),&color_tail,16);
                if(tail!=pos.c_str() && !*tail && !*color_tail && std::isfinite(at))
                    stops.push_back({std::max(0.f,std::min(1.f,at/100.f)),
                        {float((rgb>>16)&255)/255.f,float((rgb>>8)&255)/255.f,float(rgb&255)/255.f}});
            }
            if(end==std::string::npos) break;
            start=end+1;
        }
        std::stable_sort(stops.begin(),stops.end(),[](const ClawBackgroundStop&a,const ClawBackgroundStop&b){return a.at<b.at;});
        if(stops.size()<2) stops={{0,{.086f,.094f,.125f}},{1,{.086f,.094f,.125f}}};
    }
    ClawBackgroundRGB color(float t) const {
        if(t<stops.front().at) return stops.front().color;
        size_t next=0;
        while(next<stops.size() && stops[next].at<=t) ++next;
        if(next==stops.size()) return stops.back().color;
        const auto&a=stops[next-1]; const auto&b=stops[next];
        const float f=std::max(0.f,std::min(1.f,(t-a.at)/(b.at-a.at)));
        return {a.color.r+(b.color.r-a.color.r)*f,a.color.g+(b.color.g-a.color.g)*f,a.color.b+(b.color.b-a.color.b)*f};
    }
    static float position(float x,float y,float w,float h,int mode,float angle,float cx,float cy,float radius) {
        if(mode==2) {
            const float dx=x-w*cx/100.f,dy=y-h*cy/100.f;
            return std::hypot(dx,dy)/std::max(1.f,std::hypot(w,h)*.5f*radius/100.f);
        }
        const float a=angle*3.14159265358979323846f/180.f;
        const float c=std::cos(a),s=std::sin(a);
        return .5f+((x-w*.5f)*c+(y-h*.5f)*s)/std::max(1.f,std::abs(c)*w+std::abs(s)*h);
    }
};
