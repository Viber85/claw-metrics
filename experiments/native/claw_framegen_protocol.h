#pragma once
#include <cstdint>

namespace claw_framegen {
constexpr std::uint32_t magic = 0x31474643; // CFG1
constexpr unsigned capacity = 256;
enum Kind : std::uint32_t { game = 1, generated = 2 };

struct Event {
    std::uint64_t at = 0; // Unix epoch nanoseconds, on both sides of Proton.
    std::uint64_t sequence = 0;
    std::uint32_t kind = 0;
    std::uint32_t reserved = 0;
};

struct Wire {
    std::uint32_t marker = 0;
    std::uint32_t guard = 0; // Odd while publishing, even after a complete event.
    std::uint64_t last = 0;
    Event events[capacity];
};
static_assert(sizeof(Event) == 24);
static_assert(sizeof(Wire) == 16 + 24 * capacity);
}
