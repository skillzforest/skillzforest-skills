# runtimes/codex

Status: **supported** (see [`runtime.json`](runtime.json)) — implemented, not independently lab-tested.

Target layout: `~/.agents/skills/<skill-name>/`, the same plain `SKILL.md` folder shape Claude Code uses (`installStrategy: "filesystem"`). This is the convention Codex is documented to follow; it hasn't been confirmed against a live Codex install, which is why skill compatibility is declared `"supported"` rather than `"native"`.

## Building and installing locally

```bash
npm run build:skill -- presales-quote codex   # -> dist/skills/presales-quote/codex/
npm run build:runtime -- codex          # every compatible skill for this runtime

cp -R dist/skills/presales-quote/codex ~/.agents/skills/presales-quote
```

## Once verified

If a real Codex install confirms this path and format, bump `runtime.json`'s `status` to `"verified"` and, if needed, each skill's compatibility from `"supported"` to `"native"`. If Codex actually expects something different, keep the id and update `paths.user` / `installStrategy` accordingly — nothing else in the build pipeline needs to change.
