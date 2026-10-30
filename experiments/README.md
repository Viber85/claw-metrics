# Experimental horizontal spacing controls (v0.2.3 base)

This experiment **does not replace the working v0.2.3 release**. Do not install it on the MSI Claw until the native renderer has been separately validated.

## Why the controls are gated

Official/stock MangoHud v0.8.1 has hard-coded horizontal values in `src/overlay.cpp`:

- `ImGuiStyleVar_WindowPadding = ImVec2(5, 5)`: 5 px on **both left and right**.
- `ImGuiStyleVar_ItemSpacing = ImVec2(8, -3)`: 8 px horizontal ImGui spacing, affecting separators/adjacent items.

There is no stock `cellpadding_x` or equivalent horizontal spacing parameter in v0.8.1. A proposed upstream PR #1398 exists, but it is not included in this pinned release. Merely writing unsupported config keys would make the sliders placebo controls.

## Prototype

The QAM offers two **disabled** controls pending native verification; additionally, the experimental patched renderer supports narrower internal columns and a shorter graph:

1. **Padding lijevo i desno**: symmetric side padding, 0–24 px, default 5 px.
2. **Razmak između elemenata**: horizontal spacing, 0–20 px, default 8 px.

The unequal blank space is **not** one setting: MangoHud uses fixed 150px frametime plots, 8px horizontal item spacing, 4px table-cell padding, plus separators. The isolated patch adds `claw_table_padding_x` (stock 4px) and `claw_graph_width` (stock 150px) as separate experimental native parameters. A future compact experimental combination would be, for example, graph 110px, item spacing 4px, table-cell padding 2px while preserving all metrics. These are not deployed or user-facing working controls.

Settings are persisted and bounded, but the stock MangoHud config remains identical. There is no change to TDP, Panel de Control, existing game launch commands, or the 0.2.3 release. A separate minimal source patch under `experiments/mangohud-v0.8.1-spacing.patch` defines `claw_padding_x` and `claw_element_gap` parameters for investigation only. A `mango_config(settings, native_spacing=True)` test mode writes them **only** when explicitly requested by tests; normal execution never enables that mode.

## Requirements before enabling sliders

- Build and run native tests for the pinned MangoHud version on both architectures used by SteamOS game processes.
- Verify overlay launches in an actual game without the Steam loading-logo hang seen with v0.3.0.
- Confirm both slider values have measurable independent visual effects, without breaking the frametime graph, battery-time line, text glyphs, or other QAM controls.
- Confirm fallback to stock MangoHud when the native renderer is unavailable.
- Only then wire `layout_spacing_supported: true` and publish an installable release.

### Source references

- https://github.com/flightlessmango/MangoHud/blob/v0.8.1/src/overlay.cpp
- https://github.com/flightlessmango/MangoHud/pull/1398

This is development work only and should not be described as a completed functional QAM feature.
