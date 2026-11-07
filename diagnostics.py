"""Opt-in, bounded session evidence; never changes hardware or OS configuration."""
import asyncio
import csv
import collections
import json
import os
import pathlib
import platform
import re
import subprocess
import time
import threading
import uuid
import zipfile

MAX_BYTES = 8 * 1024 * 1024
UI_EVENTS = {'editor_open','editor_mount','editor_exit_request','editor_unmount',
             'editor_apply_start','editor_apply_done','editor_dispose','ui_error',
             'settings_queued','settings_save_start','settings_saved','settings_error'}
_ui_lock = threading.Lock()
LOG_QUERIES = {
    'gpu-errors.log': ['--case-sensitive=no', '--grep', r'amdgpu|\bdrm\b|ring.*timeout|gpu.*(hang|reset|fault|timeout)|oom|out of memory'],
    # journalctl --grep searches MESSAGE, not the printed process prefix.
    # PluginLoader's MESSAGE can start with [CSS_Loader], with no "decky".
    'decky.log': ['--case-sensitive=no', '--grep', r'decky|pluginloader|plugin_loader|claw.?metrics|css_loader|css_browserhook|steamwebhelper|segfault|coredump'],
    'steam-ui-journal.log': ['--case-sensitive=no', '--grep', r'Runtime\.evaluate|css_browserhook|CEF|JS context|Hook.*lost|evaluate failed|Uncaught|TypeError|RangeError|ReferenceError|Maximum update depth|focus.*(error|fail)'],
    'input-journal.log': ['--case-sensitive=no', '--grep', r'inputplumber::|Loading gamepad profile|Setting target devices|intercept.*mode'],
    'system-warnings.log': ['--priority', 'warning'],
}


def read_text(path, limit=65536):
    try:
        with pathlib.Path(path).open(encoding='utf-8', errors='replace') as stream:
            return stream.read(limit)
    except OSError:
        return ''


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temp = path.with_suffix('.tmp')
    with temp.open('w', encoding='utf-8') as stream:
        os.chmod(temp, 0o600)
        json.dump(value, stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)
    # Persist the directory entry too, so a reboot can recover the marker.
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def redact(text):
    text = re.sub(r'/home/[^/\s]+', '/home/USER', text)
    text = re.sub(r'(?i)\b(token|password|authorization|secret|api_key)\s*[:=]\s*\S+', r'\1=[REDACTED]', text)
    text = re.sub(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '[IP]', text)
    return text


def record_ui_event(base, event, detail=''):
    if event not in UI_EVENTS:
        raise ValueError('Unknown UI event')
    root = pathlib.Path(base) / 'diagnostics'
    entry = json.dumps({'at': time.time(), 'monotonic': time.monotonic(),
                        'boot_id': read_text('/proc/sys/kernel/random/boot_id',128).strip(), 'event': event,
                        'detail': redact(str(detail))[:400]}, ensure_ascii=True) + '\n'
    with _ui_lock:
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        target = root / 'editor-ui.jsonl'
        if target.exists() and target.stat().st_size > 60000:
            lines = target.read_bytes()[-30000:].splitlines()[1:]
            target.write_bytes(b'\n'.join(lines) + b'\n')
        with target.open('a', encoding='utf-8') as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(entry);stream.flush();os.fsync(stream.fileno())


def command_result(args):
    """Bound memory, wall time and output, including when journald is absent."""
    try:
        import tempfile
        with tempfile.TemporaryFile() as output:
            process = subprocess.Popen(args, stdout=output, stderr=subprocess.STDOUT)
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                return {'ok': False, 'returncode': None, 'text': 'Unavailable: command timed out\n'}
            total = output.seek(0, os.SEEK_END)
            # Preserve the newest evidence. Reading the first 512 KiB of a
            # large journal excerpt can lose the actual error at its end.
            offset = max(0, total - 512 * 1024)
            output.seek(offset)
            payload = output.read(512 * 1024)
            return {'ok': process.returncode == 0, 'returncode': process.returncode,
                    'text': redact(payload.decode('utf-8', 'replace')),
                    'queried_output_bytes': total, 'captured_bytes': len(payload),
                    'byte_truncated': offset > 0}
    except OSError as error:
        return {'ok': False, 'returncode': None,
                'text': 'Unavailable: ' + type(error).__name__ + '\n'}


