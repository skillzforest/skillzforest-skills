# The SEO profile (`.seo/profile.json`)

One JSON file per site. Every skill of the SEO factory reads it; none of them hard-codes anything about a site.
It lives in the site's **workspace**: the site's own Git repository (mode `repo`), or a small dedicated Git
repository that only holds the profile, the journal and the reports (mode `advise`).

Validate it with `python3 scripts/validate_profile.py <path/to/profile.json>` (from the `skf-seo-profile` folder).
A complete example: [`templates/profile.example.json`](../templates/profile.example.json).

## Fields

### `site` (required)

| Field | Type | Meaning |
|---|---|---|
| `name` | string | Product or brand name, as people write it |
| `url` | string | Home page, `https://…/` with the trailing slash |
| `pitch` | string | One or two sentences: what the product does, for whom. The agent's reference for relevance |
| `audience` | string | Who searches for it (role, level, situation) |
| `business` | string | Free, freemium, paid SaaS, open source… Drives what the agent may say about price |

### `languages` (required)

| Field | Type | Meaning |
|---|---|---|
| `default` | string | ISO 639-1 code of the reference language |
| `list[]` | array | One entry per language the site is published in |
| `list[].code` | string | ISO 639-1 code (`fr`, `en`, `es`, `de`…) |
| `list[].pathPrefix` | string | URL prefix of that language: `/`, `/en/`, `/es/` |
| `list[].voice` | string | How to address the reader: `vous`, `tu`, `you`, `usted`, `Sie`, `du`… |
| `list[].markets` | string[] | Optional. ISO 3166 country codes the language mainly serves (`FR`, `BE`, `CA`) |

Every change is made in **all** languages at once, adapted rather than translated word for word.

### `facts` (required)

What the agent may claim about the product. It never writes a feature, a number, a price, a compatibility or a
testimonial that is not in these sources.

| Field | Type | Meaning |
|---|---|---|
| `files` | string[] | Mode `repo`: paths in the repository (data files, feature lists, FAQ) |
| `urls` | string[] | Pages of the live site that hold the facts (always allowed; the only source in mode `advise`) |
| `notes` | string | Optional. Facts given by the owner that are on no page yet |

### `topics` (required)

