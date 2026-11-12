# Indexing check

Google offers no API for the Search Console « Pages » report (« Détectée, actuellement non indexée », « Explorée,
actuellement non indexée »…). The audit and every pass rebuild it from the URL Inspection API, on **every URL of
the sitemap**, then turn the URLs that are not indexed into one tracker action per cause. Paths below are relative
to the `skf-seo-audit` folder. Search Console stays read only.

Skip when `sources.searchConsole.via` is `none` (say so in the report: the indexing state is not measured).

## 1. Inspect every sitemap URL

1. Crawl the whole sitemap: `python3 scripts/crawl.py <site.url> --max 300 --out /tmp/crawl.json` (the audit reuses
   its own crawl). A sampled crawl (`crawl-sampled`) cannot tell orphan pages: say so.
2. Inspect each URL of the crawl, one call per URL: Composio `GOOGLE_SEARCH_CONSOLE_INSPECT_URL` with
   `site_url` = `sources.searchConsole.property`, `inspection_url` = the URL, **`language_code: "en-US"`** (the
   states are then always in English), and the profile's account; or `gum read searchconsole.urlInspection.index.inspect`.
   Up to 50 calls in one Composio batch. Quota: 2,000 inspections a day per property, 600 a minute; past 300 URLs,
   inspect the 300 most important (home, `repo.pages`, newest articles, then the rest in sitemap order) and say so.
   A `429` stops the inspection: keep what you have and say how many URLs were left.
3. Append one line per URL to `/tmp/inspections.jsonl`: `{"url": "<URL>", "result": <the tool's response>}`.

The API and the « Pages » screen are not always in step (a URL « détectée » on screen can read « unknown to Google »
in the API for a few days): the cause matters, not the exact label.

## 2. Classify and find the causes

```bash
python3 scripts/indexing.py --crawl /tmp/crawl.json --inspections /tmp/inspections.jsonl \
        --site-name "<site.name>" --protected "<repo.protected, comma-separated>" \
        --lang <style.reportLanguage> --date <YYYY-MM-DD> --out <paths.reports>indexing-<YYYY-MM-DD>.json
```

It prints the states like the « Pages » report (indexed, discovered, crawled, unknown, duplicate, noindex, robots,
error) and one action per cause, with its URLs:

| Cause | Who | Priority | What the fix is |
|---|---|---|---|
| `page-error` | agent | P1 | restore the page or remove it from the sitemap, routes and links |
| `noindex` | agent | P1 | remove noindex, or take the page out of the sitemap |
| `canonical` | agent | P1 | canonical to itself, or drop the copy from the sitemap |
| `foreign-brand` | agent | P2 | **delete** the pages of another brand: files, routes, sitemap, hreflang, links |
| `duplicate` | agent | P2 | translate the version left in another language, or keep one and drop the others |
| `orphan` | agent | P2 | plain HTML links from the templates (menu, footer, lists), or drop the page |
| `crawled-not-indexed` | agent | P2 | enrich, merge or drop the page |
| `awaiting-crawl` | owner | P3 | request indexing in Search Console, 10 a day at most |

A cause covering a fifth of the sitemap or more becomes `P1`. Read the result with judgement before filing it:

- **Another brand's pages** (`foreign-brand`, title ending with a brand other than `site.name`) are found on every
  page of the crawl, indexed or not: a site carries its own brand only. The fix is to delete them, never to
  redirect them to the other brand's site, unless the profile's `style.rules` say otherwise.
- **Pages outside the site's navigation**: a page of the sitemap that the site's own menu and footer never link to
  is either worth a link (`orphan`) or not worth keeping. When it duplicates another page or serves another brand,
  the fix is to delete it.
- Files listed in `repo.protected`: the action stays `agent` in the report but is filed `owner`, its body saying
  « ajouter `claude:fix` pour que la tâche de correction le fasse » (the fix task may touch protected files for
  that issue only). With `features` lacking `fix`, the owner does it.

## 3. File the actions

Upsert each action in the tracker (`../skf-seo-profile/references/tracker.md`) with its `id` (`indexing:<cause>`),
`title`, `who`, `priority` and `body` from the JSON. An `indexing:*` action already open is updated with the new URL
list; one whose cause is gone (no URL left) is closed with a comment saying so. Older actions that name the same
pages (`orphan-page:*`, `title-duplicate:*`, `not-indexed:*`) are closed with a comment pointing to the
`indexing:*` action, so the owner reads one action per cause.

The `awaiting-crawl` action lists the URLs to submit, most important first (home, `repo.pages`, newest articles),
10 at most for the next day; the owner can ask Claude to submit them in the desktop app's browser.

## 4. Report

- The scorecard gets `--indexing <indexed>,<total>` (`scorecard.md`): the line « Indexation : N/M pages indexées »
  with its change.
- The report gives the states table, the actions and their URLs, and the number of URLs not inspected (quota).
- The final answer gives the line « Indexation : N/M » and the `P1` indexing actions.
