# runtimes/mistral

Status: **supported** (see [`runtime.json`](runtime.json)) via `installStrategy: "manual-bundle"`.

Mistral (Le Chat / API) has no file-based skill loading, so this isn't a native install — it's a real, generated artifact you paste in by hand:

```bash
npm run build:skill -- av-devis mistral
# -> dist/skills/av-devis/mistral/av-devis-0.1.0.md
```

Open that file and paste its content into Le Chat's custom instructions, or use it as a system prompt when calling the Mistral API directly.
