---
name: skf-prospect-pipeline
description: Finds and qualifies business opportunities for one project of the growth workspace - client companies, distribution and integration partners, prescribers and media outlets - from legal public sources, keeps the provenance of every piece of information, looks for dated need or interest signals, scores each organization with a fixed grid (fit, signal, potential, feasibility, confidence), classifies A, B or C, removes duplicates against the CRM and the tracker, records organizations and professional contacts in the CRM under the project's property, and proposes the best ones to the owner as tracker decisions. Targeted and capped every week, never bulk lists, never B2C individuals. Use it for the weekly prospecting run, or whenever someone asks to find prospects, partners, distributors or media for a project, or to qualify a list of companies.
---

# Prospect pipeline

You build a short, well-sourced list of organizations worth contacting, never a database. Read first:
`../../../marketing/content/skf-growth-profile/references/guardrails.md` (People, above all), the project's
`growth.json` (`icp`, `partners`, `media`, `outreach`), the last intelligence files, the previous pipeline files and
the decision log. Grid and file format: [`references/lead-scoring.md`](references/lead-scoring.md).

The profile must be `validated` before anything is written to the CRM; with a `draft` profile, write the pipeline
file only.

## 1. Take stock

1. Organizations already known: the CRM records with the project's property (`outreach.crm`), the tracker items
   labeled `type:prospect` or `type:media` for the project (open and closed), and the pipeline files. A closed REJECT
   or a recorded opposition excludes the organization.
2. This week's room: `outreach.maxNewContactsPerWeek` minus the people added this week.

## 2. Discover

Start from the intelligence signals of the last weeks (Partners and companies, Media), then search for the ICP:
industry directories, member lists of trade associations, exhibitor lists of the profile's events, integration or
partner directories of the platforms the product works with, outlets' section pages, public job ads that reveal the
need. Read the organization's own site before keeping it. Record for each fact the URL and the date read.

Allowed: public pages, official registries, the organization's own pages, public professional profiles published by
the person. Not allowed: logging into a platform to extract profiles, scraping sites whose terms forbid it, buying or
importing lists, guessing email patterns.

## 3. Qualify

Score with the grid, write one line of reason per criterion, classify. Keep at most 10 A and B organizations per run
and project. For each kept one, name the role to reach and the legitimate contact route (contact form, press
address, partner program, public professional address). When no legitimate route exists, feasibility is 0.

## 4. Record

1. Pipeline file `pipeline/YYYY-Www.md`, organizations only, committed to the workspace.
2. CRM (profile `validated`): for each A organization, a company record (name, domain, industry, source URL, score,
   class, signal) and, when a legitimate professional contact was found, a contact record linked to it (name, role,
   professional address, source URL, legal basis « intérêt légitime B2B » for EU business contacts), both with the
   project property set to the profile's value. Search the CRM by domain first: update, never duplicate. Never
   create a record for a private individual.
3. Tracker, through `skf-growth-tracker` (mode log): one item per A organization, type `prospect` (or `media`),
   growth-id `prospect:<project>:<domain>`, Status Decision, label `decision:pending`, Pole BizDev, Nature Prospect
   or Media/Partner, Score, Confidence, Effort, with the decision layout: opportunity, kind, signal, why now, proposed
   approach (channel, angle, offer), risks, recommendation, link to the CRM record. No personal data in the issue.

When a project uses HubSpot for the first time, check that the project property exists on companies and contacts; if
it does not, create it (internal CRM setting, no outside effect) and say so in the report.

## 5. Final answer

In `reportLanguage`: organizations proposed (issue links, class, one line each), CRM records created or updated,
organizations set aside and why, the room left this week, sources that failed.
