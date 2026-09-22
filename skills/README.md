# skills/

This is the **canonical source of truth** for every Agent Skill in SkillzForest. Nothing outside this folder may hold an independently maintained copy of a skill — `packs/`, `runtimes/`, and `dist/` only reference or generate from what lives here.

## Layout

```text
skills/<domain>/<skill-name>/
skills/<domain>/<subcategory>/<skill-name>/   # only for a domain that declares subcategories (e.g. development)
├── SKILL.md        # required — the skill's business content (the actual prompt/logic)
├── skill.json      # required — SkillzForest metadata + runtime compatibility (see schemas/skill.schema.json)
├── scripts/        # optional — skill-owned automation
├── references/      # optional — supporting material read by the skill
├── templates/       # optional — reusable structural templates
├── masters/          # optional — master documents the skill fills/copies
└── assets/           # optional — static assets
```

A skill exists exactly once, under the **domain** (and, where relevant, **subcategory**) its name prefix belongs to (see below), and its `id` is always runtime-agnostic — `dev-seo`, never `claude-dev-seo` or `codex-dev-seo`. Which runtimes it actually works on is declared in `skill.json`'s `compatibility` map (see [`runtimes/README.md`](../runtimes/README.md)), not baked into its name or location.

## Domains

Skills are grouped into **8 domains**, named in plain English — the same buckets a buyer sees in the SkillzForest catalog, not internal engineering jargon, and English so the catalog reads the same in every market. The registry is [`skills/domains.json`](./domains.json) (schema: [`schemas/domain.schema.json`](../schemas/domain.schema.json)); this table is its human-readable mirror. A domain can accept several technical prefixes directly, or split into named **subcategories** one folder level deeper when it's broad enough to need it (today, only `development/`).

| Domain folder | Name (buyer-facing) | Accepted prefixes | Scope |
|---|---|---|---|
| `sales/` | Sales & Presales | `av-` | Quotes, client scoping, presentations, meeting notes |
| `marketing/` | Marketing & Communication | `growth-` | Content, social media, advertising |
| `finance/` | Finance & Billing | `billing-` | Invoicing, payments, subscriptions |
| `hr/` | HR & Recruiting | `hr-` | Job postings, candidate screening, onboarding |
| `customer-support/` | Customer Support | `support-` | Inbox, tickets, reviews |
| `project-management/` | Project Management | `board-`, `docs-` | Backlog, sprints, reporting, documentation |
| `legal/` | Legal & Compliance | `legal-` | Contracts, GDPR, regulatory compliance |
| `development/` | Development & Engineering | see subcategories below | Product, design, dev, data, AI, QA, infra, ops, release, security |

### `development/` subcategories

Broad enough on its own that a buyer benefits from a finer split, and specific enough internally that the people building skills still need the old technical distinctions:

| Subcategory folder | Name | Accepted prefixes | Scope |
|---|---|---|---|
| `development/seo/` | SEO | `seo-` | Technical and content search-engine optimization |
| `development/code/` | Code | `product-`, `arch-`, `dev-`, `data-`, `ai-`, `qa-`, `infra-`, `ops-`, `release-`, `sec-`, `github-` | Product scoping, architecture, development, data, AI, QA, infra, ops, release, security |
| `development/ux-ui/` | UX/UI | `ux-`, `ui-` | User experience, journeys, interface, design system |

Only `sales/` and `development/code/` currently contain real skills — see [`packs/sales/pack.json`](../packs/sales/pack.json) and [`packs/development/pack.json`](../packs/development/pack.json). The other domains (and `development/seo/`, `development/ux-ui/`) are placeholders, created ahead of need so the catalog's shape is already right — see each domain's `README.md`.

Each of the 8 domains has exactly one matching pack under `packs/<domain-id>/pack.json` — the domain is the engineering-side grouping, the pack is what's actually sold, and today they're 1:1. That's a convenience for a small catalog, not a rule: nothing stops a future pack from bundling skills across several domains, or a domain from being split across several packs, once there's enough content to make that useful.

## Standalone skills (no domain)

A directory directly under `skills/<skill-name>/` that itself contains a
`SKILL.md` is a **standalone skill** — a generic Claude Code Agent Skill
meant to be invoked directly by its own name, not part of the commercial
pack/runtime distribution system the domain convention above exists for. It
follows Anthropic's standard `skills/<skill-name>/SKILL.md` layout as-is: no
name prefix, and `skill.json` is optional (only add one if the skill will
actually be distributed through a pack). `scripts/validate.js` and
`scripts/lib/skills.js` both know the difference between a domain (a folder
whose immediate children are skills, or subcategories of skills) and a
standalone skill (a folder that is itself a skill).

No standalone skill exists today — `github-issue-context` and
`github-implement-issue` (Claude Code developer tooling for turning a
GitHub Issue into a context bundle and then implementing it) started this
way but now live under
[`skills/development/code/`](./development/code/), since they're
genuinely part of the Development & Engineering catalog. The mechanism
stays documented here for whenever a future skill is generic enough to
warrant it.

## Rules

1. A skill exists once, in one domain (and, where relevant, subcategory) folder, under one runtime-agnostic id.
2. A skill's name prefix must be one of the prefixes `skills/domains.json` registers for the domain (or subcategory) folder it lives in — `npm run validate` enforces this.
3. A skill contains no runtime-specific logic (no Claude-Code-only or Codex-only behavior) unless that logic is intrinsic to the skill itself — runtime adaptation belongs in `runtimes/`.
4. A skill contains no orchestration logic — that belongs in `workflows/`.
5. Packs, bundles and runtimes only reference skills by name; they never copy skill files.
6. `skill.json`'s `compatibility` map only ever records what's actually been verified — see [`runtimes/README.md`](../runtimes/README.md) for the `native`/`supported`/`adapted`/`unsupported`/`unknown` distinction.
7. Run `npm run validate` before committing changes here — it checks for missing `SKILL.md`/`skill.json`, duplicate ids, prefix/domain mismatches, invalid compatibility values, and broken pack/runtime references.
