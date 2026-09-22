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
  "id": "presales",
  "name": "Pre-Sales Pack",
  "publisher": "SkillzForest",
  "version": "0.1.0",
  "description": "...",
  "skills": ["av-devis", "av-cadrage-fonctionnel"]
}
```

A pack **only references** skills by name — it never embeds a copy of a skill's files. Skills are resolved from [`skills/`](../skills/) at build time by [`scripts/build-pack.js`](../scripts/build-pack.js).

## Packs in this repository

| Pack | Status |
|---|---|
| [`presales`](presales/pack.json) | Active — the existing `av-*` pre-sales skills |
| [`saas-builder`](saas-builder/pack.json) | Skeleton — no skills assigned yet |
| [`saas-ops`](saas-ops/pack.json) | Skeleton — no skills assigned yet |

## Building a pack

```bash
npm run build:pack -- presales
```

This reads `packs/presales/pack.json`, resolves each listed skill from `skills/`, and — for every runtime at least one of its skills is compatible with (see [`runtimes/`](../runtimes/)) — builds a distribution per skill and assembles them under `dist/packs/presales/<runtime>/`:

```text
dist/packs/presales/
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

A runtime with no verified/implemented adapter for any of the pack's skills (e.g. `codex` today) is simply absent from `dist/packs/presales/` — nothing fictional gets built. The command never modifies anything under `skills/`, `packs/`, or `runtimes/`.
