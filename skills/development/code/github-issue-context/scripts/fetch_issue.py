#!/usr/bin/env python3
"""Fetch a GitHub issue (metadata + comments, in chronological order) via `gh`.

Usage:
    python3 fetch_issue.py <issue_number_or_url> [--repo owner/name] [--out-dir .agent/issues]

Writes the raw `gh issue view --json ...` payload verbatim to
  <out-dir>/<number>/raw_issue.json
and prints a small summary JSON to stdout. This script never summarizes,
filters, or drops any comment — that happens later, in build_context.py,
where the original data always remains available alongside any derived view.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

ISSUE_FIELDS = (
    "number,title,body,author,labels,comments,state,url,"
    "createdAt,updatedAt,assignees,milestone"
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("issue_ref", help="Issue number (427) or full URL")
    parser.add_argument("--repo", help="owner/name (auto-detected from the current git repo if omitted)")
    parser.add_argument("--out-dir", default=".agent/issues", help="Root directory for issue context bundles")
    args = parser.parse_args()

    try:
        common.ensure_gh_ready()
        url_repo, number = common.parse_issue_reference(args.issue_ref)
        repo = common.resolve_repo(args.repo or url_repo)

        common.log(f"Fetching issue #{number} from {repo} ...")
        raw = common.run_gh_json(
            ["issue", "view", str(number), "--repo", repo, "--json", ISSUE_FIELDS]
        )
    except common.SkillError as exc:
        common.print_json(exc.to_dict())
        return 1

    paths = common.issue_paths(args.out_dir, number)
    paths.ensure_dirs()
    common.atomic_write_json(paths.raw_issue, raw)

    common.log(f"Wrote {paths.raw_issue}")
    common.print_json(
        {
            "status": "ok",
            "repository": repo,
            "number": number,
            "title": raw.get("title"),
            "state": raw.get("state"),
            "updated_at": raw.get("updatedAt"),
            "comments_count": len(raw.get("comments") or []),
            "raw_issue_path": str(paths.raw_issue),
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
