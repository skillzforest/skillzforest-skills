# skills/development — Development & Engineering

Design, build, test, and run a software product.

Seen from the outside (a buyer, a client), this is one domain — the
commercial pack [`packs/development/pack.json`](../../packs/development/pack.json)
sells it as such. Internally it splits into **subcategories**, one folder
level deeper, so both a buyer with a narrower need and the people building
skills here get the right level of detail:

| Subcategory folder | Name | Accepted prefixes | Scope |
|---|---|---|---|
| `seo/` | SEO | `seo-*` | Technical and content search-engine optimization |
| `code/` | Code | `product-*`, `arch-*`, `dev-*`, `data-*`, `ai-*`, `qa-*`, `infra-*`, `ops-*`, `release-*`, `sec-*`, `github-*` | Product scoping, architecture, development, data, AI, QA, infra, ops, release, security |
| `ux-ui/` | UX/UI | `ux-*`, `ui-*` | User experience, journeys, interface, design system |

The registry is [`skills/domains.json`](../domains.json) (schema:
[`schemas/domain.schema.json`](../../schemas/domain.schema.json)); this table
is its human-readable mirror. `npm run validate` enforces that every skill
under `skills/development/<subcategory>/` uses a prefix registered for that
subcategory.

## What lives here today

- `code/github-issue-context` and `code/github-implement-issue` — the pair
  of Claude Code Agent Skills that turn a GitHub Issue into a ready-to-use
  context bundle and then implement it in a codebase. See
  [`code/github-issue-workflow.md`](./code/github-issue-workflow.md) for how
  they work together.

`seo/` and `ux-ui/` are placeholders, created ahead of need — no skill lives
there yet.
