#!/usr/bin/env python3
"""Render a product page's images and video with Remotion, as the profile's media
slots ask (`media.<slot>.render`).

    render_media.py --profile <name|path> --props <props.json> --out <dir>
                    [--slots cover,cover_mobile,hero_video,hero_poster,outcome_1]
                    [--project <remotion project>] [--scaffold]

props.json: {"product": {…ProductProps without brand…}, "outcomes": [{"title": "…"}, …]}
The brand comes from `profile.remotion.brand` unless props.product.brand is given.

The templates (templates/remotion/) are copied into <project>/<install_dir> and rendered
through their own entry point: the project's Root is never touched. No project:
--scaffold creates a minimal one in <out>/remotion (npm install, needs the network).
Prints {"slot": "file", …} as JSON.
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from cms_profile import load_profile

TEMPLATES = Path(__file__).resolve().parent.parent / "templates" / "remotion"
SCAFFOLD_DEPS = ["remotion@^4", "@remotion/cli@^4", "react@^19", "react-dom@^19", "zod@^4"]


def run(cmd: list[str], cwd: Path) -> None:
    done = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if done.returncode != 0:
        tail = (done.stderr or done.stdout).strip().splitlines()[-15:]
        raise SystemExit(f"{' '.join(cmd[:4])}… failed:\n" + "\n".join(tail))


def project_dir(profile: dict, args) -> Path:
    candidate = args.project or profile.get("remotion", {}).get("project")
    if candidate:
        path = Path(candidate).expanduser()
        if (path / "node_modules" / "remotion").is_dir():
            return path
        if args.project:
            raise SystemExit(f"not a Remotion project with installed dependencies: {path}")
    scaffold = Path(args.out).expanduser().resolve() / "remotion"
    if (scaffold / "node_modules" / "remotion").is_dir():
        return scaffold
    if not args.scaffold:
        raise SystemExit(
            "no Remotion project found — pass --project <dir>, or --scaffold to create a minimal one "
            f"in {scaffold} (runs npm install)"
        )
    scaffold.mkdir(parents=True, exist_ok=True)
    (scaffold / "package.json").write_text(json.dumps({"name": "content-import-media", "private": True}, indent=2))
    run(["npm", "install", "--no-audit", "--no-fund", *SCAFFOLD_DEPS], scaffold)
    return scaffold


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--props", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--slots", help="comma-separated; default: every slot with a render spec")
    parser.add_argument("--project")
    parser.add_argument("--scaffold", action="store_true")
    args = parser.parse_args()

    profile = load_profile(args.profile)
    props = json.loads(Path(args.props).read_text())
    out = Path(args.out).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)

    slots = {k: v for k, v in profile.get("media", {}).items() if v.get("render")}
    for kind in profile.get("kinds", {}).values():
        slots.update({k: v for k, v in kind.get("media", {}).items() if v.get("render")})
    wanted = args.slots.split(",") if args.slots else list(slots)
    unknown = [s for s in wanted if s not in slots]
    if unknown:
        raise SystemExit(f"no render spec for: {', '.join(unknown)}")

    project = project_dir(profile, args)
    install = project / profile.get("remotion", {}).get("install_dir", "src/skf-content-import")
    install.mkdir(parents=True, exist_ok=True)
    for template in TEMPLATES.iterdir():
        shutil.copy(template, install / template.name)
    entry = install / "index.ts"

    product = {"brand": profile.get("remotion", {}).get("brand", {}), **props["product"]}
    outcomes = props.get("outcomes", [])
    result = {}
    for slot in wanted:
        spec = slots[slot]["render"]
        payload = {**product, "variant": "cover", "title": ""}
        if slot.startswith("outcome_"):
            index = int(slot.split("_")[1]) - 1
            if index >= len(outcomes):
                continue
            payload.update(variant="outcome", title=outcomes[index]["title"])
        elif spec["composition"] == "ProductPoster":
            payload["variant"] = "poster"
        if spec["composition"] == "ProductHero":
            payload = product
        props_file = out / f".props-{slot}.json"
        props_file.write_text(json.dumps(payload, ensure_ascii=False))

        if spec["composition"] == "ProductHero":
            target = out / f"{slot}.mp4"
            run(["npx", "remotion", "render", str(entry), "ProductHero", str(target),
                 f"--props={props_file}", f"--codec={spec.get('codec', 'h264')}", "--crf=23"], project)
        else:
            fmt = spec.get("format", "png")
            target = out / f"{slot}.{'jpg' if fmt == 'jpeg' else fmt}"
            max_bytes = slots[slot].get("target_bytes") or slots[slot].get("max_bytes")
            # JPEG: lower the quality until the file fits its weight budget.
            for quality in ([88, 80, 70, 60, 50] if fmt == "jpeg" else [None]):
                cmd = ["npx", "remotion", "still", str(entry), spec["composition"], str(target),
                       f"--props={props_file}", f"--image-format={fmt}", f"--scale={spec.get('scale', 1)}"]
                if quality:
                    cmd.append(f"--jpeg-quality={quality}")
                run(cmd, project)
                if not max_bytes or target.stat().st_size <= max_bytes:
                    break
        props_file.unlink(missing_ok=True)
        result[slot] = str(target)

    print(json.dumps({"project": str(project), "media": result}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    sys.exit(main())
