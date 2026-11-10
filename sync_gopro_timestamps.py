#!/usr/bin/env python3
"""Copy filesystem creation and modification times from GoPro .360 files to reframed MP4s.

An MP4 matches a .360 clip when its name is <stem>.mp4 or <stem>_<anything>.mp4
(e.g. GS010018_reframed.mp4, GS010018_reframed_nohl.mp4). Use --suffix to restrict
matching to one naming pattern, e.g. --suffix _reframed_nohl.mp4.

Usage:
  py sync_gopro_timestamps.py "D:\\Videos\\Galtur2026\\MAX2\\Galtur" "D:\\Videos\\Galtur2026\\MAX2\\Galtur\\rf"
  py sync_gopro_timestamps.py "D:\\Videos\\Galtur2026\\MAX2\\Galtur" "D:\\Videos\\Galtur2026\\MAX2\\Galtur\\rf" --apply

Without --apply, displays the proposed changes without modifying files.
Requires: py -m pip install pywin32
"""
import argparse
from pathlib import Path
import sys

import win32con
import win32file

FILE_WRITE_ATTRIBUTES = 0x0100

def copy_windows_timestamps(source: Path, destination: Path) -> None:
    """Copy Windows creation and last-modified timestamps, leave last-access unchanged."""
    if destination.suffix.casefold() != '.mp4':
        raise ValueError(f'Refusing to modify non-MP4 file: {destination}')
    source_handle = win32file.CreateFile(
        str(source), win32con.GENERIC_READ,
        win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
        None, win32con.OPEN_EXISTING, win32con.FILE_ATTRIBUTE_NORMAL, None,
    )
    try:
        created, _accessed, modified = win32file.GetFileTime(source_handle)
    finally:
        win32file.CloseHandle(source_handle)

    dest_handle = win32file.CreateFile(
        str(destination), FILE_WRITE_ATTRIBUTES,
        win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
        None, win32con.OPEN_EXISTING, win32con.FILE_ATTRIBUTE_NORMAL, None,
    )
    try:
        win32file.SetFileTime(dest_handle, created, None, modified)
    finally:
        win32file.CloseHandle(dest_handle)


def find_original_base(mp4_name: str, source_bases: set, suffix: str | None) -> str | None:
    """Return the casefolded .360 stem that mp4_name was exported from, or None.

    With suffix, the name must end with it and the remainder is the stem. Without it,
    the longest prefix of the MP4 stem that equals a .360 stem and is followed by '_'
    (or is the whole stem) wins.
    """
    name = mp4_name.casefold()
    if suffix is not None:
        suffix = suffix.casefold()
        if not name.endswith(suffix):
            return None
        base = name[:-len(suffix)]
        return base if base in source_bases else None
    stem = name[:-len('.mp4')]
    best = None
    for base in source_bases:
        if stem == base or stem.startswith(base + '_'):
            if best is None or len(base) > len(best):
                best = base
    return best


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('source_dir', type=Path, help='Directory containing original .360 clips')
    parser.add_argument('output_dir', type=Path, help='Directory containing exported MP4 files')
    parser.add_argument('--suffix', help='Only match MP4s named <stem><suffix>, e.g. _reframed_nohl.mp4 '
                        '(default: any <stem>.mp4 or <stem>_*.mp4)')
    parser.add_argument('--apply', action='store_true', help='Actually update MP4 timestamps (default: dry run)')
    args = parser.parse_args()

    if not args.source_dir.is_dir() or not args.output_dir.is_dir():
        parser.error('Both source_dir and output_dir must be existing directories')

    if args.suffix is not None and not args.suffix.casefold().endswith('.mp4'):
        args.suffix += '.mp4'

    sources = {p.stem.casefold(): p for p in args.source_dir.iterdir() if p.is_file() and p.suffix.casefold() == '.360'}
    if not sources:
        parser.error(f'No .360 files found in source_dir {args.source_dir} '
                     '(arguments are: source_dir with .360 clips first, then output_dir with MP4s)')
    if args.source_dir.resolve() == args.output_dir.resolve():
        print('Note: source_dir and output_dir are the same directory; only .mp4 files will be modified.')
    matched = missing = changed = errors = 0
    for mp4 in sorted(args.output_dir.iterdir(), key=lambda p: p.name.casefold()):
        name = mp4.name.casefold()
        if not mp4.is_file() or not name.endswith('.mp4') or name.endswith('.partial.mp4'):
            continue
        if args.suffix is not None and not name.endswith(args.suffix.casefold()):
            continue
        base = find_original_base(mp4.name, sources.keys(), args.suffix)
        if base is None:
            print(f'MISSING original: {mp4.name}')
            missing += 1
            continue
        original = sources[base]
        matched += 1
        if not args.apply:
            print(f'WOULD UPDATE: {mp4.name}  <-  {original.name}')
            continue
        try:
            copy_windows_timestamps(original, mp4)
            print(f'UPDATED: {mp4.name}  <-  {original.name}')
            changed += 1
        except (OSError, ValueError) as exc:
            print(f'ERROR updating {mp4.name}: {exc}', file=sys.stderr)
            errors += 1

    print(f'\nMatched: {matched}; missing originals: {missing}; updated: {changed}; errors: {errors}; mode: {"APPLY" if args.apply else "DRY RUN"}')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
