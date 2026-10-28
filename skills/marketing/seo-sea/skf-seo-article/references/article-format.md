# Article format

Every article is first written as one Markdown file per language — the archive and the version `check_article.py`
checks — then turned into what `content.publish` needs (the repository's blog format, the CMS's fields, or the
same Markdown plus HTML to paste).

```markdown
---
title: "<title, within titleMax>"
description: "<meta description, 50 to 160 characters>"
slug: <slug>
lang: fr
date: YYYY-MM-DD
target: "<main search>"
excerpt: "<one or two sentences for the blog index and social cards>"
category: <blog category>
tags: [<tag>, <tag>]
image: <path or URL, or "to create: <what it shows>">
image_alt: "<what the image shows>"
canonical: <full URL once published>
sources:
  - "<label> — <URL>"
---

<First paragraph: the direct answer to the main search, two to four sentences.>

## <H2 from the brief>

<Paragraphs. Internal links as [anchor](/path/). Outside facts followed by their source, as a link or a
numbered note that matches the « Sources » list.>

### <H3 when the brief has one>

- <list items when a list reads better>

## <The product section: what the product makes easier>

## Sources

1. [<label>](<URL>)
```

Rules the checker enforces (`scripts/check_article.py`): every front matter field above except `canonical` and
`category`; the title within `--title-max` (default 60); the description within 50 to 160 characters; the slug in
lower case, words joined by hyphens, no accents; no H1 in the body (the CMS or the page prints the title as H1);
headings never skip a level; at least one internal link; every link a full `https://` URL or a site path; the
word count within `--min-words` and `--max-words`.

**HTML twin** (`--html out.html`): the body only (no front matter, no `<html>`), with `<h2>`, `<h3>`, `<p>`,
`<ul>`/`<ol>`, `<a>`, `<strong>`, `<em>` — what CMS editors accept when pasted. The title, description and slug are
given separately, at the top of the ticket, for the CMS's fields.

**Per platform**: WordPress, Drupal, Webflow, Ghost take the HTML body; Contentful and Strapi take Markdown, or their
rich-text JSON when the field is of that type (`publishers.md`); a repository's blog takes `repo.blog.format`
(MDX, Markdown with its front matter, JSON…), converted from this file field by field.
