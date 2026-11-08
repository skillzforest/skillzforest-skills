---
name: skf-market-intel
description: Runs the weekly market intelligence of one or several projects of the growth workspace - market and trend changes, competitors, needs and questions audiences express in public, communities and platforms, digital and print media, journalists and sections, creators, potential partners and client companies showing a need, events, trade fairs and editorial calendars - each finding with its source URL, publication date, reading date and confidence. Writes one dated intelligence file per project and sends the opportunities worth acting on to the tracker. Works one project at a time, in parallel sub-agents when several projects are asked. Use it for the scheduled weekly watch, or whenever someone asks what is new in a project's market, who covers its topic, which communities or events matter, or what competitors did.
---

# Market intelligence

You find what changed around a project and what it could act on, with proof. Read first:
`../skf-growth-profile/references/guardrails.md`, the project's `growth.json`
(`../skf-growth-profile/references/profile.md`) and, when `seoProfile` is set, its SEO profile (pitch, facts,
topics, competitors). Output format: [`references/intel-format.md`](references/intel-format.md).

A project whose profile is missing stops here: say that `skf-growth-profile` must run first.

## Several projects

When the request covers several projects, give each project to its own sub-agent when the runtime has them (one
project per sub-agent, never two), each with only that project's folder and profile. Without sub-agents, do the
projects one after the other and start each from a clean note. Then collect the results; never merge findings of
two projects in one file.

## 1. Take stock

1. Read the last two intelligence files of the project (`intel/`), the open opportunity items of the project on the
   tracker (label `type:opportunity`, `proj:<id>`), and `strategy/decisions.md` (what the owner refused stays
   refused for 90 days).
2. Period: the 7 days ending today, and back to the previous file's date when the last run is older.
3. Budget: at most 25 searches and 40 page reads per project. Spend them where the profile's goals point.

## 2. Search

Cover each block below. Use the profile's languages and markets, its audiences' `where`, its `media.themes`,
its competitors and the SEO profile's topics as starting points. Prefer primary sources.

| Block | What to look for | Typical sources |
|---|---|---|
| Market and trends | regulation, standards, platform changes, launches that change the demand | official sites, trade press, Google Trends through the SEO profile's account (at most 3 calls) |
| Competitors | new features, prices, positioning, launches, fundraising, closures | their sites, changelogs, blogs, release notes, app stores, GitHub |
| Audience needs | questions and complaints in the audience's own words | forums, Reddit threads, GitHub issues, Q&A sites, product reviews (read pages, do not scrape) |
| Communities and platforms | where the audience gathers, its size or activity, its self-promotion rules | community pages and rules, subreddit sidebars, Discord invite pages, forum charters |
| Media | outlets and sections covering the topic recently, editorial calendars, calls for contributions | outlet sites, section pages, newsletters' archives |
| Creators | channels, podcasts, newsletters active on the topic in the last month | their public pages; when `media.creatorsSource` exists, add only new names and leave the list to its owner skill |
| Partners and companies | organizations whose public signals match the ICP or a partner kind: job ads, announcements, migrations, new products | company sites, press releases, job boards' public pages, public registries |
| Events | fairs, conferences, meetups, game jams, hackathons, awards; their dates and useful deadlines | official event pages only for dates |

Never open a page that requires an account the run does not own, never bypass a paywall, never collect a person's
private contact data.

## 3. Sort what you found

- Keep what is new since the previous file and relevant to the profile's audiences and goals. Drop the rest; list
  important dead ends in « Non trouvé ou non vérifié ».
- Each kept item: source URL, publication date, reading date, confidence. A claim with no source becomes a
  hypothesis or is dropped.
- An **opportunity** is a concrete action the project could take because of a finding: a media section covering the
  topic, a community thread asking for exactly what the product does, an event with an open call, a company showing
  the need, a competitor gap. At most 5 per project per week, the strongest first.

## 4. Write and log

1. Write `projects/<id>/intel/YYYY-Www.md` (format file). Commit it to the workspace's default branch.
2. Send each opportunity to the tracker through `skf-growth-tracker` (mode log): type `opportunity` (or `media`,
   `prospect` when the finding is an outlet or an organization), Status To qualify, Pole Market Intel, Nature and
   Channel set, Priority from the profile's goals, Confidence from the sources, Horizon 30 d when it can be acted on
   within a month. Body: the finding, why now, the sources.
3. People found (journalists, creators, contacts) are not written in GitHub: name the outlet or the channel, and leave
   the person to `skf-prospect-pipeline` or the creator skill.

## 5. Final answer

In the profile's `reportLanguage`, per project: the file link, three lines on what matters, the opportunities sent
(issue links), sources that failed, and anything the owner must do (an access to grant, a doubt to settle).
