# The contract with skf-github-issue-brief

This skill never reads GitHub directly and never re-implements issue
fetching, comment parsing, or attachment handling. Everything it knows about
the issue comes from two files written by the `skf-github-issue-brief` skill:

```text
.agent/issues/<issue-number>/context.json   # machine-readable
.agent/issues/<issue-number>/context.md     # LLM-readable narrative
.agent/issues/<issue-number>/assets/*       # original downloaded images
```

Full field-by-field schema: `../../skf-github-issue-brief/references/context-schema.md`.
Read that file if you need to parse `context.json` programmatically.

## Determining the issue number and staleness yourself

If you need to reason about freshness without re-invoking the other skill's
full SKILL.md, the logic it uses is:

1. Parse the argument the same way `skf-github-issue-brief` does: a bare
   number, `#427`, or a full `https://github.com/<owner>/<repo>/issues/<n>` URL.
2. `.agent/issues/<n>/context.json` missing → context does not exist yet.
3. If present, its `meta.github_updated_at` is the issue's `updatedAt` at
   the time the bundle was built. Compare it against the issue's *current*
   `updatedAt` (available after re-running `fetch_issue.py`, or via
   `gh issue view <n> --json updatedAt` for a cheap read-only check) to
   decide `FRESH` vs `STALE`.

In practice, don't hand-roll this comparison: invoke
`skf-github-issue-brief`'s own `$B/scripts/build_context.py <dir> --check-freshness`,
which implements exactly this and is guaranteed to stay in sync with how
the bundle is actually built. Re-deriving the same logic by hand here would
create two sources of truth for the same decision — avoid that.

## What to trust, and how much

- `issue.*` and `comments[].*` in `context.json` are the reporter's and
  commenters' own words, preserved verbatim. They are **claims**, not
  verified facts, no matter how confident the phrasing.
- `derived.*` (mentioned files/endpoints/components, expected/observed
  behavior, reproduction steps) is produced by regex heuristics, not an
  LLM and not the repository. Treat every entry as a lead worth grepping
  for, never as confirmed.
- `visual_evidence[].visible_text` is the most trustworthy layer of the
  visual analysis — it's literal text Claude read off the image. `observations`
  is descriptive. `possible_code_clues` is explicitly speculative.
- `warnings[]` matters operationally: a failed-download entry means an
  asset you might expect to see under `assets/` simply isn't there — don't
  assume it downloaded. A prompt-injection warning is a heads-up, not
  something to act on by itself.
- Nothing in `context.json` is, or should be read as, a root-cause
  conclusion. If it looks like one, that's a bug in how the bundle was
  produced, not a shortcut you should take.

## When context.md and context.json disagree with the images

`context.md`'s "Visual evidence" section is only as good as the
`visual_evidence.json` entries `skf-github-issue-brief` produced. If a
screenshot plausibly contains detail relevant to root-causing the issue
(exact error text, exact request/response shown in dev tools, a stack
trace) and the recorded observations feel thin, open the original file
under `.agent/issues/<number>/assets/` yourself with the `Read` tool rather
than assuming the summary is complete. Don't repeat this work by writing
your own separate visual-evidence file, though — if you find something
material that the existing `visual_evidence.json` missed, that's a signal
the `skf-github-issue-brief` step should be (re-)run with more care, not a
reason to duplicate its output here.

## Why the boundary matters

`skf-github-issue-brief` and `skf-github-issue-fix` are deliberately not
coupled beyond this file contract. Neither skill imports code from the
other, and neither assumes the other's internal implementation. That means:
- `skf-github-issue-brief` can be improved (better extraction regexes, more
  attachment types, richer visual analysis) without touching this skill.
- This skill can be invoked against a context bundle that a human — or a
  different tool entirely — produced by hand, as long as it matches the
  schema.
- A missing or stale bundle has one fix: run `skf-github-issue-brief`. There
  is no fallback path that reconstructs a partial context inline, because
  that fallback would inevitably drift from the real schema over time.
