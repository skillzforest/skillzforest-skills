#!/usr/bin/env python3
"""Check an article written as Markdown with front matter (references/article-format.md), and optionally write
its HTML twin, ready to paste into a CMS editor.

Usage:
    python3 check_article.py article.md [--title-max 60] [--min-words 700] [--max-words 1600] [--html out.html]

Prints one line per problem and exits with 1 when there is at least one, 0 otherwise. Standard library only: the
front matter is read as simple YAML (key: value, inline [lists] and "- " lists) and the body converted with the
Markdown the format allows (headings, paragraphs, lists, links, bold, italic).
"""

import argparse
import html
import re
import sys

REQUIRED = ("title", "description", "slug", "lang", "date", "target", "excerpt", "tags", "image", "image_alt", "sources")
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")


def parse(text):
    """Split front matter and body; return (meta dict, body)."""
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not match:
        return {}, text
    meta, key = {}, None
    for line in match.group(1).splitlines():
        if not line.strip():
            continue
        item = re.match(r"^\s+-\s+(.*)$", line)
        if item and key:
            meta.setdefault(key, [])
            if isinstance(meta[key], list):
                meta[key].append(item.group(1).strip().strip('"'))
            continue
        pair = re.match(r"^([A-Za-z_]+):\s*(.*)$", line)
        if not pair:
            continue
        key, value = pair.group(1), pair.group(2).strip()
        if value.startswith("[") and value.endswith("]"):
            meta[key] = [v.strip().strip('"') for v in value[1:-1].split(",") if v.strip()]
        elif value:
            meta[key] = value.strip('"')
        else:
            meta[key] = []
    return meta, match.group(2)


def inline(text):
    out = html.escape(text, quote=False)
    out = LINK.sub(lambda m: f'<a href="{html.escape(m.group(2))}">{m.group(1)}</a>', out)
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", out)
    return out


def to_html(body):
    blocks, paragraph, items, kind = [], [], [], None

    def flush():
        nonlocal paragraph, items, kind
        if paragraph:
            blocks.append(f"<p>{inline(' '.join(paragraph))}</p>")
            paragraph = []
        if items:
            blocks.append(f"<{kind}>" + "".join(f"<li>{inline(i)}</li>" for i in items) + f"</{kind}>")
            items, kind = [], None

    for line in body.splitlines():
        heading = re.match(r"^(#{2,4})\s+(.*)$", line)
        bullet = re.match(r"^\s*[-*]\s+(.*)$", line)
        number = re.match(r"^\s*\d+[.)]\s+(.*)$", line)
        if heading:
            flush()
            level = len(heading.group(1))
            blocks.append(f"<h{level}>{inline(heading.group(2).strip())}</h{level}>")
        elif bullet or number:
            if paragraph:
                flush()
            wanted = "ul" if bullet else "ol"
            if kind and kind != wanted:
                flush()
            kind = wanted
            items.append((bullet or number).group(1).strip())
        elif not line.strip():
            flush()
        else:
            if items:
                flush()
            paragraph.append(line.strip())
    flush()
    return "\n".join(blocks) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Check a Markdown article and write its HTML twin.")
    parser.add_argument("article")
    parser.add_argument("--title-max", type=int, default=60)
    parser.add_argument("--min-words", type=int, default=700)
    parser.add_argument("--max-words", type=int, default=1600)
    parser.add_argument("--html", help="write the body as HTML to this file")
    args = parser.parse_args()

    with open(args.article, encoding="utf-8") as handle:
        meta, body = parse(handle.read())
    problems = []
    if not meta:
        problems.append("no front matter (--- … --- at the top)")
    for field in REQUIRED:
        if not meta.get(field):
            problems.append(f"front matter: {field} missing")
    title, description, slug = meta.get("title", ""), meta.get("description", ""), meta.get("slug", "")
    if title and len(title) > args.title_max:
        problems.append(f"title: {len(title)} characters (max {args.title_max})")
    if description and not 50 <= len(description) <= 160:
        problems.append(f"description: {len(description)} characters (50 to 160)")
    if slug and not SLUG.match(slug):
        problems.append(f"slug: '{slug}' must be lower case words joined by hyphens, no accents")
    if meta.get("date") and not re.match(r"^\d{4}-\d{2}-\d{2}$", meta["date"]):
        problems.append("date: expected YYYY-MM-DD")

    levels = [len(m.group(1)) for m in re.finditer(r"^(#{1,6})\s", body, re.M)]
    if 1 in levels:
        problems.append("body: no H1 (# …) — the page prints the title as H1")
    previous = 1
    for level in levels:
        if level > previous + 1:
            problems.append(f"headings: H{level} after H{previous} skips a level")
        previous = level
    if not levels:
        problems.append("body: no H2 sections")

    links = [m.group(2) for m in LINK.finditer(body)]
    if not any(href.startswith("/") for href in links):
        problems.append("body: no internal link (a path such as /pricing/)")
    for href in links:
        if not (href.startswith("/") or href.startswith("https://") or href.startswith("#")):
            problems.append(f"link: {href} is neither a site path nor an https:// URL")

    text = LINK.sub(r"\1", body)
    text = re.sub(r"[#*`>|_-]", " ", text)
    words = len(re.findall(r"\w[\w'’-]*", text))
    if not args.min_words <= words <= args.max_words:
        problems.append(f"length: {words} words ({args.min_words} to {args.max_words})")

    if args.html:
        with open(args.html, "w", encoding="utf-8") as handle:
            handle.write(to_html(body))

    for problem in problems:
        print(problem)
    print(f"{args.article}: {words} words, {len(links)} links — {'PASS' if not problems else 'FAIL'}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
