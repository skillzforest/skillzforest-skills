#!/usr/bin/env python3
"""Indexing state of a whole site, and why its pages are not indexed: one tracker action per cause.

Google has no API for the Search Console « Pages » report. This script rebuilds it from the URL Inspection API:
the agent inspects every URL of the sitemap (GOOGLE_SEARCH_CONSOLE_INSPECT_URL with language_code "en-US", or
`gum read searchconsole.urlInspection.index.inspect`) and saves one JSON object per line:

    {"url": "https://example.com/en/roadmap", "result": <inspectionResult, or the whole API response>}

Then:

    python3 indexing.py --crawl crawl.json --inspections inspections.jsonl --site-name "Example" \
        [--protected "public/secteurs/,public/services.html"] [--lang fr|en] [--out indexing.json]

It joins each inspection with the crawl of the same URL (crawl.py: status, title, canonical, robots, internal
links, findings), classifies every URL like the « Pages » report, gives each URL that is not indexed its most
likely cause, and groups the URLs by cause into actions ready for the tracker (id `indexing:<cause>`, who,
priority, title, body). It prints a Markdown summary and writes the JSON. Standard library only.

Causes, in the order they are checked (the first that matches wins):
    (foreign-brand also lists the other brand's pages that Google did index: they go too)
    page-error         the page does not answer 200                                  agent  P1
    noindex            noindex on a page listed in the sitemap                       agent  P1
    canonical          canonical pointing elsewhere, or Google chose another one     agent  P1
    foreign-brand      the page carries another brand than the site                  agent  P2
    duplicate          same title as another page (often a language left untranslated) agent P2
    orphan             no page of the site links to it in the HTML                   agent  P2
    crawled-not-indexed  Google read it and dropped it: content too thin or too close agent P2
    awaiting-crawl     sound page Google has not crawled yet: ask for indexing       owner  P3
A cause covering a fifth of the sitemap or more is raised to P1: it blocks the site, not one page.
"""

import argparse
import collections
import json
import re
import sys
import urllib.parse

SEPARATORS = re.compile(r"\s+[—–|·-]\s+")

CAUSES = ["page-error", "noindex", "canonical", "foreign-brand", "duplicate", "orphan", "crawled-not-indexed",
          "awaiting-crawl"]
WHO = {c: "agent" for c in CAUSES}
WHO["awaiting-crawl"] = "owner"
PRIORITY = {"page-error": "P1", "noindex": "P1", "canonical": "P1", "foreign-brand": "P2", "duplicate": "P2",
            "orphan": "P2", "crawled-not-indexed": "P2", "awaiting-crawl": "P3"}

