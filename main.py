"""Claw Metrics — isolated MangoHud profile writer and read-only sensor sampler.
No TDP writes; Panel de Control retains control of the device.
"""
import asyncio
import json
import os
import pathlib
import tempfile
import shlex
import copy
import base64
import gzip
import hashlib

ORDER = ["fps", "frametime", "cpu", "gpu", "ram", "vram", "battery", "draw", "time"]
METRICS = {
    "fps_ms": True, "graph": True,
    "cpu_temp": True, "cpu_mhz": True, "cpu_power": True,
    "gpu_temp": True, "gpu_junction_temp": False, "gpu_core_clock": True,
    "gpu_mem_clock": False, "gpu_mem_temp": False, "gpu_power": True,
    "gpu_fan": False, "gpu_voltage": False,
    "battery_icon": False, "battery_time": True,
}
DEFAULTS = {
    "enabled": True, "fontsize": 18, "opacity": 80,
    "fps": True, "frametime": True, "cpu": True, "gpu": True,
    "ram": True, "vram": True, "battery": True, "draw": True,
    "power": True, "time": True, "tdp": False,
    "sans": True, "rounding": 10, "offset_x": 8, "offset_y": 8, "padding_y": 8,
    # Native MangoHud 0.8.1 hard-codes these; retain the desired values
    # until a separately validated compatible renderer is installed.
    "padding_x": 5, "element_gap": 8,
    "order": ORDER, "metrics": METRICS,
}
# The service is normally executed as root: use the invoking desktop user instead.
def user_home():
    explicit = os.getenv("DECKY_USER_HOME")
    if explicit and pathlib.Path(explicit).is_absolute():
        return pathlib.Path(explicit)
    for name in ("DECKY_USER", "SUDO_USER"):
        value = os.getenv(name, "")
        if value and value != "root":
            import pwd
            try:
                return pathlib.Path(pwd.getpwnam(value).pw_dir)
            except KeyError:
                pass
    for path in ("/home/gamer", "/home/deck", "/home/user"):
        if pathlib.Path(path).is_dir():
            return pathlib.Path(path)
    return pathlib.Path.home()

BASE = user_home() / ".config" / "ClawMetrics"
CONFIG = BASE / "settings.json"
HUD = BASE / "MangoHud.conf"

def draw_path():
    return BASE / "draw.txt"

def battery_draw(root=pathlib.Path('/sys/class/power_supply')):
    try:
        for battery in sorted(root.glob('*')):
            if (battery / 'type').read_text().strip() != 'Battery':
                continue
            # Charging power is not total device consumption.
            if (battery / 'status').read_text().strip() != 'Discharging':
                return 'DRAW --'
            power = battery / 'power_now'
            watts = (abs(int(power.read_text())) / 1_000_000 if power.is_file()
                     else abs(int((battery / 'current_now').read_text()) *
                              int((battery / 'voltage_now').read_text())) / 1_000_000_000_000)
            return f'DRAW {watts:.1f}W'
    except (OSError, ValueError):
        pass
    return 'DRAW --'


def normalize(payload):
    d = copy.deepcopy(DEFAULTS)
    if not isinstance(payload, dict):
        return d
    for key, default in DEFAULTS.items():
        v = payload.get(key)
        if type(default) is bool and type(v) is bool:
            d[key] = v
    for key, low, high in (("fontsize", 12, 28), ("opacity", 0, 100),
                           ("rounding", 0, 20), ("offset_x", -1920, 1920),
                           ("offset_y", -1200, 1200), ("padding_y", 0, 24),
                           ("padding_x", 0, 24), ("element_gap", 0, 20)):
        v = payload.get(key)
        if type(v) is int:
            d[key] = min(high, max(low, v))
    # Preserve the old top-margin preference when upgrading to explicit X/Y.
    if "offset_y" not in payload and type(payload.get("margin")) is int:
        d["offset_y"] = min(1200, max(-1200, payload["margin"]))
    # Migrate v0.1 sensor-power toggle without changing existing preferences.
    if "metrics" not in payload and payload.get("power") is False:
        d["metrics"]["cpu_power"] = False
        d["metrics"]["gpu_power"] = False
    if isinstance(payload.get("metrics"), dict):
        for key, v in payload["metrics"].items():
            if key in METRICS and type(v) is bool:
                d["metrics"][key] = v
    if isinstance(payload.get("order"), list):
        seen = []
        for key in payload["order"]:
            if isinstance(key, str) and key in ORDER and key not in seen:
                seen.append(key)
        d["order"] = seen + [key for key in ORDER if key not in seen]
    return d

FONT_SHA256 = "507e0aff243abd8cb440c7ed9927d9d554dafddaf8d4526ca9ed2b145f20f699"

def font_path():
    return BASE / "ClawSans.ttf"

def sans_font():
    return str(font_path())

def install_font():
    # Ship a licensed font; host /usr font paths can differ inside a game runtime.
    asset = pathlib.Path(__file__).resolve().parent / "assets" / "ClawSans.ttf.gz.b64"
    data = gzip.decompress(base64.b64decode(asset.read_bytes(), validate=False))
    if hashlib.sha256(data).hexdigest() != FONT_SHA256:
        raise ValueError("Claw Sans font asset failed checksum verification")
    write_atomic(font_path(), data)

def write_atomic(path, content):
    BASE.mkdir(parents=True, exist_ok=True)
    BASE.chmod(0o755)
    fd, temporary = tempfile.mkstemp(dir=str(BASE), prefix=".tmp-")
    try:
        binary = isinstance(content, bytes)
        with os.fdopen(fd, "wb" if binary else "w", **({} if binary else {"encoding": "utf-8"})) as file:
            file.write(content)
            # mkstemp defaults to 0600; the game runs as the desktop user.
            os.fchmod(file.fileno(), 0o644)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)

