# Modular renderer — experimental development

Base: Claw Metrics test.72. DevLab model: Viber85/claw-devlab commit 4aad44fab8d00beaab47f0d65427e53cca93b8b2. This directory is an isolated development path. There is no new user-facing mode, configuration output, launch change or replacement release.

## Implemented

- Strict Python reader for the existing `claw-modular-layout` v1 document. Preserves every supported property, rejects malformed trees, duplicate IDs, unknown tokens, non-finite numeric values, and more than 96 nodes / 8 nesting levels. Unknown fields are dropped. Documents over 1 MiB are rejected before parsing.
- Two real DevLab-generated starter documents: Two rows and Graph focus.
- Header-only C++14 native geometry engine with no ImGui/Vulkan/global HUD dependency. Its input is a fully assembled immutable tree. It measures text through a callback at the effective font size, then positions the tree in a second pass. Font scaling is inherited through groups. Pixel gaps/padding and graph dimensions match the current DevLab CSS/SVG contract, rather than scaling with font size.
- All six anchors, horizontal adjustment from center, cross-axis alignment, hidden-node exclusion, nested rows/columns and explicit overflow detection. Oversized layouts are not silently distorted; the eventual renderer must clip them to the viewport.
- Complete structural validation, including hidden branches, repeated parents/cycles, unreachable nodes and invalid measurement results.

## Validation and limits

`python -m unittest discover -s tests` checks DevLab document compatibility and existing backend behavior. `python tools/check_modular_layout.py` compiles and exercises the actual geometry header with AddressSanitizer/UndefinedBehaviorSanitizer. The fixture uses deterministic text sizes, not an ImGui font or real game. Passing geometry tests does not establish rendering parity, Vulkan injection, gamepad behavior or stability on the device.

## Next stages

1. Wire the validated transport and immutable exchange into an explicitly experimental native activation path.
2. Connect the ImGui adapter to production token formatting, numerical-width policy and font selection. Maintain rendered fixtures at 1280x800 and 1920x1080 before exposing the mode.
3. Load validated snapshots outside live mutation paths; only swap the complete layout on the renderer thread between frames. Never let the watcher mutate groups or font resources in place.
4. Add background/outline and graph rendering within measured node rectangles. Match alpha and sRGB behavior of the working renderer.
5. Add explicit experimental activation and import/export without rewriting legacy settings or existing saved styles. A malformed layout must keep the last valid complete snapshot.
6. Run live Vulkan style switching and device tests on Claw/SteamOS and Legion Go/Bazzite before publishing a test ZIP.


## Stage 2: ImGui adapter

`claw_modular_imgui.h` now resolves measurements and drawing from an owned, prepared frame snapshot. Text uses the same ImFont, effective font size and string for `CalcTextSizeA` and `AddText`. Font-atlas pointers remain borrowed and must stay alive until drawing finishes; only the renderer thread may prepare/paint or rebuild fonts. Missing source/font and invalid styles reject preparation without returning a partial frame. Drawing walks the tree in parent-first order, independent of storage order, and clips to the viewport. Solid backgrounds, inside outlines and a basic graph line are supported in this adapter; production gradient and existing graph-mode integration remains pending.

`tools/check_modular_imgui.py` uses hash-verified ImGui v1.89.9 sources and both DevLab starter documents. It produces actual draw-list vertices/indices, font-atlas images and CPU-rasterized PNGs at 1280x800 and 1920x1080. CI uses the bundled fallback font; `--font` accepts hash-verified Barlow Regular for inspection against the packaged font. These are renderer fixtures, not screenshots from SteamOS or a GPU backend. The fixture rasterizer approximates texture filtering and does not reproduce Vulkan color-space conversion. Visual browser/native parity and numerical-width stability remain unverified.

No active MangoHud integration, game sensor wiring or modular JSON import UI has been enabled yet. Next is the validated native transport and renderer-thread snapshot switch described above, followed by existing token formatting/font policies and live Vulkan tests.


## Stage 3: bounded transport and immutable exchange

`schema.encode_native` converts a strictly validated DevLab document into a bounded versioned transport. `claw_modular_transport.h` validates the complete native input before constructing an immutable `Document`: fixed token allowlist, indices, unique IDs, child ownership, numeric ranges, style colors/opacity, size/depth limits and trailing data. IDs use hex-encoded UTF-8 so whitespace and localized names cannot become delimiters. Geometry accepts up to 400 ID bytes to cover the schema's 100 Unicode-character cap.

`Exchange.publish` builds a new snapshot before publishing under a mutex. The rendering thread calls `take` between frames. Changes coalesce, old frames retain their shared immutable document, and rejected/truncated imports do not replace pending or active snapshots. Rendering/font calls stay out of the loader. `tools/check_modular_transport.py` passes both actual DevLab documents from Python into C++ and exercises concurrent updates under ASan/UBSan. This is not a Vulkan/thread-sanitizer test.

The ImGui probe now consumes the encoded native document as well, so its fixtures cover the Python-to-C++ path, per-node colors/backgrounds/opacity and anchored geometry. Defaults in this fixture are explicit test values, not an implementation of all saved plugin styles. Reading the file and swapping the snapshot are not yet wired to the active MangoHud watcher or HUD draw path.
