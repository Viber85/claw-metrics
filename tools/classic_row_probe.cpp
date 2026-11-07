// Photo-matching classic strip fixture using the production reading helper.
#include "claw_classic_units.h"
#include <cassert>
#include <fstream>
#include <iostream>
int main(int argc,char**argv){
 if(argc!=3)return 2;const int width=1280,height=800;
 ImGui::CreateContext();auto& io=ImGui::GetIO();io.IniFilename=nullptr;io.DisplaySize=ImVec2(width,height);io.DeltaTime=1.f/60;
 auto* font=io.Fonts->AddFontFromFileTTF(argv[1],18);auto* fpsfont=io.Fonts->AddFontFromFileTTF(argv[1],36);assert(font&&fpsfont);io.FontDefault=font;io.Fonts->Build();
 unsigned char* atlas;int aw,ah;io.Fonts->GetTexDataAsAlpha8(&atlas,&aw,&ah);
 std::ofstream pgm(std::string(argv[2])+"-atlas.pgm",std::ios::binary);pgm<<"P5\n"<<aw<<" "<<ah<<"\n255\n";pgm.write((char*)atlas,aw*ah);pgm.close();
 for(bool raised:{false,true}){
  assert(std::abs(claw_classic::extent(6,"1111 MHz",font,18,raised,true).x-claw_classic::extent(6,"8888 MHz",font,18,raised,true).x)<.001f);
  assert(claw_classic::extent(5,"52°C",font,18,raised,true).x<claw_classic::extent(5,"888.8°C",font,18,raised,true).x-18);
 }
 claw_classic::width_floor()=0;assert(claw_classic::hold_width(400)==400);assert(claw_classic::hold_width(390)==400);assert(claw_classic::hold_width(420)==420);
 claw_classic::width_floor()=0;assert(claw_classic::hold_width(300)==300);
 io.DisplaySize=ImVec2(1920,1080);assert(claw_classic::hold_width(250)==250);io.DisplaySize=ImVec2(width,height);
 ImGui::NewFrame();ImGui::SetNextWindowPos(ImVec2(0,0));ImGui::SetNextWindowSize(ImVec2(width,height));ImGui::Begin("Classic strip",nullptr,ImGuiWindowFlags_NoDecoration|ImGuiWindowFlags_NoSavedSettings);
 ImGui::PushStyleVar(ImGuiStyleVar_FramePadding,ImVec2(0,0));
 for(bool raised:{false,true}){
  const float top=raised?270:100,center=top+9;
  ImGui::SetCursorPos(ImVec2(20,top-45));ImGui::TextUnformatted(raised?"Classic horizontal / Superscript / FPS 200%":"Classic horizontal / Normal / FPS 200%");
  ImGui::SetCursorPos(ImVec2(20,center));ImGui::TextUnformatted("FPS");
  ImGui::SameLine(0,4);ImGui::SetCursorPosY(top);ImGui::PushFont(fpsfont);assert(claw_classic::draw_number("120",IM_COL32_WHITE));ImGui::PopFont();
  ImGui::SameLine(0,4);ImGui::SetCursorPosY(center);assert(claw_classic::draw(2,"8.3 ms",IM_COL32_WHITE,raised,true));
  auto group=[&](const char* name,int token,const std::vector<std::pair<int,std::string>>& values){
   ImGui::SameLine(0,16);ImGui::SetCursorPosY(center);
   auto* draw=ImGui::GetWindowDrawList();const int first=draw->VtxBuffer.Size;
   ImGui::TextUnformatted(name);
   float label_bottom=-1e10f;for(int i=first;i<draw->VtxBuffer.Size;++i)label_bottom=std::max(label_bottom,draw->VtxBuffer[i].pos.y);
   for(const auto& value:values){
    const float previous=ImGui::GetItemRectMax().x;ImGui::SameLine(0,4);
    assert(std::abs(ImGui::GetCursorScreenPos().x-previous-4)<.001f);
    claw_classic::DrawInk ink;
    assert(claw_classic::draw(value.first,value.second,IM_COL32_WHITE,raised,true,0,0,0,&ink));
    assert(std::abs(label_bottom-ink.number_bottom)<=1);
    if(raised)assert(ink.unit_bottom<ink.number_bottom);
   }
  };
  group("AVG",28,{{28,"103.5 FPS"}});group("1% LOW",29,{{29,"8.0 FPS"}});
  ImGui::SameLine(0,16);ImGui::SetCursorPosY(center);auto pos=ImGui::GetCursorScreenPos();ImGui::Dummy(ImVec2(100,18));ImGui::GetWindowDrawList()->AddLine(ImVec2(pos.x,pos.y+12),ImVec2(pos.x+100,pos.y+12),IM_COL32(49,226,165,255),1.5);
  group("CPU",3,{{4,"18%"},{5,"52°C"},{6,"3829 MHz"},{7,"6.4 W"}});
  group("GPU",8,{{9,"13%"},{10,"49°C"},{11,"752 MHz"}});
  assert(ImGui::GetItemRectMax().x<width-8);
 }
 ImGui::PopStyleVar();ImGui::End();ImGui::Render();
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
