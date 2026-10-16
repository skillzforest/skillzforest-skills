#!/usr/bin/env python3
"""Zip every subdirectory of a directory, one archive per subdirectory.

    python3 zip_folders.py <directory> [--out <dir>] [--overwrite] [--include-all] [--dry-run]

Each immediate subdirectory `<directory>/<name>/` becomes `<out>/<name>.zip`
(`<out>` defaults to `<directory>` itself). The archive's root entry is the
folder `<name>/`, like the Finder's or Explorer's "Compress". Hidden
subdirectories (`.git`, `.venv`...) are not zipped. Inside each folder,
`.DS_Store`, `__MACOSX`, `.git`, `node_modules` and `__pycache__` are left
out unless `--include-all`. Symlinks are stored as the files they point to
when those files sit inside the folder, and skipped otherwise.

An existing `<name>.zip` is left untouched unless `--overwrite`; it is
reported in `existing`. Prints a JSON report on stdout; exit code 1 when
the directory is invalid or an archive failed.

Standard library only.
"""

import argparse
import json
import os
import sys
import zipfile
from pathlib import Path

if sys.version_info < (3, 8):
    sys.exit(f"Python 3.8 or newer is required (found {sys.version.split()[0]}).")

EXCLUDED_NAMES = {".DS_Store", "__MACOSX", ".git", "node_modules", "__pycache__", "Thumbs.db"}


def human(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size} B"


def files_to_zip(folder: Path, include_all: bool):
    """Yield (path on disk, name in the archive) for every file of `folder`."""
    root = folder.resolve()
    for dirpath, dirnames, filenames in os.walk(folder, followlinks=False):
        if not include_all:
            dirnames[:] = [d for d in dirnames if d not in EXCLUDED_NAMES]
        dirnames.sort()
        current = Path(dirpath)
        for name in sorted(filenames):
            if not include_all and name in EXCLUDED_NAMES:
                continue
            path = current / name
            if path.is_symlink():
                target = path.resolve()
                if not target.is_file() or root not in target.parents:
                    continue
            elif not path.is_file():
                continue
            yield path, Path(folder.name) / path.relative_to(folder)


def zip_folder(folder: Path, archive: Path, include_all: bool) -> dict:
    tmp = archive.with_name(archive.name + ".part")
    count = 0
    try:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            zf.write(folder, f"{folder.name}/")
            for path, arcname in files_to_zip(folder, include_all):
                zf.write(path, arcname.as_posix())
                count += 1
        with zipfile.ZipFile(tmp) as zf:
            bad = zf.testzip()
            if bad:
                raise zipfile.BadZipFile(f"corrupt entry: {bad}")
        tmp.replace(archive)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    return {"files": count, "bytes": archive.stat().st_size}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("directory")
    parser.add_argument("--out", help="where to write the archives (default: the directory itself)")
    parser.add_argument("--overwrite", action="store_true", help="replace existing <name>.zip")
    parser.add_argument("--include-all", action="store_true", help="keep .DS_Store, .git, node_modules...")
    parser.add_argument("--dry-run", action="store_true", help="list what would be zipped, write nothing")
    args = parser.parse_args()

    directory = Path(args.directory).expanduser()
    if not directory.is_dir():
        print(json.dumps({"ok": False, "error": f"not a directory: {directory}"}), file=sys.stdout)
        return 1
    directory = directory.resolve()
    out = Path(args.out).expanduser().resolve() if args.out else directory

    folders = sorted(
        (
            p
            for p in directory.iterdir()
            # the output folder, when it sits inside the directory, is never zipped itself
            if p.is_dir() and not p.is_symlink() and not p.name.startswith(".") and p.resolve() != out
        ),
        key=lambda p: p.name.lower(),
    )
    report = {
        "ok": True,
        "directory": str(directory),
        "out": str(out),
        "dry_run": args.dry_run,
        "folders": len(folders),
        "zipped": [],
        "existing": [],
        "empty": [],
        "errors": [],
    }

    if not args.dry_run:
        out.mkdir(parents=True, exist_ok=True)

    for folder in folders:
        archive = out / f"{folder.name}.zip"
        if archive.exists() and not args.overwrite:
            report["existing"].append(str(archive))
            continue
        if not any(True for _ in files_to_zip(folder, args.include_all)):
            report["empty"].append(folder.name)
        if args.dry_run:
            report["zipped"].append({"folder": folder.name, "archive": str(archive)})
            continue
        try:
            result = zip_folder(folder, archive, args.include_all)
            report["zipped"].append(
                {"folder": folder.name, "archive": str(archive), **result, "size": human(result["bytes"])}
            )
        except Exception as exc:  # report and keep going with the other folders
            report["errors"].append({"folder": folder.name, "error": str(exc)})

    report["ok"] = not report["errors"]
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
