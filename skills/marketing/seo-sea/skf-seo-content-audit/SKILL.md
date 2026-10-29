---
name: skf-seo-content-audit
description: SEO audit for blog content — asks how many articles the owner wants and how often, studies what the site's audience searches (Search Console, Google autocomplete, Google Trends, what already ranks, the site's existing pages and articles) and writes a content plan of that many articles, one Markdown brief per article (target search, angle, outline, sources, internal links, publication date), then opens one ticket per article on a GitHub Project board, a Jira project or a Google Sheet, and sets up how articles get validated before publication — pull requests when the site lives in a Git repository (creating the blog section when there is none), drafts in the CMS (WordPress, Drupal, Contentful, Strapi, Webflow, Ghost or a custom API), or ready-to-paste Markdown files for any other back office. skf-seo-article then writes the articles one by one at the chosen pace. Use it whenever someone wants a blog, an editorial calendar, article ideas, a content plan, SEO articles written regularly, or runs /skf-seo-content-audit.
---

# SEO content audit

**Which site**: the one whose workspace you are in; when that is not obvious, ask the owner first — `../skf-seo-profile/references/profile.md`, Which site.

You turn search demand into a **content plan**: N articles worth writing for this site, each with a brief precise
enough for `skf-seo-article` to write it without guessing, each tracked as a ticket, each going through the owner's
validation before anything is published. Everything about the site is in `.seo/profile.json`
(`../skf-seo-profile/references/profile.md`); no profile → run `skf-seo-profile` first (it takes a few minutes and
this skill needs its themes, exclusions, languages and facts).

The content factory:

```text
skf-seo-content-audit  →  N briefs (.md) + N tickets (board)  →  skf-seo-article, at the chosen pace
                                                                  → validation: pull request | CMS draft | .md file
                                                                  → the owner publishes
```

Read first: [`references/brief.md`](references/brief.md) (the brief format),
[`../skf-seo-article/references/publishers.md`](../skf-seo-article/references/publishers.md) (validation and
publication per platform), `../skf-seo-profile/references/tracker.md` (tickets) and
`../skf-seo-profile/references/connectors.md` (sources).

Write the plan, briefs, tickets and messages in `style.reportLanguage`; article titles and searches in each site
language.

## Guardrails

- Read only on every source. Never publish anything: this skill plans; `skf-seo-article` writes; the owner
  validates and publishes.
- Nothing invented: demand comes from the sources below (say which), product claims from `facts`. No search
  volumes you did not get from a tool — autocomplete and Trends are signs of demand, not volumes.
- Never plan a subject matching `topics.exclude`, nor one an existing page or article already answers (plan an
  update of that page instead, as its own ticket, `type: update`).
- Credentials (CMS tokens, Jira) are never written in the profile, the briefs or the tickets: only the name of the
  environment variable or the connected account that holds them.

## 1. Ask the owner

Use the question tool when there is one; propose, the owner confirms. Skip what the profile's `content` block
already says, unless the owner wants to change it.

1. **How many articles** in this plan (`content.articles`): propose 8 (two months at two a week); 4 to 24 is
   reasonable. More can be planned later by running this skill again.
2. **How often** (`content.perWeek`, `content.schedule`): propose 1 a week for a small team, 2 for a site that needs
   content fast (a young site, a new market); never more than 3 — the owner must have time to validate them.
   Ask the day(s) and hour, in their time zone.
3. **Where the site is edited**, to choose how articles are validated and published (`content.publish`,
   `publishers.md`):
   - the site lives in a Git repository the agent can open (`mode: repo`) → **`repo`**: each article is a pull
     request; the owner merges it. No blog yet → the plan's first ticket creates the blog section (step 5);
   - a CMS with an API the agent may use (WordPress, Drupal, Contentful, Strapi, Webflow, Ghost, a custom back
     office) → **`cms`**: each article is created as a **draft** in the CMS; the owner reviews and publishes it
     there. Ask the CMS, its address, and create with the owner the most limited credential that can write drafts
     (`publishers.md` per CMS) — stored as an environment variable of the agent's cloud environment;
   - any other back office, or the owner prefers to paste → **`markdown`**: each article is a Markdown file (and
     its HTML twin) ready to copy into the CMS; the owner validates it on the ticket, then pastes it.
4. **Where tickets live** (`tracker`, when the profile has none or the owner wants another): a GitHub Project board
   (the site's repository, or the workspace's), a **Jira** project (ask the site URL and project key; connected
   through Composio), or a Google Sheet.
5. Optional: the target length (default 900 to 1,400 words), the author name shown on articles, categories the blog
   uses, whether every article needs an image (and where images come from).

## 2. Take stock of the content

1. Existing pages and articles: in mode `repo`, `repo.pages` and `repo.blog.dir`; otherwise the sitemap, the blog's
   index page or the CMS's API (list posts, read only). Note each one's subject, main search and date.
