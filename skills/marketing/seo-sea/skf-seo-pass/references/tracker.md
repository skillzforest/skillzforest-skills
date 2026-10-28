# Action tracker

Every action the SEO factory finds — an audit finding, an opportunity left for later, something only the owner can
do — becomes **one item in a tracker**, never a line lost in a Markdown file. The tracker is chosen in the profile
(`tracker.type`) and set up by `skf-seo-setup`.

| `tracker.type` | Where the actions live | When |
|---|---|---|
| `github-issues` | One GitHub issue per action, in `tracker.repo`, on the GitHub Project board `tracker.project` when there is one | The owner uses GitHub (default in mode `repo`) |
| `jira` | One Jira issue per action in the project `tracker.jiraProject` of `tracker.jiraSite`, through Composio (`tracker.account`) | The owner's team works in Jira |
| `google-sheets` | One row per action in the Google Sheet `tracker.sheetId`, shared with `notify.to` | No GitHub, or the owner prefers a sheet (default in mode `advise`) |

Whatever the tracker, the owner is told by `notify` (email or Slack): a digest of open owner actions every
`tracker.digest` (default `weekly`), and a message when new high-priority actions appear.

## An action

| Field | Meaning |
|---|---|
| **id** | Stable fingerprint, `<rule>:<page path or theme>`, e.g. `title-duplicate:/docs/administration/`, `sitemap-old:www.romkade.com`, `content-gap:sunrise-2027`. Never two open actions with the same id |
| **title** | What to do, in `style.reportLanguage`, under 80 characters, starting with a verb: « Supprimer l'ancien sitemap www.romkade.com dans Search Console » |
| **who** | `agent` — anything that lives in the repository, whatever the folder: pages, layouts, documentation sites built from it, blog or demo content (MDX, Markdown), sitemap, links, titles. `owner` — only what no commit can do: Search Console settings, indexing requests, DNS, a CMS or back office without an API the agent can use, legal or factual sign-off, decisions. When in doubt, `agent` |
| **priority** | `P1` blocking (not indexable, errors, wrong canonical, broken sitemap) · `P2` important (template issues on many pages, pages with impressions and few clicks, content gaps with clear demand) · `P3` polish |
| **page** | URL concerned, or the theme for a content gap |
| **problem** | What is wrong, with the figure that shows it |
| **why** | One sentence: what it costs in search |
| **fix** | What to do, with the exact text when there is one |
| **check** | How to verify it is done (a URL to open, a Search Console screen, a search to watch) |
| **source** | `audit YYYY-MM-DD` or `pass YYYY-MM-DD` |

## GitHub issues (`tracker.type: github-issues`)

Labels (created by setup): `seo`, `seo:agent`, `seo:owner`, `seo:P1`, `seo:P2`, `seo:P3`, `seo:scorecard`,
`claude:fix`, and for article tickets `article`, `article:planned`, `article:review`, `article:changes`,
`article:approved`, `article:published`, `article:abandoned`.

`seo:scorecard` marks the one issue per site that holds the SEO scorecard (`SKILL.md`, Scorecard): its body is the
latest card, its comments the history. It is not an action: leave it out of every list, count and digest of actions.

`claude:fix` is the owner's switch: put on any issue (agent or owner), it starts the fix task (`skf-seo-setup`,
step 6) that fixes that issue with `skf-github-issue-fix` and opens a pull request — even in protected files, for
that issue only. The SEO pass leaves those issues to it.

Issue body:

```markdown
**Page**: <page>
**Problem**: <problem>
**Why it matters**: <why>
**What to do**: <fix>
**How to check**: <check>

_Source: <source>_
<!-- seo-id: <id> -->
```

`scripts/tracker_github.py` does the GitHub side with the `gh` command line:

```bash
python3 scripts/tracker_github.py setup --repo OWNER/REPO [--project-owner OWNER --project-number N]
python3 scripts/tracker_github.py upsert --repo OWNER/REPO --id ID --title "..." --who agent|owner \
        --priority P1|P2|P3 --body-file body.md [--project-owner OWNER --project-number N]
python3 scripts/tracker_github.py list --repo OWNER/REPO [--who owner] [--state open|closed|all]
python3 scripts/tracker_github.py close --repo OWNER/REPO --id ID --comment "Done: ..."
```

`upsert` never duplicates: it finds the open or closed issue holding `seo-id: ID`, updates an open one, reopens
nothing (a closed action stays closed unless the problem is back, then it comments and reopens). Without `gh` (a
cloud run), use the runtime's GitHub tools or Composio `GITHUB_CREATE_AN_ISSUE`, `GITHUB_UPDATE_AN_ISSUE`,
`GITHUB_LIST_REPOSITORY_ISSUES` (search the body for the `seo-id` marker), `GITHUB_CREATE_AN_ISSUE_COMMENT`, with the
same body and labels.

A pull request that fixes an action says `Fixes #<number>` in its body: the issue closes when the owner merges.

