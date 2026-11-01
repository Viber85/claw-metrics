#!/usr/bin/env python3
"""Freeze numerical HUD slots without padding the user's inter-metric gaps.

Applied last, after the pinned MangoHud 0.8.1 patches, individual Claw
font weights, live-scaled FPS digits and automatic horizontal centering.
No change to sampling, ordering, colors, graphics or stock MangoHud paths.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv)>1 else "src")

def change(name, before, after, reason):
    path = root/name
    old = path.read_text()
    count = old.count(before)
    if count != 1:
        raise RuntimeError(f"{reason}: expected exactly 1 anchor in {name}, got {count}: {before[:90]!r}")
    path.write_text(old.replace(before, after, 1))

change("hud_elements.cpp", "#include <functional>",
       "#include <functional>\n#include <cstdio>\n#include <cstring>", "stdlib formatting")

change("hud_elements.cpp",
    """template<typename... Args>
static void ClawText(int token, ImVec4 color, const char* fmt, Args... args) {
    color = ClawColorForToken(token, color);
    ImFont* font = ClawFontForToken(token);
    if (font) ImGui::PushFont(font);
    HUDElements.TextColored(color, fmt, args...);
    if (font) ImGui::PopFont();
}""",
    """// Absolute screen-space right edge of a text slot after its reserved width.
// The centered window uses this edge in addition to the actual draw vertices.
// A plain GetItemRectMax from a 64-column ImGui table is not usable here.
float claw_fixed_slot_right = 0.0f;

// Reserve only numerical fields, not labels, separator margins, graphs or
// metric groups. This preserves the user's own inner_gap/element_gap settings.
static std::string ClawSlotReference(int token, const char* fmt, const char* current) {
    if (!fmt || !current) return {};
    const bool numeric = fmt[0] == '%' && std::strcmp(fmt, "%s") != 0;
    if (!numeric && token != 25 && token != 26 && token != 27) return {};
    switch (token) {
        case 1:  return "888";          // numeric FPS (0..999)
        case 2:  return numeric ? "888.8" : "";  // frametime ms, no padding unit
        case 4: case 9: case 23: return "100%"; // CPU/GPU/BATT load
        case 5: case 10: case 20:
            return "888°" + std::string(std::strchr(current,'F') ? "F" : "C");
        case 13:
            return "888°" + std::string(std::strchr(current,'F') ? "F" : "C") + " Jnc";
        case 6: case 11: case 21:
            return numeric ? "8888" : "";   // separate MHz labels
        case 7: case 12:
            return numeric ? "88.8" : "";   // separate W labels
        case 14:
            return std::strstr(fmt, "RPM") ? "88888 RPM" : "100% FAN";
        case 15: return "8888 mV";
        case 17: case 19: return numeric ? "88.8" : ""; // GiB
        case 24: return "88:88";            // battery remaining time
        case 26: return "88:88";            // 24-hour clock
        case 25: case 27:
            if (std::strcmp(fmt, "%s") != 0)
                return numeric ? "88.8" : "";
            // TDP and DRAW are single read-only exec strings, possibly with
            // a user label or "--" when disconnected. Keep the label, reserve
            // width for their maximum normal wattage, and do not let "--"
            // collapse the whole strip.
            {
                const std::string displayed(current);
                const size_t last_space = displayed.rfind(' ');
                const std::string prefix = last_space == std::string::npos ?
                    std::string() : displayed.substr(0, last_space+1);
                return prefix + (token == 27 ? "888W" : "88.8W");
            }
        default: return {};
    }
}

template<typename... Args>
static void ClawStableText(int token, ImVec4 color, const char* fmt, Args... args) {
    if (!HUDElements.params || !HUDElements.params->claw_inline_metrics ||
        !HUDElements.params->enabled[OVERLAY_PARAM_ENABLED_horizontal]) {
        HUDElements.TextColored(color, fmt, args...);
        return;
    }
    char rendered[192];
    std::snprintf(rendered, sizeof(rendered), fmt, args...);
    const std::string reference = ClawSlotReference(token, fmt, rendered);
    if (reference.empty()) {
        HUDElements.TextColored(color, "%s", rendered);
        return;
    }

    // Use the currently selected per-token font when measuring widths.
    // 0/8 cover wide numerical glyphs in the included Barlow typeface.
    const float printed_width = ImGui::CalcTextSize(rendered).x;
    const float example_width = ImGui::CalcTextSize(reference.c_str()).x;
    std::string zeroes = reference;
    for (char& c : zeroes) if (c == '8') c = '0';
    const float zero_width = ImGui::CalcTextSize(zeroes.c_str()).x;
    const float slot_width = ImMax(printed_width,
                                  ImMax(example_width, zero_width)) + 1.0f;

    ImGui::BeginGroup();
    HUDElements.TextColored(color, "%s", rendered);
    // An invisible ImGui item extends the group's bounding rectangle;
    // the next SameLine starts at this constant edge, not the text width.
    ImGui::SameLine(0.0f, 0.0f);
    ImGui::Dummy(ImVec2(ImMax(0.0f, slot_width-printed_width), 1.0f));
    ImGui::EndGroup();
    claw_fixed_slot_right = ImMax(claw_fixed_slot_right, ImGui::GetItemRectMax().x);
}

template<typename... Args>
static void ClawText(int token, ImVec4 color, const char* fmt, Args... args) {
    color = ClawColorForToken(token, color);
    ImFont* font = ClawFontForToken(token);
    if (font) ImGui::PushFont(font);
    ClawStableText(token, color, fmt, args...);
    if (font) ImGui::PopFont();
}""",
    "stable numerical text layout")

change("hud_elements.cpp",
    """                HUDElements.TextColored(ClawColorForToken(1, color),
                    "%.0f", HUDElements.sw_stats->fps);""",
    """                ClawStableText(1, ClawColorForToken(1, color),
                    "%.0f", HUDElements.sw_stats->fps);""",
    "scaled FPS uses the same fixed numeric slot")

change("hud_elements.cpp",
    """        HUDElements.TextColored(color, "%s", text);
        ImGui::PopFont();
        return;""",
    """        ClawStableText(1, color, "%s", text);
        ImGui::PopFont();
        return;""",
    "bold FPS uses the same fixed numeric slot")

change("overlay.cpp",
    """   float claw_strip_right = 0.0f;
   ImGuiTableFlags table_flags = ImGuiTableFlags_NoClip;""",
    """   float claw_strip_right = 0.0f;
   extern float claw_fixed_slot_right;
   claw_fixed_slot_right = 0.0f;
   ImGuiTableFlags table_flags = ImGuiTableFlags_NoClip;""",
    "reset slot extent per rendered HUD frame")

change("overlay.cpp",
    """                  if (right > claw_strip_right) claw_strip_right = right;
               }
            }
            HUDElements.place += 1;""",
    """                  if (right > claw_strip_right) claw_strip_right = right;
               }
               // ImGui group's invisible reserved portion is missing from the
               // vertex buffer, but must count when centering the full strip.
               const float fixed_right = claw_fixed_slot_right - window_left;
               if (fixed_right > claw_strip_right) claw_strip_right = fixed_right;
            }
            HUDElements.place += 1;""",
    "include reserved invisible slot widths in automatic centering")

print("Stable numerical slots added to the native single-line HUD")
