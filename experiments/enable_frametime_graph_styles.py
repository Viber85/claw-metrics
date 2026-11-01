#!/usr/bin/env python3
"""A/F area / B line / C histogram for native MangoHud frametime graph."""
from pathlib import Path
import sys
root=Path(sys.argv[1] if len(sys.argv)>1 else "src")
def change(file,old,new):
    path=root/file
    source=path.read_text()
    if source.count(old)!=1:
        raise RuntimeError(f"{file}: expected exactly one anchor; got {source.count(old)}")
    path.write_text(source.replace(old,new,1))

change("overlay_params.h",
    "   OVERLAY_PARAM_CUSTOM(claw_align_right)             \\",
    "   OVERLAY_PARAM_CUSTOM(claw_align_right)             \\\n"
    "   OVERLAY_PARAM_CUSTOM(claw_graph_style)             \\")
change("overlay_params.h",
    "   bool claw_center_horizontal = false;",
    "   bool claw_center_horizontal = false;\n"
    "   int claw_graph_style = 0;")
change("overlay_params.cpp",
    "#define parse_claw_center_horizontal(s) parse_unsigned(s) != 0",
    "#define parse_claw_center_horizontal(s) parse_unsigned(s) != 0\n"
    "#define parse_claw_graph_style(s) parse_unsigned(s)")
# Avoid passing non-finite frametime samples to ImGui's vertex generator.
# During game startup / suspend-resume those counters can be temporarily invalid.
change("hud_elements.cpp", "#include <functional>",
       "#include <functional>\n#include <cmath>")
change("hud_elements.cpp",
    '            if (HUDElements.params->enabled[OVERLAY_PARAM_ENABLED_histogram]){',
    """            const int claw_style = HUDElements.params->claw_graph_style;
            if (HUDElements.params->enabled[OVERLAY_PARAM_ENABLED_horizontal]
                && claw_style == 2) {
                ImGui::PlotHistogram(hash, get_time_stat, HUDElements.sw_stats,
                    ARRAY_SIZE(HUDElements.sw_stats->frames_stats), 0,
                    NULL, min_time, max_time, ImVec2(width, height));
            } else if (HUDElements.params->enabled[OVERLAY_PARAM_ENABLED_horizontal]
                       && (claw_style == 1 || claw_style == 3)) {
                const float w = ImMax(8.0f, ImMin(width, ImGui::GetContentRegionAvail().x));
                const float h = ImMax(6.0f, height - 3.0f);
                const ImVec2 origin = ImGui::GetCursorScreenPos();
                ImGui::InvisibleButton("##claw_frametime_area", ImVec2(w, h));
                ImDrawList* draw = ImGui::GetWindowDrawList();
                const float bottom = origin.y + h;
                const ImVec4 clr = HUDElements.colors.frametime;
                const ImU32 fill = ImGui::ColorConvertFloat4ToU32(ImVec4(
                    clr.x, clr.y, clr.z, clr.w * (claw_style == 1 ? 0.75f : 0.22f)));
                const ImU32 stroke = ImGui::ColorConvertFloat4ToU32(clr);
                const int count = ARRAY_SIZE(HUDElements.sw_stats->frames_stats);
                const int n = ImMin(count, ImMax(2, int(w / 2.0f)));
                const double safe_min = std::isfinite(min_time) ? min_time : 0.0;
                const double safe_max = std::isfinite(max_time) && max_time > safe_min
                    ? max_time : safe_min + 50.0;
                const double range = ImMax(0.001, safe_max - safe_min);
                ImVec2 prev;
                draw->PushClipRect(origin, ImVec2(origin.x+w, bottom), true);
                for (int i=0; i<n; ++i) {
                    const int idx = i*(count-1)/(n-1);
                    const double raw_value = get_time_stat(HUDElements.sw_stats, idx);
                    const double value = std::isfinite(raw_value) ? raw_value : safe_min;
                    const float y = ImClamp(float((value-safe_min)/range), 0.0f, 1.0f);
                    const ImVec2 point(origin.x + w*float(i)/float(n-1),
                                      bottom-y*h);
                    if (i) {
                        draw->AddQuadFilled(prev, point, ImVec2(point.x,bottom),
                                            ImVec2(prev.x,bottom), fill);
                        draw->AddLine(prev, point, stroke, claw_style == 1 ? 1.0f : 1.6f);
                    }
                    prev=point;
                }
                draw->PopClipRect();
            } else if (HUDElements.params->enabled[OVERLAY_PARAM_ENABLED_histogram]
                       && !(HUDElements.params->enabled[OVERLAY_PARAM_ENABLED_horizontal]
                            && claw_style == 0)) {""")
print("Four selectable native frametime graph styles installed")
