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
import re
import shutil
import subprocess
import time

ORDER = ["fps", "frametime", "cpu", "gpu", "ram", "vram", "battery", "tdp", "draw", "time"]
COLORS = {
    "text": "F0F2F5",        # numeric metrics, clock and DRAW text
    "separator": "777C87",   # independent of VRAM
    "fps_label": "30E5A0",
    "fps_value": "30E5A0",
    "cpu": "37C9EF",
    "gpu": "8BDA62",
    "ram": "B077DF",
    "vram": "D76AB8",
    "battery": "30E5A0",
    "graph": "30E5A0",
    "time": "F0F2F5",  # native Clock token
    "draw": "F0F2F5",  # native DRAW text
    "tdp": "FFBD69",  # TDP limit readback
}

METRICS = {
    "fps_ms": True, "graph": True,
    "cpu_temp": True, "cpu_mhz": True, "cpu_power": True,
    "gpu_temp": True, "gpu_junction_temp": False, "gpu_core_clock": True,
    "gpu_mem_clock": False, "gpu_mem_temp": False, "gpu_power": True,
    "gpu_fan": False, "gpu_voltage": False,
    "battery_icon": False, "battery_time": True,
}
TOKEN_SLOTS = ["fps.label","fps.value","fps.ms","cpu.label","cpu.load","cpu.temp","cpu.clock","cpu.power","gpu.label","gpu.load","gpu.temp","gpu.clock","gpu.power","gpu.junction","gpu.fan","gpu.voltage","ram.label","ram.value","vram.label","vram.value","vram.temp","vram.clock","battery.label","battery.value","battery.time","battery.power","time.value","tdp.value"]
FONT_WEIGHTS = ("inherit", "light", "regular", "semibold", "bold")
FONT_DIGITS = {name: str(index) for index, name in enumerate(FONT_WEIGHTS)}


def normalize_token_weights(payload):
    out = {}
    if isinstance(payload, dict):
        for key in TOKEN_SLOTS:
            if payload.get(key) in FONT_WEIGHTS[1:]:
                out[key] = payload[key]
    return out


def normalize_token_colors(payload):
    out = {}
    if isinstance(payload, dict):
        for key in TOKEN_SLOTS:
            color = payload.get(key)
            if isinstance(color, str):
                val = color.lstrip("#").upper()
                if re.fullmatch("[0-9A-F]{6}", val):
                    out[key] = val
    return out


STYLE_LAYOUT_RANGES = {
    "fontsize": (12, 28), "fps_scale": (100, 200), "opacity": (0, 100), "rounding": (0, 20),
    "padding_x": (0, 24), "padding_y": (0, 24),
    "offset_x": (-1920, 1920), "offset_y": (-1200, 1200),
    "element_gap": (0, 20), "table_gap": (0, 12),
    "inner_gap": (0, 16), "graph_width": (80, 200),
}
STYLE_LAYOUT_FLAGS = ("sans", "inline_metrics", "center_horizontal")
HUD_POSITIONS = ("top-left", "top-center", "top-right", "bottom-left", "bottom-right")
GRAPH_STYLES = ("line", "area", "bars", "dual")


def normalize_custom_labels(payload):
    result = {}
    if not isinstance(payload, dict):
        return result
    for key in ORDER:
        value = payload.get(key)
        if not isinstance(value, str):
            continue
        # Safe single-line labels for both MangoHud config and text output.
        label = re.sub(r"\s+", " ", re.sub(r"[\x00-\x1f\x7f=,]", " ", value)).strip()[:24]
        if label:
            result[key] = label
    return result


def normalize_style_presets(payload):
    out = {}
    if not isinstance(payload, dict):
        return out
    for key in ("1", "2"):
        item = payload.get(key)
        if not isinstance(item, dict):
            continue
        stored_colors = normalize_color_overrides(item.get("colors"))
        # Old presets used text_color for both Clock and DRAW.
        for key_name in ("time", "draw"):
            if key_name not in stored_colors:
                stored_colors[key_name] = stored_colors.get("text", COLORS["text"])
        preset = {
            "colors": {**COLORS, **stored_colors},
            "font_weight": item.get("font_weight") if item.get("font_weight") in FONT_WEIGHTS[1:] else "regular",
            "fps_bold": item.get("fps_bold") if type(item.get("fps_bold")) is bool else True,
            "token_weights": normalize_token_weights(item.get("token_weights")),
            "token_colors": normalize_token_colors(item.get("token_colors")),
        }
        if item.get("version") == 2:
            preset["version"] = 2
        # Legacy presets lacked layout fields; do NOT reset layout on load.
        for field, (lo, hi) in STYLE_LAYOUT_RANGES.items():
            value = item.get(field)
            if type(value) is int:
                preset[field] = min(hi, max(lo, value))
        for field in STYLE_LAYOUT_FLAGS:
            if type(item.get(field)) is bool:
                preset[field] = item[field]
        if item.get("hud_position") in HUD_POSITIONS:
            preset["hud_position"] = item["hud_position"]
        elif preset.get("center_horizontal") is True:
            preset["hud_position"] = "top-center"
        if "hud_position" in preset:
            preset["center_horizontal"] = preset["hud_position"] == "top-center"
        if item.get("graph_style") in GRAPH_STYLES:
            preset["graph_style"] = item["graph_style"]
        out[key] = preset
    return out


def normalize_color_overrides(payload):
    out = {}
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in COLORS and isinstance(value, str):
                candidate = value.lstrip("#").upper()
                if re.fullmatch("[0-9A-F]{6}", candidate):
                    out[key] = candidate
    return out


