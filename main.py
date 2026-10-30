"""Claw Metrics v0.1 — safe, isolated MangoHud configuration writer.
No TDP writes; Panel de Control retains control of the device.
"""
import json
import os
import pathlib
import tempfile
import shlex
import copy
import functools
import subprocess

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
    "sans": True, "rounding": 10, "margin": 8,
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

def normalize(payload):
    d = copy.deepcopy(DEFAULTS)
    if not isinstance(payload, dict):
        return d
    for key, default in DEFAULTS.items():
        v = payload.get(key)
        if type(default) is bool and type(v) is bool:
            d[key] = v
    for key, low, high in (("fontsize", 12, 28), ("opacity", 0, 100),
                           ("rounding", 0, 20), ("margin", 0, 24)):
        v = payload.get(key)
        if type(v) is int:
            d[key] = min(high, max(low, v))
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

@functools.lru_cache(maxsize=1)
def sans_font():
    # Use an installed proportional sans; never guess a font file path.
    try:
        result = subprocess.run(["fc-match", "-f", "%{file}", "DejaVu Sans"],
                                capture_output=True, text=True, timeout=2)
        path = pathlib.Path(result.stdout.strip())
        if result.returncode == 0 and path.is_file() and path.is_absolute():
            return str(path)
    except (OSError, subprocess.TimeoutExpired):
        pass
    for name in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                 "/usr/share/fonts/TTF/DejaVuSans.ttf"):
        if pathlib.Path(name).is_file():
            return name
    return ""

def write_atomic(path, content):
    BASE.mkdir(parents=True, exist_ok=True)
    BASE.chmod(0o755)
    fd, temporary = tempfile.mkstemp(dir=str(BASE), prefix=".tmp-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
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
        "# Claw Metrics v0.2.0 — generated from QAM settings",
        "legacy_layout=0", "horizontal", "horizontal_stretch=1",
        # Critical: compact battery_time resets the cursor to column zero.
        "hud_compact=0", "hud_no_margin", "position=top-left",
        "offset_x=" + str(d["margin"]), "offset_y=" + str(d["margin"]),
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
                helper = pathlib.Path(__file__).resolve().with_name("sensors.py")
                lines.append("exec=/usr/bin/python3 " + shlex.quote(str(helper)))
        else:
            on = active(group)
            if group == "frametime":
                on = on and m["graph"]
            # Disabled options are still explicit so MangoHud defaults cannot leak in.
            lines.append(flag(display[group], on))
    return "\n".join(lines) + "\n"

class Plugin:
    async def _main(self):
        if not CONFIG.is_file():
            write_atomic(CONFIG, json.dumps(DEFAULTS, indent=2) + "\n")
        try:
            with CONFIG.open(encoding="utf-8") as f:
                settings = normalize(json.load(f))
        except (OSError, ValueError):
            settings = dict(DEFAULTS)
        write_atomic(HUD, mango_config(settings))

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
            "tdp_note": "TDP: očitanje primijenjenog limita iz Panel de Controla još nije dostupno.",
            "power_note": "CPU/GPU sensor power is not the same as total system battery draw."
        }
