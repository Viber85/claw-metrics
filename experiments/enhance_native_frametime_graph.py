#!/usr/bin/env python3
"""Improve the *in-game* horizontal frametime graph, not the Decky menu icons.

MangoHud v0.8.1 draws the horizontal graph at font_size * 0.85 (15px for 18px
text); PlotHistogram tries to squeeze hundreds of 1-pixel-wide frame samples
into only ~150px. Keep the four graph styles and real frametime samples, but
make the plot taller and replace only the horizontal histogram with clearly
spaced, finite, independently sampled columns.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else "src")

def change(filename, old, new, label):
    path = root / filename
    source = path.read_text()
    count = source.count(old)
    if count != 1:
        raise RuntimeError(
            f"{label}: expected exactly one patch anchor in {filename}, got {count}"
        )
    path.write_text(source.replace(old, new, 1))

# The same figure must be used both by the real graph and the FPS-200%
# vertical-alignment helper. Otherwise the graph would be off-center.
change(
    "hud_elements.cpp",
    "height = HUDElements.params->font_size * 0.85;",
    """// Claw horizontal frametime graphs: readable at normal HUD sizes.
            // Vertical inset is still controlled exclusively by padding_y.
            height = ImClamp(HUDElements.params->font_size * 1.40f,
                             24.0f, 36.0f);""",
    "increase only horizontal graph display height",
)
change(
    "hud_elements.cpp",
    "125.0f : HUDElements.params->font_size * 0.85f;",
    """125.0f : ImClamp(HUDElements.params->font_size * 1.40f,
                              24.0f, 36.0f);""",
    "keep graph vertically centered relative to scaled FPS",
)

# Change only style C, not native non-horizontal histogram or other styles.
change(
    "hud_elements.cpp",
    """            if (HUDElements.params->enabled[OVERLAY_PARAM_ENABLED_horizontal]
                && claw_style == 2) {
                ImGui::PlotHistogram(hash, get_time_stat, HUDElements.sw_stats,
                    ARRAY_SIZE(HUDElements.sw_stats->frames_stats), 0,
                    NULL, min_time, max_time, ImVec2(width, height));
            } else if""",
    """            if (HUDElements.params->enabled[OVERLAY_PARAM_ENABLED_horizontal]
                && claw_style == 2) {
                // Native PlotHistogram tries to draw one bar per sample;
                // at 150px width this produces hairlines instead of columns.
                // Decimate the real data into 5-6px wide columns with a gap.
                const float w = ImMax(8.0f,
                    ImMin(width, ImGui::GetContentRegionAvail().x));
                const float h = ImMax(6.0f, height - 3.0f);
                const ImVec2 origin = ImGui::GetCursorScreenPos();
                ImGui::InvisibleButton("##claw_frametime_columns", ImVec2(w, h));
                ImDrawList* draw = ImGui::GetWindowDrawList();
                const int count = ARRAY_SIZE(HUDElements.sw_stats->frames_stats);
                const int n = ImMin(count, ImMax(2, int(w / 6.0f)));
                const float slot = w / float(n);
                const float bar_width = ImMax(2.0f, slot - 1.4f);
                const double safe_min =
                    std::isfinite(min_time) ? min_time : 0.0;
                const double safe_max =
                    std::isfinite(max_time) && max_time > safe_min
                    ? max_time : safe_min + 50.0;
                const double range = ImMax(0.001, safe_max - safe_min);
                const ImU32 color =
                    ImGui::ColorConvertFloat4ToU32(HUDElements.colors.frametime);
                const float bottom = origin.y + h;
                draw->PushClipRect(origin, ImVec2(origin.x + w, bottom), true);
                for (int i = 0; i < n; ++i) {
                    const int idx = i * (count - 1) / (n - 1);
                    const double raw = get_time_stat(HUDElements.sw_stats, idx);
                    if (!std::isfinite(raw) || raw <= safe_min)
                        continue;
                    const float fraction =
                        ImClamp(float((raw - safe_min) / range), 0.0f, 1.0f);
                    const float bar_height = ImMax(1.0f, fraction * (h - 1.0f));
                    const float x0 = origin.x + float(i) * slot + 0.7f;
                    draw->AddRectFilled(ImVec2(x0, bottom - bar_height),
                        ImVec2(x0 + bar_width, bottom), color);
                }
                draw->PopClipRect();
            } else if""",
    "draw readable separated histogram columns using real samples",
)

print("Claw in-game frametime graph taller and histogram drawn as separate columns")
