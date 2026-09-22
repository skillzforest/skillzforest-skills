# SkillzForest Skills

> The skills factory for SkillzForest — a source repository for reusable Agent Skills, workflows and commercial packs, versioned and packaged here before being distributed through SkillzForest.

```text
SkillzForest Skills
    ↓
creates and maintains
Skills
    ↓
adapted through
Runtime Distributions
    ↓
grouped into
SkillzForest Packs
    ↓
distributed on
SkillzForest
```

```text
SkillzForest Skills
│
├── Skills
├── Workflows
├── Packs
├── Runtime adapters
└── SkillzForest Installer
          ↓
      end users
```

- **SkillzForest Skills** (this repo) = production and maintenance — where skills are authored, versioned, and packaged.
- **SkillzForest** = marketplace and distribution — where finished packs are discovered, bought, and installed.
- **SkillzForest Installer** = installation multi-runtime — the desktop app (`installer/`, Tauri + React) a non-technical user runs to actually get a skill onto their machine, in whichever runtime they choose, without ever seeing a file path or a `SKILL.md`.

## Concepts

```text
Skill = capacité métier
Distribution = adaptation technique
Runtime = environnement cible
Pack = produit commercial SkillzForest
```

- **Skill** — a single atomic capability, with its own inputs, guardrails and outputs (e.g. `av-devis`, or a future `dev-seo`). Lives once, under `skills/<family>/<name>/`. A skill's id is always runtime-agnostic: `dev-seo`, never `claude-dev-seo` / `codex-dev-seo` / `cursor-dev-seo`.
- **Distribution** — how one skill is prepared for one specific runtime (a filesystem copy, a zip, a plugin manifest…). Generated on demand into `dist/skills/<name>/<runtime>/`; never hand-maintained.
- **Runtime** — a target environment where a skill installs or runs (Claude Code, Claude.ai, ChatGPT, Codex, Cursor, Perplexity, Gemini, OpenCode…). Declared under `runtimes/<id>/runtime.json`; adapts, never duplicates.
- **Compatibility** — how sure we are that a skill actually works on a given runtime: `native` (verified, no adaptation needed), `supported` (verified, different but known install path), `adapted` (verified, needs a generated transformation), `unsupported` (verified not to work), `unknown` (not checked yet — the honest default until proven otherwise).
- **Pack** — a commercial product bundling several coherent skills for SkillzForest (e.g. the Pre-Sales Pack). Lives under `packs/<id>/pack.json`; only references skill ids, never copies their files.
- **Workflow** — an ordered sequence of skills that completes an end-to-end process (e.g. a future `feature-to-production`). Lives under `workflows/`; orchestrates, never duplicates.
- **Bundle** — several commercial packs sold together. Lives under `bundles/`.

A skill can be compatible with one runtime, several, or (rarely, when truly unavoidable) be runtime-specific — but it always keeps one canonical id. See [`skills/README.md`](skills/README.md), [`runtimes/README.md`](runtimes/README.md), [`packs/README.md`](packs/README.md), [`workflows/README.md`](workflows/README.md), [`bundles/README.md`](bundles/README.md), and [`schemas/README.md`](schemas/README.md) for the full rules.

## Source of truth

```text
skills/     = canonical source
packs/      = commercial composition (references skills, never copies them)
workflows/  = orchestration (references skills, never copies them)
runtimes/   = compatibility declarations + adapters (never a second copy of a skill)
dist/       = generated distributions — always derived, never hand-edited, never itself a source
```

## Repository structure

```text
skillzforest-skills/
├── skills/                    # canonical source of every skill
│   ├── av/                    # avant-vente / pre-sales — the only populated family today
│   ├── product/ board/ ux/ ui/ arch/ dev/ data/ ai/ sec/
│   ├── qa/ release/ infra/ ops/ growth/ billing/ legal/ docs/
│   └── README.md
├── workflows/                  # documented orchestration across skills
├── packs/                      # commercial products (metadata + skill references)
│   ├── presales/pack.json      # active — all existing av-* skills
│   ├── saas-builder/pack.json  # skeleton, skills: []
│   └── saas-ops/pack.json      # skeleton, skills: []
├── bundles/                    # groups of packs (none active yet)
├── runtimes/                   # one runtime.json + README per target environment
│   ├── claude-code/ claude-ai/ codex/ gemini/
│   └── mistral/ perplexity/ chatgpt/ cursor/ opencode/
├── schemas/                    # skill / pack / runtime / distribution JSON Schemas
├── scripts/                    # validate, build-skill, build-pack, build-runtime, build-all
├── installer/                  # SkillzForest Installer — Tauri + React desktop app (see installer/README.md)
├── tests/                      # reserved for automated tests
├── dist/                       # generated artifacts only — never a source
│   ├── skills/ packs/          # from the scripts above
│   └── installer/macos|windows|linux/  # from `npm run app:build`
├── package.json
└── README.md
```

