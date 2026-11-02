#!/usr/bin/env python3
"""Install measured FPS summaries and compact process/SWAP readings after all patches."""
from pathlib import Path
import sys
root = Path(sys.argv[1] if len(sys.argv)>1 else 'src')
def replace(name, old, new):
 p=root/name;s=p.read_text()
 if s.count(old)!=1: raise RuntimeError(f'{name}: extra metric anchor count {s.count(old)}: {old[:60]}')
 p.write_text(s.replace(old,new,1))
(root/'claw_frame_metrics.h').write_bytes((Path(__file__).parent/'native/claw_frame_metrics.h').read_bytes())
replace('overlay.h','#include <deque>','#include <deque>\n#include "claw_frame_metrics.h"')
replace('overlay.h','struct swapchain_stats {','struct swapchain_stats {\n   ClawFrameMetrics claw_frames;')
# Private options have no upstream fpsMetrics worker/lifetime dependencies.
names=('claw_fps_average','claw_fps_low1','claw_ram_game')
replace('overlay_params.h','   OVERLAY_PARAM_CUSTOM(claw_fps_scale)               \\',
 '   OVERLAY_PARAM_CUSTOM(claw_fps_scale)               \\\n'+''.join('   OVERLAY_PARAM_CUSTOM('+n+')               \\\n' for n in names).rstrip('\n'))
replace('overlay_params.h','   bool claw_center_horizontal = false;',
 ''.join('   bool '+n+' = false;\n' for n in names)+'   bool claw_center_horizontal = false;')
replace('overlay_params.cpp','#define parse_claw_fps_scale(s) parse_unsigned(s)',
 '#define parse_claw_fps_scale(s) parse_unsigned(s)\n'+ '\n'.join('#define parse_'+n+'(s) parse_unsigned(s) != 0' for n in names))
replace('overlay.cpp','   if (sw_stats.last_present_time) {','''   if (!params.claw_fps_average && !params.claw_fps_low1)
      sw_stats.claw_frames.reset();
   else if (sw_stats.last_present_time)
      sw_stats.claw_frames.add(now, frametime_ms);
   if (sw_stats.last_present_time) {''')
replace('overlay.cpp','   if (params.enabled[OVERLAY_PARAM_ENABLED_procmem])',
 '   if (params.enabled[OVERLAY_PARAM_ENABLED_procmem] || params.claw_ram_game)')
replace('memory.h','extern uint64_t proc_mem_resident, proc_mem_shared, proc_mem_virt;',
        'extern uint64_t proc_mem_resident, proc_mem_shared, proc_mem_virt;\nextern bool claw_proc_mem_valid;')
replace('memory.cpp','uint64_t proc_mem_resident, proc_mem_shared, proc_mem_virt;',
        'uint64_t proc_mem_resident, proc_mem_shared, proc_mem_virt;\nbool claw_proc_mem_valid = false;')
