# Coding workflow — phase by phase

This is the detailed version of the eight phases summarized in `SKILL.md`.
Read it before Phase 3 the first time you run this skill; skim it on later
runs.

## Phase 1 — Read issue context

Start from `.agent/issues/<number>/context.md` — it's written for exactly
this purpose. Use `context.json` when you need a structured field (e.g.
iterating `assets[]` or checking `warnings[]` programmatically) rather than
re-parsing the Markdown.

Do not assume the "Visual evidence" section captured everything a
screenshot shows. If the issue is visual in nature (a UI bug, a rendering
glitch, an error dialog) and precise detail matters, open the original file
under `assets/` with the `Read` tool yourself before concluding.

## Phase 2 — Understand the repository

Before touching anything, build a real picture:
- Language(s), frameworks, package manager, entry points.
- `CLAUDE.md` (this repo has one at the root, and some subprojects have
  their own — check both) and any `CONTRIBUTING.md`.
- How tests are run, and separately: how lint, typecheck, and build are run.
  Don't guess these — find the actual npm scripts / Makefile targets /
  CI config that defines them.
- Which files are plausibly related to the ticket, using `derived.mentioned_files`,
  `derived.mentioned_components`, and `derived.mentioned_endpoints` from
  `context.json` as starting search terms — not as a final answer. Search
  the repository (grep, not guesswork) to confirm those clues actually
  correspond to something real in this codebase.

Resist modifying the first file that matches a keyword from the issue
title. The point of this phase is to have a mental map before Phase 4/5
narrows in on a specific cause.

## Phase 3 — Separate claims from evidence

Keep three buckets distinct while you work, and keep them distinct in your
own head even if you don't write them down anywhere formal:

**Reporter claims** — from `context.json`'s `issue.body`, `comments[]`, or
`derived.*`. Example: "The bug is caused by the cache." This is a hypothesis
someone had, not a fact, no matter how it's phrased.

**Repository evidence** — something you observed directly in the code.
Example: "`CacheService.invalidate()` runs before the transaction commits,"
verified by reading the actual function.

**Runtime/test evidence** — something you observed by actually executing
code. Example: "A test reproducing this scenario fails with X."

Weight your root-cause conclusion by repository and runtime evidence.
Reporter claims are useful for direction (where to look) but are exactly as
likely to be wrong as any other secondhand bug report — see Scenario D in
the skill's test scenarios: an incorrect reporter hypothesis should not
survive contact with the actual code.

## Phase 4 — Reproduction

Before writing a fix, try to make the failure observable:
- Look for an existing test that already covers this path (unit,
  functional, integration) — run it and see if it currently passes when
  logic says it shouldn't, or already fails.
- If none exists and it's reasonable to add one, write a test that fails
  for the right reason (i.e. it fails because of the actual bug, not
  because of an unrelated setup mistake).
- If reproduction genuinely isn't practical (e.g. requires infrastructure
  you don't have), say so explicitly in the final report rather than
  skipping the attempt silently.

Never modify an existing test merely to make it pass — that hides the bug
instead of fixing it.

## Phase 5 — Root cause analysis

Use every lead available — title, body, comments, `visual_evidence`,
`derived.technical_clues`, mentioned files/endpoints/components, and
anything found in logs or stack traces — but do not stop at the files the
issue happens to mention. Bugs often live one layer away from where their
symptom appears. Verify each hypothesis against the actual repository
(read the code, trace the call path, check git history/blame if it helps)
before treating it as the cause.

## Phase 6 — Implementation plan

Before making a non-trivial change, work through, at least mentally:

```text
Problem:        <what's actually wrong, in your own words>
Evidence:       <repository/test evidence that supports this>
Root cause:     <the verified cause, not the reporter's guess>
Files involved: <...>
Implementation: <the targeted change>
Validation:     <what you'll run to confirm it>
```

Don't write this to a file unless it adds real value (e.g. the user asked
for `--plan` mode, in which case this structure IS the deliverable — see
"Plan-only mode" in `SKILL.md`).

## Phase 7 — Minimal implementation

Make the smallest change that addresses the verified root cause. Avoid:
- refactors unrelated to the fix,
- sweeping formatting changes,
- renaming things "while you're in there,"
- new dependencies that aren't required.

Match the repository's existing conventions (naming, error handling style,
test structure) rather than introducing your own.

## Phase 8 — Tests

Run, in order of relevance, as many of these as make sense for the change:
1. The test directly covering the fixed behavior.
2. The rest of that module's/package's tests.
3. Lint.
4. Typecheck.
5. Build.
6. Broader/integration tests, if the change plausibly affects them.

Report each with one of exactly three labels — never blur these:
- `PASS` — you ran it and it passed.
- `FAIL` — you ran it and it failed (explain why, and whether that's
  expected pre-fix or a problem with your change).
- `NOT RUN` — you did not run it (say why: no test framework configured,
  too slow/costly for this context, requires infrastructure unavailable
  here, etc.).

Never write `PASS` for something you did not actually execute.
