"""Decky activation for Clair Obscur's optional FidelityFX frame telemetry."""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import tempfile

APP_ID = '1903340'
DLL = 'amd_fidelityfx_framegeneration_dx12.dll'
BACKUP = 'amd_fidelityfx_framegeneration_dx12.claw-original.dll'
GAME_EXE = 'SandFall-Win64-Shipping.exe'
RC1_PROXY_SHA256 = 'b1d6ec2615f336c6074beb4ef71afa5f2c43c1d735eb0b9d02793ec9bf7f0570'
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


def find_game(home):
    steamapps = set()
    for root in (home / '.local/share/Steam', home / '.steam/steam', home / '.steam/root',
                 home / '.var/app/com.valvesoftware.Steam/.local/share/Steam'):
        apps = root / 'steamapps'
        if not apps.is_dir():
            continue
        steamapps.add(apps.resolve())
        try:
            libraries = read_keyvalues(apps / 'libraryfolders.vdf').get('libraryfolders', {})
            for key, record in libraries.items():
                if key.isdecimal():
                    path = record.get('path', '') if isinstance(record, dict) else record
                    if Path(path).is_absolute():
                        steamapps.add((Path(path) / 'steamapps').resolve())
        except (OSError, ValueError, AttributeError):
            continue

    matches = set()
    for apps in steamapps:
        try:
            app = read_keyvalues(apps / f'appmanifest_{APP_ID}.acf').get('appstate', {})
            name = app.get('installdir', '')
            if app.get('appid') != APP_ID or not name or Path(name).name != name or name in ('.', '..'):
                continue
            common = (apps / 'common').resolve(strict=True)
            game = (common / name).resolve(strict=True)
            if not game.is_relative_to(common):
                continue
            binaries = (game / 'Sandfall/Binaries/Win64').resolve(strict=True)
            if binaries.is_relative_to(game) and (binaries / GAME_EXE).is_file():
                matches.add(binaries)
        except (OSError, ValueError, AttributeError, TypeError):
            continue
    if len(matches) > 1:
        raise ValueError('Steam reports more than one Clair Obscur installation.')
    if not matches:
        raise ValueError('Steam installation of Clair Obscur not found. Check that its drive is mounted.')
    return matches.pop()


def game_running(proc=Path('/proc')):
    for process in proc.iterdir():
        try:
            if not process.name.isdecimal() or process.stat().st_uid != os.geteuid():
                continue
            with (process / 'comm').open('rb') as file:
                name = file.read(32).strip().lower()
            filename = GAME_EXE.lower().encode()
            if name == filename[:15]:
                return True
            with (process / 'cmdline').open('rb') as file:
                args = file.read(4096).lower().replace(b'\\', b'/').split(b'\0')
            if any(arg.rsplit(b'/', 1)[-1] == filename for arg in args):
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


def game_bridge(folder, adapter, action):
    target, backup = folder / DLL, folder / BACKUP
    with directory_lock(folder):
        if action != 'status' and game_running():
            raise ValueError('Close Clair Obscur before changing its Frame Gen adapter.')
        adapter_hash = dll_digest(adapter)
        if adapter_hash is None:
            raise ValueError('The Frame Gen adapter is missing from this installation.')
        proxies = {adapter_hash, RC1_PROXY_SHA256}
        active_hash, backup_hash = dll_digest(target), dll_digest(backup)
        active_proxy = active_hash in proxies
        if active_proxy and (not backup_hash or backup_hash in proxies):
            raise ValueError('The original AMD DLL is missing. Verify the game files in Steam.')
        if action == 'enable' and active_hash != adapter_hash:
            if not active_hash and (not backup_hash or backup_hash in proxies):
                raise ValueError('The AMD Frame Gen DLL is missing. Verify the game files in Steam.')
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
    parser.add_argument('action', choices=('status', 'enable', 'disable'))
    parser.add_argument('home', type=Path)
    parser.add_argument('adapter', type=Path)
    args = parser.parse_args()
    try:
        folder = find_game(args.home)
        state = game_bridge(folder, args.adapter, args.action)
        result = {'state': state, 'message': ''}
    except (OSError, ValueError) as error:
        result = {'state': 'unavailable', 'message': str(error)[:240]}
    print(json.dumps(result))


if __name__ == '__main__':
    main()
