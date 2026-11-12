#!/usr/bin/env python3
"""Helpers for the growth tracker: issue bodies, fingerprints, GraphQL documents, decisions.

The script never calls GitHub: it prints what to send, so it works the same in a local terminal and in a cloud run
where GitHub is reached through MCP or Composio tools. Standard library only.

Usage:
    growth_issue.py body --fields fields.json                 Markdown body (decision layout when fields has "recommendation")
    growth_issue.py fingerprint TYPE PROJECT TEXT             growth-id from free text (slugified)
    growth_issue.py find --issues issues.json --id GROWTH_ID  matching issue as JSON, or {"match": null}
    growth_issue.py create --board board.json --title T --body-file B --labels a,b
                                                              createIssue GraphQL document (JSON {"query": ...})
    growth_issue.py add --board board.json --content-id ID    addProjectV2ItemById document
    growth_issue.py fields --board board.json --item ITEM_ID --set "Field=Value" [--set ...]
                                                              one document setting every field, in order
    growth_issue.py decision --comments comments.json --owner LOGIN
                                                              latest owner decision as JSON, or {"decision": null}
    growth_issue.py selftest
"""

import argparse
import json
import re
import sys
import unicodedata

MARKER = re.compile(r"<!--\s*growth-id:\s*([a-z0-9:._-]+)\s*-->")
TYPES = {"opportunity", "channel", "campaign", "content", "publication", "media", "prospect", "decision",
         "result", "daily"}
DECISIONS = {
    "APPROUVER": "APPROVE", "APPROVE": "APPROVE",
    "MODIFIER": "CHANGE", "CHANGE": "CHANGE",
    "REPORTER": "POSTPONE", "POSTPONE": "POSTPONE",
    "REFUSER": "REJECT", "REJECT": "REJECT",
}
DECISION_RE = re.compile(r"^\s*\**\s*(APPROUVER|APPROVE|MODIFIER|CHANGE|REPORTER|POSTPONE|REFUSER|REJECT)\b\s*\**\s*[:\-]?\s*(.*)",
                         re.IGNORECASE | re.DOTALL)
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

DECISION_LABELS_FR = [
    ("project", "Projet"), ("opportunity", "Opportunité"), ("target", "Canal ou cible"),
    ("outcome", "Résultat visé"), ("rationale", "Justification"), ("sources", "Sources"),
    ("effort", "Effort"), ("confidence", "Confiance"), ("risks", "Risques"),
    ("recommendation", "Recommandation"), ("deliverable", "Livrable"),
]
DECISION_LABELS_EN = [
    ("project", "Project"), ("opportunity", "Opportunity"), ("target", "Channel or target"),
    ("outcome", "Expected outcome"), ("rationale", "Rationale"), ("sources", "Sources"),
    ("effort", "Effort"), ("confidence", "Confidence"), ("risks", "Risks"),
    ("recommendation", "Recommendation"), ("deliverable", "Deliverable"),
]


def slugify(text, limit=60):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return text[:limit].rstrip("-") or "item"


def fingerprint(kind, project, text):
    if kind not in TYPES:
        raise SystemExit(f"type must be one of {sorted(TYPES)}")
    return f"{kind}:{slugify(project)}:{slugify(text)}"


def gql_string(value):
    return json.dumps(value, ensure_ascii=False)


def build_body(fields):
    lang = fields.get("language", "fr")
    gid = fields.get("growthId")
    if not gid or not MARKER.match(f"<!-- growth-id: {gid} -->"):
        raise SystemExit("fields.growthId missing or invalid")
    lines = []
    if "recommendation" in fields:
        labels = DECISION_LABELS_FR if lang == "fr" else DECISION_LABELS_EN
        for key, label in labels:
            value = fields.get(key)
            if value in (None, "", []):
                value = "non renseigné" if lang == "fr" else "not given"
            if isinstance(value, list):
                value = "\n" + "\n".join(f"- {v}" for v in value)
            lines.append(f"**{label}** : {value}" if lang == "fr" else f"**{label}**: {value}")
        lines.append("")
        lines.append("Répondre : APPROUVER · MODIFIER : … · REPORTER : … · REFUSER : …" if lang == "fr"
                     else "Reply: APPROVE · CHANGE: … · POSTPONE: … · REJECT: …")
    else:
        lines.append(fields.get("text", "").strip())
        if fields.get("sources"):
            lines.append("")
            lines.append("**Sources**" + (" :" if lang == "fr" else ":"))
            lines.extend(f"- {s}" for s in fields["sources"])
    lines.append("")
    lines.append(f"<!-- growth-id: {gid} -->")
    return "\n".join(lines).strip() + "\n"