TEXT = {
    "fr": {
        "states": {"indexed": "indexée", "discovered": "détectée, non indexée", "crawled": "explorée, non indexée",
                   "unknown": "inconnue de Google", "duplicate": "doublon / autre canonique", "noindex": "exclue par noindex",
                   "robots": "bloquée par robots.txt", "error": "erreur (404, 5xx, redirection)", "other": "autre"},
        "title": {
            "page-error": "Corriger ou retirer du sitemap les pages en erreur ({n} pages)",
            "noindex": "Retirer le noindex ou sortir ces pages du sitemap ({n} pages)",
            "canonical": "Corriger les balises canonical de {n} pages",
            "foreign-brand": "Supprimer les pages de la marque {brand} publiées sur ce site ({n} pages)",
            "duplicate": "Traduire ou retirer les pages en doublon ({n} pages)",
            "orphan": "Ajouter des liens HTML vers {n} pages orphelines",
            "crawled-not-indexed": "Étoffer ou retirer {n} pages explorées mais non indexées",
            "awaiting-crawl": "Demander l'indexation de {n} pages dans Search Console",
        },
        "why": {
            "page-error": "Google ne peut pas indexer une page qui ne répond pas, et un sitemap qui en contient perd sa confiance.",
            "noindex": "Le sitemap demande l'indexation et la page la refuse : Google ignore les deux signaux.",
            "canonical": "Google indexe l'autre URL à la place de celle-ci.",
            "foreign-brand": "Des pages d'une autre marque diluent le sujet du site et Google les explore en dernier.",
            "duplicate": "Google n'indexe qu'une page par contenu identique ; les autres restent « détectées ».",
            "orphan": "Sans lien dans le HTML, Google découvre ces pages par le seul sitemap et ne les explore pas.",
            "crawled-not-indexed": "Google a jugé ces pages trop proches d'autres ou trop pauvres pour les garder.",
            "awaiting-crawl": "Les pages sont saines mais Google ne les a pas encore explorées.",
        },
        "fix": {
            "page-error": "Rétablir chaque page, ou la retirer du sitemap, des routes et des liens si elle ne doit plus exister.",
            "noindex": "Pour chaque page : retirer le noindex si elle doit être trouvée, sinon la retirer du sitemap et des hreflang.",
            "canonical": "Faire pointer la canonical de chaque page vers elle-même (ou retirer du sitemap la page qui n'est qu'une copie).",
            "foreign-brand": "Supprimer ces pages du site : fichiers, routes, sitemap, hreflang et liens internes (une page supprimée répond 410 ou 404). Si leurs fichiers sont dans repo.protected, l'issue passe à owner : ajouter claude:fix pour que la tâche de correction le fasse.",
            "duplicate": "Traduire les versions restées dans une autre langue, ou ne garder qu'une version et retirer les autres du sitemap, des hreflang et des routes.",
            "orphan": "Ajouter des liens en dur dans le HTML des gabarits (menu, pied de page, listes) vers ces pages, ou les retirer du sitemap si elles n'ont pas lieu d'être.",
            "crawled-not-indexed": "Pour chaque page : l'étoffer pour qu'elle réponde à une recherche précise, la fusionner avec une page proche, ou la retirer du sitemap.",
            "awaiting-crawl": "Search Console > Inspection de l'URL > « Demander une indexation », au plus 10 par jour, dans l'ordre de la liste.",
        },
        "check_removed": "Ces URL ne sont plus dans le sitemap et répondent 404 ou 410 ; aucun lien du site n'y mène.",
        "check": "La passe suivante inspecte à nouveau ces URL : leur statut devient « indexée » (compter 1 à 3 semaines après le déploiement).",
        "problem": "{n} URL du sitemap ne sont pas indexées pour cette raison (inspection du {date}).",
        "summary": "Indexation : {indexed}/{total} pages indexées",
    },
    "en": {
        "states": {"indexed": "indexed", "discovered": "discovered, not indexed", "crawled": "crawled, not indexed",
                   "unknown": "unknown to Google", "duplicate": "duplicate / other canonical", "noindex": "excluded by noindex",
                   "robots": "blocked by robots.txt", "error": "error (404, 5xx, redirect)", "other": "other"},
        "title": {
            "page-error": "Fix or remove from the sitemap the pages in error ({n} pages)",
            "noindex": "Remove noindex or take these pages out of the sitemap ({n} pages)",
            "canonical": "Fix the canonical tags of {n} pages",
            "foreign-brand": "Remove the {brand} pages published on this site ({n} pages)",
            "duplicate": "Translate or remove the duplicate pages ({n} pages)",
            "orphan": "Add HTML links to {n} orphan pages",
            "crawled-not-indexed": "Enrich or remove {n} pages crawled but not indexed",
            "awaiting-crawl": "Request indexing of {n} pages in Search Console",
        },
        "why": {
            "page-error": "Google cannot index a page that does not answer, and a sitemap full of them loses its trust.",
            "noindex": "The sitemap asks for indexing and the page refuses it: Google ignores both.",
            "canonical": "Google indexes the other URL instead of this one.",
            "foreign-brand": "Pages of another brand blur what the site is about and Google crawls them last.",
            "duplicate": "Google indexes one page per identical content; the others stay « discovered ».",
            "orphan": "Without an HTML link, Google only knows these pages from the sitemap and does not crawl them.",
            "crawled-not-indexed": "Google found these pages too close to others or too thin to keep.",
            "awaiting-crawl": "The pages are sound but Google has not crawled them yet.",
        },
        "fix": {
            "page-error": "Restore each page, or remove it from the sitemap, the routes and the links if it should no longer exist.",
            "noindex": "For each page: remove noindex if it should be found, otherwise take it out of the sitemap and hreflang.",
            "canonical": "Point each page's canonical to itself (or take out of the sitemap the page that is only a copy).",
            "foreign-brand": "Delete these pages from the site: files, routes, sitemap, hreflang and internal links (a deleted page answers 410 or 404). When their files are in repo.protected, the issue goes to the owner: add claude:fix so the fix task does it.",
            "duplicate": "Translate the versions left in another language, or keep one version and take the others out of the sitemap, hreflang and routes.",
            "orphan": "Add plain HTML links in the templates (menu, footer, lists) to these pages, or take them out of the sitemap if they have no reason to exist.",
            "crawled-not-indexed": "For each page: enrich it so it answers one precise search, merge it with a close page, or take it out of the sitemap.",
            "awaiting-crawl": "Search Console > URL inspection > « Request indexing », 10 a day at most, in the order of the list.",
        },
        "check_removed": "These URLs are out of the sitemap and answer 404 or 410; no link of the site leads to them.",
        "check": "The next pass inspects these URLs again: their state becomes « indexed » (allow 1 to 3 weeks after deployment).",
        "problem": "{n} sitemap URLs are not indexed for this reason (inspection of {date}).",
        "summary": "Indexing: {indexed}/{total} pages indexed",
    },
}