## A skill, up close

```text
skills/av/av-devis/
├── SKILL.md      # the business content — what the skill actually does
├── skill.json    # SkillzForest metadata + runtime compatibility
├── scripts/      # optional — skill-owned automation
├── masters/      # optional — master documents this skill fills/copies
└── ...
```

```json
{
  "schemaVersion": 1,
  "id": "av-devis",
  "name": "Devis modulaire du projet",
  "publisher": "SkillzForest",
  "version": "0.1.0",
  "category": "pre-sales",
  "description": "Produit le devis modulaire forfaitaire d'un projet à partir du master Devis_Modulaire.",
  "compatibility": {
    "claude-code": "native",
    "claude-ai": "native",
    "codex": "supported",
    "gemini": "supported",
    "mistral": "supported",
    "perplexity": "supported",
    "chatgpt": "unknown",
    "cursor": "unknown",
    "opencode": "unknown"
  }
}
```

No skill in this repository declares `native`/`supported`/`adapted` for a runtime that hasn't actually been checked — see [Known compatibility](#known-compatibility-today) below.

## The pre-sales skills (`skills/av/`)

- `av-init-projet` : initialise la structure du projet et les dossiers de travail.
- `av-cadrage-fonctionnel` : produit le cadrage fonctionnel du besoin.
- `av-cadrage-plateforme` : produit le cadrage technique et architectural.
- `av-schema-logique` : génère le schéma logique.
- `av-schema-physique` : génère le schéma physique.
- `av-parcours-miro` : construit le user story mapping sur Miro.
- `av-devis` : produit le devis forfaitaire du projet.
- `av-devis-tma` : produit le devis de maintenance récurrente.
- `av-presentation-client` : assemble le deck client.
- `av-compte-rendu-reunion` : rédige les comptes rendus de réunion.
- `av-nom-de-domaine` : trouve et vérifie un nom de domaine / de marque disponible.

### Phrases d'invocation copiables

```text
av-init-projet : Initialise le projet [Nom du projet] dans l'arborescence avant-vente et crée les dossiers et documents de base.
```

```text
av-cadrage-fonctionnel : Fais le cadrage fonctionnel du projet [Nom du projet] à partir des pièces client et des comptes rendus.
```

```text
av-cadrage-plateforme : Fais le cadrage technique du projet [Nom du projet], avec les décisions structurantes, composants, services tiers et budget indicatif.
```

```text
av-schema-logique : Génère le schéma logique de l'architecture du projet [Nom du projet].
```

```text
av-schema-physique : Génère le schéma physique de l'infrastructure du projet [Nom du projet].
```

```text
av-parcours-miro : Crée le user story mapping et les parcours utilisateurs du projet [Nom du projet] sur Miro.
```

```text
av-devis : Prépare le devis du projet [Nom du projet] à partir du cadrage fonctionnel et du cadrage plateforme.
```

```text
av-devis-tma : Prépare le devis TMA du projet [Nom du projet] avec les hypothèses de maintenance récurrente.
```

```text
av-presentation-client : Assemble la présentation client du projet [Nom du projet] à partir des livrables déjà produits.
```

```text
av-compte-rendu-reunion : Rédige le compte rendu de la réunion sur le projet [Nom du projet] avec les décisions, actions et points en suspens.
```

```text
av-nom-de-domaine : Trouve et vérifie un nom de domaine disponible pour le projet [Nom du projet].
```

## Workflows

A workflow orchestrates several skills in a defined order — see [`workflows/README.md`](workflows/README.md) for the full format and governance rules. Today's active workflows (documented in Markdown, all built from existing `av-*` skills):

- `avant-vente-complete`, `cadrage-fonctionnel`, `cadrage-technique`, `ux-parcours`, `chiffrage`, `presentation-client`.

## Known compatibility today

