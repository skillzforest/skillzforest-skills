---
name: skf-growth-report
description: Growth director's reporting for every project of the growth workspace - collects the week's measures (organic discovery, traffic, sign-ups, downloads, installs, activations, press and mentions, pipeline from first contact to opportunity, owner time and tool cost) from the analytics, Search Console, CRM, SEO scorecards and tracker, compares channels and experiments, then writes either the very short daily point (decisions waiting, tomorrow's deadlines, one alert) or the weekly review - decisions to take with their rationale, KPIs per project, experiments, proposed trade-offs between projects, missing data. Never invents a figure, reports « non mesuré » instead, and never takes a binding decision. Use it for the scheduled daily and weekly reports, or whenever someone asks how the projects are doing, what is waiting for a decision, or which channels work.
---

# Growth report

You give the owner the shortest path from what happened to what to decide. You consolidate and prioritize what the
other growth skills produced; you do not redo their work. Read first:
`../skf-growth-profile/references/guardrails.md`. Formats:
[`references/report-format.md`](references/report-format.md).

Projects: every `projects/<id>/growth.json` of the workspace, unless the request names some.

## Mode daily

1. Run `skf-growth-tracker` in mode **decisions** first: the owner's replies of the day are applied before anything
   is counted.
2. Count items in Status Decision (by priority), list tomorrow's Due items (publications, follow-ups, events) and
   at most one alert (an item stuck in Decision for more than 7 days, a deadline missed, a source down).
3. Write `reports/daily/YYYY-MM-DD.md` and update the single open tracker item « Point du jour » (type `daily`,
   growth-id `daily:all:point-du-jour`): replace its body, never open a second one. No email.

## Mode weekly

1. **Measures**, per project, for the last complete ISO week and the one before, Europe/Paris unless the profile says
   otherwise:
   - analytics from `measurement.posthog` (pageviews, unique visitors, sessions on the production hosts only; sign-up,
     download or activation events when the profile names them);
   - Search Console from `measurement.searchConsole` (clicks and impressions over 28 days ending 3 days ago); when
     the site has an SEO scorecard issue (label `seo:scorecard`), read its latest card rather than querying again;
   - `measurement.other` sources (registries, GitHub stars and release downloads, licence counts);
   - pipeline counts from the CRM (project property) and the tracker;
   - operations from the tracker: decisions asked and answered, Effort of done items.
   Write `metrics/YYYY-Www.json` per project.
2. **Read** the week's intelligence files, campaign calendars, pipeline files and strategy plans.
3. **Write** `reports/weekly/YYYY-Www.md` (format file). Decisions to take come from the items in Status Decision,
   ranked by expected impact on a goal, then confidence, then effort. Trade-offs between projects are
   recommendations, labeled as such.
4. **Publish for the owner**: when the runtime can publish a private page (an artifact, a doc), publish the review
   there, updating the same page every week; otherwise the Markdown file is the review. When a mailbox tool is
   connected and the workspace conventions name an address, create an email **draft** to the owner with the
   one-minute summary and the link; never send it.
5. On the first weekly run of a month, list the projects whose channel strategy is due for its monthly review, for
   the scheduler to run `skf-channel-strategy`.

## Guardrails

- Every figure has its source and window; a missing one is « non mesuré ».
- A drop or a rise under 20 visitors a week is not a trend.
- Recommendations never become actions: they reach the owner as tracker decisions through the skill that owns them.

## Final answer

In `reportLanguage` of the workspace (the first project's when they differ): the report and page links, decisions
waiting, the alert if any, the sources that failed and which project they concern.
