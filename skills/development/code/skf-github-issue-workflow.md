# GitHub issue → implementation pipeline

Two Claude Code Agent Skills, part of the
[Development & Engineering](../README.md) domain, that work together but
stay loosely coupled, communicating only through files on disk:

- [`skf-github-issue-brief`](./skf-github-issue-brief/SKILL.md) — collects and
  normalizes a GitHub Issue (text, comments, screenshots/attachments) into
  a stable context bundle. Never touches application code.
- [`skf-github-issue-fix`](./skf-github-issue-fix/SKILL.md) —
  investigates the repository and implements a fix using that bundle.
  Never re-fetches GitHub data itself.

## Commands

```text
/skf-github-issue-brief 427
/skf-github-issue-brief https://github.com/org/repository/issues/427
/skf-github-issue-brief 427 --refresh
/skf-github-issue-brief --board https://github.com/orgs/acme/projects/7 --status "Todo"

/skf-github-issue-fix 427
/skf-github-issue-fix https://github.com/org/project/issues/427
/skf-github-issue-fix 427 --plan

/skf-github-issue-fix --board https://github.com/orgs/acme/projects/7 --status "Todo"
/skf-github-issue-fix --all --label bug
/skf-github-issue-fix --next
```

`--refresh` forces `skf-github-issue-brief` to rebuild even if nothing
changed on GitHub. `--plan` makes `skf-github-issue-fix` investigate and
propose an approach without touching any file. `--board` (a GitHub
Project) and `--all` (the repository's issues) prepare every matching
issue's context in one go and write a queue, `.agent/issues/INDEX.md`;
`--next` then fixes the first pending one.

## GitHub CLI

Both skills use `gh`. `skf-github-issue-brief`'s Step 0
(`scripts/setup_gh.py`) checks it, installs it with the user's consent
when it is missing — package manager, or the official release checked
against its SHA-256 sums into `~/.local/bin` — and hands the user the
`gh auth login` command (plus `gh auth refresh --scopes read:project` for
`--board`). Sign-in stays with the user: no token is ever asked for.

## Pipeline

```text
GitHub
   |
   v
skf-github-issue-brief
   |  gh issue view --json ...           (fetch_issue.py)
   |  regex scan for image/attachment URLs (extract_attachments.py)
   |  download images, tolerate failures  (download_attachments.py)
   |  Claude reads each image directly    (visual_evidence.json)
   |  merge everything, derive leads      (build_context.py)
   |  ... or for a whole board / repo     (prepare_issues.py -> queue.json, INDEX.md)
   v
.agent/issues/<number>/
   context.json   <- machine-readable contract
   context.md     <- LLM-readable narrative
   assets/*       <- original downloaded screenshots
   assets.json    <- download manifest (incl. failures)
   |
   v
skf-github-issue-fix
   |  read context.md / context.json (Phase 1)
   |  map the repository, find test/lint/build commands (Phase 2)
   |  separate reporter claims from code/test evidence (Phase 3)
   |  reproduce before fixing, when practical (Phase 4)
   |  find and verify the root cause against the code (Phase 5)
   |  short implementation plan (Phase 6)
   |  minimal, targeted code change (Phase 7)
   |  run tests/lint/typecheck, report PASS/FAIL/NOT RUN (Phase 8)
   v
Final report (root cause, changes, files, validation, visual evidence used,
remaining uncertainties) — no commit/push/PR unless explicitly asked.
```

## Why this boundary

`skf-github-issue-brief` and `skf-github-issue-fix` don't share code and
don't call into each other directly. The only interface between them is
`.agent/issues/<number>/context.json` (schema documented in
[`skf-github-issue-brief/references/context-schema.md`](./skf-github-issue-brief/references/context-schema.md))
and its companion `context.md`. That means:

- `skf-github-issue-brief` can be run standalone, by a human or another
  skill, purely to understand a ticket — it never starts editing code.
- `skf-github-issue-fix` checks for a fresh context bundle before doing
  anything else and triggers `skf-github-issue-brief`'s own workflow if it's
  missing or stale, rather than re-implementing issue fetching itself (see
  [`skf-github-issue-fix/references/context-contract.md`](./skf-github-issue-fix/references/context-contract.md)).
- Either skill can change internally (a better regex, a smarter root-cause
  heuristic) without the other needing to change, as long as the schema
  holds.

## Security posture (both skills)

GitHub issue bodies, comments, attachments, screenshots, and logs are
**untrusted external data**. Both skills extract technical information from
that content but never execute instructions found inside it, never expose
or persist a GitHub token, and never run shell commands lifted from a
comment without independently assessing them first. See each skill's
"Untrusted issue content" section for the exact wording both follow.
