#!/usr/bin/env python3
"""Send a validated content file to a CMS, driven entirely by its profile's `adapter`.

    push_content.py <content.json> --dry-run            plan only: GET lookups run, nothing written
    push_content.py <content.json> --apply              upload media, then run the profile's steps
    push_content.py <content.json> --export <dir>       no CMS call: record.json + content.md + media
    push_content.py --libraries [--profile <p>]          fetch the profile's pick lists (categories…)

Adapter types: `http` (any REST API: uploads, lookups, ordered steps) and `export`.
See references/profile-format.md. Standard library only (curl for HTTP if present).
Prints a JSON summary; exit 0 ok, 1 a step failed, 2 bad input.
"""

import argparse
import json
import mimetypes
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

from cms_profile import condition, get, load_content, load_profile, refs_in, render, resolve_refs


class StepError(Exception):
    pass


class Http:
    def __init__(self, adapter: dict, dry_run: bool):
        base = os.environ.get(adapter.get("base_url_env", ""), "") or adapter.get("base_url_default", "")
        if not base:
            raise SystemExit(f"no base URL: set {adapter.get('base_url_env')}")
        self.base = base.rstrip("/")
        self.headers = {"Accept": "application/json"}
        auth = adapter.get("auth", {"type": "none"})
        if auth["type"] != "none":
            token = os.environ.get(auth["token_env"], "")
            if not token:
                raise SystemExit(f"{auth['token_env']} is not set")
            if auth["type"] == "bearer":
                self.headers["Authorization"] = f"Bearer {token}"
            else:
                self.headers[auth["name"]] = token
        self.dry_run = dry_run
        self.log: list[dict] = []

    def url(self, path: str, query: dict | None) -> str:
        query = {k: v for k, v in (query or {}).items() if v not in (None, "")}
        return self.base + path + (("?" + urllib.parse.urlencode(query)) if query else "")

    def request(self, method: str, path: str, *, query=None, body=None, file: Path | None = None,
                field: str = "file", extra_fields: dict | None = None):
        url = self.url(path, query)
        entry = {"method": method, "url": url}
        if body is not None:
            entry["body"] = body
        if file is not None:
            entry["file"] = str(file)
        if self.dry_run and method != "GET":
            entry["skipped"] = "dry-run"
            self.log.append(entry)
            return None
        headers = dict(self.headers)
        data = None
        if file is not None:
            boundary = uuid.uuid4().hex
            parts = b""
            for key, value in (extra_fields or {}).items():
                parts += (f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n'
                          f"{value}\r\n").encode()
            kind = mimetypes.guess_type(file.name)[0] or "application/octet-stream"
            parts += (f'--{boundary}\r\nContent-Disposition: form-data; name="{field}"; '
                      f'filename="{file.name}"\r\nContent-Type: {kind}\r\n\r\n').encode()
            data = parts + file.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
            headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        elif body is not None:
            data = json.dumps(body, ensure_ascii=False).encode()
            headers["Content-Type"] = "application/json"
        status, text = self._send(method, url, headers, data)
        entry["status"] = status
        self.log.append(entry)
        if status >= 400:
            entry["error"] = text[:800]
            raise StepError(f"{method} {url} → {status}: {text[:300]}")
        return json.loads(text) if text.strip() else None

    @staticmethod
    def _send(method, url, headers, data) -> tuple[int, str]:
        if shutil.which("curl"):  # system certificates; python.org's Python on macOS has none
            with tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / "out"
                cmd = ["curl", "-sS", "-X", method, "-o", str(out), "-w", "%{http_code}", "--max-time", "300"]
                for key, value in headers.items():
                    cmd += ["-H", f"{key}: {value}"]
                if data is not None:
                    payload = Path(tmp) / "payload"
                    payload.write_bytes(data)
                    cmd += ["--data-binary", f"@{payload}"]
                done = subprocess.run(cmd + [url], capture_output=True, text=True)
                if done.returncode != 0:
                    raise StepError(f"{method} {url}: {done.stderr.strip()}")
                return int(done.stdout.strip() or 0), out.read_text(errors="replace") if out.exists() else ""
        request = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=300) as response:
                return response.status, response.read().decode(errors="replace")
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode(errors="replace")


def lookup(http: Http, spec: dict, key: str):
    data = http.request("GET", render(spec["path"], {"key": key}), query=render(spec.get("query", {}), {"key": key}))
    items = get(data, spec["items"]) if spec.get("items") else data
    for item in items or []:
        if str(get(item, spec["match"], None)) == key:
            return get(item, spec["result"])
    return None


def run_http(content: dict, base: Path, profile: dict, dry_run: bool) -> dict:
    http = Http(profile["adapter"], dry_run)
    try:
        return _run_http(http, content, base, profile)
    except StepError as exc:
        exc.requests = http.log  # what already went through: the CMS may hold a partial record
        raise


