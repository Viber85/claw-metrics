#!/usr/bin/env python3
"""Apply independent Claw Metrics token colors/font weights after pinned MangoHud patches.

This script intentionally fails on source drift instead of silently installing
non-functional UI controls. It operates only on a staged build tree.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else "native-source/src")
assert root.is_dir(), root

def replace_once(src, old, new, name):
    count = src.count(old)
    if count != 1:
        raise RuntimeError(f"{name}: expected 1 match, found {count}: {old[:90]!r}")
    return src.replace(old, new, 1)

params_h = root / "overlay_params.h"
s = params_h.read_text()
s = replace_once(s, "   OVERLAY_PARAM_CUSTOM(claw_bold_font_file)          \\",
"""   OVERLAY_PARAM_CUSTOM(claw_bold_font_file)          \\
   OVERLAY_PARAM_CUSTOM(claw_light_font_file)         \\
   OVERLAY_PARAM_CUSTOM(claw_regular_font_file)       \\
   OVERLAY_PARAM_CUSTOM(claw_semibold_font_file)      \\
   OVERLAY_PARAM_CUSTOM(claw_weight_map)              \\
   OVERLAY_PARAM_CUSTOM(claw_color_map)               \\""", "params registration")
s = replace_once(s,
    "   std::string font_file, font_file_text, claw_bold_font_file;",
    """   std::string font_file, font_file_text, claw_bold_font_file;
   std::string claw_light_font_file, claw_regular_font_file, claw_semibold_font_file;
   std::string claw_weight_map, claw_color_map;""",
    "params fields")
params_h.write_text(s)

params_cpp = root / "overlay_params.cpp"
s = params_cpp.read_text()
s = replace_once(s, "#define parse_claw_bold_font_file(s) parse_path(s)",
"""#define parse_claw_bold_font_file(s) parse_path(s)
#define parse_claw_light_font_file(s) parse_path(s)
#define parse_claw_regular_font_file(s) parse_path(s)
#define parse_claw_semibold_font_file(s) parse_path(s)
#define parse_claw_weight_map(s) parse_str(s)
#define parse_claw_color_map(s) parse_str(s)""", "parser registration")
params_cpp.write_text(s)

font_cpp = root / "font.cpp"
s = font_cpp.read_text()
s = replace_once(s, "ImFont* claw_bold_fps_font = nullptr;",
"""ImFont* claw_bold_fps_font = nullptr;
ImFont* claw_metric_light = nullptr;
ImFont* claw_metric_regular = nullptr;
ImFont* claw_metric_semibold = nullptr;""", "font globals")
s = replace_once(s, "   claw_bold_fps_font = nullptr;",
"""   claw_bold_fps_font = nullptr;
   claw_metric_light = nullptr;
   claw_metric_regular = nullptr;
   claw_metric_semibold = nullptr;""", "clear atlas")
s = replace_once(s,
"""   font_atlas->Build();
}""",
"""   if (!params.claw_light_font_file.empty() && file_exists(params.claw_light_font_file))
      claw_metric_light = font_atlas->AddFontFromFileTTF(
         params.claw_light_font_file.c_str(), font_size, nullptr, default_range);
   if (!params.claw_regular_font_file.empty() && file_exists(params.claw_regular_font_file))
      claw_metric_regular = font_atlas->AddFontFromFileTTF(
         params.claw_regular_font_file.c_str(), font_size, nullptr, default_range);
   if (!params.claw_semibold_font_file.empty() && file_exists(params.claw_semibold_font_file))
      claw_metric_semibold = font_atlas->AddFontFromFileTTF(
         params.claw_semibold_font_file.c_str(), font_size, nullptr, default_range);
   font_atlas->Build();
}""", "font atlas")
font_cpp.write_text(s)

hud = root / "hud_elements.cpp"
s = hud.read_text()
helpers = r"""
// Each map position is a stable token id, shared with main.py TOKEN_SLOTS.
// Zero means inherit the original font/color. No new row or table is created.
extern ImFont* claw_bold_fps_font;
extern ImFont* claw_metric_light;
extern ImFont* claw_metric_regular;
extern ImFont* claw_metric_semibold;

static ImFont* ClawFontForToken(int token) {
    if (!HUDElements.params || token < 0)
        return nullptr;
    const auto& m = HUDElements.params->claw_weight_map;
    if (size_t(token) >= m.size())
        return nullptr;
    switch (m[size_t(token)]) {
        case '1': return claw_metric_light;
        case '2': return claw_metric_regular;
        case '3': return claw_metric_semibold;
        case '4': return claw_bold_fps_font;
        default: return nullptr;
    }
}

static ImVec4 ClawColorForToken(int token, ImVec4 current) {
    if (!HUDElements.params || token < 0)
        return current;
    const auto& s = HUDElements.params->claw_color_map;
    const size_t start = size_t(token) * 7;
    if (start + 6 > s.size() || s[start] == '-')
        return current;
    unsigned rgb = 0;
    for (size_t i = 0; i < 6; ++i) {
        char c = s[start + i];
        const int nibble = c >= '0' && c <= '9' ? c - '0'
            : c >= 'A' && c <= 'F' ? c - 'A' + 10 : -1;
        if (nibble < 0) return current;
        rgb = (rgb << 4) | unsigned(nibble);
    }
    return ImVec4(((rgb >> 16) & 255) / 255.f,
                  ((rgb >> 8) & 255) / 255.f,
                  (rgb & 255) / 255.f, current.w);
}

template<typename... Args>
static void ClawText(int token, ImVec4 color, const char* fmt, Args... args) {
    color = ClawColorForToken(token, color);
    ImFont* font = ClawFontForToken(token);
    if (font) ImGui::PushFont(font);
    HUDElements.TextColored(color, fmt, args...);
    if (font) ImGui::PopFont();
}
"""
s = replace_once(s, "static void ClawMetricGap() {", helpers + "\nstatic void ClawMetricGap() {", "inline helper")

