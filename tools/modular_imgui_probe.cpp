// Actual ImGui draw-list fixture, not Vulkan injection or real sensor data.
#include "claw_modular_imgui.h"
#include "claw_modular_transport.h"
#include "modular_fixture.h"
#include <cassert>
#include <fstream>
#include <iostream>
using namespace claw_modular;
int main(int argc,char**argv){
 if(argc!=7&&argc!=8)return 2;
 const int width=std::stoi(argv[2]),height=std::stoi(argv[3]);
 ImGui::CreateContext();auto& io=ImGui::GetIO();io.IniFilename=nullptr;io.BackendFlags|=ImGuiBackendFlags_RendererHasVtxOffset;io.DisplaySize=ImVec2(width,height);io.DeltaTime=1.f/60;
 ImFont* font=io.Fonts->AddFontFromFileTTF(argv[1],24);assert(font);
 ImFont* large=io.Fonts->AddFontFromFileTTF(argv[1],48);assert(large);
 io.FontDefault=font;io.Fonts->Build();unsigned char* atlas;int aw,ah;io.Fonts->GetTexDataAsAlpha8(&atlas,&aw,&ah);
 std::ofstream pgm(std::string(argv[4])+"-atlas.pgm",std::ios::binary);pgm<<"P5\n"<<aw<<" "<<ah<<"\n255\n";pgm.write((char*)atlas,aw*ah);pgm.close();
 std::ifstream layout_file(argv[5]);
 std::string bytes((std::istreambuf_iterator<char>(layout_file)),{});
 auto document=decode(bytes);auto nodes=document.nodes;std::map<std::string,Text> values;
 for(const auto& n:nodes)if(!n.group&&n.token!="graph")values[n.token]={reading(n.token),n.token=="fps.value"?large:font,color(n.token)};
 std::vector<Style> styles(nodes.size());styles[0].fill=IM_COL32(16,24,38,240);styles[0].outline=IM_COL32(107,126,153,150);styles[0].rounding=argc==8&&std::string(argv[7])=="pill"?1000:10;
 for(size_t i=0;i<nodes.size();++i){
  const auto& appearance=document.appearance[i];
  auto packed=[](const std::string& hex,float opacity)->ImU32{
   if(hex.empty())return 0;
   const unsigned rgb=std::stoul(hex,nullptr,16);
   return IM_COL32((rgb>>16)&255,(rgb>>8)&255,rgb&255,static_cast<unsigned>(std::round(opacity*255/100)));
  };
  if(!appearance.background.empty())styles[i].fill=packed(appearance.background,appearance.opacity);
  styles[i].text=packed(appearance.color,100);
  if(appearance.outline)styles[i].outline=IM_COL32(143,184,217,255);
 }
 values["fps.value"].slot="888";
 values["battery.time"].slot="88:88";
 const bool charging=argc==8&&std::string(argv[7])=="charging";
 if(charging){values["battery.time"].value="";values["battery.time"].plugged=true;}
 const bool superscript=argc==8&&(std::string(argv[7])=="1"||charging);
 auto frame=prepare(nodes,styles,values,{8,9,8,10,12,11,8,9,7,8,9,8},0,{float(width),float(height)},document.anchor,document.x,document.y,24,superscript);
 if(nodes[1].self_align==SelfAlign::End){auto default_nodes=nodes;default_nodes[1].self_align=SelfAlign::Auto;
  auto baseline=prepare(default_nodes,styles,values,frame.graph,0,{float(width),float(height)},document.anchor,document.x,document.y,24,superscript);
  assert(frame.geometry.boxes[1].y>baseline.geometry.boxes[1].y+1);}
 frame.graph_style=std::stoi(argv[6]);
 assert(!frame.geometry.outside);
 if(document.anchor==Anchor::CenterLeft||document.anchor==Anchor::CenterRight){
  const auto& b=frame.geometry.boxes[0];
  assert(std::abs(b.y+b.h/2-height/2.f-document.y)<.001f);
  assert(std::abs(b.x-(document.anchor==Anchor::CenterLeft?document.x:width-b.w-document.x))<.001f);
  const auto larger=prepare(nodes,styles,frame.readings,frame.graph,0,{float(width),float(height)},document.anchor,document.x,document.y,28,superscript);
  const auto& changed=larger.geometry.boxes[0];
  assert(std::abs(changed.y+changed.h/2-height/2.f-document.y)<.001f);
 }

 auto lower_readings=frame.readings;lower_readings["fps.value"].value="9";
 // Compare changing readings with the same unit mode to isolate width stability.
 auto lower=prepare(nodes,styles,lower_readings,frame.graph,0,{float(width),float(height)},document.anchor,document.x,document.y,24,superscript);
 assert(std::abs(lower.geometry.boxes[0].w-frame.geometry.boxes[0].w)<.001f);
 // The unit must be measured at its actual reduced size and raised position.
 assert(unit_parts("cpu.temp","54°C").first=="54");
 assert(unit_parts("cpu.clock","3500 MHz").second=="MHz");
 assert(unit_parts("ram.value","12.6 GiB").second=="GiB");
 assert(unit_parts("fps.ms","11.9 ms").second=="ms");
 assert(unit_parts("cpu.temp","--").second.empty());
 Text temperature;temperature.value="54°C";temperature.font=font;
 auto normal=reading_size(temperature,"cpu.temp",24,false,temperature.value);
 auto raised=reading_size(temperature,"cpu.temp",24,true,temperature.value);
 assert(raised.w<normal.w&&raised.h>normal.h);
 // Every unit uses a gap in full-size pixels, including power strings with
 // a space after the number and memory/frequency strings before the suffix.
 for(bool raised_units:{false,true})for(float size:{18.f,32.f}){
  for(const auto& reading:std::vector<std::pair<std::string,std::string>>{
      {"cpu.power","8.6 W"},{"gpu.power","12.4 W"},{"battery.power","DRAW 27 W"},
      {"tdp.value","TDP 28 W"},{"ram.value","12.6 GiB"},{"vram.value","7.4 GiB"},
      {"cpu.clock","3500 MHz"},{"fps.ms","11.9 ms"},{"cpu.temp","54°C"}}){
   const auto parts=unit_parts(reading.first,reading.second);
   assert(!parts.second.empty()&&parts.first.back()!=' '&&parts.second.front()!=' ');
   Text t;t.value=reading.second;t.font=font;
   const auto extent=reading_size(t,reading.first,size,raised_units,t.value);
   const float main_width=font->CalcTextSizeA(size,1e10f,0,parts.first.c_str()).x;
   const float unit_width=font->CalcTextSizeA(size*(raised_units?.7f:1.f),1e10f,0,parts.second.c_str()).x;
   assert(std::abs(extent.w-main_width-unit_width-size*.14f)<.001f);
  }
 }
 // Separate CPU/GPU containers in either direction without changing their
 // internal spacing; these are the same parent gaps edited by the builder.
 for(Axis axis:{Axis::Row,Axis::Column}){
  Node root;root.id="spacing-root";root.axis=axis;root.padding=70;root.children={1,4};
  Node cpu;cpu.id="cpu-group";cpu.children={2,3};cpu.gap=6;cpu.padding=60;
  Node gpu;gpu.id="gpu-group";gpu.children={5,6};gpu.gap=9;gpu.padding=50;
  Node a;a.id="cpu-reading-1";a.group=false;a.token="cpu.power";
  Node b=a;b.id="cpu-reading-2";
  Node c=a;c.id="gpu-reading-1";c.token="gpu.power";
  Node d=c;d.id="gpu-reading-2";
  std::vector<Node> groups={root,cpu,a,b,gpu,c,d};
  auto spacing_readings=frame.readings;spacing_readings["cpu.power"]={"8.6 W",font};spacing_readings["gpu.power"]={"12.4 W",font};
  auto sample=[&](float gap){groups[0].gap=gap;return prepare(groups,std::vector<Style>(7),spacing_readings,{},0,{float(width),float(height)},Anchor::TopLeft,10,10,24,superscript);};
  const auto tight=sample(0);
  for(float gap:{0.f,1.f,240.f}){const auto wide=sample(gap);
  const auto& first=wide.geometry.boxes[1];const auto& second=wide.geometry.boxes[4];
  assert(std::abs((axis==Axis::Row?second.x-first.x-first.w:second.y-first.y-first.h)-gap)<.001f);
  assert(std::abs(first.w-tight.geometry.boxes[1].w)<.001f&&std::abs(first.h-tight.geometry.boxes[1].h)<.001f);
  assert(wide.nodes[1].gap==6&&wide.nodes[4].gap==9);
  assert(std::abs(wide.geometry.boxes[2].x-first.x)<.001f);
  assert(std::abs(wide.geometry.boxes[2].y-first.y)<.001f);
  }
 }
 auto elevated=prepare(nodes,styles,frame.readings,frame.graph,0,{float(width),float(height)},document.anchor,document.x,document.y,24,true);
 assert(elevated.unit_superscript);
 for(size_t i=0;i<nodes.size();++i){const auto& b=frame.geometry.boxes[i];assert(b.visible&&b.w>0&&b.h>0);}
 if(nodes[0].axis==Axis::Column&&nodes.size()>2&&nodes[1].axis==Axis::Row&&nodes.back().token=="graph"){
  const auto& row=frame.geometry.boxes[1];const auto& graph=frame.geometry.boxes.back();
  assert(graph.y>=row.y+row.h-0.1f);
  assert(std::abs(graph.x-row.x)<1.0f);
 }
 // Readings are owned by the prepared frame; mutation of the caller's map
 // cannot change what is measured/drawn mid-frame.
 values.clear();
 bool rejected=false;
 try {prepare(nodes,styles,values,{},0,{float(width),float(height)},Anchor::TopCenter,0,20,24);}
 catch(const std::invalid_argument&){rejected=true;}
 assert(rejected); // No partial frame is returned if a source/font is missing.
 auto invalid_styles=styles;invalid_styles[0].rounding=-1;rejected=false;
 try {prepare(nodes,invalid_styles,frame.readings,{},0,{float(width),float(height)},Anchor::TopCenter,0,20,24);}
 catch(const std::invalid_argument&){rejected=true;}
 assert(rejected);
 ImGui::NewFrame();
 // Real glyph vertices: every text metric uses the same main-text origin.
 // This checks the bug with top, center and bottom alignment, units on/off.
 for(bool raised:{false,true})for(auto align:{Align::Start,Align::Center,Align::End}){
  const std::vector<std::pair<std::string,std::string>> all={
   {"fps.label","88"},{"cpu.label","88"},{"gpu.label","88"},{"ram.label","88"},{"vram.label","88"},{"battery.label","88"},
   {"fps.value","88"},{"fps.average","88"},{"fps.low1","88"},{"fps.ms","88 ms"},
   {"cpu.load","88%"},{"cpu.temp","88°C"},{"cpu.clock","88 MHz"},{"cpu.power","88 W"},
   {"gpu.load","88%"},{"gpu.temp","88°C"},{"gpu.clock","88 MHz"},{"gpu.power","88 W"},{"gpu.junction","88°C"},{"gpu.fan","88 RPM"},{"gpu.voltage","88 mV"},
   {"ram.value","88 GiB"},{"ram.game","88 GiB"},{"ram.swap","88 GiB"},{"vram.value","88 GiB"},{"vram.temp","88°C"},{"vram.clock","88 MHz"},
   {"battery.value","88%"},{"battery.time","88:88"},{"battery.power","88 W"},{"tdp.value","88 W"},{"time.value","88:88"}};
  float first_y=0;
  for(size_t i=0;i<all.size();++i){
   Node root;root.id="all-metrics";root.children={1};root.align=align;
   Node node;node.id="text";node.group=false;node.token=all[i].first;
   Text value;value.font=font;value.value=all[i].second;
   auto sample=prepare({root,node},std::vector<Style>(2),{{node.token,value}},{},0,{float(width),float(height)},Anchor::TopLeft,20,30,24,raised);
   ImDrawList ink(ImGui::GetDrawListSharedData());ink._ResetForNewFrame();ink.PushClipRectFullScreen();paint(sample,&ink);
   assert(ink.VtxBuffer.Size>=4);const float y=ink.VtxBuffer[0].pos.y;
   if(i==0)first_y=y;assert(std::abs(y-first_y)<.01f);
  }
 }
 // Charge transitions keep the reserved time width and draw a vector plug.
 for(bool raised:{false,true}){
  Node root;root.id="charging";root.children={1};Node timer;timer.id="time";timer.group=false;timer.token="battery.time";
  Text value;value.font=font;value.value="02:15";value.slot="88:88";
  auto discharge=prepare({root,timer},std::vector<Style>(2),{{timer.token,value}},{},0,{float(width),float(height)},Anchor::TopLeft,20,30,24,raised);
  value.value="";value.plugged=true;
  auto charge=prepare({root,timer},std::vector<Style>(2),{{timer.token,value}},{},0,{float(width),float(height)},Anchor::TopLeft,20,30,24,raised);
  assert(std::abs(charge.geometry.boxes[0].w-discharge.geometry.boxes[0].w)<.001f);
  assert(std::abs(charge.geometry.boxes[0].h-discharge.geometry.boxes[0].h)<.001f);
  ImDrawList ink(ImGui::GetDrawListSharedData());ink._ResetForNewFrame();ink.PushClipRectFullScreen();paint(charge,&ink);assert(ink.VtxBuffer.Size>20);
 }
 // Rounded backgrounds must become real capsules on both axes.
 for(bool vertical:{false,true}){
  Node root;root.id="pill";root.overlay_padding_x=vertical?30:120;root.overlay_padding_y=vertical?120:30;
  Style style;style.fill=IM_COL32(40,80,120,255);style.rounding=1000;
  auto pill=prepare({root},{style},{},{},0,{float(width),float(height)},Anchor::TopLeft,20,30,24);
  ImDrawList ink(ImGui::GetDrawListSharedData());ink._ResetForNewFrame();ink.PushClipRectFullScreen();paint(pill,&ink);assert(ink.VtxBuffer.Size>20);
  const auto& box=pill.geometry.boxes[0];const float r=std::min(box.w,box.h)/2;
  for(const auto& v:ink.VtxBuffer){
   const float cx=std::max(box.x+r,std::min(box.x+box.w-r,v.pos.x));const float cy=std::max(box.y+r,std::min(box.y+box.h-r,v.pos.y));
   assert(std::hypot(v.pos.x-cx,v.pos.y-cy)<=r+1.5f);
  }
 }
 // Verify actual graph primitives: every style honors its node override,
 // and clearing it returns to the shared plugin color.
 for(int kind=0;kind<6;++kind)for(ImU32 override_color:{ImU32(0),IM_COL32(255,0,255,255),IM_COL32(255,255,0,255)}){
  Node root;root.id="graph-color-root";root.children={1,2};
  Node graph;graph.id="custom-graph";graph.token="graph";graph.group=false;graph.width=200;graph.height=50;
  Node other=graph;other.id="global-graph";
  std::vector<Style> appearance(3);appearance[1].text=override_color;
  auto sample=prepare({root,graph,other},appearance,{}, {8,14,9,5,11},0,{float(width),float(height)},Anchor::TopLeft,20,30,24);
  sample.graph_style=kind;sample.graph_color=IM_COL32(0,255,255,255);
  ImDrawList list(ImGui::GetDrawListSharedData());list._ResetForNewFrame();list.PushClipRectFullScreen();paint(sample,&list);
  assert(list.VtxBuffer.Size>0);bool custom=false,global=false;
  const auto split=(sample.geometry.boxes[1].x+sample.geometry.boxes[1].w+sample.geometry.boxes[2].x)/2;
  for(const auto& vertex:list.VtxBuffer){
   const auto expected=vertex.pos.x<split?(override_color?override_color:sample.graph_color):sample.graph_color;
   assert((vertex.col&~IM_COL32_A_MASK)==(expected&~IM_COL32_A_MASK));
   custom|=vertex.pos.x<split;global|=vertex.pos.x>=split;
  }
  assert(custom&&global);
 }
 ImDrawList units(ImGui::GetDrawListSharedData());units._ResetForNewFrame();units.PushClipRectFullScreen();
 paint(elevated,&units);assert(units.VtxBuffer.Size>0);
 // Real glyph vertices must move with a column's start/center/end setting,
 // while the reserved width remains stable for changing readings.
 auto draw_alignment=[&](Align align,SelfAlign item_alignment=SelfAlign::Auto){
  Node root;root.id="alignment";root.axis=Axis::Column;root.align=align;root.children={1};
  Node child;child.id="reading";child.group=false;child.token="cpu.load";child.self_align=item_alignment;
  Text value;value.value="2%";value.slot="100%";value.font=font;
  auto sample=prepare({root,child},std::vector<Style>(2),{{"cpu.load",value}},{},0,{float(width),float(height)},Anchor::TopLeft,20,30,24);
  ImDrawList list(ImGui::GetDrawListSharedData());list._ResetForNewFrame();list.PushClipRectFullScreen();
  const int before=list.VtxBuffer.Size;paint(sample,&list);assert(list.VtxBuffer.Size>before);
  float first=std::numeric_limits<float>::max();
  for(int i=before;i<list.VtxBuffer.Size;++i)first=std::min(first,list.VtxBuffer[i].pos.x);
  return first;
 };
 const float left=draw_alignment(Align::Start),center=draw_alignment(Align::Center),right=draw_alignment(Align::End);
 assert(left+1<center&&center+1<right);
 assert(std::abs(draw_alignment(Align::Center,SelfAlign::Start)-left)<1);
 paint(frame,ImGui::GetBackgroundDrawList());ImGui::Render();
 auto* data=ImGui::GetDrawData();assert(data->TotalVtxCount>0);
 std::ofstream out(std::string(argv[4])+".json");out<<"{\"width\":"<<width<<",\"height\":"<<height<<",\"lists\":[";
 for(int list=0;list<data->CmdListsCount;++list){if(list)out<<",";auto* d=data->CmdLists[list];out<<"{\"v\":[";
  for(int i=0;i<d->VtxBuffer.Size;++i){if(i)out<<",";const auto& v=d->VtxBuffer[i];out<<"["<<v.pos.x<<","<<v.pos.y<<","<<v.uv.x<<","<<v.uv.y<<","<<v.col<<"]";}
  out<<"],\"idx\":[";for(int i=0;i<d->IdxBuffer.Size;++i){if(i)out<<",";out<<d->IdxBuffer[i];}
  out<<"],\"cmd\":[";for(int i=0;i<d->CmdBuffer.Size;++i){if(i)out<<",";const auto& c=d->CmdBuffer[i];out<<"["<<c.IdxOffset<<","<<c.ElemCount<<","<<c.ClipRect.x<<","<<c.ClipRect.y<<","<<c.ClipRect.z<<","<<c.ClipRect.w<<","<<c.VtxOffset<<"]";}
  out<<"]}";}
 out<<"]}";std::cout<<"PASS "<<width<<"x"<<height<<" nodes="<<nodes.size()<<" vertices="<<data->TotalVtxCount<<"\n";
 ImGui::DestroyContext();
}
