# packs/

A pack is a commercial product bundling several coherent skills, sold and distributed through SkillzForest.

```text
packs/<pack-id>/
├── pack.json   # metadata + skill references
└── docs/       # optional — pack-level supporting documentation (never skill copies)
```

`pack.json` fields (see [`schemas/pack.schema.json`](../schemas/pack.schema.json)):

```json
{
  "schemaVersion": 1,
  "id": "sales",
  "name": "Sales & Presales",
  "publisher": "SkillzForest",
  "version": "0.1.0",
  "description": "...",
  "skills": ["av-devis", "av-cadrage-fonctionnel"]
}
```

A pack **only references** skills by name — it never embeds a copy of a skill's files. Skills are resolved from [`skills/`](../skills/) at build time by [`scripts/build-pack.js`](../scripts/build-pack.js).

## Packs in this repository

Packs are the **commercial, buyer-facing** view of the catalog — one pack per domain in [`skills/domains.json`](../skills/domains.json), named in plain English. A pack name is meant to be understood in a few seconds by anyone (an enterprise buyer, a freelancer, or the general public), regardless of the technical skill prefixes or subcategories it happens to bundle underneath.

| Pack | Domain | Status |
|---|---|---|
| [`sales`](sales/pack.json) | Sales & Presales | Active — the existing `av-*` skills |
| [`marketing`](marketing/pack.json) | Marketing & Communication | Skeleton — no skills assigned yet |
| [`finance`](finance/pack.json) | Finance & Billing | Skeleton — no skills assigned yet |
| [`hr`](hr/pack.json) | HR & Recruiting | Skeleton — no skills assigned yet |
| [`customer-support`](customer-support/pack.json) | Customer Support | Skeleton — no skills assigned yet |
| [`project-management`](project-management/pack.json) | Project Management | Skeleton — no skills assigned yet |
| [`legal`](legal/pack.json) | Legal & Compliance | Skeleton — no skills assigned yet |
| [`development`](development/pack.json) | Development & Engineering | Active — `github-issue-context`, `github-implement-issue` |

## Building a pack

```bash
npm run build:pack -- sales
```

This reads `packs/sales/pack.json`, resolves each listed skill from `skills/`, and — for every runtime at least one of its skills is compatible with (see [`runtimes/`](../runtimes/)) — builds a distribution per skill and assembles them under `dist/packs/sales/<runtime>/`:

```text
dist/packs/sales/
├── claude-code/
│   ├── pack.json
│   ├── pack-distribution.json
│   ├── av-devis/
│   └── ...
└── claude-ai/
    ├── pack.json
    ├── pack-distribution.json
    ├── av-devis/          # contains av-devis-0.1.0.skill
    └── ...
```

A runtime with no verified/implemented adapter for any of the pack's skills (e.g. `codex` today) is simply absent from `dist/packs/sales/` — nothing fictional gets built. The command never modifies anything under `skills/`, `packs/`, or `runtimes/`.
