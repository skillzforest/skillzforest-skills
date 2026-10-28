#!/usr/bin/env python3
"""Check an SEO profile (.seo/profile.json) against the rules of references/profile.md.

Usage:
    python3 validate_profile.py path/to/profile.json

Prints one line per problem and exits with 1 when there is at least one error, 0 otherwise.
Warnings (missing optional but useful fields) never fail the check. Standard library only.
"""

import json
import re
import sys

LANG = re.compile(r"^[a-z]{2}$")
MODES = {"repo", "advise"}
SC_VIA = {"composio", "gum", "none"}
TRENDS_VIA = {"serpapi", "none"}
CHANNELS = {"gmail", "outlook", "slack", "none"}
WHEN = {"on-change", "every-pass"}
DELIVERABLES = {"google-slides", "xlsx", "markdown"}
TRACKERS = {"github-issues", "jira", "google-sheets"}
PUBLISH = {"repo", "cms", "markdown"}
CMS_TYPES = {"wordpress", "drupal", "contentful", "strapi", "webflow", "ghost", "custom"}
DIGESTS = {"weekly", "every-pass", "none"}

errors = []
warnings = []


def error(path, message):
    errors.append(f"error   {path}: {message}")


def warn(path, message):
    warnings.append(f"warning {path}: {message}")


def get(obj, path):
    """Walk a dotted path; return None when any step is missing."""
    for key in path.split("."):
        if not isinstance(obj, dict) or key not in obj:
            return None
        obj = obj[key]
    return obj


def need(obj, path, kind, allowed=None):
    """Require a field of a given type (and, optionally, one of the allowed values)."""
    value = get(obj, path)
    if value is None:
        error(path, "missing")
        return None
    if not isinstance(value, kind) or isinstance(value, bool) and kind is int:
        error(path, f"expected {kind.__name__}")
        return None
    if isinstance(value, str) and not value.strip():
        error(path, "empty")
        return None
    if allowed is not None and value not in allowed:
        error(path, f"must be one of {', '.join(sorted(allowed))}")
    return value


