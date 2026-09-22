# schemas/

Plain JSON Schemas for the manifest types in this repo. Kept deliberately simple — enough to catch a malformed manifest, not a validation framework.

| Schema | Validates |
|---|---|
| [`skill.schema.json`](skill.schema.json) | `skills/<domain>/<name>/skill.json` |
| [`domain.schema.json`](domain.schema.json) | `skills/domains.json` — the métier domain registry |
| [`pack.schema.json`](pack.schema.json) | `packs/<id>/pack.json` |
| [`runtime.schema.json`](runtime.schema.json) | `runtimes/<id>/runtime.json` |
| [`distribution.schema.json`](distribution.schema.json) | `dist/skills/<name>/<runtime>/distribution.json` (generated, never authored by hand) |

`scripts/validate.js` currently checks the same rules by hand (no `ajv` dependency yet, to avoid pulling in a new package before it's actually needed) — these schemas are the reference definition that logic follows, and the natural next step if/when the checks outgrow a hand-rolled script.