def mango_config(settings):
    d = normalize(settings)
    m = d["metrics"]
    active = lambda key: d["enabled"] and d[key]
    flag = lambda key, value: key + "=" + str(int(bool(value)))
    lines = [
        "# Claw Metrics v0.2.3 base — generated from QAM settings",
        "legacy_layout=0", "horizontal", "horizontal_stretch=0",
        # Critical: compact battery_time resets the cursor to column zero.
        "hud_compact=0", "hud_no_margin", "position=top-left",
        "offset_x=" + str(d["offset_x"]), "offset_y=" + str(d["offset_y"]),
        # MangoHud multiplies this factor by real_font_size.y = font_size/2.
        "cellpadding_y=" + format(d["padding_y"] / (d["fontsize"] / 2), ".6f"),
        "round_corners=" + str(d["rounding"]),
        "background_color=161820", "text_color=F0F2F5",
        "cpu_color=37C9EF", "gpu_color=8BDA62", "ram_color=B077DF",
        "vram_color=D76AB8", "battery_color=30E5A0",
        "engine_color=30E5A0", "frametime_color=30E5A0",
        "horizontal_separator_color=777C87", "fps_color_change=1",
        "fps_value=30,60", "fps_color=30E5A0,30E5A0,30E5A0",
        "background_alpha=" + str(d["opacity"] / 100),
        "font_size=" + str(d["fontsize"]),
        "font_size_text=" + str(max(10, round(d["fontsize"] * 0.78))),
        "text_outline=0", "table_columns=64",
        flag("no_display", not d["enabled"]),
        'time_format=%H:%M',
        # Set submetrics before the ordered display blocks.
        flag("frametime", active("frametime") and m["fps_ms"]),
        flag("cpu_temp", active("cpu") and m["cpu_temp"]),
        flag("cpu_mhz", active("cpu") and m["cpu_mhz"]),
        flag("cpu_power", active("cpu") and m["cpu_power"]),
        flag("gpu_temp", active("gpu") and m["gpu_temp"]),
        flag("gpu_junction_temp", active("gpu") and m["gpu_junction_temp"]),
        flag("gpu_core_clock", active("gpu") and m["gpu_core_clock"]),
        flag("gpu_power", active("gpu") and m["gpu_power"]),
        flag("gpu_fan", active("gpu") and m["gpu_fan"]),
        flag("gpu_voltage", active("gpu") and m["gpu_voltage"]),
        # MangoHud renders memory clocks/temperature in its VRAM block.
        flag("gpu_mem_clock", active("gpu") and active("vram") and m["gpu_mem_clock"]),
        flag("gpu_mem_temp", active("gpu") and active("vram") and m["gpu_mem_temp"]),
        flag("battery_icon", active("battery") and m["battery_icon"]),
        flag("battery_time", active("battery") and m["battery_time"]),
        "battery_watt=0",
    ]
    if d["sans"] and sans_font():
        lines += ["font_file=" + sans_font(), "font_file_text=" + sans_font()]
    display = {"fps": "fps", "frametime": "frame_timing", "cpu": "cpu_stats",
               "gpu": "gpu_stats", "ram": "ram", "vram": "vram",
               "battery": "battery", "time": "time"}
    for group in d["order"]:
        if group == "draw":
            if active("draw"):
                # Read a host-generated value: no Python/runtime dependency in games.
                lines.append("exec=cat " + shlex.quote(str(draw_path())))
        else:
            on = active(group)
            if group == "frametime":
                on = on and m["graph"]
            # Disabled options are still explicit so MangoHud defaults cannot leak in.
            lines.append(flag(display[group], on))
    return "\n".join(lines) + "\n"

class Plugin:
    async def _main(self):
        install_font()
        if not CONFIG.is_file():
            write_atomic(CONFIG, json.dumps(DEFAULTS, indent=2) + "\n")
        try:
            with CONFIG.open(encoding="utf-8") as f:
                settings = normalize(json.load(f))
        except (OSError, ValueError):
            settings = dict(DEFAULTS)
        write_atomic(HUD, mango_config(settings))
        write_atomic(draw_path(), battery_draw() + "\n")
        self._draw_task = asyncio.create_task(self._draw_loop())

    async def _draw_loop(self):
        while True:
            await asyncio.sleep(2)
            try:
                write_atomic(draw_path(), battery_draw() + "\n")
            except OSError:
                # A temporary filesystem failure must not kill the Decky backend.
                pass

    async def _unload(self):
        task = getattr(self, "_draw_task", None)
        if task is not None:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    async def get_settings(self):
        try:
            with CONFIG.open(encoding="utf-8") as f:
                return normalize(json.load(f))
        except (OSError, ValueError):
            return dict(DEFAULTS)

    async def save_settings(self, settings: dict):
        data = normalize(settings)
        write_atomic(CONFIG, json.dumps(data, indent=2) + "\n")
        write_atomic(HUD, mango_config(data))
        return {"ok": True, "settings": data, "config_path": str(HUD)}

    async def get_info(self):
        return {
            "config_path": str(HUD),
            "launch_option": "MANGOHUD_CONFIGFILE=" + shlex.quote(str(HUD)) + " mangohud %command%",
            "config_readable": HUD.is_file() and bool(HUD.stat().st_mode & 0o004),
            "font_path": sans_font(),
            "font_ready": font_path().is_file() and hashlib.sha256(font_path().read_bytes()).hexdigest() == FONT_SHA256,
            "layout_spacing_supported": False,  # Stock MangoHud has no corresponding config options.
            "tdp_note": "TDP: očitanje primijenjenog limita iz Panel de Controla još nije dostupno.",
            "power_note": "CPU/GPU sensor power is not the same as total system battery draw."
        }
