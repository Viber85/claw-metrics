# Claw Metrics v0.2.4-test.6 — gamepad color editor

Based on the verified working `v0.2.4-test.5` layout. Keeps the one-line overlay, inner spacing controls, bold FPS, the explicit Vulkan launch path, and all sensor options.

## What's new

The **BOJE / COLORS** section in Decky QAM includes a controller-operated color picker (hue, saturation, lightness) for:
- Numeric values / clock / DRAW (shared `text_color`)
- Vertical separators between categories (**independent** from VRAM)
- FPS label and FPS number (separate controls)
- CPU, GPU, RAM, VRAM and BATT category labels
- Frametime graph

The existing defaults are kept as the initial palette. Values are saved as six-digit RGB colors, validated in Python, and applied to both MangoHud configs. `Vrati zadane boje` resets **only** the colors.

**Technical compatibility:** stock MangoHud 0.8.1 draws separators with `params.vram_color`. The experimental native patch changes that to a new `horizontal_separator_color` parameter, making independent separator customization work; stock MangoHud will still tie separator color to VRAM. This test is for our **experimental Vulkan** launch command.

## Test

Install the Decky ZIP, restart Decky if needed, launch a 64-bit Vulkan game with the experimental command, and confirm renderer status **AKTIVNO**. In QAM, open **BOJE / COLORS**, choose a color, move the HSL sliders and confirm. The game overlay should update without restarting, as in the preceding test. Try separator bright red and VRAM label green to verify the colors are independent; then restore default colors. Changes outside a running game are persisted for next launch.

If color changes do not refresh automatically in your game, re-open the overlay or restart that game. Do not change system MangoHud, OS files or Panel de Control settings.

**Status:** compiled in CI, not yet device-tested for the color editor. The confirmed functional prior `v0.2.4-test.5` release remains available.

---

# Claw Metrics v0.2.4-test.5 — uniform spacing across ALL metric groups

Built from the working `v0.2.3` baseline; retains the working experimental Vulkan layer integration confirmed on the MSI Claw in v0.2.4-test.3.

Changes compared with test.4:
- The **FPS** label, number and frametime in ms now use one group with equal interior spacing.
- **RAM**, **VRAM** and **BATT** use the same single-cell layout as the now-working CPU and GPU blocks.
- **DRAW** and **time** are already single-text cells; their inter-group spacing is controlled by existing horizontal gap settings.
- The numeric FPS value is drawn with additional left/right strokes (+/-1.1 px and +1.8 px) without increasing font size. This is faux-bold, not a distinct bold font. The prior +0.8 px stroke was too subtle.
- All functionality remains in **one horizontal line**. Existing QAM sliders and normal MangoHud fallback are preserved.

## How to compare
Install the ZIP in Decky, use the newly copied experimental Vulkan launch command, keep the SteamOS overlay disabled. Confirm renderer diagnostic `AKTIVNO`. Turn on `Jednaki razmaci: FPS, CPU, GPU, RAM, VRAM, BATT`; adjust `Razmak unutar grupa` to 3–5 px; toggle `Podebljani FPS broj` and compare just the numerical FPS. Changes should appear live as in the last hardware test. If text clips or any metric disappears, turn off the compact setting or restore v0.2.3 command.

This version has **not** been device-tested. GitHub compilation passing is not sufficient proof of on-device behavior.

---

# Claw Metrics v0.2.4-test.4 — uniform inline CPU/GPU + bold FPS

This experimental version changes **only the custom renderer**. It retains one single horizontal row, all existing metrics, and the known-working Vulkan launch integration from test.3.

- The CPU/GPU sections use the same adjustable **inner gap** between label, load, temperature, clock and power. They are no longer separate right-aligned four-character-wide table cells.
- `Razmak unutar CPU/GPU (px)` (0–16 px, default 4 px) controls that gap.
- `CPU/GPU vrijednosti u jednom redu` toggles the custom layout on/off for comparison.
- `Podebljani FPS broj` makes the **numeric FPS** slightly bolder by drawing an additional subpixel stroke. **Font size does not change.** This is faux-bold, not a separate bold font.
- The current FPS* label is the temporary experimental-config diagnostic.
- The four previous spacing controls remain. Stock MangoHud and Panel de Control are left unchanged.

## Test steps

