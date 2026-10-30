# Claw Metrics v0.2.1

Decky QAM metric controls for MSI Claw A8 Z2 Extreme on official SteamOS.

## Audit fixes in v0.2.1

The full-width HUD now uses zero horizontal offset; only the top margin is adjustable. Battery discharge readings are collected in the Decky host and exposed as text, removing the requirement for Python inside the game runtime. Regression tests include producer lifecycle, permission checks, save/reload persistence, and packaging validation. Final SteamUI navigation, sensor access inside the game sandbox, and actual HUD appearance still require the MSI Claw.

## Elements menu

Expandable groups with per-metric switches, enabled counts, up/down reorder controls, hide (×), and Add Element restore controls. Arrow moves swap with the adjacent visible group and survive restarts. Headers and instructions follow the supplied ELEMENTS / GROUP METRICS reference. Uses Decky focusable buttons for controller navigation. GPU load and CPU load are the base Always metrics within their enabled group.

Supported GPU options: load, temperature, junction temperature, core clock, VRAM clock, VRAM temperature, watts, fan, voltage. These are supported MangoHud options, not a claim that all sensors exist on Z2 Extreme. The photograph only exposes part of its 13-option list; this version exposes nine supported fields rather than inventing unseen controls. VRAM clock and temperature render in MangoHud's VRAM block, which requires GPU and VRAM enabled.

FPS/frametime: milliseconds belong to the FPS block in MangoHud; the Frametime group's graph can be reordered separately. Battery percentage and icon are alternatives in MangoHud; remaining time is retained with the v0.1.5 compact-mode workaround.

## Appearance

Reference-style dark background, green FPS and graph, cyan CPU, green GPU, purple RAM, pink VRAM, colored separators. Apply the reference-style preset with the QAM button: 18 px base text, 80% background, 10 px corner radius, 8 px top offset (horizontal offset is zero to avoid clipping the full-width row). Existing font-size and opacity preferences are retained on upgrade until the preset is applied. Controls include sans-serif font, size, opacity, rounding, and margin. Selects an installed DejaVu Sans using fontconfig, with validated system-path fallback; if none exists MangoHud retains its own font. No font is downloaded or claimed to be an exact identification from the generated mockup.

MangoHud does not expose separate FPS-number sizing in this renderer; the illustration's oversized FPS, exact battery icon/percentage combination, per-subfield separator geometry, and exact pixel proportions are not reproduced. All metrics must fit the game's render width; smaller fonts or fewer sensors may be needed at low resolutions. Horizontal layout does not imply automatic text shrinking.

## DRAW and TDP

DRAW reads actual battery discharge power from sysfs (power_now, or current_now × voltage_now). Shows DRAW -- while charging or without a valid sensor; charging power is never mislabeled as total device consumption. The Decky host backend samples the sensors every two seconds and atomically writes a readable draw.txt; MangoHud reads that text with cat, so games do not need Python installed in their runtime. The sampling task is cancelled on plugin unload. CPU/GPU watts remain separate sensor readings. TDP readback from Panel de Control remains unavailable and is labeled as such; no fake setpoint is displayed or written.

## Install

Download ClawMetrics-v0.2.1.zip from this repository's Releases and install in Decky. Restart Decky Loader, apply the appearance preset if desired, and restart the game. The launch option remains unchanged; keep Steam's native performance overlay off during use. This is still a per-game MangoHud launch-option profile, not a launch-option-free Gamescope integration.

## Validation

Python regression tests cover the compact/battery overlap workaround, migration from v0.1 settings, order sanitization, generated block order, independent defaults, sensor switches, and battery power unit/status handling. TypeScript checking and the frontend build are CI gates. Actual controller navigation, sensor availability, font rendering, and final visual spacing require hardware testing.
