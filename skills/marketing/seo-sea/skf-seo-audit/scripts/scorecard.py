#!/usr/bin/env python3
"""SEO scorecard of a site: one score out of 100, computed the same way at every pass so it can be compared.

Usage:
    python3 scorecard.py --site "Example" --crawl crawl.json [--pagespeed pagespeed.csv] \
        [--actions P1,P2,P3] [--sc clicks,impressions,position] [--sc-prev clicks,impressions,position] \
        [--previous previous.json] [--lang fr|en] [--out scorecard.json]

Score (out of 100, parts without data are left out and the rest scaled up):
    technical  /50  pages without SEO problems, from the crawl (high 1, medium 0.4, low 0.1 per finding, per page;
                    a missing sitemap or a crawl blocked costs 10 points)
    speed      /25  mean mobile PageSpeed performance of the pages measured on the latest date
    actions    /25  25 - 8 per open P1, 3 per open P2, 1 per open P3
Status: red under 60 or with an open P1, orange under 80, green otherwise.
Search Console figures (28 days) are shown with their change but are not part of the score: a young site has none.
They give the visibility stage instead, shown next to the score: starting (under 100 impressions in 28 days),
growing (under 1,000), established — a sound site nobody finds yet is not "good SEO".

Prints the Markdown card (for the scorecard issue body), then writes the JSON (embedded in the card as a comment, so
the next pass and the digest can read it back). Standard library only.
"""

import argparse
import csv
import datetime
import json
import re
import sys

WEIGHTS = {"high": 1.0, "medium": 0.4, "low": 0.1, "info": 0.0}
SITEWIDE = {"sitemap-missing", "crawl-blocked"}
SKIPPED = {"not-checked", "crawl-sampled"}
MARKER = "seo-scorecard"

TEXT = {
    "fr": {
        "title": "Tableau de bord SEO", "score": "Note SEO", "technical": "Technique", "speed": "Vitesse",
        "actions": "Actions ouvertes", "sc": "Search Console (28 j)", "clicks": "clics", "impressions": "impressions",
        "position": "position moyenne", "pages": "pages vérifiées", "clean": "sans problème", "since": "depuis le",
        "status": {"green": "🟢 bon", "orange": "🟠 à surveiller", "red": "🔴 à corriger"}, "none": "pas de données",
        "updated": "Mis à jour par la passe SEO du",
        "visibility": "Visibilité", "stages": {"starting": "🌱 démarrage", "growing": "📈 en progression", "established": "✅ installée"},
    },
    "en": {
        "title": "SEO scorecard", "score": "SEO score", "technical": "Technical", "speed": "Speed",
        "actions": "Open actions", "sc": "Search Console (28 days)", "clicks": "clicks", "impressions": "impressions",
        "position": "average position", "pages": "pages checked", "clean": "without problems", "since": "since",
        "status": {"green": "🟢 good", "orange": "🟠 to watch", "red": "🔴 to fix"}, "none": "no data",
        "updated": "Updated by the SEO pass of",
        "visibility": "Visibility", "stages": {"starting": "🌱 starting", "growing": "📈 growing", "established": "✅ established"},
    },
}


def triple(value, cast=(int, int, float)):
    if not value:
        return None
    parts = [p.strip() for p in value.split(",")]
    if len(parts) != len(cast):
        raise SystemExit(f"expected {len(cast)} comma-separated values, got {value!r}")
    return [c(p) for c, p in zip(cast, parts)]


def technical(crawl):
    pages = [p for p in crawl.get("pages", []) if p.get("status") == 200]
    findings = [f for f in crawl.get("findings", []) if f["rule"] not in SKIPPED]
    penalty = {}
    for f in findings:
        if f["rule"] not in SITEWIDE:
            penalty[f["page"]] = penalty.get(f["page"], 0) + WEIGHTS.get(f["severity"], 0)
    if not pages:
        return None, 0, 0
    total = sum(max(0.0, 1 - penalty.get(p["url"], 0)) for p in pages)
    clean = sum(1 for p in pages if penalty.get(p["url"], 0) == 0)
    score = 50 * total / len(pages) - 10 * sum(1 for f in findings if f["rule"] in SITEWIDE)
    return max(0, round(score)), len(pages), clean


def speed(path):
    try:
        with open(path, encoding="utf-8") as handle:
            rows = [r for r in csv.DictReader(handle) if r.get("strategy", "mobile") == "mobile" and r.get("performance")]
    except (FileNotFoundError, TypeError):
        return None, None
    if not rows:
        return None, None
    latest = max(r["date"] for r in rows)
    values = [int(float(r["performance"])) for r in rows if r["date"] == latest]
    mean = sum(values) / len(values)
    return round(25 * mean / 100), round(mean)


