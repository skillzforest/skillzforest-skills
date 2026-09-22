# runtimes/

A runtime is a target environment where a skill installs or executes. This folder holds one `runtime.json` per runtime plus adaptation notes — it never holds an independently maintained copy of a skill.

```text
skills/    = canonical source
runtimes/  = compatibility declarations + adapters
dist/      = generated, distributable artifacts
```

Each `runtimes/<id>/runtime.json` declares how that runtime installs skills:

```json
{
  "id": "claude-code",
  "name": "Claude Code",
  "type": "filesystem",
  "supportsAgentSkills": true,
  "installStrategy": "filesystem",
  "status": "verified"
}
```

`installStrategy` selects the adapter in [`scripts/lib/adapters.js`](../scripts/lib/adapters.js) used to build a distribution. `status` says how confident that manifest is: `verified` (tested end-to-end), `supported` (implemented against a documented/confirmed convention, not independently lab-tested), or `unknown` (no confirmed mechanism at all) — see each runtime's own `README.md` for the reasoning.

| Runtime | installStrategy | status | Notes |
|---|---|---|---|
| [`claude-code/`](claude-code/) | `filesystem` | `verified` | `~/.claude/skills/<skill-name>/` |
| [`claude-ai/`](claude-ai/) | `upload` | `verified` | Zip upload (Claude.ai / Claude Desktop custom Skills) |
| [`codex/`](codex/) | `filesystem` | `supported` | `~/.agents/skills/<skill-name>/` |
| [`gemini/`](gemini/) | `filesystem` | `supported` | Gemini CLI, `~/.gemini/skills/<skill-name>/` |
| [`mistral/`](mistral/) | `manual-bundle` | `supported` | Generates a copy-pasteable Markdown file (no file-based loading) |
| [`perplexity/`](perplexity/) | `manual-bundle` | `supported` | Generates a copy-pasteable Markdown file (no file-based loading) |
| [`chatgpt/`](chatgpt/) | `plugin` | `unknown` | No adapter implemented |
| [`cursor/`](cursor/) | `manual` | `unknown` | No adapter implemented |
| [`opencode/`](opencode/) | `manual` | `unknown` | No adapter implemented |

`filesystem`, `upload`, and `manual-bundle` have real adapters. A runtime with `installStrategy: "manual"` and `status: "unknown"` is a placeholder: it exists so the architecture doesn't need reshaping when that runtime is confirmed, but nothing gets built for it until an adapter is written and its manifest is updated — see [`scripts/lib/adapters.js`](../scripts/lib/adapters.js) and [`scripts/lib/distribute.js`](../scripts/lib/distribute.js).

## Adding a new runtime

1. Create `runtimes/<id>/runtime.json` (see [`schemas/runtime.schema.json`](../schemas/runtime.schema.json)).
2. If it needs a real transformation (not a plain filesystem copy or a zip), add an adapter function to `scripts/lib/adapters.js` keyed by its `installStrategy`.
3. Update each skill's `skill.json` `compatibility` block once compatibility is actually verified — never mark a runtime `native`/`supported` speculatively.