| Field | Type | Meaning |
|---|---|---|
| `target[]` | array | Themes worth ranking for, tied to what the product actually does |
| `target[].theme` | string | The theme in plain words |
| `target[].seeds` | object | Per language code, 2 to 6 beginnings of searches people type (`{"fr": ["anbernic ajouter"]}`) |
| `exclude` | string[] | Searches or words never to target, whatever their volume (piracy, "crack", "free" for a paid product, competitors' trademarks…) |
| `competitors` | string[] | Optional. Sites ranking on the same searches, for comparison only |

### `style` (required)

| Field | Type | Meaning |
|---|---|---|
| `reportLanguage` | string | Language of reports, emails and slides for the owner |
| `rules` | string[] | Writing rules: words to use or avoid, tone, things never to say |

### `mode` (required)

`"repo"` — the agent edits the site in its Git repository and opens a pull request for the owner to merge.
`"advise"` — no repository: the agent writes recommendations (exact texts to paste, article drafts) into a Google
Slides deck and a report, and the owner applies them in their CMS.

### `repo` (required when `mode` is `repo`)

| Field | Type | Meaning |
|---|---|---|
| `url` | string | `https://github.com/<owner>/<repo>` |
| `baseBranch` | string | Usually `main` |
| `branchPrefix` | string | Branches the agent creates, e.g. `claude/seo-` |
| `pushToBaseDeploys` | boolean | `true` when a push to the base branch puts the site online (the agent then never touches it) |
| `check` | string | Command that must pass before a pull request (`npm ci && npm test`, `hugo --minify`…). Empty: build only by reading |
| `pages[]` | array | Where each page's texts live |
| `pages[].name` | string | Page name (`Home`, `Pricing`…) |
| `pages[].url` | string | Path in the default language (`/`, `/pricing/`) |
| `pages[].file` | string | File holding its title, description and texts |
| `pages[].fields` | string | What to edit there and how translations are organized |
| `blog` | object | Optional. Absent: the agent never writes articles |
| `blog.dir` | string | Folder of articles, `{lang}` replaced by the language code (`src/content/blog/{lang}/`) |
| `blog.format` | string | File format and required front matter fields |
| `blog.urlPattern` | string | Public URL of an article, `{lang}` and `{slug}` replaced |
| `blog.images` | string | Optional. Folder of images the agent may use for articles |
| `blog.rules` | string | Optional. Length, internal links, structure the checks enforce |
| `limits` | object | Optional. `titleMax`, `descriptionMin`, `descriptionMax` (characters) |
| `protected` | string[] | Files and folders the agent never touches (legal pages, styles, CI, `.seo/profile.json`) |

### `advise` (required when `mode` is `advise`)

| Field | Type | Meaning |
|---|---|---|
| `cms` | string | WordPress, Webflow, Wix, Shopify, Squarespace, custom… (how the owner applies changes) |
| `deliverable` | string | `google-slides` (default), `xlsx` (Excel workbook, `skf-seo-audit/scripts/export_xlsx.py`) or `markdown` |
| `driveFolder` | string | Optional. Google Drive folder name or id for decks and drafts |
| `maxPending` | integer | Recommendations left unapplied before the agent stops adding new ones (default 3) |

### `sources` (required)

| Field | Type | Meaning |
|---|---|---|
| `searchConsole.via` | string | `composio`, `gum` or `none` |
| `searchConsole.property` | string | `sc-domain:example.com` or `https://example.com/` |
| `searchConsole.account` | string | Optional. Connected account alias (Composio) |
| `trends.via` | string | `serpapi` or `none` |
| `trends.account` | string | Optional. Connected account alias |
| `trends.maxCallsPerPass` | integer | Free plans are small: 5 is a good default |
| `suggest` | boolean | Use Google autocomplete (`suggest.py`) |
| `webSearch` | boolean | Look at what already ranks |
| `pagespeed` | boolean | PageSpeed Insights (Core Web Vitals): 3 pages at every pass, key pages at each audit; needs a free key in the `PAGESPEED_KEY` environment variable |

### `cadence` (required)

| Field | Type | Meaning |
|---|---|---|
| `schedule` | string | Human words, e.g. `every 2 days at 08:00 Europe/Paris` (setup turns it into a cron) |
| `cron` | string | Optional. Filled by `skf-seo-setup`: the cron in UTC |
| `articleEveryDays` | integer | Minimum days between two new articles (14) |
| `pageCooldownDays` | integer | Days before the same page is touched again (28) |
| `maxActionsPerPass` | integer | Always 1 unless the owner insists |

### `content` (optional: the blog's content plan)

Written by `skf-seo-content-audit`, read by `skf-seo-article`. Present: articles are planned and written by those
two skills at this pace, and `skf-seo-pass` no longer writes new articles itself (it turns the gaps it finds into
`content-gap:` actions for the next plan).

| Field | Type | Meaning |
|---|---|---|
| `articles` | integer | Articles in the current plan (asked to the owner) |
| `perWeek` | integer | Articles written a week, 1 to 3 |
| `schedule` | string | Human words, e.g. `Tuesday and Friday at 09:00 Europe/Paris` |
| `cron` | string | Filled by setup: the writer's cron in UTC |
| `publish` | string | `repo` (pull requests), `cms` (drafts in the CMS through its API) or `markdown` (files to paste) — `skf-seo-article/references/publishers.md` |
| `cms` | object | `publish: cms`: `type` (`wordpress`, `drupal`, `contentful`, `strapi`, `webflow`, `ghost`, `custom`), `baseUrl`, `tokenEnv` (environment variable holding the credential — never the credential), `userEnv`, `options`, `editUrl` |
| `markdown` | object | `publish: markdown`: `dir` (default `<paths.reports>articles/`), `html` (default true) |
| `planDir` | string | Folder of the current plan's briefs (`<paths.reports>content-plan-<date>/`) |
| `maxPending` | integer | Articles waiting for validation before the writer pauses (default 2) |
| `length` | string | Optional. Target length, e.g. `900-1400` words |
| `author` | string | Optional. Author shown on articles |

### `notify` (required)

| Field | Type | Meaning |
|---|---|---|
| `channel` | string | `gmail`, `outlook`, `slack` or `none` |
| `to` | string | Mailbox address (`gmail`, `outlook`) or channel name (`slack`). For a mailbox, the connected account's own address is the safe choice |
| `account` | string | Optional. Connected account alias |
| `when` | string | `on-change` (a pull request or a recommendation) or `every-pass` |

### `tracker` (required)

Where every action to do lives — audit findings, opportunities for later, things only the owner can do — so that
nothing is forgotten. Details: `skf-seo-pass/references/tracker.md`.

| Field | Type | Meaning |
|---|---|---|
| `type` | string | `github-issues` (one issue per action, on a GitHub Project board), `jira` (one Jira issue per action) or `google-sheets` (one row per action) |
| `jiraSite` | string | `jira`: the Jira address, `https://<team>.atlassian.net` |
| `jiraProject` | string | `jira`: the project key (`SEO`, `WEB`…) |
| `jiraIssueType` | string | Optional. Issue type for actions and articles (default `Task`) |
| `repo` | string | `github-issues`: repository holding the issues (`owner/repo`), usually the site's or the workspace's |
| `projectOwner` | string | Optional. Owner (user or organization) of the GitHub Project board |
| `projectNumber` | integer | Optional. Number of the board; absent: issues only |
| `sheetId` | string | `google-sheets`: spreadsheet id (filled by `skf-seo-setup`) |
| `sheetName` | string | `google-sheets`: tab holding the actions (`Actions`) |
| `account` | string | Optional. Connected account alias for the sheet |
| `url` | string | Link to the board or the sheet, given in every message (filled by `skf-seo-setup`) |
| `digest` | string | How often the owner gets the list of actions waiting for them: `weekly` (default), `every-pass`, `none` |

### `paths` (required)

| Field | Type | Meaning |
|---|---|---|
| `journal` | string | One line per applied action, read to respect the cadence (`.seo/journal.md`) |
| `reports` | string | Folder of pass and audit reports (`.seo/reports/`) |

### `routine` (filled by `skf-seo-setup`)

| Field | Type | Meaning |
|---|---|---|
| `id` | string | Scheduled task id |
| `url` | string | Where to see and pause it |
| `skillsRepo` | string | Repository the scheduled task clones to read the skills |