def load_issues(path):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, dict):
        for key in ("issues", "items", "nodes", "data"):
            if isinstance(data.get(key), list):
                return data[key]
    return data if isinstance(data, list) else []


def find(issues, gid):
    for issue in issues:
        found = MARKER.findall(issue.get("body") or "")
        if gid in found:
            return {"match": {k: issue.get(k) for k in ("number", "id", "title", "state", "state_reason", "labels",
                                                          "html_url", "url") if k in issue}}
    return {"match": None}


def board_load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def create_doc(board, title, body, labels):
    label_ids = []
    for name in labels:
        if name not in board["labels"]:
            raise SystemExit(f"unknown label {name!r}: add it to the repository and to board.json")
        label_ids.append(board["labels"][name])
    query = ("mutation { createIssue(input:{repositoryId:%s, title:%s, body:%s, labelIds:%s}) "
             "{ issue { id number url } } }") % (gql_string(board["repository"]["id"]), gql_string(title),
                                                  gql_string(body), json.dumps(label_ids))
    return {"query": query}


def add_doc(board, content_id):
    query = ("mutation { addProjectV2ItemById(input:{projectId:%s, contentId:%s}) { item { id } } }"
             % (gql_string(board["project"]["id"]), gql_string(content_id)))
    return {"query": query}


def fields_doc(board, item_id, assignments):
    parts = []
    for i, assignment in enumerate(assignments):
        if "=" not in assignment:
            raise SystemExit(f"--set expects Field=Value, got {assignment!r}")
        name, value = assignment.split("=", 1)
        aliases = board.get("aliases", {})
        name = aliases.get("fields", {}).get(name, name)
        value = aliases.get("options", {}).get(name, {}).get(value, value)
        field = board["fields"].get(name)
        if not field:
            raise SystemExit(f"unknown field {name!r} (board.json has {sorted(board['fields'])})")
        if "options" in field:
            if value not in field["options"]:
                raise SystemExit(f"{name}: unknown option {value!r} (options: {sorted(field['options'])})")
            val = "{singleSelectOptionId:%s}" % gql_string(field["options"][value])
        elif field.get("type") == "date":
            if not DATE.match(value):
                raise SystemExit(f"{name}: date YYYY-MM-DD expected")
            val = "{date:%s}" % gql_string(value)
        elif field.get("type") == "number":
            val = "{number:%s}" % float(value)
        else:
            val = "{text:%s}" % gql_string(value)
        parts.append("f%d: updateProjectV2ItemFieldValue(input:{projectId:%s, itemId:%s, fieldId:%s, value:%s}) "
                     "{ projectV2Item { id } }" % (i, gql_string(board["project"]["id"]), gql_string(item_id),
                                                    gql_string(field["id"]), val))
    return {"query": "mutation { " + " ".join(parts) + " }"}


BOT_MARK = "<!-- growth-bot -->"


def author_of(comment):
    user = comment.get("user") or comment.get("author") or {}
    if isinstance(user, dict):
        return user.get("login") or user.get("name")
    return user


def decision(comments, owner):
    def when(c):
        return c.get("created_at") or c.get("createdAt") or ""
    for comment in sorted(comments, key=when, reverse=True):
        if (author_of(comment) or "").lower() != owner.lower():
            continue
        if BOT_MARK in (comment.get("body") or ""):
            continue
        match = DECISION_RE.match(comment.get("body") or "")
        if match:
            return {"decision": DECISIONS[match.group(1).upper()], "word": match.group(1).upper(),
                    "note": match.group(2).strip(), "comment": comment.get("id"), "at": when(comment)}
    return {"decision": None}


