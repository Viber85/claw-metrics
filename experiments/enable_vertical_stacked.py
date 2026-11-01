#!/usr/bin/env python3
"""Install Claw Metrics' opt-in two-column native vertical stack after all other patches."""
from pathlib import Path
import re
import sys

root=Path(sys.argv[1] if len(sys.argv)>1 else "src")
def change(path, before, after):
    f=root/path
    src=f.read_text()
    count=src.count(before)
    if count!=1:
        raise RuntimeError(f"{path}: expected one anchor, got {count}: {before[:65]!r}")
    f.write_text(src.replace(before,after,1))

change("overlay_params.h",
    "   OVERLAY_PARAM_CUSTOM(claw_fps_scale)               \\",
    "   OVERLAY_PARAM_CUSTOM(claw_fps_scale)               \\\n"
    "   OVERLAY_PARAM_CUSTOM(claw_vertical_stack)          \\")
change("overlay_params.h",
    "   bool claw_center_horizontal = false;",
    "   bool claw_vertical_stack = false;\n   bool claw_center_horizontal = false;")
change("overlay_params.cpp",
    "#define parse_claw_fps_scale(s) parse_unsigned(s)",
    "#define parse_claw_fps_scale(s) parse_unsigned(s)\n"
    "#define parse_claw_vertical_stack(s) parse_unsigned(s) != 0")

hud=root/"hud_elements.cpp"
s=hud.read_text()
def swap(old,new):
    global s
    n=s.count(old)
    if n!=1:
        raise RuntimeError(f"HUD anchor count {n}: {old[:70]!r}")
    s=s.replace(old,new,1)

swap("static void ImguiNextColumnFirstItem()\n{",
"""static bool claw_vertical_first_value = false;
static void ImguiNextColumnFirstItem()
{""")
helper_start=s.index("static void ImguiNextColumnFirstItem()")
helper_brace=s.index("{",helper_start)
helper_end=s.index("\n}",helper_brace)
s=s[:helper_end]+"""
    claw_vertical_first_value = HUDElements.params &&
        HUDElements.params->claw_vertical_stack &&
        !HUDElements.params->enabled[OVERLAY_PARAM_ENABLED_horizontal];"""+s[helper_end:]
swap("""static void ClawMetricGap() {
    ImGui::SameLine(0.0f, HUDElements.params->claw_inner_gap);
}""",
"""static void ClawMetricGap() {
    if (HUDElements.params->claw_vertical_stack &&
        !HUDElements.params->enabled[OVERLAY_PARAM_ENABLED_horizontal] &&
        claw_vertical_first_value) {
        claw_vertical_first_value = false;
        ImGui::TableSetColumnIndex(1);
    } else {
        ImGui::SameLine(0.0f, HUDElements.params->claw_inner_gap);
    }
}""")
for name in ("fps","cpu_stats","gpu_stats","ram","vram","battery"):
    start=s.index("void HudElements::"+name+"(){")
    stop=s.index("\n        return;",start) if name in ("ram","vram","battery") else s.index("\n            return;",start)
    chunk=s[start:stop]
    needle=r"HUDElements\.params->claw_inline_metrics &&\s*HUDElements\.params->enabled\[OVERLAY_PARAM_ENABLED_horizontal\]"
    replacement="HUDElements.params->claw_inline_metrics &&\n            (HUDElements.params->enabled[OVERLAY_PARAM_ENABLED_horizontal] ||\n             HUDElements.params->claw_vertical_stack)"
    revised,n=re.subn(needle,replacement,chunk,count=1)
    if n!=1: raise RuntimeError(f"cannot locate {name} compact branch")
    s=s[:start]+revised+s[stop:]

# In vertical mode, sensor unit glyphs must use the same font as the values.
# The previous small units (GHz/MHz/GiB/W) looked like superscripts.
for name in ("cpu_stats","gpu_stats","ram","vram"):
    start=s.index("void HudElements::"+name+"(){")
    stop=s.index("\n        return;",start) if name in ("ram","vram") else s.index("\n            return;",start)
    chunk=s[start:stop]
    pushes=chunk.count("ImGui::PushFont(HUDElements.sw_stats->font1);")
    pops=chunk.count("ImGui::PopFont();")
    if not pushes or pushes!=pops: raise RuntimeError(f"{name}: unit font pairs {pushes}/{pops}")
    chunk=chunk.replace("ImGui::PushFont(HUDElements.sw_stats->font1);",
        "if (!HUDElements.params->claw_vertical_stack) ImGui::PushFont(HUDElements.sw_stats->font1);")
    chunk=chunk.replace("ImGui::PopFont();",
        "if (!HUDElements.params->claw_vertical_stack) ImGui::PopFont();")
    s=s[:start]+chunk+s[stop:]

# Show TDP and DRAW at normal font size in Claw Stacked, without
# changing their read-only values or horizontal rendering.
old="const bool claw_exec_small_font = !HUDElements.params->enabled[OVERLAY_PARAM_ENABLED_horizontal];"
if s.count(old)!=1: raise RuntimeError("exec font anchor drift")
s=s.replace(old, "const bool claw_exec_small_font = !HUDElements.params->enabled[OVERLAY_PARAM_ENABLED_horizontal] && !HUDElements.params->claw_vertical_stack;", 1)

