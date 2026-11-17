#!/usr/bin/env python3
"""Read a website's brand and pitch for a short video (stdlib only).

    site_brand.py <url> --short <shorts/slug> [--pages /pricing,/features] [--screens] [--max-css 6]

Fetches the page (and --pages), its stylesheets, then writes <short>/inbox/site/site.json:
title, description, Open Graph, theme-color, language, headings, paragraphs, calls to
action, CSS custom properties, most used colors and fonts, Google Fonts families,
@font-face files, logo and icon candidates. Downloads the Open Graph image, the logo
candidates and the icons into <short>/assets/site/. With --screens, takes desktop
(1440×900) and mobile (500×1080 @2x — 500 px is headless Chrome's narrowest window) screenshots of every page with a local headless
Chrome / Chromium / Edge into <short>/assets/site/screens/.

Nothing is decided here: the agent picks the brand colors and fonts from this file.
Prints a short summary as JSON.
"""
import argparse
import json
import re
import shutil
import ssl
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
HEX = re.compile(r"#(?:[0-9a-fA-F]{3}){1,2}\b")
RGB = re.compile(r"rgba?\(\s*(\d{1,3})[\s,]+(\d{1,3})[\s,]+(\d{1,3})(?:[\s,/]+([\d.]+%?))?\s*\)")
VAR = re.compile(r"(--[\w-]+)\s*:\s*([^;}{]+)")
FONT = re.compile(r"font-family\s*:\s*([^;}{]+)")
FACE = re.compile(r"@font-face\s*{([^}]*)}", re.S)
URL = re.compile(r"url\(\s*['\"]?([^'\")]+)['\"]?\s*\)")
IMPORT = re.compile(r"@import\s+(?:url\()?['\"]?([^'\")\s;]+)")
ROOT_BLOCK = re.compile(r"(:root|html|\[data-theme[^\]]*\]|\.dark|\.light)[^{]*{([^}]*)}", re.S)


def fetch(url, binary=False, limit=4_000_000):
    data, ctype, charset = _get(url, {"User-Agent": UA, "Accept-Language": "fr,en;q=0.8"}, 25, limit)
    if binary:
        return data, ctype
    return data.decode(charset or "utf-8", errors="replace")


def _ssl_context():
    try:
        import certifi  # noqa: PLC0415 — optional
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return None


def _get(url, headers, timeout, limit=None):
    """GET with urllib; on a certificate error (Python without root certificates,
    common on macOS), retry with certifi, then with the system curl."""
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read(limit) if limit else resp.read(), resp.headers.get_content_type(), resp.headers.get_content_charset()
    except urllib.error.URLError as exc:
        if "CERTIFICATE_VERIFY_FAILED" not in str(exc):
            raise
    ctx = _ssl_context()
    if ctx:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.read(limit) if limit else resp.read(), resp.headers.get_content_type(), resp.headers.get_content_charset()
    cmd = ["curl", "-sSL", "--fail", "--max-time", str(timeout), "-w", "\\n%{content_type}"]
    for k, v in headers.items():
        cmd += ["-H", f"{k}: {v}"]
    done = subprocess.run(cmd + [url], capture_output=True)
    if done.returncode != 0:
        raise urllib.error.URLError(done.stderr.decode(errors="replace").strip() or "curl failed")
    body, _, ctype = done.stdout.rpartition(b"\n")
    ctype = ctype.decode(errors="replace")
    charset = ctype.split("charset=")[-1].strip() if "charset=" in ctype else None
    return (body[:limit] if limit else body), ctype.split(";")[0].strip(), charset


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.meta, self.links, self.styles, self.inline_css = {}, [], [], []
        self.headings = {"h1": [], "h2": [], "h3": []}
        self.paragraphs, self.ctas, self.nav, self.images = [], [], [], []
        self.lang, self.title = None, ""
        self._stack, self._text, self._in_style, self._in_title = [], [], False, False
        self._a_href, self._a_cls = None, ""

    def handle_starttag(self, tag, attrs):
        a = {k: (v or "") for k, v in attrs}
        if tag == "html":
            self.lang = a.get("lang")
        elif tag == "meta":
            key = a.get("property") or a.get("name")
            if key and a.get("content"):
                self.meta[key.lower()] = a["content"]
        elif tag == "link":
            rel = a.get("rel", "").lower()
            self.links.append({"rel": rel, "href": a.get("href", ""), "sizes": a.get("sizes", ""), "type": a.get("type", "")})
            if "stylesheet" in rel and a.get("href"):
                self.styles.append(a["href"])
        elif tag == "style":
            self._in_style = True
        elif tag == "title":
            self._in_title = True
        elif tag == "img":
            self.images.append({"src": a.get("src") or a.get("data-src", ""), "alt": a.get("alt", ""), "cls": a.get("class", "") + " " + a.get("id", "")})
        elif tag == "a":
            self._a_href, self._a_cls = a.get("href"), a.get("class", "")
        if tag in ("h1", "h2", "h3", "p", "a", "button", "li"):
            self._stack.append(tag)
            self._text = []
        if a.get("style"):
            self.inline_css.append(a["style"])

    def handle_endtag(self, tag):
        if tag == "style":
            self._in_style = False
        elif tag == "title":
            self._in_title = False
        if self._stack and self._stack[-1] == tag:
            self._stack.pop()
            text = " ".join("".join(self._text).split())
            if not text:
                return
            if tag in self.headings and len(self.headings[tag]) < 25:
                self.headings[tag].append(text)
            elif tag == "p" and len(text) > 40 and len(self.paragraphs) < 30:
                self.paragraphs.append(text[:400])
            elif tag in ("a", "button") and len(text) < 40:
                cls = self._a_cls if tag == "a" else ""
                if tag == "button" or re.search(r"btn|button|cta", cls, re.I):
                    if text not in self.ctas:
                        self.ctas.append(text)
                elif tag == "a" and self._a_href and len(self.nav) < 40:
                    self.nav.append({"text": text, "href": self._a_href})

    def handle_data(self, data):
        if self._in_style:
            self.inline_css.append(data)
        elif self._in_title:
            self.title += data
        elif self._stack:
            self._text.append(data)


