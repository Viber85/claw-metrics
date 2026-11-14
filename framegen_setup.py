"""Discover games and configure their optional FidelityFX frame telemetry."""
import argparse
from contextlib import contextmanager
from dataclasses import dataclass
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import stat
import struct
import tempfile

DLL = 'amd_fidelityfx_framegeneration_dx12.dll'
BACKUP = 'amd_fidelityfx_framegeneration_dx12.claw-original.dll'
PREVIOUS_PROXIES = {
    'b1d6ec2615f336c6074beb4ef71afa5f2c43c1d735eb0b9d02793ec9bf7f0570',
    '53484b853f60d95fa13655759e16427625cfbbc26ffb1a49ad3395647442f49d',
    '89b16b63a934f657fbd8dc8470331a6bd745a1e5f7cfad7d63edc591a948b1f5',
}
REQUIRED_EXPORTS = {b'ffxCreateContext', b'ffxDestroyContext', b'ffxConfigure', b'ffxQuery', b'ffxDispatch'}
KV_TOKEN = re.compile(r'//[^\r\n]*|"(?:\\.|[^"\\])*"|[{}]|[^\s{}"]+')


def read_keyvalues(path):
    with path.open(encoding='utf-8-sig') as file:
        content = file.read(2_000_001)
    if len(content) > 2_000_000:
        raise ValueError('Steam library data is too large.')
    tokens = iter(token for token in KV_TOKEN.findall(content) if not token.startswith('//'))

    def decode(token):
        return re.sub(r'\\(["\\])', r'\1', token[1:-1]) if token.startswith('"') else token

    def block(depth):
        if depth > 24:
            raise ValueError('Invalid Steam library data.')
        out = {}
        for key in tokens:
            if key == '}' and depth:
                return out
            if key in ('{', '}'):
                raise ValueError('Invalid Steam library data.')
            value = next(tokens, None)
            if value is None or value == '}':
                raise ValueError('Invalid Steam library data.')
            out[decode(key).lower()] = block(depth + 1) if value == '{' else decode(value)
        if depth:
            raise ValueError('Invalid Steam library data.')
        return out

    return block(0)


def steam_roots(home):
    seen = set()
    for path in ('.local/share/Steam', '.steam/steam', '.steam/root',
                 '.var/app/com.valvesoftware.Steam/.local/share/Steam'):
        root = (home / path).resolve()
        if root.is_dir() and root not in seen:
            seen.add(root)
            yield root


def steam_library_apps(roots):
    for root in roots:
        apps = root / 'steamapps'
        if apps.is_dir():
            yield apps.resolve()
        try:
            libraries = read_keyvalues(apps / 'libraryfolders.vdf').get('libraryfolders', {})
            for key, record in libraries.items():
                if key.isdecimal():
                    path = record.get('path', '') if isinstance(record, dict) else record
                    if Path(path).is_absolute():
                        yield (Path(path) / 'steamapps').resolve()
        except (OSError, ValueError, AttributeError):
            continue


def read_shortcuts(path):
    """Read Steam's binary KeyValues shortcut records without modifying them."""
    with path.open('rb') as file:
        data = file.read(2_000_001)
    if len(data) > 2_000_000:
        raise ValueError('Steam shortcut data is too large.')
    stream = io.BytesIO(data)

    def cstring():
        start = stream.tell()
        end = data.find(b'\0', start)
        if end < 0:
            raise ValueError('Invalid Steam shortcut data.')
        stream.seek(end + 1)
        return data[start:end].decode('utf-8', errors='replace')

    def block(depth=0):
        if depth > 16:
            raise ValueError('Invalid Steam shortcut data.')
        result = {}
        while kind := stream.read(1):
            if kind in (b'\x08', b'\x0b'):
                return result
            key = cstring().lower()
            if kind == b'\x00':
                value = block(depth + 1)
            elif kind == b'\x01':
                value = cstring()
            elif kind == b'\x02':
                raw = stream.read(4)
                if len(raw) != 4:
                    raise ValueError('Truncated Steam shortcut.')
                value = int.from_bytes(raw, 'little')
            else:
                raise ValueError('Unsupported Steam shortcut field.')
            result[key] = value
        if depth:
            raise ValueError('Truncated Steam shortcut.')
        return result

    shortcuts = block().get('shortcuts', {})
    return shortcuts.values() if isinstance(shortcuts, dict) else ()


@dataclass(frozen=True)
class Game:
    appid: str
    name: str
    source: str
    path: Path | None


def game_id(value):
    return (isinstance(value, str) and 1 <= len(value) <= 10 and value.isascii()
            and value.isdecimal() and not value.startswith('0') and int(value) <= 0xffffffff)


def clean_name(name):
    return ' '.join(''.join(c if c.isprintable() else ' ' for c in name).split())[:80]


