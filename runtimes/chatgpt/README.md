# runtimes/chatgpt

Status: **unknown** (see [`runtime.json`](runtime.json)) — no adapter is implemented yet.

ChatGPT does not consume the Agent Skills `SKILL.md` format natively (`supportsAgentSkills: false`). Reaching it would mean building and maintaining a separate integration — a Custom GPT or a plugin manifest generated from the skill's content — which doesn't exist in this repo yet. `installStrategy` is declared as `"plugin"` as the expected shape of that future adapter, but no code implements it, so `npm run build:runtime -- chatgpt` will skip every skill until one is written.
