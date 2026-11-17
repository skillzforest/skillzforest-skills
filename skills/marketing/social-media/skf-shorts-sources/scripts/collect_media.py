#!/usr/bin/env python3
"""Add files or folders to a short's source kit (stdlib only).

    collect_media.py <file|folder>... --short shorts/<slug> [--origin local|site|gdrive|sharepoint|onedrive|dropbox|url]
                     [--licence own|cc0|cc-by|royalty-free|unknown] [--group media] [--max-mb 300] [--dry-run]

Copies every image, video, audio, font and document into the short's folder
(assets/<group>/ for media, docs/ for documents), reads its size (width, height,
duration — videos and audio with ffprobe, or Remotion's own ffprobe when
SKF_REMOTION_PROJECT points to a Remotion project), skips duplicates (same content)
and records each file in kit.json > assets[]. Folders are walked recursively; hidden
files and system clutter are ignored. Creates kit.json when it does not exist.
Prints what was added, skipped and why.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path

KINDS = {
    "image": {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".avif"},
    "video": {".mp4", ".mov", ".m4v", ".webm", ".mkv"},
    "audio": {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"},
    "font": {".woff2", ".woff", ".ttf", ".otf"},
    "doc": {".pdf", ".docx", ".pptx", ".xlsx", ".odt", ".odp", ".md", ".txt", ".html", ".htm", ".csv", ".json", ".rtf"},
}
SKIP = {".DS_Store", "Thumbs.db", "desktop.ini"}


def kind_of(path: Path):
    ext = path.suffix.lower()
    return next((k for k, exts in KINDS.items() if ext in exts), None)


def image_size(path: Path):
    data = path.read_bytes()[:512_000]
    try:
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            return struct.unpack(">II", data[16:24])
        if data[:6] in (b"GIF87a", b"GIF89a"):
            return struct.unpack("<HH", data[6:10])
        if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
            chunk = data[12:16]
            if chunk == b"VP8X":
                w = int.from_bytes(data[24:27], "little") + 1
                h = int.from_bytes(data[27:30], "little") + 1
                return w, h
            if chunk == b"VP8L":
                b = data[21:25]
                w = 1 + (((b[1] & 0x3F) << 8) | b[0])
                h = 1 + (((b[3] & 0xF) << 10) | (b[2] << 2) | ((b[1] & 0xC0) >> 6))
                return w, h
            if chunk == b"VP8 ":
                w, h = struct.unpack("<HH", data[26:30])
                return w & 0x3FFF, h & 0x3FFF
        if data[:2] == b"\xff\xd8":
            i = 2
            while i < len(data) - 9:
                if data[i] != 0xFF:
                    i += 1
                    continue
                marker = data[i + 1]
                if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                    h, w = struct.unpack(">HH", data[i + 5:i + 9])
                    return w, h
                i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
        if path.suffix.lower() == ".svg":
            text = data.decode(errors="ignore")
            vb = re.search(r'viewBox="[\d.\-]+[ ,]+[\d.\-]+[ ,]+([\d.]+)[ ,]+([\d.]+)"', text)
            if vb:
                return round(float(vb.group(1))), round(float(vb.group(2)))
    except (struct.error, IndexError):
        pass
    return None, None


def ffprobe_cmd():
    if shutil.which("ffprobe"):
        return ["ffprobe"], None
    project = os.environ.get("SKF_REMOTION_PROJECT") or str(Path.home() / ".skf-shorts" / "remotion")
    if (Path(project) / "node_modules" / "@remotion" / "cli").is_dir():
        return ["npx", "--no-install", "remotion", "ffprobe"], project
    return None, None


def probe(path: Path):
    cmd, cwd = ffprobe_cmd()
    if not cmd:
        return {}
    done = subprocess.run(cmd + ["-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path.resolve())],
                          capture_output=True, text=True, cwd=cwd)
    try:
        info = json.loads(done.stdout)
    except json.JSONDecodeError:
        return {}
    out = {"duration": round(float(info.get("format", {}).get("duration", 0) or 0), 2) or None}
    for s in info.get("streams", []):
        if s.get("codec_type") == "video" and "width" not in out:
            out.update(width=s.get("width"), height=s.get("height"), codec=s.get("codec_name"))
            rot = (s.get("tags") or {}).get("rotate") or next((d.get("rotation") for d in s.get("side_data_list", []) if "rotation" in d), None)
            if rot and abs(int(float(rot))) in (90, 270):
                out["width"], out["height"] = out["height"], out["width"]
        if s.get("codec_type") == "audio":
            out["hasAudio"] = True
    return out


def sha1(path: Path):
    h = hashlib.sha1()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_name(name: str):
    stem, ext = os.path.splitext(name)
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", stem).strip("-")[:60] or "file"
    return stem + ext.lower()


def load_kit(short: Path):
    path = short / "kit.json"
    if path.is_file():
        return path, json.loads(path.read_text())
    return path, {"version": 1, "slug": short.name, "createdAt": dt.date.today().isoformat(), "status": "draft",
                  "platforms": [], "idea": {}, "product": {}, "brand": {}, "facts": [], "assets": []}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--short", required=True)
    ap.add_argument("--origin", default="local")
    ap.add_argument("--licence", default="unknown")
    ap.add_argument("--group", default="media")
    ap.add_argument("--max-mb", type=float, default=300)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    short = Path(args.short)
    kit_path, kit = load_kit(short)
    assets = kit.setdefault("assets", [])
    known = {a.get("sha1"): a for a in assets if a.get("sha1")}
    next_id = 1 + max([int(a["id"][1:]) for a in assets if re.fullmatch(r"a\d+", a.get("id", ""))] or [0])

    files = []
    for raw in args.paths:
        p = Path(raw).expanduser()
        if p.is_dir():
            files += [f for f in sorted(p.rglob("*")) if f.is_file()
                      and not any(part.startswith(".") for part in f.relative_to(p).parts) and f.name not in SKIP]
        elif p.is_file():
            files.append(p)
        else:
            print(f"introuvable : {p}", file=sys.stderr)

    added, skipped = [], []
    for f in files:
        kind = kind_of(f)
        if not kind:
            skipped.append((str(f), "type non géré"))
            continue
        size = f.stat().st_size
        if size > args.max_mb * 1_000_000:
            skipped.append((str(f), f"{size / 1e6:.0f} Mo > --max-mb {args.max_mb:.0f}"))
            continue
        digest = sha1(f)
        if digest in known:
            skipped.append((str(f), f"déjà présent ({known[digest]['id']})"))
            continue
        inside = short.resolve() in f.resolve().parents
        if inside:  # already in the short's folder (site captures, downloads): record it where it is
            target = f.resolve()
            folder = target.parent
        else:
            folder = short / ("docs" if kind == "doc" else "assets/fonts" if kind == "font" else f"assets/{args.group}")
            target = folder / safe_name(f.name)
            n = 2
            while target.exists() and sha1(target) != digest:
                target = folder / f"{Path(safe_name(f.name)).stem}-{n}{f.suffix.lower()}"
                n += 1
        rel = target.relative_to(short.resolve()) if inside else target.relative_to(short)
        entry = {"id": f"a{next_id}", "kind": kind, "file": str(rel), "origin": args.origin,
                 "source": str(f), "bytes": size, "sha1": digest, "licence": args.licence}
        if kind == "image":
            w, h = image_size(f)
            entry.update(width=w, height=h)
        elif kind in ("video", "audio"):
            entry.update(probe(f))
            if kind == "video" and not entry.get("width"):
                entry["note"] = "taille et durée inconnues : ni ffprobe, ni projet Remotion (SKF_REMOTION_PROJECT)"
        if not args.dry_run:
            folder.mkdir(parents=True, exist_ok=True)
            if not inside and not target.exists():
                shutil.copy2(f, target)
        assets.append(entry)
        known[digest] = entry
        next_id += 1
        added.append(entry)

    if not args.dry_run:
        short.mkdir(parents=True, exist_ok=True)
        kit_path.write_text(json.dumps(kit, ensure_ascii=False, indent=2) + "\n")
    for e in added:
        dims = f"{e.get('width')}×{e.get('height')}" if e.get("width") else ""
        dur = f"{e['duration']} s" if e.get("duration") else ""
        print(f"+ {e['id']:<5} {e['kind']:<6} {e['file']}  {dims} {dur}".rstrip())
    for path, why in skipped:
        print(f"- {path} : {why}")
    print(f"{len(added)} ajouté(s), {len(skipped)} ignoré(s){' (simulation)' if args.dry_run else ''} → {kit_path}")


if __name__ == "__main__":
    sys.exit(main())
