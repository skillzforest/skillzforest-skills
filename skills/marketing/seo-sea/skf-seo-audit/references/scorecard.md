# Scorecard

Every audit, and every scheduled run after it (`skf-seo-pass` or `skf-seo-watch`), measures the site the same way so
the owner sees whether its SEO is good and where it is heading — continuous SEO needs a number that moves. Paths
below are relative to the `skf-seo-audit` folder.

1. Crawl the live site: `python3 scripts/crawl.py <site.url> --max 100 --out /tmp/crawl.json` (the audit uses its
   own full crawl instead).
2. Count the open tracker actions by priority (`P1,P2,P3`, the scorecard item itself excluded).
3. Search Console totals of the analysis window and of the previous one, when there is a property.
4. Read the previous card: the tracker item `seo-id: scorecard` (GitHub: the issue labeled `seo:scorecard`; Jira:
   the issue labeled `seo-scorecard`; sheet: the tab `Scorecard`). Save its body to `/tmp/previous.md`.
5. `python3 scripts/scorecard.py --site <site.name> --crawl /tmp/crawl.json --pagespeed <paths.reports>pagespeed.csv
   --actions <P1,P2,P3> [--sc <clicks,impressions,position> --sc-prev <…>] --previous /tmp/previous.md
   --lang <style.reportLanguage>` prints the card: a score out of 100 (technical /50, speed /25, open actions /25),
   a status 🟢 / 🟠 / 🔴 and the change since the previous card.
6. Publish it, never on the site's base branch:
   - GitHub issues: one issue per site, title `📊 Tableau de bord SEO — <site.name>` (in `style.reportLanguage`),
     labels `seo` and `seo:scorecard`, body = the card. Create it once, then edit its body at every run and add a
     comment with one line, `<date> — <summary>`, so the comments are the history. Never close it, never give it
     `seo:agent`, `seo:owner` or `claude:fix`.
   - Jira: the same as one issue labeled `seo` and `seo-scorecard`, its description = the card, a comment per run.
   - Google Sheets: a tab `Scorecard`, one row per run (date, score, status, technical, speed, actions, clicks,
     impressions, position).
7. Give the card's first line in the report and the final answer.

The score is a trend indicator, not an absolute grade: say so when the owner asks. A score that drops 10 points or
more since the previous card, or turns 🔴, is told to the owner in the same run, with the cause (which part fell).
