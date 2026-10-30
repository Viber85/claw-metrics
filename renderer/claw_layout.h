// Claw Metrics layout helpers. Shared by the native fork and headless tests.
#pragma once
#include <algorithm>
#include <cmath>
namespace claw {
inline float fit_scale(float natural_body, float screen, float padding_x) {
    if (natural_body <= 0.0f) return 1.0f;
    return std::max(0.10f, std::min(1.0f, (screen - 16.0f - 2.0f * padding_x) / natural_body));
}
inline float row_x(float screen, float width, float offset, bool centered) {
    return (centered ? (screen - width) * 0.5f : 0.0f) + offset;
}
inline float line_height(float base, float fps, bool show_fps, float scale) {
    return std::max(base, show_fps ? fps : base) * scale;
}
}
