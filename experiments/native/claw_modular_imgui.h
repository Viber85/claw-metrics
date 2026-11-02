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
        const auto extent=text.font->CalcTextSizeA(size,std::numeric_limits<float>::max(),0,text.value.c_str());
        return Size{extent.x,extent.y};
    });
    return frame;
}
inline void paint(const Frame& frame,ImDrawList* draw) {
    if(!draw)throw std::invalid_argument("Missing draw list");
    draw->PushClipRect(ImVec2(0,0),ImVec2(frame.screen.w,frame.screen.h),true);
    std::function<void(size_t,float)> visit=[&](size_t i,float inherited){
        const auto& box=frame.geometry.boxes[i];if(!box.visible)return;
        const auto& n=frame.nodes[i];const auto& style=frame.styles[i];
        const float scale=inherited*n.scale;
        const ImVec2 lo(box.x,box.y),hi(box.x+box.w,box.y+box.h);
        if(style.fill>>24)draw->AddRectFilled(lo,hi,style.fill,style.rounding);
        if((style.outline>>24)&&style.outline_width>0){
            const float inset=style.outline_width/2;
            if(box.w>2*inset&&box.h>2*inset)draw->AddRect(ImVec2(lo.x+inset,lo.y+inset),ImVec2(hi.x-inset,hi.y-inset),style.outline,std::max(0.f,style.rounding-inset),0,style.outline_width);
        }
        if(n.group){for(auto child:n.children)visit(child,scale);return;}
        if(n.token=="graph"){
            if(frame.graph.size()<2)return;
            float max_value=1;for(float value:frame.graph)max_value=std::max(max_value,value);
            for(size_t k=1;k<frame.graph.size();++k){
                const float x0=lo.x+n.padding+(box.w-2*n.padding)*(k-1)/(frame.graph.size()-1);
                const float x1=lo.x+n.padding+(box.w-2*n.padding)*k/(frame.graph.size()-1);
                const float y0=hi.y-n.padding-(box.h-2*n.padding)*frame.graph[k-1]/max_value;
                const float y1=hi.y-n.padding-(box.h-2*n.padding)*frame.graph[k]/max_value;
                draw->AddLine(ImVec2(x0,y0),ImVec2(x1,y1),frame.graph_color,1.5f);
            }
        }else{
            const auto& text=frame.readings.at(n.token);
            draw->AddText(text.font,frame.font_size*scale,ImVec2(lo.x+n.padding,lo.y+n.padding),style.text?style.text:text.color,text.value.c_str());
        }
    };
    visit(frame.root,1);
    draw->PopClipRect();
}
} // namespace claw_modular
