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
// Append new anchors: existing transport IDs 0..5 must remain stable.
enum class Anchor { TopLeft, TopCenter, TopRight, BottomLeft, BottomCenter, BottomRight, CenterLeft, CenterRight };
struct Node {
    std::string id,token;
    bool group=true,visible=true;
    int font_weight=0; // 0 inherits the group/plugin; 1..4 are bundled faces.
    Axis axis=Axis::Row;
    Align align=Align::Center;
    SelfAlign self_align=SelfAlign::Auto;
    float gap=8,padding=0,scale=1,width=180,height=44;
    float overlay_padding_x=0,overlay_padding_y=0; // Per-element X/Y insets; root values come from the transport header.
    // Negative one inherits the corresponding legacy symmetric inset.
    float padding_left=-1,padding_right=-1,padding_top=-1,padding_bottom=-1;
    float min_width=0;
    std::vector<size_t> children;
};
inline bool is_graph(const std::string& token) { return token=="graph" || token=="graph.framegen"; }
struct Result { std::vector<Rect> boxes; bool outside=false; };
using Measure=std::function<Size(const std::string&,float)>;
using NodeMeasure=std::function<Size(size_t,const std::string&,float)>;

// Explicit per-axis padding defaults to zero for every element.
inline float inset_left(const Node& node) { return node.padding_left>=0?node.padding_left:node.overlay_padding_x; }
inline float inset_right(const Node& node) { return node.padding_right>=0?node.padding_right:node.overlay_padding_x; }
inline float inset_top(const Node& node) { return node.padding_top>=0?node.padding_top:node.overlay_padding_y; }
inline float inset_bottom(const Node& node) { return node.padding_bottom>=0?node.padding_bottom:node.overlay_padding_y; }
inline float horizontal_insets(const Node& node) { return inset_left(node)+inset_right(node); }
inline float vertical_insets(const Node& node) { return inset_top(node)+inset_bottom(node); }
inline bool finite(float x) { return std::isfinite(x); }
inline bool range(float x,float lo,float hi) { return finite(x)&&x>=lo&&x<=hi; }
inline Result layout(const std::vector<Node>& nodes, size_t root, Size screen,
                     Anchor anchor,float x,float y,float font,const Measure& measure,const NodeMeasure& node_measure={}) {
    if(nodes.empty()||nodes.size()>96||root>=nodes.size()||!nodes[root].group||
       !range(screen.w,1,32768)||!range(screen.h,1,32768)||!range(x,0,2000)||
       !range(y,anchor==Anchor::CenterLeft||anchor==Anchor::CenterRight?-2000.f:0.f,2000)||!range(font,1,256)||static_cast<int>(anchor)<0||static_cast<int>(anchor)>7||!measure)
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
           (n.font_weight<0||n.font_weight>4)||!range(n.overlay_padding_x,0,160)||!range(n.overlay_padding_y,0,160)||
           !range(n.min_width,0,240)||
           !range(n.gap,0,n.group?240.f:80.f)||!range(n.padding,0,80)||!range(n.scale,.5,2.5)||
           !range(n.width,!n.group&&(is_graph(n.token)?0.f:n.token=="separator"?4.f:40.f),1000)||!range(n.height,n.token=="separator"?1.f:16.f,240)||(!n.group&&!n.children.empty())||
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
            if(n.token=="separator")
                out=n.axis==Axis::Column?Size{n.height,n.width}:Size{n.width,n.height};
            else if(is_graph(n.token))
                out={n.width,n.height};
            else
                out=node_measure?node_measure(i,n.token,font*scale):measure(n.token,font*scale);
            if(!range(out.w,0,1000000)||!range(out.h,0,1000000))throw std::invalid_argument("Invalid metric measurement");
            out.w=std::max(out.w,n.min_width);
        } else {
            size_t count=0;std::vector<size_t> children;float widest_non_auto_graph=0;
            for(auto child:n.children) {
                if(!nodes[child].visible)continue;
                auto c=size(child,scale);children.push_back(child);
                const bool auto_graph=!nodes[child].group&&is_graph(nodes[child].token)&&nodes[child].width==0;
                if(!auto_graph)widest_non_auto_graph=std::max(widest_non_auto_graph,c.w);
                if(n.axis==Axis::Row){out.w+=c.w;out.h=std::max(out.h,c.h);}
                else {out.h+=c.h;out.w=std::max(out.w,c.w);}
                ++count;
            }
            // A graph with width=0 follows the widest sibling in a vertical group.
            // This keeps it aligned with the readings row instead of overshooting it.
            for(auto child:children)if(!nodes[child].group&&is_graph(nodes[child].token)&&nodes[child].width==0){
                const float target=n.axis==Axis::Column&&widest_non_auto_graph>0?std::max(widest_non_auto_graph,horizontal_insets(nodes[child])+1.f):180.f+horizontal_insets(nodes[child]);
                sizes[child].w=target;
            }
            if(n.axis==Axis::Column){
                // Recompute after resolving auto-width graph children so their
                // own default padding cannot make the parent wider than readings.
                out.w=0;for(auto child:children)out.w=std::max(out.w,sizes[child].w);
            }else{out.w=0;for(auto child:children)out.w+=sizes[child].w;}
            const float gaps=count?float(count-1)*n.gap:0;
            if(n.axis==Axis::Row)out.w+=gaps;else out.h+=gaps;
        }
        out.w+=horizontal_insets(n);out.h+=vertical_insets(n);
        sizes[i]=out;return out;
    };
    const auto total=size(root,1);
    float left=x,top=y;
    if(anchor==Anchor::TopCenter||anchor==Anchor::BottomCenter)left=(screen.w-total.w)/2+x;
    if(anchor==Anchor::TopRight||anchor==Anchor::BottomRight||anchor==Anchor::CenterRight)left=screen.w-total.w-x;
    if(anchor==Anchor::BottomLeft||anchor==Anchor::BottomCenter||anchor==Anchor::BottomRight)top=screen.h-total.h-y;
    if(anchor==Anchor::CenterLeft||anchor==Anchor::CenterRight)top=(screen.h-total.h)/2+y;
    Result out;out.boxes.resize(nodes.size());
    std::function<void(size_t,float,float)> place=[&](size_t i,float px,float py) {
        const auto& n=nodes[i];if(!n.visible)return;
        const auto s=sizes[i];out.boxes[i]={px,py,s.w,s.h,true};
        const float px_inset=inset_left(n);
        const float py_inset=inset_top(n);float cursor=0;
        for(auto child:n.children) {
            if(!nodes[child].visible)continue;
            const auto c=sizes[child];
            float cross=n.axis==Axis::Row?s.h-vertical_insets(n)-c.h:s.w-horizontal_insets(n)-c.w;
            const auto alignment=nodes[child].self_align==SelfAlign::Auto?n.align:
                nodes[child].self_align==SelfAlign::Start?Align::Start:
                nodes[child].self_align==SelfAlign::Center?Align::Center:Align::End;
            cross=alignment==Align::Start?0:alignment==Align::Center?cross/2:cross;
            place(child,px+px_inset+(n.axis==Axis::Row?cursor:cross),py+py_inset+(n.axis==Axis::Row?cross:cursor));
            cursor+=(n.axis==Axis::Row?c.w:c.h)+n.gap;
        }
    };
    place(root,left,top);
    out.outside=left<0||top<0||left+total.w>screen.w||top+total.h>screen.h;
    return out;
}
} // namespace claw_modular
