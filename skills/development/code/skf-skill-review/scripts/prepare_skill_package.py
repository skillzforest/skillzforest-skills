#!/usr/bin/env python3
"""Turn a skill source — a local folder, a .zip, a lone SKILL.md, or a URL — into the
zip a reviewer expects: SKILL.md at the root, junk removed. Standard library only.

    prepare_skill_package.py <source> [--skill-path <dir-in-source>] [--out <dir>]

<source>:
  ./my-skill/                                   folder holding SKILL.md (or a repo with several)
  ./my-skill.zip | ./SKILL.md
  https://github.com/<owner>/<repo>             whole repo (default branch)
  https://github.com/<owner>/<repo>/tree/<ref>/<path>
  https://github.com/<owner>/<repo>/blob/<ref>/<path>/SKILL.md
  https://…/skill.zip | https://…/SKILL.md      direct download

Prints one JSON object on stdout:
  {"zip": …, "root": …, "name": …, "description": …, "files": [...], "hints": {...}}
Exit 3 with {"error": "several-skills", "candidates": [...]} when the source holds more
than one SKILL.md and --skill-path doesn't pick one.
"""

import argparse
import io
import json
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

MAX_ENTRIES = 2000
MAX_UNPACKED_BYTES = 200 * 1024 * 1024
MAX_DOWNLOAD_BYTES = 100 * 1024 * 1024
JUNK_DIRS = {"__MACOSX", ".git", ".svn", ".hg", "__pycache__", "node_modules", ".venv"}
JUNK_FILES = {".DS_Store", "Thumbs.db", "desktop.ini"}
# Files that often carry an example prompt for the functional test.
HINT_NAMES = re.compile(r"(readme|example|usage|prompt)[^/]*\.(md|txt|json)$", re.I)


def fail(message: str, code: int = 2, **extra) -> None:
    print(json.dumps({"error": message, **extra}, ensure_ascii=False))
    sys.exit(code)


def is_junk(parts: list[str]) -> bool:
    return (
        any(p in JUNK_DIRS for p in parts[:-1])
        or parts[-1] in JUNK_FILES
        or parts[-1].startswith("._")
    )


