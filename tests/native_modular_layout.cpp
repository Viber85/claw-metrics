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
 nodes[1].self_align=SelfAlign::Start;r=run();assert(near(r.boxes[1].y,35)&&near(r.boxes[2].y,35));
 nodes[1].self_align=SelfAlign::End;r=run();assert(near(r.boxes[1].y,45)&&near(r.boxes[2].y,35));
 nodes[1].self_align=SelfAlign::Auto;
 for(auto anchor:{Anchor::TopLeft,Anchor::TopCenter,Anchor::TopRight,Anchor::BottomLeft,Anchor::BottomCenter,Anchor::BottomRight}){
  r=run(anchor);const bool bottom=anchor==Anchor::BottomLeft||anchor==Anchor::BottomCenter||anchor==Anchor::BottomRight;
  const bool center=anchor==Anchor::TopCenter||anchor==Anchor::BottomCenter;
  const bool right=anchor==Anchor::TopRight||anchor==Anchor::BottomRight;
  assert(near(r.boxes[0].x,center?620:right?1180:20));assert(near(r.boxes[0].y,bottom?740:30));assert(!r.outside);
 }
 nodes[0].axis=Axis::Column;r=run();assert(near(r.boxes[0].w,50)&&near(r.boxes[0].h,50));assert(near(r.boxes[1].x,35));
 nodes[0].align=Align::End;r=run();assert(near(r.boxes[1].x,45));
 nodes[0].align=Align::Start;r=run();assert(near(r.boxes[1].x,25));
 nodes[1].self_align=SelfAlign::End;r=run();assert(near(r.boxes[1].x,45));nodes[1].self_align=SelfAlign::Auto;
 nodes[1].visible=false;r=run();assert(!r.boxes[1].visible);assert(near(r.boxes[0].h,30));
 nodes[2].visible=false;r=run();assert(near(r.boxes[0].w,10)&&near(r.boxes[0].h,10));
 nodes={root,a,b};nodes[2].token="graph";nodes[2].scale=2;r=run();assert(near(r.boxes[2].w,180)); // graph pixel dimensions don't scale with font
 nodes={root,a,b};nodes[2].token="separator";nodes[2].width=140;nodes[2].height=2;r=run();assert(near(r.boxes[2].w,140)&&near(r.boxes[2].h,2));
 nodes={root,a,b};nodes[0].children={1};nodes[1].group=true;nodes[1].scale=2;nodes[1].children={2};r=run();assert(near(r.boxes[2].h,40)); // inherited font scale
 auto rejects=[&](){try{run();return false;}catch(const std::invalid_argument&){return true;}};
 nodes[1].children={0};assert(rejects());
 nodes={root,a,b};nodes[0].children={1,1};assert(rejects());
 nodes={root,a,b};nodes[1].visible=false;nodes[1].children={2};assert(rejects());
 nodes={root,a,b};nodes[2].scale=std::numeric_limits<float>::quiet_NaN();assert(rejects());
 nodes={root,a,b};nodes[2].id=nodes[1].id;assert(rejects());
 nodes={root,a,b};r=layout(nodes,0,{40,20},Anchor::TopCenter,0,0,10,measure);assert(r.outside&&r.boxes[0].x<0);
 bool bad=false;try{layout(nodes,0,{1280,800},Anchor::TopLeft,0,0,10,[](const std::string&,float){return Size{-1,0};});}catch(const std::invalid_argument&){bad=true;}assert(bad);
 std::vector<Node> fit(5);fit[0].id="overlay";fit[0].axis=Axis::Column;fit[0].children={1,4};fit[1].id="readings";fit[1].axis=Axis::Row;fit[1].gap=10;fit[1].children={2,3};
 fit[2].id="cpu";fit[2].group=false;fit[2].token="cpu.load";fit[3]=fit[2];fit[3].id="gpu";fit[3].token="gpu.load";
 fit[4].id="graph";fit[4].group=false;fit[4].token="graph";fit[4].width=0;fit[4].height=20;
 auto fit_result=layout(fit,0,{1280,800},Anchor::TopLeft,20,30,10,[](const std::string& token,float){return Size{token=="cpu.load"?40.f:50.f,10.f};});
 assert(near(fit_result.boxes[1].w,100));assert(near(fit_result.boxes[4].w,fit_result.boxes[1].w));assert(near(fit_result.boxes[0].w,fit_result.boxes[1].w));
 std::cout<<"PASS: nested layout, inherited scale, auto graph width, all anchors, alignment, hidden children, overflow and invalid trees\n";
}
