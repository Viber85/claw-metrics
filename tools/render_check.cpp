// Headless layout probe using the window/table operations from MangoHud v0.8.1.
// Fixture metrics only: this is not a Vulkan injection or hardware sensor test.
#include "imgui/imgui.h"
#include "imgui/imgui_internal.h"
#include <cstdio>
#include <fstream>
#include <vector>
#include <string>
#include <cmath>
static int count=0;
static ImU32 fg=IM_COL32(240,242,245,255);
static bool record=false;
struct Label {std::string text;float x,y,w,h;};
std::vector<Label> labels;
void text(const char* s,ImU32 color=fg){
 auto* window=ImGui::GetCurrentWindow();auto pos=window->DC.CursorPos;auto sz=ImGui::CalcTextSize(s);
 if(record)labels.push_back({s,pos.x,pos.y,sz.x,sz.y});
 window->DrawList->AddText(ImGui::GetFont(),ImGui::GetFontSize(),pos,color,s);
 ImGui::ItemSize(sz,ImGui::GetStyle().FramePadding.y);
}
void next(){ImGui::TableNextColumn();count++;}
void value(const char* s){next();ImVec2 p=ImGui::GetCursorPos();float off=ImGui::CalcTextSize("A").x*4;ImGui::SetCursorPosX(p.x+off-ImGui::CalcTextSize(s).x);text(s);}
void unit(const char*s,ImFont* small){ImGui::SameLine(0,1);ImGui::PushFont(small);text(s);ImGui::PopFont();}
void separator(){ImGui::SameLine();ImGui::Spacing();ImGui::SameLine();auto p=ImGui::GetCursorScreenPos();ImGui::GetWindowDrawList()->AddLine(ImVec2(p.x-5,p.y+2),ImVec2(p.x-5,p.y+18*.85),IM_COL32(119,124,135,255));ImGui::SameLine();ImGui::Spacing();}
int main(int argc,char**argv){
 bool stretch=atoi(argv[2]);int width=atoi(argv[3]);bool minimal=argc>4 && atoi(argv[4]);
 ImGui::CreateContext();auto &io=ImGui::GetIO();io.IniFilename=nullptr;io.DisplaySize=ImVec2(width,200);io.DeltaTime=1.f/60;
 ImFont* main=io.Fonts->AddFontFromFileTTF(argv[1],18);ImFont* small=io.Fonts->AddFontFromFileTTF(argv[1],18*.55);io.FontDefault=main;io.Fonts->Build();
 unsigned char* atlas;int aw,ah;io.Fonts->GetTexDataAsAlpha8(&atlas,&aw,&ah);std::ofstream pgm("atlas.pgm",std::ios::binary);pgm<<"P5\n"<<aw<<" "<<ah<<"\n255\n";pgm.write((char*)atlas,aw*ah);pgm.close();
 ImVec2 size(width,40),pos;int columns=64;ImVec2 realpos,realsize;
 for(int frame=0;frame<12;frame++){
  record=frame==11;count=0;
  ImGui::NewFrame();auto &style=ImGui::GetStyle();style.WindowRounding=10;style.CellPadding.y=-.085f*9;style.Colors[ImGuiCol_WindowBg]=ImVec4(22/255.f,24/255.f,32/255.f,1);
  ImGui::PushStyleVar(ImGuiStyleVar_WindowBorderSize,0);ImGui::PushStyleVar(ImGuiStyleVar_ItemSpacing,ImVec2(8,-3));ImGui::PushStyleVar(ImGuiStyleVar_WindowPadding,ImVec2(5,5));
  ImGui::SetNextWindowBgAlpha(.8);ImGui::SetNextWindowSize(size,ImGuiCond_Always);
  pos=ImVec2(width/2.f-size.x/2.f-(stretch?0:columns*64),8);
  ImGui::SetNextWindowPos(pos,ImGuiCond_Always);
  size=ImVec2(width,40);
  ImGui::Begin("Main",nullptr,ImGuiWindowFlags_NoDecoration);realpos=ImGui::GetWindowPos();realsize=ImGui::GetWindowSize();
  if(ImGui::BeginTable("hud",columns,ImGuiTableFlags_NoClip|ImGuiTableFlags_SizingFixedFit|ImGuiTableFlags_NoHostExtendX)){
   next();text("FPS",IM_COL32(48,229,160,255));value("120");value("8.3");unit("ms",small);separator();
   next();{ImGui::PushFont(small);static float v[50]={1,2,1,1,3};ImGui::BeginChild("graph",ImVec2(150,18*.85),false,ImGuiWindowFlags_NoDecoration);ImGui::PlotLines("##graph",v,50,0,nullptr,0,50,ImVec2(150,18*.85));ImGui::EndChild();ImGui::PopFont();}separator();
   if(!minimal){
   next();text("CPU",IM_COL32(55,201,239,255));value("43");ImGui::SameLine(0,1);text("%");value("72");ImGui::SameLine(0,1);text("°C");value("3200");unit("MHz",small);value("3.7");unit("W",small);separator();
   next();text("GPU",IM_COL32(139,218,98,255));value("91");ImGui::SameLine(0,1);text("%");value("68");ImGui::SameLine(0,1);text("°C");value("2200");unit("MHz",small);value("2.3");unit("W",small);separator();
   next();text("RAM",IM_COL32(176,119,223,255));value("13.2");unit("GiB",small);separator();
   next();text("VRAM",IM_COL32(215,106,184,255));value("5.8");unit("GiB",small);separator();
   next();text("BATT",IM_COL32(48,229,160,255));value("78");ImGui::SameLine(0,1);text("%");next();value("01:42");separator();
   next();ImGui::PushFont(small);text("DRAW 24.6W");ImGui::PopFont();separator();
   }
   next();text("15:42");
   if(count>0&&count<65)columns=count;
   if(!stretch)size=ImVec2(ImGui::GetContentRegionAvail().x-columns*64,40);
   ImGui::EndTable();
  }
  size=ImVec2(size.x,ImGui::GetCursorPosY()+10);ImGui::End();ImGui::PopStyleVar(3);ImGui::Render();
 }
 printf("glyph I=%g W=%g\n",main->FindGlyph('I')->AdvanceX,main->FindGlyph('W')->AdvanceX);
 printf("window x=%g y=%g w=%g h=%g nextWidth=%g cols=%d stretch=%d font=%s\n",realpos.x,realpos.y,realsize.x,realsize.y,size.x,columns,stretch,main->GetDebugName());
 auto*d=ImGui::GetDrawData();std::ofstream out("draw.json");out<<"{\"width\":"<<width<<",\"height\":200,\"lists\":[";
 for(int n=0;n<d->CmdListsCount;n++){if(n)out<<",";auto*l=d->CmdLists[n];out<<"{\"v\":[";for(int i=0;i<l->VtxBuffer.Size;i++){if(i)out<<",";auto&v=l->VtxBuffer[i];out<<"["<<v.pos.x<<","<<v.pos.y<<","<<v.uv.x<<","<<v.uv.y<<","<<v.col<<"]";}out<<"],\"idx\":[";for(int i=0;i<l->IdxBuffer.Size;i++){if(i)out<<",";out<<l->IdxBuffer[i];}out<<"],\"cmd\":[";for(int i=0;i<l->CmdBuffer.Size;i++){if(i)out<<",";auto&c=l->CmdBuffer[i];out<<"["<<c.IdxOffset<<","<<c.ElemCount<<","<<c.ClipRect.x<<","<<c.ClipRect.y<<","<<c.ClipRect.z<<","<<c.ClipRect.w<<"]";}out<<"]}";}out<<"]}";
 for(auto &l:labels)printf("label %s at %g..%g\n",l.text.c_str(),l.x,l.x+l.w);
 ImGui::DestroyContext();
}
