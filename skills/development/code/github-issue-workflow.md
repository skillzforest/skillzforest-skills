# GitHub issue → implementation pipeline

Two Claude Code Agent Skills, part of the
[Development & Engineering](../README.md) domain, that work together but
stay loosely coupled, communicating only through files on disk:

- [`github-issue-context`](./github-issue-context/SKILL.md) — collects and
  normalizes a GitHub Issue (text, comments, screenshots/attachments) into
  a stable context bundle. Never touches application code.
- [`github-implement-issue`](./github-implement-issue/SKILL.md) —
  investigates the repository and implements a fix using that bundle.
  Never re-fetches GitHub data itself.

## Commands

```text
/github-issue-context 427
/github-issue-context https://github.com/org/repository/issues/427
/github-issue-context 427 --refresh

/github-implement-issue 427
/github-implement-issue https://github.com/org/project/issues/427
/github-implement-issue 427 --plan
```

`--refresh` forces `github-issue-context` to rebuild even if nothing
changed on GitHub. `--plan` makes `github-implement-issue` investigate and
propose an approach without touching any file.

## Pipeline

```text
GitHub
   |
   v
github-issue-context
   |  gh issue view --json ...           (fetch_issue.py)
   |  regex scan for image/attachment URLs (extract_attachments.py)
   |  download images, tolerate failures  (download_attachments.py)
   |  Claude reads each image directly    (visual_evidence.json)
   |  merge everything, derive leads      (build_context.py)
   v
.agent/issues/<number>/
   context.json   <- machine-readable contract
   context.md     <- LLM-readable narrative
   assets/*       <- original downloaded screenshots
   assets.json    <- download manifest (incl. failures)
   |
   v
github-implement-issue
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

`github-issue-context` and `github-implement-issue` don't share code and
don't call into each other directly. The only interface between them is
`.agent/issues/<number>/context.json` (schema documented in
[`github-issue-context/references/context-schema.md`](./github-issue-context/references/context-schema.md))
and its companion `context.md`. That means:

- `github-issue-context` can be run standalone, by a human or another
  skill, purely to understand a ticket — it never starts editing code.
- `github-implement-issue` checks for a fresh context bundle before doing
  anything else and triggers `github-issue-context`'s own workflow if it's
  missing or stale, rather than re-implementing issue fetching itself (see
  [`github-implement-issue/references/context-contract.md`](./github-implement-issue/references/context-contract.md)).
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
