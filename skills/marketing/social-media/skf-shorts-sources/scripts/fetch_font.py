#!/usr/bin/env python3
"""Download a Google Fonts family (latin subset, woff2) into a short's kit (stdlib only).

    fetch_font.py "<Family Name>" --short shorts/<slug> [--weights 400,700,800] [--write]
    fetch_font.py "<Family Name>" --short shorts/<slug> --url <woff2 url> [--weight "100 900"] [--write]

Asks the Google Fonts CSS API for the family, keeps the latin files (accents of
French, Spanish, German… included), saves them in <short>/assets/fonts/ and prints
the `fontFiles` entries for kit.json > brand. --write adds them to kit.json directly.
A variable font served as one file for several weights becomes one entry whose
weight is a range ("400 800").
--url downloads one font file the website itself serves (site.json > fontFaces,
take the "latin" file) instead of asking Google Fonts.
"""
import argparse
import json
import re
import ssl
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"


def get(url, binary=False):
    data, _, _ = _get(url, {"User-Agent": UA}, 30)
    return data if binary else data.decode()


def _ssl_context():
    try:
        import certifi  # noqa: PLC0415 — optional
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return None


def _get(url, headers, timeout, limit=None):
    """GET with urllib; on a certificate error (Python without root certificates,
    common on macOS), retry with certifi, then with the system curl."""
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read(limit) if limit else resp.read(), resp.headers.get_content_type(), resp.headers.get_content_charset()
    except urllib.error.URLError as exc:
        if "CERTIFICATE_VERIFY_FAILED" not in str(exc):
            raise
    ctx = _ssl_context()
    if ctx:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.read(limit) if limit else resp.read(), resp.headers.get_content_type(), resp.headers.get_content_charset()
    cmd = ["curl", "-sSL", "--fail", "--max-time", str(timeout), "-w", "\\n%{content_type}"]
    for k, v in headers.items():
        cmd += ["-H", f"{k}: {v}"]
    done = subprocess.run(cmd + [url], capture_output=True)
    if done.returncode != 0:
        raise urllib.error.URLError(done.stderr.decode(errors="replace").strip() or "curl failed")
    body, _, ctype = done.stdout.rpartition(b"\n")
    ctype = ctype.decode(errors="replace")
    charset = ctype.split("charset=")[-1].strip() if "charset=" in ctype else None
    return (body[:limit] if limit else body), ctype.split(";")[0].strip(), charset


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("family")
    ap.add_argument("--short", required=True)
    ap.add_argument("--weights", default="400,700,800")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--url", help="font file served by the site (woff2, woff, ttf)")
    ap.add_argument("--weight", default="400", help='with --url: "700" or a range "100 900"')
    args = ap.parse_args()
    if args.url:
        return save(args, {args.url: [int(w) for w in args.weight.split()]}, keep_ext=True)

    weights = sorted({int(w) for w in args.weights.split(",") if w.strip()})
    fam = urllib.parse.quote_plus(args.family)
    css = None
    for spec in (f"{fam}:wght@{';'.join(map(str, weights))}", fam):
        try:
            css = get(f"https://fonts.googleapis.com/css2?family={spec}&display=swap")
            break
        except urllib.error.URLError:
            continue
    if not css:
        sys.exit(f"« {args.family} » introuvable sur Google Fonts : prendre la police la plus proche, ou fournir ses fichiers")

    blocks = re.findall(r"/\*\s*([\w-]+)\s*\*/\s*@font-face\s*{([^}]*)}", css)
    found = {}
    for subset, body in blocks:
        if subset != "latin":
            continue
        if "italic" in re.search(r"font-style:\s*(\w+)", body).group(1):
            continue
        weight = int(re.search(r"font-weight:\s*(\d+)", body).group(1))
        url = re.search(r"url\(([^)]+)\)", body).group(1)
        found.setdefault(url, []).append(weight)
    if not found:
        sys.exit("aucun fichier latin dans la réponse de Google Fonts")
    return save(args, found)


def save(args, found, keep_ext=False):
    short = Path(args.short)
    folder = short / "assets" / "fonts"
    folder.mkdir(parents=True, exist_ok=True)
    base = re.sub(r"[^A-Za-z0-9]+", "", args.family)
    entries = []
    for url, ws in found.items():
        ws = sorted(set(ws))
        label = f"{ws[0]}-{ws[-1]}" if len(ws) > 1 else str(ws[0])
        ext = Path(urllib.parse.urlparse(url).path).suffix.lower() if keep_ext else ".woff2"
        target = folder / f"{base}-{label}{ext or '.woff2'}"
        target.write_bytes(get(url, binary=True))
        entries.append({"family": args.family, "file": str(target.relative_to(short)),
                        "weight": f"{ws[0]} {ws[-1]}" if len(ws) > 1 else str(ws[0])})

    if args.write:
        kit_path = short / "kit.json"
        kit = json.loads(kit_path.read_text())
        files = kit.setdefault("brand", {}).setdefault("fontFiles", [])
        files[:] = [f for f in files if f.get("family") != args.family] + entries
        kit_path.write_text(json.dumps(kit, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(entries, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    sys.exit(main())
