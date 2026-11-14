#!/usr/bin/env python3
"""Install or remove Better Overlay's opt-in DX12 telemetry adapter."""
import argparse
import os
from pathlib import Path
import shutil
import tempfile

NAME = 'amd_fidelityfx_framegeneration_dx12.dll'
BACKUP = 'amd_fidelityfx_framegeneration_dx12.claw-original.dll'


def replace_file(source, destination):
    with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as file:
        temporary = Path(file.name)
    try:
        shutil.copy2(source, temporary)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def matches(first, second):
    return (first.is_file() and second.is_file() and
            first.stat().st_size == second.stat().st_size and first.read_bytes() == second.read_bytes())


def manage(action, folder, adapter):
    original = folder / NAME
    backup = folder / BACKUP
    if original.is_symlink() or backup.is_symlink():
        raise ValueError('Select the game folder containing the original regular AMD DLL.')
    if action == 'remove':
        if not backup.is_file():
            raise ValueError('No Better Overlay backup found.')
        if original.exists() and not matches(original, adapter):
            raise ValueError('The game DLL changed since installation. The original backup is still available.')
        os.replace(backup, original)
        return
    if not adapter.is_file() or not original.is_file():
        raise ValueError(f'Expected a bundled adapter and {NAME} in the game folder.')
    if backup.exists():
        if matches(original, adapter):
            return
        raise ValueError('A previous backup already exists. Resolve the game DLL change before reinstalling.')
    if matches(original, adapter):
        raise ValueError('The original game DLL is missing.')
    # Link the original first so a failure or interruption leaves a usable DLL.
    os.link(original, backup)
    try:
        replace_file(adapter, original)
    except BaseException:
        if not matches(original, adapter):
            backup.unlink()
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['install', 'remove'])
    parser.add_argument('folder', type=Path, help='Folder containing the game’s AMD frame generation DLL')
    args = parser.parse_args()
    try:
        manage(args.action, args.folder.resolve(strict=True), Path(__file__).resolve().with_name(NAME))
    except (OSError, ValueError) as error:
        parser.exit(1, f'{error}\n')
    print('Frame Gen adapter installed.' if args.action == 'install' else 'Original AMD DLL restored.')


if __name__ == '__main__':
    main()
