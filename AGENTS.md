# Claw Metrics release checks

The user wants fewer install-and-test cycles. Do not publish a visual change based only on a successful frontend build or generated config strings.

Before publishing a version:
- Run `python -m unittest discover -s tests`, `npm run typecheck`, and `npm run build`.
- For font or layout changes, run `python tools/check_native_layout.py` and inspect the actual ImGui result. The script checks fixture geometry and proportional font loading using the pinned renderer, not the real console.
- Keep the CI native-layout and ZIP-content checks enabled. Wait for successful release packaging and verify that the expected ZIP exists before giving a download link.
- Keep the `hud_compact=0` battery-time workaround. Cover changes with a regression test.
- Package font files and license, verify installed bytes and readable permissions, and avoid relying on host `/usr` font paths from inside a game runtime.
- Preserve existing settings through normalization/migration.
- Explain test scope precisely: mock Decky controls do not verify native controller navigation; ImGui fixtures do not verify Vulkan injection or actual SteamOS appearance. Never call these on-device validation.
- Do not replace working builds with speculative configuration changes just to produce another download. Diagnose against upstream implementation and collect evidence first.

Manual X/Y must use the top-left positioning branch. The native horizontal top-center branch ignores offset_x. Test actual coordinate changes, vertical padding changes, and the compact preset at 1280 px. Never label vertical-only padding as full horizontal/vertical padding or expose a fake independent FPS-font slider.

## Private renderer (v0.3)

Independent FPS size and four-side padding are real features only in the isolated native fork, not stock config. New controls must be disabled when the native bundle/mode is unavailable. Preserve stock fallback and never alter the system MangoHud installation. The custom measured-center branch honors X relative to center; the stock top-left branch retains absolute X/Y.

Release must require both native architectures, actual Vulkan rendering with the FPS draw-font ratio, and the packaged wrapper's Vulkan/OpenGL tests. A rendered frame followed by a crash is a failed test. Develop on renderer-native; do not publish its intermediate test artifacts as a release. One new launch command is required for first activation and must be stated clearly.
