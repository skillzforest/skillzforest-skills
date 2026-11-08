# Growth profile (`projects/<id>/growth.json`)

One file per project. Every growth skill reads it first. It says who the project serves, what it wants, where it may
speak and how it is measured. It never repeats what the project's SEO profile (`.seo/profile.json`, skf-seo-profile)
already holds: when `seoProfile` is set, the pitch, facts, topics, competitors and writing rules are read there.

Check a profile: `python3 scripts/validate_growth_profile.py projects/<id>/growth.json`.

## Fields

| Field | Required | Meaning |
|---|---|---|
| `schemaVersion` | yes | `1` |
| `id` | yes | project slug, equal to the folder name |
| `name` | yes | brand name, written as the brand writes it |
| `status` | yes | `draft` (proposed by the agent) or `validated` (the owner approved it); skills that act outside the workspace require `validated` |
| `reportLanguage` | yes | language of reports, drafts for the owner and issues (`fr`, `en`) |
| `site.url` | yes | main site |
| `site.languages` | yes | languages the site really serves, e.g. `["fr", "en"]` |
| `seoProfile` | no | `{ "repo": "owner/name", "path": ".seo/profile.json" }`: source of pitch, facts, topics, competitors, style rules |
| `pitch`, `business` | when no `seoProfile` | one sentence each, taken from the site |
| `model` | yes | `b2b`, `b2c`, `b2b2c`, `community` or `marketplace` |
| `stage` | yes | `prelaunch`, `launched` or `growing` |
| `goals[]` | yes | `{ id, horizon: "30d"/"90d", objective, metric, baseline, target, basis }`; `baseline` and `target` are numbers or `null` (not measured / not set) |
| `audiences[]` | yes | `{ id, name, kind: "customer"/"user"/"partner"/"prescriber"/"publisher", description, where[], basis }`; `where` = places this audience can be met (communities, media, events, marketplaces) |
| `personas[]` | yes | `{ id, audience, name, role, job, pains[], triggers[], objections[], basis }` |
| `icp` | when `model` has b2b | `{ industries[], companySize, geos[], roles[], signals[], disqualifiers[] }`: who is worth prospecting and what shows a need |
| `partners[]` | no | `{ kind, why, examples[] }`: distribution, technology, integration, reseller partners worth looking for |
| `channels` | yes | `{ candidates[], excluded[{ id, reason }], accounts[{ platform, handle, status }], socialProfile }`; `status` = `active`, `to-create`, `paused`, `unknown`; `socialProfile` = `"owner/repo:path"` of a skf-social profile when one exists |
| `media` | no | `{ languages[], themes[], creatorsSource }`: what press and creators to look for; `creatorsSource` = where the creator list already lives |
| `outreach` | yes | `{ b2bEmail, b2cDirect, maxNewContactsPerWeek, maxFirstMessagesPerWeek, sender, crm }` (below) |
| `measurement` | yes | `{ posthog, searchConsole, other[], unavailable[] }` (below) |
| `constraints[]` | no | rules on top of the SEO profile's style rules (claims to avoid, words to use) |
| `competitors[]` | no | when no SEO profile lists them: `{ name, url }` |
| `assets[]` | no | `{ kind, ref }`: reusable material (video repository, screenshots, demo, press kit) |
| `openQuestions[]` | no | what the owner must answer before `validated` |

`basis` (goals, audiences, personas) says where an item comes from: `site` (read on the site), `seo-profile`,
`owner` (stated by the owner), `data` (measured) or `hypothesis` (the agent's proposal, to confirm). A profile can
be `validated` with hypotheses left in it: the owner accepts them as working assumptions.

### `outreach`

| Field | Meaning |
|---|---|
| `b2bEmail` | `true` when the project prospects organizations by email (B2B), `false` otherwise |
| `b2cDirect` | always `false`: no cold message to private individuals (guardrails.md) |
| `maxNewContactsPerWeek` | ceiling of new people added to the CRM per week (default 15) |
| `maxFirstMessagesPerWeek` | ceiling of first messages the owner is asked to approve per week (default 5) |
| `sender` | `{ channel: "gmail"/"manual", account, address }` or `null` when not decided; with `null`, drafts are delivered as text to paste |
| `crm` | `{ type: "hubspot", projectProperty, value }` or `{ type: "none" }`; `projectProperty` is the CRM property that keeps projects apart |

### `measurement`

| Field | Meaning |
|---|---|
| `posthog` | `{ via: "mcp"/"composio"/"none", account, organizationId, projectId, host }` |
| `searchConsole` | `{ via: "composio"/"none", account, property }`; usually the SEO profile's |
| `other[]` | `{ metric, source, how }`: downloads, GitHub stars, licences, Discord members… |
| `unavailable[]` | metrics the goals need but no source gives yet (each one is reported « non mesuré ») |

## Example

`templates/growth.example.json`.
