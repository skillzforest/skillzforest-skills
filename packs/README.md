# packs/

A pack is a commercial product bundling several coherent skills, sold and distributed through SkillzForest.

```text
packs/<category>/<subcategory>/<pack-id>/
├── pack.json   # metadata + skill references
└── docs/       # optional — pack-level supporting documentation (never skill copies)
```

Packs are filed like skills: under the site category and subcategory they're listed in (see [`skills/domains.json`](../skills/domains.json)), with the pack's catalog slug as its folder name and `id`. `pack.json`'s `category` and `subcategory` match its folders — `npm run validate` enforces it. Folder names are lowercase slugs: no spaces, no accents, hyphens between words.

`pack.json` fields (see [`schemas/pack.schema.json`](../schemas/pack.schema.json)):

```json
{
  "schemaVersion": 1,
  "id": "presales-scoping",
  "name": "Presales Scoping Pack",
  "publisher": "SkillzForest",
  "category": "development",
  "subcategory": "code",
  "version": "0.1.0",
  "description": "...",
  "skills": ["presales-quote", "presales-functional-scoping"]
}
```

When the skills build on each other (the second works from what the first produced), set `"ordered": true`: `skills` is then the order to use them in, and the site and the Manager show them as numbered steps — mirror it with the back office's « Les skills s'utilisent dans cet ordre » box. `github-issue-resolver` is ordered (context, then fix); `presales-scoping` is not.

A pack **only references** skills by name — it never embeds a copy of a skill's files. Skills are resolved from [`skills/`](../skills/) at build time by [`scripts/build-pack.js`](../scripts/build-pack.js), wherever they're filed.

## Packs in this repository

| Pack | Folder | Skills |
|---|---|---|
| GitHub Issue Resolver | [`development/code/github-issue-resolver/`](development/code/github-issue-resolver/pack.json) | `github-issue-context`, `github-implement-issue` |
| Presales Scoping Pack | [`development/code/presales-scoping/`](development/code/presales-scoping/pack.json) | the 11 `presales-*` skills |

## Building a pack

```bash
npm run build:pack -- presales-scoping
```

This reads `packs/development/code/presales-scoping/pack.json`, resolves each listed skill from `skills/`, and — for every runtime at least one of its skills is compatible with (see [`runtimes/`](../runtimes/)) — builds a distribution per skill and assembles them under `dist/packs/presales-scoping/<runtime>/`:

```text
dist/packs/presales-scoping/
├── claude-code/
│   ├── pack.json
│   ├── pack-distribution.json
│   ├── presales-quote/
│   └── ...
└── claude-ai/
    ├── pack.json
    ├── pack-distribution.json
    ├── presales-quote/          # contains presales-quote-0.1.0.skill
    └── ...
```

A runtime with no verified/implemented adapter for any of the pack's skills is simply absent from `dist/packs/<pack-id>/` — nothing fictional gets built. The command never modifies anything under `skills/`, `packs/`, or `runtimes/`.
