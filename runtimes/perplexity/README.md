# runtimes/perplexity

Status: **supported** (see [`runtime.json`](runtime.json)) via `installStrategy: "manual-bundle"`.

Perplexity has no file-based skill loading, so this isn't a native install — it's a real, generated artifact you paste in by hand:

```bash
npm run build:skill -- av-devis perplexity
# -> dist/skills/av-devis/perplexity/av-devis-0.1.0.md
```

Open that file and paste its content into a Perplexity Space's custom instructions. The generated file already contains a short header plus the skill's full `SKILL.md` content — nothing more to edit.
