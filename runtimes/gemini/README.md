# runtimes/gemini

Status: **supported** (see [`runtime.json`](runtime.json)) — implemented, not independently lab-tested.

Refers to **Gemini CLI** (the local coding-agent CLI), not the remote Gemini web app, which has no file-based skill loading. Target layout: `~/.gemini/skills/<skill-name>/`, the same plain `SKILL.md` folder shape as Claude Code and Codex (`installStrategy: "filesystem"`).

## Building and installing locally

```bash
npm run build:skill -- av-devis gemini
npm run build:runtime -- gemini

cp -R dist/skills/av-devis/gemini ~/.gemini/skills/av-devis
```

## Once verified

Bump `runtime.json`'s `status` to `"verified"` once confirmed against a live Gemini CLI install, and each skill's compatibility to `"native"` if no adjustment was needed.
