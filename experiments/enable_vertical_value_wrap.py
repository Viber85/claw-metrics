#!/usr/bin/env python3
"""Wrap complete metric values within the native two-column Claw Vertical HUD.

Installed AFTER enable_vertical_stacked.py and the per-token font patches.
Only activates when claw_vertical_stack is set, and never modifies the
horizontal renderer or MangoHud's stock vertical fallback.
"""
from pathlib import Path
import sys

root=Path(sys.argv[1] if len(sys.argv)>1 else "src")
source=root/"hud_elements.cpp"
s=source.read_text(encoding="utf-8")

def change(old,new,name):
    global s
    count=s.count(old)
    if count!=1:
        raise RuntimeError(f"{name}: expected 1 anchor, got {count}")
    s=s.replace(old,new,1)

change(
    "static bool claw_vertical_first_value = false;",
    """static bool claw_vertical_first_value = false;
// Deferred placement allows measuring the ENTIRE next reading before drawing.
static bool claw_vertical_pending = false;
static bool claw_vertical_pending_first = false;
static float claw_vertical_values_x = 0.0f;""",
    "vertical wrapping state")

change(
    """    claw_vertical_first_value = HUDElements.params &&
        HUDElements.params->claw_vertical_stack &&
        !HUDElements.params->enabled[OVERLAY_PARAM_ENABLED_horizontal];""",
    """    claw_vertical_first_value = HUDElements.params &&
        HUDElements.params->claw_vertical_stack &&
        !HUDElements.params->enabled[OVERLAY_PARAM_ENABLED_horizontal];
    claw_vertical_pending = false;
    claw_vertical_pending_first = false;""",
    "reset state for every new metric group")

change(
    """static void ClawMetricGap() {
    if (HUDElements.params->claw_vertical_stack &&
        !HUDElements.params->enabled[OVERLAY_PARAM_ENABLED_horizontal] &&
        claw_vertical_first_value) {
        claw_vertical_first_value = false;
        ImGui::TableSetColumnIndex(1);
    } else {
        ImGui::SameLine(0.0f,
            HUDElements.params->claw_vertical_stack
                ? HUDElements.params->claw_vertical_value_gap
                : HUDElements.params->claw_inner_gap);
    }
}""",
    """static void ClawMetricGap() {
    if (HUDElements.params->claw_vertical_stack &&
        !HUDElements.params->enabled[OVERLAY_PARAM_ENABLED_horizontal]) {
        if (claw_vertical_first_value) {
            claw_vertical_first_value = false;
            ImGui::TableSetColumnIndex(1);
            claw_vertical_values_x = ImGui::GetCursorScreenPos().x;
            claw_vertical_pending_first = true;
        } else {
            claw_vertical_pending_first = false;
        }
        claw_vertical_pending = true;
        return;
    }
    ImGui::SameLine(0.0f, HUDElements.params->claw_inner_gap);
}""",
    "defer vertical SameLine until actual token width is known")

# IMPORTANT: A clock value such as 2532MHz or 2.1W consists of two ClawText
# calls in the existing renderer. The width test must include the later unit,
# so MHz/W/GiB never end up on their own line.
before = """template<typename... Args>
static void ClawText(int token, ImVec4 color, const char* fmt, Args... args) {
    color = ClawColorForToken(token, color);
    ImFont* font = ClawFontForToken(token);
    if (font) ImGui::PushFont(font);
    ClawStableText(token, color, fmt, args...);
    if (font) ImGui::PopFont();
}"""
after = """template<typename... Args>
static void ClawText(int token, ImVec4 color, const char* fmt, Args... args) {
    color = ClawColorForToken(token, color);
    ImFont* font = ClawFontForToken(token);
    if (font) ImGui::PushFont(font);
    if (HUDElements.params && HUDElements.params->claw_vertical_stack &&
        !HUDElements.params->enabled[OVERLAY_PARAM_ENABLED_horizontal] &&
        claw_vertical_pending) {
        const bool first = claw_vertical_pending_first;
        claw_vertical_pending = false;
        claw_vertical_pending_first = false;
        if (!first) {
            ImGui::SameLine(0.0f, HUDElements.params->claw_vertical_value_gap);
            char displayed[192];
            std::snprintf(displayed, sizeof(displayed), fmt, args...);
            const char* suffix = "";
            // Atomic number+unit measurement, using the actual selected font.
            if (token==6 || token==11 || token==21) suffix = "MHz";
            else if (token==7 || token==12 || token==25) suffix = "W";
            else if (token==17 || token==19) suffix = "GiB";
            else if (token==2) suffix = "ms";
            float needed = ImGui::CalcTextSize(displayed).x;
            if (*suffix) needed += 1.0f + ImGui::CalcTextSize(suffix).x;
            const ImGuiStyle& style = ImGui::GetStyle();
            const float right = ImGui::GetWindowPos().x + ImGui::GetWindowWidth()
                - style.WindowPadding.x - style.CellPadding.x - 3.0f;
            const float x = ImGui::GetCursorScreenPos().x;
            // Never start a new row before the very first value. A value
            // taller than the available column cannot be split at a digit.
            if (x + needed > right && x > claw_vertical_values_x + 0.5f) {
                ImGui::NewLine();
                const float y = ImGui::GetCursorScreenPos().y;
                ImGui::SetCursorScreenPos(ImVec2(claw_vertical_values_x, y));
            }
        }
    }
    ClawStableText(token, color, fmt, args...);
    if (font) ImGui::PopFont();
}"""
change(before, after, "atomic next-value measurement and wrap")

source.write_text(s,encoding="utf-8")
print("Enabled Claw Vertical per-metric value wrapping (horizontal unchanged)")
