---
name: skf-growth-profile
description: Builds or updates the growth profile of one project (projects/ID/growth.json in the growth workspace) - who it serves, its audiences and personas, its B2B ideal customer profile, its 30 and 90 day goals and how they are measured, the channels it may use and the accounts it already has, its outreach limits and CRM, and the open questions for its owner. Starts from what the site and the project's SEO profile already say, never invents, marks every proposal as a hypothesis, and hands the profile to the owner for validation as a pull request. Every other skf-growth skill reads this profile first. Use it when a project joins the growth workspace, when its positioning, audience, goals or channels change, or when someone asks to set up or review a project's growth profile.
---

# Growth profile

You write the one file every growth skill reads before acting on a project: `projects/<id>/growth.json` in the
growth workspace. Format: [`references/profile.md`](references/profile.md). Workspace layout:
[`references/workspace.md`](references/workspace.md). Rules shared by every growth skill:
[`references/guardrails.md`](references/guardrails.md), read them first.

**Which project**: the one named in the request. When it is not obvious, ask. One run, one project, unless the
request lists several (then one profile per project, never mixed).

## 1. Gather what already exists

Read, in this order, and note for each fact where you read it:

1. The existing `growth.json`, if any (an update keeps everything the owner wrote: `basis: owner`).
2. The project's SEO profile (`.seo/profile.json` in the site's repository) when there is one: pitch, audience,
   business, languages, facts, topics, competitors, style rules. Set `seoProfile` to point at it and do not copy
   these fields.
3. The live site: home page, pricing, features, use cases, about, documentation (fetch each page you rely on).
4. Other profiles of the same project in the owner's repositories when the request or the SEO profile points to them
   (a skf-social profile, a README, a press kit). Set `channels.socialProfile` and `media.creatorsSource` to them
   rather than copying their lists.
5. Measurement sources the owner already uses (analytics project ids, Search Console property), only from the
   owner's files or what the owner says.

When two sources disagree (one says open source, another says proprietary), do not choose: write the contradiction
in `openQuestions`.

## 2. Write the profile

- `model`, `stage`: from the site (a waiting page is `prelaunch`).
- `audiences`: who the site addresses, plus partner and prescriber audiences that a growth plan needs (integrators,
  media, creators, publishers). `where` lists real places where they gather, found in this run (with the URL in your
  report), not guesses.
- `personas`: two to four per project, each tied to an audience; pains, triggers and objections drawn from the
  site's own words, its FAQ and public discussions you read; mark the rest `hypothesis`.
- `icp` (B2B): industries, size, roles and buying signals that the site's use cases support; disqualifiers that save
  wasted outreach.
- `goals`: one or two per horizon, each with a metric that a listed source can measure. Leave `target` at `null`
  unless the owner gave one: targets are the owner's call. `baseline` comes from data read in this run, else `null`.
- `channels.candidates`: channels where the audiences are, without scoring them (skf-channel-strategy scores).
  `excluded` only with a reason grounded in the profile (audience absent, terms forbid it, owner's choice).
- `outreach`: `b2cDirect` is always `false`; `b2bEmail` only for projects that sell to organizations; leave
  `sender` at `null` until the owner names a mailbox.
- `measurement.unavailable`: every metric a goal needs that no source gives yet.
- `openQuestions`: what blocks validation, phrased as questions the owner can answer in one line.
- `status`: `draft`. Only the owner moves it to `validated` (by merging, or by saying so).

## 3. Check and hand over

1. `python3 scripts/validate_growth_profile.py projects/<id>/growth.json` until it reports no error.
2. Re-read each `basis: site` or `seo-profile` item against its source; downgrade to `hypothesis` what you cannot
   point to.
3. Commit on a branch `growth/profile-<id>-<date>` and open a pull request in the workspace. Body: what the profile
   says in five lines, the sources read (links), the hypotheses to confirm and the open questions.
4. Final answer in the profile's `reportLanguage`: the pull request link, the open questions, and what the owner must
   decide before the other growth skills can act outside the workspace.
