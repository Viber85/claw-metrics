"""Separate classic TDP title token 32 from the existing value token 27.

Run after verify_classic_superscript_baseline.py. The original 32 token IDs
stay unchanged; the title is appended to the map for old setting compatibility.
"""
from pathlib import Path
import sys
root=Path(sys.argv[1] if len(sys.argv)>1 else 'src')
path=root/'hud_elements.cpp';source=path.read_text()
anchor='void HudElements::_exec(){'
helper=r'''static void ClawTdpReading(const std::string& raw,bool vertical){
    const auto parts=claw_modular::power_parts(raw,"TDP");
    const bool verify=std::getenv("CLAW_METRICS_VERIFY")&&HUDElements.sw_stats->n_frames%60==0;
    auto* draw=ImGui::GetWindowDrawList();int first=draw->VtxBuffer.Size;
    ClawText(32,HUDElements.colors.engine,"%s",parts.first.c_str());
    auto report=[&](int token,int start){
        if(!verify)return;
        float top=1e10f,bottom=-1e10f;bool color_ok=true;
        const auto expected=ImGui::ColorConvertFloat4ToU32(ClawColorForToken(token,token==32?HUDElements.colors.engine:HUDElements.colors.text));
        for(int i=start;i<draw->VtxBuffer.Size;++i){top=ImMin(top,draw->VtxBuffer[i].pos.y);bottom=ImMax(bottom,draw->VtxBuffer[i].pos.y);color_ok&=draw->VtxBuffer[i].col==expected;}
        std::fprintf(stderr,"CLAW_TDP_STYLE vertical=%d raised=%d token=%d color=%08x color_ok=%d custom_font=%d separate_fonts=%d vertices=%d top=%.2f bottom=%.2f\n",
            vertical?1:0,HUDElements.params->claw_unit_superscript?1:0,token,expected,color_ok?1:0,ClawFontForToken(token)?1:0,ClawFontForToken(32)!=ClawFontForToken(27)?1:0,draw->VtxBuffer.Size-start,top,bottom);
    };
    report(32,first);
    if(vertical)ImGui::TableSetColumnIndex(1);else ClawMetricGap();
    first=draw->VtxBuffer.Size;
    ClawText(27,HUDElements.colors.text,"%s",parts.second.c_str());
    report(27,first);
}

'''
assert source.count(anchor)==1
source=source.replace(anchor,helper+anchor,1)
old='''            const std::string text = item.ret;
            const auto split = text.find_last_of(' ');'''
new='''            if(item.value.find("tdp.txt")!=std::string::npos){ClawTdpReading(item.ret,true);continue;}
            const std::string text = item.ret;
            const auto split = text.find_last_of(' ');'''
assert source.count(old)==1;source=source.replace(old,new,1)
old='ClawText(27, HUDElements.colors.text, "%s", item.ret.c_str());'
assert source.count(old)==1;source=source.replace(old,'ClawTdpReading(item.ret,false);',1)
path.write_text(source)
print('Separated TDP label token 32 and value token 27 in classic horizontal/vertical HUD')
