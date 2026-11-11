#pragma once
#include "imgui.h"
#include <algorithm>

namespace claw_horizontal_separator {
struct Line { ImVec2 start, end; float thickness; };

// Horizontal MangoHud uses one window for the complete row. Item cursor Y
// moves when a preceding reading uses a smaller font or a taller graph, so
// anchor every divider to the same window content origin instead.
inline Line geometry(ImVec2 window, float padding_y, float font_size,
                     float cursor_x, float height_percent, float thickness) {
    const float height = font_size * .85f * std::max(50.f, std::min(150.f, height_percent)) / 100.f;
    const float center = window.y + padding_y + font_size * .5f;
    const float x = cursor_x - 5.f;
    return {{x, center - height * .5f}, {x, center + height * .5f},
            std::max(1.f, std::min(6.f, thickness))};
}
}

namespace claw_horizontal_separator {
enum Orientation { Auto, Horizontal, Vertical, Off };

inline ImVec2 size(bool strip, unsigned orientation, float length, float thickness,
                   float height_percent, float font_size, float available_width) {
    if (orientation == Off) return {0.f, 0.f};
    const bool vertical = orientation == Vertical || (orientation != Horizontal && strip);
    const float automatic = vertical
        ? font_size * .85f * std::max(50.f, std::min(150.f, height_percent)) / 100.f
        : (strip ? font_size * .85f : available_width);
    length = std::max(0.f, std::min(1000.f, length));
    length = length > 0.f ? length : automatic;
    if (!strip && !vertical) length = std::min(length, available_width);
    thickness = std::max(1.f, std::min(20.f, thickness));
    return vertical ? ImVec2(thickness, length) : ImVec2(length, thickness);
}

inline void draw(ImDrawList& list, ImVec2 pos, ImVec2 size,
                 unsigned rgb, float radius, float opacity) {
    const int alpha = int(std::max(0.f, std::min(100.f, opacity)) * 255.f / 100.f + .5f);
    if (!alpha || size.x <= 0.f || size.y <= 0.f) return;
    const auto color = IM_COL32((rgb >> 16) & 0xff, (rgb >> 8) & 0xff, rgb & 0xff, alpha);
    list.AddRectFilled(pos, ImVec2(pos.x + size.x, pos.y + size.y), color,
                       std::max(0.f, std::min(radius, std::min(size.x, size.y) * .5f)));
}
}