def report_summary(meta, results, ui_events):
    lines=['Claw Metrics diagnostic summary',
           'Session: '+str(meta.get('id','unknown')),
           'Plugin version: '+str(meta.get('version','unknown')),
           'Session state: '+str(meta.get('state','unknown')),
           'Cause: not determined. Log matches and interrupted sessions do not identify a culprit.',
           '', 'Collected journal excerpts (same boot/session window):']
    for name, result in results.items():
        clipped=result.get('byte_truncated')
        lines.append(f"- {name}: {'available' if result['ok'] else 'UNAVAILABLE'}; "
                     f"byte truncation: {'yes' if clipped else 'no' if clipped is False else 'not reported'}")
    lines += ['', 'Repeated messages in the captured general journal (raw logs retained):']
    counts=collections.Counter()
    for line in results['system-journal.log']['text'].splitlines():
        message=re.sub(r'^\S+\s+\S+\s+', '',line)
        # Collapse a changing uptime counter, not the actual message content.
        message=re.sub(r'(:\s+(?:WARNING:\s+)?)\d+\s+(\[)',r'\1<uptime> \2',message)
        counts[message]+=1
    repeats=[(message,count) for message,count in counts.most_common(10) if count>1]
    lines += [f'- {count} times: {message[:400]}' for message,count in repeats] or ['- No repeated messages found in this excerpt.']
    lines += ['', f'UI events captured for this boot/session: {len(ui_events)}']
    if not ui_events:lines.append('No matching UI trace. This does not mean that no UI failure occurred.')
    for event in sorted(ui_events,key=lambda row:row['at'])[-10:]:
        lines.append(f"- {event['at']}: {event.get('event','unknown')} {event.get('detail','')}")
    lines += ['', 'SteamUI journal excerpts are not a JavaScript stack trace. Missing/limited logs cannot rule out a fault.']
    return redact('\n'.join(lines)+'\n')


def compatibility_snapshot(sys_root=pathlib.Path('/sys'), os_release=pathlib.Path('/etc/os-release')):
    """Read-only discovery; available nodes do not prove in-game compatibility."""
    def value(path):
        return read_text(path, 4096).strip() or None
    sensors = []
    for hw in sorted((sys_root / 'class/hwmon').glob('hwmon*')):
        channels = []
        for pattern in ('temp*_input', 'power*_average', 'power*_input', 'power*_cap', 'fan*_input'):
            for node in sorted(hw.glob(pattern)):
                channels.append({'node': str(node), 'label': value(node.with_name(node.name.rsplit('_', 1)[0] + '_label')),
                                 'readable': value(node) is not None})
        sensors.append({'name': value(hw / 'name'), 'channels': channels})
    cards = []
    for card in sorted((sys_root / 'class/drm').glob('card*')):
        if not re.fullmatch(r'card\d+', card.name):
            continue
        cards.append({'card': card.name, 'vendor': value(card / 'device/vendor'),
                      'device': value(card / 'device/device'),
                      'driver': (card / 'device/driver').resolve().name if (card / 'device/driver').exists() else None,
                      'gpu_busy_readable': value(card / 'device/gpu_busy_percent') is not None})
    return {'schema_version': 1, 'captured_at': time.time(), 'os_release': value(os_release),
            'kernel': platform.release(), 'architecture': platform.machine(),
            'device': {key: value(sys_root / 'class/dmi/id' / key) for key in
                       ('sys_vendor', 'product_name', 'product_version', 'board_name')},
            'drm': cards, 'hwmon': sensors,
            'batteries': [{'name': battery.name, 'capacity_readable': value(battery / 'capacity') is not None,
                           'power_readable': value(battery / 'power_now') is not None,
                           'current_readable': value(battery / 'current_now') is not None}
                          for battery in sorted((sys_root / 'class/power_supply').glob('*'))
                          if value(battery / 'type') == 'Battery'],
            'support_status': 'Unverified: sensor discovery is not validation of readings, TDP control or Vulkan injection.'}


