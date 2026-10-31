# Claw Metrics v0.2.4-test.17 — TDP configured setpoint and normal text size

- TDP probes RyzenAdj from the real Decky plugin directory **Panel de Control/bin/ryzenadj** (with spaces), checks additional installed locations, and reads a valid STAPM row even when an unrelated RyzenAdj probe exits nonzero.
- If hardware readback is blocked by official SteamOS, it can read Panel de Control's persisted **configured global TDP** from `tdp_profiles.json` (read-only). The Advanced screen reports that a configured setpoint is **not hardware verified**. It refuses that fallback for Auto TDP and conflicting per-game overrides.
- The native 1-line HUD now renders TDP and DRAW at the same normal font size as other metric groups; each retains its own token color and font-weight overrides.
- No power limits are written. DRAW continues to show measured system battery discharge, not an APU-only estimate. Test.16 SteamOS TextField keyboard fix and compact layout are included.
- This version requires device validation on official SteamOS. A running game reporting no TDP can mean no usable hardware readback and no unambiguous configured PDC profile.

---

# Claw Metrics v0.2.4-test.16 — SteamOS virtual keyboard fix (experimental)

The Rename Metric modal now uses Decky's Steam-native `TextField` rather than a raw browser `<input>`. In Game Mode, highlight "Naziv stavke" and press A to invoke the SteamOS text keyboard. The built-in focus behavior is used rather than DOM `autoFocus` or unsupported keyboard APIs. Renaming stays limited to 24 characters; Confirm, Cancel, and Restore Default keep their prior behavior.

The test.15 compact three-column layout and the existing custom MangoHud/TDP/DRAW renderer are unchanged.

This was compiled/tested in CI. Game Mode virtual keyboard behavior on MSI Claw A8 must be confirmed on the handheld.

---

# Claw Metrics v0.2.4-test.15 — Decky Game Mode compact UI

UI-only prerelease based on v0.2.4-test.14 (official SteamOS, MSI Claw A8 Z2 Extreme).

- **Colors & Font:** style categories and global colors now display in 3 columns with reduced 13–15px icons and smaller padding, so 11 categories and all colors fit a narrow Decky Quick Access Menu.
- **Metrics:** enabled metrics appear as compact 3-column cards. Selecting a card reveals its original edit, reorder, hide and per-submetric toggle actions in a full-width details panel below. Disabled metrics return via compact "ADD ELEMENT" tiles. Renaming, state persistence and gamepad focus are retained.
- Font-weight options use a compact 2x2 grid to prevent overflow. Saved style slots and advanced style controls remain present.
- No changes to the modified MangoHud Vulkan renderer, Decky Python backend, TDP read-only sampling or battery DRAW telemetry. Existing launch option stays the same.

The layout must be checked on the actual SteamOS Decky panel. If any focus or functionality regression occurs, reinstall test.14 from its release.

---

# Claw Metrics v0.2.4-test.14 — read-only TDP and DRAW

- Optional **TDP** metric: sustained APU limit from `ryzenadj -i` STAPM readback on official SteamOS or MSI firmware PL1 if exposed. Never invokes writes and never guesses an unavailable limit. Displays `TDP --` if neither source is readable.
- **DRAW** remains whole-device battery-discharge telemetry from battery sensors, not APU power. DRAW becomes `--` while charging or on AC because total wall draw cannot be reliably derived from the battery sensor.
- Both are separate groups in Metrics, independently ordered and colored in Colors & Font. TDP starts off for existing installs: enable with **Metrics → ADD ELEMENT → TDP**; position it as desired near DRAW.
- Advanced → Provjeri TDP očitanje reports the current source. If kernel blocks RyzenAdj information, the display cannot promise a number.
- Read-only sensor sampling runs on the Decky backend, not inside games. The native modified Vulkan MangoHud renderer and test.13 layout are preserved.

Linux/CI checks do not prove hardware TDP readback or Proton behavior. SteamOS MSI Claw A8 verification needed. Roll back to test.13 if anything regresses.

---

# Claw Metrics v0.2.4-test.13 — Claw DevLab sync (experimental)

Source: `ikorljan-droid/claw-devlab` main commit `9acb36c6ab1b3e3d3a866f6dc09ff0eaf548431e` (2026-10-31).

Imports the current DevLab Decky QAM UI: named metrics, global font weight clearing manual overrides, palette changes clearing related manual colors, separate Clock/DRAW/Values categories, active style marker, and full visual style presets including font size, position, padding and spacing.

The backend now normalizes/persists the new settings and migrates older color/preset configurations. Native modified MangoHud keeps its Vulkan renderer, implements custom RAM/VRAM/Battery labels and maps the Clock and DRAW appearance independently; FPS/CPU/GPU labels use existing MangoHud config parameters. DRAW is still host-sampled battery discharge, not APU TDP.

**Compatibility:** This is a separate prerelease, not a change to SteamOS MangoHud. The overlay is an opt-in experiment with the same short Steam launch option as test.12. Native Game Mode/Proton results must be checked on the MSI Claw A8; browser preview and CI alone do not establish compatibility. Use test.12 to roll back.

