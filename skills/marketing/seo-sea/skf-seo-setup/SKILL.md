---
name: skf-seo-setup
description: Turns a validated .seo/profile.json into a running SEO agent — checks the workspace (the site's Git repository, or a dedicated seo-SITE repository for sites on a CMS), connects and tests each source and output named in the profile (Google Search Console, SerpApi for Google Trends, Gmail, Outlook or Slack, Google Slides, GitHub), creates the journal, reports folder and backlog, then schedules the recurring skf-seo-pass as a cloud task (a Claude Code routine) that reads the skills from the SkillzForest skills repository, and runs it once to prove it works. Use it right after skf-seo-profile, when a connection breaks, when the cadence or notification changes, or whenever someone asks to schedule, automate or (re)connect their SEO agent, or runs /skf-seo-setup.
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
- `paths.reports` (with a `.gitkeep`);
- `paths.backlog` with a heading and an empty checklist.

Commit them with the profile: mode `repo` through a pull request the owner merges (or directly when they say so),
mode `advise` on the workspace's base branch.

## 5. Schedule the pass

1. Turn `cadence.schedule` into a cron **in UTC** and confirm it with the owner in their local time ("08:00 Paris
   = 07:00 UTC in winter, 06:00 in summer — the task stays on UTC"). Every 2 days: `0 7 */2 * *` (odd days of the
   month; the 31st and the 1st run back to back). Write it to `cadence.cron`.
2. Create the scheduled task with the runtime's scheduling tool (Claude Code: the `schedule` skill / routines):
   - name `SEO <site.name>`;
   - repositories: the workspace **and** the skills repository;
   - connectors: Composio (and any other the profile needs);
   - model: a capable, economical one (Claude Sonnet) unless the owner prefers otherwise;
   - tools: shell, file read/write/edit, search, web search and fetch, skills;
   - prompt: [`references/routine-prompt.md`](references/routine-prompt.md) with the values filled in.
3. Write `routine.id`, `routine.url` and `routine.skillsRepo` to the profile and commit.
4. Run the task once now and read its log: it must reach Search Console (or say why not), respect the cadence, and
   end with a clear answer. Fix and rerun until it does.

No scheduling tool in this runtime: give the owner the prompt and the cron to paste into their scheduler, and say
the pass can always be run by hand with `skf-seo-pass`.

## 6. Hand over

Tell the owner, in a few lines:

- where to see, pause or run the task (`routine.url`), and where each run's session appears;
- what they will receive (a pull request and a message, or a deck and a message) and how often to expect it — once
  or twice a month, not every pass;
- what they do: merge or close the pull request, or apply the recommendation and say so (the journal entry becomes
  `applied`);
- the next step: **`skf-seo-audit`** for a full picture and a backlog, if it has not run yet.
