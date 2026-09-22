# context.json — field reference

`context.json` is the machine-readable contract produced by this skill and
consumed by `github-implement-issue` (and any other skill that needs GitHub
issue context). Treat it as an interface: don't rename fields, and add new
optional fields rather than repurposing existing ones.

## Top level

| Field | Type | Notes |
|---|---|---|
| `schema_version` | string | `"1.0"`. Bump on breaking changes. |
| `meta.generated_at` | ISO 8601 | When this file was written. |
| `meta.github_updated_at` | ISO 8601 | The issue's `updatedAt` at generation time — the freshness key. |
| `issue` | object | See below. |
| `comments` | array | Chronological order, never filtered or summarized. |
| `assets` | array | One entry per detected attachment, including failed downloads. |
| `visual_evidence` | array | One entry per asset that was actually inspected by Claude. |
| `derived` | object | Heuristic indices extracted from the text — leads, not facts. |
| `warnings` | array of strings | Anomalies: failed downloads, detected prompt-injection attempts, and a standing reminder that `derived` is unverified. |

## `issue`

Mirrors `gh issue view --json number,title,body,author,labels,comments,state,url,createdAt,updatedAt,assignees,milestone`,
flattened to plain values (e.g. `author` is the login string, not the author object).
`repository` is `owner/name`, derived from the issue URL.

## `comments[]`

```json
{
  "id": 183728,
  "author": "some-login",
  "created_at": "...",
  "updated_at": "...",
  "url": "https://github.com/.../issues/427#issuecomment-183728",
  "body": "..."
}
```

Provenance for anything in a comment is `issue.comment:<id>` — use that id to
cite exactly which comment a claim came from.

## `assets[]`

```json
{
  "id": "asset-001",
  "type": "image",
  "source_type": "issue_body | comment",
  "source_comment_id": 183728,
  "original_url": "...",
  "local_path": "assets/issue-body-image-001.png",
  "mime_type": "image/png",
  "status": "downloaded | error | skipped_unsupported_type",
  "error": "present only when status == 'error'"
}
```

A failed download never removes the entry — it stays in the manifest with
`status: "error"` and an `error` message, and a matching line appears in
`warnings`. See `references/github-attachments.md` for the extraction and
download rules.

## `visual_evidence[]`

Written by Claude after reading a downloaded image directly (not by any
script — see `github-attachments.md`). Distinguish strictly between:

- `visible_text`: text that literally appears in the image (OCR-like reading, not paraphrase).
- `observations`: what is visually present (a UI element, a color, a layout) without interpreting it.
- `possible_code_clues`: tokens worth grepping for (a path, an identifier) — explicitly a hypothesis, never promoted to fact elsewhere in the file.

```json
{
  "asset_id": "asset-001",
  "observations": ["A red error banner is visible over an order summary screen."],
  "visible_text": ["500 Internal Server Error", "POST /api/orders"],
  "possible_code_clues": ["/api/orders", "checkout"]
}
```

## `derived`

Everything here is produced by regex heuristics in `build_context.py`, run
over the issue body and comments — no model call, no repository access.
That is deliberate: it keeps this file cheap to regenerate and honest about
what it is. None of these fields are root-cause conclusions.

| Field | How it's produced |
|---|---|
| `problem_summary` | First non-heading paragraph of the issue body (an excerpt, not a synthesis). |
| `expected_behavior` / `observed_behavior` | Text found under headings like "Expected behavior" / "Actual behavior". |
| `reproduction_steps` | List items found under a "Steps to reproduce" heading. |
| `technical_clues` | Inline code spans from the text, plus `visible_text`/`possible_code_clues` from `visual_evidence`. |
| `mentioned_files` | Tokens that look like file paths with a known extension. |
| `mentioned_components` | CamelCase-looking identifiers. |
| `mentioned_endpoints` | `METHOD /path` patterns and `/api/...`-looking paths. |

## `warnings`

Always includes a fixed reminder that `derived` is unverified. Also
includes, when applicable:
- one line per attachment that failed to download,
- one line per detected prompt-injection-style pattern in the issue text (see `github-attachments.md` — this is a heuristic safety net, not a guarantee),
- one line per `visual_evidence` entry referencing an unknown `asset_id`.
