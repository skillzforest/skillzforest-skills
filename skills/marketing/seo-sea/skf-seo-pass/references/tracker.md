# Action tracker

Every action the SEO factory finds — an audit finding, an opportunity left for later, something only the owner can
do — becomes **one item in a tracker**, never a line lost in a Markdown file. The tracker is chosen in the profile
(`tracker.type`) and set up by `skf-seo-setup`.

| `tracker.type` | Where the actions live | When |
|---|---|---|
| `github-issues` | One GitHub issue per action, in `tracker.repo`, on the GitHub Project board `tracker.project` when there is one | The owner uses GitHub (default in mode `repo`) |
| `google-sheets` | One row per action in the Google Sheet `tracker.sheetId`, shared with `notify.to` | No GitHub, or the owner prefers a sheet (default in mode `advise`) |

Whatever the tracker, the owner is told by `notify` (email or Slack): a digest of open owner actions every
`tracker.digest` (default `weekly`), and a message when new high-priority actions appear.

## An action

| Field | Meaning |
|---|---|
| **id** | Stable fingerprint, `<rule>:<page path or theme>`, e.g. `title-duplicate:/docs/administration/`, `sitemap-old:www.romkade.com`, `content-gap:sunrise-2027`. Never two open actions with the same id |
| **title** | What to do, in `style.reportLanguage`, under 80 characters, starting with a verb: « Supprimer l'ancien sitemap www.romkade.com dans Search Console » |
| **who** | `agent` — the SEO pass can do it (titles, descriptions, sitemap entries in code, articles, links); `owner` — only a person can (Search Console settings, indexing requests, CMS changes in mode `advise`, legal or factual review, decisions) |
| **priority** | `P1` blocking (not indexable, errors, wrong canonical, broken sitemap) · `P2` important (template issues on many pages, pages with impressions and few clicks, content gaps with clear demand) · `P3` polish |
| **page** | URL concerned, or the theme for a content gap |
| **problem** | What is wrong, with the figure that shows it |
| **why** | One sentence: what it costs in search |
| **fix** | What to do, with the exact text when there is one |
| **check** | How to verify it is done (a URL to open, a Search Console screen, a search to watch) |
| **source** | `audit YYYY-MM-DD` or `pass YYYY-MM-DD` |

## GitHub issues (`tracker.type: github-issues`)

Labels (created by setup): `seo`, `seo:agent`, `seo:owner`, `seo:P1`, `seo:P2`, `seo:P3`, and `claude:fix`.

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
