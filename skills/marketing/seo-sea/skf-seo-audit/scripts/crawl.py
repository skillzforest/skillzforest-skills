#!/usr/bin/env python3
"""Crawl a website from its sitemap and check the on-page SEO basics of every page.

Usage:
    python3 crawl.py https://example.com/ [--max 200] [--out crawl.json]

Reads robots.txt and the sitemap (sitemap.xml, sitemap-index.xml or the one robots.txt names), fetches every page
listed (up to --max), and writes a JSON report: one entry per page with what was found, plus a list of findings
(severity, rule, page, detail). Prints a one-screen summary. Standard library only; falls back to curl when Python
has no CA certificates.

Checks: HTTP status and redirects, <title> and meta description (present, length, duplicates), exactly one <h1>,
canonical, robots noindex, <html lang>, hreflang alternates (present, reciprocal, x-default), images without alt,
JSON-LD present, internal links to pages that fail, pages in the sitemap but not linked, response weight.
"""

import argparse
import collections
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

AGENT = "Mozilla/5.0 (compatible; skf-seo-audit/0.1)"
TITLE_MAX = 60
DESC_MIN, DESC_MAX = 50, 160
HEAVY_BYTES = 1_000_000


def fetch(url, timeout=15):
    """Return (status, final_url, headers, body bytes). Never raises for HTTP errors."""
    request = urllib.request.Request(url, headers={"User-Agent": AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.geturl(), dict(response.headers), response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, url, dict(exc.headers or {}), b""
    except urllib.error.URLError as exc:
        if "CERTIFICATE_VERIFY_FAILED" not in str(exc):
            return 0, url, {}, b""
    # Python without CA certificates: let curl do the request.
    result = subprocess.run(
        ["curl", "-sSL", "--max-time", str(timeout), "-A", AGENT, "-o", "-", "-w", "\n%{http_code} %{url_effective}", url],
        capture_output=True,
    )
    body, _, tail = result.stdout.rpartition(b"\n")
    parts = tail.decode().split(" ", 1)
    status = int(parts[0]) if parts[0].isdigit() else 0
    return status, parts[1] if len(parts) > 1 else url, {}, body


class PageParser(HTMLParser):
    """Collect the SEO-relevant elements of one HTML page."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.lang = None
        self.title = None
        self.description = None
        self.robots = None
        self.canonical = None
        self.hreflang = {}
        self.h1 = []
        self.images_without_alt = 0
        self.images = 0
        self.links = set()
        self.jsonld = 0
        self._in = None
        self._text = []

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "html":
            self.lang = a.get("lang") or None
        elif tag == "title" and self.title is None:
            self._in, self._text = "title", []
        elif tag == "h1":
            self._in, self._text = "h1", []
        elif tag == "meta":
            name = a.get("name", "").lower()
            if name == "description":
                self.description = a.get("content", "").strip()
            elif name == "robots":
                self.robots = a.get("content", "").lower()
        elif tag == "link":
            rel = a.get("rel", "").lower().split()
            if "canonical" in rel:
                self.canonical = a.get("href")
            if "alternate" in rel and a.get("hreflang"):
                self.hreflang[a["hreflang"].lower()] = a.get("href")
        elif tag == "a" and a.get("href"):
            self.links.add(a["href"])
        elif tag == "img":
            self.images += 1
            if "alt" not in a:
                self.images_without_alt += 1
        elif tag == "script" and a.get("type", "").lower() == "application/ld+json":
            self.jsonld += 1

    def handle_endtag(self, tag):
        if tag == self._in:
            text = re.sub(r"\s+", " ", "".join(self._text)).strip()
            if tag == "title":
                self.title = text
            else:
                self.h1.append(text)
            self._in = None

    def handle_data(self, data):
        if self._in:
            self._text.append(data)


def sitemap_urls(site):
    """Every page URL listed by the site's sitemap(s)."""
    candidates = []
    status, _, _, body = fetch(urllib.parse.urljoin(site, "/robots.txt"))
    if status == 200:
        candidates += re.findall(r"(?im)^\s*sitemap:\s*(\S+)", body.decode("utf-8", "replace"))
    candidates += [urllib.parse.urljoin(site, p) for p in ("/sitemap-index.xml", "/sitemap_index.xml", "/sitemap.xml")]

    seen, pages = set(), []
    queue = collections.deque(candidates)
    while queue:
        url = queue.popleft()
        if url in seen:
            continue
        seen.add(url)
        status, _, _, body = fetch(url)
        if status != 200 or not body:
            continue
        try:
            root = ET.fromstring(body)
        except ET.ParseError:
            continue
        for loc in root.iter():
            if loc.tag.endswith("loc") and loc.text:
                target = loc.text.strip()
                if root.tag.endswith("sitemapindex"):
                    queue.append(target)
                else:
                    pages.append(target)
        if pages:
            break  # one working sitemap (index) is enough
    return list(dict.fromkeys(pages))


def normalize(url):
    parsed = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc.lower(), parsed.path or "/", "", ""))


