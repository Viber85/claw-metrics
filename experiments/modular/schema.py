"""Strict reader for DevLab modular-layout v1; never changes live HUD settings."""
import json
import math

TOKENS = set(('fps.label fps.value fps.ms fps.average fps.low1 cpu.label cpu.load cpu.temp '
              'cpu.clock cpu.power gpu.label gpu.load gpu.temp gpu.clock gpu.power gpu.junction '
              'gpu.fan gpu.voltage ram.label ram.value ram.game ram.swap vram.label vram.value '
              'vram.temp vram.clock battery.label battery.value battery.time battery.power '
              'time.value tdp.value graph').split())
ANCHORS = ('top-left', 'top-center', 'top-right', 'bottom-left', 'bottom-center', 'bottom-right')


def validate_layout(value):
    """Return a detached, whitelisted document or reject the whole document."""
    if not isinstance(value, dict) or value.get('schema') != 'claw-modular-layout' or type(value.get('version')) is not int or value['version'] != 1 or value.get('anchor') not in ANCHORS:
        raise ValueError('Expected modular layout v1')
    ids = set()

    def number(v, low, high):
        if type(v) not in (int, float) or not math.isfinite(v) or not low <= v <= high:
            raise ValueError('Invalid numeric layout value')
        return v

    def color(v):
        if not isinstance(v, str) or (v and (len(v) != 7 or v[0] != '#' or any(c not in '0123456789abcdefABCDEF' for c in v[1:]))):
            raise ValueError('Invalid color')
        return v

    def visit(v, depth):
        if len(ids) >= 96 or depth > 8 or not isinstance(v, dict):
            raise ValueError('Layout exceeds 96 nodes or 8 nesting levels')
        key = v.get('id')
        if not isinstance(key, str) or len(key) > 100 or key in ids:
            raise ValueError('Invalid or duplicate node ID')
        ids.add(key)
        if v.get('kind') not in ('group', 'metric') or not isinstance(v.get('name'), str) or len(v['name']) > 80 or type(v.get('visible')) is not bool or v.get('axis') not in ('row', 'column') or v.get('align') not in ('start', 'center', 'end') or type(v.get('outline')) is not bool or not isinstance(v.get('children'), list):
            raise ValueError('Invalid node')
        if v['kind'] == 'metric' and (not isinstance(v.get('token'), str) or v['token'] not in TOKENS or v['children']):
            raise ValueError('Invalid metric')
        out = {k: v[k] for k in ('id', 'kind', 'name', 'visible', 'axis', 'align', 'outline')}
        out['token'] = v['token'] if v['kind'] == 'metric' else 'fps.value'
        for key, low, high in (('gap', 0, 80), ('padding', 0, 80), ('scale', 50, 250), ('opacity', 0, 100), ('width', 40, 1000), ('height', 16, 240)):
            out[key] = number(v.get(key), low, high)
        out['color'] = color(v.get('color'))
        out['background'] = color(v.get('background'))
        out['children'] = [visit(c, depth + 1) for c in v['children']]
        return out

    root = visit(value.get('root'), 0)
    if root['kind'] != 'group':
        raise ValueError('Root must be a group')
    return {'schema': 'claw-modular-layout', 'version': 1, 'anchor': value['anchor'],
            'x': number(value.get('x'), 0, 2000), 'y': number(value.get('y'), 0, 2000), 'root': root}


def load_layout(text):
    if len(text.encode('utf-8')) > 1024 * 1024:
        raise ValueError('Layout exceeds 1 MiB')
    try:
        return validate_layout(json.loads(text))
    except (RecursionError, TypeError, KeyError) as error:
        raise ValueError('Malformed layout') from error