The board: a GitHub Project (`tracker.project`) with the default Status field (Todo, In Progress, Done). Every issue
is added to it. Creating a board needs the `project` scope (`gh auth refresh -s project`).

## Jira (`tracker.type: jira`)

Through the Composio Jira toolkit, account `tracker.account` (look the exact tool names up with the toolkit's
search: create issue, edit issue, search with JQL, transition issue, add comment, list transitions). Issue type
`Task` (or `tracker.jiraIssueType`), labels `seo`, `seo-agent` or `seo-owner`, `seo-P1`/`P2`/`P3` (Jira labels take
no colon), summary = the action's title, description = the same body as a GitHub issue, the `seo-id` marker on its
last line. Find an action by JQL: `project = <key> AND labels = seo AND text ~ "seo-id: <id>"`. Close = transition
to the project's done status with a comment. `claude:fix` has no Jira equivalent: the owner asks in the chat or
labels the action `claude-fix`, which the next pass treats like an open `agent` action of priority `P1`.

## Article tickets

The content plan (`skf-seo-content-audit`) opens one ticket per article; `skf-seo-article` moves it along:

| Status | GitHub labels | Jira | Google Sheet (tab `Articles`) | Meaning |
|---|---|---|---|---|
| Planned | `seo`, `article`, `article:planned` | first status, label `article` | `Planned` | In the plan, with its date |
| To review | `article`, `article:review` | « In Review » (or the closest), comment with the link | `To review` | Written: pull request, CMS draft or `.md` file waiting for the owner |
| Changes | `article:changes` added | label `article-changes` | `Changes` | The owner asked for changes in a comment |
| Approved | `article:approved` | « Approved » or the closest | `Approved` | `markdown` mode: validated, to paste |
| Published | closed, `article:published` | done status, the URL in a comment | `Published` + URL | Live on the site |
| Abandoned | closed, `article:abandoned` | « Won't do » | `Abandoned` | Not worth writing any more (reason in a comment) |

Ticket body:

```markdown
**Publication** : <date> · **Type** : <new|update|news|pillar|setup>
**Recherche visée** : <main search per language>
**Pourquoi** : <the brief's evidence in two lines>
**Brief** : <link to the brief file>
**Validation** : <pull request | brouillon dans <CMS> | fichier .md à coller>

Relisez l'article quand le ticket passe à « À valider », puis publiez-le (fusion, « Publier » dans le CMS, ou collage
du fichier) et passez le ticket à « Publié » avec l'adresse.
<!-- seo-id: article:<slug> -->
```

`python3 scripts/tracker_github.py article --repo OWNER/REPO --id article:<slug> --status <status> [--title … --body-file …]
[--comment …]` creates the ticket (first call, with title and body) or moves it; `published` and `abandoned` close it.

Article tickets are not SEO actions: the pass and the digest count them separately (`article:*`), and a pass never
fixes one. The sheet keeps them in an `Articles` tab: ID, Date, Type, Title, Target, Status, Brief, Link, URL.

## Google Sheets (`tracker.type: google-sheets`)

One sheet named `Actions`, header row:

| A | B | C | D | E | F | G | H | I | J | K | L | M |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ID | Priority | Who | Status | Action | Page | Problem | Why | What to do | How to check | Source | Opened | Closed / link |

Status values: `To do`, `In progress`, `Done`, `Won't do`. The owner changes Status in the sheet; the agent reads it.

Tools (Composio, account `tracker.account`):

- create: `GOOGLESHEETS_CREATE_GOOGLE_SHEET1` (`title`: `SEO actions — <site.name>`), then
  `GOOGLESHEETS_VALUES_UPDATE` on `Actions!A1:M1` (or `Sheet1!A1:M1`, then keep that sheet name in the profile) for
  the header; share with `notify.to` as writer through `GOOGLEDRIVE_CREATE_PERMISSION` when the sheet's owner is not
  that address;
- read: `GOOGLESHEETS_VALUES_GET` on `<sheet>!A:M`; an action exists when column A holds its id;
- add: `GOOGLESHEETS_SPREADSHEETS_VALUES_APPEND` (`valueInputOption`: `USER_ENTERED`), one row per new id;
- update a row (status, closing date, link): `GOOGLESHEETS_VALUES_UPDATE` on that row's range.

Never delete a row: a finished action is `Done` with its date and link.

## Digest

At every pass, when the last digest is older than `tracker.digest` (date kept in the journal as a line
`- YYYY-MM-DD — digest sent`), send through `notify`:

- subject `SEO <site.name>: <n> actions waiting for you`;
- the open `owner` actions, `P1` first then oldest first, each on one line: priority, title, link (issue or sheet);
- one line on what the agent fixed since the last digest, and the link to the board or sheet.

Nothing open for the owner: no digest. An owner who follows several sites gets one consolidated digest instead
(`tracker.digest: none` in each profile, one `SEO digest` task: `skf-seo-setup/references/digest-prompt.md`). A new `P1` owner action: tell the owner in the same pass, without waiting
for the digest.
