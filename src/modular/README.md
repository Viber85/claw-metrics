# Decky layout builder

The editor uses a Decky route and a draft. Apply publishes after unmount;
Cancel discards changes. Save style uses the shared main menu slots. Undo/Redo
cover layout and appearance.

Every group and reading, including graphs/separators, has independent horizontal
and vertical padding, 0–160 px and initially zero. Child padding is stored on the
node; the root Overlay retains its layout-level paddingX/paddingY from test.104.
Legacy scalar padding is ignored. Insets affect measured geometry, backgrounds,
anchors, sibling positions and fitted graph content width.

Group outlines have an enable switch, color, width 0–12 px and opacity 0–100%.
They draw inward and do not add layout spacing. Local Overlay outline settings
override the inherited global background outline, including at zero opacity.
Old layouts default to a 1 px #8fb8d9 opaque outline when their switch is enabled.

Position on screen is global and only shown for the root Overlay. Radius remains
0–1000 with a Pill shape shortcut and clamps to the measured shorter side.
Containing row/column gap controls remain separate from element padding.
Native V4 transports insets/outline settings and still decodes V1/V2/V3.

Superscript text uses a shared main baseline; battery state uses the checked
formatter and a vector charger icon. The HTML preview uses simulated readings.
Tests cover schema/style persistence, native geometry, actual glyph/outline
vertices, imported layouts and Vulkan/OpenGL. These are not handheld/controller
focus or QAM stability validation.

FPS value uses a tight digit-ink box. It no longer reserves three digits or
full-em/superscript line height. Fixed digit cells preserve width for values
with the same digit count; 99 to 100 grows the box. The native adapter uses
baked glyph bounds; the editor uses the pinned font's SVG outlines and generated
metrics from tools/generate_fps_metrics.py (fontTools required for regeneration).
Selection outlines follow actual boxes without an added visual offset. Explicit
padding remains independent. Other metrics retain their shared unit baselines.
