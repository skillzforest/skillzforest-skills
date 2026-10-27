#!/usr/bin/env python3
"""SEO actions as GitHub issues, through the gh command line.

Usage:
    tracker_github.py setup  --repo OWNER/REPO [--project-owner OWNER --project-number N]
    tracker_github.py upsert --repo OWNER/REPO --id ID --title TITLE --who agent|owner --priority P1|P2|P3
                             --body-file FILE [--project-owner OWNER --project-number N]
    tracker_github.py list   --repo OWNER/REPO [--who agent|owner] [--state open|closed|all]
    tracker_github.py close  --repo OWNER/REPO --id ID [--comment TEXT]

Every issue carries a hidden marker `<!-- seo-id: ID -->` in its body: upsert finds it again instead of opening a
duplicate. Output is JSON on stdout. Requires gh, signed in (`gh auth status`); a board needs the `project` scope.
"""

import argparse
import json
import subprocess
import sys

LABELS = {
    "seo": ("0E8A16", "Search engine optimization"),
    "seo:agent": ("43C891", "The SEO agent can do it"),
    "seo:owner": ("FBCA04", "Needs the site owner"),
    "seo:P1": ("B60205", "Blocking: indexing, errors"),
    "seo:P2": ("D93F0B", "Important"),
    "seo:P3": ("C5DEF5", "Polish"),
    "claude:fix": ("7B4DFF", "Fix it now: Claude opens a pull request"),
}


def gh(*args, check=True):
    result = subprocess.run(["gh", *args], capture_output=True, text=True)
    if check and result.returncode != 0:
        raise SystemExit(f"gh {' '.join(args[:3])}…: {result.stderr.strip()}")
    return result.stdout


def marker(seo_id):
    return f"<!-- seo-id: {seo_id} -->"


def find(repo, seo_id):
    """The issue (open or closed) whose body holds the marker, or None."""
    issues = json.loads(gh("issue", "list", "-R", repo, "--state", "all", "--label", "seo", "--limit", "500",
                           "--json", "number,title,state,body,url,labels"))
    for issue in issues:
        if marker(seo_id) in (issue.get("body") or ""):
            return issue
    return None


def add_to_project(args, url):
    if args.project_owner and args.project_number:
        gh("project", "item-add", str(args.project_number), "--owner", args.project_owner, "--url", url)


def cmd_setup(args):
    existing = {label["name"] for label in json.loads(gh("label", "list", "-R", args.repo, "--limit", "200", "--json", "name"))}
    created = []
    for name, (color, description) in LABELS.items():
        if name not in existing:
            gh("label", "create", name, "-R", args.repo, "--color", color, "--description", description)
            created.append(name)
    project = None
    if args.project_owner and args.project_number:
        project = json.loads(gh("project", "view", str(args.project_number), "--owner", args.project_owner, "--format", "json"))
        project = {"title": project.get("title"), "url": project.get("url")}
    return {"labelsCreated": created, "project": project}


def cmd_upsert(args):
    with open(args.body_file, encoding="utf-8") as handle:
        body = handle.read().rstrip()
    if marker(args.id) not in body:
        body += f"\n{marker(args.id)}\n"
    labels = ["seo", f"seo:{args.who}", f"seo:{args.priority}"]
    issue = find(args.repo, args.id)

    if issue is None:
        url = gh("issue", "create", "-R", args.repo, "--title", args.title, "--body", body,
                 *sum((["--label", label] for label in labels), [])).strip()
        add_to_project(args, url)
        return {"action": "created", "url": url}

    number = str(issue["url"].rsplit("/", 1)[-1])
    if issue["state"] == "OPEN":
        old = [label["name"] for label in issue["labels"] if label["name"].startswith("seo:")]
        edit = ["issue", "edit", number, "-R", args.repo, "--title", args.title, "--body", body]
        for label in old:
            if label not in labels:
                edit += ["--remove-label", label]
        for label in labels:
            edit += ["--add-label", label]
        gh(*edit)
        add_to_project(args, issue["url"])
        return {"action": "updated", "url": issue["url"]}

    # Closed but found again: the problem is back.
    gh("issue", "reopen", number, "-R", args.repo)
    gh("issue", "comment", number, "-R", args.repo, "--body", "The problem is back.\n\n" + body)
    return {"action": "reopened", "url": issue["url"]}


def cmd_list(args):
    state = {"open": "open", "closed": "closed", "all": "all"}[args.state]
    command = ["issue", "list", "-R", args.repo, "--state", state, "--label", "seo", "--limit", "500",
               "--json", "number,title,state,url,labels,createdAt,closedAt,body"]
    if args.who:
        command += ["--label", f"seo:{args.who}"]
    items = []
    for issue in json.loads(gh(*command)):
        body = issue.pop("body") or ""
        seo_id = body.split("<!-- seo-id: ", 1)[1].split(" -->", 1)[0] if "<!-- seo-id: " in body else None
        names = [label["name"] for label in issue.pop("labels")]
        priority = next((n.split(":")[1] for n in names if n in ("seo:P1", "seo:P2", "seo:P3")), None)
        who = "owner" if "seo:owner" in names else "agent" if "seo:agent" in names else None
        items.append({**issue, "id": seo_id, "priority": priority, "who": who})
    items.sort(key=lambda i: (i["priority"] or "P9", i["createdAt"]))
    return items


def cmd_close(args):
    issue = find(args.repo, args.id)
    if issue is None or issue["state"] != "OPEN":
        return {"action": "none", "reason": "no open issue with this id"}
    number = issue["url"].rsplit("/", 1)[-1]
    if args.comment:
        gh("issue", "comment", number, "-R", args.repo, "--body", args.comment)
    gh("issue", "close", number, "-R", args.repo)
    return {"action": "closed", "url": issue["url"]}


def main():
    parser = argparse.ArgumentParser(description="SEO actions as GitHub issues.")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("setup", "upsert", "list", "close"):
        p = sub.add_parser(name)
        p.add_argument("--repo", required=True)
        if name in ("setup", "upsert"):
            p.add_argument("--project-owner")
            p.add_argument("--project-number", type=int)
        if name in ("upsert", "close"):
            p.add_argument("--id", required=True)
    up = sub.choices["upsert"]
    up.add_argument("--title", required=True)
    up.add_argument("--who", choices=("agent", "owner"), required=True)
    up.add_argument("--priority", choices=("P1", "P2", "P3"), required=True)
    up.add_argument("--body-file", required=True)
    ls = sub.choices["list"]
    ls.add_argument("--who", choices=("agent", "owner"))
    ls.add_argument("--state", choices=("open", "closed", "all"), default="open")
    sub.choices["close"].add_argument("--comment")

    args = parser.parse_args()
    handler = {"setup": cmd_setup, "upsert": cmd_upsert, "list": cmd_list, "close": cmd_close}[args.command]
    json.dump(handler(args), sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
