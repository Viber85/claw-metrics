# Claw Metrics v0.3.0

Decky QAM controls for MSI Claw A8 Z2 Extreme on official SteamOS. Includes an isolated, opt-in native MangoHud fork for 64-bit and 32-bit Vulkan/OpenGL games.

## Custom renderer

- Independent font size for the FPS number in ELEMENTS → FPS. Other text keeps the base font size.
- Horizontal and vertical padding, rounded background, actual measured centering, and X/Y adjustment.
- Fit-to-width scales the entire row only when its measured natural width exceeds the game render width. Relative FPS size is retained. Disable fitting if you want fixed pixel sizes and manage overflow yourself.
- Stock mode remains available; old settings do not automatically activate the native renderer.

The private binaries and font are checksum-verified and copied into ~/.config/ClawMetrics. No OS package, system MangoHud library, SteamOS partition or power limit is modified. See renderer/README.md and shipped MIT/font licenses for source and build details.

## First activation

1. Install the full ZIP and restart Decky Loader.
2. Open CLAW RENDERER and select Claw renderer + izgled prijedloga.
3. Copy the NEW launch command from ACTIVATION into the test game's Steam Launch Options. The old mangohud command loads the system library and cannot enable the new native controls.
4. Restart the game. Keep Steam's native performance overlay off to avoid duplication.
5. Expand ELEMENTS → FPS to change only the FPS number size. APPEARANCE contains padding, centering, fit-to-width and X/Y controls.

To return to stock, disable Koristi Claw renderer and copy the displayed stock launch command back into Steam. The private fork also follows the stock rendering path when its custom-mode setting is off.

## Existing features

Expandable metric groups, per-sensor switches, enabled counts, up/down ordering, hide/restore, opacity, rounding and bundled proportional Claw Sans. Existing top-margin preferences migrate to Y, and order/submetrics are retained. CPU/GPU load are the base Always metrics. VRAM clocks/temperature render in MangoHud's VRAM block and require GPU and VRAM enabled. Frametime milliseconds belong to the FPS block; the graph can be moved separately. GPU sensor availability depends on the hardware.

DRAW samples actual battery discharge power in the Decky host and exposes readable text; it does not require Python in the game runtime. Charging or missing readings display DRAW --. Applied TDP readback from Panel de Control is still unavailable; no fake TDP or power-limit write is made.

## Verification scope

Release gates include Python tests, TypeScript checks, frontend build, stock ImGui fixtures, 64/32-bit native compilation, real software Vulkan rendering, packaged private-launch Vulkan/OpenGL integration, actual FPS draw-font ratios and ZIP contents/version. Test branches do not publish releases. The main branch only publishes after every required job succeeds.

These checks do not replace MSI Claw hardware, real Proton-game, sleep/resume or controller-navigation testing. This is a launch-option renderer, not an automatic Gamescope replacement. Keep the working v0.2.3 package available as a fallback while first testing the new native mode.
