#pragma once
#include "claw_modular_layout.h"
#include <atomic>
#include <cstdint>
#include <locale>
#include <memory>
#include <mutex>
#include <sstream>

namespace claw_modular {
struct Appearance {
    std::string color,background; // Six-digit RGB, empty means inherited/transparent.
    float opacity=100,corner_radius=-1;
    bool outline=false;
    float outline_width=1,outline_opacity=100;
    std::string outline_color="8FB8D9";
};
struct Document {
    std::vector<Node> nodes;
    std::vector<Appearance> appearance;
    Anchor anchor=Anchor::TopLeft;
    float x=0,y=0;
};
inline bool valid_color(const std::string& value){
    if(value=="-")return true;
    if(value.size()!=6)return false;
    for(char c:value)if(!((c>='0'&&c<='9')||(c>='a'&&c<='f')||(c>='A'&&c<='F')))return false;
    return true;
}
inline std::string decode_id(const std::string& value){
    if(value=="-")return "";
    if(value.size()>800||value.size()%2)throw std::invalid_argument("Invalid ID encoding");
    std::string out;
    for(size_t i=0;i<value.size();i+=2){
        unsigned byte=0;
        for(size_t j=0;j<2;++j){char c=value[i+j];int d=c>='0'&&c<='9'?c-'0':c>='a'&&c<='f'?c-'a'+10:-1;
            if(d<0)throw std::invalid_argument("Invalid ID encoding");
            byte=byte*16+d;}
        out+=static_cast<char>(byte);
    }
    return out;
}
inline Document decode(const std::string& bytes){
    if(bytes.size()>1024*1024)throw std::invalid_argument("Native layout exceeds 1 MiB");
    std::istringstream input(bytes);input.imbue(std::locale::classic());
    std::string magic;int anchor=0,count=0;Document doc;
    if(!(input>>magic>>anchor>>doc.x>>doc.y>>count)||(magic!="CLAW_MODULAR_V1"&&magic!="CLAW_MODULAR_V2"&&magic!="CLAW_MODULAR_V3"&&magic!="CLAW_MODULAR_V4"&&magic!="CLAW_MODULAR_V5")||anchor<0||anchor>7||count<1||count>96)
        throw std::invalid_argument("Invalid transport header");
    doc.anchor=static_cast<Anchor>(anchor);doc.nodes.resize(count);doc.appearance.resize(count);
    if((magic=="CLAW_MODULAR_V3"||magic=="CLAW_MODULAR_V4"||magic=="CLAW_MODULAR_V5")&&!(input>>doc.nodes[0].overlay_padding_x>>doc.nodes[0].overlay_padding_y))throw std::invalid_argument("Invalid overlay padding");
    const std::string tokens=" fps.label fps.value fps.ms fps.average fps.low1 cpu.label cpu.load cpu.temp cpu.clock cpu.power gpu.label gpu.load gpu.temp gpu.clock gpu.power gpu.junction gpu.fan gpu.voltage ram.label ram.value ram.game ram.swap vram.label vram.value vram.temp vram.clock battery.label battery.value battery.time battery.power time.value tdp.value graph separator ";
    for(int i=0;i<count;++i){
        auto& n=doc.nodes[i];auto& style=doc.appearance[i];std::string id;int group,visible,axis,align,self_align=0,outline,children;
        if(!(input>>id>>n.token>>group>>visible>>axis>>align)||
           (magic!="CLAW_MODULAR_V1"&&!(input>>self_align))||
           !(input>>n.gap>>n.padding>>n.scale>>n.width>>n.height>>style.color>>style.background>>style.opacity>>outline>>children)||
           group<0||group>1||visible<0||visible>1||axis<0||axis>1||align<0||align>2||outline<0||outline>1||children<0||children>96||
           self_align<0||self_align>3||
           !range(style.opacity,0,100)||!valid_color(style.color)||!valid_color(style.background)||tokens.find(" "+n.token+" ")==std::string::npos)
            throw std::invalid_argument("Invalid transport record");
        n.id=decode_id(id);n.group=group;n.visible=visible;n.axis=static_cast<Axis>(axis);n.align=static_cast<Align>(align);n.self_align=static_cast<SelfAlign>(self_align);style.outline=outline;
        if(magic=="CLAW_MODULAR_V4"||magic=="CLAW_MODULAR_V5"){
            float px=0,py=0;
            if(!(input>>px>>py>>style.outline_width>>style.outline_color>>style.outline_opacity)||
               !range(px,0,160)||!range(py,0,160)||!range(style.outline_width,0,12)||!range(style.outline_opacity,0,100)||
               !valid_color(style.outline_color)||(i==0&&(px!=0||py!=0)))throw std::invalid_argument("Invalid group appearance");
            if(i>0){n.overlay_padding_x=px;n.overlay_padding_y=py;}
            if(style.outline_color=="-")style.outline_color="8FB8D9";
        }
        if(magic=="CLAW_MODULAR_V5"){
            if(!(input>>style.corner_radius>>n.font_weight)||(style.corner_radius!=-1&&!range(style.corner_radius,0,1000))||n.font_weight<0||n.font_weight>4)
                throw std::invalid_argument("Invalid radius or font weight");
        }
        if(style.color=="-")style.color.clear();
        if(style.background=="-")style.background.clear();
        for(int j=0;j<children;++j){int child;if(!(input>>child)||child<0||child>=count)throw std::invalid_argument("Invalid child index");n.children.push_back(static_cast<size_t>(child));}
    }
    std::string trailing;if(input>>trailing)throw std::invalid_argument("Trailing layout data");
    // Structural/geometry validation runs before publishing, including hidden nodes.
    layout(doc.nodes,0,{1280,800},doc.anchor,doc.x,doc.y,24,[](const std::string&,float font){return Size{font,font};});
    return doc;
}
class Exchange {
    std::mutex mutex;
    std::shared_ptr<const Document> pending;
    std::uint64_t generation=0,consumed=0;
public:
    // Call from the loader. A rejected document never acquires the publication lock.
    void publish(const std::string& bytes){
        auto next=std::make_shared<const Document>(decode(bytes));
        std::lock_guard<std::mutex> guard(mutex);pending=std::move(next);++generation;
    }
    // Call only at a renderer frame boundary. Existing frames retain their snapshot.
    std::shared_ptr<const Document> take(){
        std::lock_guard<std::mutex> guard(mutex);
        if(consumed==generation)return {};
        consumed=generation;return pending;
    }
};
} // namespace claw_modular
