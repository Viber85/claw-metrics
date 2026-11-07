// Photo-matching classic strip fixture using the production reading helper.
#include "claw_classic_units.h"
#include <cassert>
#include <fstream>
#include <iostream>
int main(int argc,char**argv){
 if(argc!=3)return 2;const int width=1280,height=800;
 ImGui::CreateContext();auto& io=ImGui::GetIO();io.IniFilename=nullptr;io.DisplaySize=ImVec2(width,height);io.DeltaTime=1.f/60;
 auto* font=io.Fonts->AddFontFromFileTTF(argv[1],18);auto* fpsfont=io.Fonts->AddFontFromFileTTF(argv[1],36);
 const std::string font_path=argv[1],directory=font_path.substr(0,font_path.find_last_of('/')+1);
 auto load=[&](const char* weight){const auto path=directory+"BarlowSemiCondensed-"+weight+".ttf";std::ifstream exists(path);return io.Fonts->AddFontFromFileTTF(exists?path.c_str():argv[1],18);};
 auto* title_font=load("Bold");auto* value_font=load("Light");assert(font&&fpsfont&&title_font&&value_font);io.FontDefault=font;io.Fonts->Build();
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
 const ImU32 orange=IM_COL32(255,172,18,255),white=IM_COL32(221,238,255,255);
 for(bool raised:{false,true}){
  const float y=raised?580:450;
  ImGui::SetCursorPos(ImVec2(20,y-30));ImGui::TextUnformatted(raised?"Classic TDP / Bold title + Light value / Superscript":"Classic TDP / Bold title + Light value / Normal");
  ImGui::SetCursorPos(ImVec2(20,y));ImGui::PushFont(title_font);ImGui::TextColored(ImGui::ColorConvertU32ToFloat4(orange),"Power Limit");ImGui::PopFont();
  ImGui::SameLine(0,4);ImGui::PushFont(value_font);claw_classic::DrawInk ink;
  assert(claw_classic::draw(27,"20W",white,raised,true,0,0,0,&ink));ImGui::PopFont();
  assert(ink.number_bottom>ink.number_top);
  // The existing modular node now contains two independently styled runs.
  std::vector<claw_modular::Node> nodes(2);nodes[0].id="root";nodes[0].children={1};nodes[1].id="tdp";nodes[1].group=false;nodes[1].token="tdp.value";
  claw_modular::Text reading;reading.value="20W";reading.font=value_font;reading.color=white;reading.prefix="Power Limit";reading.prefix_font=title_font;reading.prefix_color=orange;
  const auto numeric=claw_modular::reading_size(claw_modular::Text{"20W",value_font,white},"tdp.value",18,raised,"20W");
  const auto combined=claw_modular::reading_size(reading,"tdp.value",18,raised,"20W");
  assert(std::abs(combined.w-numeric.w-claw_modular::prefix_width(reading,18))<.001f);
  auto frame=claw_modular::prepare(nodes,std::vector<claw_modular::Style>(2),{{"tdp.value",reading}},{},0,{1280,800},claw_modular::Anchor::TopLeft,640,y,18,raised);
  ImGui::SetCursorPos(ImVec2(640,y-30));ImGui::TextUnformatted("Modular TDP / independent title and value");
  auto* draw=ImGui::GetWindowDrawList();const int first=draw->VtxBuffer.Size;claw_modular::paint(frame,draw);
  int label_vertices=0,value_vertices=0;
  for(int i=first;i<draw->VtxBuffer.Size;++i){const auto color=draw->VtxBuffer[i].col;assert(color==orange||color==white);label_vertices+=color==orange;value_vertices+=color==white;}
  assert(label_vertices>=32&&value_vertices==12);
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
