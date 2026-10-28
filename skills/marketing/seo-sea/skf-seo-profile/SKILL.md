---
name: skf-seo-profile
description: Builds the SEO profile of a website, step by step with its owner — product and audience, languages, where the product's facts live, themes to rank for and searches to avoid, writing rules, whether the site lives in a Git repository (the agent edits it through pull requests) or not (the agent advises through Google Slides), data sources (Search Console, Google Trends), cadence and how to notify the owner — then writes and validates .seo/profile.json, the single input of the whole SEO factory (skf-seo-setup, skf-seo-audit, skf-seo-pass). Use it whenever someone wants to start continuous SEO on a site, set up an SEO agent, describe a site for SEO, or change an existing SEO profile, or runs /skf-seo-profile.
---

# SEO profile

You interview the owner of a website and write `.seo/profile.json`: everything the other SEO skills need to know
about the site, and nothing they could work out alone. The format is described field by field in
[`references/profile.md`](references/profile.md); a complete example is
[`templates/profile.example.json`](templates/profile.example.json). Read both before the first question.

The SEO factory, for the owner's orientation:

```text
skf-seo-profile  →  .seo/profile.json  →  skf-seo-setup  →  skf-seo-audit (once, then now and then)
                                                          →  skf-seo-pass  (scheduled, every few days)
```

## How to interview

- **Work it out first, ask second.** Read the repository, fetch the live site, then propose an answer the owner
  confirms or corrects. Never ask a question whose answer is on the page or in the code.
- **One step at a time**, in the order below. Use the question tool when there is one (2 to 4 options, your
  proposal first and marked as recommended); otherwise a short numbered question in the chat.
- Speak the owner's language. The profile's keys stay in English; its values (pitch, themes, rules) can be in any
  language.
- Never put a password, an API key or a token in the profile: accounts are connected in the connectors (Composio,
  gum), the profile only names them.
- Editing an existing profile: read it, ask only about what the owner wants to change, keep everything else.

## Steps

### 1. The workspace and the mode

1. Are you inside the site's Git repository (`git rev-parse --show-toplevel`, a `package.json`, `astro.config.*`,
   `next.config.*`, `hugo.toml`, `_config.yml`, `content/`)? Then propose mode **`repo`**: the agent edits the site
   and opens pull requests.
2. Otherwise ask where the site is made. A CMS (WordPress, Webflow, Wix, Shopify, Squarespace) or no access to the
   code means mode **`advise`**: the agent writes recommendations in a Google Slides deck and the owner applies
   them. The profile then lives in a small dedicated Git repository (`seo-<site>`) that `skf-seo-setup` creates;
   until then, write it in the current folder.
3. In mode `repo`, find out whether a push to the base branch deploys the site (`.github/workflows/`,
   `netlify.toml`, `vercel.json`, the host's settings). Say what you found; when unsure, assume it does.

### 2. The site

Fetch the home page with and without `www` and follow the redirects: `site.url` is the final address, the one the
page's canonical names (never assume one form). Propose `site.name`, `site.url`, `site.pitch` (what it does, for whom, in two sentences),
`site.audience` and `site.business` (free, freemium, paid, open source). Ask the owner to correct.

### 3. Languages

Read the `hreflang` links of the home page and the i18n setup of the code. Propose `languages.list` with each
`pathPrefix`; ask the default language and how to address readers in each (`vous` or `tu`, `usted` or `tú`, `Sie`
or `du`). Markets (countries) are optional: ask only when one language serves very different countries.

### 4. Facts

The agent may only claim what these sources say. In mode `repo`, list the files that hold features, pricing,
compatibility, FAQ (`src/data/`, `content/`, i18n dictionaries) and propose them; always add the live pages that
show them (`facts.urls`). Ask whether something true is on no page yet (`facts.notes`).

### 5. Themes and exclusions

1. From the pitch and the site's pages, propose 3 to 6 **themes** the product genuinely answers (a problem, a task,
   a comparison people search for), each with 2 to 6 **beginnings of searches** per language, as people type them
   (`how to invoice`, `anbernic add games`). If `skf-seo-pass` is installed, check a few with its
   `scripts/suggest.py <lang> "<beginning>"` and keep the ones Google completes.
2. Propose **exclusions**: searches with volume the site must never chase — piracy and cracks, "free" for a paid
   product, competitors' brand names, off-topic meanings of the same word. Ask the owner to add their own.
