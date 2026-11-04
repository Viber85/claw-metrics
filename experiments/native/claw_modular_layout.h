#pragma once
// Experimental geometry engine. No Vulkan, global HUD state or config watcher access.
#include <algorithm>
#include <cmath>
#include <functional>
#include <stdexcept>
#include <string>
#include <vector>

namespace claw_modular {
struct Size { float w=0,h=0; };
struct Rect { float x=0,y=0,w=0,h=0; bool visible=false; };
enum class Axis { Row, Column };
enum class Align { Start, Center, End };
enum class SelfAlign { Auto, Start, Center, End };
enum class Anchor { TopLeft, TopCenter, TopRight, BottomLeft, BottomCenter, BottomRight };
struct Node {
    std::string id,token;
    bool group=true,visible=true;
    Axis axis=Axis::Row;
    Align align=Align::Center;
    SelfAlign self_align=SelfAlign::Auto;
    float gap=8,padding=0,scale=1,width=180,height=44;
    std::vector<size_t> children;
};
struct Result { std::vector<Rect> boxes; bool outside=false; };
using Measure=std::function<Size(const std::string&,float)>;

inline bool finite(float x) { return std::isfinite(x); }
inline bool range(float x,float lo,float hi) { return finite(x)&&x>=lo&&x<=hi; }
inline Result layout(const std::vector<Node>& nodes, size_t root, Size screen,
                     Anchor anchor,float x,float y,float font,const Measure& measure) {
    if(nodes.empty()||nodes.size()>96||root>=nodes.size()||!nodes[root].group||
       !range(screen.w,1,32768)||!range(screen.h,1,32768)||!range(x,0,2000)||
       !range(y,0,2000)||!range(font,1,256)||static_cast<int>(anchor)<0||static_cast<int>(anchor)>5||!measure)
        throw std::invalid_argument("Invalid layout input");
    std::vector<bool> visited(nodes.size(),false);
    std::vector<std::string> ids;
    // Validate the complete tree, including hidden branches, before any measuring.
    std::function<void(size_t,int)> validate=[&](size_t i,int depth) {
        if(i>=nodes.size()||depth>8||visited[i])throw std::invalid_argument("Cycle, repeated parent or depth limit");
        visited[i]=true;
        const auto& n=nodes[i];
        if(n.id.size()>400||std::find(ids.begin(),ids.end(),n.id)!=ids.end()||
           (n.axis!=Axis::Row&&n.axis!=Axis::Column)||
           (n.align!=Align::Start&&n.align!=Align::Center&&n.align!=Align::End)||
           (n.self_align!=SelfAlign::Auto&&n.self_align!=SelfAlign::Start&&n.self_align!=SelfAlign::Center&&n.self_align!=SelfAlign::End)||
           !range(n.gap,0,80)||!range(n.padding,0,80)||!range(n.scale,.5,2.5)||
           !range(n.width,40,1000)||!range(n.height,n.token=="separator"?1.f:16.f,240)||(!n.group&&!n.children.empty())||
           (!n.group&&n.token.empty()))throw std::invalid_argument("Invalid node");
        ids.push_back(n.id);
        for(auto child:n.children)validate(child,depth+1);
    };
    validate(root,0);
    if(std::find(visited.begin(),visited.end(),false)!=visited.end())throw std::invalid_argument("Unreachable nodes");
    std::vector<Size> sizes(nodes.size());
    std::function<Size(size_t,float)> size=[&](size_t i,float inherited) -> Size {
        const auto& n=nodes[i];if(!n.visible)return {};
        const float scale=inherited*n.scale;
        Size out;
        if(!n.group) {
            // Graph dimensions are CSS/device pixels, like DevLab's SVG attributes.
            out=(n.token=="graph"||n.token=="separator")?Size{n.width,n.height}:measure(n.token,font*scale);
            if(!range(out.w,0,1000000)||!range(out.h,0,1000000))throw std::invalid_argument("Invalid metric measurement");
        } else {
            size_t count=0;
            for(auto child:n.children) {
                if(!nodes[child].visible)continue;
                const auto c=size(child,scale);
                if(n.axis==Axis::Row){out.w+=c.w;out.h=std::max(out.h,c.h);}
                else {out.h+=c.h;out.w=std::max(out.w,c.w);}
                ++count;
            }
            const float gaps=count?float(count-1)*n.gap:0;
            if(n.axis==Axis::Row)out.w+=gaps;else out.h+=gaps;
        }
        out.w+=2*n.padding;out.h+=2*n.padding;
        sizes[i]=out;return out;
    };
    const auto total=size(root,1);
    float left=x,top=y;
    if(anchor==Anchor::TopCenter||anchor==Anchor::BottomCenter)left=(screen.w-total.w)/2+x;
    if(anchor==Anchor::TopRight||anchor==Anchor::BottomRight)left=screen.w-total.w-x;
    if(anchor==Anchor::BottomLeft||anchor==Anchor::BottomCenter||anchor==Anchor::BottomRight)top=screen.h-total.h-y;
    Result out;out.boxes.resize(nodes.size());
    std::function<void(size_t,float,float)> place=[&](size_t i,float px,float py) {
        const auto& n=nodes[i];if(!n.visible)return;
        const auto s=sizes[i];out.boxes[i]={px,py,s.w,s.h,true};
        float cursor=0;
        for(auto child:n.children) {
            if(!nodes[child].visible)continue;
            const auto c=sizes[child];
            float cross=n.axis==Axis::Row?s.h-2*n.padding-c.h:s.w-2*n.padding-c.w;
            const auto alignment=nodes[child].self_align==SelfAlign::Auto?n.align:
                nodes[child].self_align==SelfAlign::Start?Align::Start:
                nodes[child].self_align==SelfAlign::Center?Align::Center:Align::End;
            cross=alignment==Align::Start?0:alignment==Align::Center?cross/2:cross;
            place(child,px+n.padding+(n.axis==Axis::Row?cursor:cross),py+n.padding+(n.axis==Axis::Row?cross:cursor));
            cursor+=(n.axis==Axis::Row?c.w:c.h)+n.gap;
        }
    };
    place(root,left,top);
    out.outside=left<0||top<0||left+total.w>screen.w||top+total.h>screen.h;
    return out;
}
} // namespace claw_modular