def discover_games(home):
    roots = list(steam_roots(home))
    games = set()
    for apps in set(steam_library_apps(roots)):
        for manifest in apps.glob('appmanifest_*.acf'):
            appid = manifest.stem.removeprefix('appmanifest_')
            if not game_id(appid):
                continue
            try:
                app = read_keyvalues(manifest).get('appstate', {})
                name = app.get('installdir', '')
                if app.get('appid') != appid or not name or Path(name).name != name or name in ('.', '..'):
                    continue
                common = (apps / 'common').resolve(strict=True)
                location = (common / name).resolve(strict=True)
                if location.is_dir() and location.is_relative_to(common):
                    label = app.get('name')
                    games.add(Game(appid, clean_name(label if isinstance(label, str) else name) or appid,
                                   'Steam', location))
            except (OSError, ValueError, AttributeError, TypeError, RuntimeError):
                continue
    for root in roots:
        for path in (root / 'userdata').glob('[0-9]*/config/shortcuts.vdf'):
            try:
                for record in read_shortcuts(path):
                    if not isinstance(record, dict):
                        continue
                    appid = str(record.get('appid', ''))
                    name, exe = record.get('appname'), record.get('exe')
                    if not game_id(appid) or not isinstance(name, str):
                        continue
                    location = Path(exe.strip('"')) if isinstance(exe, str) else None
                    if not location or not location.is_absolute() or location.suffix.lower() != '.exe':
                        location = None
                    games.add(Game(appid, clean_name(name) or appid, 'Non-Steam', location))
            except (OSError, ValueError):
                continue
    return sorted(games, key=lambda game: (game.name.casefold(), game.source, int(game.appid), str(game.path)))


def find_dll_folder(path, automatic, home):
    if path.name in (DLL, BACKUP):
        if path.is_symlink() or not path.is_file():
            raise ValueError('Select a regular AMD Frame Gen DLL.')
        return path.parent.resolve(strict=True)
    path = path.resolve(strict=True)
    if path.is_file():
        if path.suffix.lower() != '.exe':
            raise ValueError('Select the game EXE or its AMD Frame Gen DLL.')
        # Bootstrap EXEs can live above the game binaries.
        if (path.parent / DLL).is_file() or (path.parent / BACKUP).is_file():
            return path.parent
        path = path.parent
    # Never search an entire home directory or mount from a wrapper shortcut.
    if not path.is_dir() or (automatic and (path == path.parent or home.is_relative_to(path))):
        raise ValueError('Choose the game folder or its AMD Frame Gen DLL.')
    found = set()
    for index, (directory, subdirs, files) in enumerate(os.walk(path)):
        folder = Path(directory)
        if index >= 512:
            raise ValueError('Choose the AMD Frame Gen DLL directly.')
        if len(folder.relative_to(path).parts) >= 5:
            subdirs.clear()
        else:
            subdirs[:] = [sub for sub in subdirs if not sub.startswith('.')]
        if DLL in files or BACKUP in files:
            found.add(folder)
    if len(found) == 1:
        return found.pop()
    if found:
        raise ValueError('Multiple AMD Frame Gen DLLs found. Choose the one used by the game.')
    raise ValueError('Compatible AMD DX12 Frame Gen DLL not found. Choose the DLL directly.')


def launch_ids(appid):
    number = int(appid)
    if number < 2**31:
        return (appid,)
    return (appid, str(number - 2**32), str((number << 32) | 0x02000000))


def game_running(folder, appid, proc=Path('/proc')):
    names = {item.name.lower().encode() for item in folder.iterdir() if item.suffix.lower() == '.exe'}
    ids = {key.encode() for key in launch_ids(appid)}
    for process in proc.iterdir():
        try:
            if not process.name.isdecimal() or process.stat().st_uid != os.geteuid():
                continue
            with (process / 'comm').open('rb') as file:
                name = file.read(32).strip().lower()
            if any(name == filename[:15] for filename in names):
                return True
            with (process / 'environ').open('rb') as file:
                for entry in file.read(131072).split(b'\0'):
                    key, _, value = entry.partition(b'=')
                    if key in (b'SteamAppId', b'SteamGameId', b'STEAM_COMPAT_APP_ID') and value in ids:
                        return True
        except OSError:
            continue
    return False