Install this version and use the **experimental Vulkan 64-bit launch command** in a single game. Keep the built-in SteamOS performance overlay off. While the game runs, verify `AKTIVNO` under renderer diagnostics. Compare CPU/GPU with `CPU/GPU vrijednosti u jednom redu` off/on; adjust `Razmak unutar CPU/GPU` between 2 and 10 px. Toggle `Podebljani FPS broj` to compare. Other metrics should stay in the same single top row.

This native change is CI compiled but has **not** been tested yet on your MSI Claw hardware. Keep the working v0.2.3 for rollback.

---

# Claw Metrics v0.2.4-test.3 — Vulkan layer diagnostic

The previous test reported NIJE AKTIVNO on MSI Claw A8 / official SteamOS despite using the experimental launch command. This release is a **diagnostic experiment, not a confirmed fix**.

Changes:
- Custom Vulkan explicit layer uses a **unique layer name** `VK_LAYER_CLAW_METRICS_overlay_x86_64`, rather than colliding with system MangoHud.
- Install a discoverable but inactive-by-default JSON manifest at `~/.local/share/vulkan/explicit_layer.d/ClawMetrics.test3.x86_64.json`. The manifest does not automatically load the layer for other games; it needs the launch option. This is a user-level file, not a modification of Valve's OS files.
- Launch command requests the custom layer and sets `DISABLE_MANGOHUD=1` to prevent interference from system MangoHud.
- Diagnostics scan process library mappings and selected environment variables. No process command lines, passwords, or raw environment strings are shown.
- Existing stock v0.2.3 configuration stays unchanged; use its original launch command to revert.

**Testing:** Install v0.2.4-test.3 ZIP, restart Decky, copy the newly generated EXPERIMENTAL launch command (do not reuse the command from test.2), replace all launch options for one 64-bit Vulkan game, and relaunch the game. While running, select **Provjeri koristi li igra eksperimentalni renderer**. Read the counts:
- `native` > 0: our library was loaded.
- `zahtjev za slojem` > 0 and `native` = 0: environment reached a process but the library did not load.
- `testni config` > 0 but `zahtjev za slojem` = 0: game got config but not Vulkan request.
- Both zero: command may not have reached game, or process inspection is restricted. Do not claim a specific cause without more data.
- `manifest` = NE: on-disk manifest was not created/accessible.

The Vulkan layer has been compiled in CI, but its behavior with Proton/Steam Runtime on MSI Claw still requires hardware confirmation.

---

# Claw Metrics v0.2.4-test.2 (experimental SteamOS Vulkan injection)

**This is NOT a stable replacement for v0.2.3.**

The v0.2.4-test.1 layer was generated with implicit-layer enable/disable fields but was searched through `VK_LAYER_PATH` (an explicit layer path), so QAM controls could save values without the customized library actually loading. v0.2.4-test.2 removes those implicit fields and uses an explicitly requested Vulkan layer with `VK_ADD_LAYER_PATH` to avoid overriding other system layer search paths.

**How to test**: install the test.2 ZIP through Decky, restart Decky, enable the game-specific experimental launch option from the QAM *Activation* section, and fully restart a **64-bit Vulkan game**. Do not append the old `mangohud %command%` command. Keep SteamOS performance overlay off. Set graph width to 80, then 180 (or change gap) and restart the game between tests. If a value changes visually, the experimental renderer is working.

Two diagnostics:
- `FPS*` in the overlay proves the game read **our experimental config**. It does NOT by itself prove the modified library was loaded.
- With the game running, open QAM and press **Provjeri koristi li igra eksperimentalni renderer**. Only `AKTIVNO` means the modified `native64/libMangoHud.so` was found in the process map.

If it shows `NIJE AKTIVNO`, this might be due to the game using a 32-bit Vulkan runtime, a sandboxed path, or another layer taking precedence. If the game refuses to start, replace the launch option with the original v0.2.3 command. The stable MangoHud and Panel de Control are not changed.

## Original v0.2.3 documentation

# Claw Metrics v0.2.3

Decky QAM controls for MSI Claw A8 Z2 Extreme on official SteamOS. Generates a per-game MangoHud profile; the launch option remains necessary.

## Appearance

