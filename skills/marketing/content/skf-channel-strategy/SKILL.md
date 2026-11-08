---
name: skf-channel-strategy
description: Builds and reviews the distribution strategy of one project of the growth workspace - maps the channels where its audiences really are (communities, forums, social networks, video, newsletters, press, marketplaces and directories, events, partnerships, direct B2B email, SEO already handled elsewhere), scores each one with a fixed grid (reach, fit, impact on a goal, owner effort, cost, platform constraints, measured results), decides to launch, test, strengthen, reduce, watch or drop it, sets formats and frequencies, designs bounded experiments with stop criteria, and writes the 30 day and 90 day plans. Proposals go to the owner as tracker decisions. Use it for the monthly strategy review, after a profile is validated, or whenever someone asks which channels a project should use, how often to post, or what to test next.
---

# Channel strategy

You decide where a project should speak, how often, and what to test, with evidence. Read first:
`../skf-growth-profile/references/guardrails.md`, the project's `growth.json`, its SEO profile when set, the last
four intelligence files (`intel/`), the measures (`metrics/`), the decision log (`strategy/decisions.md`) and the
current strategy files if any. Grid: [`references/scoring.md`](references/scoring.md).

A profile in `draft` gets a proposal only: everything is written, nothing is logged as Approved.

## 1. Map the channels

Start from `channels.candidates` and the audiences' `where`, then add what the intelligence files found. For each
channel note: which persona is there (with the source), the format that works there, the self-promotion rules read on
the place itself (link), whether an account exists (`channels.accounts`), and whether posting can be automated within
the platform's current terms (link to the page read; else « manuel »).

SEO is already handled by the SEO skills: count it as a channel for the plan (its articles feed campaigns), never plan
SEO work here.

## 2. Score and decide

Score every channel with the grid, write the reason for each criterion in one line, then the verdict. Do not assume
that what suits one project suits another: a B2B project rarely needs TikTok, a retro gaming tool rarely needs
LinkedIn ads.

## 3. Write the strategy files

In the profile's `reportLanguage`:

- `strategy/channels.md`: table Channel · Persona · Score (with the criterion breakdown) · Verdict · Format ·
  Frequency · Account status · Automation (allowed / manual, with the terms link) · Next step; below it, the channels
  dropped and why.
- `strategy/plan-30d.md`: immediately usable opportunities, channels to test, existing content to reuse (merged SEO
  articles and guides, demos, videos in `assets`), first media and partners, first prospect segments (B2B), low
  effort campaigns, success indicators. Each line: action, channel, owner time, due week, metric.
- `strategy/plan-90d.md`: channels to run on a cadence, the publication calendar by week, press and partnership
  relationships to build, targeted prospecting strategy, content and assets to prepare, resources and possible costs
  (marked « à valider »), expected results and stop criteria.

Label every line **fait** (sourced), **hypothèse** or **reco** (in the report language).

## 4. Propose to the owner

Through `skf-growth-tracker` (mode log), one decision item per structuring choice: a channel to launch, an
experiment, a channel to drop, a cost. Type `channel`, Nature Channel strategy, Status Decision, label
`decision:pending`, Pole Marketing, with project, opportunity, channel, expected outcome, rationale, sources, effort,
confidence, risks, recommendation and the link to the strategy file. Minor technical choices (file layout, posting
time within a slot) are not decisions.

Open a pull request with the three files in the workspace when they changed (branch `growth/strategy-<id>-<date>`).

## 5. Monthly review

When strategy files exist: compare each experiment with its stop criterion using `metrics/`, apply the reduce or
drop rule, update scores with the measured signal, and say in the plan what changed since last month and why.

## Final answer

In `reportLanguage`: the pull request link, the verdict per channel in one line, the decisions waiting (issue links),
and the data that was missing.
