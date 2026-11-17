#!/usr/bin/env python3
"""Render a short (vertical video, feed variants, covers) with Remotion, then check it.

    render_short.py shorts/<slug> [--formats 9x16,4x5] [--covers 9x16,4x5,1x1,16x9]
                    [--only video|covers|sheet] [--draft] [--project <dir>] [--scaffold]
    render_short.py shorts/<slug> --probe-assets      # durations and sizes of kit videos and sounds

Reads <short>/storyboard.json (props of the templates, paths relative to <short>/assets/)
and <short>/kit.json (platforms). The templates (templates/remotion/) are copied into
<project>/src/skf-shorts-studio/ and bundled with --public-dir <short>/assets: the
project's own Root is never touched. Project: --project, else $SKF_REMOTION_PROJECT,
else ~/.skf-shorts/remotion (--scaffold creates it: npm install, needs the network).

Writes into <short>/out/: short-<format>.mp4, cover-<format>.jpg / thumb-16x9.jpg,
sheet.jpg (frame 0 then the middle of every scene, side by side) and render.json
(files, measures, per-platform checks against references/formats.json).
--draft renders the videos at half size, for a quick look.
"""
import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
TEMPLATES = HERE / "templates" / "remotion"
FORMATS = json.loads((HERE / "references" / "formats.json").read_text())
DEPS = ["remotion@4.0.532", "@remotion/cli@4.0.532", "react@19.2.0", "react-dom@19.2.0", "zod@4.5.4"]  # zod: the exact version this Remotion expects
PROPS_KEYS = ("language", "brand", "scenes", "music", "voice", "sounds", "progressBar", "cover")
SIZES = {"9x16": (1080, 1920), "4x5": (1080, 1350), "1x1": (1080, 1080), "16x9": (1280, 720)}
FPS = 30


def run(cmd, cwd, quiet=True):
    done = subprocess.run(cmd, cwd=cwd, capture_output=quiet, text=True)
    if done.returncode != 0:
        tail = ((done.stderr or "") + (done.stdout or "")).strip().splitlines()[-25:]
        raise SystemExit(f"échec : {' '.join(cmd[:5])}…\n" + "\n".join(tail))
    return done.stdout or ""


def project_dir(args):
    candidate = args.project or os.environ.get("SKF_REMOTION_PROJECT") or str(Path.home() / ".skf-shorts" / "remotion")
    path = Path(candidate).expanduser().resolve()
    if (path / "node_modules" / "@remotion" / "cli").is_dir():
        return path
    if args.project and not args.scaffold:
        raise SystemExit(f"pas un projet Remotion installé : {path}")
    if not args.scaffold:
        raise SystemExit(f"aucun projet Remotion dans {path} — relancer avec --scaffold (npm install, réseau requis) "
                         "ou --project <projet Remotion existant>")
    path.mkdir(parents=True, exist_ok=True)
    if not (path / "package.json").exists():
        (path / "package.json").write_text(json.dumps({"name": "skf-shorts-remotion", "private": True}, indent=2))
    print(f"installation de Remotion dans {path}…", file=sys.stderr)
    run(["npm", "install", "--no-audit", "--no-fund", *DEPS], path)
    return path


def remotion(project, *args):
    return run(["npx", "--no-install", "remotion", *args], project)