def download(url: str) -> tuple[bytes, str]:
    # curl first: it uses the system's certificates, which python.org's Python on macOS lacks.
    if shutil.which("curl"):
        with tempfile.TemporaryDirectory() as tmp:
            body, head = Path(tmp) / "body", Path(tmp) / "head"
            done = subprocess.run(
                ["curl", "-fsSL", "--max-time", "120", "--max-filesize", str(MAX_DOWNLOAD_BYTES),
                 "-A", "skf-skill-review", "-D", str(head), "-o", str(body), url],
                capture_output=True,
                text=True,
            )
            if done.returncode != 0:
                fail(f"download failed: {url} ({done.stderr.strip() or done.returncode})")
            types = re.findall(r"(?im)^content-type:\s*(.+?)\s*$", head.read_text(errors="replace"))
            return body.read_bytes(), types[-1] if types else ""
    request = urllib.request.Request(url, headers={"User-Agent": "skf-skill-review"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = response.read(MAX_DOWNLOAD_BYTES + 1)
            content_type = response.headers.get("Content-Type", "")
    except OSError as exc:
        fail(f"download failed: {url} ({exc})")
    if len(data) > MAX_DOWNLOAD_BYTES:
        fail(f"download larger than {MAX_DOWNLOAD_BYTES // (1024 * 1024)} MB: {url}")
    return data, content_type


def github_target(url: str) -> tuple[str, str | None, str] | None:
    """github.com URL → (owner/repo, ref or None, path inside the repo)."""
    parsed = urllib.parse.urlparse(url)
    if parsed.netloc not in ("github.com", "www.github.com"):
        return None
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) < 2:
        return None
    repo = f"{parts[0]}/{parts[1].removesuffix('.git')}"
    if len(parts) >= 4 and parts[2] in ("tree", "blob"):
        ref, inner = parts[3], parts[4:]
        if parts[2] == "blob" and inner:
            inner = inner[:-1]  # a file: review the folder it sits in
        return repo, ref, "/".join(inner)
    return repo, None, ""


def extract_zip(data: bytes, dest: Path) -> None:
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        fail("not a valid zip archive")
    with archive:
        infos = archive.infolist()
        if len(infos) > MAX_ENTRIES:
            fail(f"too many entries in the archive ({len(infos)})")
        if sum(i.file_size for i in infos) > MAX_UNPACKED_BYTES:
            fail("archive too large once unpacked")
        for info in infos:
            name = info.filename.replace("\\", "/")
            parts = [p for p in name.split("/") if p not in ("", ".")]
            if name.startswith("/") or ".." in parts or (parts and ":" in parts[0]):
                fail(f"unsafe path in the archive: {info.filename}")
            if stat.S_ISLNK(info.external_attr >> 16):
                fail(f"symbolic link in the archive: {info.filename}")
            if info.flag_bits & 0x1:
                fail("encrypted archive")
            if not parts or info.is_dir() or is_junk(parts):
                continue
            target = dest.joinpath(*parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(info))


def fetch(source: str, workdir: Path) -> tuple[Path, str]:
    """Materialise the source under workdir; returns (folder, sub-path to look in)."""
    tree = workdir / "src"
    tree.mkdir()
    if re.match(r"^https?://", source):
        gh = github_target(source)
        if gh:
            repo, ref, inner = gh
            api = f"https://api.github.com/repos/{repo}/zipball" + (f"/{ref}" if ref else "")
            data, _ = download(api)
            extract_zip(data, tree)
            # GitHub wraps everything in "<owner>-<repo>-<sha>/".
            tops = [p for p in tree.iterdir()]
            root = tops[0] if len(tops) == 1 and tops[0].is_dir() else tree
            return root, inner
        data, content_type = download(source)
        path = urllib.parse.urlparse(source).path
        if data[:4] == b"PK\x03\x04" or path.endswith(".zip"):
            extract_zip(data, tree)
        elif path.endswith(".md") or "markdown" in content_type or "text/plain" in content_type:
            (tree / "SKILL.md").write_bytes(data)
        else:
            fail(f"don't know what to do with {source} ({content_type or 'no content type'})")
        return tree, ""

    local = Path(source).expanduser().resolve()
    if not local.exists():
        fail(f"not found: {local}")
    if local.is_dir():
        return local, ""
    if local.suffix == ".zip":
        extract_zip(local.read_bytes(), tree)
        return tree, ""
    if local.suffix == ".md":
        shutil.copy(local, tree / "SKILL.md")
        return tree, ""
    fail(f"expected a folder, a .zip or a .md: {local}")
    raise AssertionError  # unreachable


def frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not match:
        return {}
    fields: dict[str, str] = {}
    key = None
    for line in match.group(1).splitlines():
        m = re.match(r"^([A-Za-z_-]+):\s*(.*)$", line)
        if m:
            key, value = m.group(1), m.group(2).strip()
            fields[key] = "" if value in (">-", ">", "|", "|-") else value.strip("'\"")
        elif key and line.startswith((" ", "\t")):
            fields[key] = (fields[key] + " " + line.strip()).strip()
    return fields


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("--skill-path", default="", help="folder of the skill inside the source")
    parser.add_argument("--out", default=None, help="where to write the zip (default: a temp dir)")
    args = parser.parse_args()

    workdir = Path(tempfile.mkdtemp(prefix="skf-skill-review-"))
    base, inner = fetch(args.source, workdir)
    search = base / (args.skill_path or inner)
    if not search.is_dir():
        fail(f"no such folder in the source: {args.skill_path or inner}")

    skills = sorted(
        p.parent
        for p in search.rglob("SKILL.md")
        if not is_junk(list(p.relative_to(search).parts))
    )
    if not skills:
        fail("no SKILL.md found in the source")
    if len(skills) > 1:
        fail(
            "several-skills",
            3,
            candidates=[str(s.relative_to(base)) for s in skills],
            hint="re-run with --skill-path <one of the candidates>",
        )
    root = skills[0]

    files = sorted(
        p for p in root.rglob("*") if p.is_file() and not is_junk(list(p.relative_to(root).parts))
    )
    meta = frontmatter((root / "SKILL.md").read_text(encoding="utf-8", errors="replace"))
    name = meta.get("name") or root.name
    out_dir = Path(args.out).expanduser().resolve() if args.out else workdir
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / f"{re.sub(r'[^a-z0-9-]+', '-', name.lower()).strip('-') or 'skill'}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.relative_to(root).as_posix())

    relative = [p.relative_to(root).as_posix() for p in files]
    print(
        json.dumps(
            {
                "zip": str(zip_path),
                "root": str(root),
                "name": name,
                "description": meta.get("description", ""),
                "files": relative,
                "hints": {
                    # Where an example prompt may already be written down.
                    "prompt_sources": [f for f in relative if HINT_NAMES.search(f)],
                    "has_fixtures": any(f.startswith("tests/fixtures/") for f in relative),
                    "has_skill_json": "skill.json" in relative,
                },
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