def check(profile):
    need(profile, "schemaVersion", int)

    # Site
    url = need(profile, "site.url", str)
    if url and not re.match(r"^https?://[^/]+/$", url):
        error("site.url", "expected the home page with a trailing slash, e.g. https://example.com/")
    for field in ("name", "pitch", "audience", "business"):
        need(profile, f"site.{field}", str)

    # Languages
    default = need(profile, "languages.default", str)
    langs = need(profile, "languages.list", list) or []
    codes = []
    for i, lang in enumerate(langs):
        code = need(lang, "code", str)
        if code and not LANG.match(code):
            error(f"languages.list[{i}].code", "expected an ISO 639-1 code such as en")
        prefix = need(lang, "pathPrefix", str)
        if prefix and not (prefix.startswith("/") and prefix.endswith("/")):
            error(f"languages.list[{i}].pathPrefix", "expected a path such as / or /en/")
        if not get(lang, "voice"):
            warn(f"languages.list[{i}].voice", "missing: the agent will guess how to address readers")
        codes.append(code)
    if default and default not in codes:
        error("languages.default", "not in languages.list")

    # Facts
    files = get(profile, "facts.files") or []
    urls = get(profile, "facts.urls") or []
    if not files and not urls:
        error("facts", "give at least one file or URL holding the product's facts")

    # Topics
    targets = need(profile, "topics.target", list) or []
    if not targets:
        error("topics.target", "at least one theme")
    for i, target in enumerate(targets):
        need(target, "theme", str)
        seeds = need(target, "seeds", dict) or {}
        for code in codes:
            if code and not seeds.get(code):
                warn(f"topics.target[{i}].seeds.{code}", "no search beginnings for this language")
    if not get(profile, "topics.exclude"):
        warn("topics.exclude", "empty: are there really no searches to avoid?")

    # Style
    report = need(profile, "style.reportLanguage", str)
    if report and not LANG.match(report):
        error("style.reportLanguage", "expected an ISO 639-1 code")

    # Mode
    mode = need(profile, "mode", str, MODES)
    if mode == "repo":
        repo_url = need(profile, "repo.url", str)
        if repo_url and not re.match(r"^https://github\.com/[^/]+/[^/]+$", repo_url):
            warn("repo.url", "not a github.com repository: pull requests may need another tool")
        need(profile, "repo.baseBranch", str)
        need(profile, "repo.branchPrefix", str)
        if get(profile, "repo.pushToBaseDeploys") is None:
            error("repo.pushToBaseDeploys", "missing: say whether a push to the base branch deploys the site")
        if get(profile, "repo.check") is None:
            warn("repo.check", "no check command: changes will not be built before the pull request")
        pages = need(profile, "repo.pages", list) or []
        if not pages:
            error("repo.pages", "at least the home page")
        for i, page in enumerate(pages):
            if not isinstance(page, dict):
                error(f"repo.pages[{i}]", "expected an object")
                continue
            for field in ("name", "url", "file", "fields"):
                if not isinstance(page.get(field), str) or not page[field].strip():
                    error(f"repo.pages[{i}].{field}", "missing")
        if get(profile, "repo.blog"):
            for field in ("dir", "format", "urlPattern"):
                need(profile, f"repo.blog.{field}", str)
        if not get(profile, "repo.protected"):
            warn("repo.protected", "empty: nothing is off limits to the agent")
    elif mode == "advise":
        need(profile, "advise.cms", str)
        deliverable = get(profile, "advise.deliverable") or "google-slides"
        if deliverable not in DELIVERABLES:
            error("advise.deliverable", f"must be one of {', '.join(sorted(DELIVERABLES))}")
        if not urls:
            error("facts.urls", "required in advise mode: the agent only sees the live site")

    # Sources
    via = need(profile, "sources.searchConsole.via", str, SC_VIA)
    if via and via != "none":
        prop = need(profile, "sources.searchConsole.property", str)
        if prop and not (prop.startswith("sc-domain:") or re.match(r"^https?://.+/$", prop)):
            error("sources.searchConsole.property", "expected sc-domain:example.com or https://example.com/")
    elif via == "none":
        warn("sources.searchConsole", "no Search Console: the agent only knows public demand, not the site's own")
    trends = need(profile, "sources.trends.via", str, TRENDS_VIA)
    if trends == "serpapi":
        calls = need(profile, "sources.trends.maxCallsPerPass", int)
        if calls is not None and not 0 < calls <= 20:
            error("sources.trends.maxCallsPerPass", "between 1 and 20")

    # Cadence
    need(profile, "cadence.schedule", str)
    for field, low in (("articleEveryDays", 1), ("pageCooldownDays", 7), ("maxActionsPerPass", 1)):
        value = need(profile, f"cadence.{field}", int)
        if value is not None and value < low:
            error(f"cadence.{field}", f"at least {low}")
    if get(profile, "cadence.articlesPerWeek") is not None:
        warn("cadence.articlesPerWeek", "moved to content.perWeek (skf-seo-content-audit)")

    # Content plan (optional)
    if get(profile, "content") is not None:
        for field, low, high in (("articles", 1, 100), ("perWeek", 1, 3)):
            value = need(profile, f"content.{field}", int)
            if value is not None and not low <= value <= high:
                error(f"content.{field}", f"between {low} and {high}")
        need(profile, "content.schedule", str)
        publish = need(profile, "content.publish", str, PUBLISH)
        if publish == "repo" and get(profile, "mode") != "repo":
            error("content.publish", "repo needs mode repo")
        if publish == "repo" and not get(profile, "repo.blog"):
            warn("repo.blog", "no blog yet: the plan's first article ticket creates the blog section")
        if publish == "cms":
            need(profile, "content.cms.type", str, CMS_TYPES)
            need(profile, "content.cms.baseUrl", str)
            token = need(profile, "content.cms.tokenEnv", str)
            if token and not re.match(r"^[A-Z][A-Z0-9_]*$", token):
                error("content.cms.tokenEnv", "the NAME of an environment variable (UPPER_CASE), never the credential")
            if get(profile, "content.cms.type") == "custom" and not get(profile, "content.cms.options.create"):
                error("content.cms.options.create", "a custom API needs the endpoint that creates a draft")
        pending = get(profile, "content.maxPending")
        if pending is not None and (not isinstance(pending, int) or pending < 1):
            error("content.maxPending", "at least 1")

    # Notification
    channel = need(profile, "notify.channel", str, CHANNELS)
    if channel and channel != "none":
        need(profile, "notify.to", str)
    when = get(profile, "notify.when")
    if when is not None and when not in WHEN:
        error("notify.when", f"must be one of {', '.join(sorted(WHEN))}")

    # Tracker
    tracker = need(profile, "tracker.type", str, TRACKERS)
    if tracker == "github-issues":
        repo = need(profile, "tracker.repo", str)
        if repo and not re.match(r"^[^/\s]+/[^/\s]+$", repo):
            error("tracker.repo", "expected owner/repo")
        if get(profile, "tracker.projectNumber") is None:
            warn("tracker.projectNumber", "no board: issues only")
    elif tracker == "jira":
        need(profile, "tracker.jiraSite", str)
        need(profile, "tracker.jiraProject", str)
    elif tracker == "google-sheets":
        if not get(profile, "tracker.sheetId"):
            warn("tracker.sheetId", "not created yet: skf-seo-setup creates the sheet")
    digest = get(profile, "tracker.digest")
    if digest is not None and digest not in DIGESTS:
        error("tracker.digest", f"must be one of {', '.join(sorted(DIGESTS))}")
    if tracker and get(profile, "notify.channel") == "none":
        warn("notify.channel", "none: the owner will never be told about the actions waiting for them")

    # Paths
    for field in ("journal", "reports"):
        need(profile, f"paths.{field}", str)


def main():
    if len(sys.argv) != 2:
        print("Usage: validate_profile.py path/to/profile.json", file=sys.stderr)
        return 2
    try:
        with open(sys.argv[1], encoding="utf-8") as handle:
            profile = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error   {sys.argv[1]}: {exc}")
        return 1
    check(profile)
    for line in errors + warnings:
        print(line)
    print(f"{len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
