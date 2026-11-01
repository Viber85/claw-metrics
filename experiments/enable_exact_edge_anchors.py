#!/usr/bin/env python3
"""Remove the upstream 10 px implicit position margin in the isolated Claw renderer.

All six supported HUD positions must be measured from the actual ImGui display
edges. The user's offset_x/offset_y are the *only* offsets. This modifies no
system-wide MangoHud binary, and does not affect unrelated rendering geometry.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else "src")
path = root / "overlay.cpp"
source = path.read_text()

before = """   float margin = 10.0f;
   if (params.offset_x > 0 || params.offset_y > 0 || params.enabled[OVERLAY_PARAM_ENABLED_hud_no_margin])
      margin = 0.0f;"""
after = """   // Claw edge anchors: no hidden 10px MangoHud fallback. Exact screen
   // coordinates are determined only by the explicitly configured offsets.
   const float margin = 0.0f;"""

if source.count(before) != 1:
    raise RuntimeError(
        f"Expected exactly one original MangoHud position margin, got {source.count(before)}"
    )
source = source.replace(before, after, 1)
assert "const float margin = 0.0f;" in source
assert "margin + params.offset_y" in source  # Top corner/center uses margin=0.
assert "window_size.y - margin + params.offset_y" in source  # Bottom edge.
assert "params.claw_center_horizontal" in source  # Custom centered anchors.
path.write_text(source)
print("Claw screen-edge anchors have no implicit top/bottom margin")
