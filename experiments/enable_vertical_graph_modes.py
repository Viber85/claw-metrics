#!/usr/bin/env python3
"""Add two distinct native Vertical Stacked frametime graph modes.

Style 4 Smooth Curve uses bounded Catmull-Rom interpolation of actual
frametime measurements. Style 5 Dual Layer adds an independently calculated
5-sample moving-average trend, transparent local-variation band, plus
the same smoothed foreground curve. Style IDs 0-3 and the horizontal path
remain unchanged. Apply after enable_vertical_stacked.py.
"""
from pathlib import Path
import sys

root=Path(sys.argv[1] if len(sys.argv)>1 else "src")
path=root/"hud_elements.cpp"
s=path.read_text()
start=s.index("static void ClawVerticalGraph() {")
end=s.index("\nvoid HudElements::frame_timing(){",start)
old=s[start:end]
if old.count("const int style=ImClamp(p->claw_graph_style,0,3);")!=1:
    raise RuntimeError("Vertical graph mode clamp drift")
old=old.replace("const int style=ImClamp(p->claw_graph_style,0,3);",
                "const int style=ImClamp(p->claw_graph_style,0,5);")
needle="    if(style==2) {"
if old.count(needle)!=1: raise RuntimeError("Vertical graph histogram branch drift")
new=r"""
    if(style==4 || style==5) {
        // Smooth, bounded Catmull-Rom interpolation. Actual data points are
        // preserved and spline overshoot is prevented at every interval.
        constexpr int subdivisions=4;
        ImVec2 smooth[(samples-1)*subdivisions+1];
        int idx_out=0;
        for(int i=0;i<samples-1;++i) {
            const ImVec2& p0=pts[i>0?i-1:0];
            const ImVec2& p1=pts[i];
            const ImVec2& p2=pts[i+1];
            const ImVec2& p3=pts[i+2<samples?i+2:samples-1];
            for(int j=0;j<subdivisions;++j) {
                const float t=float(j)/float(subdivisions);
                const float t2=t*t, t3=t2*t;
                const float y=0.5f*((2.0f*p1.y)+(-p0.y+p2.y)*t+
                    (2.0f*p0.y-5.0f*p1.y+4.0f*p2.y-p3.y)*t2+
                    (-p0.y+3.0f*p1.y-3.0f*p2.y+p3.y)*t3);
                smooth[idx_out++]=ImVec2(p1.x+(p2.x-p1.x)*t,
                    ImClamp(y,ImMin(p1.y,p2.y),ImMax(p1.y,p2.y)));
            }
        }
        smooth[idx_out++]=pts[samples-1];
        if(style==5) {
            // Distinct from classic Line+fill: rolling trend and a ribbon
            // around the trend, not a solid fill down to the graph baseline.
            ImVec2 trend[samples];
            for(int i=0;i<samples;++i) {
                float avg=0.0f;
                int n=0;
                for(int k=-2;k<=2;++k) {
                    const int j=i+k;
                    if(j>=0 && j<samples) {avg+=pts[j].y;++n;}
                }
                trend[i]=ImVec2(pts[i].x,avg/float(n));
            }
            const ImU32 band=ImGui::ColorConvertFloat4ToU32(
                ImVec4(col.x,col.y,col.z,col.w*0.13f));
            const ImU32 trendColor=ImGui::ColorConvertFloat4ToU32(
                ImVec4(col.x,col.y,col.z,col.w*0.43f));
            for(int i=1;i<samples;++i) {
                const float r0=ImClamp(ImFabs(pts[i-1].y-trend[i-1].y)+2.0f,2.0f,7.0f);
                const float r1=ImClamp(ImFabs(pts[i].y-trend[i].y)+2.0f,2.0f,7.0f);
                draw->AddQuadFilled(
                    ImVec2(trend[i-1].x,trend[i-1].y-r0),
                    ImVec2(trend[i].x,trend[i].y-r1),
                    ImVec2(trend[i].x,trend[i].y+r1),
                    ImVec2(trend[i-1].x,trend[i-1].y+r0),band);
            }
            draw->AddPolyline(trend,samples,trendColor,false,1.2f);
        }
        draw->AddPolyline(smooth,idx_out,line,false,1.8f);
    } else if(style==2) {"""
old=old.replace(needle,new,1)
s=s[:start]+old+s[end:]
path.write_text(s)
print("Installed native Smooth Curve (4) and Dual Layer (5) for Claw Vertical")
