#pragma once
#include "claw_framegen.h"
#include "imgui.h"
#include <algorithm>
#include <cstdio>

namespace claw_framegen {
inline void paint_graph(ImDrawList* draw, ImVec2 origin, ImVec2 size,
                        const Snapshot& frames, ImU32 output_color, ImU32 game_color) {
    if (size.x < 1 || size.y < 1) return;
    const ImVec2 end(origin.x + size.x, origin.y + size.y);
    draw->PushClipRect(origin, end, true);
    const float legend = std::min(12.f, size.y * .6f);
    const float label_y = origin.y;
    draw->AddText(ImGui::GetFont(), legend, ImVec2(origin.x + 2, label_y), output_color, "Output");
    if (!frames.game_graph.empty())
        draw->AddText(ImGui::GetFont(), legend, ImVec2(origin.x + 5 + 3.4f * legend, label_y), game_color, "Game");

    float ceiling = 16.7f;
    for (const auto& point : frames.output_graph) ceiling = std::max(ceiling, point.ms);
    for (const auto& point : frames.game_graph) ceiling = std::max(ceiling, point.ms);
    const auto plot = [&](const std::vector<Point>& series, ImU32 color) {
        std::vector<ImVec2> vertices;
        vertices.reserve(series.size());
        for (const auto& point : series) {
            const float age = float(frames.at - point.at) / history;
            vertices.emplace_back(end.x - size.x * age, end.y - (size.y - legend) * point.ms / ceiling);
        }
        if (vertices.size() > 1) draw->AddPolyline(vertices.data(), int(vertices.size()), color, 0, 1.5f);
    };
    plot(frames.output_graph, output_color);
    plot(frames.game_graph, game_color);
    draw->PopClipRect();
    if (std::getenv("CLAW_METRICS_VERIFY") && ImGui::GetFrameCount() % 60 == 0) {
        std::fprintf(stderr, "CLAW_FRAMEGEN_GRAPH game=%.1f fg=%.1f output=%.1f game_points=%zu output_points=%zu\n",
                     frames.game_fps, frames.generated_fps, frames.output_fps,
                     frames.game_graph.size(), frames.output_graph.size());
    }
}
}