def normalize(url):
    parts = urllib.parse.urlsplit(url.strip())
    path = parts.path.rstrip("/") or "/"
    return f"{parts.scheme.lower()}://{parts.netloc.lower()}{path}"


def squash(text):
    return re.sub(r"[^a-z0-9]", "", (text or "").lower())


def inspection(record):
    result = record.get("result") or record
    for key in ("data", "inspectionResult"):
        if isinstance(result, dict) and key in result:
            result = result[key]
    return (result or {}).get("indexStatusResult", {}) if isinstance(result, dict) else {}


def state_of(status):
    text = (status.get("coverageState") or "").lower()
    if status.get("verdict") == "PASS" or "indexed" in text and "not indexed" not in text or "indexée" in text and "non indexée" not in text:
        return "indexed"
    if "discovered" in text or "détectée" in text:
        return "discovered"
    if "crawled" in text or "explorée" in text:
        return "crawled"
    if "unknown" in text or "ne reconnaît pas" in text:
        return "unknown"
    if "duplicate" in text or "canonical" in text or "doublon" in text or "canonique" in text:
        return "duplicate"
    if "noindex" in text:
        return "noindex"
    if "robots" in text:
        return "robots"
    if any(k in text for k in ("404", "5xx", "soft", "redirect", "redirection", "server", "erreur", "error")):
        return "error"
    return "other"


def brand_of(title):
    parts = SEPARATORS.split(title or "")
    if len(parts) < 2:
        return None
    last = parts[-1].strip()
    return last if 0 < len(last.split()) <= 3 else None


