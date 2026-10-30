#!/bin/bash
set -euo pipefail
arch="$1"
root="$(pwd)"
if [ ! -d native-source ]; then
  git clone --depth 1 --branch v0.8.1 https://github.com/flightlessmango/MangoHud.git native-source
fi
test "$(git -C native-source rev-parse HEAD)" = fea4292519a3085881d567a18ad3e1fee37078d8
git -C native-source apply --check "$root/renderer/claw-metrics.patch"
git -C native-source apply "$root/renderer/claw-metrics.patch"
cp renderer/claw_layout.h native-source/src/
extra=()
if [ "$arch" = i386 ]; then
  cat > native-cross.ini <<'CROSS'
[binaries]
c = ['gcc', '-m32']
cpp = ['g++', '-m32']
pkgconfig = 'pkg-config'
[properties]
pkg_config_libdir = '/usr/lib/i386-linux-gnu/pkgconfig:/usr/share/pkgconfig'
[host_machine]
system = 'linux'
cpu_family = 'x86'
cpu = 'i686'
endian = 'little'
CROSS
  extra=(--cross-file "$root/native-cross.ini")
fi
meson setup native-source/build native-source "${extra[@]}" --buildtype=release --prefix=/usr \
  -Dinclude_doc=false -Dwith_x11=enabled -Dwith_wayland=disabled -Dwith_dbus=disabled \
  -Dwith_nvml=disabled -Dwith_xnvctrl=disabled -Dtests=disabled -Dmangoplot=disabled
meson compile -C native-source/build -j 4
mkdir -p native-dist
cp native-source/build/src/libMangoHud.so native-source/build/src/libMangoHud_opengl.so native-source/build/src/libMangoHud_shim.so native-dist/
cp native-source/LICENSE native-dist/MANGOHUD-LICENSE.txt
file native-dist/*.so
