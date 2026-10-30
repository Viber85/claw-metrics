// Headless layout probe using the window/table operations from MangoHud v0.8.1.
// Fixture metrics only: this is not a Vulkan injection or hardware sensor test.
#include "imgui/imgui.h"
#include "imgui/imgui_internal.h"
#include "claw_layout.h"
#include <cstdio>
#include <fstream>
#include <vector>
#include <string>
#include <cmath>
static int count=0;
static ImU32 fg=IM_COL32(240,242,245,255);
static bool record=false;
static bool custom=false;
static float base_size=18, fps_size=28;
struct Label {std::string text;float x,y,w,h;};
std::vector<Label> labels;
void text(const char* s,ImU32 color=fg){
 auto* window=ImGui::GetCurrentWindow();auto pos=window->DC.CursorPos;auto sz=ImGui::CalcTextSize(s);
 if(custom){float line=claw::line_height(base_size,fps_size,true,ImGui::GetIO().FontGlobalScale);pos.y+=(line-sz.y)*.5f;}
 if(record)labels.push_back({s,pos.x,pos.y,sz.x,sz.y});
 window->DrawList->AddText(ImGui::GetFont(),ImGui::GetFontSize(),pos,color,s);
 if(custom)sz.y=claw::line_height(base_size,fps_size,true,ImGui::GetIO().FontGlobalScale);
 ImGui::ItemSize(sz,ImGui::GetStyle().FramePadding.y);
}
void next(){ImGui::TableNextColumn();count++;}
void value(const char* s){next();ImVec2 p=ImGui::GetCursorPos();float off=ImGui::CalcTextSize("A").x*4;ImGui::SetCursorPosX(p.x+off-ImGui::CalcTextSize(s).x);text(s);}
void unit(const char*s,ImFont* small){ImGui::SameLine(0,1);ImGui::PushFont(small);text(s);ImGui::PopFont();}
void separator(){ImGui::SameLine();ImGui::Spacing();ImGui::SameLine();auto p=ImGui::GetCursorScreenPos();ImGui::GetWindowDrawList()->AddLine(ImVec2(p.x-5,p.y+2),ImVec2(p.x-5,p.y+ImGui::GetFontSize()*.85),IM_COL32(119,124,135,255));ImGui::SameLine();ImGui::Spacing();}
int main(int argc,char**argv){
 bool stretch=atoi(argv[2]);int width=atoi(argv[3]);int mode=argc>4?atoi(argv[4]):0;bool minimal=mode==1;bool clocks=mode!=2;
 float font_size=argc>5?atof(argv[5]):18;
 float ox=argc>6?atof(argv[6]):8, oy=argc>7?atof(argv[7]):8, padding=argc>8?atof(argv[8]):8;
 custom=argc>9 && atoi(argv[9]);fps_size=argc>10?atof(argv[10]):28;float padx=argc>11?atof(argv[11]):12;bool centered=argc>12 && atoi(argv[12]);bool fit=argc>13 && atoi(argv[13]);base_size=font_size;
 float natural=0,fit_scale=1;
 ImGui::CreateContext();auto &io=ImGui::GetIO();io.IniFilename=nullptr;io.DisplaySize=ImVec2(width,200);io.DeltaTime=1.f/60;
 ImFont* main=io.Fonts->AddFontFromFileTTF(argv[1],font_size);ImFont* small=io.Fonts->AddFontFromFileTTF(argv[1],font_size*.55);ImFont* fps=io.Fonts->AddFontFromFileTTF(argv[1],fps_size);io.FontDefault=main;io.Fonts->Build();
 unsigned char* atlas;int aw,ah;io.Fonts->GetTexDataAsAlpha8(&atlas,&aw,&ah);std::ofstream pgm("atlas.pgm",std::ios::binary);pgm<<"P5\n"<<aw<<" "<<ah<<"\n255\n";pgm.write((char*)atlas,aw*ah);pgm.close();
 ImVec2 size(width,40),pos;int columns=64;ImVec2 realpos,realsize;
 for(int frame=0;frame<80;frame++){
  record=frame==79;count=0;
  fit_scale=custom&&fit?claw::fit_scale(natural,width,padx):1;io.FontGlobalScale=fit_scale;
  ImGui::NewFrame();auto &style=ImGui::GetStyle();style.WindowRounding=10;style.CellPadding=custom?ImVec2(4*fit_scale,0):ImVec2(4,padding);style.Colors[ImGuiCol_WindowBg]=ImVec4(22/255.f,24/255.f,32/255.f,1);
  ImGui::PushStyleVar(ImGuiStyleVar_WindowBorderSize,0);ImGui::PushStyleVar(ImGuiStyleVar_ItemSpacing,ImVec2(8*fit_scale,-3*fit_scale));ImGui::PushStyleVar(ImGuiStyleVar_WindowPadding,custom?ImVec2(padx,padding):ImVec2(5,5));
  ImGui::SetNextWindowBgAlpha(.8);ImGui::SetNextWindowSize(size,ImGuiCond_Always);
  pos=ImVec2(custom?claw::row_x(width,size.x,ox,centered):ox,oy); // MangoHud top-left branch: both offsets are honored.
  ImGui::SetNextWindowPos(pos,ImGuiCond_Always);
  if(!custom)size=ImVec2(width,40);
  ImGui::Begin("Main",nullptr,ImGuiWindowFlags_NoDecoration);realpos=ImGui::GetWindowPos();realsize=ImGui::GetWindowSize();
  if(ImGui::BeginTable("hud",columns,ImGuiTableFlags_NoClip|ImGuiTableFlags_SizingFixedFit|ImGuiTableFlags_NoHostExtendX|(custom?ImGuiTableFlags_NoKeepColumnsVisible:0))){
   next();text("FPS",IM_COL32(48,229,160,255));if(custom)ImGui::PushFont(fps);value("120");if(custom)ImGui::PopFont();value("8.3");unit("ms",small);separator();
   next();{ImGui::PushFont(small);static float v[50]={1,2,1,1,3};ImGui::BeginChild("graph",ImVec2(150*fit_scale,custom?claw::line_height(base_size,fps_size,true,fit_scale)*.85:font_size*.85),false,ImGuiWindowFlags_NoDecoration);ImGui::PlotLines("##graph",v,50,0,nullptr,0,50,ImVec2(150*fit_scale,custom?claw::line_height(base_size,fps_size,true,fit_scale)*.85:font_size*.85));ImGui::EndChild();ImGui::PopFont();}separator();
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
   if(!custom&&!stretch)size=ImVec2(ImGui::GetContentRegionAvail().x-columns*64,40);
   ImGui::EndTable();
   if(custom){float body=ImGui::GetCurrentWindow()->DC.CursorMaxPos.x-ImGui::GetWindowPos().x-padx;natural=std::max(1.f,body/fit_scale);size.x=std::ceil(body+2*padx);}
  }
  size=ImVec2(size.x,custom?std::ceil(claw::line_height(base_size,fps_size,true,fit_scale)+2*padding):ImGui::GetCursorPosY()+10);ImGui::End();ImGui::PopStyleVar(3);ImGui::Render();
 }
 printf("glyph I=%g W=%g\n",main->FindGlyph('I')->AdvanceX,main->FindGlyph('W')->AdvanceX);
 printf("window x=%g y=%g w=%g h=%g nextWidth=%g cols=%d stretch=%d font=%s\n",realpos.x,realpos.y,realsize.x,realsize.y,size.x,columns,stretch,main->GetDebugName());
 auto*d=ImGui::GetDrawData();std::ofstream out("draw.json");out<<"{\"width\":"<<width<<",\"height\":200,\"lists\":[";
 for(int n=0;n<d->CmdListsCount;n++){if(n)out<<",";auto*l=d->CmdLists[n];out<<"{\"v\":[";for(int i=0;i<l->VtxBuffer.Size;i++){if(i)out<<",";auto&v=l->VtxBuffer[i];out<<"["<<v.pos.x<<","<<v.pos.y<<","<<v.uv.x<<","<<v.uv.y<<","<<v.col<<"]";}out<<"],\"idx\":[";for(int i=0;i<l->IdxBuffer.Size;i++){if(i)out<<",";out<<l->IdxBuffer[i];}out<<"],\"cmd\":[";for(int i=0;i<l->CmdBuffer.Size;i++){if(i)out<<",";auto&c=l->CmdBuffer[i];out<<"["<<c.IdxOffset<<","<<c.ElemCount<<","<<c.ClipRect.x<<","<<c.ClipRect.y<<","<<c.ClipRect.z<<","<<c.ClipRect.w<<"]";}out<<"]}";}out<<"]}";
 for(auto &l:labels)printf("label %s at %g..%g y=%g h=%g\n",l.text.c_str(),l.x,l.x+l.w,l.y,l.h);
 ImGui::DestroyContext();
}