2. Open tickets of the tracker: `content-gap:` actions from audits and passes, and articles already planned
   (`article:*` labels or the sheet's Article rows) — never plan twice.
3. Previous plan (`<paths.reports>content-plan-*/`): what was written, published, abandoned.

## 3. Read the demand

For each theme of `topics.target` and each language:

- **Search Console** (when connected): queries with impressions on pages that only touch them in passing
  (position 8 to 40, few clicks), questions (`how`, `why`, `which`, `comment`, `pourquoi`, `quel`…), queries
  already bringing clicks to an article that a deeper one would serve better. Window: the last 3 months ending 3
  days ago.
- **Autocomplete**: `../skf-seo-profile/scripts/suggest.py <lang> "<seed>"` on the seeds and on question forms
  (`how to <seed>`, `<seed> vs`, `best <seed>`, `<seed> for <audience>`), with `--country` when the language has a
  market.
- **Google Trends** (`sources.trends`, within `maxCallsPerPass` × 2): compare the candidate themes; rising related
  queries on the best one.
- **What ranks**: web search on the 10 to 15 best candidates — what the first results answer, what they miss, their
  format (guide, list, comparison, definition), their length. A search dominated by marketplaces, forums or giant
  sites the site cannot beat is dropped or narrowed.
- **News**, when the site's themes move (a regulation, a standard, a product release): recent, checkable facts from
  the sources `facts.notes` allows. A news article is planned with a date and its sources.

## 4. Build the plan

1. Group the candidate searches into **subjects** (one article answers one intent; close variants go in the same
   article). Drop excluded or already-answered ones.
2. Score each subject: demand (evidence count and strength), fit with what the product does (`site.pitch`), chance
   to rank (what ranks, the site's authority), business value (how close the reader is to needing the product).
   Keep the best N; mix intents — a few **pillar** guides early (they receive the internal links), then specific
   questions, comparisons and news.
3. Order them: the blog section (when it must be created) first, pillars next, then by score; news articles at
   their date. Assign publication dates from `content.schedule` starting at the next slot.
4. For each article, write its brief, `<paths.reports>content-plan-<YYYY-MM-DD>/<NN>-<slug>.md`, following
   `references/brief.md`: target search and variants per language, intent, angle, title and description proposals,
   outline (H2/H3), what to say about the product (from `facts` only), sources to use, internal links (existing
   pages and other planned articles), length, image, date, the evidence behind it.
5. Write `<paths.reports>content-plan-<YYYY-MM-DD>/README.md`: the plan in one table (date, title, target search,
   type, ticket), how articles will be validated and published, and the demand findings in five lines.

## 5. The blog section (`content.publish: repo`, no `repo.blog`)

Plan it as ticket `#0` of the plan (`type: setup`), done by `skf-seo-article` on its first run (or now, when the
owner asks): it follows `../skf-seo-article/references/blog-scaffold.md` — find the framework, add a blog index, an
article page, the sitemap entries, the navigation link and the checks, with one example article removed before the
pull request — then fills `repo.blog` in the profile in the same pull request. Say so in the plan's README.

## 6. Tickets

One ticket per article, following `../skf-seo-profile/references/tracker.md` (section Article tickets):

- id `article:<slug>`, title `Article — <title>` (or `Mise à jour — <page>` for an update), type, publication
  date, the brief's summary and a link to the brief file;
- status **Planned** (GitHub: labels `article` and `article:planned`, added to the board with its date; Jira: the
  project's first status, label `article`, due date; sheet: a row with status `Planned`);
- `content-gap:` actions the plan answers get a comment linking the article ticket, and close when it is
  published.

The owner's part, said in every ticket: « Relisez l'article quand il passe à **À valider** : pull request à
fusionner, brouillon dans le CMS à publier, ou fichier .md à coller — puis passez le ticket à **Publié** avec
l'adresse de l'article. »

## 7. Schedule the writing

Write the `content` block of the profile (`profile.md`): `articles`, `perWeek`, `schedule`, `cron` (UTC), `publish`
and its settings (`cms` or `markdown`), `planDir`, `maxPending` (default 2: the writer waits when that many
articles wait for validation). Validate it (`../skf-seo-profile/scripts/validate_profile.py`).

Then schedule the writer: a task `SEO articles <site.name>` as `skf-seo-setup` step 7b says (same environment,
repositories and connectors as the other SEO tasks; its prompt runs `skf-seo-article`). In mode `cms`, the environment must
hold the CMS credential's variable: give the owner the exact variable name and where to set it, never ask them to
paste the secret in the chat. No scheduler: say the owner can run `skf-seo-article` by hand at each slot.

Commit the plan, the briefs and the profile (mode `repo`: on a branch `<repo.branchPrefix>content-plan-<date>`
with a pull request; otherwise on the workspace's base branch).

## 8. Tell the owner

Notify (`notify`) and answer, in a few lines: the N articles with their dates (a table), the evidence behind the
top three, how each article will reach them for validation and what they do then, the board link, the first
writing date, and what they must do now (merge the plan, set a credential, connect Jira).
