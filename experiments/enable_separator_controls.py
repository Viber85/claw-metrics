"""Wire Classic separator settings into the pinned MangoHud source."""
import sys
from pathlib import Path

root = Path(sys.argv[1])


def replace(source, old, new):
    if source.count(old) != 1:
        raise SystemExit(f"Expected one MangoHud anchor: {old!r}")
    return source.replace(old, new, 1)


params = root / "overlay_params.h"
source = params.read_text()
fields = ("orientation", "length", "rounding", "opacity")
marker = next(line for line in source.splitlines(keepends=True) if
              "OVERLAY_PARAM_CUSTOM(claw_separator_thickness)" in line)
source = replace(source, marker, marker + "".join(
    marker.replace("thickness", field) for field in fields))
marker = "   float claw_separator_height, claw_separator_thickness;\n"
params.write_text(replace(source, marker, marker +
    "   unsigned claw_separator_orientation;\n"
    "   float claw_separator_length, claw_separator_rounding, claw_separator_opacity;\n"))

config = root / "overlay_params.cpp"
source = config.read_text()
marker = "#define parse_claw_separator_thickness(s) parse_float(s)\n"
source = replace(source, marker, marker +
    "#define parse_claw_separator_orientation(s) parse_unsigned(s)\n" +
    "".join(f"#define parse_claw_separator_{field}(s) parse_float(s)\n" for field in fields[1:]))
marker = "   params->claw_separator_thickness = 2.0f;\n"
config.write_text(replace(source, marker, marker +
    "   params->claw_separator_orientation = 0;\n"
    "   params->claw_separator_length = 0.0f;\n"
    "   params->claw_separator_rounding = 0.0f;\n"
    "   params->claw_separator_opacity = 100.0f;\n"))

overlay = root / "overlay.cpp"
source = overlay.read_text()
start = source.index("void horizontal_separator(struct overlay_params& params) {")
end = source.index("\n}\n", start) + len("\n}")
source = source[:start] + """static float ClawClassicSeparator(const overlay_params& params, bool strip) {
    using namespace claw_horizontal_separator;
    if (params.claw_separator_orientation == Off) return 0.f;

    const ImVec2 window = ImGui::GetWindowPos();
    const ImVec2 padding = ImGui::GetStyle().WindowPadding;
    const float content_width = ImMax(0.f, ImGui::GetWindowSize().x - 2.f * padding.x);
    const ImVec2 dimensions = size(strip, params.claw_separator_orientation,
        params.claw_separator_length, params.claw_separator_thickness,
        params.claw_separator_height, params.font_size, content_width);

    if (strip) {
        ImGui::SameLine();
        ImGui::Spacing();
        ImGui::SameLine();
    } else {
        ImGui::TableNextRow();
        ImGui::TableSetColumnIndex(0);
    }
    ImVec2 pos = ImGui::GetCursorScreenPos();
    if (strip) {
        // Use one shared Y coordinate for the whole strip, independent of the
        // preceding metric's font or graph height.
        pos.y = window.y + padding.y + ImMax(0.f, (params.font_size - dimensions.y) * .5f);
        ImGui::Dummy(dimensions);
        ImGui::SameLine();
        ImGui::Spacing();
    } else {
        pos.x = window.x + padding.x + (content_width - dimensions.x) * .5f;
        ImGui::Dummy(ImVec2(0.f, dimensions.y));
    }
    draw(*ImGui::GetWindowDrawList(), pos, dimensions, params.horizontal_separator_color,
         params.claw_separator_rounding, params.claw_separator_opacity);
    return pos.x + dimensions.x - window.x;
}""" + source[end:]

source = replace(source,
    """            if(!HUDElements.ordered_functions.empty() && params.enabled[OVERLAY_PARAM_ENABLED_horizontal] && HUDElements.ordered_functions.size() != (size_t)HUDElements.place)
               horizontal_separator(params);""",
    """            if (HUDElements.ordered_functions.size() != (size_t)HUDElements.place) {
               const bool strip = params.enabled[OVERLAY_PARAM_ENABLED_horizontal];
               if (strip || claw_vertical_stack) {
                  const float right = ClawClassicSeparator(params, strip);
                  if (strip && right > claw_strip_right) claw_strip_right = right;
               }
            }""")
source = replace(source, """   if (claw_vertical_stack)
       table_flags |= ImGuiTableFlags_BordersInnerH;
""", "")
source = replace(source, """       if (claw_vertical_stack) ImGui::PushStyleColor(ImGuiCol_TableBorderLight, ImVec4(0.44f,0.58f,0.70f,0.055f));
""", "")
source = replace(source, """       if (claw_vertical_stack) ImGui::PopStyleColor();
""", "")
overlay.write_text(source)