# Only alter our custom one-line rendering branches, never upstream fallback.
def update_inline(func, changes):
    global s
    start = s.index("void HudElements::" + func + "(){")
    # The custom rendering branch ends with return; immediately before fallback.
    marker = "\n            return;" if func in ("fps", "cpu_stats", "gpu_stats") else "\n        return;"
    end = s.index(marker, start) + len(marker)
    original = s[start:end]
    chunk = original
    for old, new in changes:
        chunk = replace_once(chunk, old, new, func)
    s = s[:start] + chunk + s[end:]


update_inline("fps", [
    ('HUDElements.TextColored(HUDElements.colors.engine, "%s", label);',
     'ClawText(0, HUDElements.colors.engine, "%s", label);'),
    ('if (HUDElements.params->claw_fps_bold) {',
     'if (ClawFontForToken(1)) {\n'
     '                ClawText(1, color, "%.0f", HUDElements.sw_stats->fps);\n'
     '            } else if (HUDElements.params->claw_fps_bold) {'),
    ('ClawBoldFpsNumber(color, ImGui::CalcTextSize(fps_string).x, HUDElements.sw_stats->fps);',
     'ImVec4 selected_color = ClawColorForToken(1, color);\\n'
     '                ClawBoldFpsNumber(selected_color, ImGui::CalcTextSize(fps_string).x, HUDElements.sw_stats->fps);'),
    ('HUDElements.TextColored(color, "%.0f", HUDElements.sw_stats->fps);',
     'ClawText(1, color, "%.0f", HUDElements.sw_stats->fps);'),
    ('HUDElements.TextColored(HUDElements.colors.text, "%.1f",',
     'ClawText(2, HUDElements.colors.text, "%.1f",'),
    ('HUDElements.TextColored(HUDElements.colors.text, "ms");',
     'ClawText(2, HUDElements.colors.text, "ms");'),
])
update_inline("cpu_stats", [
    ('HUDElements.TextColored(HUDElements.colors.cpu, "%s", label);',
     'ClawText(3, HUDElements.colors.cpu, "%s", label);'),
    ('HUDElements.TextColored(text_color, "%d%%", int(cpuStats.GetCPUDataTotal().percent));',
     'ClawText(4, text_color, "%d%%", int(cpuStats.GetCPUDataTotal().percent));'),
    ('HUDElements.TextColored(text_color, "%i°%c", temperature,',
     'ClawText(5, text_color, "%i°%c", temperature,'),
    ('HUDElements.TextColored(text_color, "%i", cpuStats.GetCPUDataTotal().cpu_mhz);',
     'ClawText(6, text_color, "%i", cpuStats.GetCPUDataTotal().cpu_mhz);'),
    ('HUDElements.TextColored(text_color, "MHz");',
     'ClawText(6, text_color, "MHz");'),
    ('HUDElements.TextColored(text_color, "%.1f", cpuStats.GetCPUDataTotal().power);',
     'ClawText(7, text_color, "%.1f", cpuStats.GetCPUDataTotal().power);'),
    ('HUDElements.TextColored(text_color, "W");',
     'ClawText(7, text_color, "W");'),
])
update_inline("gpu_stats", [
    ('HUDElements.TextColored(HUDElements.colors.gpu, "%s", gpu->gpu_text().c_str());',
     'ClawText(8, HUDElements.colors.gpu, "%s", gpu->gpu_text().c_str());'),
    ('HUDElements.TextColored(text_color, "%i%%", gpu->metrics.load);',
     'ClawText(9, text_color, "%i%%", gpu->metrics.load);'),
    ('HUDElements.TextColored(text_color, "%i°%c", temperature,\n'
     "                        HUDElements.params->enabled[OVERLAY_PARAM_ENABLED_temp_fahrenheit] ? 'F' : 'C');",
     'ClawText(10, text_color, "%i°%c", temperature,\n'
     "                        HUDElements.params->enabled[OVERLAY_PARAM_ENABLED_temp_fahrenheit] ? 'F' : 'C');"),
    ('HUDElements.TextColored(text_color, "%i°%c Jnc", temperature,',
     'ClawText(13, text_color, "%i°%c Jnc", temperature,'),
    ('HUDElements.TextColored(text_color, "%i RPM", gpu->metrics.fan_speed);',
     'ClawText(14, text_color, "%i RPM", gpu->metrics.fan_speed);'),
    ('HUDElements.TextColored(text_color, "%i%% FAN", gpu->metrics.fan_speed);',
     'ClawText(14, text_color, "%i%% FAN", gpu->metrics.fan_speed);'),
    ('HUDElements.TextColored(text_color, "%i", gpu->metrics.CoreClock);',
     'ClawText(11, text_color, "%i", gpu->metrics.CoreClock);'),
    ('HUDElements.TextColored(text_color, "MHz");',
     'ClawText(11, text_color, "MHz");'),
    ('HUDElements.TextColored(text_color, "%.1f", gpu->metrics.powerUsage);',
     'ClawText(12, text_color, "%.1f", gpu->metrics.powerUsage);'),
    ('HUDElements.TextColored(text_color, "W");',
     'ClawText(12, text_color, "W");'),
    ('HUDElements.TextColored(text_color, "%i mV", gpu->metrics.voltage);',
     'ClawText(15, text_color, "%i mV", gpu->metrics.voltage);'),
])
update_inline("ram", [
    ('HUDElements.TextColored(HUDElements.colors.ram, "RAM");',
     'ClawText(16, HUDElements.colors.ram, "RAM");'),
    ('HUDElements.TextColored(HUDElements.colors.text, "%.1f", memused);',
     'ClawText(17, HUDElements.colors.text, "%.1f", memused);'),
    ('HUDElements.TextColored(HUDElements.colors.text, "GiB");',
     'ClawText(17, HUDElements.colors.text, "GiB");'),
    ('HUDElements.TextColored(HUDElements.colors.text, "%.1f", swapused);',
     'ClawText(17, HUDElements.colors.text, "%.1f", swapused);'),
    ('HUDElements.TextColored(HUDElements.colors.text, "GiB swap");',
     'ClawText(17, HUDElements.colors.text, "GiB swap");'),
])
update_inline("vram", [
    ('HUDElements.TextColored(HUDElements.colors.vram, "%s", gpu->vram_text().c_str());',
     'ClawText(18, HUDElements.colors.vram, "%s", gpu->vram_text().c_str());'),
    ('HUDElements.TextColored(HUDElements.colors.text, "%.1f", used);',
     'ClawText(19, HUDElements.colors.text, "%.1f", used);'),
    ('HUDElements.TextColored(HUDElements.colors.text, "GiB");',
     'ClawText(19, HUDElements.colors.text, "GiB");'),
    ('HUDElements.TextColored(HUDElements.colors.text, "%i°%c", temp,',
     'ClawText(20, HUDElements.colors.text, "%i°%c", temp,'),
    ('HUDElements.TextColored(HUDElements.colors.text, "%i", gpu->metrics.MemClock);',
     'ClawText(21, HUDElements.colors.text, "%i", gpu->metrics.MemClock);'),
    ('HUDElements.TextColored(HUDElements.colors.text, "MHz");',
     'ClawText(21, HUDElements.colors.text, "MHz");'),
])
update_inline("battery", [
    ('HUDElements.TextColored(HUDElements.colors.battery, "BATT");',
     'ClawText(22, HUDElements.colors.battery, "BATT");'),
    ('HUDElements.TextColored(HUDElements.colors.text, "%s", icon);',
     'ClawText(23, HUDElements.colors.text, "%s", icon);'),
    ('HUDElements.TextColored(HUDElements.colors.text, "%.0f%%", Battery_Stats.current_percent);',
     'ClawText(23, HUDElements.colors.text, "%.0f%%", Battery_Stats.current_percent);'),
    ('HUDElements.TextColored(HUDElements.colors.text, "%.1f", Battery_Stats.current_watt);',
     'ClawText(25, HUDElements.colors.text, "%.1f", Battery_Stats.current_watt);'),
    ('HUDElements.TextColored(HUDElements.colors.text, "W");',
     'ClawText(25, HUDElements.colors.text, "W");'),
    ('HUDElements.TextColored(HUDElements.colors.text, "%02d:%02d",',
     'ClawText(24, HUDElements.colors.text, "%02d:%02d",'),
    ('HUDElements.TextColored(HUDElements.colors.text, "%s", ICON_FK_PLUG);',
     'ClawText(23, HUDElements.colors.text, "%s", ICON_FK_PLUG);'),
])
# Independent clock font and color, while preserving the fallback layout.
s = replace_once(s,
    '            ImguiNextColumnFirstItem();\n'
    '            HUDElements.TextColored(HUDElements.colors.text, "%s", HUDElements.sw_stats->time.c_str());',
    '            ImguiNextColumnFirstItem();\n'
    '            ClawText(26, HUDElements.colors.text, "%s", HUDElements.sw_stats->time.c_str());',
    "clock value in one-row layout")

hud.write_text(s)
print("Applied per-token font/color renderer:", root)
