"""Shared helpers for the github-issue-context skill scripts.

Every script in this skill is a small, deterministic step in a pipeline:

  fetch_issue.py -> extract_attachments.py -> download_attachments.py -> build_context.py

They communicate through files under .agent/issues/<number>/, never through
shared process state, so each step can be re-run independently. This module
only holds the plumbing (gh invocation, path layout, atomic writes) that
every step needs.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

SKILL_TAG = "github-issue-context"

MAX_ASSET_BYTES = 20 * 1024 * 1024  # 20 MB — generous for screenshots, bounded against abuse

IMAGE_MIME_BY_EXT = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
}
EXT_BY_IMAGE_MIME = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
    "image/gif": ".gif",
}

# Non-image types the extractor already recognizes so the manifest schema
# does not need to change when downloading is implemented for them later.
FUTURE_TYPE_BY_EXT = {
    ".mp4": "video",
    ".mov": "video",
    ".webm": "video",
    ".pdf": "pdf",
    ".log": "log",
    ".txt": "text",
}

# Hosts that are allowed to receive the user's gh token as a bearer header
# when downloading attachments. Never send the token anywhere else — issue
# bodies are untrusted and could otherwise be used to exfiltrate it via a
# crafted "attachment" URL pointing at an attacker-controlled host.
GITHUB_ASSET_HOSTS = {
    "github.com",
    "user-images.githubusercontent.com",
    "raw.githubusercontent.com",
    "objects.githubusercontent.com",
}


class SkillError(Exception):
    """Base class for errors that should be reported as structured JSON, not a traceback."""

    error_type = "error"
    remediation: list[str] = []

    def to_dict(self) -> dict:
        return {
            "status": "error",
            "error_type": self.error_type,
            "message": str(self),
            "remediation": self.remediation,
        }


class GhNotInstalled(SkillError):
    error_type = "gh_not_installed"
    remediation = [
        "Install the GitHub CLI: https://cli.github.com/",
        "macOS: brew install gh",
    ]


class GhNotAuthenticated(SkillError):
    error_type = "gh_not_authenticated"
    remediation = [
        "Run: gh auth login",
        "Then verify with: gh auth status",
    ]


class GhCommandError(SkillError):
    error_type = "gh_command_failed"


class IssueRefError(SkillError):
    error_type = "invalid_issue_reference"
    remediation = [
        "Pass an issue number (e.g. 427) together with --repo owner/name, "
        "or a full URL like https://github.com/owner/name/issues/427",
    ]


def log(*parts: object) -> None:
    print(f"[{SKILL_TAG}]", *parts, file=sys.stderr, flush=True)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ensure_gh_ready() -> None:
    if shutil.which("gh") is None:
        raise GhNotInstalled("The GitHub CLI ('gh') was not found on PATH.")
    result = subprocess.run(
        ["gh", "auth", "status"], capture_output=True, text=True, timeout=15
    )
    if result.returncode != 0:
        raise GhNotAuthenticated(
            "gh is installed but not authenticated (`gh auth status` failed)."
        )


def run_gh_json(args: list[str], timeout: int = 30):
    result = subprocess.run(
        ["gh", *args], capture_output=True, text=True, timeout=timeout
    )
    if result.returncode != 0:
        raise GhCommandError(
            f"`gh {' '.join(args)}` failed: {result.stderr.strip() or result.stdout.strip()}"
        )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise GhCommandError(
            f"`gh {' '.join(args)}` returned non-JSON output: {exc}"
        ) from exc


def run_gh_text(args: list[str], timeout: int = 15) -> str:
    result = subprocess.run(
        ["gh", *args], capture_output=True, text=True, timeout=timeout
    )
    if result.returncode != 0:
        raise GhCommandError(
            f"`gh {' '.join(args)}` failed: {result.stderr.strip() or result.stdout.strip()}"
        )
    return result.stdout.strip()


def get_gh_token() -> Optional[str]:
    """Return the current gh token for transient use (in-memory only).

    Never write this value to disk (context.json, logs, or otherwise).
    """
    try:
        result = subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True, timeout=10
        )
    except Exception:
        return None
    if result.returncode != 0:
        return None
    token = result.stdout.strip()
    return token or None


_URL_RE = re.compile(
    r"^https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/issues/(?P<number>\d+)/?"
)


def parse_issue_reference(ref: str) -> tuple[Optional[str], int]:
    """Parse a bare number ("427", "#427") or a full issue URL.

    Returns (owner/repo or None, issue_number).
    """
    ref = ref.strip()
    match = _URL_RE.match(ref)
    if match:
        return f"{match.group('owner')}/{match.group('repo')}", int(match.group("number"))
    bare = ref.lstrip("#")
    if bare.isdigit():
        return None, int(bare)
    raise IssueRefError(f"Could not parse issue reference: {ref!r}")


def resolve_repo(explicit: Optional[str]) -> str:
    if explicit:
        return explicit
    try:
        return run_gh_text(["repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"])
    except GhCommandError as exc:
        raise GhCommandError(
            "Could not determine the repository from the current directory. "
            f"Pass --repo owner/name explicitly. ({exc})"
        ) from exc


class IssuePaths:
    """Deterministic file layout for one issue's context bundle."""

    def __init__(self, out_root: Path, number: int):
        self.dir = out_root / str(number)
        self.assets_dir = self.dir / "assets"
        self.raw_issue = self.dir / "raw_issue.json"
        self.attachments_extracted = self.dir / "attachments_extracted.json"
        self.assets_manifest = self.dir / "assets.json"
        self.visual_evidence = self.dir / "visual_evidence.json"
        self.context_json = self.dir / "context.json"
        self.context_md = self.dir / "context.md"

    def ensure_dirs(self) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        self.assets_dir.mkdir(parents=True, exist_ok=True)


def issue_paths(out_root: str | os.PathLike, number: int) -> IssuePaths:
    return IssuePaths(Path(out_root), number)


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(path)


def atomic_write_json(path: Path, data) -> None:
    atomic_write_text(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def load_json(path: Path, default=None):
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def print_json(payload: dict) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))