| Runtime | installStrategy | Status | Basis |
|---|---|---|---|
| Claude Code | `filesystem` | **verified** (`native`) | Skills are authored directly in the Agent Skills `SKILL.md` format Claude Code loads unmodified. |
| Claude.ai | `upload` | **verified** (`native`) | Same `SKILL.md` format, delivered as a zip through Claude.ai's custom Skills upload. |
| Codex | `filesystem` | **supported** | Installs a plain `SKILL.md` folder under `~/.agents/skills/<name>/` — implemented against the documented convention, not independently lab-tested. |
| Gemini | `filesystem` | **supported** | Gemini CLI, `~/.gemini/skills/<name>/` — same caveat as Codex. |
| Mistral | `manual-bundle` | **supported** | No file-based loading; generates one copy-pasteable Markdown file for Le Chat's custom instructions. |
| Perplexity | `manual-bundle` | **supported** | No file-based loading; generates one copy-pasteable Markdown file for a Space's custom instructions. |
| ChatGPT | `plugin` | **unknown** | No native Agent Skills support; would need a dedicated, unbuilt integration. |
| Cursor | `manual` | **unknown** | No confirmed skill format. |
| OpenCode | `manual` | **unknown** | No confirmed integration mechanism. |

Every `skill.json` and `runtimes/*/runtime.json` in this repo reflects this table exactly. `supported` means "implemented and usable today, against a documented convention" — distinct from `native`/`verified`, which means independently confirmed. `unknown` stays a deliberate, honest default for the three runtimes with no confirmed mechanism at all, not a gap to hide. Building a distribution for an `unknown` runtime is skipped by default (`npm run build:runtime -- cursor` reports every skill as skipped); pass `--include-unknown` to force it once you're validating a candidate integration, not shipping one.

## Building and testing locally

```bash
npm run validate                        # checks skills/, packs/, and runtimes/ for structural and compatibility errors
npm run build:skill -- av-devis         # -> dist/skills/av-devis/<runtime>/ for every compatible runtime
npm run build:skill -- av-devis claude-code   # -> just that one runtime
npm run build:runtime -- claude-code    # builds every compatible skill for one runtime
npm run build:pack -- presales          # -> dist/packs/presales/<runtime>/ for every runtime the pack's skills support
npm run build                           # builds every runtime, then every pack

./scripts/install-pack.sh dist/packs/presales/claude-code ~/.claude/skills   # local install test (filesystem runtimes only)
```

Every build script reads only from `skills/` (or from previously generated `dist/` output within the same run) and never writes back into `skills/`, `packs/`, or `runtimes/`.

## SkillzForest Installer

```text
Discover → Buy → Install → Choose runtime → Ready to use
```

`installer/` is a desktop app (Tauri + React + TypeScript) that drives this journey without ever exposing a file path, a manifest format, or the word "SKILL.md" to the end user. It reads `skills/`, `packs/`, and `runtimes/` from this repo (via `LocalSkillSource`) and installs into whichever runtime the user picks — today, fully automated for Claude Code, Codex, and Gemini; every other runtime shows "Manual installation" or "Coming soon" rather than pretending to support something unverified.

```text
detect(runtime)       -> RuntimeAdapter::detect()
checkCompatibility(skill) -> RuntimeAdapter::can_install()
download(skill)        -> SkillSource::resolve_distribution() (LocalSkillSource today; RemoteSkillSource is a documented stub)
install(skill, runtime) -> installer::engine::install_skill()
update(skill, runtime)  -> installer::engine (clean reinstall)
uninstall(skill, runtime) -> installer::engine::uninstall_skill() (registry-scoped — never touches an install it didn't create)
```

See [`installer/README.md`](installer/README.md) for the full architecture, dev/build commands, and how to add a runtime or a remote source.

## Compatibility notes (retired / transitional)

- `plugins/ai-factory-av/` was removed: its manifest and build logic are now `packs/presales/pack.json` + `scripts/build-pack.js`.
- `skills-claude/*.skill` (hand-zipped archives, one per skill) was removed: it was a second source of truth that could silently drift from `skills/`. The same `.skill` zip format is now generated on demand for the `claude-ai` runtime — see [`runtimes/claude-ai/README.md`](runtimes/claude-ai/README.md).
- `.agents/skills/` (this repo's former canonical source) moved to `skills/av/`. `.agents/skills/<name>/` remains the *install target* other projects use to consume these skills via Codex — never a source maintained in this repository.
- `templates/documents/` was removed: its files were either exact duplicates of masters already versioned with their skill (`skills/*/masters/`), or not yet placed with their skill — they were moved, not duplicated. `templates/projet/` (local, untracked test fixtures) was left untouched.

## Development

```bash
npm install       # script dependencies (fill_master, build-skill, build-pack)
npm run validate  # skills/packs/runtimes consistency checks
npm run build     # builds every runtime distribution, then every pack

npm run app:dev    # launches the SkillzForest Installer desktop app (Tauri dev mode)
npm run app:build  # builds it -> dist/installer/<os>/
```