def probe(project, file):
    out = remotion(project, "ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(file))
    info = json.loads(out[out.index("{"):])
    res = {"bytes": file.stat().st_size, "duration": round(float(info["format"].get("duration", 0) or 0), 2)}
    for s in info.get("streams", []):
        if s.get("codec_type") == "video" and "width" not in res:
            res.update(width=s["width"], height=s["height"], codec=s.get("codec_name"),
                       fps=round(_fps(s.get("r_frame_rate")), 2))
        elif s.get("codec_type") == "audio":
            res["audio"] = s.get("codec_name")
    return res


def _fps(rate):
    try:
        num, den = (rate or "0/1").split("/")
        return float(num) / float(den or 1)
    except (ValueError, ZeroDivisionError):
        return 0.0


def contact_sheet(shots, target):
    """Side-by-side strip of the frames (Remotion's ffmpeg has no stacking filter): Pillow
    when installed, otherwise None — the frames stay readable one by one."""
    try:
        from PIL import Image  # noqa: PLC0415 — optional
    except ImportError:
        return None
    images = [Image.open(s).convert("RGB") for s in shots]
    gap = 8
    sheet = Image.new("RGB", (sum(i.width for i in images) + gap * (len(images) - 1), max(i.height for i in images)), "white")
    x = 0
    for img in images:
        sheet.paste(img, (x, 0))
        x += img.width + gap
    sheet.save(target, quality=85)
    return target


def files_in(props):
    found = []
    def walk(node, where):
        if isinstance(node, dict):
            for k, v in node.items():
                if k in ("file", "logo") and isinstance(v, str):
                    found.append((f"{where}.{k}", v))
                else:
                    walk(v, f"{where}.{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{where}[{i}]")
    walk(props, "storyboard")
    return found


def probe_assets(short, project):
    kit_path = short / "kit.json"
    kit = json.loads(kit_path.read_text())
    for a in kit.get("assets", []):
        if a.get("kind") in ("video", "audio") and (not a.get("duration") or (a["kind"] == "video" and not a.get("width"))):
            info = probe(project, (short / a["file"]).resolve())
            a.update({k: v for k, v in info.items() if k in ("duration", "width", "height", "codec")})
            if info.get("audio"):
                a["hasAudio"] = True
            a.pop("note", None)
            print(f"{a['id']:<5} {a['file']}  {a.get('width', '')}×{a.get('height', '')} {a.get('duration')} s")
    kit_path.write_text(json.dumps(kit, ensure_ascii=False, indent=2) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("short")
    ap.add_argument("--formats")
    ap.add_argument("--covers")
    ap.add_argument("--only", choices=["video", "covers", "sheet"])
    ap.add_argument("--draft", action="store_true")
    ap.add_argument("--project")
    ap.add_argument("--scaffold", action="store_true")
    ap.add_argument("--probe-assets", action="store_true")
    args = ap.parse_args()

    short = Path(args.short).resolve()
    project = project_dir(args)
    if args.probe_assets:
        probe_assets(short, project)
        return

    story = json.loads((short / "storyboard.json").read_text())
    kit = json.loads((short / "kit.json").read_text()) if (short / "kit.json").is_file() else {}
    platforms = story.get("platforms") or kit.get("platforms") or ["youtube", "tiktok", "instagram"]
    assets = short / "assets"
    missing = [f"{where} → assets/{rel}" for where, rel in files_in({k: story.get(k) for k in PROPS_KEYS})
               if not re.match(r"(https?|data):", rel) and not (assets / rel).is_file()]
    if missing:
        raise SystemExit("fichiers absents (chemins relatifs à assets/) :\n  " + "\n  ".join(missing))

    formats = (args.formats.split(",") if args.formats else story.get("formats")) or ["9x16"]
    if "9x16" not in formats:
        formats.insert(0, "9x16")
    covers = args.covers.split(",") if args.covers else story.get("covers")
    if not covers:
        wanted = {"cover-9x16.jpg"}
        for p in platforms:
            wanted.update(FORMATS["platforms"].get(p, {}).get("coverFiles", []))
        covers = [re.search(r"(\d+x\d+)", w).group(1) for w in sorted(wanted)]

    out = short / "out"
    out.mkdir(exist_ok=True)
    props_file = out / ".props.json"
    props_file.write_text(json.dumps({k: story[k] for k in PROPS_KEYS if k in story}, ensure_ascii=False))

    install = project / "src" / "skf-shorts-studio"
    install.mkdir(parents=True, exist_ok=True)
    for template in TEMPLATES.iterdir():
        shutil.copy(template, install / template.name)
    bundle = project / ".skf-shorts-bundle" / short.name
    print("bundle…", file=sys.stderr)
    remotion(project, "bundle", str(install / "index.tsx"), f"--out-dir={bundle}", f"--public-dir={assets}")

    report_path = out / "render.json"
    report = json.loads(report_path.read_text()) if report_path.is_file() else {}
    report.update({"slug": short.name, "renderedAt": dt.datetime.now().isoformat(timespec="seconds"),
                   "project": str(project), "draft": args.draft})
    total = sum(max(1, round(s["duration"] * FPS)) for s in story["scenes"]) / FPS
    report["durationSeconds"] = round(total, 2)

    if args.only in (None, "video"):
        report["videos"] = {}
        for stale in out.glob("short-*.mp4"):  # a format not rendered this time must not be published
            if stale.stem.split("-", 1)[1] not in formats:
                stale.unlink()
        for f in formats:
            target = out / f"short-{f}.mp4"
            print(f"vidéo {f}…", file=sys.stderr)
            cmd = ["render", str(bundle), f"Short{f}", str(target), f"--props={props_file}", "--codec=h264",
                   "--crf=20", "--audio-codec=aac", "--pixel-format=yuv420p"]
            if args.draft:
                cmd.append("--scale=0.5")
            remotion(project, *cmd)
            report["videos"][f] = {"file": str(target.relative_to(short)), **probe(project, target)}

    if args.only in (None, "covers"):
        report["covers"] = {}
        for f in covers:
            comp = "Thumb16x9" if f == "16x9" else f"Cover{f}"
            target = out / (f"thumb-{f}.jpg" if f == "16x9" else f"cover-{f}.jpg")
            remotion(project, "still", str(bundle), comp, str(target), f"--props={props_file}",
                     "--image-format=jpeg", "--jpeg-quality=90")
            w, h = SIZES[f]
            report["covers"][f] = {"file": str(target.relative_to(short)), "width": w, "height": h, "bytes": target.stat().st_size}

    master = out / "short-9x16.mp4"
    if args.only in (None, "video", "sheet") and master.is_file():
        frames_dir = out / "frames"
        shutil.rmtree(frames_dir, ignore_errors=True)
        frames_dir.mkdir()
        stamps, t = [0.05], 0.0
        for s in story["scenes"]:
            stamps.append(t + s["duration"] * 0.6)
            t += s["duration"]
        shots = []
        for i, ts in enumerate(stamps):
            shot = frames_dir / f"{i:02d}.jpg"
            remotion(project, "ffmpeg", "-y", "-v", "error", "-ss", f"{ts:.2f}", "-i", str(master),
                     "-frames:v", "1", "-vf", "scale=270:-2", str(shot))
            shots.append(shot)
        report["frames"] = [str(x.relative_to(short)) for x in shots]
        sheet = contact_sheet(shots, out / "sheet.jpg")
        report["sheet"] = str(sheet.relative_to(short)) if sheet else None
        report["sheetLegend"] = ["image 0 (vignette automatique)"] + [f"scène {i + 1} : {s['type']}" for i, s in enumerate(story["scenes"])]

    for existing in sorted(out.glob("short-*.mp4")):  # videos of an earlier run (--only covers / sheet)
        fmt = existing.stem.split("-", 1)[1]
        if fmt not in report.setdefault("videos", {}):
            report["videos"][fmt] = {"file": str(existing.relative_to(short)), **probe(project, existing)}

    checks = {}
    master_fmt = FORMATS["master"]
    for p in platforms:
        spec = FORMATS["platforms"].get(p)
        if not spec:
            checks[p] = {"ok": False, "issues": ["plateforme inconnue de formats.json"]}
            continue
        video = report.get("videos", {}).get(spec["video"]) or report.get("videos", {}).get(spec.get("altVideo", "")) \
            or report.get("videos", {}).get("9x16")
        issues = []
        if not video:
            issues.append("aucune vidéo rendue")
        else:
            if video["duration"] > spec["maxSeconds"]:
                issues.append(f"{video['duration']} s > {spec['maxSeconds']} s")
            if video["bytes"] > spec["maxBytes"]:
                issues.append(f"{video['bytes'] / 1e6:.0f} Mo > {spec['maxBytes'] / 1e6:.0f} Mo")
            if video.get("codec") != "h264" or video.get("audio") not in (None, "aac"):
                issues.append(f"codec {video.get('codec')}/{video.get('audio')} au lieu de h264/aac")
            if args.draft:
                issues.append("rendu brouillon (--draft) : relancer sans --draft avant publication")
        missing_covers = [c for c in spec.get("coverFiles", []) if not (out / c).is_file()]
        if missing_covers:
            issues.append("cover manquante : " + ", ".join(missing_covers))
        checks[p] = {"ok": not issues, "video": video and video["file"], "covers": spec.get("coverFiles", []), "issues": issues}
    lo, hi = master_fmt["recommendedSeconds"]
    advice = []
    if total > master_fmt["hardMaxSeconds"]:
        advice.append(f"{total:.0f} s : au-delà de {master_fmt['hardMaxSeconds']} s, un short perd l'essentiel de son public")
    elif not lo <= total <= hi:
        advice.append(f"{total:.0f} s : la zone qui retient le mieux est {lo}–{hi} s")
    report["checks"] = checks
    report["advice"] = advice
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    props_file.unlink(missing_ok=True)
    print(json.dumps({k: report.get(k) for k in ("durationSeconds", "videos", "covers", "sheet", "checks", "advice")},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    sys.exit(main())
