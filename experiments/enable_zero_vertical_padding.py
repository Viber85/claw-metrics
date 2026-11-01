#!/usr/bin/env python3
"""Move the existing vertical slider from table cell padding to true top/bottom HUD insets.

In MangoHud 0.8.1 the horizontal HUD retained 5 px at the window top/bottom
and an additional fixed 10 px at the bottom, independently of cellpadding_y.
The new scheme has zero added vertical padding at slider=0 and matches both
edges at any nonnegative slider value. The original config key is retained.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else "src")

def change(filename, before, after, description):
    path = root / filename
    original = path.read_text()
    count = original.count(before)
    if count != 1:
        raise RuntimeError(f"{description}: expected one anchor, got {count} in {filename}")
    path.write_text(original.replace(before, after, 1))

change(
    "overlay.cpp",
    "ImVec2(params.claw_padding_x,5)",
    "ImVec2(params.claw_padding_x, ImMax(0.0f, params.cellpadding_y * real_font_size.y))",
    "replace fixed 5px window top/bottom inset with slider"
)

change(
    "hud_elements.cpp",
    "style.CellPadding.y = params.cellpadding_y * real_font_size.y;",
    """// Vertical slider applies to the outer HUD window, not each table cell.
    // Otherwise the row introduces hidden padding even when the slider is zero.
    style.CellPadding.y = 0.0f;""",
    "remove independent cell-level vertical padding"
)

change(
    "overlay.cpp",
    "window_size = ImVec2(window_size.x, ImGui::GetCursorPosY() + 10.0f);",
    """// GetCursorPosY already includes the top WindowPadding. Add exactly the
       // matching bottom inset, never the upstream hard-coded extra 10 px.
       const float claw_bottom_padding =
           ImMax(0.0f, params.cellpadding_y * real_font_size.y);
       window_size = ImVec2(window_size.x,
           ImMax(1.0f, ImGui::GetCursorPosY() + claw_bottom_padding));""",
    "replace fixed 10px bottom margin with symmetric user slider"
)

print("Claw vertical slider now controls actual HUD top/bottom insets (0 px supported)")
