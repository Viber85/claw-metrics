"""Portable overlay designs. No device paths, commands or telemetry are imported."""
import copy
import json
import math
import pathlib
import re
from claw_modular import validate_layout

_ROOT = pathlib.Path(__file__).resolve().parent
if not (_ROOT / "assets/overlay-design-rules.json").is_file(): _ROOT = _ROOT.parent
RULES = json.loads((_ROOT / "assets/overlay-design-rules.json").read_text())


def appearance(value):
    if not isinstance(value, dict):
        raise ValueError("Expected appearance settings")
    out = copy.deepcopy(RULES["defaults"])
    def number(v, low, high):
        if type(v) not in (int, float) or not math.isfinite(v) or int(v) != v or not low <= v <= high:
            raise ValueError("Invalid appearance number")
        return v
    def color(v):
        if not isinstance(v, str) or not re.fullmatch(r"#?[0-9a-fA-F]{6}", v):
            raise ValueError("Invalid appearance color")
        return v.lstrip("#").upper()
    for key, bounds in RULES["ranges"].items():
        if key in value: out[key] = number(value[key], *bounds)
    for key, choices in RULES["enums"].items():
        if key in value:
            if value[key] not in choices: raise ValueError("Invalid " + key)
            out[key] = value[key]
    for key in RULES["booleans"]:
        if key in value:
            if type(value[key]) is not bool: raise ValueError("Invalid " + key)
            out[key] = value[key]
    for key, allowed in (("colors", RULES["colors"]), ("token_colors", RULES["tokens"]), ("token_weights", RULES["tokens"]), ("custom_labels", RULES["labels"])):
        if key not in value: continue
        if not isinstance(value[key], dict): raise ValueError("Invalid " + key)
        for token, v in value[key].items():
            if token not in allowed: continue
            if key == "token_weights":
                if v not in RULES["enums"]["font_weight"]: raise ValueError("Invalid token weight")
            elif key == "custom_labels":
                if not isinstance(v, str) or len(v) > 24 or any(ord(c) < 32 or ord(c) == 127 or c in "=," for c in v): raise ValueError("Invalid label")
                v = re.sub(r"\s+", " ", v).strip()
                if not v: continue
            else: v = color(v)
            out[key][token] = v
    if "background" in value:
        b = value["background"]
        if not isinstance(b, dict): raise ValueError("Invalid background")
        target = out["background"]
        for key in ("color", "outline_color"):
            if key in b: target[key] = color(b[key])
        if "mode" in b:
            if b["mode"] not in ("solid", "linear", "radial"): raise ValueError("Invalid background mode")
            target["mode"] = b["mode"]
        if "outline_enabled" in b:
            if type(b["outline_enabled"]) is not bool: raise ValueError("Invalid outline")
            target["outline_enabled"] = b["outline_enabled"]
        for key, lo, hi in (("angle",0,360),("outline_width",1,6),("outline_opacity",0,100),("center_x",0,100),("center_y",0,100),("radius",1,200)):
            if key in b: target[key] = number(b[key],lo,hi)
        if "stops" in b:
            if not isinstance(b["stops"], list) or not 2 <= len(b["stops"]) <= 8: raise ValueError("Expected 2–8 gradient stops")
            target["stops"] = [{"position":number(s["position"],0,100),"color":color(s["color"])} for s in b["stops"]]
            target["stops"].sort(key=lambda s:s["position"])
    return out


def validate_design(value):
    if not isinstance(value, dict): raise ValueError("Expected overlay design")
    if value.get("schema") == "claw-modular-layout":
        return {"layout":validate_layout(value),"appearance":{}}  # Legacy retains device appearance.
    if value.get("schema") != "claw-overlay-design" or type(value.get("version")) is not int or value["version"] != 1:
        raise ValueError("Expected claw-overlay-design v1")
    return {"schema":"claw-overlay-design","version":1,"layout":validate_layout(value.get("layout")),"appearance":appearance(value.get("appearance"))}


def load_design(text):
    if len(text.encode("utf-8")) > 1024 * 1024: raise ValueError("Design exceeds 1 MiB")
    try:
        return validate_design(json.loads(text))
    except (RecursionError, TypeError, KeyError, AttributeError) as error:
        raise ValueError("Malformed overlay design") from error


def export_design(settings, layout=None):
    return validate_design({"schema":"claw-overlay-design","version":1,"layout":layout if layout is not None else settings.get("modular_layout"),"appearance":settings})
