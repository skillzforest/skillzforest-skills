# skills/

This is the **canonical source of truth** for every Agent Skill in SkillzForest. Nothing outside this folder may hold an independently maintained copy of a skill — `packs/`, `runtimes/`, and `dist/` only reference or generate from what lives here.

## Layout

```text
skills/<family>/<skill-name>/
├── SKILL.md        # required — the skill's business content (the actual prompt/logic)
├── skill.json      # required — SkillzForest metadata + runtime compatibility (see schemas/skill.schema.json)
├── scripts/        # optional — skill-owned automation
├── references/      # optional — supporting material read by the skill
├── templates/       # optional — reusable structural templates
├── masters/          # optional — master documents the skill fills/copies
└── assets/           # optional — static assets
```

A skill exists exactly once, under the family that matches its name prefix, and its `id` is always runtime-agnostic — `dev-seo`, never `claude-dev-seo` or `codex-dev-seo`. Which runtimes it actually works on is declared in `skill.json`'s `compatibility` map (see [`runtimes/README.md`](../runtimes/README.md)), not baked into its name or location.

## Families

| Prefix | Folder | Scope |
|---|---|---|
| `av-*` | `av/` | Avant-vente / pre-sales |
| `product-*` | `product/` | Product & functional scoping |
| `board-*` | `board/` | Backlog, tickets, sprint, tracking |
| `ux-*` | `ux/` | User experience & journeys |
| `ui-*` | `ui/` | Interface & design system |
| `arch-*` | `arch/` | Architecture |
| `dev-*` | `dev/` | Development & code quality |
| `data-*` | `data/` | Data |
| `ai-*` | `ai/` | AI |
| `sec-*` | `sec/` | Cross-cutting security |
| `qa-*` | `qa/` | Validation / QA / regression |
| `release-*` | `release/` | Release & deployment |
| `infra-*` | `infra/` | Infrastructure / CI-CD / cloud |
| `ops-*` | `ops/` | Operations |
| `growth-*` | `growth/` | Acquisition / growth |
| `billing-*` | `billing/` | Monetization / subscriptions |
| `legal-*` | `legal/` | Compliance / legal |
| `docs-*` | `docs/` | Documentation |

Only `av/` currently contains real skills (the Pre-Sales Pack, see [`packs/presales/pack.json`](../packs/presales/pack.json)). The other families are placeholders, ready to receive skills as they are built — see each family's `README.md`.

## Rules

1. A skill exists once, in one family folder, under one runtime-agnostic id.
2. A skill contains no runtime-specific logic (no Claude-Code-only or Codex-only behavior) unless that logic is intrinsic to the skill itself — runtime adaptation belongs in `runtimes/`.
3. A skill contains no orchestration logic — that belongs in `workflows/`.
4. Packs, bundles and runtimes only reference skills by name; they never copy skill files.
5. `skill.json`'s `compatibility` map only ever records what's actually been verified — see [`runtimes/README.md`](../runtimes/README.md) for the `native`/`supported`/`adapted`/`unsupported`/`unknown` distinction.
6. Run `npm run validate` before committing changes here — it checks for missing `SKILL.md`/`skill.json`, duplicate ids, prefix/category mismatches, invalid compatibility values, and broken pack/runtime references.
