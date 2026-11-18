---
name: skf-channel-strategy
description: Builds and reviews the channel strategy of one project of the growth workspace - detects its communication channels (owned, social, community, earned, events, paid) and distribution channels (stores, registries, directories, partners, direct sales, product-led) down to the exact places where an action can happen, scores each channel with a fixed grid, then lists and scores the concrete marketing actions possible on each kept channel, makes each action measurable (UTM, events, store counters) and records it so its impact is measured after its window, decides to launch, test, strengthen, reduce, watch or drop, and writes the 30 day and 90 day plans. Proposals go to the owner as tracker decisions. Use it for the monthly strategy review, after a profile is validated, or whenever someone asks which channels a project should use, how often to post, or what to test next.
---

# Channel strategy

You decide where a project should speak and be available, which actions to run there first, and how each action will
be judged. Read first: `../skf-growth-profile/references/guardrails.md`, the project's `growth.json`, its SEO profile
when set, the last four intelligence files (`intel/`), the measures (`metrics/`), the decision log
(`strategy/decisions.md`), the current strategy files if any, and the open tracker items of the project. References:
[`references/channel-map.md`](references/channel-map.md) (families, places, detection),
[`references/scoring.md`](references/scoring.md) (channel grid) and
[`references/action-scoring.md`](references/action-scoring.md) (action grid, tracking, impact).

A profile in `draft` gets a proposal only: everything is written, nothing is logged as Approved.

## 1. Detect the channels

Follow the detection order of the channel map, for both families: **communication** (make the product known) and
**distribution** (put it in the users' hands). Go down to the places inside each channel, each with its link, read
date, persona, format, rules, account, automation and what can be measured there.

SEO is already handled by the SEO skills: count it as an owned channel for the plan (its articles feed campaigns and
actions), never plan SEO work here.

## 2. Score the channels

Score every channel with the channel grid, one line of reason per criterion, then the verdict. Do not assume that
what suits one project suits another: a B2B project rarely needs TikTok, a retro gaming tool rarely needs LinkedIn
ads. The measured signal comes from the verdicts of the channel's actions (action-scoring, Impact).

## 3. Find the best actions inside each channel

For every channel scored test, launch or strengthen: list the actions possible on its places, score them with the
action grid, keep at most 3 per channel and 10 per project. Link each one to the goal it serves, define its tracking,
its window, its success threshold and its stop criterion. An open tracker item that already describes an action is
linked to it, never duplicated. Record everything in `strategy/actions.json`, keeping the actions already there with
their status and results.

## 4. Write the strategy files

In the profile's `reportLanguage`:

- `strategy/channel-map.md`: the map by family, group, channel and place, with each channel's score and verdict and
  its kept actions (format in the channel map reference).
- `strategy/channels.md`: table Family · Channel · Persona · Score (with the criterion breakdown) · Verdict ·
  Format · Frequency · Account status · Automation (allowed / manual, with the terms link) · Next step; below it, the
  channels dropped and why.
- `strategy/actions.json`: the action records.
- `strategy/plan-30d.md`: the kept actions in order (action, channel and place, owner time, due week, metric and
  threshold), measurement gaps to close first, existing content to reuse, first media and partners, first prospect
  segments (B2B), success indicators.
- `strategy/plan-90d.md`: channels to run on a cadence, actions that became cadences, publication calendar by week,
  press and partnership relationships, prospecting strategy, assets to prepare, resources and possible costs
  (marked « à valider »), expected results and stop criteria.

Label every line **fait** (sourced), **hypothèse** or **reco** (in the report language).

## 5. Propose to the owner

Through `skf-growth-tracker` (mode log): one decision item per structuring choice (a channel to launch or drop, a
cost) and one per kept action that is public or binding and not yet on the tracker. Type `channel`, Nature Channel
strategy, Status Decision, label `decision:pending`, Pole Marketing (BizDev for partner and outreach actions), growth-id
the action id, with project, opportunity, channel and place, expected outcome, rationale, sources, effort,
confidence, risks, tracking and window, recommendation and the link to the strategy file. A measurement gap is one
item of Nature Opportunity. Minor technical choices are not decisions.

Open a pull request with the strategy files in the workspace when they changed (branch `growth/strategy-<id>-<date>`).

## 6. Monthly review

When strategy files exist: read the action verdicts written by `skf-growth-report`, update each channel's measured
signal, apply the drop and cadence rules of action-scoring, replace finished or dropped actions with the next best
ones, and say in the plan what changed since last month and why.

## Final answer

In `reportLanguage`: the pull request link, per family the channels with their verdict in one line, the top actions
per project with their score, the decisions waiting (issue links), and the measurement gaps.
