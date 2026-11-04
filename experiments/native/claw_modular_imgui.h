#pragma once
#include "claw_modular_layout.h"
#include "imgui.h"
#include <limits>
#include <map>

namespace claw_modular {
struct Text {
    std::string value;
    ImFont* font=nullptr; // Borrowed from a live atlas; never rebuilt by this adapter.
    ImU32 color=IM_COL32(240,242,245,255);
    std::string slot{};
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
};
inline Frame prepare(std::vector<Node> nodes,std::vector<Style> styles,
                     std::map<std::string,Text> readings, std::vector<float> graph,
                     size_t root,Size screen,Anchor anchor,float x,float y,float font) {
    if(styles.size()!=nodes.size()||graph.size()>30000)throw std::invalid_argument("Invalid drawing snapshot");
    for(const auto& s:styles)if(!range(s.rounding,0,80)||!range(s.outline_width,0,6))throw std::invalid_argument("Invalid drawing style");
    for(float value:graph)if(!range(value,0,1000000))throw std::invalid_argument("Invalid graph sample");
    Frame frame;frame.nodes=std::move(nodes);frame.styles=std::move(styles);
    frame.readings=std::move(readings);frame.graph=std::move(graph);
    frame.root=root;frame.screen=screen;frame.font_size=font;
    // One immutable reading snapshot supplies both measurement and drawing.
    frame.geometry=layout(frame.nodes,root,screen,anchor,x,y,font,[&](const std::string& token,float size){
        const auto it=frame.readings.find(token);
        if(it==frame.readings.end()||!it->second.font||!it->second.font->IsLoaded()||it->second.value.size()>16384)
            throw std::invalid_argument("Missing font or reading");
        const auto& text=it->second;
        auto extent=text.font->CalcTextSizeA(size,std::numeric_limits<float>::max(),0,text.value.c_str());
        if(!text.slot.empty())extent.x=std::max(extent.x,text.font->CalcTextSizeA(size,std::numeric_limits<float>::max(),0,text.slot.c_str()).x);
        return Size{extent.x,extent.y};
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
            auto alpha=[&](unsigned value){return (frame.graph_color&~IM_COL32_A_MASK)|(ImU32(value*int((frame.graph_color>>IM_COL32_A_SHIFT)&255)/255)<<IM_COL32_A_SHIFT);};
            if(frame.graph_style==2){
                const float bar=std::max(1.f,width/samples.size()*.72f);
                for(const auto& p:points)draw->AddRectFilled(ImVec2(p.x,p.y),ImVec2(std::min(p.x+bar,hi.x-n.padding),baseline),frame.graph_color);
            }else{
                if(frame.graph_style==1||frame.graph_style==3||frame.graph_style==5){
                    const ImU32 fill=frame.graph_style==1?frame.graph_color:alpha(frame.graph_style==3?56:36);
                    const auto flags=draw->Flags;draw->Flags&=~ImDrawListFlags_AntiAliasedFill;
                    for(size_t k=1;k<points.size();++k)draw->AddQuadFilled(points[k-1],points[k],ImVec2(points[k].x,baseline),ImVec2(points[k-1].x,baseline),fill);
                    draw->Flags=flags;
                }
                if(frame.graph_style==5){
                    auto layer=points;float average=layer.front().y;
                    for(auto& p:layer){average=.85f*average+.15f*p.y;p.y=average;}
                    draw->AddPolyline(layer.data(),int(layer.size()),alpha(110),0,1.f);
                }
                draw->AddPolyline(points.data(),int(points.size()),frame.graph_color,0,1.5f);
            }
            draw->PopClipRect();
        }else{
            const auto& text=frame.readings.at(n.token);
            const float width=text.font->CalcTextSizeA(frame.font_size*scale,std::numeric_limits<float>::max(),0,text.value.c_str()).x;
            const float offset=text_offset(horizontal_alignment,std::max(0.f,box.w-2*n.padding-width));
            draw->AddText(text.font,frame.font_size*scale,ImVec2(lo.x+n.padding+offset,lo.y+n.padding),style.text?style.text:text.color,text.value.c_str());
        }
    };
    visit(frame.root,1,Align::Start);
    draw->PopClipRect();
}
} // namespace claw_modular
