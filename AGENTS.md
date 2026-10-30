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
