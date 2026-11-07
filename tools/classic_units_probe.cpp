// Real ImGui rendering of the production classic reading helper.
#include "claw_classic_units.h"
#include <cassert>
#include <fstream>
#include <iostream>
int main(int argc,char**argv){
 if(argc!=3)return 2;const int width=1280,height=800;
 ImGui::CreateContext();auto& io=ImGui::GetIO();io.IniFilename=nullptr;io.DisplaySize=ImVec2(width,height);io.DeltaTime=1.f/60;
 auto* font=io.Fonts->AddFontFromFileTTF(argv[1],24);assert(font);io.FontDefault=font;io.Fonts->Build();
 unsigned char* atlas;int aw,ah;io.Fonts->GetTexDataAsAlpha8(&atlas,&aw,&ah);
 std::ofstream pgm(std::string(argv[2])+"-atlas.pgm",std::ios::binary);pgm<<"P5\n"<<aw<<" "<<ah<<"\n255\n";pgm.write((char*)atlas,aw*ah);pgm.close();
 ImGui::NewFrame();ImGui::SetNextWindowPos(ImVec2(10,10));ImGui::SetNextWindowSize(ImVec2(1260,780));
 ImGui::Begin("Classic HUD unit fixtures",nullptr,ImGuiWindowFlags_NoDecoration|ImGuiWindowFlags_NoSavedSettings);
 const std::vector<std::pair<int,std::string>> values={{4,"36%"},{5,"54°C"},{6,"3500 MHz"},{7,"8.6 W"},{17,"12.6 GiB"},{2,"11.9 ms"},{27,"TDP 28W"},{25,"DRAW 27W"}};
 for(bool raised:{false,true}){
  ImGui::SetCursorPos(ImVec2(20,raised?105:20));ImGui::TextUnformatted(raised?"Classic horizontal / Superscript":"Classic horizontal / Normal");
  for(size_t i=0;i<values.size();++i){if(i)ImGui::SameLine(0,18);
   const auto& v=values[i];const auto first=ImGui::GetWindowDrawList()->VtxBuffer.Size;
   assert(claw_classic::draw(v.first,v.second,IM_COL32(236,242,250,255),raised,true));
   assert(ImGui::GetWindowDrawList()->VtxBuffer.Size>first);
  }
  float y=225;const float x=raised?640:20;
  ImGui::SetCursorPos(ImVec2(x,190));ImGui::TextUnformatted(raised?"Classic vertical / Superscript":"Classic vertical / Normal");
  for(const auto& v:values){ImGui::SetCursorPos(ImVec2(x,y));assert(claw_classic::draw(v.first,v.second,IM_COL32(49,226,165,255),raised,false));y+=39;}
 }
 ImGui::SetCursorPos(ImVec2(20,600));ImGui::TextUnformatted("Non-inline number + unit / Superscript");
 const auto saved=claw_classic::capture_number("12.6",IM_COL32(49,226,165,255));ImGui::TextUnformatted("12.6");claw_classic::commit_number(saved);ImGui::SameLine(0,1);
 assert(claw_classic::finish_unit("GiB",IM_COL32(240,242,245,255),IM_COL32(0,0,0,255),1));
 bool kept_number_color=false,kept_unit_color=false;for(int i=saved.v0;i<ImGui::GetWindowDrawList()->VtxBuffer.Size;++i){auto col=ImGui::GetWindowDrawList()->VtxBuffer[i].col;kept_number_color|=col==IM_COL32(49,226,165,255);kept_unit_color|=col==IM_COL32(240,242,245,255);}assert(kept_number_color&&kept_unit_color);
 ImGui::SameLine();ImGui::TextUnformatted("indices remain valid after replacing the number");
 ImGui::SetCursorPos(ImVec2(20,680));auto stale=claw_classic::capture_number("27");ImGui::TextUnformatted("27");claw_classic::commit_number(stale);
 ImGui::TextUnformatted("An intervening label must not be replaced");assert(!claw_classic::finish_unit("W",IM_COL32_WHITE));
 ImGui::End();ImGui::Render();
 for(int i=0;i<ImGui::GetDrawData()->CmdListsCount;++i){const auto* list=ImGui::GetDrawData()->CmdLists[i];for(const auto& cmd:list->CmdBuffer)for(unsigned j=cmd.IdxOffset;j<cmd.IdxOffset+cmd.ElemCount;++j)assert(list->IdxBuffer[j]+cmd.VtxOffset<unsigned(list->VtxBuffer.Size));}
 auto* data=ImGui::GetDrawData();assert(data->TotalVtxCount>0);
 std::ofstream out(std::string(argv[2])+".json");out<<"{\"width\":"<<width<<",\"height\":"<<height<<",\"lists\":[";
 for(int list=0;list<data->CmdListsCount;++list){if(list)out<<",";auto* d=data->CmdLists[list];out<<"{\"v\":[";
  for(int i=0;i<d->VtxBuffer.Size;++i){if(i)out<<",";const auto& v=d->VtxBuffer[i];out<<"["<<v.pos.x<<","<<v.pos.y<<","<<v.uv.x<<","<<v.uv.y<<","<<v.col<<"]";}
  out<<"],\"idx\":[";for(int i=0;i<d->IdxBuffer.Size;++i){if(i)out<<",";out<<d->IdxBuffer[i];}
  out<<"],\"cmd\":[";for(int i=0;i<d->CmdBuffer.Size;++i){if(i)out<<",";const auto& c=d->CmdBuffer[i];out<<"["<<c.IdxOffset<<","<<c.ElemCount<<","<<c.ClipRect.x<<","<<c.ClipRect.y<<","<<c.ClipRect.z<<","<<c.ClipRect.w<<","<<c.VtxOffset<<"]";}
  out<<"]}";}
 out<<"]}";std::cout<<"PASS "<<width<<"x"<<height<<" nodes="<<0<<" vertices="<<data->TotalVtxCount<<"\n";
 ImGui::DestroyContext();
}
