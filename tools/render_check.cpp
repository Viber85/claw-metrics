// Headless layout probe using the window/table operations from MangoHud v0.8.1.
// Fixture metrics only: this is not a Vulkan injection or hardware sensor test.
#include "imgui/imgui.h"
#include "imgui/imgui_internal.h"
#include "claw_horizontal_separator.h"
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
std::vector<claw_horizontal_separator::Line> separators;
void text(const char* s,ImU32 color=fg){
 auto* window=ImGui::GetCurrentWindow();auto pos=window->DC.CursorPos;auto sz=ImGui::CalcTextSize(s);
 if(record)labels.push_back({s,pos.x,pos.y,sz.x,sz.y});
 window->DrawList->AddText(ImGui::GetFont(),ImGui::GetFontSize(),pos,color,s);
 ImGui::ItemSize(sz,ImGui::GetStyle().FramePadding.y);
}
void next(){ImGui::TableNextColumn();count++;}
void value(const char* s){next();ImVec2 p=ImGui::GetCursorPos();float off=ImGui::CalcTextSize("A").x*4;ImGui::SetCursorPosX(p.x+off-ImGui::CalcTextSize(s).x);text(s);}
void unit(const char*s,ImFont* small){ImGui::SameLine(0,1);ImGui::PushFont(small);text(s);ImGui::PopFont();}
void separator(){ImGui::SameLine();ImGui::Spacing();ImGui::SameLine();auto p=ImGui::GetCursorScreenPos();auto line=claw_horizontal_separator::geometry(ImGui::GetWindowPos(),ImGui::GetStyle().WindowPadding.y,ImGui::GetIO().FontDefault->FontSize,p.x,100,2);if(record)separators.push_back(line);ImGui::GetWindowDrawList()->AddLine(line.start,line.end,IM_COL32(119,124,135,255),line.thickness);ImGui::SameLine();ImGui::Spacing();}
int main(int argc,char**argv){
 bool stretch=atoi(argv[2]);int width=atoi(argv[3]);int mode=argc>4?atoi(argv[4]):0;bool minimal=mode==1;bool clocks=mode!=2;
 float font_size=argc>5?atof(argv[5]):18;
 float ox=argc>6?atof(argv[6]):8, oy=argc>7?atof(argv[7]):8, padding=argc>8?atof(argv[8]):8;
 ImGui::CreateContext();auto &io=ImGui::GetIO();io.IniFilename=nullptr;io.DisplaySize=ImVec2(width,200);io.DeltaTime=1.f/60;
 ImFont* main=io.Fonts->AddFontFromFileTTF(argv[1],font_size);ImFont* small=io.Fonts->AddFontFromFileTTF(argv[1],font_size*.55);io.FontDefault=main;io.Fonts->Build();
 unsigned char* atlas;int aw,ah;io.Fonts->GetTexDataAsAlpha8(&atlas,&aw,&ah);std::ofstream pgm("atlas.pgm",std::ios::binary);pgm<<"P5\n"<<aw<<" "<<ah<<"\n255\n";pgm.write((char*)atlas,aw*ah);pgm.close();
 ImVec2 size(width,40),pos;int columns=64;ImVec2 realpos,realsize;
 for(int frame=0;frame<12;frame++){
  record=frame==11;count=0;
  ImGui::NewFrame();auto &style=ImGui::GetStyle();style.WindowRounding=10;style.CellPadding.y=padding;style.Colors[ImGuiCol_WindowBg]=ImVec4(22/255.f,24/255.f,32/255.f,1);
  ImGui::PushStyleVar(ImGuiStyleVar_WindowBorderSize,0);ImGui::PushStyleVar(ImGuiStyleVar_ItemSpacing,ImVec2(8,-3));ImGui::PushStyleVar(ImGuiStyleVar_WindowPadding,ImVec2(5,5));
  ImGui::SetNextWindowBgAlpha(.8);ImGui::SetNextWindowSize(size,ImGuiCond_Always);
  pos=ImVec2(ox,oy); // MangoHud top-left branch: both offsets are honored.
  ImGui::SetNextWindowPos(pos,ImGuiCond_Always);
  size=ImVec2(width,40);
  ImGui::Begin("Main",nullptr,ImGuiWindowFlags_NoDecoration);realpos=ImGui::GetWindowPos();realsize=ImGui::GetWindowSize();
  if(ImGui::BeginTable("hud",columns,ImGuiTableFlags_NoClip|ImGuiTableFlags_SizingFixedFit|ImGuiTableFlags_NoHostExtendX)){
   next();text("FPS",IM_COL32(48,229,160,255));value("120");value("8.3");unit("ms",small);separator();
   next();{ImGui::PushFont(small);static float v[50]={1,2,1,1,3};ImGui::BeginChild("graph",ImVec2(150,font_size*.85),false,ImGuiWindowFlags_NoDecoration);ImGui::PlotLines("##graph",v,50,0,nullptr,0,50,ImVec2(150,font_size*.85));ImGui::EndChild();ImGui::PopFont();}separator();
   if(!minimal){
   next();text("CPU",IM_COL32(55,201,239,255));value("43");ImGui::SameLine(0,1);text("%");value("72");ImGui::SameLine(0,1);text("°C");if(clocks){value("3200");unit("MHz",small);}value("3.7");unit("W",small);separator();
   next();text("GPU",IM_COL32(139,218,98,255));value("91");ImGui::SameLine(0,1);text("%");value("68");ImGui::SameLine(0,1);text("°C");if(clocks){value("2200");unit("MHz",small);}value("2.3");unit("W",small);separator();
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
 for(auto &l:labels)printf("label %s at %g..%g y=%g\n",l.text.c_str(),l.x,l.x+l.w,l.y);
 for(const auto& line:separators)printf("separator x=%g y=%g..%g thickness=%g\n",line.start.x,line.start.y,line.end.y,line.thickness);
 const auto a=claw_horizontal_separator::geometry(ImVec2(0,4),5,18,100,50,1);
 const auto b=claw_horizontal_separator::geometry(ImVec2(0,4),5,18,200,150,6);
 if(a.end.y-a.start.y>=b.end.y-b.start.y || a.thickness!=1 || b.thickness!=6)return 4;
 // Exercise the geometry and rounded/alpha drawing used by the new renderer.
 using namespace claw_horizontal_separator;
 for (bool strip : {false, true}) {
  for (unsigned orientation : {Horizontal, Vertical}) {
   const auto d = claw_horizontal_separator::size(strip, orientation, 52, 6, 100, 18, 260);
   if (d.x != (orientation==Vertical?6:52) || d.y != (orientation==Vertical?52:6)) return 5;
  }
  const auto automatic = claw_horizontal_separator::size(strip, Auto, 0, 6, 100, 18, 260);
  if (strip ? automatic.x!=6 : automatic.y!=6) return 6;
  const auto disabled = claw_horizontal_separator::size(strip, Off, 52, 6, 100, 18, 260);
  if (disabled.x!=0 || disabled.y!=0) return 7;
 }
 ImGui::NewFrame();
 ImGui::Begin("Separator fixture");
 ImDrawList* line_draw = ImGui::GetWindowDrawList();
 const int start = line_draw->VtxBuffer.Size;
 draw(*line_draw,{10,10},{52,6},0x37c9ef,3,0);
 if (line_draw->VtxBuffer.Size!=start) return 8;
 draw(*line_draw,{10,10},{52,6},0x37c9ef,3,40);
 if (line_draw->VtxBuffer.Size<=start+4) return 9;
 bool color_found = false;
 for(int i=start; i<line_draw->VtxBuffer.Size; ++i)
  color_found |= line_draw->VtxBuffer[i].col==IM_COL32(55,201,239,102);
 if(!color_found) return 10;
 ImGui::End();
 ImGui::Render();
 ImGui::DestroyContext();
}
