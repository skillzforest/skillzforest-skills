#!/usr/bin/env python3
"""Download extracted attachments into .agent/issues/<number>/assets/.

Usage:
    python3 download_attachments.py <issue-dir>

Reads <issue-dir>/attachments_extracted.json and writes:
  - downloaded files under <issue-dir>/assets/ with deterministic names
    (issue-body-image-001.png, comment-<id>-image-001.png, ...)
  - <issue-dir>/assets.json, a manifest with one entry per attachment,
    including ones that failed — a single bad URL never aborts the run.

Only image/* content is saved. Non-image types are recorded with status
"skipped_unsupported_type" so the schema is ready for video/pdf/log support
later without a manifest migration.
"""
from __future__ import annotations

import argparse
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

DOWNLOADABLE_TYPES = {"image", "image_candidate"}


def _guess_ext(url: str, content_type: str) -> str:
    ct = (content_type or "").split(";", 1)[0].strip().lower()
    if ct in common.EXT_BY_IMAGE_MIME:
        return common.EXT_BY_IMAGE_MIME[ct]
    url_ext = Path(url.split("?", 1)[0]).suffix.lower()
    if url_ext in common.IMAGE_MIME_BY_EXT:
        return url_ext
    return ".bin"


def _fetch(url: str, token: str | None) -> tuple[bytes, str]:
    """Return (bytes, content_type). Raises on any failure."""
    headers = {"User-Agent": "github-issue-context-skill"}
    host = urlparse(url).netloc.lower()
    if token and host in common.GITHUB_ASSET_HOSTS:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=15) as response:
        content_type = response.headers.get("Content-Type", "")
        data = response.read(common.MAX_ASSET_BYTES + 1)
        if len(data) > common.MAX_ASSET_BYTES:
            raise ValueError(f"file exceeds {common.MAX_ASSET_BYTES} bytes limit")
        return data, content_type


def download_all(issue_dir: Path, attachments: list[dict]) -> list[dict]:
    token = common.get_gh_token()
    manifest: list[dict] = []
    seq_by_scope: dict[tuple[str, object], int] = {}
    asset_seq = 0

    for item in attachments:
        asset_seq += 1
        asset_id = f"asset-{asset_seq:03d}"
        entry = {
            "id": asset_id,
            "type": "image" if item["type"] in DOWNLOADABLE_TYPES else item["type"],
            "source_type": item["source_type"],
            "source_comment_id": item["source_comment_id"],
            "original_url": item["url"],
            "local_path": None,
            "mime_type": None,
            "status": "pending",
        }

        if item["type"] not in DOWNLOADABLE_TYPES:
            entry["status"] = "skipped_unsupported_type"
            manifest.append(entry)
            continue

        try:
            data, content_type = _fetch(item["url"], token)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
            entry["status"] = "error"
            entry["error"] = str(exc)
            common.log(f"{asset_id}: download failed for {item['url']}: {exc}")
            manifest.append(entry)
            continue

        ct = (content_type or "").split(";", 1)[0].strip().lower()
        if not ct.startswith("image/"):
            entry["status"] = "error"
            entry["error"] = f"unexpected content-type: {ct or 'unknown'}"
            common.log(f"{asset_id}: rejected non-image content-type '{ct}' for {item['url']}")
            manifest.append(entry)
            continue

        ext = _guess_ext(item["url"], content_type)
        scope = (item["source_type"], item["source_comment_id"])
        seq_by_scope[scope] = seq_by_scope.get(scope, 0) + 1
        scope_seq = seq_by_scope[scope]

        if item["source_type"] == "issue_body":
            filename = f"issue-body-image-{scope_seq:03d}{ext}"
        else:
            filename = f"comment-{item['source_comment_id']}-image-{scope_seq:03d}{ext}"

        local_path = issue_dir / "assets" / filename
        common.atomic_write_bytes(local_path, data)

        entry["type"] = "image"
        entry["local_path"] = f"assets/{filename}"
        entry["mime_type"] = ct
        entry["status"] = "downloaded"
        common.log(f"{asset_id}: downloaded {filename} ({len(data)} bytes)")
        manifest.append(entry)

    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("issue_dir", help="Path to .agent/issues/<number>")
    args = parser.parse_args()

    issue_dir = Path(args.issue_dir)
    extracted_path = issue_dir / "attachments_extracted.json"
    attachments = common.load_json(extracted_path)
    if attachments is None:
        common.print_json(
            {
                "status": "error",
                "error_type": "attachments_extracted_missing",
                "message": f"{extracted_path} not found — run extract_attachments.py first.",
            }
        )
        return 1

    (issue_dir / "assets").mkdir(parents=True, exist_ok=True)
    manifest = download_all(issue_dir, attachments)
    manifest_path = issue_dir / "assets.json"
    common.atomic_write_json(manifest_path, manifest)

    counts: dict[str, int] = {}
    for entry in manifest:
        counts[entry["status"]] = counts.get(entry["status"], 0) + 1

    common.print_json(
        {
            "status": "ok",
            "counts": counts,
            "assets_manifest_path": str(manifest_path),
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
