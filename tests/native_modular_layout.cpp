#include "claw_modular_layout.h"
#include <cassert>
#include <iostream>
#include <limits>
using namespace claw_modular;
bool near(float a,float b){return std::abs(a-b)<.001f;}
int main(){
 Node root;root.id="root";root.padding=5;root.gap=10;root.children={1,2};
 Node a;a.id="a";a.group=false;a.token="fps.value";
 Node b=a;b.id="b";b.token="cpu.load";b.scale=2;
 std::vector<Node> nodes={root,a,b};
 auto measure=[](const std::string&,float font){return Size{font*2,font};};
 auto run=[&](Anchor anchor=Anchor::TopLeft){return layout(nodes,0,{1280,800},anchor,20,30,10,measure);};
 auto r=run();assert(near(r.boxes[0].w,80)&&near(r.boxes[0].h,30));
 assert(near(r.boxes[1].x,25)&&near(r.boxes[1].y,40));
 assert(near(r.boxes[2].x,55)&&near(r.boxes[2].y,35));
 for(auto anchor:{Anchor::TopLeft,Anchor::TopCenter,Anchor::TopRight,Anchor::BottomLeft,Anchor::BottomCenter,Anchor::BottomRight}){
  r=run(anchor);const bool bottom=anchor==Anchor::BottomLeft||anchor==Anchor::BottomCenter||anchor==Anchor::BottomRight;
  const bool center=anchor==Anchor::TopCenter||anchor==Anchor::BottomCenter;
  const bool right=anchor==Anchor::TopRight||anchor==Anchor::BottomRight;
  assert(near(r.boxes[0].x,center?620:right?1180:20));assert(near(r.boxes[0].y,bottom?740:30));assert(!r.outside);
 }
 nodes[0].axis=Axis::Column;r=run();assert(near(r.boxes[0].w,50)&&near(r.boxes[0].h,50));assert(near(r.boxes[1].x,35));
 nodes[0].align=Align::End;r=run();assert(near(r.boxes[1].x,45));
 nodes[0].align=Align::Start;r=run();assert(near(r.boxes[1].x,25));
 nodes[1].visible=false;r=run();assert(!r.boxes[1].visible);assert(near(r.boxes[0].h,30));
 nodes[2].visible=false;r=run();assert(near(r.boxes[0].w,10)&&near(r.boxes[0].h,10));
 nodes={root,a,b};nodes[2].token="graph";nodes[2].scale=2;r=run();assert(near(r.boxes[2].w,180)); // graph pixel dimensions don't scale with font
 nodes={root,a,b};nodes[0].children={1};nodes[1].group=true;nodes[1].scale=2;nodes[1].children={2};r=run();assert(near(r.boxes[2].h,40)); // inherited font scale
 auto rejects=[&](){try{run();return false;}catch(const std::invalid_argument&){return true;}};
 nodes[1].children={0};assert(rejects());
 nodes={root,a,b};nodes[0].children={1,1};assert(rejects());
 nodes={root,a,b};nodes[1].visible=false;nodes[1].children={2};assert(rejects());
 nodes={root,a,b};nodes[2].scale=std::numeric_limits<float>::quiet_NaN();assert(rejects());
 nodes={root,a,b};nodes[2].id=nodes[1].id;assert(rejects());
 nodes={root,a,b};r=layout(nodes,0,{40,20},Anchor::TopCenter,0,0,10,measure);assert(r.outside&&r.boxes[0].x<0);
 bool bad=false;try{layout(nodes,0,{1280,800},Anchor::TopLeft,0,0,10,[](const std::string&,float){return Size{-1,0};});}catch(const std::invalid_argument&){bad=true;}assert(bad);
 std::cout<<"PASS: nested layout, inherited scale, graph dimensions, all anchors, alignment, hidden children, overflow and invalid trees\n";
}
