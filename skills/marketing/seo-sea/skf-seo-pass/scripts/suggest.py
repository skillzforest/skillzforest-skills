#!/usr/bin/env python3
"""Google search suggestions: what people actually type.

Takes a language and the beginning of a search; prints the suggestions Google's search box would show
(autocomplete), one per line. The SEO agent uses it to find out which searches exist.

Usage:
    python3 suggest.py fr "anbernic ajouter"
    python3 suggest.py en "freelance invoice"
    python3 suggest.py en "freelance invoice" --country GB    # suggestions as seen from one country

This is the only network call the agent makes outside its connectors: the URL is fixed, only the language,
the country and the search text change. Standard library only.
"""

import argparse
import json
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

ENDPOINT = "https://suggestqueries.google.com/complete/search"


def fetch(url):
    """Return the body of url as text. Falls back to curl when Python has no CA certificates (python.org on macOS)."""
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (seo-agent suggest)"})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")
    except urllib.error.URLError as exc:
        if "CERTIFICATE_VERIFY_FAILED" not in str(exc):
            raise
    result = subprocess.run(["curl", "-fsS", "--max-time", "10", url], capture_output=True, check=True)
    return result.stdout.decode("utf-8", errors="replace")


def main():
    parser = argparse.ArgumentParser(description="Google autocomplete suggestions for the beginning of a search.")
    parser.add_argument("lang", help="ISO 639-1 language code, e.g. en, fr, es")
    parser.add_argument("query", help="beginning of a search, e.g. \"how to invoice\"")
    parser.add_argument("--country", help="ISO 3166 country code, e.g. US, FR (optional)")
    args = parser.parse_args()

    if not re.fullmatch(r"[a-z]{2}", args.lang):
        parser.error("lang must be a two-letter code such as en")
    if not args.query.strip():
        parser.error("query must not be empty")

    # client=firefox returns plain JSON: [query, [suggestions...], ...]
    params = {"client": "firefox", "hl": args.lang, "q": args.query}
    if args.country:
        params["gl"] = args.country.upper()
    url = f"{ENDPOINT}?{urllib.parse.urlencode(params)}"

    try:
        data = json.loads(fetch(url))
    except Exception as exc:  # network, HTTP or JSON error: say so, never invent suggestions
        print(f"suggest: no answer from Google ({exc})", file=sys.stderr)
        return 1

    for suggestion in data[1] if len(data) > 1 else []:
        print(suggestion)
    return 0


if __name__ == "__main__":
    sys.exit(main())
