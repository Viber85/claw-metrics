#!/usr/bin/env python3
"""An independent rounded outline for solid, gradient or fully transparent backgrounds."""
from pathlib import Path
import sys
root=Path(sys.argv[1] if len(sys.argv)>1 else 'src')
def replace(name,old,new):
 p=root/name;s=p.read_text()
 if s.count(old)!=1: raise RuntimeError(f'{name}: outline anchor mismatch {old[:60]}')
 p.write_text(s.replace(old,new,1))
options=('enabled','color','width','opacity')
replace('overlay_params.h','   OVERLAY_PARAM_CUSTOM(claw_fps_scale)               \\',
 '   OVERLAY_PARAM_CUSTOM(claw_fps_scale)               \\\n'+''.join('   OVERLAY_PARAM_CUSTOM(claw_outline_'+n+')       \\\n' for n in options).rstrip('\n'))
replace('overlay_params.h','   bool claw_center_horizontal = false;',
 '''   bool claw_outline_enabled = false;
   std::string claw_outline_color = "6B7E99";
   float claw_outline_width = 1, claw_outline_opacity = 100;
   bool claw_center_horizontal = false;''')
replace('overlay_params.cpp','#define parse_claw_fps_scale(s) parse_unsigned(s)',
 '#define parse_claw_fps_scale(s) parse_unsigned(s)\n'+ '\n'.join(
 '#define parse_claw_outline_'+n+'(s) '+('parse_str(s)' if n=='color' else 'parse_unsigned(s) != 0' if n=='enabled' else 'parse_float(s)') for n in options))
helper=r'''
static void ClawDrawOutline(const overlay_params& params) {
    if(!params.claw_outline_enabled || params.claw_outline_opacity<=0) return;
    const ImVec2 pos=ImGui::GetWindowPos(),size=ImGui::GetWindowSize();
    if(size.x<3 || size.y<3) return;
    const float thickness=ImClamp(params.claw_outline_width,1.f,ImMin(6.f,ImMin(size.x,size.y)*.25f));
    const float inset=thickness*.5f+1.f;
    const unsigned rgb=std::strtoul(params.claw_outline_color.c_str(),nullptr,16);
    ImVec4 color(float((rgb>>16)&255)/255.f,float((rgb>>8)&255)/255.f,float(rgb&255)/255.f,
        ImClamp(params.claw_outline_opacity/100.f*ImGui::GetStyle().Alpha,0.f,1.f));
    if(HUDElements.colors.convert) {
        auto linear=[](float value){return value<=.04045f?value/12.92f:std::pow((value+.055f)/1.055f,2.4f);};
        color.x=linear(color.x);color.y=linear(color.y);color.z=linear(color.z);
    }
    ImDrawList* draw=ImGui::GetWindowDrawList();
    draw->PushClipRect(pos,ImVec2(pos.x+size.x,pos.y+size.y),false);
    const int first=draw->VtxBuffer.Size;
    draw->AddRect(ImVec2(pos.x+inset,pos.y+inset),ImVec2(pos.x+size.x-inset,pos.y+size.y-inset),
        ImGui::ColorConvertFloat4ToU32(color),ImMax(0.f,float(params.round_corners)-inset),
        ImDrawFlags_RoundCornersAll,thickness);
    draw->PopClipRect();
    if(std::getenv("CLAW_METRICS_VERIFY") && HUDElements.sw_stats->n_frames>30) {
        static bool seen[3][2]={};
        const int mode=ImClamp(int(params.claw_background_mode),0,2),vertical=params.claw_vertical_stack?1:0;
        if(!seen[mode][vertical]) {
            seen[mode][vertical]=true;
            unsigned alpha=0;
            float left=size.x,top=size.y,right=0,bottom=0;
            for(int i=first;i<draw->VtxBuffer.Size;++i) {
                const auto& vertex=draw->VtxBuffer[i];
                alpha=std::max(alpha,(vertex.col>>IM_COL32_A_SHIFT)&255u);
                left=ImMin(left,vertex.pos.x-pos.x);top=ImMin(top,vertex.pos.y-pos.y);
                right=ImMax(right,vertex.pos.x-pos.x);bottom=ImMax(bottom,vertex.pos.y-pos.y);
            }
            std::fprintf(stderr,"CLAW_OUTLINE mode=%d vertical=%d width=%.1f alpha=%u vertices=%d inside=%d background_alpha=%.2f\n",
                mode,vertical,thickness,alpha,draw->VtxBuffer.Size-first,
                int(left>=0 && top>=0 && right<=size.x && bottom<=size.y),params.background_alpha);
        }
    }
}
'''
replace('overlay.cpp','static void ClawDrawBackground(const overlay_params& params) {',helper+'\nstatic void ClawDrawBackground(const overlay_params& params) {')
replace('overlay.cpp','       ClawDrawBackground(params);','       ClawDrawBackground(params);\n       ClawDrawOutline(params);')
print('Installed independently colored/opaque rounded outline inside HUD bounds')
