#pragma once
#include "claw_modular_layout.h"
#include "imgui.h"
#include <limits>
#include <map>
#include <cstring>
#include <cstdlib>
#include <cstdio>

namespace claw_modular {
struct Text {
    std::string value;
    ImFont* font=nullptr; // Borrowed from a live atlas; never rebuilt by this adapter.
    ImU32 color=IM_COL32(240,242,245,255);
    std::string slot{};
    // Optional category prefix with an independent font and color. Existing
    // layout nodes remain valid; their explicit color still overrides both.
    std::string prefix{};
    ImFont* prefix_font=nullptr;
    ImU32 prefix_color=IM_COL32(240,242,245,255);
};
struct Style {
    ImU32 fill=0,outline=0,text=0;
    float rounding=0,outline_width=1;
};
struct Frame {
    std::vector<Node> nodes;
    std::vector<Style> styles;
    std::map<std::string,Text> readings;
    std::vector<float> graph;
    Result geometry;
    Size screen;
    size_t root=0;
    float font_size=24;
    ImU32 graph_color=IM_COL32(48,229,160,255);
    ImU32 separator_color=IM_COL32(240,242,245,255);
    int graph_style=0;
    bool unit_superscript=false;
};
inline std::pair<std::string,std::string> unit_parts(const std::string& token,const std::string& value) {
    const char* suffix=nullptr;
    const bool temperature=token=="cpu.temp"||token=="gpu.temp"||token=="gpu.junction"||token=="vram.temp";
    if(temperature)suffix=value.find("°F")!=std::string::npos?"°F":"°C";
    else if(token=="cpu.clock"||token=="gpu.clock"||token=="vram.clock")suffix=" MHz";
    else if(token=="ram.value"||token=="vram.value"||token=="ram.game"||token=="ram.swap")suffix=" GiB";
    else if(token=="fps.ms")suffix=" ms";
    else if(token=="cpu.power"||token=="gpu.power"||token=="battery.power"||token=="tdp.value")suffix="W";
    else if(token=="cpu.load"||token=="gpu.load"||token=="battery.value")suffix="%";
    else if(token=="gpu.voltage")suffix=" mV";
    else if(token=="gpu.fan")suffix=value.find("RPM")!=std::string::npos?" RPM":"% FAN";
    if(!suffix)return {value,{}};
    const size_t length=std::strlen(suffix);
    if(value.size()<=length||value.compare(value.size()-length,length,suffix)!=0)return {value,{}};
    auto main=value.substr(0,value.size()-length);
    if(main.find_first_of("0123456789")==std::string::npos)return {value,{}};
    while(!main.empty()&&main.back()==' ')main.pop_back();
    std::string unit=suffix;while(!unit.empty()&&unit.front()==' ')unit.erase(0,1);
    return {std::move(main),std::move(unit)};
}
inline float unit_gap(float size) { return size*.14f; }
inline float prefix_width(const Text& text,float size){
    return text.prefix.empty()?0:(text.prefix_font?text.prefix_font:text.font)->CalcTextSizeA(size,std::numeric_limits<float>::max(),0,text.prefix.c_str()).x+size*.25f;
}
inline Size reading_size(const Text& text,const std::string& token,float size,bool superscript,const std::string& value) {
    const auto parts=unit_parts(token,value);
    auto extent=text.font->CalcTextSizeA(size,std::numeric_limits<float>::max(),0,parts.first.c_str());
    if(!parts.second.empty()){
        extent.x+=unit_gap(size)+text.font->CalcTextSizeA(size*(superscript?.7f:1.f),std::numeric_limits<float>::max(),0,parts.second.c_str()).x;
        if(superscript)extent.y+=size*.18f;
    }
    return {prefix_width(text,size)+extent.x,extent.y};
}
inline Frame prepare(std::vector<Node> nodes,std::vector<Style> styles,
                     std::map<std::string,Text> readings, std::vector<float> graph,
                     size_t root,Size screen,Anchor anchor,float x,float y,float font,bool unit_superscript=false) {
    if(styles.size()!=nodes.size()||graph.size()>30000)throw std::invalid_argument("Invalid drawing snapshot");
    for(const auto& s:styles)if(!range(s.rounding,0,80)||!range(s.outline_width,0,6))throw std::invalid_argument("Invalid drawing style");
    for(float value:graph)if(!range(value,0,1000000))throw std::invalid_argument("Invalid graph sample");
    Frame frame;frame.nodes=std::move(nodes);frame.styles=std::move(styles);
    frame.readings=std::move(readings);frame.graph=std::move(graph);
    frame.root=root;frame.screen=screen;frame.font_size=font;frame.unit_superscript=unit_superscript;
    // One immutable reading snapshot supplies both measurement and drawing.
    frame.geometry=layout(frame.nodes,root,screen,anchor,x,y,font,[&](const std::string& token,float size){
        const auto it=frame.readings.find(token);
        if(it==frame.readings.end()||!it->second.font||!it->second.font->IsLoaded()||it->second.value.size()>16384)
            throw std::invalid_argument("Missing font or reading");
        const auto& text=it->second;
        auto extent=reading_size(text,token,size,unit_superscript,text.value);
        if(!text.slot.empty()){
            auto slot=reading_size(text,token,size,unit_superscript,text.slot);
            extent.w=std::max(extent.w,slot.w);extent.h=std::max(extent.h,slot.h);
        }
        return extent;
    });
    return frame;
}
inline float text_offset(Align alignment,float available) {
    return alignment==Align::End?available:alignment==Align::Center?available/2:0;
}
inline void paint(const Frame& frame,ImDrawList* draw) {
    if(!draw)throw std::invalid_argument("Missing draw list");
    draw->PushClipRect(ImVec2(0,0),ImVec2(frame.screen.w,frame.screen.h),true);
    std::function<void(size_t,float,Align)> visit=[&](size_t i,float inherited,Align horizontal_alignment){
        const auto& box=frame.geometry.boxes[i];if(!box.visible)return;
        const auto& n=frame.nodes[i];const auto& style=frame.styles[i];
        const float scale=inherited*n.scale;
        const ImVec2 lo(box.x,box.y),hi(box.x+box.w,box.y+box.h);
        if(style.fill>>24)draw->AddRectFilled(lo,hi,style.fill,style.rounding);
        if((style.outline>>24)&&style.outline_width>0){
            const float inset=style.outline_width/2;
            if(box.w>2*inset&&box.h>2*inset)draw->AddRect(ImVec2(lo.x+inset,lo.y+inset),ImVec2(hi.x-inset,hi.y-inset),style.outline,std::max(0.f,style.rounding-inset),0,style.outline_width);
        }
        if(n.group){for(auto child:n.children){
            const auto& item=frame.nodes[child];
            const Align alignment=n.axis==Axis::Column&&item.self_align!=SelfAlign::Auto?
                item.self_align==SelfAlign::Start?Align::Start:item.self_align==SelfAlign::Center?Align::Center:Align::End:
                n.axis==Axis::Column?n.align:Align::Start;
            visit(child,scale,alignment);
        }return;}
        if(n.token=="separator"){
            draw->AddRectFilled(ImVec2(lo.x+n.padding,lo.y+n.padding),ImVec2(hi.x-n.padding,hi.y-n.padding),style.text?style.text:frame.separator_color);
            return;
        }
        if(n.token=="graph"){
            if(frame.graph.size()<2)return;
            const auto graph_color=style.text?style.text:frame.graph_color;
            const int graph_first=draw->VtxBuffer.Size;
            // Bound each primitive reservation below 16-bit index limits;
            // larger documents use the backend's per-command VtxOffset support.
            std::vector<float> samples;
            const size_t sample_count=std::min<size_t>(64,frame.graph.size());
            for(size_t k=0;k<sample_count;++k)samples.push_back(frame.graph[k*(frame.graph.size()-1)/(sample_count-1)]);
            float max_value=1;for(float value:samples)max_value=std::max(max_value,value);
            const float width=box.w-2*n.padding,height=box.h-2*n.padding;
            const float baseline=hi.y-n.padding;
            std::vector<ImVec2> points;points.reserve(samples.size()*4);
            auto point=[&](float index,float value){return ImVec2(lo.x+n.padding+width*index/(samples.size()-1),baseline-height*std::max(0.f,std::min(max_value,value))/max_value);};
            if(frame.graph_style>=4){
                for(size_t k=0;k+1<samples.size();++k){
                    const float a=samples[k?k-1:k],b=samples[k],c=samples[k+1],d=samples[std::min(k+2,samples.size()-1)];
                    for(int j=0;j<4;++j){const float t=j/4.f,t2=t*t,t3=t2*t;
                        points.push_back(point(k+t,.5f*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t2+(-a+3*b-3*c+d)*t3)));}
                }
                points.push_back(point(samples.size()-1,samples.back()));
            }else for(size_t k=0;k<samples.size();++k)points.push_back(point(k,samples[k]));
            draw->PushClipRect(ImVec2(lo.x+n.padding,lo.y+n.padding),ImVec2(hi.x-n.padding,hi.y-n.padding),true);
            auto alpha=[&](unsigned value){return (graph_color&~IM_COL32_A_MASK)|(ImU32(value*int((graph_color>>IM_COL32_A_SHIFT)&255)/255)<<IM_COL32_A_SHIFT);};
            if(frame.graph_style==2){
                const float bar=std::max(1.f,width/samples.size()*.72f);
                for(const auto& p:points)draw->AddRectFilled(ImVec2(p.x,p.y),ImVec2(std::min(p.x+bar,hi.x-n.padding),baseline),graph_color);
            }else{
                if(frame.graph_style==1||frame.graph_style==3||frame.graph_style==5){
                    const ImU32 fill=frame.graph_style==1?graph_color:alpha(frame.graph_style==3?56:36);
                    const auto flags=draw->Flags;draw->Flags&=~ImDrawListFlags_AntiAliasedFill;
                    for(size_t k=1;k<points.size();++k)draw->AddQuadFilled(points[k-1],points[k],ImVec2(points[k].x,baseline),ImVec2(points[k-1].x,baseline),fill);
                    draw->Flags=flags;
                }
                if(frame.graph_style==5){
                    auto layer=points;float average=layer.front().y;
                    for(auto& p:layer){average=.85f*average+.15f*p.y;p.y=average;}
                    draw->AddPolyline(layer.data(),int(layer.size()),alpha(110),0,1.f);
                }
                draw->AddPolyline(points.data(),int(points.size()),graph_color,0,1.5f);
            }
            draw->PopClipRect();
            if(std::getenv("CLAW_METRICS_VERIFY")&&ImGui::GetFrameCount()%60==0){
                bool rgb_ok=true;for(int j=graph_first;j<draw->VtxBuffer.Size;++j)rgb_ok&=(draw->VtxBuffer[j].col&~IM_COL32_A_MASK)==(graph_color&~IM_COL32_A_MASK);
                std::fprintf(stderr,"CLAW_MODULAR_GRAPH_COLOR style=%d override=%d expected=%08x vertices=%d rgb_ok=%d\n",frame.graph_style,style.text?1:0,graph_color,draw->VtxBuffer.Size-graph_first,rgb_ok?1:0);
            }
        }else{
            const auto& text=frame.readings.at(n.token);
            const float size=frame.font_size*scale;
            const auto parts=unit_parts(n.token,text.value);
            const float width=reading_size(text,n.token,size,frame.unit_superscript,text.value).w;
            const float offset=text_offset(horizontal_alignment,std::max(0.f,box.w-2*n.padding-width));
            const auto color=style.text?style.text:text.color;
            const float prefix=prefix_width(text,size);
            const float baseline=lo.y+n.padding+(!parts.second.empty()&&frame.unit_superscript?size*.18f:0);
            const int prefix_first=draw->VtxBuffer.Size;
            if(!text.prefix.empty())draw->AddText(text.prefix_font?text.prefix_font:text.font,size,ImVec2(lo.x+n.padding+offset,baseline),style.text?style.text:text.prefix_color,text.prefix.c_str());
            const int number_first=draw->VtxBuffer.Size;
            draw->AddText(text.font,size,ImVec2(lo.x+n.padding+offset+prefix,baseline),color,parts.first.c_str());
            if(!parts.second.empty()){
                const float main_width=text.font->CalcTextSizeA(size,std::numeric_limits<float>::max(),0,parts.first.c_str()).x;
                draw->AddText(text.font,size*(frame.unit_superscript?.7f:1.f),ImVec2(lo.x+n.padding+offset+prefix+main_width+unit_gap(size),lo.y+n.padding),color,parts.second.c_str());
            }
            if(!text.prefix.empty()&&std::getenv("CLAW_METRICS_VERIFY")&&ImGui::GetFrameCount()%60==0){
                bool label_ok=true,value_ok=true;const auto label_color=style.text?style.text:text.prefix_color;
                for(int j=prefix_first;j<number_first;++j)label_ok&=draw->VtxBuffer[j].col==label_color;
                for(int j=number_first;j<draw->VtxBuffer.Size;++j)value_ok&=draw->VtxBuffer[j].col==color;
                std::fprintf(stderr,"CLAW_TDP_MODULAR raised=%d label_color=%08x value_color=%08x label_ok=%d value_ok=%d separate_fonts=%d label_vertices=%d value_vertices=%d\n",frame.unit_superscript?1:0,label_color,color,label_ok?1:0,value_ok?1:0,text.prefix_font!=text.font?1:0,number_first-prefix_first,draw->VtxBuffer.Size-number_first);
            }
        }
    };
    visit(frame.root,1,Align::Start);
    draw->PopClipRect();
}
} // namespace claw_modular
