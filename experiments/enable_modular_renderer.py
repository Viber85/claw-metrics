#!/usr/bin/env python3
"""Explicit opt-in integration; absent environment variable preserves stock path."""
from pathlib import Path
import sys
root=Path(sys.argv[1] if len(sys.argv)>1 else 'src')
assets=Path(__file__).resolve().parent
for name in ('claw_modular_layout.h','claw_modular_transport.h','claw_modular_loader.h','claw_modular_imgui.h','claw_modular_power.h'):
    (root/name).write_bytes((assets/'native'/name).read_bytes())
path=root/'overlay_params.h';text=path.read_text()
anchor='   OVERLAY_PARAM_CUSTOM(claw_fps_scale)               \\'
assert text.count(anchor)==1
text=text.replace(anchor,anchor+'\n   OVERLAY_PARAM_CUSTOM(claw_modular_file)               \\',1)
text=text.replace('   OVERLAY_PARAM_CUSTOM(claw_modular_file)               \\', '   OVERLAY_PARAM_CUSTOM(claw_modular_file)               \\\n   OVERLAY_PARAM_CUSTOM(claw_unit_superscript)               \\',1)
text=text.replace('   bool claw_center_horizontal = false;', '   std::string claw_modular_file;\n   bool claw_center_horizontal = false;',1)
text=text.replace('   std::string claw_modular_file;', '   std::string claw_modular_file;\n   bool claw_unit_superscript = false;',1)
path.write_text(text)
path=root/'overlay_params.cpp';text=path.read_text()
anchor='#define parse_claw_fps_scale(s) parse_unsigned(s)'
assert text.count(anchor)==1
path.write_text(text.replace(anchor,anchor+'\n#define parse_claw_modular_file(s) parse_path(s)\n#define parse_claw_unit_superscript(s) parse_unsigned(s)',1))
path=root/'hud_elements.h';text=path.read_text()
assert text.count('#pragma once')==1,'HUD declaration anchor mismatch'
path.write_text(text+'\nbool ClawTryModular();\nvoid ClawModularBackground(const ImVec4& rectangle, const overlay_params& params,bool custom,ImU32 fill);\n')
path=root/'hud_elements.cpp';text=path.read_text()
assert 'bool ClawTryModular()' not in text,'Already patched'
text=text.replace('#include "hud_elements.h"','#include "hud_elements.h"\n#include "claw_modular_imgui.h"\n#include "claw_modular_loader.h"\n#include "claw_modular_power.h"',1)
text+='\n'+(assets/'modular/mangohud_adapter.inc').read_text()
path.write_text(text)
path=root/'overlay.cpp';text=path.read_text()
anchor='   HUDElements.is_vulkan = is_vulkan;'
assert text.count(anchor)==1,'Renderer hook anchor mismatch'
text=text.replace(anchor,anchor+'''\n   extern bool ClawTryModular();
   if (ClawTryModular()) { window_size=ImVec2(1,1); return; }
''',1)
path.write_text(text)

# Use the exact production rounded gradient/outline code in its own measured window.
path=root/'overlay.cpp';text=path.read_text()
anchor='void render_imgui(swapchain_stats& data, struct overlay_params& params, ImVec2& window_size, bool is_vulkan)'
assert text.count(anchor)==1
wrapper=r'''void ClawModularBackground(const ImVec4& rect,const overlay_params& params,bool custom,ImU32 fill) {
    ImGui::PushStyleVar(ImGuiStyleVar_WindowPadding,ImVec2(0,0));
    ImGui::PushStyleVar(ImGuiStyleVar_WindowMinSize,ImVec2(1,1));
    ImGui::PushStyleVar(ImGuiStyleVar_WindowBorderSize,0.f);
    ImGui::SetNextWindowPos(ImVec2(rect.x,rect.y),ImGuiCond_Always);
    ImGui::SetNextWindowSize(ImVec2(rect.z,rect.w),ImGuiCond_Always);
    ImGui::SetNextWindowBgAlpha(params.background_alpha);
    ImGui::Begin("##ClawModularBackground",nullptr,ImGuiWindowFlags_NoDecoration|ImGuiWindowFlags_NoInputs|ImGuiWindowFlags_NoSavedSettings|ImGuiWindowFlags_NoNav|
                 ((custom||params.claw_background_mode)?ImGuiWindowFlags_NoBackground:0));
    if(custom){auto* draw=ImGui::GetWindowDrawList();draw->AddRectFilled(ImVec2(rect.x,rect.y),ImVec2(rect.x+rect.z,rect.y+rect.w),fill,params.round_corners);}
    else ClawDrawBackground(params);
    ClawDrawOutline(params);
    ImGui::End();ImGui::PopStyleVar(3);
}

'''
path.write_text(text.replace(anchor,wrapper+anchor,1))

# Honor ImGui draw-command base vertices for documents above 64K vertices.
path=root/'vulkan.cpp';text=path.read_text()
anchor='device_data->vtable.CmdDrawIndexed(draw->command_buffer, pcmd->ElemCount, 1, idx_offset, vtx_offset, 0);'
assert text.count(anchor)==1,'Vulkan draw anchor mismatch'
text=text.replace(anchor,'device_data->vtable.CmdDrawIndexed(draw->command_buffer, pcmd->ElemCount, 1, idx_offset, vtx_offset + int(pcmd->VtxOffset), 0);',1)
anchor='   ImGui::GetIO().IniFilename = NULL;'
assert text.count(anchor)==1,'Vulkan IO anchor mismatch'
path.write_text(text.replace(anchor,anchor+'\n   ImGui::GetIO().BackendFlags |= ImGuiBackendFlags_RendererHasVtxOffset;',1))
