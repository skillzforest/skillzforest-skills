# Growth workspace

All growth skills work in one **growth workspace**: a private Git repository (or a folder synced to one) that keeps
the state between runs. Scheduled runs start with no memory: what is not in the workspace or the tracker is lost.

```text
<workspace>/
├── docs/board.json                 tracker ids (board, fields, options, labels), written by skf-growth-tracker setup
├── docs/conventions.md             optional: the owner's own conventions, read first when present
├── projects/<project-id>/
│   ├── growth.json                 the project's growth profile (references/profile.md)
│   ├── intel/YYYY-Www.md           market intelligence, one file per ISO week (skf-market-intel)
│   ├── strategy/channels.md        channel scores (skf-channel-strategy)
│   ├── strategy/plan-30d.md        0 to 30 day plan
│   ├── strategy/plan-90d.md        30 to 90 day plan
│   ├── strategy/decisions.md       decision log, newest first (skf-growth-tracker)
│   ├── campaigns/YYYY-MM-DD-slug/  one folder per campaign (skf-campaign-studio)
│   ├── pipeline/YYYY-Www.md        prospects and partners of the week, organizations only (skf-prospect-pipeline)
│   ├── outreach/YYYY-MM-DD-slug.md message drafts, no personal contact data (skf-sales-outreach)
│   └── metrics/YYYY-Www.json       weekly measures (skf-growth-report)
└── reports/
    ├── daily/YYYY-MM-DD.md
    └── weekly/YYYY-Www.md
```

Rules:

- Project ids are lower-case slugs (`romkade`, `xp-flightdeck`); they match the `proj:<id>` labels.
- Files are Markdown or JSON, dated with ISO dates (`2026-11-08`) and ISO weeks (`2026-W45`).
- The workspace holds no personal contact data (`guardrails.md`, People).
- Commit to the workspace's default branch for intel, metrics, reports and logs (they publish nothing). Open a
  pull request when a run changes a profile, a strategy or a campaign the owner must review.
- Commit messages: one sentence saying what changes and why; no mention of an AI, no co-author line.
- Older dated files are kept: they are the history the next runs compare against.
