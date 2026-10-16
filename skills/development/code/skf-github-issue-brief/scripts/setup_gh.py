#!/usr/bin/env python3
"""Check the GitHub CLI (gh) and install it when it is missing.

Usage:
    # Report only — never changes the machine.
    python3 setup_gh.py [--need-project]

    # Install gh with the recommended method (or the one named).
    python3 setup_gh.py --install [--method brew|port|apt|dnf|pacman|zypper|winget|scoop|choco|release]

Both print one JSON object. The report lists every install method this
machine can use, the recommended one, and the next steps (install, then
`gh auth login`, plus `read:project` when --need-project is passed for
reading a GitHub Project board).

Methods that need sudo are only run when sudo works without a password
prompt (`sudo -n true`); otherwise the script returns the command for the
user to run themselves. The `release` method needs no package manager and
no admin rights: it downloads the official build from github.com/cli/cli,
checks it against the release's SHA-256 checksums, and puts gh in the
user's own folder (~/.local/bin, or %LOCALAPPDATA%\\Programs\\gh\\bin on
Windows). `gh auth login` is interactive, so this script never runs it —
it tells the user exactly what to type.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

RELEASES_API = "https://api.github.com/repos/cli/cli/releases/latest"
MAX_DOWNLOAD_BYTES = 150 * 1024 * 1024
LOGIN_COMMAND = "{gh} auth login --web --git-protocol https"
PROJECT_SCOPE_COMMAND = "{gh} auth refresh --scopes read:project"

APT_COMMAND = (
    "(type -p wget >/dev/null || (sudo apt-get update && sudo apt-get install wget -y))"
    " && sudo mkdir -p -m 755 /etc/apt/keyrings"
    " && wget -qO- https://cli.github.com/packages/githubcli-archive-keyring.gpg"
    " | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null"
    " && sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg"
    ' && echo "deb [arch=$(dpkg --print-architecture)'
    ' signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg]'
    ' https://cli.github.com/packages stable main"'
    " | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null"
    " && sudo apt-get update && sudo apt-get install gh -y"
)


def _platform() -> tuple[str, str]:
    system = platform.system()
    machine = platform.machine().lower()
    arch = {"x86_64": "amd64", "amd64": "amd64", "arm64": "arm64", "aarch64": "arm64"}.get(machine, machine)
    return system, arch


def install_methods() -> list[dict]:
    """Every method usable on this machine, best first. `release` is always last."""
    system, _ = _platform()
    has = lambda tool: shutil.which(tool) is not None  # noqa: E731
    methods: list[dict] = []
    if system == "Darwin":
        if has("brew"):
            methods.append({"id": "brew", "command": "brew install gh", "sudo": False})
        if has("port"):
            methods.append({"id": "port", "command": "sudo port install gh", "sudo": True})
    elif system == "Linux":
        if has("apt-get"):
            methods.append({"id": "apt", "command": APT_COMMAND, "sudo": True})
        if has("dnf"):
            methods.append({"id": "dnf", "command": "sudo dnf install -y gh", "sudo": True})
        if has("pacman"):
            methods.append({"id": "pacman", "command": "sudo pacman -S --noconfirm github-cli", "sudo": True})
        if has("zypper"):
            methods.append({"id": "zypper", "command": "sudo zypper install -y gh", "sudo": True})
        if has("brew"):
            methods.append({"id": "brew", "command": "brew install gh", "sudo": False})
    elif system == "Windows":
        if has("winget"):
            methods.append({
                "id": "winget",
                "command": "winget install --id GitHub.cli -e --accept-source-agreements --accept-package-agreements",
                "sudo": False,
            })
        if has("scoop"):
            methods.append({"id": "scoop", "command": "scoop install gh", "sudo": False})
        if has("choco"):
            methods.append({"id": "choco", "command": "choco install gh -y", "sudo": False})
    methods.append({
        "id": "release",
        "command": f"python3 {Path(__file__).resolve()} --install --method release",
        "sudo": False,
        "installs_to": str(common.user_install_dir()),
    })
    # Prefer a method that needs no password when there is one.
    methods.sort(key=lambda m: (m["sudo"], m["id"] == "release"))
    return methods


def report(need_project: bool) -> dict:
    system, arch = _platform()
    gh = common.gh_executable()
    payload: dict = {
        "status": "ok",
        "platform": {"system": system, "arch": arch},
        "gh": {"installed": gh is not None, "path": gh, "version": None},
        "auth": None,
        "next_steps": [],
        "ready": False,
    }
    if gh is None:
        methods = install_methods()
        payload["install_methods"] = methods
        payload["recommended_method"] = methods[0]["id"]
        payload["next_steps"] = [
            f"Ask the user before installing, then run: python3 {Path(__file__).resolve()} "
            f"--install --method {methods[0]['id']}",
            f"Then have the user run: {LOGIN_COMMAND.format(gh='gh')}",
        ]
        return payload

    version = subprocess.run([gh, "--version"], capture_output=True, text=True, timeout=15)
    payload["gh"]["version"] = (version.stdout.splitlines() or [""])[0].strip() or None
    payload["gh"]["on_path"] = shutil.which("gh") is not None
    auth = common.gh_auth_status()
    payload["auth"] = auth
    gh_cmd = "gh" if payload["gh"]["on_path"] else f'"{gh}"'
    if not payload["gh"]["on_path"]:
        payload["next_steps"].append(
            f"gh works from this skill, but {Path(gh).parent} is not on PATH: "
            "suggest the user add it to their shell profile to call gh themselves."
        )
    if not auth["authenticated"]:
        scopes = " --scopes read:project" if need_project else ""
        payload["next_steps"].append(
            f"Have the user run, in a terminal or in Claude Code prefixed with !: {LOGIN_COMMAND.format(gh=gh_cmd)}{scopes}"
        )
    missing_scope = need_project and auth["scopes"] is not None and not {"project", "read:project"} & set(auth["scopes"])
    if auth["authenticated"] and missing_scope:
        payload["next_steps"].append(
            f"Have the user run, in a terminal or in Claude Code prefixed with !: {PROJECT_SCOPE_COMMAND.format(gh=gh_cmd)}"
        )
    payload["ready"] = auth["authenticated"] and not missing_scope
    return payload


def _fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "skf-github-issue-brief"})
    with urllib.request.urlopen(request, timeout=60, context=common.ssl_context()) as response:
        data = response.read(MAX_DOWNLOAD_BYTES + 1)
    if len(data) > MAX_DOWNLOAD_BYTES:
        raise common.SkillError(f"{url} is larger than {MAX_DOWNLOAD_BYTES} bytes.")
    return data


def install_from_release() -> str:
    system, arch = _platform()
    os_tag = {"Darwin": "macOS", "Linux": "linux", "Windows": "windows"}.get(system)
    if os_tag is None or arch not in ("amd64", "arm64"):
        raise common.SkillError(f"No prebuilt gh for {system}/{arch}: install it from https://cli.github.com/")

    release = json.loads(_fetch(RELEASES_API))
    assets = {a["name"]: a["browser_download_url"] for a in release.get("assets", [])}
    archive_re = re.compile(rf"^gh_[\d.]+_{os_tag}_{arch}\.(zip|tar\.gz)$")
    archive = next((name for name in assets if archive_re.match(name)), None)
    checksums = next((name for name in assets if name.endswith("_checksums.txt")), None)
    if archive is None or checksums is None:
        raise common.SkillError(
            f"Release {release.get('tag_name')} has no {os_tag}_{arch} archive: install from https://cli.github.com/"
        )

    common.log(f"Downloading {archive} ...")
    data = _fetch(assets[archive])
    expected = None
    for line in _fetch(assets[checksums]).decode().splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1] == archive:
            expected = parts[0]
    actual = hashlib.sha256(data).hexdigest()
    if expected is None or expected != actual:
        raise common.SkillError(f"Checksum mismatch for {archive} — nothing installed.")

    binary_name = "gh.exe" if system == "Windows" else "gh"
    if archive.endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            member = next(n for n in zf.namelist() if n.endswith(f"bin/{binary_name}"))
            binary = zf.read(member)
    else:
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tf:
            member = next(m for m in tf.getmembers() if m.name.endswith(f"bin/{binary_name}"))
            binary = tf.extractfile(member).read()

    target_dir = common.user_install_dir()
    target = target_dir / binary_name
    common.atomic_write_bytes(target, binary)
    target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return str(target)


def install(method_id: str | None) -> dict:
    if common.gh_executable():
        return {"status": "ok", "message": "gh is already installed.", **report(False)}
    methods = install_methods()
    method = next((m for m in methods if m["id"] == method_id), None) if method_id else methods[0]
    if method is None:
        raise common.SkillError(
            f"Method {method_id!r} is not available here. Available: {', '.join(m['id'] for m in methods)}"
        )

    if method["id"] == "release":
        path = install_from_release()
    else:
        if method["sudo"] and subprocess.run(["sudo", "-n", "true"], capture_output=True).returncode != 0:
            return {
                "status": "needs_user",
                "message": "This method needs sudo with a password, which this script can't type.",
                "run_yourself": method["command"],
                "alternative": "Or install without admin rights: --install --method release",
            }
        common.log(f"Running: {method['command']}")
        shell = os.name != "nt" or method["id"] not in ("winget", "scoop", "choco")
        result = subprocess.run(method["command"], shell=shell, timeout=900)
        if result.returncode != 0:
            raise common.SkillError(f"`{method['command']}` exited with code {result.returncode}.")
        path = common.gh_executable()
        if path is None:
            raise common.SkillError(
                "The install finished but gh is still not found: open a new terminal "
                "(PATH may need refreshing) or try --method release."
            )
    return {"status": "ok", "installed_with": method["id"], "gh_path": path, **{
        k: v for k, v in report(False).items() if k in ("gh", "auth", "next_steps")
    }}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--install", action="store_true", help="Install gh if it is missing")
    parser.add_argument("--method", help="Install method id from the report (default: the recommended one)")
    parser.add_argument("--need-project", action="store_true", help="Also check the read:project scope (board mode)")
    args = parser.parse_args()
    try:
        payload = install(args.method) if args.install else report(args.need_project)
    except common.SkillError as exc:
        common.print_json(exc.to_dict())
        return 1
    except Exception as exc:  # network errors, malformed archive, ...
        common.print_json({"status": "error", "error_type": "install_failed", "message": str(exc),
                           "remediation": ["Install gh by hand: https://cli.github.com/"]})
        return 1
    common.print_json(payload)
    return 0 if payload.get("status") in ("ok", "needs_user") else 1


if __name__ == "__main__":
    raise SystemExit(main())
