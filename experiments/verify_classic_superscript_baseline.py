"""Instrument actual classic label/number/unit glyphs for opt-in CI checks.

Apply after fix_classic_spacing_alignment.py. Rendering itself is implemented
in claw_classic_units.h; this hook verifies the resulting production geometry.
"""
from pathlib import Path
import sys

root=Path(sys.argv[1] if len(sys.argv)>1 else 'src')
path=root/'hud_elements.cpp'
source=path.read_text()
old='''    const bool classic_stable=HUDElements.params->enabled[OVERLAY_PARAM_ENABLED_horizontal];
    if(claw_classic::draw'''
new='''    const bool classic_stable=HUDElements.params->enabled[OVERLAY_PARAM_ENABLED_horizontal];
    const bool classic_verify=std::getenv("CLAW_METRICS_VERIFY")&&HUDElements.sw_stats->n_frames%60==0;
    claw_classic::DrawInk classic_ink;
    if(claw_classic::draw'''
assert source.count(old)==1
source=source.replace(old,new,1)
old='HUDElements.params->text_outline_thickness)){\n        if(std::getenv("CLAW_METRICS_VERIFY")'
new='HUDElements.params->text_outline_thickness,0,classic_verify?&classic_ink:nullptr)){\n        if(std::getenv("CLAW_METRICS_VERIFY")'
assert source.count(old)==1
source=source.replace(old,new,1)
old='''    }else ClawStableText(token, color, fmt, args...);
    if(std::getenv("CLAW_METRICS_VERIFY")'''
new=r'''    }else ClawStableText(token, color, fmt, args...);
    if(classic_verify&&HUDElements.params->claw_inline_metrics&&(token==3||token==4||token==28||token==29)){
        auto report=[&](const char* kind,float top,float bottom){
            if(bottom>top)std::fprintf(stderr,"CLAW_CLASSIC_BASELINE frame=%llu token=%d vertical=%d raised=%d scale=%u kind=%s top=%.2f bottom=%.2f\n",
                static_cast<unsigned long long>(HUDElements.sw_stats->n_frames),token,HUDElements.params->claw_vertical_stack?1:0,HUDElements.params->claw_unit_superscript?1:0,HUDElements.params->claw_fps_scale,kind,top,bottom);
        };
        if(classic_ink.number_bottom>classic_ink.number_top){
            report("number",classic_ink.number_top,classic_ink.number_bottom);
            report("unit",classic_ink.unit_top,classic_ink.unit_bottom);
        }else{
            auto* draw=ImGui::GetWindowDrawList();float top=1e10f,bottom=-1e10f;
            for(int i=classic_first_vertex;i<draw->VtxBuffer.Size;++i){top=ImMin(top,draw->VtxBuffer[i].pos.y);bottom=ImMax(bottom,draw->VtxBuffer[i].pos.y);}
            report("label",top,bottom);
        }
    }
    if(std::getenv("CLAW_METRICS_VERIFY")'''
assert source.count(old)==1
path.write_text(source.replace(old,new,1))
print('Enabled opt-in production glyph baseline verification for classic superscript units')