def telemetry():
    values = {'load_1m': None, 'mem_available_kib': None, 'gpu_busy_percent': None,
              'gpu_temp_c': None, 'gpu_power_w': None, 'battery_percent': None,
              'battery_power_w': None}
    try:
        values['load_1m'] = os.getloadavg()[0]
    except OSError:
        pass
    for line in read_text('/proc/meminfo').splitlines():
        if line.startswith('MemAvailable:'):
            values['mem_available_kib'] = int(line.split()[1])
    # Discover AMD DRM and battery nodes instead of assuming card0/BAT0.
    for card in sorted(pathlib.Path('/sys/class/drm').glob('card[0-9]*')):
        if not card.name[4:].isdigit():
            continue
        if read_text(card / 'device/vendor').strip() != '0x1002':
            continue
        probes = [('gpu_busy_percent', card / 'device/gpu_busy_percent', 1)]
        for hw in sorted((card / 'device/hwmon').glob('hwmon*')):
            probes += [('gpu_temp_c', hw / 'temp1_input', 1000),
                       ('gpu_power_w', hw / 'power1_average', 1000000)]
        for key, path, divisor in probes:
            try:
                values[key] = float(read_text(path).strip()) / divisor
            except ValueError:
                pass
        break
    for battery in sorted(pathlib.Path('/sys/class/power_supply').glob('*')):
        if read_text(battery / 'type').strip() != 'Battery':
            continue
        for key, filename, divisor in [('battery_percent', 'capacity', 1),
                                        ('battery_power_w', 'power_now', 1000000)]:
            try:
                values[key] = float(read_text(battery / filename).strip()) / divisor
            except ValueError:
                pass
        break
    return values


