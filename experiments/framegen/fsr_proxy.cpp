// Optional Proton adapter for the public AMD FidelityFX DX12 API.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstddef>
#include <cstdint>
#include <cwchar>
#include "../native/claw_framegen_protocol.h"

namespace {
using namespace claw_framegen;

struct Header { std::uint64_t type; Header* next; };
struct Resource { void* object; std::uint32_t description[8]; std::uint32_t state; };
struct Present {
    Header header;
    void* device;
    void* command_list;
    Resource back_buffer, ui, output;
    bool generated;
    std::uint64_t frame_id;
};
using Callback = std::uint32_t (*)(Present*, void*);
struct Config {
    Header header;
    void* swapchain;
    Callback callback;
    void* callback_data;
    void* generation_callback;
    void* generation_data;
    bool enabled, async;
    Resource hudless;
    std::uint32_t flags;
    bool only_generated;
    std::int32_t rect[4];
    std::uint64_t frame_id;
};
static_assert(offsetof(Present, generated) == 176 && offsetof(Present, frame_id) == 184);
static_assert(offsetof(Config, callback) == 24 && offsetof(Config, frame_id) == 136);

constexpr std::uint64_t config_type = 0x20002;
constexpr std::uint64_t present_type = 0x20005;
constexpr std::uint32_t no_provider = 4;
struct Api {
    using Create = std::uint32_t (*)(void**, Header*, const void*);
    using Destroy = std::uint32_t (*)(void**, const void*);
    using Configure = std::uint32_t (*)(void**, const Header*);
    using Query = std::uint32_t (*)(void**, Header*);
    using Dispatch = std::uint32_t (*)(void**, const Header*);
    Create create;
    Destroy destroy;
    Configure configure;
    Query query;
    Dispatch dispatch;
};
HMODULE self = nullptr;
INIT_ONCE api_once = INIT_ONCE_STATIC_INIT;
INIT_ONCE relay_once = INIT_ONCE_STATIC_INIT;
SRWLOCK callback_lock = SRWLOCK_INIT;
SRWLOCK relay_lock = SRWLOCK_INIT;
Api api{};
Wire* relay = nullptr;

BOOL CALLBACK load_api(PINIT_ONCE, PVOID, PVOID*) {
    wchar_t path[1024]{};
    const auto length = GetModuleFileNameW(self, path, 1024);
    if (!length || length == 1024) return TRUE;
    wchar_t* slash = std::wcsrchr(path, L'\\');
    const wchar_t filename[] = L"amd_fidelityfx_framegeneration_dx12.claw-original.dll";
    if (!slash || slash - path + 1 + sizeof(filename) / sizeof(wchar_t) > 1024) return TRUE;
    std::wmemcpy(slash + 1, filename, sizeof(filename) / sizeof(wchar_t));
    HMODULE original = LoadLibraryW(path);
    if (!original) return TRUE;
    api.create = reinterpret_cast<Api::Create>(GetProcAddress(original, "ffxCreateContext"));
    api.destroy = reinterpret_cast<Api::Destroy>(GetProcAddress(original, "ffxDestroyContext"));
    api.configure = reinterpret_cast<Api::Configure>(GetProcAddress(original, "ffxConfigure"));
    api.query = reinterpret_cast<Api::Query>(GetProcAddress(original, "ffxQuery"));
    api.dispatch = reinterpret_cast<Api::Dispatch>(GetProcAddress(original, "ffxDispatch"));
    return TRUE;
}
void initialize() { InitOnceExecuteOnce(&api_once, load_api, nullptr, nullptr); }

BOOL CALLBACK open_relay(PINIT_ONCE, PVOID, PVOID*) {
    wchar_t path[1024] = L"Z:";
    const auto length = GetEnvironmentVariableW(L"CLAW_FRAMEGEN_FILE", path + 2, 1022);
    if (!length || length >= 1022 || path[2] != L'/') return TRUE;
    for (auto* c = path + 2; *c; ++c) if (*c == L'/') *c = L'\\';
    const HANDLE file = CreateFileW(path, GENERIC_READ | GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE,
                                    nullptr, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (file == INVALID_HANDLE_VALUE) return TRUE;
    LARGE_INTEGER size{};
    if (GetFileSizeEx(file, &size) && size.QuadPart == sizeof(Wire)) {
        const HANDLE mapping = CreateFileMappingW(file, nullptr, PAGE_READWRITE, 0, 0, nullptr);
        if (mapping) {
            relay = static_cast<Wire*>(MapViewOfFile(mapping, FILE_MAP_WRITE, 0, 0, sizeof(Wire)));
            CloseHandle(mapping);
        }
    }
    CloseHandle(file);
    return TRUE;
}

void record(bool is_generated) {
    FILETIME clock;
    GetSystemTimePreciseAsFileTime(&clock);
    const std::uint64_t ticks = (std::uint64_t(clock.dwHighDateTime) << 32) | clock.dwLowDateTime;
    constexpr std::uint64_t unix_offset = 116444736000000000ULL;
    AcquireSRWLockExclusive(&relay_lock);
    auto* guard = reinterpret_cast<volatile LONG*>(&relay->guard);
    InterlockedIncrement(guard);
    relay->marker = magic;
    const auto previous = relay->last;
    relay->events[previous % capacity] = {(ticks - unix_offset) * 100, previous + 1,
                                         is_generated ? generated : game, 0};
    relay->last = previous + 1;
    InterlockedIncrement(guard);
    ReleaseSRWLockExclusive(&relay_lock);
}

struct OriginalCallback { Callback function = nullptr; void* data = nullptr; };
OriginalCallback callbacks[64];

OriginalCallback* remember(Callback callback, void* data) {
    // AMD can retain an earlier callback for work already queued. Entries stay
    // valid for the lifetime of the module and repeated configurations reuse them.
    AcquireSRWLockExclusive(&callback_lock);
    OriginalCallback* entry = nullptr;
    for (auto& item : callbacks) {
        if (item.function == callback && item.data == data) { entry = &item; break; }
        if (!item.function) { item = {callback, data}; entry = &item; break; }
    }
    ReleaseSRWLockExclusive(&callback_lock);
    return entry;
}

std::uint32_t observe(Present* frame, void* data) {
    const auto* original = static_cast<const OriginalCallback*>(data);
    const auto result = original->function(frame, original->data);
    if (!result && frame && frame->header.type == present_type) record(frame->generated);
    return result;
}
}

extern "C" BOOL WINAPI DllMain(HMODULE module, DWORD reason, LPVOID) {
    if (reason == DLL_PROCESS_ATTACH) self = module;
    else if (reason == DLL_PROCESS_DETACH && relay) UnmapViewOfFile(relay);
    return TRUE;
}

extern "C" __declspec(dllexport) std::uint32_t ffxCreateContext(void** ctx, Header* desc, const void* alloc) {
    initialize();
    return api.create ? api.create(ctx, desc, alloc) : no_provider;
}
extern "C" __declspec(dllexport) std::uint32_t ffxDestroyContext(void** ctx, const void* alloc) {
    initialize();
    return api.destroy ? api.destroy(ctx, alloc) : no_provider;
}
extern "C" __declspec(dllexport) std::uint32_t ffxConfigure(void** ctx, const Header* desc) {
    initialize();
    if (!api.configure) return no_provider;
    if (ctx && desc && desc->type == config_type) {
        const auto* config = reinterpret_cast<const Config*>(desc);
        if (config->callback) {
            InitOnceExecuteOnce(&relay_once, open_relay, nullptr, nullptr);
            if (relay) {
                if (auto* original = remember(config->callback, config->callback_data)) {
                    Config wrapped = *config;
                    wrapped.callback = observe;
                    wrapped.callback_data = original;
                    return api.configure(ctx, &wrapped.header);
                }
            }
        }
    }
    return api.configure(ctx, desc);
}
extern "C" __declspec(dllexport) std::uint32_t ffxQuery(void** ctx, Header* desc) {
    initialize();
    return api.query ? api.query(ctx, desc) : no_provider;
}
extern "C" __declspec(dllexport) std::uint32_t ffxDispatch(void** ctx, const Header* desc) {
    initialize();
    return api.dispatch ? api.dispatch(ctx, desc) : no_provider;
}