def dll_digest(path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(info.st_mode) or not 2 <= info.st_size <= 128 * 1024 * 1024:
        raise ValueError('The game DLL or backup is not a supported regular file.')
    with path.open('rb') as file:
        if file.read(2) != b'MZ':
            raise ValueError('The game DLL or backup is not a Windows DLL.')
        file.seek(0)
        return hashlib.file_digest(file, 'sha256').hexdigest()


def verify_fsr_exports(path):
    """Admit x64 DX12 DLLs exposing the API wrapped by the adapter."""
    data = path.read_bytes()
    try:
        def unpack(fmt, offset):
            return struct.unpack_from('<' + fmt, data, offset)

        pe, = unpack('I', 60)
        if data[pe:pe + 4] != b'PE\0\0':
            raise ValueError
        machine, sections = unpack('HH', pe + 4)
        optional_size, characteristics = unpack('HH', pe + 20)
        optional = pe + 24
        if (machine != 0x8664 or not characteristics & 0x2000 or not 1 <= sections <= 96
                or optional_size < 120 or unpack('H', optional)[0] != 0x20b):
            raise ValueError
        mappings = [unpack('IIII', optional + optional_size + 40 * i + 8) for i in range(sections)]

        def locate(rva, size):
            for _, address, raw_size, raw in mappings:
                delta = rva - address
                if 0 <= delta and delta + size <= raw_size and raw + delta + size <= len(data):
                    return raw + delta
            raise ValueError

        export_rva, export_size = unpack('II', optional + 112)
        if not export_rva or export_size < 40:
            raise ValueError
        count, = unpack('I', locate(export_rva, 40) + 24)
        if not len(REQUIRED_EXPORTS) <= count <= 4096:
            raise ValueError
        names_rva, = unpack('I', locate(export_rva, 40) + 32)
        names = unpack(f'{count}I', locate(names_rva, count * 4))
        found = set()
        for rva in names:
            offset = locate(rva, 1)
            end = data.find(b'\0', offset, offset + 80)
            if end >= 0:
                found.add(data[offset:end])
        if not REQUIRED_EXPORTS <= found:
            raise ValueError
    except (struct.error, ValueError) as error:
        raise ValueError('The DLL does not expose the supported AMD DX12 Frame Generation API.') from error


def stage_dll(source, destination):
    fd, name = tempfile.mkstemp(prefix='.claw-fsr-', dir=destination.parent)
    pending = Path(name)
    try:
        with os.fdopen(fd, 'wb') as file:
            with source.open('rb') as dll:
                shutil.copyfileobj(dll, file)
            os.fchmod(file.fileno(), stat.S_IMODE(source.stat().st_mode) & 0o777)
        return pending
    except BaseException:
        pending.unlink(missing_ok=True)
        raise


def game_bridge(folder, adapter, action, appid):
    target, backup = folder / DLL, folder / BACKUP
    with directory_lock(folder):
        if action != 'status' and game_running(folder, appid):
            raise ValueError('Close the game before changing its Frame Gen adapter.')
        adapter_hash = dll_digest(adapter)
        if adapter_hash is None:
            raise ValueError('The Frame Gen adapter is missing from this installation.')
        proxies = PREVIOUS_PROXIES | {adapter_hash}
        active_hash, backup_hash = dll_digest(target), dll_digest(backup)
        active_proxy = active_hash in proxies
        if active_proxy and (not backup_hash or backup_hash in proxies):
            raise ValueError('The original AMD DLL is missing. Repair or reinstall the game files.')
        if action in ('status', 'enable'):
            original = backup if active_proxy or not active_hash else target
            if (active_hash and not active_proxy) or (backup_hash and backup_hash not in proxies):
                verify_fsr_exports(original)
        if action == 'enable' and active_hash != adapter_hash:
            if not active_hash and (not backup_hash or backup_hash in proxies):
                raise ValueError('The AMD Frame Gen DLL is missing. Repair or reinstall the game files.')
            pending = stage_dll(adapter, target)
            try:
                if active_hash and not active_proxy:
                    # Advance the backup to the Steam-installed DLL, atomically.
                    # If the adapter rename fails, Steam's DLL is still live.
                    preserved = stage_dll(target, backup)
                    try:
                        os.replace(preserved, backup)
                    finally:
                        preserved.unlink(missing_ok=True)
                os.replace(pending, target)
            finally:
                pending.unlink(missing_ok=True)
            return 'enabled'
        if not active_hash and not backup_hash:
            raise ValueError('The AMD Frame Gen DLL was not found in this folder.')
        if action == 'disable':
            if active_proxy or (not active_hash and backup_hash and backup_hash not in proxies):
                os.replace(backup, target)
            return 'ready'
        if active_proxy:
            return 'enabled'
        return 'update' if backup_hash else 'ready'


@contextmanager
def directory_lock(folder):
    fd = os.open(folder, os.O_DIRECTORY | os.O_RDONLY | os.O_NOFOLLOW)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('list', 'status', 'enable', 'disable'))
    parser.add_argument('home', type=Path)
    parser.add_argument('adapter', type=Path)
    parser.add_argument('--appid')
    parser.add_argument('--path', type=Path)
    args = parser.parse_args()
    try:
        games = discover_games(args.home) if args.action == 'list' or args.path is None else []
        if args.action == 'list':
            result = {'games': [
                {'appid': game.appid, 'name': game.name, 'source': game.source}
                for game in games
            ], 'home': str(args.home)}
        else:
            if not game_id(args.appid):
                raise ValueError('Choose a Steam or Non-Steam game.')
            if args.path is None:
                locations = {game.path for game in games if game.appid == args.appid}
                if len(locations) != 1 or None in locations:
                    raise ValueError('Select the actual AMD Frame Gen DLL for this game.')
                path = locations.pop()
            else:
                path = args.path
            if not path.is_absolute():
                raise ValueError('Select the game folder or its AMD Frame Gen DLL.')
            folder = find_dll_folder(path, args.path is None, args.home)
            state = game_bridge(folder, args.adapter, args.action, args.appid)
            result = {'state': state, 'folder': str(folder), 'message': ''}
    except (OSError, ValueError, RuntimeError) as error:
        result = {'state': 'unavailable', 'message': str(error)[:240]}
    print(json.dumps(result))


if __name__ == '__main__':
    main()
