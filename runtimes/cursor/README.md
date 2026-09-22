# runtimes/cursor

Status: **unknown** (see [`runtime.json`](runtime.json)) — no adapter is implemented yet.

Cursor does not have a confirmed, documented "skill" folder convention at the time of writing. Once its expected format is verified, update `runtime.json` (`type`, `supportsAgentSkills`, `installStrategy`, `status`) and, if it needs a real transformation rather than a plain copy, add an adapter to `scripts/lib/adapters.js`.
