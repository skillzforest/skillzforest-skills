---
name: skf-seo-setup
description: Turns a validated .seo/profile.json into a running SEO agent — checks the workspace (the site's Git repository, or a dedicated seo-SITE repository for sites on a CMS), connects and tests each source and output named in the profile (Google Search Console, SerpApi for Google Trends, Gmail, Outlook or Slack, Google Slides, GitHub), creates the action tracker (GitHub issues on a GitHub Project board, or a shared Google Sheet), the journal and the reports folder, then schedules the recurring skf-seo-pass as a cloud task (a Claude Code routine) that reads the skills from the SkillzForest skills repository, and runs it once to prove it works. Use it right after skf-seo-profile, when a connection breaks, when the cadence or notification changes, or whenever someone asks to schedule, automate or (re)connect their SEO agent, or runs /skf-seo-setup.
---

# SEO setup

You make the SEO agent of a site run on its own. Input: **`.seo/profile.json`** (made by `skf-seo-profile`; format:
`skf-seo-profile/references/profile.md`). Tools by profile value: `skf-seo-pass/references/connectors.md`.
Talk to the owner in their language; one step at a time; say what you are about to do before anything that leaves
their computer (connecting an account, creating a repository, scheduling a task, sending a test message).

Never ask for a password, an API key or a token in the chat: accounts are connected through the connectors' own
sign-in pages, which you open as links.

## 1. Check the profile

Run `python3 ../skf-seo-profile/scripts/validate_profile.py .seo/profile.json` (paths relative to this skill's
folder for the script). Errors: send the owner back to `skf-seo-profile`. Then read the profile and list what this
setup will connect, from its values.

## 2. The workspace

- **Mode `repo`**: the workspace is the site's repository (`repo.url`). Check that it is clean, on
  `repo.baseBranch`, pushed, and that `repo.check` passes now — the agent must start from a green build.
- **Mode `advise`**: the workspace is a small private repository holding only `.seo/`. If it does not exist, propose
  to create `<owner>/seo-<site-slug>` (`gh repo create --private`), ask for a yes, then push the profile there.

The scheduled task clones the workspace and the **skills repository** (the one holding
`skills/marketing/seo-sea/`, for SkillzForest `skillzforest/skillzforest-skills`). The Claude GitHub app must reach
both: if a later step fails with a repository access error, send the owner to
[github.com/apps/claude](https://github.com/apps/claude) > Configure > add the missing repository or organization.

## 3. Connect and test each source and output

For each entry below that the profile uses: list the connected accounts (`COMPOSIO_MANAGE_CONNECTIONS` `list`); when
the alias is missing or the account fails, create a connection (`add`, with the profile's alias) and give the owner
the link (it expires after 10 minutes: make a new one when needed); then run the **test**. Never move on with a
failing test.

| Profile | Connection | What the owner does on the link | Test (read only, except the message) |
|---|---|---|---|
| `sources.searchConsole.via: composio` | `google_search_console` | Picks the Google account that owns the property and **ticks the Search Console permission** (without it: "insufficient authentication scopes") | `LIST_SITES` shows `sources.searchConsole.property`; one `SEARCH_ANALYTICS_QUERY` on the last 28 days returns (rows may be empty on a new site) |
| `sources.searchConsole.via: gum` | `gum auth use-oauth-client` + `gum login --service searchconsole` (on the computer) | Signs in to Google | `gum read searchconsole.sites.list` — local runs only, no scheduled task |
| `sources.trends.via: serpapi` | `serpapi` | Creates a free account on serpapi.com and pastes the API key from serpapi.com/manage-api-key into the Composio form | One `SERPAPI_TRENDS_SEARCH` `TIMESERIES` on two seeds |
| `notify.channel: gmail` | `gmail` | Picks the mailbox and accepts the permissions | `GMAIL_SEND_EMAIL` of a short test message to `notify.to`, after telling the owner |
| `notify.channel: outlook` | `outlook` | Signs in with the Microsoft account | `OUTLOOK_SEND_EMAIL` test message to `notify.to` |
| `notify.channel: slack` | `slack` | Authorizes the workspace, invites the app to the channel | `SLACK_FIND_CHANNELS` then a test `SLACK_SEND_MESSAGE` |
| `advise.deliverable: google-slides` (or an audit deck) | `googleslides` (and `googledrive` for `advise.driveFolder`) | Picks the Google account | `GOOGLESLIDES_CREATE_SLIDES_MARKDOWN` of a one-slide test deck; give its link |
| `mode: repo` | GitHub, through the Claude GitHub app (and `github` in Composio as a fallback) | Installs the app on the repository | List the repository's open pull requests |

Search Console on a new site: if the property is not verified yet, walk the owner through it (Search Console > Add
property > Domain with a DNS record, or URL prefix with an HTML tag) and through submitting the sitemap. Data arrives
2 to 3 days later; the agent works on public demand until then.

## 4. Create the agent's files

In the workspace, if absent:

- `paths.journal` with a heading, one sentence on its format (`- YYYY-MM-DD — action — pages — status`) and an empty
  list;
- `paths.reports` (with a `.gitkeep`).

Commit them with the profile: mode `repo` through a pull request the owner merges (or directly when they say so),
mode `advise` on the workspace's base branch.

## 5. Create the action tracker

Jira (`tracker.type: jira`): connect the Jira toolkit in Composio (alias `tracker.account`), check with one read
(the project `tracker.jiraProject` exists and the account can create issues in it), and use labels instead of
GitHub's (`tracker.md`, Jira).

Every action — audit findings, opportunities for later, what only the owner can do — goes to the tracker, never to
a Markdown list. Format and tools: `skf-seo-pass/references/tracker.md`.

- **`github-issues`**:
  1. `python3 ../skf-seo-pass/scripts/tracker_github.py setup --repo <tracker.repo>` creates the `seo`, `seo:agent`,
     `seo:owner`, `seo:P1`–`P3` labels.
  2. Board: reuse `tracker.projectNumber`, or create one — `gh project create --owner <owner> --title "SEO
     <site.name>"`, then `gh project link <number> --owner <owner> --repo <tracker.repo>`. Creating a board needs
     the `project` scope: if `gh auth status` does not list it, ask the owner to run `gh auth refresh -s project`
     (it opens the browser) and wait. No board wanted or possible: issues alone still work.
  3. Write `projectOwner`, `projectNumber` and `url` (board, else the repository's issues filtered on `label:seo`)
     to the profile.
- **`google-sheets`** (connection `googlesheets`, and `googledrive` to share):
  1. Create `SEO actions — <site.name>` with `GOOGLESHEETS_CREATE_GOOGLE_SHEET1`, write the header row of
     `tracker.md` in the first tab, and note the tab's name in `tracker.sheetName`.
  2. When the sheet's Google account is not `notify.to`, share it with `notify.to` as writer
     (`GOOGLEDRIVE_CREATE_PERMISSION`, `type: user`, `role: writer`), after telling the owner.
  3. Write `sheetId` and `url` to the profile.
- Test: create one real action if one exists already (an owner action found during setup, such as "verify the
  property" or "remove an old sitemap"), otherwise none — never a fake one.

## 6. The cloud environment

Scheduled tasks run in a cloud environment. The default one (Claude Code: **Trusted** network) blocks most of what
the agent needs — Google autocomplete, the fact sources of an article, the site itself, PageSpeed — and holds no key.
Have the owner create one environment for the SEO tasks (once per account, shared by all their sites):

1. Claude Code (app or claude.ai/code), **Code** tab, environment selector under the message box > **Cloud** >
   **Add a cloud environment** (or **New environment** > Cloud): name `SEO`.
2. **Network access**: **Full** — or **Custom** with at least `suggestqueries.google.com`, `www.googleapis.com`, the
   site's own domain and the domains of `facts.urls`.
3. **Environment variables**: `PAGESPEED_KEY=<key>` (free key: Google Cloud console > APIs > PageSpeed Insights API >
   Credentials > API key, restricted to that API). A network secret (host `www.googleapis.com`, header
   `X-goog-api-key`, no prefix) is safer when the account allows it; the variable is the fallback.
4. Save, then get its id: in a terminal, `claude` then `/remote-env`, pick `SEO`; the id is written to
   `remote.defaultEnvironmentId` in `~/.claude/settings.json`. Use it for every task below.

Check it with a one-off task in that environment running `env | grep -o '^PAGESPEED[A-Z_]*'` (names only, never
values), `pagespeed.py` on the home page and a request to `suggestqueries.google.com`.

## 7. Schedule the pass

1. Turn `cadence.schedule` into a cron **in UTC** and confirm it with the owner in their local time ("08:00 Paris
   = 07:00 UTC in winter, 06:00 in summer — the task stays on UTC"). Every 2 days: `0 7 */2 * *` (odd days of the
   month; the 31st and the 1st run back to back). Write it to `cadence.cron`.
2. Create the scheduled task with the runtime's scheduling tool (Claude Code: the `schedule` skill / routines):
   - name `SEO <site.name>`;
   - environment: the `SEO` environment of step 6;
   - repositories: the workspace **and** the skills repository;
   - connectors: Composio (and any other the profile needs);
   - model: a capable, economical one (Claude Sonnet) unless the owner prefers otherwise;
   - tools: shell, file read/write/edit, search, web search and fetch, skills;
   - prompt: [`references/routine-prompt.md`](references/routine-prompt.md) with the values filled in.
3. Write `routine.id`, `routine.url` and `routine.skillsRepo` to the profile and commit.
   Updating a task later (Claude Code routines API): send the **whole** `job_config.ccr` — environment, session
   context (model, repositories, tools) and the prompt event. A partial `job_config` replaces the existing one and
   silently drops the prompt and repositories.
4. Run the task once now and read its log: it must reach Search Console (or say why not), respect the cadence, and
   end with a clear answer. Fix and rerun until it does.

No scheduling tool in this runtime: give the owner the prompt and the cron to paste into their scheduler, and say
the pass can always be run by hand with `skf-seo-pass`.

### 7b. Content plan and article task (optional)

Ask whether the owner wants blog articles written regularly. Yes: run `skf-seo-content-audit` (it asks how many
and how often, writes the plan and the tickets, and how articles are validated: pull request, CMS draft or Markdown
file). It then needs a third task `SEO articles <site.name>`: same environment, repositories, connectors, model and
tools as the pass, on `content.schedule` turned into a cron in UTC (write it to `content.cron`; twice a week:
`0 8 * * 2,5`), prompt [`references/routine-prompt.md`](references/routine-prompt.md) with, in step 1,
"Follow skills/marketing/seo-sea/skf-seo-article/SKILL.md (one article)". Write its id to `routine.articleId`.
Publishing through a CMS (`content.publish: cms`): the cloud environment needs the variable `content.cms.tokenEnv`
(and `userEnv`) — tell the owner its exact name and where to set it, the way PAGESPEED_KEY is set (step 6).

## 8. Schedule the fix task (GitHub issues only)

When `tracker.type` is `github-issues`, the owner can label any issue `claude:fix` to have it fixed now, through a
pull request (`skf-seo-pass/references/tracker.md`). Create a second scheduled task `Fix issues <site.name>`:

- same repositories, connectors, model and tools as the pass;
- prompt: [`references/fix-prompt.md`](references/fix-prompt.md) with the values filled in;
- trigger: the GitHub event "issue labeled" on `tracker.repo` when the runtime supports event triggers (Claude
  Code: a webhook trigger attached to the routine), otherwise every hour (`0 * * * *`: runs that find nothing stop
  at once);
- write its id to the profile (`routine.fixId`).

Test it on a real issue the owner chooses: they add the label, the pull request appears, they merge it.

## 9. One digest for several sites

When the owner already has other sites on the SEO factory, propose a single weekly email for all of them: set
`tracker.digest` to `none` in every profile and create (or extend) one `SEO digest` task with
[`references/digest-prompt.md`](references/digest-prompt.md), the SEO environment and every site's repository.

## 10. Hand over

Tell the owner, in a few lines:

- where to see, pause or run the task (`routine.url`), and where each run's session appears;
- what they will receive (a pull request and a message, or a deck and a message) and how often to expect it — once
  or twice a month, not every pass;
- where their actions are (`tracker.url`) and that they get the list of what waits for them every
  `tracker.digest`; that labeling any issue `claude:fix` gets it fixed in a pull request;
- what they do: merge or close the pull request, close the issue or set the row to `Done` when they did an owner
  action, or apply the recommendation and say so (the journal entry becomes `applied`);
- the next step: **`skf-seo-audit`** for a full picture and the first actions, if it has not run yet.
