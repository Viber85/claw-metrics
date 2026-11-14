#!/usr/bin/env python3
"""Connect Frame Gen telemetry to the bundled MangoHud renderer."""
from pathlib import Path
import sys

root = Path(sys.argv[1])
headers = Path(__file__).parent / 'native'


def replace(name, old, new):
    path = root / name
    text = path.read_text()
    if text.count(old) != 1:
        raise RuntimeError(f'{name}: Frame Gen anchor mismatch: {old[:80]!r}')
    path.write_text(text.replace(old, new, 1))


for name in ('claw_framegen.h', 'claw_framegen_graph.h', 'claw_framegen_protocol.h'):
    (root / name).write_bytes((headers / name).read_bytes())
replace('overlay.h', '#include "claw_frame_metrics.h"',
        '#include "claw_frame_metrics.h"\n#include "claw_framegen.h"')
replace('overlay.h', '   ClawFrameMetrics claw_frames;',
        '   ClawFrameMetrics claw_frames;\n   claw_framegen::Meter claw_framegen;')

options = ('claw_fps_game', 'claw_fps_generated', 'claw_fps_output', 'claw_framegen_graph')
anchor = '   OVERLAY_PARAM_CUSTOM(claw_fps_scale)               ' + chr(92)
replace('overlay_params.h', anchor, anchor + ''.join(
    '\n   OVERLAY_PARAM_CUSTOM(' + option + ')               ' + chr(92) for option in options))
anchor = '   bool claw_center_horizontal = false;'
replace('overlay_params.h', anchor, ''.join(
    f'   bool {option} = false;\n'
    for option in options) + anchor)
anchor = '#define parse_claw_fps_scale(s) parse_unsigned(s)'
replace('overlay_params.cpp', anchor, anchor + ''.join(
    f'\n#define parse_{option}(s) (parse_unsigned(s) != 0)' for option in options))

# Count only accepted Vulkan output submissions, sampled just before the call,
# after the HUD's own rendering. The next HUD draw sees the preceding result.
replace('vulkan.cpp', '      VkResult chain_result = queue_data->device->vtable.QueuePresentKHR(queue, &present_info);',
        '''      const auto& params = queue_data->device->instance->params;
      const bool framegen = params.claw_fps_game || params.claw_fps_generated ||
                            params.claw_fps_output || params.claw_framegen_graph;
      const auto at = framegen ? claw_framegen::now() : 0;
      if (present_info.pResults) present_info.pResults = pPresentInfo->pResults + i;
      VkResult chain_result = queue_data->device->vtable.QueuePresentKHR(queue, &present_info);
      const VkResult swap_result = present_info.pResults ? present_info.pResults[0] : chain_result;
      if (framegen && (swap_result == VK_SUCCESS || swap_result == VK_SUBOPTIMAL_KHR) &&
          (chain_result == VK_SUCCESS || chain_result == VK_SUBOPTIMAL_KHR)) {
         auto& meter = swapchain_data->sw_stats.claw_framegen;
         meter.presented(at);
         if (params.claw_fps_game || params.claw_fps_generated || params.claw_framegen_graph)
            meter.poll(at);
      }
'''.rstrip())
replace('gl/gl_hud.cpp', '    update_hud_info(sw_stats, params, vendorID);',
        '''    update_hud_info(sw_stats, params, vendorID);
    if (params.claw_fps_output || params.claw_framegen_graph)
        sw_stats.claw_framegen.presented(claw_framegen::now());''')
replace('hud_elements.cpp', 'static void ClawFpsSummaries() {',
        '''static void ClawFpsSummaries() {
    const auto& p = *HUDElements.params;
    if (p.claw_fps_game || p.claw_fps_generated || p.claw_fps_output) {
        const auto frames = HUDElements.sw_stats->claw_framegen.snapshot(claw_framegen::now(), false);
        if (p.claw_fps_game)
            ClawSupplementalReading("GAME",33,HUDElements.colors.engine,frames.game_fps,frames.game_fps>=0,"FPS");
        if (p.claw_fps_generated)
            ClawSupplementalReading("FG",34,HUDElements.colors.engine,frames.generated_fps,frames.generated_fps>=0,"FPS");
        if (p.claw_fps_output)
            ClawSupplementalReading("OUT",35,HUDElements.colors.engine,frames.output_fps,frames.output_fps>=0,"FPS");
    }
'''.rstrip())
replace('hud_elements.cpp', 'void HudElements::frame_timing(){',
        '''void HudElements::frame_timing(){
    const auto& p = *HUDElements.params;
    if (p.claw_framegen_graph) {
        ImguiNextColumnFirstItem();
        const auto origin = ImGui::GetCursorScreenPos();
        const bool vertical = p.claw_vertical_stack && !p.enabled[OVERLAY_PARAM_ENABLED_horizontal];
        const float requested = vertical && p.claw_vertical_graph_width > 0
            ? p.claw_vertical_graph_width : p.claw_graph_width;
        const float width = ImMax(1.f, requested);
        const float height = vertical ? p.claw_vertical_graph_height : ImClamp(p.font_size * 1.40f, 16.f, 72.f);
        ImGui::Dummy(ImVec2(width, height));
        if (!vertical) claw_fixed_slot_right = ImMax(claw_fixed_slot_right, origin.x + width);
        claw_framegen::paint_graph(ImGui::GetWindowDrawList(), origin, ImVec2(width,height),
            HUDElements.sw_stats->claw_framegen.snapshot(claw_framegen::now(), true),
            ImGui::ColorConvertFloat4ToU32(HUDElements.colors.frametime),
            IM_COL32(112,177,255,255));
        return;
    }''')
