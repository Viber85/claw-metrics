"""Classic HUD units, group spacing and measured center-edge anchors.

Run after enable_modular_renderer.py; keep the existing classic layout engine.
"""
from pathlib import Path
import re
import sys

root=Path(sys.argv[1] if len(sys.argv)>1 else 'src')
def change(name,old,new):
    p=root/name;s=p.read_text();assert s.count(old)==1,(name,s.count(old),old[:70]);p.write_text(s.replace(old,new,1))
(root/'claw_classic_units.h').write_bytes((Path(__file__).parent/'native/claw_classic_units.h').read_bytes())
change('overlay_params.h','   OVERLAY_PARAM_CUSTOM(claw_unit_superscript)               \\',
       '   OVERLAY_PARAM_CUSTOM(claw_unit_superscript)               \\\n   OVERLAY_PARAM_CUSTOM(claw_center_vertical)               \\\n   OVERLAY_PARAM_CUSTOM(claw_group_gap_x)               \\')
change('overlay_params.h','   bool claw_unit_superscript = false;',
       '   bool claw_unit_superscript = false;\n   bool claw_center_vertical = false;\n   float claw_group_gap_x = 0;')
change('overlay_params.cpp','#define parse_claw_unit_superscript(s) parse_unsigned(s)',
       '#define parse_claw_unit_superscript(s) parse_unsigned(s)\n#define parse_claw_center_vertical(s) parse_unsigned(s) != 0\n#define parse_claw_group_gap_x(s) parse_float(s)')
change('hud_elements.cpp','#include "claw_modular_imgui.h"','#include "claw_modular_imgui.h"\n#include "claw_classic_units.h"')
change('overlay.cpp','#include "claw_horizontal_separator.h"','#include "claw_horizontal_separator.h"\n#include "claw_classic_units.h"')
change('overlay.cpp','void RenderOutlinedText(const char* text, ImU32 textColor) {', '''void RenderOutlinedText(const char* text, ImU32 textColor) {
   if(HUDElements.params->claw_unit_superscript && !HUDElements.params->claw_inline_metrics && claw_classic::finish_unit(text,textColor,HUDElements.params->enabled[OVERLAY_PARAM_ENABLED_text_outline]?ImGui::ColorConvertFloat4ToU32(HUDElements.colors.text_outline):0,HUDElements.params->text_outline_thickness)){
       if(std::getenv("CLAW_METRICS_VERIFY")&&HUDElements.sw_stats->n_frames%60==0)std::fprintf(stderr,"CLAW_CLASSIC_LEGACY unit=%s\\n",text);
       return;
   }''')
change('overlay.cpp','   RenderOutlinedText(buffer, ImGui::ColorConvertFloat4ToU32(col));', '''   const bool classic_units=HUDElements.params->claw_unit_superscript&&!HUDElements.params->claw_inline_metrics;
   const auto pending_number=classic_units?claw_classic::capture_number(buffer,ImGui::ColorConvertFloat4ToU32(col)):claw_classic::PendingNumber{};
   RenderOutlinedText(buffer, ImGui::ColorConvertFloat4ToU32(col));
   if(classic_units)claw_classic::commit_number(pending_number);''')
change('hud_elements.cpp','style.CellPadding.x = params.claw_table_padding_x;',
       'style.CellPadding.x = params.claw_table_padding_x + (params.enabled[OVERLAY_PARAM_ENABLED_horizontal] ? ImClamp(params.claw_group_gap_x,0.0f,60.0f)*0.5f : 0.0f);')
change('overlay.cpp','   if (params.claw_center_horizontal &&', '''   if (params.claw_center_vertical) {
       const auto screen=ImGui::GetIO().DisplaySize;
       const float x=params.claw_align_right?screen.x-window_size.x+params.offset_x:params.offset_x;
       data.main_window_pos=ImVec2(x,(screen.y-window_size.y)*0.5f+params.offset_y);
       ImGui::SetNextWindowPos(data.main_window_pos,ImGuiCond_Always);
       return;
   }
   if (params.claw_center_horizontal &&''')
