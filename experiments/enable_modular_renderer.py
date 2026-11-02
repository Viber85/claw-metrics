#!/usr/bin/env python3
"""Explicit opt-in integration; absent environment variable preserves stock path."""
from pathlib import Path
import sys
root=Path(sys.argv[1] if len(sys.argv)>1 else 'src')
assets=Path(__file__).resolve().parent
for name in ('claw_modular_layout.h','claw_modular_transport.h','claw_modular_loader.h','claw_modular_imgui.h'):
    (root/name).write_bytes((assets/'native'/name).read_bytes())
path=root/'hud_elements.h';text=path.read_text()
assert text.count('#pragma once')==1,'HUD declaration anchor mismatch'
path.write_text(text.replace('#pragma once','#pragma once\nbool ClawTryModular();',1))
path=root/'hud_elements.cpp';text=path.read_text()
assert 'bool ClawTryModular()' not in text,'Already patched'
text=text.replace('#include "hud_elements.h"','#include "hud_elements.h"\n#include "claw_modular_imgui.h"\n#include "claw_modular_loader.h"',1)
text+='\n'+(assets/'modular/mangohud_adapter.inc').read_text()
path.write_text(text)
path=root/'overlay.cpp';text=path.read_text()
anchor='   HUDElements.is_vulkan = is_vulkan;'
assert text.count(anchor)==1,'Renderer hook anchor mismatch'
text=text.replace(anchor,anchor+'''\n   extern bool ClawTryModular();
   if (ClawTryModular()) { window_size=ImVec2(1,1); return; }
''',1)
path.write_text(text)