class SessionRecorder:
    def __init__(self, base, version, settings, context):
        self.root = pathlib.Path(base) / 'diagnostics'
        self.version = version
        self.settings = settings
        self.context = context
        self.task = None
        self.current = None
        self.error = ''
        self.lock = asyncio.Lock()
        self.boot_id = read_text('/proc/sys/kernel/random/boot_id').strip()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        for directory in self.root.glob('session-*'):
            try:
                meta = json.loads((directory / 'session.json').read_text())
                if meta.get('state') == 'recording':
                    meta['state'] = 'interrupted'
                    meta['recovery_note'] = 'Unclean end; may be reboot, Decky crash, kill or power loss. Cause unknown.'
                    atomic_json(directory / 'session.json', meta)
            except (OSError, ValueError):
                pass

    def status(self):
        sessions = []
        for directory in sorted(self.root.glob('session-*'), reverse=True):
            try:
                meta = json.loads((directory / 'session.json').read_text())
                sessions.append({key: meta.get(key) for key in ('id', 'state', 'started_at', 'last_sample_at', 'samples')})
            except (OSError, ValueError):
                pass
        return {'recording': self.task is not None and not self.task.done(),
                'sessions': sessions, 'error': self.error}

    async def start(self):
        async with self.lock:
            if self.task is not None and not self.task.done():
                return self.status()
            # Retain at most five bounded sessions. Reports can be copied before rotation.
            previous = sorted((p for p in self.root.glob('session-*') if p.is_dir()), reverse=True)
            import shutil
            for directory in previous[4:]:
                shutil.rmtree(directory)
                (self.root / (directory.name + "-CrashReport.zip")).unlink(missing_ok=True)
            sid = 'session-' + time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()) + '-' + uuid.uuid4().hex[:8]
            self.current = self.root / sid
            self.current.mkdir(mode=0o700)
            self.meta = {'id': sid, 'state': 'recording', 'version': self.version,
                         'boot_id': self.boot_id, 'started_at': time.time(), 'samples': 0,
                         'limitations': '5 second sampling; final seconds may be lost. Interruption does not identify a cause. FPS is unavailable to this sampler.',
                         'os_release': read_text('/etc/os-release'), 'kernel': platform.release(),
                         'machine': platform.machine(), 'settings': self.settings(),
                         'compatibility': await asyncio.to_thread(compatibility_snapshot)}
            self.error = ''
            await asyncio.to_thread(self._sample)
            self.stop_event = asyncio.Event()
            self.task = asyncio.create_task(self._loop())
            return self.status()

    def _sample(self):
        row = {'timestamp': time.time(), 'game_id': self.context(), **telemetry()}
        path = self.current / 'telemetry.csv'
        if path.exists() and path.stat().st_size >= MAX_BYTES:
            self.meta['state'] = 'size_limit'
            self.meta['ended_at'] = time.time()
            atomic_json(self.current / 'session.json', self.meta)
            return False
        new = not path.exists()
        with path.open('a', newline='', encoding='utf-8') as stream:
            os.chmod(path, 0o600)
            writer = csv.DictWriter(stream, fieldnames=list(row))
            if new:
                writer.writeheader()
            writer.writerow(row)
            stream.flush()
            os.fsync(stream.fileno())
        self.meta['samples'] += 1
        self.meta['last_sample_at'] = row['timestamp']
        self.meta['last_settings'] = self.settings()
        atomic_json(self.current / 'session.json', self.meta)
        return True

    async def _loop(self):
        try:
            while True:
                try:
                    await asyncio.wait_for(self.stop_event.wait(), timeout=5)
                    break
                except asyncio.TimeoutError:
                    pass
                if not await asyncio.to_thread(self._sample):
                    break
        except Exception as error:
            self.error = type(error).__name__ + ': ' + str(error)[:160]
            # Keep the last durable marker; recovery will identify the interruption.

    async def stop(self, reason='stopped'):
        async with self.lock:
            if self.task:
                # Wake the loop and wait for any in-flight fsync before changing metadata.
                self.stop_event.set()
                await self.task
                self.task = None
                if self.meta.get('state') == 'recording' and not self.error:
                    self.meta['state'] = reason
                    self.meta['ended_at'] = time.time()
                    await asyncio.to_thread(atomic_json, self.current / 'session.json', self.meta)
            return self.status()

    def export(self, session_id):
        if not isinstance(session_id, str) or not re.fullmatch(r'session-\d{8}T\d{6}Z-[a-f0-9]{8}', session_id):
            raise ValueError('Invalid session ID')
        directory = self.root / session_id
        meta = json.loads((directory / 'session.json').read_text())
        boot = meta.get('boot_id', '')
        try:
            journal_boot = uuid.UUID(boot).hex
        except (ValueError, TypeError, AttributeError):
            journal_boot = None
        journal_result = command_result(['journalctl', '--no-pager', '-o', 'short-iso', '-n', '2500',
                           '--since', '@' + str(int(meta['started_at'])),
                           '--until', '@' + str(int(meta.get('ended_at', meta.get('last_sample_at', meta['started_at']))) + 15),
                           '-b', journal_boot]) if journal_boot else {
                               'ok': False, 'returncode': None,
                               'text': 'Unavailable: invalid session boot ID; no unrelated boot queried.\n'}
        journal = journal_result['text']
        # Filter inside journald, BEFORE its line limit. RGB floods in the general
        # log must never displace independent GPU, Decky and warning evidence.
        common = ['journalctl', '--no-pager', '-o', 'short-iso', '-n', '2500',
                  '--since', '@' + str(int(meta['started_at'])),
                  '--until', '@' + str(int(meta.get('ended_at', meta.get('last_sample_at', meta['started_at']))) + 15),
                  '-b', journal_boot]
        results = {}
        for name, filters in LOG_QUERIES.items():
            result = command_result(common + filters) if journal_boot else dict(journal_result)
            # journalctl returns 1 for a successful grep with no matches.
            if result['returncode'] == 1 and result['text'].strip() == '-- No entries --':
                result = {**result, 'ok': True}
            results[name] = result
        all_results = {'system-journal.log':journal_result, **results}
        start = float(meta['started_at'])
        end = float(meta.get('ended_at',meta.get('last_sample_at',start))) + 15
        ui_events=[]
        for line in read_text(self.root / 'editor-ui.jsonl',65536).splitlines():
            try:
                entry=json.loads(line)
                if entry.get('boot_id')==boot and start-1<=float(entry['at'])<=end:
                    ui_events.append(entry)
            except (ValueError,TypeError,KeyError):
                continue
        details = {'format_version': 4, 'journal_ok': journal_result['ok'],
                   'journal_returncode': journal_result['returncode'],
                   'log_queries': {name: {'ok': result['ok'], 'returncode': result['returncode'],
                                         'line_limit': 2500, 'byte_limit': 512 * 1024,
                                         'line_limit_reached':None if result.get('byte_truncated') else len(result['text'].splitlines())>=2500,
                                         'queried_output_bytes':result.get('queried_output_bytes'),
                                         'captured_bytes':result.get('captured_bytes'),
                                         'byte_truncated':result.get('byte_truncated')}
                                   for name, result in all_results.items()},
                   'ui_event_count':len(ui_events),
                   'journal_boot_id': journal_boot, 'exported_at': time.time(), 'session_boot_id': boot,
                   'current_boot_id': self.boot_id, 'journal_scope': 'Recorded boot and session time window. Each log is independently queried and bounded; logs may be incomplete or unavailable.',
                   'privacy': 'Home usernames, common credentials and IPv4 redacted. Review logs before sharing. No automatic upload.',
                   'cause': 'Undetermined; compare sessions with and without the overlay.'}
        target = self.root / (session_id + '-CrashReport.zip')
        temp = target.with_suffix('.tmp')
        try:
            with temp.open('wb') as raw:
                os.chmod(temp, 0o600)
                with zipfile.ZipFile(raw, 'w', zipfile.ZIP_DEFLATED) as archive:
                    archive.writestr('session.json', redact(json.dumps(meta, indent=2)))
                    archive.writestr('telemetry.csv', redact(read_text(directory / 'telemetry.csv', MAX_BYTES + 4096)))
                    archive.writestr('system-journal.log', journal)
                    for name, result in results.items():
                        archive.writestr(name, result['text'] if result['ok'] else
                                         'Unavailable: log collection failed.\n' + result['text'])
                    archive.writestr('compatibility.json', redact(json.dumps(meta.get('compatibility',
                                     {'support_status': 'Unavailable: session predates capability discovery.'}), indent=2)))
                    archive.writestr('diagnostics.json', json.dumps(details, indent=2))
                    archive.writestr('editor-ui.jsonl', redact(''.join(json.dumps(event)+'\n' for event in ui_events)))
                    archive.writestr('SUMMARY.txt',report_summary(meta,all_results,ui_events))
                raw.flush()
                os.fsync(raw.fileno())
            os.replace(temp, target)
        finally:
            temp.unlink(missing_ok=True)
        # Backend is root; make the report readable by the desktop owner only.
        owner = self.root.parent.parent.parent.stat()
        if os.geteuid() == 0:
            for path in (self.root, target):
                os.chown(path, owner.st_uid, owner.st_gid)
        return {'path': str(target), 'bytes': target.stat().st_size}


