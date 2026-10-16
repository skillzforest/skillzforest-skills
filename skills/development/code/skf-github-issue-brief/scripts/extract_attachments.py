#!/usr/bin/env python3
"""Extract candidate image/attachment URLs from an issue body and its comments.

Usage:
    python3 extract_attachments.py <issue-dir>

Reads <issue-dir>/raw_issue.json (written by fetch_issue.py) and writes
<issue-dir>/attachments_extracted.json: a deduplicated, ordered list of
{ url, type, source_type, source_comment_id } — issue body first, then
comments in chronological order, first-seen URL wins.

This is intentionally just URL discovery: no network calls happen here.
Downloading is a separate, failure-tolerant step (download_attachments.py)
so a slow or broken host never blocks extraction.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

_MARKDOWN_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(\s*<?([^\s)>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
_HTML_IMG_RE = re.compile(r"<img[^>]+src=[\"']([^\"']+)[\"']", re.IGNORECASE)
_IMAGE_EXT_URL_RE = re.compile(
    r"https?://[^\s)\]\"'<>]+?\.(?:png|jpe?g|webp|gif)(?:\?[^\s)\]\"'<>]*)?",
    re.IGNORECASE,
)
_GH_USER_ATTACHMENT_RE = re.compile(
    r"https?://github\.com/user-attachments/assets/[A-Za-z0-9-]+"
)
_GH_USER_IMAGES_RE = re.compile(
    r"https?://user-images\.githubusercontent\.com/[^\s)\]\"'<>]+"
)

_FUTURE_EXT_RE = re.compile(
    r"https?://[^\s)\]\"'<>]+?\.(?:mp4|mov|webm|pdf|log|txt)(?:\?[^\s)\]\"'<>]*)?",
    re.IGNORECASE,
)


def _ext_of(url: str) -> str:
    path = url.split("?", 1)[0]
    return Path(path).suffix.lower()


def _classify(url: str) -> str:
    ext = _ext_of(url)
    if ext in common.IMAGE_MIME_BY_EXT:
        return "image"
    if ext in common.FUTURE_TYPE_BY_EXT:
        return common.FUTURE_TYPE_BY_EXT[ext]
    if _GH_USER_ATTACHMENT_RE.match(url) or _GH_USER_IMAGES_RE.match(url):
        # No extension in the URL itself — resolved by content-type at download time.
        return "image_candidate"
    return "unknown"


def _find_urls(text: str) -> list[str]:
    if not text:
        return []
    found: list[str] = []
    for pattern in (
        _MARKDOWN_IMAGE_RE,
        _HTML_IMG_RE,
        _GH_USER_ATTACHMENT_RE,
        _GH_USER_IMAGES_RE,
        _IMAGE_EXT_URL_RE,
        _FUTURE_EXT_RE,
    ):
        for match in pattern.finditer(text):
            url = match.group(1) if match.groups() else match.group(0)
            found.append(url.rstrip(").,;\"'"))
    return found


def extract(raw: dict) -> list[dict]:
    seen: set[str] = set()
    ordered: list[dict] = []

    def add_all(text: str, source_type: str, source_comment_id):
        for url in _find_urls(text):
            if url in seen:
                continue
            seen.add(url)
            ordered.append(
                {
                    "url": url,
                    "type": _classify(url),
                    "source_type": source_type,
                    "source_comment_id": source_comment_id,
                }
            )

    add_all(raw.get("body") or "", "issue_body", None)
    for comment in raw.get("comments") or []:
        add_all(comment.get("body") or "", "comment", comment.get("id"))

    return ordered


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("issue_dir", help="Path to .agent/issues/<number>")
    args = parser.parse_args()

    issue_dir = Path(args.issue_dir)
    raw_path = issue_dir / "raw_issue.json"
    raw = common.load_json(raw_path)
    if raw is None:
        common.print_json(
            {
                "status": "error",
                "error_type": "raw_issue_missing",
                "message": f"{raw_path} not found — run fetch_issue.py first.",
            }
        )
        return 1

    extracted = extract(raw)
    out_path = issue_dir / "attachments_extracted.json"
    common.atomic_write_json(out_path, extracted)

    by_type: dict[str, int] = {}
    for item in extracted:
        by_type[item["type"]] = by_type.get(item["type"], 0) + 1

    common.log(f"Found {len(extracted)} candidate attachment(s): {by_type}")
    common.print_json(
        {
            "status": "ok",
            "count": len(extracted),
            "by_type": by_type,
            "attachments_extracted_path": str(out_path),
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
