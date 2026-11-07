"""Pack classic metric cells naturally and align FPS summaries with other groups.

Apply after enable_classic_overlay_options.py. Numerical stability is supplied
by tabular digit cells; only the outside background retains its largest width.
"""
from pathlib import Path
import sys
root=Path(sys.argv[1] if len(sys.argv)>1 else 'src')
def change(name,old,new):
    p=root/name;s=p.read_text();assert s.count(old)==1,(name,s.count(old),old[:70]);p.write_text(s.replace(old,new,1))
change('hud_elements.cpp','    HUDElements.colors.update = false;',
       '    HUDElements.colors.update = false;\n    claw_classic::width_floor()=0; // reset only when settings/style change')
change('hud_elements.cpp','''    const std::string reference = ClawSlotReference(token, fmt, rendered);''','''    if(token==1&&claw_classic::draw_number(rendered,ImGui::ColorConvertFloat4ToU32(color),
        HUDElements.params->enabled[OVERLAY_PARAM_ENABLED_text_outline]?ImGui::ColorConvertFloat4ToU32(HUDElements.colors.text_outline):0,HUDElements.params->text_outline_thickness)){
        claw_pending_text_width=0;claw_fixed_slot_right=ImMax(claw_fixed_slot_right,ImGui::GetItemRectMax().x);return;
    }
    const std::string reference = ClawSlotReference(token, fmt, rendered);''')
change('hud_elements.cpp','''    const auto* draw = ImGui::GetWindowDrawList();
    const int first_vertex = draw->VtxBuffer.Size;''','''    // The main FPS item positions its own label/number and skips the common
    // column centering helper. Its appended summaries must not skip it too.
    if (HUDElements.params->enabled[OVERLAY_PARAM_ENABLED_horizontal] &&
        HUDElements.params->claw_inline_metrics && (token==28||token==29))
        ImGui::SetCursorPosY(ImGui::GetCursorPosY()+ClawFpsVerticalCenterOffset(ImGui::GetFontSize()));
    const auto* draw = ImGui::GetWindowDrawList();
    const int first_vertex = draw->VtxBuffer.Size;''')
change('hud_elements.cpp','''        const float width = ImGui::CalcTextSize(label).x + HUDElements.params->claw_inner_gap
            + ImGui::CalcTextSize(number).x
            + ((unit && *unit) ? 1.0f + ImGui::CalcTextSize(unit).x : 0.0f);''','''        const std::string reading=std::string(number)+
            ((ready&&std::isfinite(value)&&unit&&*unit)?" "+std::string(unit):std::string());
        const float width=ImGui::CalcTextSize(label).x+HUDElements.params->claw_inner_gap+
            claw_classic::extent(token,reading,ImGui::GetFont(),ImGui::GetFontSize(),HUDElements.params->claw_unit_superscript,true).x;''')
change('overlay.cpp','   ImGuiTableFlags table_flags = ImGuiTableFlags_NoClip;',
       '   ImGuiTableFlags table_flags = claw_classic::table_flags(params.enabled[OVERLAY_PARAM_ENABLED_horizontal] && params.claw_inline_metrics);')
p=root/'overlay.cpp';s=p.read_text();old='params.claw_center_horizontal || params.claw_align_right || params.claw_center_vertical'
assert s.count(old)==2
s=s.replace(old,old+' || params.claw_inline_metrics')
old='''                   content_width = ImClamp(strip_width, 1.0f,
                       ImGui::GetIO().DisplaySize.x);'''
new='''                   content_width = ImClamp(params.claw_inline_metrics?claw_classic::hold_width(strip_width):strip_width, 1.0f,
                       ImGui::GetIO().DisplaySize.x);'''
assert s.count(old)==1;s=s.replace(old,new,1);p.write_text(s)
print('Classic horizontal readings use natural cell widths, tabular digits and centered FPS summaries')

# Check actual production glyph positions, including enlarged FPS text.
change('hud_elements.cpp','    if (font) ImGui::PopFont();\n}\n\nvoid HudElements::time(){',r'''    if(std::getenv("CLAW_METRICS_VERIFY")&&HUDElements.params->claw_inline_metrics&&HUDElements.params->enabled[OVERLAY_PARAM_ENABLED_horizontal]&&HUDElements.sw_stats->n_frames%60==0&&
       (token==3||((token==28||token==29)&&std::strcmp(fmt,"%s")==0))){
        auto* draw=ImGui::GetWindowDrawList();float top=1e10f,bottom=-1e10f;
        for(int i=classic_first_vertex;i<draw->VtxBuffer.Size;++i){top=ImMin(top,draw->VtxBuffer[i].pos.y);bottom=ImMax(bottom,draw->VtxBuffer[i].pos.y);}
        if(bottom>top)std::fprintf(stderr,"CLAW_CLASSIC_ALIGN frame=%llu token=%d scale=%u top=%.2f bottom=%.2f\n",static_cast<unsigned long long>(HUDElements.sw_stats->n_frames),token,HUDElements.params->claw_fps_scale,top,bottom);
    }
    if (font) ImGui::PopFont();
}

void HudElements::time(){''')
p=root/'overlay.cpp';s=p.read_text();s=s.replace('ox=%d oy=%d\\n','ox=%d oy=%d scale=%u\\n').replace('params.offset_x,params.offset_y);','params.offset_x,params.offset_y,params.claw_fps_scale);');p.write_text(s)
