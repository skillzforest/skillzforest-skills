#!/usr/bin/env python3
"""Prepare the context bundle of many issues at once — a whole GitHub Project
board, or every issue of a repository — and write a work queue.

Usage:
    # Every item of a GitHub Project board (issues of the target repository)
    python3 prepare_issues.py --board https://github.com/orgs/acme/projects/7 \\
        [--status "Todo" --status "In progress"] [--label bug] [--query "assignee:@me"]

    # Every open issue of the repository
    python3 prepare_issues.py --all [--label bug] [--state open|closed|all]

Common options: --repo owner/name (default: the current directory's repo),
--limit 200, --refresh, --out-dir .agent/issues.

For each issue it runs the single-issue pipeline (fetch_issue.py, the
freshness check, extract_attachments.py, download_attachments.py,
build_context.py), reusing bundles that are still FRESH. It then writes:

  <out-dir>/queue.json   machine-readable queue (one entry per issue)
  <out-dir>/INDEX.md     the same queue, readable

Issues whose downloaded screenshots have not been inspected yet are listed
in `visual_pending` — Claude reads those images, writes
visual_evidence.json, and rebuilds the context (step 5 of SKILL.md). Each
entry keeps its `fix_status` (pending / planned / fixed / skipped) across
runs, so re-running the batch never forgets which issues were already done.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

SCRIPTS = Path(__file__).resolve().parent
BOARD_RE = re.compile(r"^https?://github\.com/(?:orgs|users)/(?P<owner>[^/]+)/projects/(?P<number>\d+)")
FIX_STATUSES = ("pending", "planned", "fixed", "skipped")


def _repo_of(item: dict) -> str | None:
    content = item.get("content") or {}
    repo = content.get("repository") or item.get("repository")
    if isinstance(repo, dict):
        repo = repo.get("nameWithOwner") or repo.get("url")
    if isinstance(repo, str):
        return re.sub(r"^https?://github\.com/", "", repo).strip("/") or None
    match = re.match(r"^https?://github\.com/([^/]+/[^/]+)/issues/\d+", content.get("url") or "")
    return match.group(1) if match else None


def _quote(value: str) -> str:
    return f'"{value}"' if re.search(r"\s", value) else value


def list_board(url: str, repo: str, args) -> tuple[list[dict], list[dict]]:
    match = BOARD_RE.match(url.strip())
    if not match:
        raise common.SkillError(
            f"Not a GitHub Project URL: {url!r} — expected https://github.com/orgs/<org>/projects/<n> "
            "or https://github.com/users/<user>/projects/<n>"
        )
    common.ensure_project_scope()
    query = ["is:issue"]
    if args.state != "all":
        query.append(f"is:{args.state}")
    if args.status:
        query.append("status:" + ",".join(_quote(s) for s in args.status))
    query += [f"label:{_quote(label)}" for label in args.label or []]
    if args.query:
        query.append(args.query)

    common.log(f"Listing board {match.group('owner')}/projects/{match.group('number')} ({' '.join(query)}) ...")
    data = common.run_gh_json(
        ["project", "item-list", match.group("number"), "--owner", match.group("owner"),
         "--format", "json", "--limit", str(args.limit), "--query", " ".join(query)],
        timeout=120,
    )
    wanted_status = {s.lower() for s in args.status or []}
    selected, skipped = [], []
    for item in data.get("items") or []:
        content = item.get("content") or {}
        entry = {"number": content.get("number"), "title": content.get("title") or item.get("title"),
                 "url": content.get("url"), "board_status": item.get("status")}
        item_repo = _repo_of(item)
        if content.get("type") != "Issue":
            skipped.append({**entry, "reason": f"{content.get('type') or 'item'} — not an issue"})
        elif wanted_status and (item.get("status") or "").lower() not in wanted_status:
            continue  # the query already filters; this only guards older gh versions
        elif item_repo and item_repo.lower() != repo.lower():
            skipped.append({**entry, "reason": f"belongs to {item_repo}, not {repo}"})
        else:
            selected.append(entry)
    return selected, skipped


def list_repo(repo: str, args) -> tuple[list[dict], list[dict]]:
    cmd = ["issue", "list", "--repo", repo, "--state", args.state, "--limit", str(args.limit),
           "--json", "number,title,url"]
    for label in args.label or []:
        cmd += ["--label", label]
    if args.query:
        cmd += ["--search", args.query]
    common.log(f"Listing {args.state} issues of {repo} ...")
    issues = common.run_gh_json(cmd, timeout=120)
    return [{"number": i["number"], "title": i["title"], "url": i["url"], "board_status": None} for i in issues], []


def _run(script: str, *argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPTS / script), *argv], capture_output=True, text=True, timeout=600)


def _error_message(result: subprocess.CompletedProcess) -> str:
    try:
        return json.loads(result.stdout).get("message") or result.stdout.strip()
    except Exception:
        return (result.stderr or result.stdout).strip()[-500:]


def prepare_one(number: int, repo: str, out_dir: str, refresh: bool) -> dict:
    issue_dir = Path(out_dir) / str(number)
    fetched = _run("fetch_issue.py", str(number), "--repo", repo, "--out-dir", out_dir)
    if fetched.returncode != 0:
        return {"brief": "error", "error": _error_message(fetched)}

    freshness = _run("build_context.py", str(issue_dir), "--check-freshness").stdout.strip()
    if freshness == "FRESH" and not refresh:
        brief = "reused"
    else:
        for script in ("extract_attachments.py", "download_attachments.py"):
            step = _run(script, str(issue_dir))
            if step.returncode != 0:
                return {"brief": "error", "error": f"{script}: {_error_message(step)}"}
        built = _run("build_context.py", str(issue_dir), "--repo", repo)
        if built.returncode != 0:
            return {"brief": "error", "error": f"build_context.py: {_error_message(built)}"}
        brief = "built"

    assets = common.load_json(issue_dir / "assets.json", default=[])
    evidence = common.load_json(issue_dir / "visual_evidence.json", default=[])
    inspected = {e.get("asset_id") for e in evidence}
    pending_images = [str(issue_dir / a["local_path"]) for a in assets
                      if a.get("status") == "downloaded" and a.get("id") not in inspected]
    raw = common.load_json(issue_dir / "raw_issue.json", default={})
    return {
        "brief": brief,
        "state": raw.get("state"),
        "labels": [label.get("name") for label in raw.get("labels") or []],
        "context_md": str(issue_dir / "context.md"),
        "images_to_inspect": pending_images,
    }


def render_index(queue: dict) -> str:
    source = queue["source"]
    lines = [
        f"# Issue queue — {queue['repository']}",
        "",
        f"Source: {source['kind']}" + (f" {source['url']}" if source.get("url") else "")
        + (f" · filters: {source['filters']}" if source.get("filters") else ""),
        f"Prepared: {queue['generated_at']}",
        "",
        "Work through it with `/skf-github-issue-fix <number>` (or `--next`).",
        "",
        "| # | Title | Board status | Labels | Brief | Screenshots to inspect | Fix |",
        "|---|---|---|---|---|---|---|",
    ]
    for issue in queue["issues"]:
        title = (issue.get("title") or "").replace("|", "\\|")
        link = f"[{title}]({issue['number']}/context.md)" if issue["brief"] != "error" else title
        lines.append(
            f"| {issue['number']} | {link} | {issue.get('board_status') or ''} | "
            f"{', '.join(issue.get('labels') or [])} | "
            f"{issue['brief'] if issue['brief'] != 'error' else 'error: ' + issue.get('error', '')[:80]} | "
            f"{len(issue.get('images_to_inspect') or [])} | {issue['fix_status']} |"
        )
    if queue["skipped"]:
        lines += ["", "## Not prepared", ""]
        lines += [f"- {s.get('number') or ''} {s.get('title') or ''} — {s['reason']}" for s in queue["skipped"]]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--board", metavar="PROJECT_URL", help="GitHub Project (v2) board URL")
    source.add_argument("--all", action="store_true", help="Every issue of the repository")
    parser.add_argument("--repo", help="owner/name (auto-detected from the current git repo if omitted)")
    parser.add_argument("--state", choices=("open", "closed", "all"), default="open")
    parser.add_argument("--status", action="append", help="Board column / Status value to keep (repeatable)")
    parser.add_argument("--label", action="append", help="Keep issues with this label (repeatable)")
    parser.add_argument("--query", help="Extra filter: Projects filter syntax with --board, GitHub search with --all")
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--refresh", action="store_true", help="Rebuild every bundle even if FRESH")
    parser.add_argument("--out-dir", default=".agent/issues")
    args = parser.parse_args()

    try:
        common.ensure_gh_ready()
        repo = common.resolve_repo(args.repo)
        if args.board:
            selected, skipped = list_board(args.board, repo, args)
        else:
            if args.status:
                raise common.SkillError("--status only applies to --board (it filters on the board's Status field).")
            selected, skipped = list_repo(repo, args)
    except common.SkillError as exc:
        common.print_json(exc.to_dict())
        return 1

    out_root = Path(args.out_dir)
    queue_path = out_root / "queue.json"
    previous = {i["number"]: i for i in (common.load_json(queue_path, default={}) or {}).get("issues", [])}

    issues = []
    for n, entry in enumerate(selected, 1):
        common.log(f"[{n}/{len(selected)}] #{entry['number']} {entry.get('title') or ''}")
        result = prepare_one(entry["number"], repo, args.out_dir, args.refresh)
        fix_status = (previous.get(entry["number"]) or {}).get("fix_status", "pending")
        issues.append({**entry, **result, "fix_status": fix_status if fix_status in FIX_STATUSES else "pending"})

    queue = {
        "schema_version": "1.0",
        "generated_at": common.now_iso(),
        "repository": repo,
        "source": {
            "kind": "board" if args.board else "repository",
            "url": args.board,
            "filters": {k: v for k, v in {"state": args.state, "status": args.status, "label": args.label,
                                           "query": args.query}.items() if v},
        },
        "issues": issues,
        "skipped": skipped,
    }
    common.atomic_write_json(queue_path, queue)
    common.atomic_write_text(out_root / "INDEX.md", render_index(queue))

    counts: dict[str, int] = {}
    for issue in issues:
        counts[issue["brief"]] = counts.get(issue["brief"], 0) + 1
    common.print_json({
        "status": "ok",
        "repository": repo,
        "issues": len(issues),
        "briefs": counts,
        "skipped": len(skipped),
        "visual_pending": [{"number": i["number"], "images": i["images_to_inspect"]}
                           for i in issues if i.get("images_to_inspect")],
        "errors": [{"number": i["number"], "error": i["error"]} for i in issues if i["brief"] == "error"],
        "queue_path": str(queue_path),
        "index_path": str(out_root / "INDEX.md"),
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
