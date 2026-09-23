# runtimes/claude-code

Status: **verified** (see [`runtime.json`](runtime.json)).

Target layout: `~/.claude/skills/<skill-name>/`, one folder per skill containing at least `SKILL.md`. Skills in this repo are already authored in that exact format, so the adapter (`installStrategy: "filesystem"`) is a plain copy — no transformation.

## Building and installing locally

```bash
npm run build:skill -- presales-quote claude-code   # -> dist/skills/presales-quote/claude-code/
npm run build:runtime -- claude-code          # builds every compatible skill for this runtime
npm run build:pack -- sales                   # builds every runtime a pack's skills are compatible with, including this one

cp -R dist/skills/presales-quote/claude-code ~/.claude/skills/presales-quote
```

## Compatibility note

This repository previously kept hand-zipped `.skill` archives under `skills-claude/` (one per skill, for upload to Claude.ai — a different runtime, see [`../claude-ai/`](../claude-ai/)). Those were a manually maintained second copy of `skills/` and have been removed; distributions for both Claude Code and Claude.ai are now generated on demand by `scripts/build-skill.js`.
