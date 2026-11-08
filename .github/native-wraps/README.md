# Pinned upstream Meson build patches

These are the unmodified ZIP assets from mesonbuild/wrapdb, encoded as base64 for repository transport. Each archive retains its upstream `LICENSE.build`. They only contain Meson build files; the dependency sources are still fetched by the pinned upstream wraps.

`tools/cache_native_wraps.py` decodes them into Meson's package cache and verifies SHA256 against the wrap files in the checked-out MangoHud v0.8.1 source. A mismatch stops the build. This removes a dependency on WrapDB availability and GitHub's anonymous API quota. The helper also caches dependency source archives, using GitHub's canonical codeload URL for archive downloads and verifying each against its original upstream `source_hash` before Meson runs.

| File | Official release asset | SHA256 |
| --- | --- | --- |
| vulkan-headers.zip.b64 | https://api.github.com/repos/mesonbuild/wrapdb/releases/assets/38086395 | 860358cf5e73f458cd1e88f8c38116d123ab421d5ce2e4129ec38eaedd820e17 |
| imgui.zip.b64 | https://api.github.com/repos/mesonbuild/wrapdb/releases/assets/127147440 | 9b21290c597d76bf8d4eeb3f9ffa024b11d9ea6c61e91d648ccc90b42843d584 |
| implot.zip.b64 | https://api.github.com/repos/mesonbuild/wrapdb/releases/assets/126997169 | 1c6b1462066a5452fa50c1da1dd47fed841f28232972c82d778f2962936568c7 |
| spdlog.zip.b64 | https://api.github.com/repos/mesonbuild/wrapdb/releases/assets/165966666 | ae878e732330ea1048f90d7e117c40c0cd2a6fb8ae5492c7955818ce3aaade6c |
