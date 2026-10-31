#!/usr/bin/env python3
"""FPS-only native font scale and measured-width centering for our MangoHud 0.8.1."""
from pathlib import Path
import sys

root=Path(sys.argv[1] if len(sys.argv)>1 else "src")
def change(file,old,new):
    path=root/file
    s=path.read_text()
    if s.count(old)!=1:
        raise RuntimeError(f"{file}: expected one marker, got {s.count(old)}: {old[:90]!r}")
    path.write_text(s.replace(old,new,1))

change("overlay_params.h",
    "   OVERLAY_PARAM_CUSTOM(claw_color_map)               \\",
    "   OVERLAY_PARAM_CUSTOM(claw_color_map)               \\\n"
    "   OVERLAY_PARAM_CUSTOM(claw_fps_scale)               \\\n"
    "   OVERLAY_PARAM_CUSTOM(claw_center_horizontal)       \\")
change("overlay_params.h",
    "   std::string claw_weight_map, claw_color_map;",
    "   std::string claw_weight_map, claw_color_map;\n"
    "   int claw_fps_scale = 100;\n"
    "   bool claw_center_horizontal = false;")
change("overlay_params.cpp",
    "#define parse_claw_color_map(s) parse_str(s)",
    "#define parse_claw_color_map(s) parse_str(s)\n"
    "#define parse_claw_fps_scale(s) parse_unsigned(s)\n"
    "#define parse_claw_center_horizontal(s) parse_unsigned(s) != 0")
change("font.cpp",
    "ImFont* claw_metric_semibold = nullptr;",
    """ImFont* claw_metric_semibold = nullptr;
ImFont* claw_fps_default = nullptr;
ImFont* claw_fps_light = nullptr;
ImFont* claw_fps_regular = nullptr;
ImFont* claw_fps_semibold = nullptr;
ImFont* claw_fps_bold = nullptr;""")
change("font.cpp",
    "   claw_metric_semibold = nullptr;",
    """   claw_metric_semibold = nullptr;
   claw_fps_default = nullptr;
   claw_fps_light = nullptr;
   claw_fps_regular = nullptr;
   claw_fps_semibold = nullptr;
   claw_fps_bold = nullptr;""")
change("font.cpp","   font_atlas->Build();\n}",
    """   // Separate FPS fonts use the same atlas so ImGui reserves proper width.
   if (params.claw_fps_scale > 100 && params.claw_fps_scale <= 200) {
      const float fps_size = font_size * params.claw_fps_scale / 100.0f;
      auto add_fps = [&](const std::string& path) -> ImFont* {
         if (path.empty() || !file_exists(path)) return nullptr;
         return font_atlas->AddFontFromFileTTF(path.c_str(), fps_size, nullptr, default_range);
      };
      claw_fps_default = add_fps(params.font_file);
      claw_fps_light = add_fps(params.claw_light_font_file);
      claw_fps_regular = add_fps(params.claw_regular_font_file);
      claw_fps_semibold = add_fps(params.claw_semibold_font_file);
      claw_fps_bold = add_fps(params.claw_bold_font_file);
   }
   font_atlas->Build();
}""")
change("hud_elements.cpp",
    "extern ImFont* claw_metric_semibold;\n\nstatic ImFont* ClawFontForToken",
    """extern ImFont* claw_metric_semibold;
extern ImFont* claw_fps_default;
extern ImFont* claw_fps_light;
extern ImFont* claw_fps_regular;
extern ImFont* claw_fps_semibold;
extern ImFont* claw_fps_bold;

static ImFont* ClawFpsFontForToken() {
    if (!HUDElements.params || HUDElements.params->claw_fps_scale <= 100)
        return nullptr;
    const auto& map = HUDElements.params->claw_weight_map;
    if (map.size() > 1) {
        switch (map[1]) {
            case '1': return claw_fps_light;
            case '2': return claw_fps_regular;
            case '3': return claw_fps_semibold;
            case '4': return claw_fps_bold;
            default: break;
        }
    }
    return HUDElements.params->claw_fps_bold && claw_fps_bold ?
        claw_fps_bold : claw_fps_default;
}

static ImFont* ClawFontForToken""")
change("hud_elements.cpp",
    'if (ClawFontForToken(1)) {',
    """if (ClawFpsFontForToken()) {
                ImGui::PushFont(ClawFpsFontForToken());
                HUDElements.TextColored(ClawColorForToken(1, color),
                    "%.0f", HUDElements.sw_stats->fps);
                ImGui::PopFont();
            } else if (ClawFontForToken(1)) {""")
change("overlay.cpp",
    "   ImGui::SetNextWindowSize(window_size, ImGuiCond_Always);\n   switch (params.position) {",
    """   ImGui::SetNextWindowSize(window_size, ImGuiCond_Always);
   if (params.claw_center_horizontal &&
       params.enabled[OVERLAY_PARAM_ENABLED_horizontal] &&
       params.position == LAYER_POSITION_TOP_LEFT) {
       // Previous frame's measured strip width, not full screen width.
       const float center_x = std::max(0.0f,
           (ImGui::GetIO().DisplaySize.x - window_size.x) * 0.5f);
       data.main_window_pos = ImVec2(center_x, margin + params.offset_y);
       ImGui::SetNextWindowPos(data.main_window_pos, ImGuiCond_Always);
       return;
   }
   switch (params.position) {""")
print("Native FPS scaling and centered HUD installed")
