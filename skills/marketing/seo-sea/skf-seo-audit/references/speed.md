# Speed at every run

Every scheduled run (`skf-seo-pass` or `skf-seo-watch`), even when nothing else is done, when `sources.pagespeed` is
true and the `PAGESPEED_KEY` environment variable is set (without a key the shared quota is almost always exhausted:
say once in the final answer that a free key is missing, and skip). Paths below are relative to the `skf-seo-audit`
folder.

0. Check the key without printing it: `[ -n "$PAGESPEED_KEY" ] && echo key || echo no key`. Never say a key
   is missing without running this check.
1. Measure the home page and the two pages with the most impressions (or the first two `repo.pages`), mobile:
   `python3 scripts/pagespeed.py <urls> --strategy mobile --csv <paths.reports>pagespeed.csv`.
   Commit the history file with the rest of the run (mode `repo`: in the run's pull request if there is one,
   otherwise leave it for the next one — never push to the base branch for it; mode `advise`: on the workspace's
   base branch).
2. Compare with the previous line of the same page in the history. Create or update one tracker action
   (`id: speed:<page path>`, `who: agent` when the cause is in the site's code — heavy images, scripts, fonts —
   `owner` when it is the host or a third-party script) when:
   - performance is under 50 (`P2`), or under 90 for the home page (`P3`);
   - performance lost 15 points or more since the previous measure (`P2`: a regression, say which change may have
     caused it);
   - LCP over 4 s or CLS over 0.25 (`P2`).
   Give the figures and the PageSpeed report link (`https://pagespeed.web.dev/analysis?url=<page>`) in the action.
3. When an open `speed:` action's page is back to normal, close it with the new figures.
4. Report the three scores in the run's report (or the final answer) on one line.
