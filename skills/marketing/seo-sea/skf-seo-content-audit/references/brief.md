# Article brief

One file per planned article, `<paths.reports>content-plan-<date>/<NN>-<slug>.md`. It is the contract between the
plan and the writer: `skf-seo-article` writes from it and nothing else (plus the profile's facts), so every
decision is taken here. Front matter in YAML, then the sections below, in `style.reportLanguage` except the texts
meant for the site.

```markdown
---
id: article:<slug>
number: <NN>
type: new | update | news | pillar | setup
date: YYYY-MM-DD            # planned publication slot
status: planned              # planned → written → review → published (or abandoned)
ticket: <url of the ticket>
languages: [fr, en]
slug: { fr: <slug-fr>, en: <slug-en> }
target: { fr: "<main search>", en: "<main search>" }
updates: <url>               # type update only: the page to rewrite
---

# <working title>

## Why this article
The evidence, with figures and where they come from: Search Console rows (query, impressions, position), the
autocomplete suggestions seen, the Trends comparison, what ranks today and what it misses. One sentence on the
business value: which reader, how close to needing the product.

## Searches
Per language: the main search, 3 to 8 variants and questions to answer in the text (from autocomplete and
Search Console), searches to avoid (from `topics.exclude` or off-intent).

## Angle
Intent (learn, compare, solve, choose, news), the reader and their situation, the promise of the article in one
sentence, what makes it better than what ranks (a missing answer, a fresher fact, a worked example, a table).

## Title and description
Per language, 2 proposals each: title within `repo.limits.titleMax` (60 by default, main search near the start),
description within 50 to 160 characters saying what the reader finds.

## Outline
H2 and H3, each with one line on what it says. The first paragraph answers the main search directly. One section,
near the end, on what the product makes easier — never an advert, only what `facts` say.

## Product facts to use
Bullet list, each with its source file or URL from `facts`. Nothing else may be said about the product.

## Outside sources
URLs to read and cite for every outside fact (official, primary sources first). Facts that could not be verified
are listed under « Not verified » and must stay out of the article.

## Internal links
Existing pages and planned articles to link to (path and anchor text), and the existing pages that should link to
this one once it is published.

## Format
Length (words), image (which one, or what to create), call to action, category and tags of the blog.
```

A `setup` brief (creating the blog section) has only the front matter, « Why » and the list of what the section
must contain (`../skf-seo-article/references/blog-scaffold.md`).
