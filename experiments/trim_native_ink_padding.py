#!/usr/bin/env python3
"""Size the native horizontal HUD against actual ImGui ink, not font line boxes.

A large FPS font has ascender/descent space that is *not* user window padding.
At 200% FPS, the default ImGui table row height puts empty space above
visible glyphs even when WindowPadding.y and CellPadding.y are zero.

Only the isolated Claw horizontal overlay is affected. Measure the finished
table's actual vertices AFTER EndTable merges ImGui drawing channels, then
compensate for the transparent top region and choose a window height ending
at the last drawn pixel plus the user-controlled padding. Never rewrite
frame-time sampling or font glyphs.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv)>1 else "src")
path = root / "overlay.cpp"
source = path.read_text()

def replace_once(old, new, label):
    global source
    n = source.count(old)
    if n != 1:
        raise RuntimeError(f"{label}: expected one native anchor, found {n}")
    source = source.replace(old, new, 1)

replace_once(
    '#include <algorithm>',
    '#include <algorithm>\n#include <cmath>\n#include <limits>',
    "finite native ink bounds"
)

replace_once(
    'ImGui::Begin("Main", &gui_open, ImGuiWindowFlags_NoDecoration);',
    """       // The pre-existing table height includes unused font ascender space.
       // Do not use it as the user-visible HUD background inset.
       const bool claw_ink_trim = params.enabled[OVERLAY_PARAM_ENABLED_horizontal] &&
           params.claw_inline_metrics && !params.enabled[OVERLAY_PARAM_ENABLED_fps_only];
       static float claw_ink_trim_top = 0.0f;
       static int claw_ink_font_key = -1;
       const int claw_current_font_key =
           int(params.font_size * 10.0f) * 1000 + params.claw_fps_scale;
       if (claw_current_font_key != claw_ink_font_key) {
           claw_ink_font_key = claw_current_font_key;
           claw_ink_trim_top = 0.0f;
       }
       if (claw_ink_trim)
           ImGui::PushStyleVar(ImGuiStyleVar_WindowMinSize, ImVec2(1.0f, 1.0f));
       ImGui::Begin("Main", &gui_open, ImGuiWindowFlags_NoDecoration);
       // Begin() already submitted the original window background. Capture
       // vertices starting HERE, excluding that background rectangle.
       ImDrawList* claw_ink_draw = ImGui::GetWindowDrawList();
       const int claw_ink_start = claw_ink_draw->VtxBuffer.Size;
       if (claw_ink_trim && claw_ink_trim_top > 0.0f)
           ImGui::SetCursorPosY(ImGui::GetCursorPosY() - claw_ink_trim_top);
       float claw_ink_bottom = 0.0f;
       bool claw_has_ink = false;""",
    "tracked native horizontal ink bounds"
)

replace_once(
    "ImGui::EndTable();",
    """ImGui::EndTable();
          if (claw_ink_trim) {
              // The table splitter is merged by EndTable; include FPS glyphs,
              // all other metrics, graph strokes and separator line pixels.
              const float window_y = ImGui::GetWindowPos().y;
              float top = std::numeric_limits<float>::infinity();
              float bottom = -std::numeric_limits<float>::infinity();
              for (int vi = claw_ink_start; vi < claw_ink_draw->VtxBuffer.Size; ++vi) {
                  const float y = claw_ink_draw->VtxBuffer[vi].pos.y - window_y;
                  if (!std::isfinite(y)) continue;
                  if (y < top) top = y;
                  if (y > bottom) bottom = y;
              }
              if (std::isfinite(top) && std::isfinite(bottom) && bottom > top) {
                  const float pad = ImMax(0.0f,
                      params.cellpadding_y * real_font_size.y);
                  // Incremental compensation avoids jumping on the first frame
                  // and stabilizes once the drawn top equals the slider inset.
                  const float correction = ImClamp(top - pad,
                      -float(params.font_size), float(params.font_size));
                  claw_ink_trim_top = ImClamp(claw_ink_trim_top + correction,
                      0.0f, ImMax(1.0f, float(params.font_size) * 2.0f));
                  claw_ink_bottom = bottom;
                  claw_has_ink = true;
              }
          }
          }""",
    "measure final draw vertices after table channel merge"
)

replace_once(
    """       window_size = ImVec2(window_size.x,
           ImMax(1.0f, ImGui::GetCursorPosY() + claw_bottom_padding));
       ImGui::End();""",
    """       window_size = ImVec2(window_size.x,
           ImMax(1.0f, ImGui::GetCursorPosY() + claw_bottom_padding));
       if (claw_ink_trim && claw_has_ink) {
           // Height follows actual visible ink rather than FPS font line box.
           // Keep symmetric user padding (including exactly zero).
           window_size.y = ImClamp(claw_ink_bottom + claw_bottom_padding,
               1.0f, ImMax(1.0f, ImGui::GetIO().DisplaySize.y));
       }
       ImGui::End();
       if (claw_ink_trim) ImGui::PopStyleVar();""",
    "finish measured HUD height without trailing blank space"
)

path.write_text(source)
print("Native horizontal HUD tracks visible ink at every FPS font scale")
