#!/usr/bin/env python3
"""Vertically align one-row Claw HUD items against its larger FPS number.

Runs after token styles, FPS-specific fonts and frametime graph styles were
patched into MangoHud 0.8.1. No sensor, TDP or configuration changes.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else "src")

def change(filename, original, replacement, name):
    path = root / filename
    source = path.read_text()
    matches = source.count(original)
    if matches != 1:
        raise RuntimeError(f"{name}: expected one anchor, found {matches}")
    path.write_text(source.replace(original, replacement, 1))

change("hud_elements.cpp",
    "static void ImguiNextColumnFirstItem()\n{",
    "static float ClawFpsVerticalCenterOffset(float item_height);\n\n"
    "static void ImguiNextColumnFirstItem()\n{",
    "forward declare vertical center calculation")

change("hud_elements.cpp",
    """static void ImguiNextColumnFirstItem()
{
    ImGui::TableNextColumn();
    HUDElements.table_columns_count += 1;
}""",
    """static void ImguiNextColumnFirstItem()
{
    ImGui::TableNextColumn();
    HUDElements.table_columns_count += 1;
    // Center every inline metric, no matter its order, against the enlarged
    // FPS numeral. The FPS group itself places label and number separately.
    if (!HUDElements.params || HUDElements.place < 0 ||
        size_t(HUDElements.place) >= HUDElements.ordered_functions.size())
        return;
    const std::string& group =
        HUDElements.ordered_functions[size_t(HUDElements.place)].name;
    if (group == "fps")
        return;
    float height = ImGui::GetFontSize();
    if (group == "frame_timing") {
        height = HUDElements.params->enabled[
            OVERLAY_PARAM_ENABLED_frame_timing_detailed] ?
            125.0f : HUDElements.params->font_size * 0.85f;
    }
    const float y_offset = ClawFpsVerticalCenterOffset(height);
    if (y_offset > 0.0f)
        ImGui::SetCursorPosY(ImGui::GetCursorPosY() + y_offset);
}""",
    "center every non-FPS metric in common table helper")

change("hud_elements.cpp",
    "static ImFont* ClawFontForToken(int token) {",
    """static float ClawFpsVerticalCenterOffset(float item_height) {
    const auto* p = HUDElements.params;
    if (!p || !p->claw_inline_metrics ||
        !p->enabled[OVERLAY_PARAM_ENABLED_horizontal] ||
        !p->enabled[OVERLAY_PARAM_ENABLED_fps] ||
        p->enabled[OVERLAY_PARAM_ENABLED_fps_only] ||
        p->claw_fps_scale <= 100)
        return 0.0f;
    const ImFont* fps_font = ClawFpsFontForToken();
    if (!fps_font)
        return 0.0f;
    const float fps_height =
        fps_font->FontSize * ImGui::GetIO().FontGlobalScale;
    return ImMax(0.0f, (fps_height - item_height) * 0.5f);
}

static ImFont* ClawFontForToken(int token) {""",
    "compute real FPS font height")

change("hud_elements.cpp",
    """            ImguiNextColumnFirstItem();
            const char* label = HUDElements.params->fps_text.empty()""",
    """            ImguiNextColumnFirstItem();
            const float claw_fps_row_top = ImGui::GetCursorPosY();
            const char* label = HUDElements.params->fps_text.empty()""",
    "capture unchanged FPS number origin")

change("hud_elements.cpp",
    """            ClawText(0, HUDElements.colors.engine, "%s", label);
            ClawMetricGap();""",
    """            ImGui::SetCursorPosY(claw_fps_row_top +
                ClawFpsVerticalCenterOffset(ImGui::GetFontSize()));
            ClawText(0, HUDElements.colors.engine, "%s", label);
            ClawMetricGap();
            // SameLine follows the label's y; restore the oversized numeral
            // to the original top after SameLine has placed its x coordinate.
            ImGui::SetCursorPosY(claw_fps_row_top);""",
    "center FPS label without moving large number")

change("hud_elements.cpp",
    """            if (HUDElements.params->enabled[OVERLAY_PARAM_ENABLED_frametime]) {
                ClawMetricGap();
                ClawText(2, HUDElements.colors.text, "%.1f",""",
    """            if (HUDElements.params->enabled[OVERLAY_PARAM_ENABLED_frametime]) {
                ClawMetricGap();
                ImGui::SetCursorPosY(claw_fps_row_top +
                    ClawFpsVerticalCenterOffset(ImGui::GetFontSize()));
                ClawText(2, HUDElements.colors.text, "%.1f",""",
    "center frametime ms beside enlarged FPS number")

print("Enabled vertical alignment for FPS label, FPS frametime, graph, CPU/GPU and all HUD metrics")
