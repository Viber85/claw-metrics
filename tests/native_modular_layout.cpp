#include "claw_modular_layout.h"
#include <cassert>
#include <iostream>
#include <limits>
using namespace claw_modular;
bool near(float a,float b){return std::abs(a-b)<.001f;}
int main(){
 Node root;root.id="root";root.padding=0;root.gap=10;root.children={1,2};
 Node a;a.id="a";a.group=false;a.token="fps.value";
 Node b=a;b.id="b";b.token="cpu.load";b.scale=2;
 std::vector<Node> nodes={root,a,b};
 auto measure=[](const std::string&,float font){return Size{font*2,font};};
 auto run=[&](Anchor anchor=Anchor::TopLeft){return layout(nodes,0,{1280,800},anchor,20,30,10,measure);};
 auto r=run();assert(near(r.boxes[0].w,70)&&near(r.boxes[0].h,20));
 assert(near(r.boxes[1].x,20)&&near(r.boxes[1].y,35));
 assert(near(r.boxes[2].x,50)&&near(r.boxes[2].y,30));
 nodes[1].self_align=SelfAlign::Start;r=run();assert(near(r.boxes[1].y,30)&&near(r.boxes[2].y,30));
 nodes[1].self_align=SelfAlign::End;r=run();assert(near(r.boxes[1].y,40)&&near(r.boxes[2].y,30));
 nodes[1].self_align=SelfAlign::Auto;
 for(auto anchor:{Anchor::TopLeft,Anchor::TopCenter,Anchor::TopRight,Anchor::BottomLeft,Anchor::BottomCenter,Anchor::BottomRight}){
  r=run(anchor);const bool bottom=anchor==Anchor::BottomLeft||anchor==Anchor::BottomCenter||anchor==Anchor::BottomRight;
  const bool center=anchor==Anchor::TopCenter||anchor==Anchor::BottomCenter;
  const bool right=anchor==Anchor::TopRight||anchor==Anchor::BottomRight;
  assert(near(r.boxes[0].x,center?625:right?1190:20));assert(near(r.boxes[0].y,bottom?750:30));assert(!r.outside);
 }
 // Center-edge anchors track measured HUD height at both resolutions and
 // accept signed vertical offsets without changing the legacy six IDs.
 assert(int(Anchor::BottomRight)==5&&int(Anchor::CenterLeft)==6&&int(Anchor::CenterRight)==7);
 for(auto anchor:{Anchor::CenterLeft,Anchor::CenterRight})for(float screen_h:{800.f,1080.f})for(float offset:{-35.f,0.f,42.f})for(auto axis:{Axis::Row,Axis::Column}){
  auto centered_nodes=nodes;centered_nodes[0].axis=axis;
  auto centered=layout(centered_nodes,0,{1920,screen_h},anchor,16,offset,18,measure);
  const auto& box=centered.boxes[0];
  assert(near(box.y+box.h/2,screen_h/2+offset));
  assert(near(box.x,anchor==Anchor::CenterLeft?16:1920-box.w-16));
  assert(!centered.outside);
 }
 nodes[0].axis=Axis::Column;r=run();assert(near(r.boxes[0].w,40)&&near(r.boxes[0].h,40));assert(near(r.boxes[1].x,30));
 nodes[0].align=Align::End;r=run();assert(near(r.boxes[1].x,40));
 nodes[0].align=Align::Start;r=run();assert(near(r.boxes[1].x,20));
 nodes[1].self_align=SelfAlign::End;r=run();assert(near(r.boxes[1].x,40));nodes[1].self_align=SelfAlign::Auto;
 nodes[1].visible=false;r=run();assert(!r.boxes[1].visible);assert(near(r.boxes[0].h,20));
 nodes[2].visible=false;r=run();assert(near(r.boxes[0].w,0)&&near(r.boxes[0].h,0));
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
 // A nested CPU/GPU column beside FPS: each axis is independent, even when
 // decoding an older layout with padding on every group.
 std::vector<Node> spaced(6);
 for(size_t i=0;i<spaced.size();++i){spaced[i].id=std::to_string(i);spaced[i].align=Align::Start;spaced[i].padding=80;}
 spaced[0].children={1,2};spaced[2].axis=Axis::Column;spaced[2].children={3,4,5};
 for(size_t i:{size_t(1),size_t(3),size_t(4),size_t(5)}){spaced[i].group=false;spaced[i].token="cpu.load";spaced[i].padding=0;}
 for(float horizontal:{0.f,1.f,240.f})for(float vertical:{0.f,1.f,240.f}){
  spaced[0].gap=horizontal;spaced[2].gap=vertical;
  auto geometry=layout(spaced,0,{1920,1080},Anchor::TopLeft,8,8,10,measure);
  const auto& boxes=geometry.boxes;
  assert(near(boxes[1].x,8)&&near(boxes[1].y,8));
  assert(near(boxes[2].x-(boxes[1].x+boxes[1].w),horizontal));
  assert(near(boxes[3].x,boxes[2].x)&&near(boxes[3].y,boxes[2].y));
  assert(near(boxes[4].y-(boxes[3].y+boxes[3].h),vertical));
  assert(near(boxes[5].y-(boxes[4].y+boxes[4].h),vertical));
  assert(near(boxes[0].w,40+horizontal)&&near(boxes[0].h,30+2*vertical));
 }
 spaced[0].gap=241;bool excessive=false;try{layout(spaced,0,{1920,1080},Anchor::TopLeft,8,8,10,measure);}catch(const std::invalid_argument&){excessive=true;}assert(excessive);
 // Overlay-only insets grow the measured background and translate its children.
 for(float px:{0.f,17.f,160.f})for(float py:{0.f,9.f,160.f})for(auto axis:{Axis::Row,Axis::Column}){
  auto padded=fit;padded[0].axis=axis;padded[0].overlay_padding_x=px;padded[0].overlay_padding_y=py;
  auto unpadded=padded;unpadded[0].overlay_padding_x=0;unpadded[0].overlay_padding_y=0;
  const auto plain=layout(unpadded,0,{1920,1080},Anchor::TopLeft,20,30,10,measure);
  const auto result=layout(padded,0,{1920,1080},Anchor::TopLeft,20,30,10,measure);
  assert(near(result.boxes[0].w,plain.boxes[0].w+2*px));assert(near(result.boxes[0].h,plain.boxes[0].h+2*py));
  for(size_t i=1;i<padded.size();++i){assert(near(result.boxes[i].x,plain.boxes[i].x+px));assert(near(result.boxes[i].y,plain.boxes[i].y+py));}
  for(auto anchor:{Anchor::TopCenter,Anchor::CenterRight,Anchor::BottomRight}){
   const auto anchored=layout(padded,0,{1920,1080},anchor,20,30,10,measure);const auto& box=anchored.boxes[0];
   if(anchor==Anchor::TopCenter)assert(near(box.x+box.w/2,980));
   if(anchor==Anchor::CenterRight)assert(near(box.y+box.h/2,570));
   if(anchor==Anchor::BottomRight)assert(near(box.y+box.h,1050));
  }
 }
 // Nested group padding contributes to siblings' positions without changing gaps.
 auto groups=fit;groups[1].overlay_padding_x=19;groups[1].overlay_padding_y=7;
 const auto plain_group=layout(fit,0,{1920,1080},Anchor::TopLeft,20,30,10,measure);
 const auto padded_group=layout(groups,0,{1920,1080},Anchor::TopLeft,20,30,10,measure);
 assert(near(padded_group.boxes[1].w,plain_group.boxes[1].w+38));assert(near(padded_group.boxes[1].h,plain_group.boxes[1].h+14));
 assert(near(padded_group.boxes[2].x,padded_group.boxes[1].x+19));assert(near(padded_group.boxes[2].y,padded_group.boxes[1].y+7));
 assert(near(padded_group.boxes[3].x-padded_group.boxes[2].x-padded_group.boxes[2].w,10));
 assert(near(padded_group.boxes[4].w,padded_group.boxes[1].w));
 std::cout<<"PASS: nested layout, inherited scale, auto graph width, all anchors, alignment, hidden children, overflow and invalid trees\n";
}
