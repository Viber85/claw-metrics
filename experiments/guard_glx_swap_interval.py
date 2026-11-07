#!/usr/bin/env python3
"""Avoid GLX_EXT_swap_control queries when the server lacks the extension.

MangoHud 0.8.1 unconditionally queries GLX_SWAP_INTERVAL_EXT on its first
swap; Mesa's GLX implementation can dereference a null dispatch entry on
servers without GLX_EXT_swap_control (including Xvfb).
"""
from pathlib import Path
import sys

source = Path(sys.argv[1]) / 'gl/inject_glx.cpp'
text = source.read_text()
before = '''    if (HUDElements.vsync == 10 || elapsed_seconds.count() > 5.0)
        glx.QueryDrawable(dpy, drawable, GLX_SWAP_INTERVAL_EXT, &HUDElements.vsync);'''
after = '''    if (HUDElements.vsync == 10 || elapsed_seconds.count() > 5.0) {
        using QueryExtensions = const char* (*)(Display*, int);
        static auto query_extensions = reinterpret_cast<QueryExtensions>(
            get_glx_proc_address("glXQueryExtensionsString"));
        Display* display = static_cast<Display*>(dpy);
        const char* extensions = query_extensions
            ? query_extensions(display, DefaultScreen(display)) : nullptr;
        if (glx.QueryDrawable && extensions &&
            std::strstr(extensions, "GLX_EXT_swap_control"))
            glx.QueryDrawable(dpy, drawable, GLX_SWAP_INTERVAL_EXT, &HUDElements.vsync);
        else
            HUDElements.vsync = 0;
        last_time = current_time;
    }'''
assert text.count(before) == 1, 'MangoHud GLX swap query changed'
source.write_text(text.replace(before, after))
