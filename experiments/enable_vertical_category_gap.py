#!/usr/bin/env python3
"""Increase inter-category vertical table spacing, leaving wrapped lines intact.

Run after enable_vertical_stacked.py. The horizontal renderer is not modified.
"""
from pathlib import Path
import sys

root=Path(sys.argv[1] if len(sys.argv)>1 else "src")
def change(file, old, new):
    path=root/file
    s=path.read_text()
    if s.count(old)!=1:
        raise RuntimeError(f"Vertical category gap: {file} expected one anchor, got {s.count(old)}")
    path.write_text(s.replace(old,new,1))

change("overlay_params.h",
    "   OVERLAY_PARAM_CUSTOM(claw_vertical_graph_height)   \\",
    "   OVERLAY_PARAM_CUSTOM(claw_vertical_graph_height)   \\\n"
    "   OVERLAY_PARAM_CUSTOM(claw_vertical_category_gap)  \\")
change("overlay_params.h",
    "   float claw_vertical_graph_height = 28.0f;",
    "   float claw_vertical_graph_height = 28.0f;\n"
    "   float claw_vertical_category_gap = 6.0f;")
change("overlay_params.cpp",
    "#define parse_claw_vertical_graph_height(s) parse_float(s)",
    "#define parse_claw_vertical_graph_height(s) parse_float(s)\n"
    "#define parse_claw_vertical_category_gap(s) parse_float(s)")
# CellPadding applies above and below a TABLE ROW, including wrapped values
# in its cell. It does not insert a gap between wrap continuation lines.
change("overlay.cpp",
    "if (claw_vertical_stack) ImGui::PushStyleColor(ImGuiCol_TableBorderLight,",
    """if (claw_vertical_stack) {
           const ImGuiStyle& style = ImGui::GetStyle();
           ImGui::PushStyleVar(ImGuiStyleVar_CellPadding,
               ImVec2(style.CellPadding.x, style.CellPadding.y +
                   ImClamp(params.claw_vertical_category_gap, 0.0f, 20.0f) * 0.5f));
       }
       if (claw_vertical_stack) ImGui::PushStyleColor(ImGuiCol_TableBorderLight,""")
change("overlay.cpp",
    "if (claw_vertical_stack) ImGui::PopStyleColor();",
    """if (claw_vertical_stack) ImGui::PopStyleColor();
       if (claw_vertical_stack) ImGui::PopStyleVar();""")
print("Vertical category gap applied with scoped ImGui table padding")
