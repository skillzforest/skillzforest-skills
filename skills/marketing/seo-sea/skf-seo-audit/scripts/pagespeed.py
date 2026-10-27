#!/usr/bin/env python3
"""Core Web Vitals and Lighthouse scores of a few pages, from Google PageSpeed Insights.

Usage:
    python3 pagespeed.py https://example.com/ https://example.com/pricing/ [--strategy mobile|desktop]

For each URL prints the Lighthouse performance and SEO scores, the lab metrics (LCP, CLS, TBT) and, when Google has
enough visits, the field data of real Chrome users (LCP, INP, CLS at the 75th percentile). No API key is needed for
a few calls; set PAGESPEED_KEY in the environment for more. Standard library only (curl fallback for certificates).
"""

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

ENDPOINT = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"


def fetch_json(url):
    """Return the API's JSON, raising with Google's own message on an API error (quota, bad URL)."""
    try:
        with urllib.request.urlopen(url, timeout=120) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        data = json.loads(exc.read().decode("utf-8") or "{}")
    except urllib.error.URLError as exc:
        if "CERTIFICATE_VERIFY_FAILED" not in str(exc):
            raise
        result = subprocess.run(["curl", "-sS", "--max-time", "120", url], capture_output=True, check=True)
        data = json.loads(result.stdout.decode("utf-8"))
    if "error" in data:
        # The keyless quota is shared by everyone and often exhausted: a free key in PAGESPEED_KEY avoids it.
        raise RuntimeError(f"{data['error'].get('code')}: {data['error'].get('message', '')[:160]}")
    return data


def main():
    parser = argparse.ArgumentParser(description="PageSpeed Insights for a few pages.")
    parser.add_argument("urls", nargs="+", help="pages to test (keep it to 10 or fewer)")
    parser.add_argument("--strategy", choices=("mobile", "desktop"), default="mobile")
    args = parser.parse_args()

    results = []
    for page in args.urls[:10]:
        params = [("url", page), ("strategy", args.strategy), ("category", "performance"), ("category", "seo")]
        if os.environ.get("PAGESPEED_KEY"):
            params.append(("key", os.environ["PAGESPEED_KEY"]))
        try:
            data = fetch_json(f"{ENDPOINT}?{urllib.parse.urlencode(params)}")
        except Exception as exc:
            print(f"{page}: no answer from PageSpeed Insights ({exc})", file=sys.stderr)
            continue

        lighthouse = data.get("lighthouseResult", {})
        categories = lighthouse.get("categories", {})
        audits = lighthouse.get("audits", {})
        field = data.get("loadingExperience", {}).get("metrics", {})

        def score(name):
            value = categories.get(name, {}).get("score")
            return None if value is None else round(value * 100)

        def lab(audit):
            return audits.get(audit, {}).get("displayValue")

        def p75(metric):
            return field.get(metric, {}).get("percentile")

        row = {
            "url": page,
            "strategy": args.strategy,
            "performance": score("performance"),
            "seo": score("seo"),
            "lab": {"LCP": lab("largest-contentful-paint"), "CLS": lab("cumulative-layout-shift"), "TBT": lab("total-blocking-time")},
            "field": {
                "LCP_ms": p75("LARGEST_CONTENTFUL_PAINT_MS"),
                "INP_ms": p75("INTERACTION_TO_NEXT_PAINT"),
                "CLS_x100": p75("CUMULATIVE_LAYOUT_SHIFT_SCORE"),
            } if field else None,
        }
        results.append(row)
        print(f"{page} [{args.strategy}] performance {row['performance']}, SEO {row['seo']}, "
              f"LCP {row['lab']['LCP']}, CLS {row['lab']['CLS']}, TBT {row['lab']['TBT']}"
              + ("" if field else " (not enough real visits for field data)"))

    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0 if results else 1


if __name__ == "__main__":
    sys.exit(main())
