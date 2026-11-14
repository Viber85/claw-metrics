#pragma once
#include "claw_framegen_protocol.h"
#include <cstddef>
#include <chrono>
#include <cstdlib>
#include <deque>
#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>
#include <vector>

namespace claw_framegen {
constexpr std::uint64_t second = 1000000000;
constexpr std::uint64_t history = 2 * second;
constexpr std::uint64_t stale = 500000000;

inline std::uint64_t now() {
    return std::chrono::duration_cast<std::chrono::nanoseconds>(
        std::chrono::system_clock::now().time_since_epoch()).count();
}

struct Point { std::uint64_t at; float ms; };

class Stream {
    std::deque<std::uint64_t> frames;
public:
    void add(std::uint64_t at) {
        if (!frames.empty() && (at <= frames.back() || at - frames.back() > stale)) frames.clear();
        frames.push_back(at);
        while (frames.size() > 1024 || at - frames.front() > history) frames.pop_front();
    }

    void clear() { frames.clear(); }

    double fps(std::uint64_t at) const {
        if (frames.size() < 2 || at < frames.back() || at - frames.back() > stale) return -1;
        auto first = frames.begin();
        while (first + 1 < frames.end() && frames.back() - *first > second) ++first;
        const auto duration = frames.back() - *first;
        return duration >= second / 4
            ? double(frames.end() - first - 1) * second / duration : -1;
    }

    std::vector<Point> graph(std::uint64_t at) const {
        std::vector<Point> points;
        if (frames.size() < 2 || at < frames.back() || at - frames.back() > stale) return points;
        for (auto frame = frames.begin() + 1; frame != frames.end(); ++frame) {
            if (at - *frame <= history)
                points.push_back({*frame, float(*frame - *(frame - 1)) / 1000000.f});
        }
        return points;
    }
};

struct Snapshot {
    double game_fps = -1;
    double generated_fps = -1;
    double output_fps = -1;
    std::vector<Point> game_graph;
    std::vector<Point> output_graph;
    std::uint64_t at = 0;
};

class Meter {
    Stream game_frames, output_frames;
    std::deque<Event> classified;
    std::uint64_t sequence = 0;
    std::uint64_t next_read = 0;
    int fd = -1;
public:
    Meter() = default;
    Meter(const Meter&) = delete;
    Meter& operator=(const Meter&) = delete;
    ~Meter() { if (fd >= 0) close(fd); }

    void presented(std::uint64_t at) { output_frames.add(at); }

    void ingest(const Wire& wire, std::uint64_t at) {
        if (wire.marker != magic || wire.guard % 2 || wire.last == sequence) return;
        if (wire.last < sequence || wire.last - sequence > capacity) {
            classified.clear();
            game_frames.clear();
            sequence = wire.last >= capacity ? wire.last - capacity : 0;
        }
        while (sequence < wire.last) {
            const auto& event = wire.events[sequence % capacity];
            ++sequence;
            if (event.sequence != sequence || !event.at || event.at > at ||
                at - event.at > history || (event.kind != game && event.kind != generated))
                continue;
            if (!classified.empty() &&
                (event.at < classified.back().at || event.at - classified.back().at > stale)) {
                classified.clear();
                game_frames.clear();
            }
            classified.push_back(event);
            while (!classified.empty() && event.at - classified.front().at > history)
                classified.pop_front();
            if (event.kind == game) game_frames.add(event.at);
        }
    }

    void poll(std::uint64_t at) {
        if (next_read > at && next_read - at <= second) return;
        next_read = at + second / 20;
        if (fd < 0) {
            const char* file = std::getenv("CLAW_FRAMEGEN_FILE");
            if (!file || file[0] != '/') return;
            const int candidate = open(file, O_RDONLY | O_CLOEXEC | O_NONBLOCK | O_NOFOLLOW);
            if (candidate < 0) return;
            struct stat info{};
            if (fstat(candidate, &info) || !S_ISREG(info.st_mode) || info.st_uid != geteuid()) {
                close(candidate);
                return;
            }
            fd = candidate;
        }
        Wire wire{};
        std::uint32_t before = 0, after = 0;
        constexpr auto guard_offset = offsetof(Wire, guard);
        if (pread(fd, &before, sizeof(before), guard_offset) != sizeof(before) || before % 2 ||
            pread(fd, &wire, sizeof(wire), 0) != sizeof(wire) ||
            pread(fd, &after, sizeof(after), guard_offset) != sizeof(after) ||
            before != wire.guard || before != after) return;
        ingest(wire, now());
    }

    Snapshot snapshot(std::uint64_t at, bool graph) const {
        Snapshot value;
        value.at = at;
        value.output_fps = output_frames.fps(at);
        if (graph) value.output_graph = output_frames.graph(at);
        if (classified.empty() || at < classified.back().at ||
            at - classified.back().at > stale || value.output_fps < 0) return value;

        value.game_fps = game_frames.fps(at);
        const auto end = classified.back().at;
        if (value.game_fps >= 0 && end - classified.front().at >= second / 4) {
            auto first = classified.begin();
            while (end - first->at > second) ++first;
            if (end != first->at) {
                unsigned count = 0;
                for (auto next = first + 1; next != classified.end(); ++next)
                    count += next->kind == generated;
                value.generated_fps = double(count) * second / (end - first->at);
            }
            if (graph) value.game_graph = game_frames.graph(at);
        }
        return value;
    }
};
}
