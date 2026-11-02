"""Exercise the actual Linux notifier with file replacement; no GPU/device claims.

Only overlay parsing/logging dependencies are stubbed. inotify, threading and
our notify.cpp implementation are real. The unpatched v0.8.1 watcher must fail
because it parses configuration on the watcher thread.
"""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile

HARNESS = r'''
#include <atomic>
#include <chrono>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <string>
#include <thread>
#include <unistd.h>
#include "notify.h"
std::atomic<int> parsed{0};
std::atomic<bool> wrong_thread{false};
std::thread::id render_thread;
void parse_overlay_config(overlay_params*, const char*, bool) {
    if (std::this_thread::get_id() != render_thread) wrong_thread.store(true);
    ++parsed;
}
#ifndef CLAW_SAFE
void apply_pending_config(notify_thread&) {}
#endif
int main(int argc, char** argv) {
    const std::string path = argv[1];
    render_thread = std::this_thread::get_id();
    { std::ofstream out(path); out << "horizontal=0\nfont_size=26\n"; }
    overlay_params params;
    params.config_file_path = path;
    notify_thread nt;
    nt.params = &params;
    if (!start_notifier(nt)) return 10;
    // Simulate the backend's os.replace rather than an in-place file edit.
    for (int i=0; i<24; ++i) {
        const auto temp = path + ".tmp";
        { std::ofstream out(temp); out << "horizontal=" << i%2 << "\nfont_size=" << (i%2?28:26) << "\n"; }
        if (rename(temp.c_str(), path.c_str()) != 0) return 11;
#ifdef CLAW_SAFE
        for (int tries=0; tries<50 && !nt.reload_pending.load(); ++tries)
            std::this_thread::sleep_for(std::chrono::milliseconds(20));
        if (!nt.reload_pending.load()) { stop_notifier(nt); return 12; }
        if (parsed.load() != i) { stop_notifier(nt); return 13; }
        // Loading remains deferred while the renderer is between boundaries.
        std::this_thread::sleep_for(std::chrono::milliseconds(30));
        if (parsed.load() != i) { stop_notifier(nt); return 14; }
        apply_pending_config(nt);
        if (parsed.load() != i+1) { stop_notifier(nt); return 15; }
#else
        std::this_thread::sleep_for(std::chrono::milliseconds(350));
#endif
        if (wrong_thread.load()) { stop_notifier(nt); return 21; }
    }
    // Rearming must not feed itself an endless series of IN_IGNORED reloads.
    std::this_thread::sleep_for(std::chrono::milliseconds(250));
    apply_pending_config(nt);
    stop_notifier(nt);
    if (parsed.load() != 24) return 16;
    std::cout << "24 atomic style replacements parsed only at render boundaries; watcher cleanly stopped\n";
}
'''

def run(source, baseline=False):
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        (root/'spdlog').mkdir()
        (root/'spdlog/spdlog.h').write_text('#define SPDLOG_ERROR(...) ((void)0)\n#define SPDLOG_DEBUG(...) ((void)0)\n')
        (root/'config.h').write_text('#include <cstdlib>\n#include <cstring>\n#include <cerrno>\n')
        (root/'overlay_params.h').write_text('#pragma once\n#include <string>\nstruct overlay_params { std::string config_file_path; };\nvoid parse_overlay_config(overlay_params*, const char*, bool);\n')
        for name in ('notify.cpp', 'notify.h'):
            (root/name).write_bytes((source/name).read_bytes())
        (root/'test.cpp').write_text(HARNESS)
        binary = root/'check'
        args = ['g++', '-std=c++17', '-pthread', '-O1', '-g', '-fsanitize=address,undefined', '-I', str(root)]
        if not baseline:
            args += ['-DCLAW_SAFE']
        subprocess.run([*args, str(root/'notify.cpp'), str(root/'test.cpp'), '-o', str(binary)],check=True)
        result = subprocess.run([str(binary), str(root/'MangoHud.conf')], capture_output=True, text=True, timeout=20,
                                env={**os.environ, "ASAN_OPTIONS": "detect_leaks=0"})
        if baseline:
            assert result.returncode == 21, result.stderr + result.stdout + str(result.returncode)
            print('Baseline failure reproduced: config parser runs on watcher thread')
        else:
            assert result.returncode == 0, result.stderr + result.stdout + str(result.returncode)
            print(result.stdout.strip())
            # Check the paired Vulkan integration, not just the signal producer.
            vk = (source/'vulkan.cpp').read_text()
            frame = vk[vk.index('static void compute_swapchain_display'):vk.index('static uint32_t vk_memory_type')]
            assert frame.index('check_fonts(data);') < frame.index('ImGui::NewFrame();')
            present = vk[vk.index('static struct overlay_draw *before_present'):]
            assert present.index('apply_pending_config(') < present.index('snapshot_swapchain_frame(')
            gl = (source/'gl/gl_hud.cpp').read_text().split('void imgui_render(', 1)[1]
            assert gl.index('apply_pending_config(') < gl.index('create_fonts(') < gl.index('ImGui::NewFrame();')
            print('Vulkan/OpenGL integration order verified; no on-device Vulkan execution performed')

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('--baseline', action='store_true')
    args=parser.parse_args()
    run(args.source, args.baseline)
