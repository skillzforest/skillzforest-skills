#!/usr/bin/env python3
"""Check a growth profile (projects/<id>/growth.json) against references/profile.md.

Usage:
    python3 validate_growth_profile.py path/to/growth.json [more.json ...]

Prints one line per problem; exits 1 when any file has an error. Standard library only.
"""

import json
import os
import re
import sys

SLUG = re.compile(r"^[a-z][a-z0-9-]*$")
LANG = re.compile(r"^[a-z]{2}$")
REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
STATUS = {"draft", "validated"}
MODELS = {"b2b", "b2c", "b2b2c", "community", "marketplace"}
STAGES = {"prelaunch", "launched", "growing"}
HORIZONS = {"30d", "90d"}
BASIS = {"site", "seo-profile", "owner", "data", "hypothesis"}
KINDS = {"customer", "user", "partner", "prescriber", "publisher"}
ACCOUNT_STATUS = {"active", "to-create", "paused", "unknown"}
POSTHOG_VIA = {"mcp", "composio", "none"}
SC_VIA = {"composio", "none"}
SENDER_CHANNELS = {"gmail", "manual"}
CRM_TYPES = {"hubspot", "none"}


def check(path):
    problems = []

    def err(where, msg):
        problems.append(f"error   {path}: {where}: {msg}")

    def warn(where, msg):
        problems.append(f"warning {path}: {where}: {msg}")

    try:
        with open(path, encoding="utf-8") as fh:
            p = json.load(fh)
    except (OSError, ValueError) as exc:
        err("file", f"unreadable JSON ({exc})")
        return problems

    def need(key, kind, obj=None, where=None):
        obj = p if obj is None else obj
        where = where or key
        if key not in obj or obj[key] in (None, ""):
            err(where, "missing")
            return None
        if not isinstance(obj[key], kind):
            err(where, f"expected {kind.__name__}")
            return None
        return obj[key]

    if p.get("schemaVersion") != 1:
        err("schemaVersion", "must be 1")
    pid = need("id", str)
    if pid and not SLUG.match(pid):
        err("id", "lower-case slug expected")
    folder = os.path.basename(os.path.dirname(os.path.abspath(path)))
    if pid and folder not in ("", pid) and folder != "templates":
        err("id", f"'{pid}' does not match its folder '{folder}'")
    need("name", str)
    if need("status", str) and p["status"] not in STATUS:
        err("status", f"one of {sorted(STATUS)}")
    if need("reportLanguage", str) and not LANG.match(p["reportLanguage"]):
        err("reportLanguage", "two-letter code expected")

    site = need("site", dict) or {}
    if site:
        need("url", str, site, "site.url")
        langs = need("languages", list, site, "site.languages") or []
        for lang in langs:
            if not isinstance(lang, str) or not LANG.match(lang):
                err("site.languages", f"bad language code {lang!r}")

    seo = p.get("seoProfile")
    if seo is not None:
        if not isinstance(seo, dict) or not REPO.match(str(seo.get("repo", ""))) or not seo.get("path"):
            err("seoProfile", "expected {repo: owner/name, path}")
    else:
        need("pitch", str)
        need("business", str)

    model = need("model", str)
    if model and model not in MODELS:
        err("model", f"one of {sorted(MODELS)}")
    if need("stage", str) and p["stage"] not in STAGES:
        err("stage", f"one of {sorted(STAGES)}")

    def items(key, required_fields, enums):
        lst = need(key, list) or []
        if not lst:
            err(key, "at least one item")
        ids = set()
        for i, it in enumerate(lst):
            where = f"{key}[{i}]"
            if not isinstance(it, dict):
                err(where, "object expected")
                continue
            for field in required_fields:
                if it.get(field) in (None, "", []):
                    err(where, f"{field} missing")
            for field, allowed in enums.items():
                if field in it and it[field] not in allowed:
                    err(where, f"{field} must be one of {sorted(allowed)}")
            if it.get("id") in ids:
                err(where, f"duplicate id {it.get('id')}")
            ids.add(it.get("id"))
        return lst, ids

    goals, _ = items("goals", ["id", "horizon", "objective", "metric", "basis"],
                     {"horizon": HORIZONS, "basis": BASIS})
    for i, g in enumerate(goals):
        for field in ("baseline", "target"):
            if field not in g:
                err(f"goals[{i}]", f"{field} missing (use null when not measured or not set)")
            elif g[field] is not None and not isinstance(g[field], (int, float)):
                err(f"goals[{i}]", f"{field} must be a number or null")
        if g.get("target") is None and g.get("basis") == "owner":
            warn(f"goals[{i}]", "owner goal without a target")
    _, audience_ids = items("audiences", ["id", "name", "kind", "description", "basis"],
                            {"kind": KINDS, "basis": BASIS})
    personas, _ = items("personas", ["id", "audience", "name", "role", "job", "basis"], {"basis": BASIS})
    for i, per in enumerate(personas):
        if per.get("audience") and per["audience"] not in audience_ids:
            err(f"personas[{i}]", f"audience '{per['audience']}' is not an audience id")

    if model in ("b2b", "b2b2c"):
        icp = need("icp", dict) or {}
        for field in ("industries", "roles", "signals", "disqualifiers"):
            if not icp.get(field):
                err(f"icp.{field}", "missing")

    channels = need("channels", dict) or {}
    if channels:
        if not channels.get("candidates"):
            err("channels.candidates", "at least one channel")
        for i, ex in enumerate(channels.get("excluded", [])):
            if not isinstance(ex, dict) or not ex.get("id") or not ex.get("reason"):
                err(f"channels.excluded[{i}]", "expected {id, reason}")
        for i, acc in enumerate(channels.get("accounts", [])):
            if not isinstance(acc, dict) or not acc.get("platform"):
                err(f"channels.accounts[{i}]", "platform missing")
            elif acc.get("status") not in ACCOUNT_STATUS:
                err(f"channels.accounts[{i}]", f"status must be one of {sorted(ACCOUNT_STATUS)}")

    out = need("outreach", dict) or {}
    if out:
        if out.get("b2cDirect") is not False:
            err("outreach.b2cDirect", "must be false: no cold message to private individuals")
        if not isinstance(out.get("b2bEmail"), bool):
            err("outreach.b2bEmail", "true or false")
        if model == "b2c" and out.get("b2bEmail"):
            warn("outreach.b2bEmail", "a b2c project prospecting organizations: partners only?")
        for field, default in (("maxNewContactsPerWeek", 15), ("maxFirstMessagesPerWeek", 5)):
            val = out.get(field)
            if not isinstance(val, int) or val < 0:
                err(f"outreach.{field}", f"positive integer expected (default {default})")
            elif val > 30:
                warn(f"outreach.{field}", "above 30 a week is no longer targeted outreach")
        sender = out.get("sender")
        if sender is not None and (not isinstance(sender, dict) or sender.get("channel") not in SENDER_CHANNELS):
            err("outreach.sender", f"null or {{channel: {sorted(SENDER_CHANNELS)}, account, address}}")
        crm = out.get("crm")
        if not isinstance(crm, dict) or crm.get("type") not in CRM_TYPES:
            err("outreach.crm", f"type must be one of {sorted(CRM_TYPES)}")
        elif crm["type"] == "hubspot" and (not crm.get("projectProperty") or not crm.get("value")):
            err("outreach.crm", "hubspot needs projectProperty and value")

    meas = need("measurement", dict) or {}
    if meas:
        ph = meas.get("posthog")
        if not isinstance(ph, dict) or ph.get("via") not in POSTHOG_VIA:
            err("measurement.posthog", f"via must be one of {sorted(POSTHOG_VIA)}")
        elif ph["via"] != "none" and not ph.get("projectId"):
            err("measurement.posthog", "projectId missing")
        sc = meas.get("searchConsole")
        if not isinstance(sc, dict) or sc.get("via") not in SC_VIA:
            err("measurement.searchConsole", f"via must be one of {sorted(SC_VIA)}")
        elif sc["via"] == "composio" and not sc.get("property"):
            err("measurement.searchConsole", "property missing")

    if p.get("status") == "validated" and p.get("openQuestions"):
        warn("openQuestions", "profile validated with open questions left")
    return problems


def main(argv):
    if len(argv) < 2:
        print(__doc__.strip())
        return 2
    failed = False
    for path in argv[1:]:
        problems = check(path)
        for line in problems:
            print(line)
        if any(line.startswith("error") for line in problems):
            failed = True
        elif not problems:
            print(f"ok      {path}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