def _run_http(http: Http, content: dict, base: Path, profile: dict) -> dict:
    adapter = profile["adapter"]
    resolved: dict[str, object] = {}
    record = content["record"]
    refs = refs_in(record) | refs_in(content.get("relations", {}))

    # 1. Lookups (read-only, also in dry-run).
    for ref in sorted(r for r in refs if r.startswith("@lookup:")):
        _, name, key = ref.split(":", 2)
        value = lookup(http, adapter["lookups"][name], key)
        if value is None:
            raise StepError(f"{ref}: not found in the CMS")
        resolved[ref] = value

    # 2. Media uploads.
    upload = adapter.get("upload")
    for key, entry in content.get("media", {}).items():
        ref = f"@media:{key}"
        if ref not in refs:
            continue
        file = (base / entry["file"]).resolve()
        ctx = {"media": {**entry, "key": key}}
        result = http.request(
            upload.get("method", "POST"), render(upload["path"], ctx), query=render(upload.get("query", {}), ctx),
            file=file, field=upload.get("field", "file"), extra_fields=render(upload.get("fields", {}), ctx),
        )
        resolved[ref] = get(result, upload["result"]) if result is not None else f"<uploaded {key}>"

    def resolver(ref: str):
        return resolved.get(ref, f"<{ref[1:]}>")

    context = {
        "content": content,
        "record": resolve_refs(record, resolver),
        "relations": resolve_refs(content.get("relations", {}), resolver),
        "vars": {},
    }
    if content.get("package"):
        context["package"] = {**content["package"], "path": str((base / content["package"]["file"]).resolve())}

    # 3. Steps, in order.
    for step in adapter.get("steps", []):
        if "lookup" in step:
            key = render(step["key"], context)
            context["vars"][step["save"]] = lookup(http, adapter["lookups"][step["lookup"]], str(key))
            continue
        if not condition(step.get("when"), context):
            continue
        body = render(step["body"], context) if "body" in step else None
        if isinstance(body, dict):
            body = {k: v for k, v in body.items() if k not in step.get("omit", [])}
        file = Path(render(step["file"], context)) if step.get("file") else None
        result = http.request(
            step["method"], render(step["path"], context), query=render(step.get("query", {}), context),
            body=None if file else body, file=file, field=step.get("field", "file"),
        )
        for var, path in step.get("save", {}).items():
            context["vars"][var] = get(result, path, None) if result is not None else f"<{step['name']}.{path}>"

    return {"requests": http.log, "vars": context["vars"], "resolved": {k: v for k, v in resolved.items()}}


def run_export(content: dict, base: Path, profile: dict, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    (out / "media").mkdir(exist_ok=True)
    copied = {}
    for key, entry in content.get("media", {}).items():
        source = (base / entry["file"]).resolve()
        target = out / "media" / f"{key}{source.suffix}"
        shutil.copy(source, target)
        copied[f"@media:{key}"] = f"media/{target.name}"
    record = resolve_refs(content["record"], lambda ref: copied.get(ref, ref))
    (out / "record.json").write_text(json.dumps(record, ensure_ascii=False, indent=2))

    lines = [f"# {get(record, profile.get('title_field', 'name'), 'Content')}", ""]

    def flatten(value, prefix=""):
        if isinstance(value, dict):
            for k, v in value.items():
                flatten(v, f"{prefix}{k}.")
        elif isinstance(value, list) and value and all(isinstance(v, str) for v in value):
            lines.append(f"**{prefix.rstrip('.')}**\n" + "\n".join(f"- {v}" for v in value) + "\n")
        elif isinstance(value, list):
            for i, v in enumerate(value):
                flatten(v, f"{prefix}{i}.")
        elif value not in (None, ""):
            lines.append(f"**{prefix.rstrip('.')}**\n{value}\n")

    flatten(record)
    (out / "content.md").write_text("\n".join(lines))
    return {"export": str(out), "files": sorted(str(p.relative_to(out)) for p in out.rglob("*") if p.is_file())}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("content", nargs="?")
    parser.add_argument("--profile")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--export", metavar="DIR")
    mode.add_argument("--libraries", action="store_true")
    args = parser.parse_args()

    if args.libraries:
        profile = load_profile(args.profile or "skillzforest")
        http = Http(profile["adapter"], dry_run=True)
        out = {}
        for name, spec in profile.get("libraries", {}).items():
            try:
                out[name] = http.request("GET", spec["path"], query=spec.get("query"))
            except StepError as exc:
                out[name] = {"error": str(exc)}
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    if not args.content:
        parser.error("content file required")
    content, base = load_content(args.content)
    profile = load_profile(args.profile or content.get("profile", ""))
    adapter_type = profile.get("adapter", {}).get("type", "export")
    try:
        if args.export or adapter_type == "export":
            out = Path(args.export or profile["adapter"].get("out_dir", "content-export")).expanduser()
            summary = run_export(content, base, profile, out if out.is_absolute() else base / out)
        else:
            summary = run_http(content, base, profile, dry_run=args.dry_run)
    except StepError as exc:
        report = {"ok": False, "error": str(exc), "requests": getattr(exc, "requests", [])}
        print(json.dumps(report, ensure_ascii=False, indent=2))
        sys.exit(1)
    print(json.dumps({"ok": True, "dry_run": bool(args.dry_run), **summary}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
