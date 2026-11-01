#!/usr/bin/env python3
"""Add native Smooth Curve and Dual Layer frametime graphs to Horizontal.

Run after enable_frametime_graph_styles.py and all other native HUD patches.
Keep existing Line/Area/Bars/Line+fill and Vertical graph code untouched.
"""
from pathlib import Path
import sys
p=Path(sys.argv[1] if len(sys.argv)>1 else "src")/"hud_elements.cpp"
s=p.read_text()
anchor="""            } else if (HUDElements.params->enabled[OVERLAY_PARAM_ENABLED_histogram]
                       && !(HUDElements.params->enabled[OVERLAY_PARAM_ENABLED_horizontal]
                            && claw_style == 0)) {"""
if s.count(anchor)!=1: raise RuntimeError(f"horizontal graph patch anchor {s.count(anchor)}")
block=r"""            } else if (HUDElements.params->enabled[OVERLAY_PARAM_ENABLED_horizontal]
                       && (claw_style == 4 || claw_style == 5)) {
                const float w=ImMax(8.0f,ImMin(width,ImGui::GetContentRegionAvail().x));
                const float h=ImMax(6.0f,height-3.0f);
                const ImVec2 origin=ImGui::GetCursorScreenPos();
                ImGui::InvisibleButton("##claw_frametime_smooth",ImVec2(w,h));
                constexpr int samples=48;
                const int count=ARRAY_SIZE(HUDElements.sw_stats->frames_stats);
                if(count>=2) {
                    const double safe_min=std::isfinite(min_time)?min_time:0.0;
                    const double safe_max=std::isfinite(max_time)&&max_time>safe_min
                        ?max_time:safe_min+50.0;
                    const double range=ImMax(0.001,safe_max-safe_min);
                    ImVec2 pts[samples];
                    for(int i=0;i<samples;++i) {
                        const int sample_index=i*(count-1)/(samples-1);
                        const double raw=get_time_stat(HUDElements.sw_stats,sample_index);
                        const double value=std::isfinite(raw)?raw:safe_min;
                        const float y=ImClamp(float((value-safe_min)/range),0.0f,1.0f);
                        pts[i]=ImVec2(origin.x+w*float(i)/float(samples-1),
                                      origin.y+h-y*h);
                    }
                    constexpr int divisions=4;
                    ImVec2 smooth[(samples-1)*divisions+1];
                    int out=0;
                    for(int i=0;i<samples-1;++i) {
                        const ImVec2& p0=pts[i>0?i-1:0];
                        const ImVec2& p1=pts[i];
                        const ImVec2& p2=pts[i+1];
                        const ImVec2& p3=pts[i+2<samples?i+2:samples-1];
                        for(int j=0;j<divisions;++j) {
                            const float t=float(j)/float(divisions),t2=t*t,t3=t2*t;
                            const float cy=0.5f*(2.0f*p1.y+(-p0.y+p2.y)*t+
                                (2.0f*p0.y-5.0f*p1.y+4.0f*p2.y-p3.y)*t2+
                                (-p0.y+3.0f*p1.y-3.0f*p2.y+p3.y)*t3);
                            smooth[out++]=ImVec2(p1.x+(p2.x-p1.x)*t,
                                ImClamp(cy,ImMin(p1.y,p2.y),ImMax(p1.y,p2.y)));
                        }
                    }
                    smooth[out++]=pts[samples-1];
                    ImDrawList* draw=ImGui::GetWindowDrawList();
                    const ImVec4 col=HUDElements.colors.frametime;
                    const ImU32 stroke=ImGui::ColorConvertFloat4ToU32(col);
                    draw->PushClipRect(origin,ImVec2(origin.x+w,origin.y+h),true);
                    if(claw_style==5) {
                        ImVec2 trend[samples];
                        for(int i=0;i<samples;++i) {
                            float sum=0.0f;int n=0;
                            for(int k=-2;k<=2;++k) {
                                const int j=i+k;
                                if(j>=0 && j<samples) {sum+=pts[j].y;++n;}
                            }
                            trend[i]=ImVec2(pts[i].x,sum/float(n));
                        }
                        const ImU32 ribbon=ImGui::ColorConvertFloat4ToU32(
                            ImVec4(col.x,col.y,col.z,col.w*0.13f));
                        const ImU32 trendInk=ImGui::ColorConvertFloat4ToU32(
                            ImVec4(col.x,col.y,col.z,col.w*0.43f));
                        for(int i=1;i<samples;++i) {
                            const float r0=ImClamp(ImFabs(pts[i-1].y-trend[i-1].y)+2.0f,2.0f,7.0f);
                            const float r1=ImClamp(ImFabs(pts[i].y-trend[i].y)+2.0f,2.0f,7.0f);
                            draw->AddQuadFilled(
                                ImVec2(trend[i-1].x,trend[i-1].y-r0),
                                ImVec2(trend[i].x,trend[i].y-r1),
                                ImVec2(trend[i].x,trend[i].y+r1),
                                ImVec2(trend[i-1].x,trend[i-1].y+r0),ribbon);
                        }
                        draw->AddPolyline(trend,samples,trendInk,false,1.1f);
                    }
                    draw->AddPolyline(smooth,out,stroke,false,1.7f);
                    draw->PopClipRect();
                }
"""
s=s.replace(anchor,block+anchor,1)
p.write_text(s)
print("Enabled native horizontal Smooth Curve and Dual Layer")
