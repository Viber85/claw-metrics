# Private Claw Metrics renderer

Pinned upstream: flightlessmango/MangoHud fea4292519a3085881d567a18ad3e1fee37078d8 (v0.8.1, MIT).

claw-metrics.patch adds opt-in claw_renderer, claw_center, claw_auto_fit, claw_fps_size, claw_padding_x and claw_padding_y parameters. Without claw_renderer the fork retains the ordinary rendering path. FPS has a separately loaded ImFont per swapchain/context; only its number uses that font. Row height aligns other labels around the taller FPS. Padding is applied through WindowPadding, measured content replaces the upstream negative-width/column-count estimate, and the fit scale is computed from the natural measured body width. claw_layout.h provides the shared geometry helpers.

The build produces 64-bit and 32-bit Vulkan/OpenGL libraries and the GL shim. Package installation is confined to ~/.config/ClawMetrics/renderer. Explicit Vulkan layer metadata uses a private layer name; the launcher disables the system MangoHud implicit layer, preserves existing layer/preload values and uses glibc $LIB aliases to dispatch architecture. No system MangoHud files are installed, replaced or edited.

Tests must load the actual private library, check the actual FPS draw font ratio, verify centering/fitting, and exit cleanly. Do not ignore a graphics-test crash because a frame was rendered. The packaged wrapper must also pass Vulkan and OpenGL integration tests. Software-driver tests do not establish compatibility with every Proton build, GPU or anti-cheat system.

The fork is linked with DF_1_NODELETE so application cleanup callbacks cannot jump into an already-unmapped overlay module after Vulkan instance teardown. Real-render tests must still check normal application exit. Runtime aliases cover Debian containers and lib64/lib32; the installer also reads the host glibc loader token to resolve a generic lib alias on SteamOS/Arch.
