# skills/development — Development & Tech

The site's **Development & Tech** category (*Développement & Tech*, pros & teams). Its subcategories are `code/`, `devops/` and `data-ai/` (see [`skills/domains.json`](../domains.json)); only `code/` holds skills today.

## `code/`

- `skf-github-issue-brief` and `skf-github-issue-fix` — turn a GitHub Issue — or every issue of a GitHub Project board — into a ready-to-use context bundle, then implement it in a codebase; the GitHub CLI is installed on the way if missing. See [`code/skf-github-issue-workflow.md`](./code/skf-github-issue-workflow.md) for how they work together. Sold together as the **GitHub Issue Resolver** pack ([`packs/development/code/github-issue-resolver/`](../../packs/development/code/github-issue-resolver/pack.json)).
- `skf-skill-review` — runs the SkillzForest reviewer (`skillzforest-reviewer`) on a skill given as a folder, a zip, a SKILL.md or a URL: locally, or through the back office's n8n chain (`--pipeline`).
- `skf-content-import` — writes a skill's or a pack's whole product page (French and English), renders its cover, poster and video with Remotion, and creates or updates it in a CMS. CMS-agnostic: each CMS is a JSON profile in `profiles/` (SkillzForest, file export, a Strapi example).
- `skf-zip-folders` — asks for a directory, then zips each of its subdirectories into its own `<folder>.zip` (next to it, or `--out`), without `.DS_Store`, `.git`, `node_modules` or `__pycache__`, and checks every archive.
- The 11 `presales-*` skills — functional and technical scoping of an app, web or SaaS project, from kickoff to client proposal: init project, functional and platform scoping, logical and physical diagrams, user journeys, quotes, client presentation, meeting notes and domain name. Sold together as the **Presales Scoping Pack** ([`packs/development/code/presales-scoping/`](../../packs/development/code/presales-scoping/pack.json)).

Accepted prefixes in `code/`: `github-`, `presales-`.
