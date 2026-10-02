# skills/

This is the **canonical source of truth** for every Agent Skill in SkillzForest. Nothing outside this folder may hold an independently maintained copy of a skill — `packs/`, `runtimes/`, and `dist/` only reference or generate from what lives here.

## Layout: the site's categories

Skills are organized **exactly like the SkillzForest site's catalog**: one folder per category, one per subcategory, then the skill.

```text
skills/<category>/<subcategory>/<skill-name>/
├── SKILL.md        # required — the skill's business content (the actual prompt/logic)
├── skill.json      # required — metadata (category + subcategory, matching the folders) and runtime compatibility
├── scripts/        # optional — skill-owned automation
├── references/     # optional — supporting material read by the skill
├── templates/      # optional — reusable structural templates
├── masters/        # optional — master documents the skill fills/copies
└── assets/         # optional — static assets
```

The registry is [`skills/domains.json`](./domains.json) (schema: [`schemas/domain.schema.json`](../schemas/domain.schema.json)). It mirrors the site's categories and subcategories (`GET /api/v1/categories`): the same slugs, universes and names. When the site's taxonomy changes, update `domains.json` first, then move the folders — `npm run validate` checks that every folder is a registered category/subcategory and that each `skill.json` declares the `category`/`subcategory` it lives under.

A skill's folder must also match where the site lists it: a skill the site files under *Development › Code* lives in `skills/development/code/`.

Folder names are the site's slugs: lowercase, no spaces, no accents, hyphens between words (`sales-crm/client-follow-up`, never `Vente & CRM/Suivi client`). The same goes for files a skill ships (`User-story-mapping-Template.jpg`).

## Categories

### General public (`personal`)

| Category folder | Name (FR) | Subcategory folders |
|---|---|---|
| `social-media/` | Social media (Réseaux sociaux) | `personal-branding`, `content-creation`, `growth` |
| `career/` | Job Search & Career (Recherche d'emploi & Carrière) | `resume`, `cover-letter`, `skills-assessment`, `job-search`, `application-tracking` |
| `creative/` | Creative & AI avatars (Création & avatars IA) | `ai-avatar`, `visuals`, `video` |
| `token-savings/` | Token savings & AI costs (Économie de tokens & coûts IA) | `context-management`, `prompt-optimization`, `cost-monitoring` |

### Pros & teams (`pro`)

| Category folder | Name (FR) | Subcategory folders |
|---|---|---|
| `marketing/` | Marketing & Growth (Marketing & Growth) | `content`, `seo-sea`, `social-media`, `emailing` |
| `writing/` | Writing & Content (Écriture & Contenu) | `drafting`, `editing`, `translation` |
| `design/` | Design & Creative (Design & Créa) | `ui-ux` (skf-), `visual-content` |
| `support/` | Customer Support (Support client) | `ticketing`, `knowledge-base` |
| `sales-crm/` | Sales & CRM (Vente & CRM) | `prospecting`, `client-follow-up`, `reporting` |
| `product/` | Product Management (Product Management) | `roadmap`, `specs`, `user-research` |
| `development/` | Development & Tech (Développement & Tech) | `code` (presales-, github-), `devops`, `data-ai` |
| `hr/` | HR & Recruiting (RH & Recrutement) | `sourcing`, `onboarding`, `payroll` |
| `finance/` | Finance & Accounting (Finance & Comptabilité) | `invoicing`, `closing`, `reporting` |
| `legal/` | Legal & Compliance (Juridique & Conformité) | `contracts`, `compliance` |

A subcategory may restrict the skill-id prefixes it accepts (shown in parentheses); without that, any prefix is fine. Folders are only created once a category holds a skill — today, `development/code/` (the `github-*` and `presales-*` skills) and `design/ui-ux/` (`skf-design-extractor`).

## Standalone skills (no category)

A directory directly under `skills/<skill-name>/` that itself contains a `SKILL.md` is a **standalone skill** — a generic Claude Code Agent Skill invoked by its own name, outside the catalog. No name prefix, and `skill.json` is optional. `scripts/validate.js` and `scripts/lib/skills.js` tell a category folder from a standalone skill. None exists today.

## Rules

1. A skill exists once, in the category/subcategory folder the site files it under, with one runtime-agnostic id (`dev-seo`, never `claude-dev-seo`).
2. `skill.json`'s `category` and `subcategory` match its folders — `npm run validate` enforces it, along with any prefix a subcategory restricts.
3. A skill contains no runtime-specific logic unless intrinsic to it — runtime adaptation belongs in `runtimes/`.
4. A skill contains no orchestration logic — that belongs in `workflows/`.
5. Packs, bundles and runtimes only reference skills by name; they never copy skill files.
6. `skill.json`'s `compatibility` map only records what's actually been verified — see [`runtimes/README.md`](../runtimes/README.md).
7. Run `npm run validate` before committing changes here.
