#!/usr/bin/env python3
"""Opt-in CI diagnostics from the actual graph fill vertices, silent in normal use."""
from pathlib import Path
import sys
p=Path(sys.argv[1])/'hud_elements.cpp'
s=p.read_text()
anchor='static void ClawVerticalGraph() {'
assert s.count(anchor)==1
helper=r'''
static void ClawVerifyFillAlpha(const char* orientation, int style, const ImDrawList* draw, int first) {
    if (!std::getenv("CLAW_METRICS_VERIFY") || first>=draw->VtxBuffer.Size) return;
    static bool seen[2][6] = {};
    const int layout = orientation[0]=='v' ? 1 : 0;
    if (style<0 || style>=6 || seen[layout][style]) return;
    seen[layout][style] = true;
    // AddQuadFilled's first vertex is interior; antialias fringe vertices may
    // legitimately have zero alpha even when the actual fill is opaque.
    const unsigned alpha = (draw->VtxBuffer[first].col >> IM_COL32_A_SHIFT) & 255;
    std::fprintf(stderr,"CLAW_GRAPH layout=%s style=%d fill_alpha=%u\n",orientation,style,alpha);
}
'''
s=s.replace(anchor,helper+'\n'+anchor,1)
old='''        if(opacity>0.0f)
            for(int i=1;i<samples;++i)
                draw->AddQuadFilled(ImVec2(pts[i-1].x,bottom),pts[i-1],
                    pts[i],ImVec2(pts[i].x,bottom),fill);'''
new='''        if(opacity>0.0f)
            for(int i=1;i<samples;++i) {
                const int first=draw->VtxBuffer.Size;
                draw->AddQuadFilled(ImVec2(pts[i-1].x,bottom),pts[i-1],
                    pts[i],ImVec2(pts[i].x,bottom),fill);
                ClawVerifyFillAlpha("vertical",style,draw,first);
            }'''
assert s.count(old)==1;s=s.replace(old,new,1)
old='''                        draw->AddQuadFilled(prev, point, ImVec2(point.x,bottom),
                                            ImVec2(prev.x,bottom), fill);'''
new='''                        const int first=draw->VtxBuffer.Size;
                        draw->AddQuadFilled(prev, point, ImVec2(point.x,bottom),
                                            ImVec2(prev.x,bottom), fill);
                        ClawVerifyFillAlpha("horizontal",claw_style,draw,first);'''
assert s.count(old)==1;s=s.replace(old,new,1)
p.write_text(s)