def trend(now, before, lower_is_better=False):
    if before in (None, 0) or now is None:
        return ""
    change = (now - before) / before * 100
    if abs(change) < 1:
        return " (=)"
    good = change < 0 if lower_is_better else change > 0
    arrow = "▲" if change > 0 else "▼"
    return f" ({arrow} {abs(change):.0f} %{' ✓' if good else ''})"


def main():
    parser = argparse.ArgumentParser(description="SEO scorecard of a site, out of 100.")
    parser.add_argument("--site", required=True)
    parser.add_argument("--crawl", required=True, help="crawl.json from skf-seo-audit/scripts/crawl.py")
    parser.add_argument("--pagespeed", help="pagespeed.csv history from skf-seo-audit/scripts/pagespeed.py --csv")
    parser.add_argument("--actions", default="0,0,0", help="open tracker actions: P1,P2,P3")
    parser.add_argument("--sc", help="Search Console, last 28 days: clicks,impressions,position")
    parser.add_argument("--sc-prev", help="Search Console, the 28 days before: clicks,impressions,position")
    parser.add_argument("--previous", help="previous scorecard JSON (to show the change)")
    parser.add_argument("--lang", default="fr", choices=sorted(TEXT))
    parser.add_argument("--date", default=datetime.date.today().isoformat())
    parser.add_argument("--out", default="scorecard.json")
    args = parser.parse_args()
    t = TEXT[args.lang]

    with open(args.crawl, encoding="utf-8") as handle:
        crawl = json.load(handle)
    tech, checked, clean = technical(crawl)
    spd, perf = speed(args.pagespeed)
    p1, p2, p3 = triple(args.actions, (int, int, int))
    act = max(0, 25 - 8 * p1 - 3 * p2 - p3)

    parts = {"technical": (tech, 50), "speed": (spd, 25), "actions": (act, 25)}
    got = sum(v for v, _ in parts.values() if v is not None)
    out_of = sum(m for v, m in parts.values() if v is not None)
    score = round(100 * got / out_of) if out_of else 0
    status = "red" if score < 60 or p1 else "orange" if score < 80 else "green"

    previous = None
    if args.previous:
        try:
            with open(args.previous, encoding="utf-8") as handle:
                text = handle.read()
            match = re.search(rf"<!-- {MARKER}: (\{{.*?\}}) -->", text, re.S)
            previous = json.loads(match.group(1) if match else text)
        except (FileNotFoundError, ValueError, AttributeError):
            previous = None

    sc, sc_prev = triple(args.sc), triple(args.sc_prev)
    data = {
        "site": args.site, "date": args.date, "score": score, "status": status,
        "technical": tech, "speed": spd, "actions": act, "performance": perf,
        "pages": checked, "clean": clean, "open": {"P1": p1, "P2": p2, "P3": p3},
        "searchConsole": dict(zip(("clicks", "impressions", "position"), sc)) if sc else None,
    }

    delta = ""
    if previous and previous.get("score") is not None:
        diff = score - previous["score"]
        change = f"▲ +{diff}" if diff > 0 else f"▼ {diff}" if diff < 0 else "="
        delta = f" ({change} {t['since']} {previous.get('date')})"
    stage = None if not sc else "starting" if sc[1] < 100 else "growing" if sc[1] < 1000 else "established"
    data["visibility"] = stage
    data["summary"] = f"{t['status'][status]} {score}/100{delta}" + (f" · {t['visibility']} {t['stages'][stage]}" if stage else "")

    none = t["none"]
    tech_cell = f"{tech}/50 — {clean}/{checked} {t['pages']} {t['clean']}" if tech is not None else none
    speed_cell = f"{spd}/25 — PageSpeed mobile {perf}/100" if spd is not None else none
    lines = [
        f"## {t['title']} — {args.site}",
        "",
        f"**{t['score']} : {score}/100** — {t['status'][status]}{delta}"
        + (f" · **{t['visibility']} : {t['stages'][stage]}**" if stage else ""),
        "",
        "| | |",
        "|---|---|",
        f"| {t['technical']} | {tech_cell} |",
        f"| {t['speed']} | {speed_cell} |",
        f"| {t['actions']} | {act}/25 — 🔴 P1 {p1} · 🟠 P2 {p2} · 🔵 P3 {p3} |",
    ]
    if sc:
        prev = sc_prev or [None, None, None]
        lines.append(
            f"| {t['sc']} | {sc[0]} {t['clicks']}{trend(sc[0], prev[0])} · {sc[1]} {t['impressions']}"
            f"{trend(sc[1], prev[1])} · {t['position']} {sc[2]:.1f}{trend(sc[2], prev[2], True)} |"
        )
    else:
        lines.append(f"| {t['sc']} | {none} |")
    lines += ["", f"_{t['updated']} {args.date}._", f"<!-- {MARKER}: {json.dumps(data, ensure_ascii=False)} -->"]
    card = "\n".join(lines)

    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
    print(card)
    return 0


if __name__ == "__main__":
    sys.exit(main())
