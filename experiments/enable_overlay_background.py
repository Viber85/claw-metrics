#!/usr/bin/env python3
"""Rounded multistop native gradients, independent of HUD metrics and placement."""
from pathlib import Path
import sys
root=Path(sys.argv[1] if len(sys.argv)>1 else 'src')
def replace(name,old,new):
 p=root/name;s=p.read_text()
 if s.count(old)!=1: raise RuntimeError(f'{name}: background anchor mismatch: {old[:65]}')
 p.write_text(s.replace(old,new,1))
(root/'claw_background.h').write_bytes((Path(__file__).parent/'native/claw_background.h').read_bytes())
options=('mode','stops','angle','center_x','center_y','radius')
replace('overlay_params.h','   OVERLAY_PARAM_CUSTOM(claw_fps_scale)               \\',
 '   OVERLAY_PARAM_CUSTOM(claw_fps_scale)               \\\n'+''.join('   OVERLAY_PARAM_CUSTOM(claw_background_'+n+')       \\\n' for n in options).rstrip('\n'))
replace('overlay_params.h','   bool claw_center_horizontal = false;',
 '''   unsigned claw_background_mode = 0;
   std::string claw_background_stops;
   float claw_background_angle = 0, claw_background_center_x = 50,
         claw_background_center_y = 50, claw_background_radius = 70;
   bool claw_center_horizontal = false;''')
replace('overlay_params.cpp','#define parse_claw_fps_scale(s) parse_unsigned(s)',
 '#define parse_claw_fps_scale(s) parse_unsigned(s)\n'+ '\n'.join(
 '#define parse_claw_background_'+n+'(s) '+('parse_str(s)' if n=='stops' else 'parse_unsigned(s)' if n=='mode' else 'parse_float(s)') for n in options))