def main():
    parser = argparse.ArgumentParser(description="Indexing state of a site and one action per cause.")
    parser.add_argument("--crawl", required=True, help="crawl.json from crawl.py (full sitemap, not sampled)")
    parser.add_argument("--inspections", required=True, help="JSON lines: {url, result} per sitemap URL")
    parser.add_argument("--site-name", required=True, help="site.name of the profile")
    parser.add_argument("--protected", default="", help="comma-separated repo.protected paths (informative)")
    parser.add_argument("--lang", default="fr", choices=sorted(TEXT))
    parser.add_argument("--date", default="")
    parser.add_argument("--out", default="indexing.json")
    args = parser.parse_args()
    t = TEXT[args.lang]

    with open(args.crawl, encoding="utf-8") as handle:
        crawl = json.load(handle)
    pages = {normalize(p["url"]): p for p in crawl.get("pages", [])}
    findings = collections.defaultdict(set)
    for f in crawl.get("findings", []):
        findings[normalize(f["page"])].add(f["rule"])
    titles = collections.Counter(p.get("title") for p in pages.values() if p.get("status") == 200 and p.get("title"))
    site_key = squash(args.site_name)

    rows = []
    with open(args.inspections, encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                record = json.loads(line)
                rows.append((record["url"], inspection(record)))

    states = collections.Counter()
    groups = collections.defaultdict(list)
    brands = collections.Counter()
    for url, status in rows:
        state = state_of(status)
        states[state] += 1
        if state == "indexed":
            continue
        key = normalize(url)
        page = pages.get(key, {})
        rules = findings.get(key, set())
        title = page.get("title") or ""
        brand = brand_of(title)
        user_canonical, google_canonical = status.get("userCanonical"), status.get("googleCanonical")
        if page and page.get("status") not in (200, None) or state in ("error",) or "page-error" in rules:
            cause = "page-error"
        elif state == "noindex" or "noindex-in-sitemap" in rules:
            cause = "noindex"
        elif "canonical-elsewhere" in rules or (google_canonical and user_canonical and normalize(google_canonical) != normalize(user_canonical)):
            cause = "canonical"
        elif brand and squash(brand) != site_key and site_key not in squash(title):
            cause = "foreign-brand"
            brands[brand] += 1
        elif title and titles[title] > 1 or state == "duplicate":
            cause = "duplicate"
        elif "orphan-page" in rules:
            cause = "orphan"
        elif state == "crawled":
            cause = "crawled-not-indexed"
        else:
            cause = "awaiting-crawl"
        groups[cause].append({"url": url, "state": state, "coverage": status.get("coverageState"),
                              "lastCrawl": status.get("lastCrawlTime"), "title": title})

    # Another brand's pages go, even when Google indexed them: the site should not carry them at all.
    listed = {normalize(u["url"]) for u in groups.get("foreign-brand", [])}
    inspected = {normalize(url): state_of(status) for url, status in rows}
    for key, page in pages.items():
        title = page.get("title") or ""
        brand = brand_of(title)
        if page.get("status") == 200 and key not in listed and brand and squash(brand) != site_key and site_key not in squash(title):
            brands[brand] += 1
            groups["foreign-brand"].append({"url": page["url"], "state": inspected.get(key, "other"),
                                            "coverage": None, "lastCrawl": None, "title": title})

    total = len(rows)
    indexed = states["indexed"]
    actions = []
    for cause in CAUSES:
        urls = groups.get(cause)
        if not urls:
            continue
        n = len(urls)
        priority = "P1" if total and n / total >= 0.2 and cause != "awaiting-crawl" else PRIORITY[cause]
        brand = brands.most_common(1)[0][0] if cause == "foreign-brand" and brands else ""
        listing = "\n".join(f"- {u['url']} ({t['states'][u['state']]})" for u in urls)
        body = (
            f"**Page**: {n} URL\n{listing}\n"
            f"**Problem**: {t['problem'].format(n=n, date=args.date or 'today')}\n"
            f"**Why it matters**: {t['why'][cause]}\n"
            f"**What to do**: {t['fix'][cause]}\n"
            f"**How to check**: {t['check_removed'] if cause == 'foreign-brand' else t['check']}\n"
        )
        actions.append({
            "id": f"indexing:{cause}", "cause": cause, "who": WHO[cause], "priority": priority,
            "title": t["title"][cause].format(n=n, brand=brand), "urls": urls, "body": body,
        })

    report = {"date": args.date, "total": total, "indexed": indexed, "states": dict(states), "actions": actions,
              "protected": [p for p in args.protected.split(",") if p]}
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)

    print(f"## {t['summary'].format(indexed=indexed, total=total)}\n")
    for state, count in states.most_common():
        print(f"- {t['states'][state]} : {count}")
    print()
    for a in actions:
        print(f"- [{a['priority']} · {a['who']}] {a['title']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