graph=r"""
static void ClawVerticalGraph() {
    auto* p = HUDElements.params;
    constexpr int samples=48;
    const int count=ARRAY_SIZE(HUDElements.sw_stats->frames_stats);
    HUDElements.sw_stats->stat_selector=OVERLAY_PLOTS_frame_timing;
    HUDElements.sw_stats->time_dividor=1000000.0f;
    const float w=ImMax(56.0f,float(p->width)-2.0f*ImMax(0.0f,p->claw_padding_x)-12.0f);
    const float h=ImClamp(float(p->font_size)*1.40f,23.0f,38.0f);
    ImguiNextColumnFirstItem();
    const ImVec2 origin=ImGui::GetCursorScreenPos();
    ImGui::Dummy(ImVec2(0.0f,h));
    if(count<2) return;
    float values[samples];
    float low=250.0f, high=0.0f;
    for(int i=0;i<samples;++i) {
        const int idx=i*(count-1)/(samples-1);
        const double raw=get_time_stat(HUDElements.sw_stats,idx);
        values[i]=std::isfinite(raw)&&raw>=0.0 ? ImClamp(float(raw),0.0f,250.0f) : 0.0f;
        if(values[i]>0.0f) {
            low=ImMin(low,values[i]);
            high=ImMax(high,values[i]);
        }
    }
    if(high<=0.0f) return;
    // Adaptive, padded graph scale: a stable frame time is a fine
    // line near the middle, not a bright, solid block at the top.
    const float span=ImMax(4.0f,high-low);
    const float lower=ImMax(0.0f,(low+high)*0.5f-span*0.75f);
    const float range=span*1.5f;
    ImVec2 pts[samples];
    for(int i=0;i<samples;++i) {
        const float y=ImClamp((values[i]-lower)/range,0.0f,1.0f);
        pts[i]=ImVec2(origin.x+w*float(i)/float(samples-1),
                      origin.y+h-3.0f-y*(h-6.0f));
    }
    ImDrawList* draw=ImGui::GetWindowDrawList();
    const ImVec4 col=HUDElements.colors.frametime;
    const int style=ImClamp(p->claw_graph_style,0,3);
    const ImU32 line=ImGui::ColorConvertFloat4ToU32(col);
    const float opacity=style==1 ? 0.20f : (style==3 ? 0.07f : 0.0f);
    const ImU32 fill=ImGui::ColorConvertFloat4ToU32(
        ImVec4(col.x,col.y,col.z,col.w*opacity));
    const float bottom=origin.y+h-2.0f;
    draw->PushClipRect(origin,ImVec2(origin.x+w,origin.y+h),true);
    if(style==2) {
        const float slot=w/float(samples);
        for(int i=0;i<samples;++i) {
            const float x=origin.x+slot*float(i);
            draw->AddRectFilled(ImVec2(x,pts[i].y),
                ImVec2(x+ImMax(1.0f,slot-1.3f),bottom),line);
        }
    } else {
        if(opacity>0.0f)
            for(int i=1;i<samples;++i)
                draw->AddQuadFilled(ImVec2(pts[i-1].x,bottom),pts[i-1],
                    pts[i],ImVec2(pts[i].x,bottom),fill);
        draw->AddPolyline(pts,samples,line,false,1.65f);
    }
    draw->PopClipRect();
}

"""
swap("void HudElements::frame_timing(){",graph+"""void HudElements::frame_timing(){
    if (HUDElements.params->claw_vertical_stack &&
        !HUDElements.params->enabled[OVERLAY_PARAM_ENABLED_horizontal] &&
        HUDElements.params->enabled[OVERLAY_PARAM_ENABLED_frame_timing]) {
        ClawVerticalGraph();
        return;
    }
""")
hud.write_text(s)

change("overlay.cpp",
    "   ImGuiTableFlags table_flags = ImGuiTableFlags_NoClip;",
    """   const bool claw_vertical_stack = params.claw_vertical_stack &&
       !params.enabled[OVERLAY_PARAM_ENABLED_horizontal];
   ImGuiTableFlags table_flags = ImGuiTableFlags_NoClip;
   if (claw_vertical_stack)
       table_flags |= ImGuiTableFlags_BordersInnerH;""")

overlay=root/"overlay.cpp"
code=overlay.read_text()
pattern=r'if\s*\(\s*ImGui::BeginTable\("hud",\s*params\.table_columns,\s*table_flags\s*\)\s*\)\s*\{'
replacement='''\g<0>
          if (claw_vertical_stack && params.table_columns == 2) {
              const float label_width = ImClamp(params.font_size * 3.7f,58.0f,105.0f);
              ImGui::TableSetupColumn("Metric",ImGuiTableColumnFlags_WidthFixed,label_width);
              ImGui::TableSetupColumn("Values",ImGuiTableColumnFlags_WidthStretch);
          }'''
code,n=re.subn(pattern,replacement,code,count=1)
if n!=1: raise RuntimeError(f"table layout marker count {n}")
# Subtler horizontal row dividers, without changing horizontal style.
begin='if (ImGui::BeginTable("hud", params.table_columns, table_flags )) {'
if code.count(begin)!=1: raise RuntimeError("begin table anchor drift")
code=code.replace(begin,
    'if (claw_vertical_stack) ImGui::PushStyleColor(ImGuiCol_TableBorderLight,'
    ' ImVec4(0.44f,0.58f,0.70f,0.20f));\n       '+begin,1)
end_pattern=r'HUDElements\\.table_columns_count\\s*=\\s*0;\\s*\\n\\s*\\}'
code,n=re.subn(end_pattern,lambda m: m.group(0)+"\\n       if (claw_vertical_stack) ImGui::PopStyleColor();",code,count=1)
if n!=1: raise RuntimeError(f"end table style guard found {n} blocks")
overlay.write_text(code)
print("Claw native vertical stacked renderer installed")
