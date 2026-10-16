#!/usr/bin/env python3
"""Pipeline mode: hand a prepared skill zip to the API so n8n drives the review
(claim → A ∥ B → gate/approval → functional → judge → email). Standard library only.

    queue_review.py <skill.zip> [--item <catalog-slug>] [--wait <minutes>]

Without --item: upload (kind=file) then POST /review-jobs — no catalog item, so no
example prompt: the functional test is skipped and the verdict is at best `warn`.
With --item: the zip is attached to that catalog item as a new file (the API queues the
review itself), and the item's page `usage` prompt drives the functional test. This
changes what users of that item can install: only do it once the user has agreed.

Environment:
  SKF_API_URL           default http://api.localhost:9080/api/v1
  SKF_ADMIN_TOKEN       Supabase access token of an admin (upload / attach)
  REVIEW_SERVICE_TOKEN  same value as the API's (queue / poll)

Prints the job as JSON; with --wait, polls until it's done or failed and prints the
final job with its report. Exit 0 pass, 1 warn, 2 fail, 4 still running, 5 error.
"""

import argparse
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

API = os.environ.get("SKF_API_URL", "http://api.localhost:9080/api/v1").rstrip("/")


def call(method: str, path: str, *, body=None, headers=None, raw: bytes | None = None):
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    request = urllib.request.Request(f"{API}{path}", data=data, method=method)
    if body is not None:
        request.add_header("Content-Type", "application/json")
    for key, value in (headers or {}).items():
        request.add_header(key, value)
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            text = response.read().decode()
            return json.loads(text) if text else None
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:500]
        print(json.dumps({"error": f"{method} {path} → {exc.code}", "detail": detail}))
        sys.exit(5)


def multipart(path: Path) -> tuple[bytes, str]:
    boundary = uuid.uuid4().hex
    kind = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    head = (
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{path.name}"\r\n'
        f"Content-Type: {kind}\r\n\r\n"
    ).encode()
    return head + path.read_bytes() + f"\r\n--{boundary}--\r\n".encode(), boundary


def need(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        print(json.dumps({"error": f"{name} is not set"}))
        sys.exit(5)
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("zip")
    parser.add_argument("--item", help="catalog slug to attach the file to")
    parser.add_argument("--version", help="version recorded with the attached file")
    parser.add_argument("--wait", type=float, default=0, help="minutes to wait for the verdict")
    args = parser.parse_args()

    admin = {"Authorization": f"Bearer {need('SKF_ADMIN_TOKEN')}"}
    review = {"X-Review-Token": need("REVIEW_SERVICE_TOKEN")}

    body, boundary = multipart(Path(args.zip))
    stored = call(
        "POST",
        "/admin/uploads?kind=file",
        raw=body,
        headers={**admin, "Content-Type": f"multipart/form-data; boundary={boundary}"},
    )

    if args.item:
        page = call("GET", f"/admin/catalog?q={args.item}&limit=100", headers=admin)
        match = next((row for row in page["items"] if row["slug"] == args.item), None)
        if match is None:
            print(json.dumps({"error": f"no catalog item with slug {args.item}"}))
            sys.exit(5)
        call(
            "POST",
            f"/admin/catalog/{match['id']}/files",
            body={"stored_file_id": stored["id"], "version": args.version},
            headers=admin,
        )
        jobs = call("GET", f"/review-jobs?stored_file_id={stored['id']}&limit=1", headers=review)
        if not jobs:
            print(json.dumps({"error": "file attached but no review job was queued"}))
            sys.exit(5)
        job = jobs[0]
    else:
        job = call("POST", "/review-jobs", body={"stored_file_id": stored["id"]}, headers=review)

    deadline = time.time() + args.wait * 60
    while job["status"] in ("queued", "running") and time.time() < deadline:
        time.sleep(20)
        job = call("GET", f"/review-jobs/{job['id']}", headers=review)
    if job["status"] in ("queued", "running"):
        print(json.dumps(job, ensure_ascii=False, indent=2))
        sys.exit(4)
    if job["status"] == "done":
        job = call("GET", f"/review-jobs/{job['id']}", headers=review)
    print(json.dumps(job, ensure_ascii=False, indent=2))
    sys.exit({"pass": 0, "warn": 1, "fail": 2}.get(job.get("verdict") or "", 5))


if __name__ == "__main__":
    main()