def overlay_loaded(library, proc=pathlib.Path('/proc')):
    """Evidence of our exact mapped library; a launch request alone is insufficient.

    None means inspection is restricted, so it must not end a recording.
    """
    libraries = library if isinstance(library, (list, tuple, set)) else (library,)
    expected = {str(pathlib.Path(path).resolve()) for path in libraries}
    restricted = False
    try:
        processes = list(proc.iterdir())
    except OSError:
        return None
    for process in processes:
        if not process.name.isdecimal():
            continue
        try:
            with (process / 'maps').open(encoding='utf-8', errors='replace') as stream:
                for line in stream:
                    fields = line.rstrip('\n').split(None, 5)
                    if len(fields) == 6 and fields[5].removesuffix(' (deleted)') in expected:
                        return True
        except PermissionError:
            restricted = True
        except OSError:
            pass  # Process exited during the scan.
    return None if restricted else False


class OverlayRecording:
    """Debounced lifecycle independent of QAM and frontend game reporting."""
    def __init__(self, recorder):
        self.recorder = recorder
        self.lock = asyncio.Lock()
        self.paused = False
        self.auto_session = False
        self.absent = 0

    async def update(self, loaded):
        async with self.lock:
            if loaded is None:
                self.absent = 0
                return
            if loaded:
                self.absent = 0
                if not self.paused and not self.recorder.status()['recording']:
                    # Do not create repeated sessions after disk errors or size limit.
                    if not self.auto_session:
                        await self.recorder.start()
                        self.auto_session = True
                return
            self.absent += 1
            if self.absent < 3:
                return
            if self.auto_session:
                await self.recorder.stop('overlay_unloaded')
            self.auto_session = False
            self.paused = False

    async def manual(self, start):
        async with self.lock:
            self.paused = not start
            self.auto_session = False
            return await (self.recorder.start() if start else self.recorder.stop())
