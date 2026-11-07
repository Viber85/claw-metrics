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
 std::vector<Style> styles(nodes.size());styles[0].fill=IM_COL32(16,24,38,240);styles[0].outline=IM_COL32(107,126,153,150);styles[0].rounding=10;
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
 const bool superscript=argc==8&&std::string(argv[7])=="1";
 auto frame=prepare(nodes,styles,values,{8,9,8,10,12,11,8,9,7,8,9,8},0,{float(width),float(height)},document.anchor,document.x,document.y,24,superscript);
 if(nodes[1].self_align==SelfAlign::End){auto default_nodes=nodes;default_nodes[1].self_align=SelfAlign::Auto;
  auto baseline=prepare(default_nodes,styles,values,frame.graph,0,{float(width),float(height)},document.anchor,document.x,document.y,24,superscript);
  assert(frame.geometry.boxes[1].y>baseline.geometry.boxes[1].y+1);}
 frame.graph_style=std::stoi(argv[6]);
 assert(!frame.geometry.outside);
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
  Node root;root.id="spacing-root";root.axis=axis;root.children={1,4};
  Node cpu;cpu.id="cpu-group";cpu.children={2,3};cpu.gap=6;
  Node gpu;gpu.id="gpu-group";gpu.children={5,6};gpu.gap=9;
  Node a;a.id="cpu-reading-1";a.group=false;a.token="cpu.power";
  Node b=a;b.id="cpu-reading-2";
  Node c=a;c.id="gpu-reading-1";c.token="gpu.power";
  Node d=c;d.id="gpu-reading-2";
  std::vector<Node> groups={root,cpu,a,b,gpu,c,d};
  auto sample=[&](float gap){groups[0].gap=gap;return prepare(groups,std::vector<Style>(7),frame.readings,{},0,{float(width),float(height)},Anchor::TopLeft,10,10,24,superscript);};
  const auto tight=sample(0),wide=sample(31);
  const auto& first=wide.geometry.boxes[1];const auto& second=wide.geometry.boxes[4];
  assert(std::abs((axis==Axis::Row?second.x-first.x-first.w:second.y-first.y-first.h)-31)<.001f);
  assert(std::abs(first.w-tight.geometry.boxes[1].w)<.001f&&std::abs(first.h-tight.geometry.boxes[1].h)<.001f);
  assert(wide.nodes[1].gap==6&&wide.nodes[4].gap==9);
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