Content-width horizontal row with a rounded translucent dark background and manual X/Y placement. Configuration uses horizontal_stretch=0, position=top-left and explicit offset_x/offset_y. Native top-center's horizontal branch ignores offset_x, so manual placement deliberately uses top-left. X/Y are measured from the left/top edges, not as offsets from the center. Existing top-margin settings migrate to Y; default X is 8 px.

Extra vertical padding is expressed in pixels and mapped to cellpadding_y using the font size, so its effect is independent of the chosen text size. MangoHud still adds its fixed 5 px window padding. Horizontal window padding is hard-coded in this renderer and is not exposed as a working control. Keep hud_compact=0 to prevent the battery-time overwrite bug.

A licensed DejaVu Sans subset, renamed Claw Sans, ships in assets/ClawSans.ttf.gz.b64. The backend decodes it into ~/.config/ClawMetrics/ClawSans.ttf, makes it readable (0644), and verifies its SHA-256. Both font_file settings point to that profile location. There is no fontconfig or host /usr font dependency. QAM shows whether the actual installed bytes passed validation. Attribution/license ships in assets/FONT-LICENSE.txt.

The appearance preset uses 18 px text, 80% background, 10 px corner radius, X=8/Y=8 and 8 px extra vertical padding. Old size/opacity preferences are preserved until the preset button is pressed. Colors follow the supplied reference: green FPS/graph, cyan CPU, green GPU, purple RAM and pink VRAM. The font is similar to the concept, not an exact identification of its font. Separate oversized FPS, exact icon-plus-percentage combination and exact mockup proportions are not supported by this renderer.

## Elements menu

Expand groups, switch individual metrics, move visible groups using arrows, hide with × and restore with Add Element. Order and options survive restarts. CPU/GPU load are the Always metrics within each enabled group. Nine supported GPU fields are exposed rather than inventing unseen entries from the photograph's 13-option list. Available sensors depend on the hardware. VRAM clock/temperature render in the VRAM block and require both GPU and VRAM enabled. Frametime milliseconds belong to the FPS block; the graph can be moved separately. Battery icon and percentage are alternative render modes.

## DRAW and TDP

The Decky host samples battery discharge power every two seconds and writes readable draw.txt. MangoHud reads that text with cat; games do not need Python. Values use power_now, or current_now × voltage_now with sysfs unit conversion. While charging or without a valid sensor, DRAW -- is shown rather than charging watts mislabeled as total device consumption. The task is cancelled on unload. CPU/GPU watts remain separate sensors. Applied TDP readback from Panel de Control is still unavailable; no fake value or power-limit write is made.

## Installation

Install ClawMetrics-v0.2.3.zip from Releases, restart Decky Loader to install the font and regenerate the profile, then restart the game. Launch options do not change. Select Primijeni izgled prijedloga for the reference-style preset. Keep the system performance overlay disabled to avoid duplication.

## Verification and limits

CI runs Python regressions (migration, order sanitization/persistence, submetrics, compact-mode safeguard, font checksum/readability, background task lifecycle and discharge-power units), TypeScript checking, frontend build and ZIP content/version checks.

CI also compiles a headless ImGui 1.89.9 probe, the ImGui version pinned by MangoHud v0.8.1. It uses the same window positioning, table-sizing, text-drawing, rounding and battery-column traversal with fixture metrics. Manual coordinates must match the configured X/Y, increasing padding must increase the background height, labels must fit, and the installed font must have proportional glyph advances. Downloaded source files are hash-verified. Locally run: python tools/check_native_layout.py, or supply --imgui-dir with the pinned sources.

The fixture covers default and reduced rows, explicit X/Y movement, zero/default/maximum vertical padding and a compact preset at 1280 px. A manual-position reset restores X=8/Y=8 without changing other options. The compact-preset button is explicitly labeled Uži red: manji font i bez MHz. It uses a 12 px font, X=8/Y=8, 4 px extra vertical padding, and disables CPU/GPU clock submetrics to retain headroom at 1280 px. Other submetric preferences are preserved. This is a local renderer check, not a Vulkan injection or device screenshot. Native controller focus, actual game sandbox access, exact SteamOS MangoHud version and device visual appearance still require the Claw. Different metric values, lower game resolutions, larger fonts or excessive sensors can exceed screen width; reduce text size/options in that case. No automatic font shrinking is claimed. Moving a row cannot make a row that is wider than the game fit; use the compact preset or disable optional sensors in that case. Independent FPS size would require changes to the native renderer, not another config slider.
