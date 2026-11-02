// Actual ImGui draw-list fixture, not Vulkan injection or real sensor data.
#include "claw_modular_imgui.h"
#include "modular_fixture.h"
#include <cassert>
#include <fstream>
#include <iostream>
using namespace claw_modular;
int main(int argc,char**argv){
 if(argc!=5)return 2;
 const int width=std::stoi(argv[2]),height=std::stoi(argv[3]);
 ImGui::CreateContext();auto& io=ImGui::GetIO();io.IniFilename=nullptr;io.DisplaySize=ImVec2(width,height);io.DeltaTime=1.f/60;
 ImFont* font=io.Fonts->AddFontFromFileTTF(argv[1],24);assert(font);
 ImFont* large=io.Fonts->AddFontFromFileTTF(argv[1],48);assert(large);
 io.FontDefault=font;io.Fonts->Build();unsigned char* atlas;int aw,ah;io.Fonts->GetTexDataAsAlpha8(&atlas,&aw,&ah);
 std::ofstream pgm(std::string(argv[4])+"-atlas.pgm",std::ios::binary);pgm<<"P5\n"<<aw<<" "<<ah<<"\n255\n";pgm.write((char*)atlas,aw*ah);pgm.close();
 auto nodes=fixture();std::map<std::string,Text> values;
 for(const auto& n:nodes)if(!n.group&&n.token!="graph")values[n.token]={reading(n.token),n.token=="fps.value"?large:font,color(n.token)};
 std::vector<Style> styles(nodes.size());styles[0].fill=IM_COL32(16,24,38,240);styles[0].outline=IM_COL32(107,126,153,150);styles[0].rounding=10;
 auto frame=prepare(nodes,styles,values,{8,9,8,10,12,11,8,9,7,8,9,8},0,{float(width),float(height)},Anchor::TopCenter,0,20,24);
 assert(!frame.geometry.outside);
 for(size_t i=0;i<nodes.size();++i){const auto& b=frame.geometry.boxes[i];assert(b.visible&&b.w>0&&b.h>0);}
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
 ImGui::NewFrame();paint(frame,ImGui::GetBackgroundDrawList());ImGui::Render();
 auto* data=ImGui::GetDrawData();assert(data->TotalVtxCount>0);
 std::ofstream out(std::string(argv[4])+".json");out<<"{\"width\":"<<width<<",\"height\":"<<height<<",\"lists\":[";
 for(int list=0;list<data->CmdListsCount;++list){if(list)out<<",";auto* d=data->CmdLists[list];out<<"{\"v\":[";
  for(int i=0;i<d->VtxBuffer.Size;++i){if(i)out<<",";const auto& v=d->VtxBuffer[i];out<<"["<<v.pos.x<<","<<v.pos.y<<","<<v.uv.x<<","<<v.uv.y<<","<<v.col<<"]";}
  out<<"],\"idx\":[";for(int i=0;i<d->IdxBuffer.Size;++i){if(i)out<<",";out<<d->IdxBuffer[i];}
  out<<"],\"cmd\":[";for(int i=0;i<d->CmdBuffer.Size;++i){if(i)out<<",";const auto& c=d->CmdBuffer[i];out<<"["<<c.IdxOffset<<","<<c.ElemCount<<","<<c.ClipRect.x<<","<<c.ClipRect.y<<","<<c.ClipRect.z<<","<<c.ClipRect.w<<"]";}
  out<<"]}";}
 out<<"]}";std::cout<<"PASS "<<width<<"x"<<height<<" nodes="<<nodes.size()<<" vertices="<<data->TotalVtxCount<<"\n";
 ImGui::DestroyContext();
}