def selftest():
    assert slugify("Retro Dodo (média)") == "retro-dodo-media"
    gid = fingerprint("media", "romkade", "Retro Dodo")
    assert gid == "media:romkade:retro-dodo", gid
    body = build_body({"growthId": gid, "project": "ROMKADE", "opportunity": "x", "recommendation": "y"})
    assert body.rstrip().endswith("<!-- growth-id: media:romkade:retro-dodo -->")
    issues = [{"number": 3, "state": "CLOSED", "body": "a\n<!-- growth-id: media:romkade:retro-dodo -->"}]
    assert find(issues, gid)["match"]["number"] == 3
    assert find(issues, "media:romkade:other")["match"] is None
    comments = [
        {"user": {"login": "someone"}, "body": "APPROUVER", "created_at": "2026-11-09T10:00:00Z"},
        {"user": {"login": "owner"}, "body": "REPORTER : après le salon", "created_at": "2026-11-08T10:00:00Z"},
        {"user": {"login": "owner"}, "body": "Merci", "created_at": "2026-11-09T11:00:00Z"},
        {"user": {"login": "owner"}, "body": "APPROUVER pour envoi ?\n<!-- growth-bot -->", "created_at": "2026-11-09T12:00:00Z"},
    ]
    got = decision(comments, "owner")
    assert got["decision"] == "POSTPONE" and got["note"] == "après le salon", got
    assert decision(comments, "nobody")["decision"] is None
    board = {"project": {"id": "P"}, "repository": {"id": "R"}, "labels": {"growth": "L1"},
             "fields": {"Status": {"id": "F1", "options": {"Décision": "o1"}}, "Score": {"id": "F2", "type": "number"},
                        "Échéance": {"id": "F3", "type": "date"}}}
    doc = fields_doc(board, "I", ["Status=Décision", "Score=42", "Échéance=2026-11-15"])["query"]
    assert "singleSelectOptionId:\"o1\"" in doc and "number:42.0" in doc and "date:\"2026-11-15\"" in doc
    assert "labelIds:[\"L1\"]" in create_doc(board, "t", "b", ["growth"])["query"]
    board["aliases"] = {"fields": {"Due": "Échéance"}, "options": {"Status": {"Decision": "Décision"}}}
    doc = fields_doc(board, "I", ["Status=Decision", "Due=2026-11-15"])["query"]
    assert "singleSelectOptionId:\"o1\"" in doc and "fieldId:\"F3\"" in doc
    print("selftest ok")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("body"); p.add_argument("--fields", required=True)
    p = sub.add_parser("fingerprint"); p.add_argument("type"); p.add_argument("project"); p.add_argument("text")
    p = sub.add_parser("find"); p.add_argument("--issues", required=True); p.add_argument("--id", required=True)
    p = sub.add_parser("create"); p.add_argument("--board", required=True); p.add_argument("--title", required=True)
    p.add_argument("--body-file", required=True); p.add_argument("--labels", default="")
    p = sub.add_parser("add"); p.add_argument("--board", required=True); p.add_argument("--content-id", required=True)
    p = sub.add_parser("fields"); p.add_argument("--board", required=True); p.add_argument("--item", required=True)
    p.add_argument("--set", action="append", default=[])
    p = sub.add_parser("decision"); p.add_argument("--comments", required=True); p.add_argument("--owner", required=True)
    sub.add_parser("selftest")
    args = parser.parse_args()

    if args.cmd == "body":
        with open(args.fields, encoding="utf-8") as fh:
            sys.stdout.write(build_body(json.load(fh)))
    elif args.cmd == "fingerprint":
        print(fingerprint(args.type, args.project, args.text))
    elif args.cmd == "find":
        print(json.dumps(find(load_issues(args.issues), args.id), ensure_ascii=False))
    elif args.cmd == "create":
        with open(args.body_file, encoding="utf-8") as fh:
            body = fh.read()
        labels = [l.strip() for l in args.labels.split(",") if l.strip()]
        print(json.dumps(create_doc(board_load(args.board), args.title, body, labels), ensure_ascii=False))
    elif args.cmd == "add":
        print(json.dumps(add_doc(board_load(args.board), args.content_id), ensure_ascii=False))
    elif args.cmd == "fields":
        print(json.dumps(fields_doc(board_load(args.board), args.item, args.set), ensure_ascii=False))
    elif args.cmd == "decision":
        with open(args.comments, encoding="utf-8") as fh:
            data = json.load(fh)
        comments = data.get("comments", data) if isinstance(data, dict) else data
        print(json.dumps(decision(comments, args.owner), ensure_ascii=False))
    else:
        selftest()


if __name__ == "__main__":
    main()