---

# v0.2.4-test.12 — stability only

The short launcher now publishes executable content atomically and avoids rewriting itself when already valid. If the renderer library, Vulkan manifest or custom HUD configuration is missing during an update, it launches the game normally without the custom HUD. It does not try to inject or fix an incompatible present layer. No TDP additions, SteamOS native integrations or native renderer changes in this build.

---
# Claw Metrics v0.2.4-test.11 — short launcher for experimental Vulkan

This is a minimal follow-up to test.10. The custom Vulkan renderer, font atlas, metric styles and QAM visuals have not changed. A small POSIX shell launcher is now written automatically to the persistent user config directory at startup (and regenerated after settings updates), with executable permissions. The launcher exports **exactly the same** `VK_ADD_LAYER_PATH`, `VK_INSTANCE_LAYERS`, `DISABLE_MANGOHUD` and `MANGOHUD_CONFIGFILE` variables as the long experimental command, then uses `exec "$@"` to start the Steam game without changing its arguments or exit status.

**Use:** Open **Activation**, copy **Kratka testna komanda**, and paste it into the Steam Launch Options for a selected game. The command is an absolute path such as `/home/deck/.config/ClawMetrics/claw-metrics %command%`; this avoids relying on an uncertain Game Mode `PATH` and remains valid when Decky updates the plugin files. The old full-length experimental command remains available behind **Prikaži dugu rezervnu komandu**, and the standard stock MangoHud command is unchanged.

This does not automatically inject the overlay into every game. It is still **opt-in 64-bit Vulkan experimental support**; check **Provjeri koristi li igra eksperimentalni renderer** while playing. If a game fails to launch, revert its Steam Launch Options to the previous working command. Tests in GitHub Actions verify POSIX-shell delegation, environment variables, paths with whitespace/quotes, executable permissions and fallback. Actual SteamOS Game Mode/Proton compatibility still requires an on-device test.

---

# Claw Metrics v0.2.4-test.10 — individual typography and persistent QAM navigation

This experimental build preserves the exact QAM design from v0.2.4-test.9: dark blue cards, cyan active border, purple inactive accents, and six collapsible sections. The existing one-row Claw Metrics overlay, Vulkan launch method, Barlow Semi Condensed fonts, metrics and slider settings remain unchanged by default.

## Navigation correction

Decky can remount the React plugin panel when a setting is saved. The expanded QAM section, current metric submenu, and selected Colors & Font category now survive a remount while the plugin remains loaded. The Colors & Font tab does not jump back to Metrics after every edit.

## Colors & Font

Within the existing **Colors & Font** accordion there are compact tabs:
- **Global**: current default font, separator/label/value colors, FPS Bold toggle, three independent style-preset slots
- **FPS**: FPS label, FPS number and frametime in ms
- **CPU**: label, load, temperature, clock, power
- **GPU**: label, load, temperature, clock, power, junction, fan and voltage (where supported)
- **RAM**: label and GiB usage
- **VRAM**: label, usage, temperature and clock
- **Battery**: label, percent/icon, remaining time and watts
- **Clock**: time value

Each supported text token has a font-weight action that cycles **Global → Light → Regular → SemiBold → Bold → Global**. The same token may optionally override its inherited text color via the opaque-only HSL picker; **Vrati** removes that override. Text defaults to **Global**, preserving the user-tested look until deliberately changed. The three style slots each save/reload the complete palette and weight overrides.

### Native renderer

New experimental MangoHud configuration keys `claw_weight_map` (one character per token) and `claw_color_map` (opaque hex RGB or inherit for each token) drive actual ImGui font push/pop and token colors in the custom **64-bit Vulkan** renderer. The four bundled Barlow font weights are loaded into the font atlas. No changes are made to system MangoHud, Panel de Control, or the stable v0.2.3 release. DRAW (battery discharge read from an external command) and native frametime graph plotting use the existing **global** text/graph controls, not individual text-font overrides.

On-game font weight changes might need a game restart if the font atlas has not refreshed. Color changes should follow the existing live settings path. This release requires on-device verification before declaring these new renderer paths stable.

## Suggested Claw smoke test

Install as a test over the Decky plugin. Open **Colors & Font → CPU**, change `Temperatura` to SemiBold and its color, and verify the CPU temperature changes without affecting load, clock or GPU. Then open **GPU**, change the temperature to Light and check it stays open during save. Finally save Style 1, make a change and restore Style 1. Confirm that all metrics remain on one row and unchanged when overrides return to Global. If the game fails to start or text disappears, return to the previous working v0.2.4-test.9 package.

---

# Claw Metrics v0.2.4-test.9 — grouped QAM redesign

**UI-only changes based on the user-tested v0.2.4-test.8 native renderer.** All existing overlay functionality, the one-line HUD, fonts, metric preferences, colors, copyable launch commands and diagnostic functions are retained.

The Decky QAM now displays six controller-accessible, collapsible icon cards. Only one top-level card opens at once; **Metrics** opens by default:

