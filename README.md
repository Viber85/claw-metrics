# Claw Metrics v0.1.5 — battery-time overlap fix

Root cause verified in MangoHud v0.8.1 src/hud_elements.cpp, HudElements::battery(): with hud_compact enabled, battery_time calls ImGuiTableSetColumnIndex(0). This overwrites the FPS column and subsequent time output, even with enough table columns. v0.1.5 explicitly sets hud_compact=0 while retaining horizontal mode and remaining battery time. Restart Decky Loader and the game. Visual confirmation on hardware remains required.

# Claw Metrics v0.1.4 — horizontal layout fix

The horizontal HUD now starts with 64 table columns instead of 20. MangoHud automatically measures and reduces the active column count. This prevents multi-column CPU/GPU and battery/time fields from wrapping into the initial FPS cells. Explicit horizontal_stretch keeps the row across the screen. Existing settings are retained; restart Decky and the test game after installing. Hardware visual verification remains required.

# Claw Metrics v0.1.2 — SteamOS experimental prototype

A Decky QAM control panel for a compact MangoHud performance row. Target: **MSI Claw A8 Z2 Extreme running official SteamOS**. This is a prototype: not yet a pixel-perfect replica of the agreed mockup, and **not yet device-tested**.

## v0.1.2 — copy launch command

Added **Kopiraj launch komandu** in the Decky QAM panel below the Steam Launch Options line. The button uses the SteamUI-compatible `document.execCommand("copy")` from a direct click with a `navigator.clipboard.writeText` fallback; a success or error message appears in QAM. This still requires a test in Game Mode on the actual MSI Claw A8.

## v0.1.1 hotfix

Fixed the frontend packaging responsible for `ReferenceError: require is not defined` in QAM by adopting the official `@decky/rollup` pipeline and matching Decky plugin export format (`titleView`). This fixes a known build-time incompatibility; verification on real hardware is still required.

**Do not reinstall v0.1.0** if you saw that error. Download the new v0.1.2 ZIP under Releases once the GitHub Actions build finishes successfully.

## Status

- Decky toggles for FPS/frametime graph, CPU/GPU, RAM, VRAM, battery, sensor power, and clock.
- Generated independent MangoHud configuration: `~/.config/ClawMetrics/MangoHud.conf`.
- **Not implemented yet:** reading the applied TDP setting from Panel de Control; measured *total device* power draw; reliable charge indicator / remaining battery time on every SteamOS build; automatic native Gamescope overlay replacement.
- CPU/GPU power readings are not the same as total device power.
- The compact layout may require adjustments for resolution and displayed measurements.

## SteamOS Game Mode — important

The official SteamOS Game Mode performance overlay is typically implemented by Gamescope/mangoapp and can follow a different configuration path from manually launched MangoHud. **Do not assume that `mangohud %command%` controls the built-in overlay.** First test the generated config with one game and keep the system overlay disabled to avoid duplicate overlays. We will integrate with the native overlay only after checking the MSI Claw A8 SteamOS build.

No changes to sleep/resume, SD card, OS partitions, or kernel settings are made by this plugin. All device power limits remain under **Panel de Control**.

## Installation (experimental)

1. Open the repository's **Actions** tab and choose a successful *Build Decky plugin* run. Download the `ClawMetrics-v0.1.2` artifact.
2. Find the ZIP package inside the artifact. If your Decky Loader version supports install-from-ZIP, install this ZIP using its developer settings; otherwise use the documented Decky plugin development installation procedure.
3. Open Decky QAM → Claw Metrics. Adjust metrics and note the **exact** MangoHud config path and launch option displayed.
4. For a first test, pick one game and only use the launch option shown in QAM if the system's native performance overlay is disabled. Restart the game after changing settings.
5. If Game Mode's Gamescope overlay does not reflect changes, stop here: it means we need a native Gamescope integration, **not** that you should overwrite Valve's global MangoHud files.

**Note:** this build has not been validated against your exact SteamOS version. If the Actions build fails, use the build log to diagnose before installing. Do not assume an artifact is available until the build is green.

## Safety and development

This plugin only generates files under `~/.config/ClawMetrics`; it does **not** set TDP and does not edit Panel de Control settings. Next: validate installation and Gamescope integration on official SteamOS, then add the exact one-line styling and device-specific sensors.