p=root/'overlay.cpp';s=p.read_text();assert 'params.claw_center_horizontal || params.claw_align_right' in s;s=s.replace('params.claw_center_horizontal || params.claw_align_right','params.claw_center_horizontal || params.claw_align_right || params.claw_center_vertical');p.write_text(s)
p=root/'hud_elements.cpp';s=p.read_text()
# Merge separate unit-font items into one atomic reading. This also makes
# vertical wrapping measure the actual complete reading before it is drawn.
pattern=r'ClawText\((\d+), ([^,\n]+), "([^"\n]+)"([^;]*?)\);\s*ImGui::SameLine\(0\.0f, 1\.0f\);\s*(?:if \(!HUDElements.params->claw_vertical_stack\) )?ImGui::PushFont\(HUDElements.sw_stats->font1\);\s*ClawText\(\1, \2, "(MHz|W|GiB|ms)"\);\s*(?:if \(!HUDElements.params->claw_vertical_stack\) )?ImGui::PopFont\(\);'
s,n=re.subn(pattern,lambda m:f'ClawText({m[1]}, {m[2]}, "{m[3]} {m[5]}"{m[4]});',s)
assert n==9,('Expected nine atomic classic number/unit readings',n)
old='''    if (ready && std::isfinite(value))
        ClawText(token, HUDElements.colors.text, "%.1f", value);
    else
        ClawText(token, HUDElements.colors.text, "%s", "--");
    if (unit && *unit) {
        ImGui::SameLine(0.0f, 1.0f);
        ClawText(token, HUDElements.colors.text, "%s", unit);
    }'''
assert s.count(old)==1
s=s.replace(old,'''    if (ready && std::isfinite(value))
        ClawText(token, HUDElements.colors.text, "%.1f %s", value,unit?unit:"");
    else
        ClawText(token, HUDElements.colors.text, "%s", "--");''',1)
# Only the ClawText call site changes; the original fixed-slot helper remains
# the fallback for labels, clocks, main FPS and unsupported strings.
old='    ClawStableText(token, color, fmt, args...);\n    if (font) ImGui::PopFont();'
assert s.count(old)==1
s=s.replace(old,'''    char classic_reading[192];std::snprintf(classic_reading,sizeof(classic_reading),fmt,args...);
    const int classic_first_vertex=ImGui::GetWindowDrawList()->VtxBuffer.Size;
    const bool classic_stable=HUDElements.params->enabled[OVERLAY_PARAM_ENABLED_horizontal];
    if(claw_classic::draw(token,classic_reading,ImGui::ColorConvertFloat4ToU32(color),HUDElements.params->claw_unit_superscript,classic_stable,HUDElements.params->enabled[OVERLAY_PARAM_ENABLED_text_outline]?ImGui::ColorConvertFloat4ToU32(HUDElements.colors.text_outline):0,HUDElements.params->text_outline_thickness)){
        if(std::getenv("CLAW_METRICS_VERIFY")&&HUDElements.sw_stats->n_frames%60==0)std::fprintf(stderr,"CLAW_CLASSIC_UNIT vertical=%d raised=%d token=%d vertices=%d\\n",HUDElements.params->claw_vertical_stack?1:0,HUDElements.params->claw_unit_superscript?1:0,token,ImGui::GetWindowDrawList()->VtxBuffer.Size-classic_first_vertex);
        claw_pending_text_width=0;
        if(classic_stable)claw_fixed_slot_right=ImMax(claw_fixed_slot_right,ImGui::GetItemRectMax().x);
    }else ClawStableText(token, color, fmt, args...);
    if (font) ImGui::PopFont();''',1)
s=s.replace('if (*suffix) needed += 1.0f + ImGui::CalcTextSize(suffix).x;',
            'if (*suffix && !std::strstr(displayed,suffix)) needed += 1.0f + ImGui::CalcTextSize(suffix).x;')
old='HUDElements.TextColored(HUDElements.colors.text,\n                                    "%s", value.c_str());'
assert s.count(old)==1
s=s.replace(old,'ClawText(token, HUDElements.colors.text, "%s", value.c_str());',1)
p.write_text(s)
change('overlay.cpp','      ImGui::End();\n      if (claw_ink_trim) ImGui::PopStyleVar();', '''      if(std::getenv("CLAW_METRICS_VERIFY")&&data.n_frames>100&&data.n_frames%60==0){
          const auto pos=ImGui::GetWindowPos(),box=ImGui::GetWindowSize(),screen=ImGui::GetIO().DisplaySize;
          std::fprintf(stderr,"CLAW_CLASSIC vertical=%d units=%d center=%d right=%d gap=%.1f inline=%d x=%.1f y=%.1f w=%.1f h=%.1f sw=%.0f sh=%.0f ox=%d oy=%d\\n",
              params.claw_vertical_stack?1:0,params.claw_unit_superscript?1:0,params.claw_center_vertical?1:0,params.claw_align_right?1:0,params.claw_group_gap_x,params.claw_inline_metrics?1:0,pos.x,pos.y,box.x,box.y,screen.x,screen.y,params.offset_x,params.offset_y);
      }
      ImGui::End();
      if (claw_ink_trim) ImGui::PopStyleVar();''')
print('Enabled classic unit rendering, independent horizontal group gap and center-edge anchors')
