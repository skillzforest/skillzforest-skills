# Pass report

One file per pass that changes or recommends something: `<paths.reports><YYYY-MM-DD>.md`, written in
`style.reportLanguage`. In mode `repo` it is also the pull request's body. Keep it short: the owner reads it on a
phone before merging.

```markdown
# SEO pass — <site.name> — <YYYY-MM-DD>

## Summary
<Two sentences: what was done or recommended, and why it should bring visitors.>

## Figures (<window start> → <window end>, compared with the 28 days before)
| | Now | Before |
|---|---|---|
| Impressions | | |
| Clicks | | |
| Average CTR | | |
| Average position | | |

Top 15 searches:
| Search | Page | Impressions | Clicks | CTR | Position |
|---|---|---|---|---|---|

## Demand
<Autocomplete, Trends (worldwide, relative interest) and search results that weighed in the choice. Say these are
signs of demand, not volumes.>

## Opportunities
1. <The one chosen — why, with the figures.>
2. <The next ones, one line each: candidates for the next passes.>

## Change
<Files touched (mode repo) or the page and field to change (mode advise). For a title or description: before and
after, per language. For an article: title, slug and URL per language.>

## How to measure it
<The search and page to watch in Search Console, and when (usually 3 to 4 weeks).>

## For the owner
<Pages to submit for indexing, a connector to renew, a screenshot to make, an owner action created in
the tracker (with its link).
"Nothing" when there is nothing.>
```

When the pass changes nothing, no file: the same sections, shortened, go in the final answer.
