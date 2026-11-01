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
    "   OVERLAY_PARAM_CUSTOM(claw_center_horizontal)       \\n" +
    "   OVERLAY_PARAM_CUSTOM(claw_align_right)             \\")
change("overlay_params.h",
    "   std::string claw_weight_map, claw_color_map;",
    "   std::string claw_weight_map, claw_color_map;\n"
    "   int claw_fps_scale = 100;\n"
    "   bool claw_center_horizontal = false;\n" +
    "   bool claw_align_right = false;")
change("overlay_params.cpp",
    "#define parse_claw_color_map(s) parse_str(s)",
    "#define parse_claw_color_map(s) parse_str(s)\n"
    "#define parse_claw_fps_scale(s) parse_unsigned(s)\n"
    "#define parse_claw_center_horizontal(s) parse_unsigned(s) != 0\n" +
    "#define parse_claw_align_right(s) parse_unsigned(s) != 0")
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
    """   // Bake FPS glyphs at 200% once, even if FPS was 100% at game startup.
   // The display percentage is selected at runtime via ImFont::Scale.
   {
      const float fps_size = font_size * 2.0f;
      static const ImWchar claw_fps_digits[] = {
         0x0020, 0x0020, 0x002D, 0x002E, 0x0030, 0x0039, 0
      };
      auto add_fps = [&](const std::string& path) -> ImFont* {
         if (path.empty() || !file_exists(path)) return nullptr;
         return font_atlas->AddFontFromFileTTF(path.c_str(), fps_size,
                                               nullptr, claw_fps_digits);
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
    ImFont* chosen = nullptr;
    const auto& map = HUDElements.params->claw_weight_map;
    if (map.size() > 1) {
        switch (map[1]) {
            case '1': chosen = claw_fps_light; break;
            case '2': chosen = claw_fps_regular; break;
            case '3': chosen = claw_fps_semibold; break;
            case '4': chosen = claw_fps_bold; break;
            default: break;
        }
    }
    if (!chosen)
        chosen = HUDElements.params->claw_fps_bold && claw_fps_bold ?
            claw_fps_bold : claw_fps_default;
    // Dedicated digit font only. Do not scale CPU/GPU labels or any other
    // glyphs. ImGui::PushFont respects Scale for layout and rasterization.
    if (chosen)
        chosen->Scale = ImClamp(float(HUDElements.params->claw_fps_scale) / 200.0f,
                               0.5f, 1.0f);
    return chosen;
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
       // Make the compact window equal to the previous frame's visible HUD.
       // The ImGui host/table width is not a valid measurement.
       const float display_width = ImGui::GetIO().DisplaySize.x;
       const float strip_width = ImClamp(window_size.x, 1.0f, display_width);
       ImGui::SetNextWindowSize(ImVec2(strip_width, window_size.y), ImGuiCond_Always);
       const float center_x = ImMax(0.0f, (display_width - strip_width) * 0.5f);
       data.main_window_pos = ImVec2(center_x, margin + params.offset_y);
       ImGui::SetNextWindowPos(data.main_window_pos, ImGuiCond_Always);
       return;
   }
   switch (params.position) {""")
# Measure actual text/glyph extents, not MangoHud's historical approximation
# based on table_columns * 64. The latter is inaccurate for our inline text.
change("overlay.cpp",
    "   ImGuiTableFlags table_flags = ImGuiTableFlags_NoClip;",
    "   float claw_strip_right = 0.0f;\n"
    "   ImGuiTableFlags table_flags = ImGuiTableFlags_NoClip;")
change("overlay.cpp",
    "            func.run();\n            HUDElements.place += 1;",
    """            ImDrawList* claw_draw = ImGui::GetWindowDrawList();
            const int claw_vertex_start = claw_draw->VtxBuffer.Size;
            func.run();
            if ((params.claw_center_horizontal || params.claw_align_right) &&
                params.enabled[OVERLAY_PARAM_ENABLED_horizontal]) {
               // ImGui::GetItemRectMax may cover the full host table width.
               // Measure actual submitted glyphs, graphs and icon pixels.
               const float window_left = ImGui::GetWindowPos().x;
               for (int vi = claw_vertex_start; vi < claw_draw->VtxBuffer.Size; ++vi) {
                  const float right = claw_draw->VtxBuffer[vi].pos.x - window_left;
                  if (right > claw_strip_right) claw_strip_right = right;
               }
            }
            HUDElements.place += 1;""")
change("overlay.cpp",
    """               float content_width = ImGui::GetContentRegionAvail().x - (params.table_columns * 64);
               window_size = ImVec2(content_width, params.height);""",
    """               float content_width = ImGui::GetContentRegionAvail().x - (params.table_columns * 64);
               if ((params.claw_center_horizontal || params.claw_align_right) &&
                   claw_strip_right > 0.0f) {
                   // Last drawn pixel + side padding (not an ImGui table item).
                   const float strip_width = claw_strip_right +
                       ImMax(0.0f, float(params.claw_padding_x));
                   content_width = ImClamp(strip_width, 1.0f,
                       ImGui::GetIO().DisplaySize.x);
               }
               window_size = ImVec2(content_width, params.height);""")
print("Native FPS scaling and centered HUD installed")
