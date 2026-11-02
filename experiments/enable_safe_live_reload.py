#!/usr/bin/env python3
"""Defer config parsing to a render boundary; rebuild Vulkan fonts before NewFrame.

MangoHud v0.8.1's parser mutates global HUD elements, not just local_params.
Taking the notifier mutex only for the final assignment does not protect that.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'src')

def replace(name, before, after):
    path = root / name
    text = path.read_text()
    if text.count(before) != 1:
        raise RuntimeError(f'{name}: live-reload anchor mismatch: {before[:80]!r}')
    path.write_text(text.replace(before, after, 1))

replace('notify.h', '#include <mutex>', '#include <mutex>\n#include <atomic>')
replace('notify.h', '    bool quit = false;',
        '    std::atomic<bool> quit{false};\n    std::atomic<bool> reload_pending{false};')
replace('notify.h', 'void stop_notifier(notify_thread& nt);',
        'void stop_notifier(notify_thread& nt);\nvoid apply_pending_config(notify_thread& nt);')
p = root / 'notify.cpp'
s = p.read_text()
start = s.index('static void fileChanged(')
end = s.index('\nbool start_notifier(', start)
s = s[:start] + '''// The watcher never calls parse_overlay_config: it also mutates HUDElements.
// A release/acquire flag coalesces writes until the render thread is ready.
static void fileChanged(notify_thread *nt) {
    alignas(struct inotify_event) char buffer[EVENT_BUF_LEN];
    while (!nt->quit.load()) {
        const int length = read(nt->fd, buffer, sizeof(buffer));
        for (int i = 0; i + int(EVENT_SIZE) <= length;) {
            const auto* event = reinterpret_cast<const inotify_event*>(&buffer[i]);
            const int step = int(EVENT_SIZE + event->len);
            if (step <= 0 || i + step > length) break;
            i += step;
            if (event->mask & (IN_MODIFY | IN_DELETE_SELF | IN_MOVE_SELF | IN_IGNORED))
                nt->reload_pending.store(true, std::memory_order_release);
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }
}

// Called before HUD sampling, font rebuilding and ImGui::NewFrame, on the
// same thread that draws the HUD. Never during iteration over ordered_functions.
void apply_pending_config(notify_thread& nt) {
    if (!nt.reload_pending.exchange(false, std::memory_order_acquire)) return;
    std::lock_guard<std::mutex> lock(nt.mutex);
    parse_overlay_config(nt.params, getenv("MANGOHUD_CONFIG"), false);
    // Atomic file replacement invalidates an inode watch. Always rearm it,
    // even when the config pathname has not changed.
    if (nt.fd >= 0) {
        if (nt.wd >= 0) inotify_rm_watch(nt.fd, nt.wd);
        nt.wd = inotify_add_watch(nt.fd, nt.params->config_file_path.c_str(),
                                 IN_MODIFY | IN_DELETE_SELF | IN_MOVE_SELF);
        // The reader ignores IN_IGNORED from removing our own old watch.
    }
}
''' + s[end:]
# IN_IGNORED from our own rm_watch must not cause a reload loop.
s=s.replace('if (event->mask & (IN_MODIFY | IN_DELETE_SELF | IN_MOVE_SELF | IN_IGNORED))',
            'if (event->mask & (IN_MODIFY | IN_DELETE_SELF | IN_MOVE_SELF))')
p.write_text(s)
replace('notify.cpp', '    nt.thread = std::thread(fileChanged, &nt);',
        '    nt.quit.store(false);\n    nt.reload_pending.store(false);\n    nt.thread = std::thread(fileChanged, &nt);')
replace('vulkan.cpp', '   snapshot_swapchain_frame(swapchain_data);',
        '   apply_pending_config(swapchain_data->device->instance->notifier);\n   snapshot_swapchain_frame(swapchain_data);')
# The original check occurs in ensure_swapchain_fonts AFTER ImGui::Render.
# Check before NewFrame as well, so no frame is laid out with the old atlas.
replace('vulkan.cpp', 'static void compute_swapchain_display(struct swapchain_data *data)',
        'static void check_fonts(struct swapchain_data* data);\n\nstatic void compute_swapchain_display(struct swapchain_data *data)')
replace('vulkan.cpp', '   ImGui::SetCurrentContext(data->imgui_context);\n   if (HUDElements.colors.update)',
        '   ImGui::SetCurrentContext(data->imgui_context);\n   check_fonts(data); // rebuild atlas before any ImGui frame uses its fonts\n   if (HUDElements.colors.update)')
replace('gl/gl_hud.cpp', '    static int control_client = -1;',
        '    apply_pending_config(notifier);\n    static int control_client = -1;')
print('Safe render-thread configuration reload and pre-frame Vulkan font refresh installed')
