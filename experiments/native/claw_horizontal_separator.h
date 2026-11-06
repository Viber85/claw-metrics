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
