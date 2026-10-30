# Claw Metrics v0.2.2

Decky QAM controls for MSI Claw A8 Z2 Extreme on official SteamOS. Generates a per-game MangoHud profile; the launch option remains necessary.

## Appearance

Content-width horizontal row centered at the top, with a rounded translucent dark background. Native configuration: horizontal_stretch=0, position=top-center, hud_compact=0. Compact mode must remain disabled because MangoHud's battery remaining-time code otherwise resets to column zero and overwrites FPS.

A licensed DejaVu Sans subset, renamed Claw Sans, ships in assets/ClawSans.ttf.gz.b64. The backend decodes it into ~/.config/ClawMetrics/ClawSans.ttf, makes it readable (0644), and verifies its SHA-256. Both font_file settings point to that profile location. There is no fontconfig or host /usr font dependency. QAM shows whether the actual installed bytes passed validation. Attribution/license ships in assets/FONT-LICENSE.txt.

The appearance preset uses 18 px text, 80% background, 10 px corner radius and 8 px top offset. Old size/opacity preferences are preserved until the preset button is pressed. Colors follow the supplied reference: green FPS/graph, cyan CPU, green GPU, purple RAM and pink VRAM. The font is similar to the concept, not an exact identification of its font. Separate oversized FPS, exact icon-plus-percentage combination and exact mockup proportions are not supported by this renderer.

## Elements menu

Expand groups, switch individual metrics, move visible groups using arrows, hide with × and restore with Add Element. Order and options survive restarts. CPU/GPU load are the Always metrics within each enabled group. Nine supported GPU fields are exposed rather than inventing unseen entries from the photograph's 13-option list. Available sensors depend on the hardware. VRAM clock/temperature render in the VRAM block and require both GPU and VRAM enabled. Frametime milliseconds belong to the FPS block; the graph can be moved separately. Battery icon and percentage are alternative render modes.

## DRAW and TDP

The Decky host samples battery discharge power every two seconds and writes readable draw.txt. MangoHud reads that text with cat; games do not need Python. Values use power_now, or current_now × voltage_now with sysfs unit conversion. While charging or without a valid sensor, DRAW -- is shown rather than charging watts mislabeled as total device consumption. The task is cancelled on unload. CPU/GPU watts remain separate sensors. Applied TDP readback from Panel de Control is still unavailable; no fake value or power-limit write is made.

## Installation

Install ClawMetrics-v0.2.2.zip from Releases, restart Decky Loader to install the font and regenerate the profile, then restart the game. Launch options do not change. Select Primijeni izgled prijedloga for the reference-style preset. Keep the system performance overlay disabled to avoid duplication.

## Verification and limits

CI runs Python regressions (migration, order sanitization/persistence, submetrics, compact-mode safeguard, font checksum/readability, background task lifecycle and discharge-power units), TypeScript checking, frontend build and ZIP content/version checks.

CI also compiles a headless ImGui 1.89.9 probe, the ImGui version pinned by MangoHud v0.8.1. It uses the same window positioning, table-sizing, text-drawing, rounding and battery-column traversal with fixture metrics. Full and reduced rows must remain centered, all labels must fit, and the installed font must have proportional glyph advances. Downloaded source files are hash-verified. Locally run: python tools/check_native_layout.py, or supply --imgui-dir with the pinned sources.

The full 1920 px fixture with 18 px font yields a rounded 1604 px row at x=169, y=8, height=32. This is a local renderer check, not a Vulkan injection or device screenshot. Native controller focus, actual game sandbox access, exact SteamOS MangoHud version and device visual appearance still require the Claw. Different metric values, lower game resolutions, larger fonts or excessive sensors can exceed screen width; reduce text size/options in that case. No automatic font shrinking is claimed.