replace('memory.cpp','void update_procmem()\n{','void update_procmem()\n{\n    claw_proc_mem_valid = false;')
replace('memory.cpp','    proc_mem_shared = meminfo[2];','    proc_mem_shared = meminfo[2];\n    claw_proc_mem_valid = true;')
# Compact supplemental readings form a normal-sized group; only main FPS is enlarged.
helper=r'''
static void ClawSupplementalReading(const char* label, int token, ImVec4 label_color,
                                    double value, bool ready, const char* unit) {
    ImguiNextColumnFirstItem();
    const auto* draw = ImGui::GetWindowDrawList();
    const int first_vertex = draw->VtxBuffer.Size;
    ClawText(token, label_color, "%s", label);
    ClawMetricGap();
    if (ready && std::isfinite(value))
        ClawText(token, HUDElements.colors.text, "%.1f", value);
    else
        ClawText(token, HUDElements.colors.text, "%s", "--");
    if (unit && *unit) {
        ImGui::SameLine(0.0f, 1.0f);
        ClawText(token, HUDElements.colors.text, "%s", unit);
    }
    // Opt-in CI evidence from the actual Vulkan draw branch; silent in normal games.
    if (std::getenv("CLAW_METRICS_VERIFY") && ready && token>=28 && token<=31) {
        static bool seen[4][4] = {};
        const int mode = HUDElements.params->claw_vertical_stack ? 1 :
                         (HUDElements.params->claw_inline_metrics ? 0 : 2);
        if (!seen[mode][token-28]) {
            seen[mode][token-28] = true;
            float left=100000.0f,top=100000.0f,right=0.0f,bottom=0.0f;
            for (int i=first_vertex;i<draw->VtxBuffer.Size;++i) {
                left=ImMin(left,draw->VtxBuffer[i].pos.x); top=ImMin(top,draw->VtxBuffer[i].pos.y);
                right=ImMax(right,draw->VtxBuffer[i].pos.x); bottom=ImMax(bottom,draw->VtxBuffer[i].pos.y);
            }
            std::fprintf(stderr,"CLAW_EXTRA mode=%d token=%d value=%.4f x=%.1f y=%.1f right=%.1f bottom=%.1f vertices=%d\n",
                         mode,token,value,left,top,right,bottom,draw->VtxBuffer.Size-first_vertex);
        }
    }
}
static void ClawFpsSummaries() {
    const auto& stats = HUDElements.sw_stats->claw_frames;
    if (HUDElements.params->claw_fps_average)
        ClawSupplementalReading("AVG",28,HUDElements.colors.engine,
                                stats.average,stats.count()>0,"FPS");
    if (HUDElements.params->claw_fps_low1)
        ClawSupplementalReading("1% LOW",29,HUDElements.colors.engine,
                                stats.low1,stats.low1_ready,"FPS");
}
'''
replace('hud_elements.cpp','void HudElements::fps(){',helper+'\nvoid HudElements::fps(){')
p=root/'hud_elements.cpp';s=p.read_text();a=s.index('void HudElements::fps(){');b=s.index('\nvoid HudElements::fps_only()',a);chunk=s[a:b];chunk=chunk.replace('            return;','            ClawFpsSummaries();\n            return;',1)
# Also handle non-inline native mode without changing stock fallback configs.
anchor='    } else if (HUDElements.params->enabled[OVERLAY_PARAM_ENABLED_engine_version])'
if chunk.count(anchor)!=1: raise RuntimeError('FPS fallback anchor')
chunk=chunk.replace(anchor,'        ClawFpsSummaries();\n'+anchor,1);s=s[:a]+chunk+s[b:];p.write_text(s)
# Existing swap rendering inside compact RAM must not duplicate the new group.
s=p.read_text();a=s.index('void HudElements::ram(){');b=s.index('\nvoid HudElements::procmem()',a);chunk=s[a:b];start=chunk.index('        if (HUDElements.params->enabled[OVERLAY_PARAM_ENABLED_swap]) {');end=chunk.index('\n        return;',start)
chunk=chunk[:start]+'''        if (HUDElements.params->claw_ram_game)
            ClawSupplementalReading("GAME",30,HUDElements.colors.ram,
                                    proc_mem_resident / 1073741824.0,claw_proc_mem_valid,"GiB");
        if (HUDElements.params->enabled[OVERLAY_PARAM_ENABLED_swap])
            ClawSupplementalReading("SWAP",31,HUDElements.colors.ram,swapused,true,"GiB");'''+chunk[end:]
# The non-inline mode needs the same readings, with explicit SWAP labeling.
a=chunk.index('    if (HUDElements.params->enabled[OVERLAY_PARAM_ENABLED_ram] && HUDElements.params->enabled[OVERLAY_PARAM_ENABLED_swap]){')
b=chunk.index('\n#endif',a)
chunk=chunk[:a]+'''    if (HUDElements.params->enabled[OVERLAY_PARAM_ENABLED_ram]) {
        if (HUDElements.params->claw_ram_game)
            ClawSupplementalReading("GAME",30,HUDElements.colors.ram,
                                    proc_mem_resident / 1073741824.0,claw_proc_mem_valid,"GiB");
        if (HUDElements.params->enabled[OVERLAY_PARAM_ENABLED_swap])
            ClawSupplementalReading("SWAP",31,HUDElements.colors.ram,swapused,true,"GiB");
    }'''+chunk[b:]
# The helper must be defined before ram(), not only before fps().
ram_start=s.index('void HudElements::ram(){');ram_end=s.index('\nvoid HudElements::procmem()',ram_start)
s=s[:ram_start]+chunk+s[ram_end:];s=s.replace(helper+'\n','',1);s=s.replace('void HudElements::ram(){',helper+'\nvoid HudElements::ram(){',1)
# Stable numeric widths and correct unit-aware wrapping for the four appended tokens.
s=s.replace('        case 1:  return "888";', '        case 28: case 29: return numeric ? "8888.8" : "";\n        case 30: case 31: return numeric ? "88.8" : "";\n        case 1:  return "888";',1)
s=s.replace('if (token==6 || token==11 || token==21) suffix = "MHz";', 'if (token==28 || token==29) suffix = "FPS";\n            else if (token==30 || token==31) suffix = "GiB";\n            else if (token==6 || token==11 || token==21) suffix = "MHz";',1)
p.write_text(s)
print('Installed rolling 60s average/slowest-1% summaries, game RSS and system SWAP')