DEFAULTS = {
    "enabled": True, "fontsize": 18, "fps_scale": 100, "center_horizontal": False,
    "hud_position": "top-left", "opacity": 80,
    "fps": True, "frametime": True, "cpu": True, "gpu": True,
    "ram": True, "vram": True, "battery": True, "draw": True,
    "power": True, "time": True, "tdp": False,
    "sans": True, "rounding": 10, "offset_x": 8, "offset_y": 8, "padding_y": 8,
    # Native MangoHud 0.8.1 hard-codes these; retain the desired values
    # until a separately validated compatible renderer is installed.
    "padding_x": 5, "element_gap": 8, "table_gap": 4, "graph_width": 150,
    "inner_gap": 4, "inline_metrics": True, "fps_bold": True, "graph_style": "line",
    "colors": COLORS,
    "font_weight": "regular",
    "token_weights": {}, "token_colors": {}, "style_presets": {},
    "active_style": None, "custom_labels": {},
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

def experimental_library():
    return pathlib.Path(__file__).resolve().parent / "native64" / "libMangoHud.so"


def experimental_manifest():
    return BASE / "vk_layers" / "ClawMetrics.x86_64.json"


def user_vulkan_manifest():
    # Vulkan Loader's standard user explicit-layer location. The manifest is
    # discoverable but NOT enabled unless VK_INSTANCE_LAYERS requests it.
    return user_home() / ".local/share/vulkan/explicit_layer.d/ClawMetrics.test3.x86_64.json"


EXPERIMENTAL_LAYER_NAME = "VK_LAYER_CLAW_METRICS_overlay_x86_64"


def native_hud_path():
    return BASE / "MangoHud-experimental.conf"


def native_renderer_available():
    binary = experimental_library()
    # Only expose the native option when the installer actually contains
    # the experimental library. This is an opt-in test, not a system override.
    return binary.is_file() and binary.stat().st_size > 100_000


def install_native_manifest():
    if not native_renderer_available():
        return
    # Use a unique explicit-layer name. Reusing the standard MangoHud name
    # clashes with SteamOS/Proton's already registered implicit layer.
    content = {"file_format_version": "1.0.0", "layer": {
        "name": EXPERIMENTAL_LAYER_NAME,
        "type": "GLOBAL", "api_version": "1.3.0",
        "library_path": str(experimental_library()),
        "implementation_version": "1",
        "description": "Claw Metrics experimental Vulkan 64-bit HUD",
        "functions": {"vkGetInstanceProcAddr": "overlay_GetInstanceProcAddr",
                      "vkGetDeviceProcAddr": "overlay_GetDeviceProcAddr"},
    }}
    private_manifest = experimental_manifest()
    private_manifest.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    write_atomic(private_manifest, json.dumps(content, indent=2) + "\n")

    # A discoverable user explicit layer is inert until requested by name.
    # Create any missing XDG directories as the desktop user, not root:
    # Decky's privileged backend must not leave root-owned user directories.
    public_manifest = user_vulkan_manifest()
    try:
        home = user_home()
        owner = home.stat()
        for directory in (home / ".local", home / ".local/share",
                          home / ".local/share/vulkan", public_manifest.parent):
            if not directory.exists():
                directory.mkdir(mode=0o755)
                if os.geteuid() == 0 and owner.st_uid != 0:
                    os.chown(directory, owner.st_uid, owner.st_gid)
        write_atomic(public_manifest, json.dumps(content, indent=2) + "\n")
        if os.geteuid() == 0 and owner.st_uid != 0:
            os.chown(public_manifest, owner.st_uid, owner.st_gid)
    except OSError as error:
        # This fallback is optional. A permission issue must never prevent
        # the QAM plugin or the private manifest from working.
        print("Claw Metrics: user Vulkan manifest unavailable:", error)


def short_launcher_path():
    # Stable across Decky updates; do not depend on the game's PATH.
    return BASE / "claw-metrics"


def short_launcher_script():
    """POSIX shell equivalent of the existing experimental Steam command."""
    return (
        "#!/bin/sh\n"
        "# Generated by Claw Metrics. Do not edit; QAM will regenerate this file.\n"
        "# Fail open if Decky upgraded or removed the native renderer assets.\n"
        "if [ ! -r " + shlex.quote(str(experimental_library()))
        + " ] || [ ! -r " + shlex.quote(str(experimental_manifest()))
        + " ] || [ ! -r " + shlex.quote(str(native_hud_path())) + " ]; then\n"
        '    echo "Claw Metrics: missing renderer assets; launching game without custom HUD" >&2\n'
        '    exec "$@"\n'
        "fi\n"
        "export VK_ADD_LAYER_PATH=" + shlex.quote(str(experimental_manifest().parent)) + "\n"
        "export VK_INSTANCE_LAYERS=" + shlex.quote(EXPERIMENTAL_LAYER_NAME) + "\n"
        "export DISABLE_MANGOHUD=1\n"
        "export MANGOHUD_CONFIGFILE=" + shlex.quote(str(native_hud_path())) + "\n"
        'exec "$@"\n'
    )


def install_short_launcher():
    """Install only alongside the optional experimental Vulkan renderer."""
    if not native_renderer_available():
        return
    if short_launcher_ready():
        return
    # Publish a fully executable file atomically, without a 0644 race window.
    write_atomic(short_launcher_path(), short_launcher_script(), mode=0o755)


def short_launcher_ready():
    try:
        path = short_launcher_path()
        return (native_renderer_available() and path.is_file()
                and bool(path.stat().st_mode & 0o111)
                and experimental_manifest().is_file()
                and native_hud_path().is_file()
                and path.read_text(encoding="utf-8") == short_launcher_script())
    except (OSError, UnicodeError):
        return False


# TDP monitoring is read-only. Never invoke ryzenadj with write flags.
STAPM_LIMIT_RE = re.compile(r"(?im)^\s*\|?\s*STAPM LIMIT\s*\|\s*([0-9]+(?:\.[0-9]+)?)")
TDP_MIN_W, TDP_MAX_W = 3, 100


def tdp_path():
    return BASE / "tdp.txt"


def resolve_ryzenadj(plugin_roots=None):
    """Locate the actual Panel de Control binary without invoking write commands.

    Decky installs it in 'Panel de Control/bin/ryzenadj' (spaces included).
    Other Decky installations mount homebrew either under /homebrew or HOME.
    """
    roots = plugin_roots if plugin_roots is not None else [
        pathlib.Path(__file__).resolve().parent.parent,
        pathlib.Path("/homebrew/plugins"),
        user_home() / "homebrew" / "plugins",
        pathlib.Path("/home/deck/homebrew/plugins"),
        pathlib.Path("/home/gamer/homebrew/plugins"),
    ]
    candidates = [shutil.which("ryzenadj")]
    for root in roots:
        for plugin in ("Panel de Control", "panel-de-control", "Panel-de-Control",
                       "panel_de_control"):
            candidates.append(str(root / plugin / "bin" / "ryzenadj"))
    for name in candidates:
        if name:
            path = pathlib.Path(name)
            if path.is_file() and os.access(path, os.X_OK):
                return str(path)
    return None


def panel_settings_roots():
    """Known Decky settings roots; never scan arbitrary files or game directories."""
    configured = os.environ.get("DECKY_PLUGIN_SETTINGS_DIR", "")
    roots = []
    if configured and pathlib.Path(configured).is_absolute():
        roots.append(pathlib.Path(configured).parent)
    roots.extend([
        pathlib.Path("/homebrew/settings"),
        user_home() / "homebrew/settings",
        pathlib.Path("/home/deck/homebrew/settings"),
        pathlib.Path("/home/gamer/homebrew/settings"),
    ])
    return list(dict.fromkeys(roots))


def read_panel_setpoint(roots=None, appid=None, context_known=False):
    """Read only the PDC PL1 setpoint for the active game, not a claimed HW limit."""
    locations = roots if roots is not None else panel_settings_roots()
    for directory in locations:
        for name in ("Panel de Control", "panel-de-control", "Panel-de-Control",
                     "panel_de_control"):
            plugin = pathlib.Path(directory) / name
            profiles_path = plugin / "tdp_profiles.json"
            try:
                if not profiles_path.is_file() or profiles_path.stat().st_size > 262144:
                    continue
                profiles = json.loads(profiles_path.read_text(encoding="utf-8"))
                state_path = plugin / "state.json"
                if state_path.is_file() and state_path.stat().st_size <= 262144:
                    state = json.loads(state_path.read_text(encoding="utf-8"))
                    if isinstance(state, dict) and state.get("tdp_control_enabled") is False:
                        return None, "PDC: upravljanje TDP-om isključeno"
                if not isinstance(profiles, dict):
                    continue
                global_profile = profiles.get("global")
                if not isinstance(global_profile, dict):
                    continue
                games = profiles.get("games", {})
                if not isinstance(games, dict):
                    games = {}
                if not context_known:
                    if any(isinstance(p, dict) and not p.get("follow_global")
                           for p in games.values()):
                        return None, "PDC: različiti profili igara, čekam potvrdu aktivne igre"
                    selected, scope = global_profile, "globalno"
                elif appid is not None:
                    if not isinstance(appid, str) or not (0 < len(appid) <= 160):
                        return None, "PDC: neispravan identitet igre"
                    ownership_path = plugin / "power_ownership.json"
                    if ownership_path.is_file() and ownership_path.stat().st_size <= 262144:
                        ownership = json.loads(ownership_path.read_text(encoding="utf-8"))
                        if isinstance(ownership, dict):
                            owners = ownership.get("games", {})
                            owner = owners.get(appid, {}) if isinstance(owners, dict) else {}
                            if isinstance(owner, dict) and owner.get("owner") == "steam":
                                return None, "PDC: Steam upravlja TDP-om ove igre"
                    game_profile = games.get(appid)
                    if isinstance(game_profile, dict) and not game_profile.get("follow_global"):
                        selected, scope = game_profile, "profil aktivne igre"
                    else:
                        selected, scope = global_profile, "globalni profil za aktivnu igru"
                else:
                    selected, scope = global_profile, "globalno (nema pokrenute igre)"
                watts = valid_tdp_w(selected.get("pl1", selected.get("watts")))
                if watts is None:
                    return None, "PDC: odabrani profil nema valjan PL1"
                if selected.get("auto_tdp") is True:
                    return None, "PDC: Auto TDP aktivnog profila (promjenjiv limit)"
                return watts, (f"Panel de Control · {scope} · postavljeno "
                               "(nije hardverski potvrđeno)")
            except (OSError, ValueError, TypeError, AttributeError):
                continue
    return None, "Nije dostupno"


def valid_tdp_w(value):
    try:
        watts = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if not (TDP_MIN_W <= watts <= TDP_MAX_W):
        return None
    return round(watts)


def read_tdp_limit(root=pathlib.Path("/sys/class/firmware-attributes"),
                   binary=None, runner=None, panel_roots=None,
                   appid=None, context_known=False):
    """Return (readback in watts, source). No cached/setpoint guesses.

    On official SteamOS prefer the same RyzenAdj STAPM readback used by
    Panel de Control. Some newer kernels deny this read; MSI firmware PL1
    is a strictly read-only secondary source if available. The saved PDC
    setpoint is the last fallback and is explicitly tagged unverified.
    """
    executable = resolve_ryzenadj() if binary is None else binary
    if executable:
        try:
            invoke = runner or subprocess.run
            env = dict(os.environ)
            env["LD_LIBRARY_PATH"] = ""
            result = invoke([executable, "-i"], capture_output=True,
                            text=True, timeout=2, env=env)
            # PDC also accepts a valid parsed STAPM row even when RyzenAdj
            # reports a non-zero exit code for an unrelated system probe.
            match = STAPM_LIMIT_RE.search(result.stdout or "")
            watts = valid_tdp_w(match.group(1)) if match else None
            if watts is not None:
                return watts, "RyzenAdj STAPM"
        except (OSError, ValueError, subprocess.SubprocessError):
            pass
    try:
        for attr in sorted(root.glob(
                "msi-wmi-platform*/attributes/ppt_pl1_spl/current_value")):
            watts = valid_tdp_w(attr.read_text(encoding="utf-8").strip())
            if watts is not None:
                return watts, "MSI firmware PL1"
    except (OSError, ValueError):
        pass
    # Intended setpoint remains useful when modern SteamOS blocks HW readback.
    # Do not silently claim it was applied, especially with game overrides.
    return read_panel_setpoint(panel_roots, appid=appid, context_known=context_known)



def tdp_source_diagnostics(firmware_root=pathlib.Path("/sys/class/firmware-attributes"),
                           plugin_roots=None, settings_roots=None, runner=None,
                           appid=None, context_known=False):
    """On-demand read-only TDP source report; never include stored game IDs."""
    notes = []
    nodes = sorted(firmware_root.glob(
        "msi-wmi-platform*/attributes/ppt_pl1_spl/current_value"))
    if not nodes:
        notes.append("MSI firmware PL1: putanja nije pronađena")
    for node in nodes[:3]:
        try:
            watts = valid_tdp_w(node.read_text(encoding="utf-8").strip())
            notes.append("MSI firmware PL1: " +
                         (f"{watts}W" if watts is not None else "nečitljivo"))
        except OSError as error:
            notes.append("MSI firmware PL1: " + type(error).__name__)
    binary = resolve_ryzenadj(plugin_roots)
    if not binary:
        notes.append("RyzenAdj: izvršna datoteka nije pronađena")
    else:
        try:
            env = dict(os.environ)
            env["LD_LIBRARY_PATH"] = ""
            proc = (runner or subprocess.run)([binary, "-i"], capture_output=True,
                                              text=True, timeout=3, env=env)
            match = STAPM_LIMIT_RE.search(proc.stdout or "")
            watts = valid_tdp_w(match.group(1)) if match else None
            reading = f"{watts}W" if watts is not None else "STAPM nije pročitan"
            notes.append(f"RyzenAdj: {reading}, izlazni kod {proc.returncode}")
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            notes.append("RyzenAdj: " + type(error).__name__)
    locations = settings_roots if settings_roots is not None else panel_settings_roots()
    for directory in locations:
        for name in ("Panel de Control", "panel-de-control", "Panel-de-Control",
                     "panel_de_control"):
            plugin = pathlib.Path(directory) / name
            profile_path = plugin / "tdp_profiles.json"
            if not profile_path.is_file():
                continue
            try:
                if profile_path.stat().st_size > 262144:
                    notes.append("PDC: profili preveliki")
                    continue
                profiles = json.loads(profile_path.read_text(encoding="utf-8"))
                if not isinstance(profiles, dict):
                    notes.append("PDC: neispravan format profila")
                    continue
                global_profile = profiles.get("global")
                if not isinstance(global_profile, dict):
                    notes.append("PDC: globalni profil nedostaje")
                    continue
                glob = valid_tdp_w(global_profile.get(
                    "pl1", global_profile.get("watts")))
                games = profiles.get("games", {})
                overrides = 0
                if isinstance(games, dict):
                    for game in games.values():
                        if isinstance(game, dict) and not game.get("follow_global"):
                            if (valid_tdp_w(game.get("pl1", game.get("watts"))) != glob
                                    or game.get("auto_tdp") is True):
                                overrides += 1
                enabled = "nepoznato"
                state_path = plugin / "state.json"
                if state_path.is_file() and state_path.stat().st_size <= 262144:
                    state = json.loads(state_path.read_text(encoding="utf-8"))
                    if isinstance(state, dict):
                        value = state.get("tdp_control_enabled")
                        if isinstance(value, bool):
                            enabled = "da" if value else "ne"
                _, reason = read_panel_setpoint([directory], appid=appid,
                                                 context_known=context_known)
                notes.append(
                    f"PDC: globalno {glob if glob is not None else '--'}W, "
                    f"upravljanje uključeno {enabled}, različitih profila igara "
                    f"{overrides}, Auto TDP globalno "
                    f"{'da' if global_profile.get('auto_tdp') else 'ne'}; "
                    f"rezervno čitanje: {reason}")
                return " | ".join(notes)
            except (OSError, ValueError, TypeError) as error:
                notes.append("PDC: greška " + type(error).__name__)
                return " | ".join(notes)
    notes.append("PDC: tdp_profiles.json nije pronađen u Decky settings")
    return " | ".join(notes)


def tdp_text(settings, watts):
    label = normalize_custom_labels(settings.get("custom_labels", {})).get("tdp", "TDP")
    return label + (" --" if watts is None else f" {watts}W")


def draw_text(settings):
    reading = battery_draw()
    label = normalize_custom_labels(settings.get("custom_labels", {})).get("draw", "DRAW")
    return label + reading[len("DRAW"):] if reading.startswith("DRAW ") else reading


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
    for key, low, high in (("fontsize", 12, 28), ("fps_scale", 100, 200), ("opacity", 0, 100),
                           ("rounding", 0, 20), ("offset_x", -1920, 1920),
                           ("offset_y", -1200, 1200), ("padding_y", 0, 24),
                           ("padding_x", 0, 24), ("element_gap", 0, 20),
                           ("table_gap", 0, 12), ("graph_width", 80, 200),
                           ("inner_gap", 0, 16)):
        v = payload.get(key)
        if type(v) is int:
            d[key] = min(high, max(low, v))
    # Migrate old center_horizontal profiles while making a new anchor authoritative.
    if payload.get("hud_position") in HUD_POSITIONS:
        d["hud_position"] = payload["hud_position"]
    elif d["center_horizontal"]:
        d["hud_position"] = "top-center"
    d["center_horizontal"] = d["hud_position"] == "top-center"
    if payload.get("graph_style") in GRAPH_STYLES:
        d["graph_style"] = payload["graph_style"]
    # Preserve the old top-margin preference when upgrading to explicit X/Y.
    if "offset_y" not in payload and type(payload.get("margin")) is int:
        d["offset_y"] = min(1200, max(-1200, payload["margin"]))
    # Migrate v0.1 sensor-power toggle without changing existing preferences.
    if "metrics" not in payload and payload.get("power") is False:
        d["metrics"]["cpu_power"] = False
        d["metrics"]["gpu_power"] = False
    if payload.get("font_weight") in ("light", "regular", "semibold", "bold"):
        d["font_weight"] = payload["font_weight"]
    if isinstance(payload.get("colors"), dict):
        for key, value in payload["colors"].items():
            if key in COLORS and isinstance(value, str):
                candidate = value.lstrip("#").upper()
                if re.fullmatch(r"[0-9A-F]{6}", candidate):
                    d["colors"][key] = candidate
        # Old saved settings had no independent Clock / DRAW colors.
        for label in ("time", "draw"):
            if label not in payload["colors"]:
                d["colors"][label] = d["colors"]["text"]
    d["custom_labels"] = normalize_custom_labels(payload.get("custom_labels"))
    d["token_weights"] = normalize_token_weights(payload.get("token_weights"))
    d["token_colors"] = normalize_token_colors(payload.get("token_colors"))
    d["style_presets"] = normalize_style_presets(payload.get("style_presets"))
    active_slot = payload.get("active_style")
    if active_slot in d["style_presets"]:
        d["active_style"] = active_slot
    if isinstance(payload.get("metrics"), dict):
        for key, v in payload["metrics"].items():
            if key in METRICS and type(v) is bool:
                d["metrics"][key] = v
    if isinstance(payload.get("order"), list):
        seen = []
        for key in payload["order"]:
            if isinstance(key, str) and key in ORDER and key not in seen:
                seen.append(key)
        # Put newly introduced TDP immediately before DRAW on upgrades.
        if "tdp" not in seen:
            i = seen.index("draw") if "draw" in seen else len(seen)
            seen.insert(i, "tdp")
        d["order"] = seen + [key for key in ORDER if key not in seen]
    return d

FONT_SHA256 = "507e0aff243abd8cb440c7ed9927d9d554dafddaf8d4526ca9ed2b145f20f699"

def font_path():
    return BASE / "ClawSans.ttf"

# These public OFL fonts are packaged into assets/fonts/ by GitHub Actions.
# No network access is required on the MSI Claw after installation.
# The hashes identify immutable official Google Fonts revision binaries.
BARLOW_BLOBS = {
    "light": ("Light", "f7e0277904b0d7e560d5b178e0ad680d9a096cfd"),
    "regular": ("Regular", "473604976bc07e69c0a8e6dca63e159fac54f5fe"),
    "semibold": ("SemiBold", "082c76327d21d663948c8ccd2271fa527bd0c145"),
    "bold": ("Bold", "ee04b09e31e98d2509354d7003797ec6540e796f"),
}


def bundled_font_path(weight):
    return pathlib.Path(__file__).resolve().parent / "assets" / "fonts" / (
        "BarlowSemiCondensed-" + BARLOW_BLOBS[weight][0] + ".ttf")


def condensed_font_path(weight):
    return BASE / ("BarlowSemiCondensed-" + BARLOW_BLOBS[weight][0] + ".ttf")


def valid_git_font(blob, expected):
    return (len(blob) > 20000
            and blob[:4] in (bytes([0, 1, 0, 0]), b"OTTO")
            and hashlib.sha1(b"blob " + str(len(blob)).encode()
                             + bytes([0]) + blob).hexdigest() == expected)


def install_condensed_fonts():
    """Install validated packaged fonts without any network access."""
    for weight, (_, git_sha) in BARLOW_BLOBS.items():
        src = bundled_font_path(weight)
        dest = condensed_font_path(weight)
        try:
            if dest.is_file() and valid_git_font(dest.read_bytes(), git_sha):
                continue
            if not src.is_file():
                raise FileNotFoundError("Missing bundled font asset: " + src.name)
            blob = src.read_bytes()
            if not valid_git_font(blob, git_sha):
                raise ValueError("Bundled font checksum mismatch: " + src.name)
            write_atomic(dest, blob)
        except (OSError, ValueError) as error:
            print("Claw Metrics: bundled font " + weight + " unavailable: " + str(error))


def condensed_fonts_ready():
    return all(condensed_font_path(w).is_file() and
               valid_git_font(condensed_font_path(w).read_bytes(), sha)
               for w, (_, sha) in BARLOW_BLOBS.items())


def sans_font(weight="regular"):
    if weight not in BARLOW_BLOBS:
        weight = "regular"
    path = condensed_font_path(weight)
    if path.is_file() and valid_git_font(path.read_bytes(), BARLOW_BLOBS[weight][1]):
        return str(path)
    return str(font_path())


def install_font():
    # Ship a licensed font; host /usr font paths can differ inside a game runtime.
    asset = pathlib.Path(__file__).resolve().parent / "assets" / "ClawSans.ttf.gz.b64"
    data = gzip.decompress(base64.b64decode(asset.read_bytes(), validate=False))
    if hashlib.sha256(data).hexdigest() != FONT_SHA256:
        raise ValueError("Claw Sans font asset failed checksum verification")
    write_atomic(font_path(), data)

def write_atomic(path, content, mode=0o644):
    BASE.mkdir(parents=True, exist_ok=True)
    BASE.chmod(0o755)
    fd, temporary = tempfile.mkstemp(dir=str(BASE), prefix=".tmp-")
    try:
        binary = isinstance(content, bytes)
        with os.fdopen(fd, "wb" if binary else "w", **({} if binary else {"encoding": "utf-8"})) as file:
            file.write(content)
            # Set final permissions before the atomic rename.
            os.fchmod(file.fileno(), mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)

def mango_config(settings, native_spacing=False):
    d = normalize(settings)
    m = d["metrics"]
    c = d["colors"]
    active = lambda key: d["enabled"] and d[key]
    flag = lambda key, value: key + "=" + str(int(bool(value)))
    # Avoid the broken native top-center branch for non-stretched horizontal HUDs.
    position = d["hud_position"]
    native_position = "top-left" if position == "top-center" else position
    # Offsets are distances IN from the selected corner.
    hud_x = -d["offset_x"] if position.endswith("right") else d["offset_x"]
    hud_y = -d["offset_y"] if position.startswith("bottom") else d["offset_y"]
    lines = [
        "# Claw Metrics v0.2.3 base — generated from QAM settings",
        "legacy_layout=0", "horizontal", "horizontal_stretch=0",
        # Critical: compact battery_time resets the cursor to column zero.
        "hud_compact=0", "hud_no_margin", "position=" + native_position,
        "offset_x=" + str(hud_x), "offset_y=" + str(hud_y),
        # MangoHud multiplies this factor by real_font_size.y = font_size/2.
        "cellpadding_y=" + format(d["padding_y"] / (d["fontsize"] / 2), ".6f"),
        "round_corners=" + str(d["rounding"]),
        "background_color=161820",
        "text_color=" + c["text"],
        "cpu_color=" + c["cpu"], "gpu_color=" + c["gpu"],
        "ram_color=" + c["ram"], "vram_color=" + c["vram"],
        "battery_color=" + c["battery"], "engine_color=" + c["fps_label"],
        "frametime_color=" + c["graph"],
        "horizontal_separator_color=" + c["separator"], "fps_color_change=1",
        "fps_value=30,60",
        "fps_color=" + ",".join([c["fps_value"]] * 3),
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
    if native_spacing:
        # Visible diagnostic: FPS* confirms this experimental config was read.
        # An ordinary FPS label means the game is still using the stock profile.
        # This marker is temporary and only affects the experimental profile.
        lines.extend([
            "fps_text=" + d["custom_labels"].get("fps", "FPS*"),
            "cpu_text=" + d["custom_labels"].get("cpu", "CPU"),
            "gpu_text=" + d["custom_labels"].get("gpu", "GPU"),
            "claw_ram_label=" + d["custom_labels"].get("ram", "RAM"),
            "claw_vram_label=" + d["custom_labels"].get("vram", "VRAM"),
            "claw_battery_label=" + d["custom_labels"].get("battery", "BATT"),
            "claw_padding_x=" + str(d["padding_x"]),
            "claw_element_gap=" + str(d["element_gap"]),
            "claw_table_padding_x=" + str(d["table_gap"]),
            "claw_graph_width=" + str(d["graph_width"]),
            "claw_graph_style=" + str(GRAPH_STYLES.index(d["graph_style"])),
            "claw_inner_gap=" + str(d["inner_gap"]),
            "claw_inline_metrics=" + str(int(d["inline_metrics"])),
            "claw_fps_bold=" + str(int(d["fps_bold"])),
            "claw_fps_scale=" + str(d["fps_scale"]),
            "claw_center_horizontal=" + str(int(position == "top-center")),
            "claw_align_right=" + str(int(position.endswith("right"))),
            "claw_weight_map=" + "".join(FONT_DIGITS[d["token_weights"].get(slot, "inherit")] for slot in TOKEN_SLOTS),
            "claw_color_map=" + ":".join(
                d["token_colors"].get(slot, c["time"] if slot == "time.value" else
                                      c["draw"] if slot == "battery.power" else
                                      c["tdp"] if slot == "tdp.value" else "------")
                for slot in TOKEN_SLOTS
            ),
        ])
    if d["sans"]:
        primary = sans_font(d["font_weight"])
        lines += ["font_file=" + primary, "font_file_text=" + primary]
        if native_spacing and condensed_fonts_ready():
            lines.append("claw_bold_font_file=" + str(condensed_font_path("bold")))
            for weight in ("light", "regular", "semibold"):
                lines.append("claw_" + weight + "_font_file=" + str(condensed_font_path(weight)))
    display = {"fps": "fps", "frametime": "frame_timing", "cpu": "cpu_stats",
               "gpu": "gpu_stats", "ram": "ram", "vram": "vram",
               "battery": "battery", "time": "time"}
    for group in d["order"]:
        if group == "tdp":
            if active("tdp"):
                lines.append("exec=cat " + shlex.quote(str(tdp_path())))
        elif group == "draw":
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
        install_condensed_fonts()
        if not CONFIG.is_file():
            write_atomic(CONFIG, json.dumps(DEFAULTS, indent=2) + "\n")
        try:
            with CONFIG.open(encoding="utf-8") as f:
                settings = normalize(json.load(f))
        except (OSError, ValueError):
            settings = dict(DEFAULTS)
        write_atomic(HUD, mango_config(settings))
        if native_renderer_available():
            install_native_manifest()
            write_atomic(native_hud_path(), mango_config(settings, native_spacing=True))
            install_short_launcher()
        self._current_settings = settings
        self._tdp_last_value = None
        self._tdp_last_source = "Nije provjereno"
        self._tdp_context_game = None
        self._tdp_context_known = False
        self._tdp_context_at = 0.0
        write_atomic(draw_path(), draw_text(settings) + "\n")
        write_atomic(tdp_path(), tdp_text(settings, None) + "\n")
        self._draw_task = asyncio.create_task(self._draw_loop())
        self._tdp_task = asyncio.create_task(self._tdp_loop())

    async def _draw_loop(self):
        while True:
            await asyncio.sleep(2)
            try:
                value = draw_text(getattr(self, "_current_settings", DEFAULTS))
                # No need to replace the file if its content did not change.
                if not draw_path().is_file() or draw_path().read_text() != value + "\n":
                    write_atomic(draw_path(), value + "\n")
            except OSError:
                # A temporary filesystem failure must not kill the Decky backend.
                pass

    async def _tdp_loop(self):
        while True:
            try:
                current_game = getattr(self, "_tdp_context_game", None)
                context_known = (getattr(self, "_tdp_context_known", False)
                                 and time.monotonic() - getattr(self, "_tdp_context_at", 0.0) < 25)
                watts, source = await asyncio.to_thread(
                    read_tdp_limit, appid=current_game if context_known else None,
                    context_known=context_known)
                if current_game != getattr(self, "_tdp_context_game", None):
                    continue
                self._tdp_last_value = watts
                self._tdp_last_source = source
                settings = getattr(self, "_current_settings", DEFAULTS)
                value = tdp_text(settings, watts) + "\n"
                if not tdp_path().is_file() or tdp_path().read_text() != value:
                    write_atomic(tdp_path(), value)
            except OSError:
                self._tdp_last_value = None
                self._tdp_last_source = "Greška čitanja"
                try:
                    write_atomic(tdp_path(), tdp_text(
                        getattr(self, "_current_settings", DEFAULTS), None) + "\n")
                except OSError:
                    pass
            await asyncio.sleep(5)

    async def _unload(self):
        for key in ("_draw_task", "_tdp_task"):
            task = getattr(self, key, None)
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
        self._current_settings = data
        write_atomic(draw_path(), draw_text(data) + "\n")
        write_atomic(tdp_path(), tdp_text(data, getattr(self, "_tdp_last_value", None)) + "\n")
        write_atomic(HUD, mango_config(data))
        if native_renderer_available():
            install_native_manifest()
            write_atomic(native_hud_path(), mango_config(data, native_spacing=True))
            install_short_launcher()
        return {"ok": True, "settings": data, "config_path": str(HUD)}

    async def set_tdp_game_context(self, appid=None):
        """Steam Router reports the stable PDC game key, even with QAM closed."""
        if appid is not None:
            if (not isinstance(appid, str) or not (0 < len(appid) <= 160)
                    or any(ord(ch) < 32 for ch in appid)):
                return {"ok": False}
        previous = getattr(self, "_tdp_context_game", None)
        known = getattr(self, "_tdp_context_known", False)
        self._tdp_context_game = appid
        self._tdp_context_known = True
        self._tdp_context_at = time.monotonic()
        if not known or previous != appid:
            self._tdp_last_value = None
            self._tdp_last_source = "Očitavam profil aktivne igre"
            try:
                write_atomic(tdp_path(), tdp_text(
                    getattr(self, "_current_settings", DEFAULTS), None) + "\n")
            except OSError:
                pass
        return {"ok": True}

    async def get_tdp_status(self):
        known = (getattr(self, "_tdp_context_known", False)
                 and time.monotonic() - getattr(self, "_tdp_context_at", 0.0) < 25)
        game = getattr(self, "_tdp_context_game", None) if known else None
        details = await asyncio.to_thread(
            tdp_source_diagnostics, appid=game, context_known=known)
        details = ("Kontekst: " +
                   ("aktivna igra" if game else "nema igre" if known else "nije potvrđen") +
                   " | " + details)
        watts = getattr(self, "_tdp_last_value", None)
        source = getattr(self, "_tdp_last_source", "Nije provjereno")
        is_configured = watts is not None and source.startswith("Panel de Control")
        return {
            "readable": watts is not None,
            "hardware_verified": watts is not None and not is_configured,
            "watts": watts,
            "source": source,
            "description": (
                ("Postavljeni TDP: " if is_configured else "Očitani TDP limit: ") +
                str(watts) + "W · " + source
                if watts is not None else
                "TDP -- · " + source + ". RyzenAdj i MSI firmware nisu dali očitanje; "
                "provjeri Panel de Control profile."
            ) + "\nIzvori: " + details
        }

    async def get_renderer_status(self):
        """Detect both Vulkan request propagation and actual native library maps.

        Files existing on disk don't prove the game loaded them. The backend is
        normally root in Decky and can inspect /proc, but sandboxing may limit
        some reads, so the counts are evidence rather than a definitive error.
        """
        expected = str(experimental_library().resolve())
        found_native = 0
        found_other_hud = 0
        layer_request = 0
        config_request = 0
        path_request = 0
        process_count = 0
        environment_accessible = 0
        for process in pathlib.Path("/proc").iterdir():
            if not process.name.isdecimal():
                continue
            process_count += 1
            try:
                with (process / "maps").open("r", encoding="utf-8", errors="replace") as mapping:
                    paths = [line.split()[-1] for line in mapping if "libMangoHud.so" in line]
                    if any(p == expected or p.startswith(expected + " ") for p in paths):
                        found_native += 1
                    elif paths:
                        found_other_hud += 1
            except (OSError, PermissionError):
                pass
            try:
                with (process / "environ").open("rb") as env_file:
                    raw = env_file.read(262144)
                environment_accessible += 1
                envs = raw.split(bytes([0]))
                if any(x.startswith(b"VK_INSTANCE_LAYERS=") and
                       EXPERIMENTAL_LAYER_NAME.encode() in x for x in envs):
                    layer_request += 1
                if any(x.startswith(b"MANGOHUD_CONFIGFILE=") and
                       b"MangoHud-experimental.conf" in x for x in envs):
                    config_request += 1
                if any(x.startswith(b"VK_ADD_LAYER_PATH=") and
                       b"ClawMetrics" in x for x in envs):
                    path_request += 1
            except (OSError, PermissionError):
                pass
        if found_native:
            reason = "Aktivno: modificirana biblioteka učitana je u igri."
        elif layer_request:
            reason = ("Komanda je stigla do procesa, ali Vulkan sloj NIJE učitan. "
                      "Mogući uzrok: Steam Runtime, duplikat sloja ili nedostajuća biblioteka.")
        elif config_request:
            reason = ("Proces vidi naš konfiguracijski profil, ali ne i zahtjev "
                      "za prilagođenim Vulkan slojem.")
        else:
            reason = ("Nema dokaza da je eksperimentalna komanda stigla do igre. "
                      "To može biti zbog Steam Runtime okruženja ili nedostupnih /proc podataka.")
        return {
            "native_loaded": found_native > 0,
            "native_processes": found_native,
            "stock_processes": found_other_hud,
            "layer_requests": layer_request,
            "config_requests": config_request,
            "path_requests": path_request,
            "processes_seen": process_count,
            "environments_read": environment_accessible,
            "manifest_in_user_location": user_vulkan_manifest().is_file(),
            "reason": reason
        }

    async def get_info(self):
        return {
            "config_path": str(HUD),
            "launch_option": "MANGOHUD_CONFIGFILE=" + shlex.quote(str(HUD)) + " mangohud %command%",
            "config_readable": HUD.is_file() and bool(HUD.stat().st_mode & 0o004),
            "font_path": sans_font(),
            "font_ready": font_path().is_file() and hashlib.sha256(font_path().read_bytes()).hexdigest() == FONT_SHA256,
            "condensed_fonts_ready": condensed_fonts_ready(),
            "layout_spacing_supported": native_renderer_available(),
            # Binary presence does not mean the SteamOS game actually loads it.
            "experimental_config_readable": (
                native_hud_path().is_file()
                and bool(native_hud_path().stat().st_mode & 0o004)
            ),
            "short_launcher_ready": short_launcher_ready(),
            "short_launch_option": (shlex.quote(str(short_launcher_path())) + " %command%"
                                    if short_launcher_ready() else ""),
            "experimental_launch_option": (
                "env VK_ADD_LAYER_PATH=" + shlex.quote(str(experimental_manifest().parent))
                + " VK_INSTANCE_LAYERS=" + EXPERIMENTAL_LAYER_NAME
                + " DISABLE_MANGOHUD=1"
                + " MANGOHUD_CONFIGFILE=" + shlex.quote(str(native_hud_path()))
                + " %command%" if native_renderer_available() else ""
            ),
            "tdp_note": ("TDP: " + str(getattr(self, "_tdp_last_value", None)) + "W · " +
                         getattr(self, "_tdp_last_source", "") if
                         getattr(self, "_tdp_last_value", None) is not None else
                         "TDP -- · očitavanje limita nije dostupno."),
            "power_note": "CPU/GPU sensor power is not the same as total system battery draw."
        }
