#include "experiments/native/claw_framegen.h"
#include <cassert>
#include <cmath>

using namespace claw_framegen;

static void append(Wire& wire, std::uint64_t at, Kind kind) {
    wire.marker = magic;
    auto& event = wire.events[wire.last % capacity];
    event = {at, ++wire.last, kind, 0};
}

int main() {
    Meter meter;
    Wire wire{};
    constexpr std::uint64_t start = 10 * second;
    constexpr std::uint64_t step = 10000000;
    auto at = start;
    for (int i = 0; i < 450; ++i, at += step) {
        meter.presented(at);
        append(wire, at - 1000, i % 2 == 0 ? game : generated);
        if (i % 5 == 0) meter.ingest(wire, at);
    }
    meter.ingest(wire, at);
    const auto initial = meter.snapshot(at, true);
    assert(std::abs(initial.game_fps - 50) < 1);
    assert(std::abs(initial.generated_fps - 50) < 1);
    assert(std::abs(initial.output_fps - 100) < 1);
    assert(initial.game_graph.size() > 50 && initial.output_graph.size() > 100);
    assert(std::abs(initial.game_graph.back().ms - 20) < .01);
    assert(std::abs(initial.output_graph.back().ms - 10) < .01);
    assert(initial.game_graph.back().at < initial.output_graph.back().at);

    for (int i = 0; i < 70; ++i, at += step) meter.presented(at);
    const auto stale_data = meter.snapshot(at, true);
    assert(stale_data.game_fps < 0 && stale_data.generated_fps < 0);
    assert(stale_data.game_graph.empty() && stale_data.output_fps > 99);
    for (int i = 0; i < 110; ++i, at += step) {
        meter.presented(at);
        append(wire, at - 1000, game);
        meter.ingest(wire, at);
    }
    const auto disabled = meter.snapshot(at, false);
    assert(disabled.game_fps > 99 && disabled.generated_fps == 0);
    assert(disabled.game_graph.empty() && disabled.output_graph.empty());
    wire.guard = 1;
    for (int i = 0; i < 60; ++i, at += step) {
        meter.presented(at);
        append(wire, at - 1000, generated);
    }
    meter.ingest(wire, at);
    assert(meter.snapshot(at, false).generated_fps < 0);
    assert(meter.snapshot(at + 2 * second, true).output_graph.empty());
}