1. **Overlay** — enable/disable and backend status
2. **Layout** — x/y position, text size, graph width, padding, separation and compact presets
3. **Metrics** — metric visibility, in-group switches, reorder buttons, hide/restore groups
4. **Colors & Font** — fully opaque HSL color picker, reset palette, Barlow Semi Condensed Light / Regular / SemiBold / Bold and FPS Bold
5. **Activation** — Steam launch options and one-click copying for normal/experimental Vulkan commands
6. **Advanced** — renderer diagnostics, unavailable TDP readback notice, battery DRAW notes and reconnect

The cards are styled with a restrained dark blue background, cyan accents for the open card and purple accents when collapsed; icons use packaged react-icons (no network dependency). Each heading is a Decky `DialogButton` for gamepad focus and selection.

No new backend calls, new sensors, live overlay renderer changes, TDP integrations, OS modifications or launch command changes were introduced by this UI update. Users can return to v0.2.4-test.8 directly if the QAM layout does not work well on their MSI Claw A8.

## Suggested smoke test on MSI Claw

Open the Decky plugin, switch between each card and verify only the chosen card is expanded. In **Metrics**, reorder CPU/GPU and change a sensor toggle, then restore it. Under **Colors & Font**, change a separator color and switch Regular/SemiBold. Under **Activation**, check that the experimental launch option can still be copied. Finally, make sure the in-game HUD remains on one line, with no changes to the saved profile.

---

# Claw Metrics v0.2.4-test.8 — four offline font weights and alpha-safe colors

This test build retains the working v0.2.4-test.7 Vulkan renderer, single-row overlay, all sensors, all spacing controls and separate separator-color configuration.

**Font weights**: Barlow Semi Condensed Light 300, Regular 400, SemiBold 600, Bold 700. The user-provided four files were inspected to verify the intended font family and weight variants. The release build fetches corresponding licensed official Google Fonts binaries at an immutable revision, validates Git blob hashes, and includes their OFL license in the plugin assets. They are the same family and weights but not guaranteed byte-identical to the four supplied files. The actual installed MSI Claw requires **no internet for font loading**. The plugin installs them from its assets on startup and verifies them. Existing settings are preserved and normal font preference defaults to Regular; FPS may use real Bold separately. Previous Claw Sans remains as a fallback if packaged assets are missing or damaged.

**Color picker fix:** The built-in Decky picker exposed an Alpha slider although the plugin only stores 24-bit RGB. A custom QAM picker now offers only Hue, Saturation and Lightness and always uses fully opaque color. This avoids the unused alpha control implicated in the game's crash report; its safety in live games still needs confirmation on the user's MSI Claw.

**Testing:** Install the new ZIP through Decky and restart Decky. Confirm the Font status shows Barlow Semi Condensed available, then switch between all four weights. Keep the experimental Vulkan launch command used in test.7, or copy the new one from Activation if it changed. While a game runs, test red separator, blue VRAM, and verify other metrics remain stable with the alpha-free picker. If a game crashes or font is missing, restore the last working v0.2.4-test.7.

The existing system MangoHud, stable v0.2.3, and Panel de Control are unchanged.

---

# Claw Metrics v0.2.4-test.7 — separator color and Barlow Semi Condensed

Based on the user-tested v0.2.4-test.6 renderer. The existing single row, metrics, color controls, and spacing options are preserved.

**Fixed**: Separators used a 24-bit RGB configuration color directly as an ImGui draw-list color. Draw-list colors require packed RGBA with an opaque alpha channel. The native fix converts the configured RGB to `IM_COL32(r,g,b,255)`, so separator and VRAM colors remain independent.

**Font**: Replaces the primary Claw Sans look with the slightly narrower, legible **Barlow Semi Condensed** family. QAM Appearance offers Light (300), Regular (400), Bold (700). The FPS Bold option uses the actual Bold font at the same point size, rather than faux-bold, when available. If fonts are unavailable, the existing Claw Sans and faux-bold remain safe fallbacks.

To avoid shipping font files directly, the Decky backend downloads the three weights on initial startup from an immutable Google Fonts revision and verifies the canonical Git blob hash of each file. **Internet access is required on first install.** Once downloaded, the fonts are cached locally and work offline. If Google Fonts is unreachable, the original font remains in use; restarting Decky online retries. Source and license:
- https://github.com/google/fonts/tree/89f5431ff0db41bd2fe3f7ba21a723a01622428b/ofl/barlowsemicondensed
- https://github.com/google/fonts/blob/89f5431ff0db41bd2fe3f7ba21a723a01622428b/ofl/barlowsemicondensed/OFL.txt (SIL Open Font License 1.1)

**Test**: Install the v0.2.4-test.7 ZIP. Restart Decky once online. The QAM Appearance font status should say Barlow Semi Condensed available. Start a 64-bit Vulkan game with the experimental launch command, check renderer ACTIVE, then compare Light/Regular/Bold; restart the game if the font doesn't reload. Next, change separators to red and VRAM label to green. Confirm only separators change. Toggle FPS bold; font size must stay unchanged. Stable v0.2.3 and user-confirmed v0.2.4-test.6 remain published and unchanged.

---

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