def to_hex(r, g, b):
    return "#{:02X}{:02X}{:02X}".format(*(max(0, min(255, int(x))) for x in (r, g, b)))


def norm_hex(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return "#" + h.upper()


def colors_in(css):
    found = [norm_hex(h) for h in HEX.findall(css)]
    for r, g, b, a in RGB.findall(css):
        if a and a not in ("1", "100%") and float(a.rstrip("%")) < (100 if a.endswith("%") else 1):
            continue  # translucent overlays are not brand colors
        found.append(to_hex(r, g, b))
    return found


def chrome():
    for name in ("google-chrome", "chromium", "chromium-browser", "microsoft-edge", "chrome"):
        path = shutil.which(name)
        if path:
            return path
    for path in ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                 "/Applications/Chromium.app/Contents/MacOS/Chromium",
                 "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
                 "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"):
        if Path(path).exists():
            return path
    return None


def screenshot(binary, url, target, width, height, scale):
    cmd = [binary, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
           "--no-default-browser-check", f"--window-size={width},{height}",
           f"--force-device-scale-factor={scale}", "--virtual-time-budget=6000",
           f"--screenshot={target}", url]
    done = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
    return target.exists() and target.stat().st_size > 0, (done.stderr or "")[-300:]


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "home"


def download(url, folder, name):
    try:
        data, ctype = fetch(url, binary=True, limit=15_000_000)
    except Exception as exc:  # noqa: BLE001 — report, keep going
        return None, str(exc)
    ext = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp", "image/svg+xml": ".svg",
           "image/gif": ".gif", "image/x-icon": ".ico", "image/vnd.microsoft.icon": ".ico"}.get(ctype)
    if not ext:
        ext = Path(urllib.parse.urlparse(url).path).suffix.lower() or ".bin"
    target = folder / f"{name}{ext}"
    target.write_bytes(data)
    return target, None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url")
    ap.add_argument("--short", required=True, help="the short's folder (shorts/<slug>)")
    ap.add_argument("--pages", default="", help="comma-separated paths or URLs to read too")
    ap.add_argument("--screens", action="store_true")
    ap.add_argument("--max-css", type=int, default=6)
    args = ap.parse_args()

    short = Path(args.short)
    inbox = short / "inbox" / "site"
    assets = short / "assets" / "site"
    inbox.mkdir(parents=True, exist_ok=True)
    assets.mkdir(parents=True, exist_ok=True)

    base = args.url if re.match(r"https?://", args.url) else "https://" + args.url
    pages = [base] + [urllib.parse.urljoin(base, p.strip()) for p in args.pages.split(",") if p.strip()]
    report = {"url": base, "pages": [], "warnings": []}
    css_text, css_seen = [], set()
    color_count, font_count, variables = Counter(), Counter(), {}
    google_fonts, faces, logos, icons = set(), [], [], []

    for i, url in enumerate(pages):
        try:
            html = fetch(url)
        except Exception as exc:  # noqa: BLE001
            report["warnings"].append(f"{url}: {exc}")
            continue
        page = Page()
        page.feed(html)
        entry = {
            "url": url, "title": page.title.strip(), "lang": page.lang,
            "description": page.meta.get("description") or page.meta.get("og:description"),
            "og": {k: v for k, v in page.meta.items() if k.startswith(("og:", "twitter:"))},
            "themeColor": page.meta.get("theme-color"),
            "headings": page.headings, "paragraphs": page.paragraphs, "ctas": page.ctas[:15],
            "nav": page.nav[:30] if i == 0 else [],
        }
        report["pages"].append(entry)
        css_text.append("\n".join(page.inline_css))
        for href in page.styles:
            full = urllib.parse.urljoin(url, href)
            if "fonts.googleapis.com" in full:
                google_fonts.update(re.findall(r"family=([^:&]+)", urllib.parse.unquote(full)))
                continue
            if full in css_seen or len(css_seen) >= args.max_css:
                continue
            css_seen.add(full)
            try:
                css = fetch(full)
            except Exception as exc:  # noqa: BLE001
                report["warnings"].append(f"css {full}: {exc}")
                continue
            for imp in IMPORT.findall(css):
                if "fonts.googleapis.com" in imp:
                    google_fonts.update(re.findall(r"family=([^:&]+)", urllib.parse.unquote(imp)))
            for block in FACE.findall(css):
                fam = re.search(r"font-family\s*:\s*['\"]?([^;'\"]+)", block)
                weight = re.search(r"font-weight\s*:\s*([^;]+)", block)
                srcs = [urllib.parse.urljoin(full, u) for u in URL.findall(block)]
                if fam and srcs:
                    faces.append({"family": fam.group(1).strip(), "weight": (weight.group(1).strip() if weight else None),
                                  "src": next((s for s in srcs if s.endswith(".woff2")), srcs[0])})
            css_text.append(css)
        for img in page.images:
            hint = f"{img['src']} {img['alt']} {img['cls']}".lower()
            if img["src"] and "logo" in hint:
                logos.append({"url": urllib.parse.urljoin(url, img["src"]), "reason": "img logo"})
        for link in page.links:
            if "icon" in link["rel"] and link["href"]:
                icons.append({"url": urllib.parse.urljoin(url, link["href"]), "rel": link["rel"], "sizes": link["sizes"]})
        if "fonts.googleapis.com" in html:
            google_fonts.update(re.findall(r"fonts\.googleapis\.com/css2?\?family=([^:&\"']+)", urllib.parse.unquote(html)))
        for m in re.finditer(r"<svg[^>]*(?:logo|brand)[^>]*>.*?</svg>", html, re.S | re.I):
            if len(m.group(0)) < 60_000 and not any(l.get("inline") for l in logos):
                svg = assets / "logo-inline.svg"
                svg.write_text(m.group(0))
                logos.append({"url": None, "inline": True, "file": str(svg.relative_to(short)), "reason": "inline svg logo"})

    css = "\n".join(css_text)
    for selector, body in ROOT_BLOCK.findall(css):
        for name, value in VAR.findall(body):
            value = " ".join(value.split())
            if len(value) < 120:
                variables.setdefault(selector, {})[name] = value
    color_count.update(colors_in(css))
    for fam in FONT.findall(css):
        fam = re.sub(r"\s*!important$", "", " ".join(fam.split()))
        if "var(" not in fam and "inherit" not in fam:
            font_count[fam] += 1

    report.update({
        "cssVariables": variables,
        "colors": [{"hex": h, "count": n} for h, n in color_count.most_common(24)],
        "fonts": [{"family": f, "count": n} for f, n in font_count.most_common(10)],
        "googleFonts": sorted(f.replace("+", " ") for f in google_fonts),
        "fontFaces": faces[:20],
        "logos": logos[:8],
        "icons": icons[:8],
        "downloads": {},
    })

    first = report["pages"][0] if report["pages"] else {}
    wanted = []
    if first.get("og", {}).get("og:image"):
        wanted.append(("og-image", urllib.parse.urljoin(base, first["og"]["og:image"])))
    for n, logo in enumerate(x for x in logos if x.get("url")):
        wanted.append((f"logo-{n + 1}", logo["url"]))
        if n >= 3:
            break
    best_icon = sorted(icons, key=lambda x: ("apple-touch" not in x["rel"], "svg" not in x["url"]))[:2]
    for n, icon in enumerate(best_icon):
        wanted.append((f"icon-{n + 1}", icon["url"]))
    for name, url in wanted:
        target, err = download(url, assets, name)
        if target:
            report["downloads"][name] = str(target.relative_to(short))
        else:
            report["warnings"].append(f"download {name}: {err}")

    if args.screens:
        binary = chrome()
        if not binary:
            report["warnings"].append("no Chrome/Chromium/Edge found for screenshots: use the browser tool, or add screenshots by hand")
        else:
            screens = assets / "screens"
            screens.mkdir(exist_ok=True)
            for url in pages:
                name = slug(urllib.parse.urlparse(url).path)
                for kind, (w, h, s) in {"desktop": (1440, 900, 1), "mobile": (500, 1080, 2)}.items():
                    target = screens / f"{name}-{kind}.png"
                    ok, err = screenshot(binary, url, target, w, h, s)
                    if ok:
                        report["downloads"][f"screen-{name}-{kind}"] = str(target.relative_to(short))
                    else:
                        report["warnings"].append(f"screenshot {url} {kind}: {err.strip()[:160]}")

    (inbox / "site.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({
        "site": str(inbox / "site.json"),
        "title": first.get("title"), "description": first.get("description"),
        "topColors": [c["hex"] for c in report["colors"][:8]],
        "fonts": [f["family"] for f in report["fonts"][:4]], "googleFonts": report["googleFonts"],
        "downloads": report["downloads"], "warnings": report["warnings"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    sys.exit(main())
