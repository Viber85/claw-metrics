// Real ImGui geometry/draw data for comparison with the browser preview.
#include "claw_modular_imgui.h"
#include "claw_modular_transport.h"
#include <fstream>
#include <iostream>
#include <sstream>
using namespace claw_modular;
int main(int argc,char**argv){
 if(argc!=7)return 2;
 const float size=std::stof(argv[5]);
 ImGui::CreateContext();auto& io=ImGui::GetIO();io.IniFilename=nullptr;
 io.DisplaySize={1280,800};io.DeltaTime=1.f/60;io.BackendFlags|=ImGuiBackendFlags_RendererHasVtxOffset;
 auto* font=io.Fonts->AddFontFromFileTTF(argv[1],size);if(!font)return 3;
 FontFaces faces{};const std::string path=argv[1],directory=path.substr(0,path.find_last_of('/')+1);
 const char* names[]={"Light","Regular","SemiBold","Bold"};
 for(int i=1;i<=4;++i){const auto name=directory+"BarlowSemiCondensed-"+names[i-1]+".ttf";
  faces[i]=name==path?font:io.Fonts->AddFontFromFileTTF(name.c_str(),size);if(!faces[i])return 3;}
 io.FontDefault=font;io.Fonts->Build();
 unsigned char* atlas;int aw,ah;io.Fonts->GetTexDataAsAlpha8(&atlas,&aw,&ah);
 std::ofstream pgm(std::string(argv[4])+"-atlas.pgm",std::ios::binary);
 pgm<<"P5\n"<<aw<<" "<<ah<<"\n255\n";pgm.write((char*)atlas,aw*ah);pgm.close();
 std::ifstream transport(argv[2]);std::string encoded((std::istreambuf_iterator<char>(transport)),{});
 const auto doc=decode(encoded);std::map<std::string,Text> readings;
 std::ifstream snapshot(argv[3]);std::string line;
 while(std::getline(snapshot,line)){
  std::istringstream row(line);std::string key,value,slot;
  std::getline(row,key,'\t');std::getline(row,value,'\t');std::getline(row,slot,'\t');
  Text text;text.font=font;text.value=value;text.slot=slot;readings[key]=text;
 }
 std::vector<Style> styles(doc.nodes.size());
 for(size_t i=0;i<styles.size();++i){const auto& a=doc.appearance[i];
  styles[i].separator_opacity=a.separator_opacity;
  styles[i].rounding=a.corner_radius>=0?a.corner_radius:(a.outline?6:0);
  if(a.outline){const unsigned rgb=std::stoul(a.outline_color,nullptr,16);styles[i].outline=IM_COL32(rgb>>16,(rgb>>8)&255,rgb&255,int(a.outline_opacity*255/100));styles[i].outline_width=a.outline_width;}
  if(!a.background.empty()){const unsigned rgb=std::stoul(a.background,nullptr,16);styles[i].fill=IM_COL32(rgb>>16,(rgb>>8)&255,rgb&255,255);}
 }
 auto frame=prepare(doc.nodes,styles,readings,{},0,{1280,800},doc.anchor,doc.x,doc.y,size,std::string(argv[6])=="1",faces);
 for(size_t i=0;i<doc.nodes.size();++i){const auto& id=doc.nodes[i].id;
  if(id=="ram-light"&&frame.node_readings[i].font!=faces[1])return 5;
  if(id=="ram-bold"&&frame.node_readings[i].font!=faces[4])return 5;
  if(id=="cpu-label"&&frame.node_readings[i].font!=faces[4])return 5;
  if(id=="cpu-load"&&frame.node_readings[i].font!=faces[3])return 5;
 }
 auto changed=readings;
 changed["cpu.clock"].value="2545 MHz";changed["gpu.clock"].value="600 MHz";
 changed["ram.value"].value="5.4 GiB";changed["vram.value"].value="2.2 GiB";
 auto live=prepare(doc.nodes,styles,changed,{},0,{1280,800},doc.anchor,doc.x,doc.y,size,std::string(argv[6])=="1",faces);
 for(size_t i=0;i<doc.nodes.size();++i){
  const auto& a=frame.geometry.boxes[i];const auto& b=live.geometry.boxes[i];
  if(std::abs(a.x-b.x)>.001f||std::abs(a.y-b.y)>.001f||std::abs(a.w-b.w)>.001f||std::abs(a.h-b.h)>.001f)return 4;
 }
 ImGui::NewFrame();paint(frame,ImGui::GetBackgroundDrawList());ImGui::Render();
 std::ofstream out(std::string(argv[4])+".json");out<<"{\"width\":1280,\"height\":800,\"boxes\":{";
 for(size_t i=0;i<doc.nodes.size();++i){if(i)out<<",";const auto& b=frame.geometry.boxes[i];out<<'"'<<doc.nodes[i].id<<"\":["<<b.x<<","<<b.y<<","<<b.w<<","<<b.h<<"]";}
 out<<"},\"lists\":[";auto* data=ImGui::GetDrawData();
 for(int k=0;k<data->CmdListsCount;++k){if(k)out<<",";auto* d=data->CmdLists[k];out<<"{\"v\":[";
  for(int i=0;i<d->VtxBuffer.Size;++i){if(i)out<<",";const auto& v=d->VtxBuffer[i];out<<"["<<v.pos.x<<","<<v.pos.y<<","<<v.uv.x<<","<<v.uv.y<<","<<v.col<<"]";}
  out<<"],\"idx\":[";for(int i=0;i<d->IdxBuffer.Size;++i){if(i)out<<",";out<<d->IdxBuffer[i];}
  out<<"],\"cmd\":[";for(int i=0;i<d->CmdBuffer.Size;++i){if(i)out<<",";const auto& c=d->CmdBuffer[i];out<<"["<<c.IdxOffset<<","<<c.ElemCount<<","<<c.ClipRect.x<<","<<c.ClipRect.y<<","<<c.ClipRect.z<<","<<c.ClipRect.w<<","<<c.VtxOffset<<"]";}
  out<<"]}";
 }
 out<<"]}";ImGui::DestroyContext();
}