def main():
    parser = argparse.ArgumentParser(description="Crawl a site from its sitemap and check on-page SEO.")
    parser.add_argument("site", help="home page, e.g. https://example.com/")
    parser.add_argument("--max", type=int, default=200, help="maximum pages to fetch (default 200)")
    parser.add_argument("--out", default="crawl.json", help="JSON report path (default crawl.json)")
    args = parser.parse_args()

    site = args.site if args.site.endswith("/") else args.site + "/"
    host = urllib.parse.urlsplit(site).netloc.lower()
    findings = []

    def finding(severity, rule, page, detail=""):
        findings.append({"severity": severity, "rule": rule, "page": page, "detail": detail})

    urls = sitemap_urls(site)
    if not urls:
        finding("high", "sitemap-missing", site, "no sitemap found in robots.txt, /sitemap-index.xml or /sitemap.xml")
        urls = [site]
    if len(urls) > args.max:
        finding("info", "crawl-truncated", site, f"{len(urls)} pages in the sitemap, {args.max} crawled")
        urls = urls[: args.max]

    pages = {}
    for url in urls:
        status, final, headers, body = fetch(url)
        page = {"url": url, "status": status, "final": final, "bytes": len(body)}
        if final and normalize(final) != normalize(url):
            finding("medium", "sitemap-redirect", url, f"redirects to {final}: list the final URL in the sitemap")
        if status != 200:
            finding("high", "page-error", url, f"HTTP {status}")
            pages[normalize(url)] = page
            continue
        html = PageParser()
        html.feed(body.decode("utf-8", "replace"))
        page.update(
            lang=html.lang, title=html.title, description=html.description, robots=html.robots,
            canonical=html.canonical, hreflang=html.hreflang, h1=html.h1, images=html.images,
            imagesWithoutAlt=html.images_without_alt, jsonld=html.jsonld,
        )
        internal = set()
        for href in html.links:
            absolute = urllib.parse.urljoin(final, href)
            if urllib.parse.urlsplit(absolute).netloc.lower() == host and absolute.startswith("http"):
                internal.add(normalize(absolute))
        page["internalLinks"] = sorted(internal)
        pages[normalize(url)] = page
        time.sleep(0.2)  # be gentle with the server

        if not html.title:
            finding("high", "title-missing", url)
        elif len(html.title) > TITLE_MAX:
            finding("low", "title-long", url, f"{len(html.title)} characters (Google shows about {TITLE_MAX})")
        if not html.description:
            finding("medium", "description-missing", url)
        elif not DESC_MIN <= len(html.description) <= DESC_MAX:
            finding("low", "description-length", url, f"{len(html.description)} characters ({DESC_MIN}-{DESC_MAX})")
        if len(html.h1) != 1:
            finding("medium", "h1-count", url, f"{len(html.h1)} <h1>")
        if not html.lang:
            finding("low", "lang-missing", url, "<html> has no lang attribute")
        if html.robots and "noindex" in html.robots:
            finding("high", "noindex-in-sitemap", url, "listed in the sitemap but marked noindex")
        if not html.canonical:
            finding("low", "canonical-missing", url)
        elif normalize(urllib.parse.urljoin(final, html.canonical)) != normalize(final):
            finding("medium", "canonical-elsewhere", url, f"canonical points to {html.canonical}")
        if html.images_without_alt:
            finding("low", "img-alt-missing", url, f"{html.images_without_alt} of {html.images} images without alt")
        if not html.jsonld:
            finding("info", "structured-data-missing", url, "no JSON-LD")
        if len(body) > HEAVY_BYTES:
            finding("low", "page-heavy", url, f"HTML of {len(body) // 1024} KB")

    # Site-wide checks
    ok = [p for p in pages.values() if p.get("status") == 200]
    for field, rule in (("title", "title-duplicate"), ("description", "description-duplicate")):
        groups = collections.defaultdict(list)
        for p in ok:
            if p.get(field):
                groups[p[field]].append(p["url"])
        for value, same in groups.items():
            if len(same) > 1:
                finding("medium", rule, same[0], f"{len(same)} pages share it: {', '.join(same[:5])}")

    langs = {p.get("lang") for p in ok if p.get("lang")}
    if len(langs) > 1:
        for p in ok:
            alternates = p.get("hreflang") or {}
            if not alternates:
                finding("medium", "hreflang-missing", p["url"], f"site in {len(langs)} languages")
                continue
            if "x-default" not in alternates:
                finding("low", "hreflang-x-default", p["url"])
            for code, href in alternates.items():
                other = pages.get(normalize(urllib.parse.urljoin(p["final"], href or "")))
                if other and other.get("status") == 200:
                    back = {normalize(urllib.parse.urljoin(other["final"], h or "")) for h in (other.get("hreflang") or {}).values()}
                    if normalize(p["final"]) not in back:
                        finding("medium", "hreflang-not-reciprocal", p["url"], f"{code} → {href} does not link back")

    linked = set()
    for p in ok:
        linked.update(p.get("internalLinks", []))
    for key, p in pages.items():
        if p.get("status") == 200 and key not in linked and key != normalize(site):
            finding("low", "orphan-page", p["url"], "in the sitemap but no page links to it")
    known_bad = {k for k, p in pages.items() if p.get("status") not in (200, None)}
    for p in ok:
        for target in p.get("internalLinks", []):
            if target in known_bad:
                finding("high", "broken-internal-link", p["url"], f"links to {target}")

    report = {"site": site, "crawled": len(pages), "pages": list(pages.values()), "findings": findings}
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)

    counts = collections.Counter(f["severity"] for f in findings)
    rules = collections.Counter(f["rule"] for f in findings)
    print(f"{site}: {len(pages)} pages crawled, {len(findings)} findings "
          f"(high {counts['high']}, medium {counts['medium']}, low {counts['low']}, info {counts['info']})")
    for rule, n in rules.most_common():
        print(f"  {n:4}  {rule}")
    print(f"Report: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