3. Competitors are optional: ask for 1 to 3 sites that rank on the same searches.

### 6. Writing rules

Read a few pages and propose `style.rules`: words the brand uses or avoids, tone, promises it never makes (legal,
medical, results). Ask the language for reports and emails (`style.reportLanguage`), usually the owner's.

### 7. Where things are edited

- Mode `repo`: map `repo.pages` — for the home page and the main pages (features, pricing, docs, FAQ…), the file that
  holds the title, description and texts, and how translations are organized. Find the blog if there is one
  (folder, front matter, URL pattern, images, the checks it must pass) and the check command (`npm test`,
  `npm run build`, `hugo`…) — run it once to be sure it passes before the agent relies on it, **without the local
  `.env`**: a scheduled cloud run has none. When the build needs public variables (those the deploy workflow sets),
  put them in the command itself (`npm ci && PUBLIC_X=… npm test`); never a secret. Propose
  `repo.protected`: legal pages, layouts and styles, CI, the `.seo/` profile itself. Branch prefix: `claude/seo-`.
  Read the limits the checks enforce (title and description lengths) into `repo.limits`.
- Mode `advise`: ask the CMS, whether decks go to Google Slides (default) or stay as Markdown, an optional Google
  Drive folder, and how many unapplied recommendations may pile up before the agent waits (3).

### 8. Data sources

Ask, proposing the default in bold:

- **Google Search Console** — what already brings visitors. Through **Composio** (works in scheduled cloud runs, the
  account is connected once), through **gum** (only on this computer), or none (a site not verified yet). Ask the
  property: `sc-domain:example.com` for a domain property, `https://example.com/` for a URL prefix. Ask the alias
  of the connected account if the owner has several.
- **Google Trends** — which themes rise or fall, worldwide. Through **SerpApi** (free plan, about 100 searches a
  month: `maxCallsPerPass` 5) or none.
- Google autocomplete and web search: on by default, no account needed. PageSpeed Insights for the audit: on.

Do not connect anything here: `skf-seo-setup` does it and tests each connection.

### 9. Cadence

Propose `every 2 days at 08:00` in the owner's time zone, one action per pass, a new article at most every 14 days
and no page touched again before 28 days (Google needs that long to measure a change). A young site with no
traffic can run weekly. A site that needs content (a blog to fill, a young site) can also get **articles every
week**: say that `skf-seo-content-audit` plans them (how many, how often, how they are validated) once the setup is
done — do not ask about it here.

### 10. Notification

Ask how the owner wants to hear about a pull request or a new recommendation: **Gmail**, **Outlook** (Microsoft
365), **Slack**, or none (they watch GitHub or the deck). For a mailbox, the safest recipient is the connected
account's own address. `when`: `on-change` (default) or `every-pass`.

### 11. Action tracker

Every action the agent finds — and above all those only the owner can do — must land somewhere the owner sees and
cannot forget. Ask:

1. Does the owner use GitHub? Mode `repo` almost always: propose **GitHub issues** in the site's repository
   (`tracker.repo`). A team that works in **Jira**: a Jira project (`tracker.jiraSite`, `tracker.jiraProject`),
   connected through Composio. Then, for GitHub, ask whether they already have a GitHub Project board for it (`gh project list --owner
   <owner>`): reuse it (`projectOwner`, `projectNumber`) or let `skf-seo-setup` create one named `SEO <site.name>`.
2. No GitHub, or a team that lives in spreadsheets: **Google Sheets** — one row per action, shared with the owner's
   address, created by `skf-seo-setup`.
3. How often to receive the list of actions waiting for them: **weekly** (default), at every pass, or never
   (discouraged: say why).

The owner is told by `notify`, so the tracker never relies on them remembering to look. Details:
`skf-seo-pass/references/tracker.md`.

### 12. Write and check

1. Write `.seo/profile.json` with `paths` set to `.seo/journal.md` and `.seo/reports/` (keep existing paths if the
   site already has a journal elsewhere).
2. Run `python3 scripts/validate_profile.py .seo/profile.json` (path relative to this skill's folder for the
   script). Fix every error; read the warnings to the owner and fix those they agree with.
3. Show a short summary: mode, languages, themes, exclusions, sources, cadence, notification, tracker.
4. Next step: **`skf-seo-setup`**, which connects the sources, creates the journal and schedules the agent. In mode
   `repo`, the profile is committed with the rest of the setup, not now.