replace('overlay.cpp','#include <algorithm>','#include <algorithm>\n#include "claw_background.h"')
helper=r'''
static void ClawDrawBackground(const overlay_params& params) {
    if(params.claw_background_mode==0 || params.background_alpha<=0) return;
    const ImVec2 origin=ImGui::GetWindowPos(), size=ImGui::GetWindowSize();
    const float w=size.x,h=size.y;
    if(w<1 || h<1) return;
    static ClawBackgroundRamp ramp;
    ramp.configure(params.claw_background_stops);
    const float r=ImClamp(float(params.round_corners),0.f,ImMin(w,h)*.5f);
    std::vector<float> rows;
    for(int i=0;i<=96;++i) rows.push_back(h*float(i)/96.f);
    for(int i=0;i<=16;++i) { rows.push_back(r*float(i)/16.f); rows.push_back(h-r*float(i)/16.f); }
    std::sort(rows.begin(),rows.end());
    rows.erase(std::unique(rows.begin(),rows.end()),rows.end());
    auto inset=[&](float y) {
        const float dy=ImMax(0.f,ImMax(r-y,y-(h-r)));
        return r-std::sqrt(ImMax(0.f,r*r-dy*dy));
    };
    ImDrawList* draw=ImGui::GetWindowDrawList();
    draw->PushClipRect(origin,ImVec2(origin.x+w,origin.y+h),false);
    const ImVec2 uv=ImGui::GetFontTexUvWhitePixel();
    const float alpha=ImClamp(params.background_alpha*ImGui::GetStyle().Alpha,0.f,1.f);
    auto color=[&](float x,float y,float a) {
        const auto rgb=ramp.color(ClawBackgroundRamp::position(x,y,w,h,
            params.claw_background_mode,params.claw_background_angle,
            params.claw_background_center_x,params.claw_background_center_y,
            params.claw_background_radius));
        auto linear=[](float value) {
            return value<=.04045f ? value/12.92f : std::pow((value+.055f)/1.055f,2.4f);
        };
        // Match the stock solid-background conversion for sRGB swapchains.
        return ImGui::ColorConvertFloat4ToU32(HUDElements.colors.convert
            ? ImVec4(linear(rgb.r),linear(rgb.g),linear(rgb.b),a)
            : ImVec4(rgb.r,rgb.g,rgb.b,a));
    };
    auto quad=[&](ImVec2 a,ImVec2 b,ImVec2 c,ImVec2 d,ImU32 ca,ImU32 cb,ImU32 cc,ImU32 cd) {
        draw->PrimReserve(6,4);
        const ImDrawIdx index=ImDrawIdx(draw->_VtxCurrentIdx);
        draw->PrimWriteIdx(index);draw->PrimWriteIdx(ImDrawIdx(index+1));draw->PrimWriteIdx(ImDrawIdx(index+2));
        draw->PrimWriteIdx(index);draw->PrimWriteIdx(ImDrawIdx(index+2));draw->PrimWriteIdx(ImDrawIdx(index+3));
        draw->PrimWriteVtx(ImVec2(origin.x+a.x,origin.y+a.y),uv,ca);
        draw->PrimWriteVtx(ImVec2(origin.x+b.x,origin.y+b.y),uv,cb);
        draw->PrimWriteVtx(ImVec2(origin.x+c.x,origin.y+c.y),uv,cc);
        draw->PrimWriteVtx(ImVec2(origin.x+d.x,origin.y+d.y),uv,cd);
    };
    const int first=draw->VtxBuffer.Size;
    for(size_t row=1;row<rows.size();++row) {
        const float y0=rows[row-1],y1=rows[row],left0=inset(y0),left1=inset(y1);
        for(int column=0;column<32;++column) {
            const float a=float(column)/32.f,b=float(column+1)/32.f;
            const float x0=left0+(w-2*left0)*a,x1=left0+(w-2*left0)*b;
            const float x2=left1+(w-2*left1)*b,x3=left1+(w-2*left1)*a;
            quad({x0,y0},{x1,y0},{x2,y1},{x3,y1},color(x0,y0,alpha),color(x1,y0,alpha),color(x2,y1,alpha),color(x3,y1,alpha));
        }
        // One-pixel antialias fringe around the rounded perimeter. Internal
        // cells share edges with no alpha overlap or visible mesh seams.
        quad({left0-1,y0},{left0,y0},{left1,y1},{left1-1,y1},
             color(left0,y0,0),color(left0,y0,alpha),color(left1,y1,alpha),color(left1,y1,0));
        quad({w-left0,y0},{w-left0+1,y0},{w-left1+1,y1},{w-left1,y1},
             color(w-left0,y0,alpha),color(w-left0,y0,0),color(w-left1,y1,0),color(w-left1,y1,alpha));
    }
    draw->PopClipRect();
    if(std::getenv("CLAW_METRICS_VERIFY")) {
        static bool seen[3][2]={};
        const int mode=ImClamp(int(params.claw_background_mode),0,2),vertical=params.claw_vertical_stack?1:0;
        if(!seen[mode][vertical] && HUDElements.sw_stats->n_frames>30) {
            seen[mode][vertical]=true;
            unsigned max_alpha=0;
            std::vector<unsigned> rgb_values;
            for(int i=first;i<draw->VtxBuffer.Size;++i) {
                const auto col=draw->VtxBuffer[i].col;
                max_alpha=std::max(max_alpha,(col>>IM_COL32_A_SHIFT)&255u);
                rgb_values.push_back(col&~IM_COL32_A_MASK);
            }
            std::sort(rgb_values.begin(),rgb_values.end());
            const auto distinct=std::unique(rgb_values.begin(),rgb_values.end())-rgb_values.begin();
            std::fprintf(stderr,"CLAW_BACKGROUND mode=%d vertical=%d stops=%zu alpha=%.3f vertices=%d max_alpha=%u colors=%zu\n",
                mode,vertical,ramp.stops.size(),alpha,draw->VtxBuffer.Size-first,max_alpha,size_t(distinct));
        }
    }
}
'''
replace('overlay.cpp','void render_imgui(swapchain_stats& data, struct overlay_params& params, ImVec2& window_size, bool is_vulkan)',
 helper+'\nvoid render_imgui(swapchain_stats& data, struct overlay_params& params, ImVec2& window_size, bool is_vulkan)')
replace('overlay.cpp','ImGui::Begin("Main", &gui_open, ImGuiWindowFlags_NoDecoration);',
 '''ImGui::Begin("Main", &gui_open, ImGuiWindowFlags_NoDecoration |
           (params.claw_background_mode ? ImGuiWindowFlags_NoBackground : 0));
       ClawDrawBackground(params);''')
print('Installed rounded solid/linear/radial multistop backgrounds')
