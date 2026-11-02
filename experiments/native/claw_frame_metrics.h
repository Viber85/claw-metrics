#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <deque>
#include <functional>
#include <vector>

// One accumulator per swapchain, owned and updated by the render thread.
class ClawFrameMetrics {
    struct Sample { uint64_t at; double ms; };
    std::deque<Sample> samples;
    uint64_t last_calculation = 0;
    double total_ms = 0;
public:
    double average = 0;
    double low1 = 0;
    bool low1_ready = false;
    size_t count() const { return samples.size(); }
    void reset() {
        samples.clear(); total_ms = 0; last_calculation = 0;
        average = 0; low1 = 0; low1_ready = false;
    }
    void add(uint64_t at, double ms) {
        if (!std::isfinite(ms) || ms <= 0) return;
        if (!samples.empty() && at < samples.back().at) reset();
        samples.push_back({at, ms}); total_ms += ms;
        while (!samples.empty() && (samples.size() > 30000 || at - samples.front().at > 60000000000ULL)) {
            total_ms -= samples.front().ms; samples.pop_front();
        }
        average = samples.size() * 1000.0 / total_ms;
        low1_ready = samples.size() >= 100;
        if (!low1_ready) { low1 = 0; return; }
        if (last_calculation && at - last_calculation < 500000000ULL) return;
        last_calculation = at;
        std::vector<double> worst;
        worst.reserve(samples.size());
        for (const auto& sample : samples) worst.push_back(sample.ms);
        const size_t n = (worst.size() + 99) / 100;
        std::partial_sort(worst.begin(), worst.begin() + n, worst.end(), std::greater<double>());
        double slow_ms = 0;
        for (size_t i = 0; i < n; ++i) slow_ms += worst[i];
        low1 = n * 1000.0 / slow_ms;
    }
};
