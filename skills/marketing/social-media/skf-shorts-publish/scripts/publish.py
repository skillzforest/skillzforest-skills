#!/usr/bin/env python3
"""Publish a rendered short on social networks — through Postiz, or as a manual upload kit.
Stdlib only.

    publish.py validate <short>                    check publish.json (lengths, files, hashtags)
    publish.py kit <short> [--out <dir>]           manual kit: one folder per network + UPLOAD.md
    publish.py check                               Postiz connection test
    publish.py integrations [--json]               channels connected in Postiz
    publish.py settings <integration_id>           live posting rules and settings schema
    publish.py bind <short> [--write]              match publish.json targets to Postiz channels
    publish.py send <short> [--only a,b] [--type now|schedule|draft] [--date ISO] [--dry-run] [--force]
    publish.py status [--from ISO] [--to ISO]      posts in a date range and their links

<short> is the folder shorts/<slug> (publish.json, out/). Postiz configuration:
POSTIZ_URL (self-hosted, e.g. http://127.0.0.1:4007, or https://api.postiz.com for
Postiz Cloud) and POSTIZ_API_KEY, from the environment or the first .env found walking
up from the current directory (or $SKF_SOCIAL_HOME/.env). The key is never printed.

In a target's settings, a value "@upload:<file>" (relative to the short) is uploaded
and replaced by the Postiz media reference: that is how a cover or thumbnail goes into
a network field that accepts one (see `settings <id>`).
"""
import argparse
import datetime as dt
import hashlib
import json
import mimetypes
import os
import re
import shutil
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

LIMITS = {  # characters of the post text (YouTube: description), title, hashtags
    "youtube": {"text": 5000, "title": 100, "hashtags": 15},
    "tiktok": {"text": 2200, "hashtags": 8},
    "instagram": {"text": 2200, "hashtags": 30},
    "x": {"text": 280, "hashtags": 3, "url": 23},
    "bluesky": {"text": 300, "hashtags": 3},
    "linkedin": {"text": 3000, "hashtags": 5},
    "threads": {"text": 500, "hashtags": 1},
    "facebook": {"text": 63206, "hashtags": 5},
}
SETTINGS = {  # Postiz "settings" defaults; the live schema is `settings <id>`
    "youtube": {"__type": "youtube", "type": "public", "selfDeclaredMadeForKids": "no", "tags": []},
    "tiktok": {"__type": "tiktok", "privacy_level": "PUBLIC_TO_EVERYONE", "duet": False, "stitch": False,
               "comment": True, "autoAddMusic": "no", "brand_content_toggle": False,
               "brand_organic_toggle": True, "content_posting_method": "DIRECT_POST"},  # « your brand » disclosure
    "instagram": {"__type": "instagram", "post_type": "post"},
    "x": {"__type": "x", "who_can_reply_post": "everyone"},
    "bluesky": {"__type": "bluesky"},
    "linkedin": {"__type": "linkedin", "post_as_images_carousel": False},
    "threads": {"__type": "threads"},
    "facebook": {"__type": "facebook"},
}
UPLOAD = {
    "youtube": ("YouTube Studio", "https://studio.youtube.com", [
        "Créer → Importer des vidéos → short-9x16.mp4 (vertical ≤ 3 min : classé Short automatiquement).",
        "Titre : title.txt ; description : caption.txt.",
        "Miniature : sur l'application mobile, choisir l'image 0 de la vidéo (elle reprend la cover) ; "
        "sur ordinateur, importer thumb-16x9.jpg si le champ est proposé."]),
    "tiktok": ("TikTok Studio", "https://www.tiktok.com/tiktokstudio/upload", [
        "Importer short-9x16.mp4, coller caption.txt.",
        "Couverture : choisir la première image (elle reprend la cover), ou importer cover-9x16.jpg si proposé."]),
    "instagram": ("Instagram", "https://www.instagram.com/", [
        "Créer → Reel (ou depuis l'application mobile) → short-9x16.mp4.",
        "Couverture : « Modifier la couverture » → Ajouter depuis la pellicule → cover-9x16.jpg ; "
        "vérifier le recadrage de la grille du profil.",
        "Légende : caption.txt."]),
    "x": ("X", "https://x.com/compose/post", [
        "Joindre la vidéo (short-4x5.mp4 si présent, sinon short-9x16.mp4) et coller caption.txt."]),
    "bluesky": ("Bluesky", "https://bsky.app/", [
        "Nouveau post → joindre la vidéo (≤ 100 Mo, ≤ 3 min), coller caption.txt, ajouter le texte alternatif (alt.txt)."]),
    "linkedin": ("LinkedIn", "https://www.linkedin.com/feed/", [
        "Commencer un post → Vidéo → short-4x5.mp4 si présent ; miniature : cover-4x5.jpg ; texte : caption.txt."]),
    "threads": ("Threads", "https://www.threads.net/", ["Nouveau thread → joindre la vidéo, coller caption.txt."]),
    "facebook": ("Facebook", "https://www.facebook.com/", ["Créer un Reel → short-9x16.mp4, couverture cover-9x16.jpg, texte caption.txt."]),
}


# ---------------------------------------------------------------- files

def load(short):
    short = Path(short).resolve()
    path = short / "publish.json"
    if not path.is_file():
        sys.exit(f"publish.json introuvable dans {short}")
    return short, path, json.loads(path.read_text())


def full_text(target):
    text = target.get("text", "").rstrip()
    tags = [t if t.startswith("#") else f"#{t}" for t in target.get("hashtags", [])]
    missing = [t for t in tags if t.lower() not in text.lower()]
    return (text + ("\n\n" + " ".join(missing) if missing else "")).strip()


def text_length(platform, text):
    if platform == "x":  # every URL counts as 23 characters
        text = re.sub(r"https?://\S+", "x" * LIMITS["x"]["url"], text)
    if platform == "bluesky":  # graphemes, roughly: combining marks do not count
        return sum(1 for ch in text if not unicodedata.combining(ch))
    return len(text)


def cmd_validate(args):
    short, _, pub = load(args.short)
    errors, warnings = [], []
    if pub.get("status") not in ("draft", "approved", "published", "scheduled", "drafted", "partial"):
        errors.append(f"status inconnu : {pub.get('status')}")
    when = pub.get("when") or {}
    if when.get("type") == "schedule":
        try:
            date = dt.datetime.fromisoformat(when["date"].replace("Z", "+00:00"))
            if date < dt.datetime.now(dt.timezone.utc):
                errors.append(f"date programmée dans le passé : {when['date']}")
        except (KeyError, ValueError):
            errors.append("when.date manquante ou illisible (ISO 8601, ex. 2026-11-20T17:00:00Z)")
    seen = set()
    for t in pub.get("targets", []):
        p = t.get("platform")
        label = f"[{p}]"
        if p not in LIMITS:
            errors.append(f"{label} plateforme inconnue")
            continue
        if p in seen:
            warnings.append(f"{label} deux cibles pour le même réseau (deux comptes ?)")
        seen.add(p)
        if t.get("skip"):
            continue
        for key in ("video", "cover"):
            if t.get(key) and not (short / t[key]).is_file():
                errors.append(f"{label} {key} absent : {t[key]}")
        if not t.get("video"):
            errors.append(f"{label} aucune vidéo")
        text = full_text(t)
        n, limit = text_length(p, text), LIMITS[p]["text"]
        if n > limit:
            errors.append(f"{label} texte {n} > {limit} caractères")
        if not text:
            warnings.append(f"{label} texte vide")
        if len(t.get("hashtags", [])) > LIMITS[p]["hashtags"]:
            warnings.append(f"{label} {len(t['hashtags'])} hashtags (conseillé ≤ {LIMITS[p]['hashtags']})")
        if p == "youtube":
            title = t.get("title", "")
            if not title:
                errors.append(f"{label} titre manquant")
            elif len(title) > LIMITS["youtube"]["title"]:
                errors.append(f"{label} titre {len(title)} > 100 caractères")
            elif len(title) > 60:
                warnings.append(f"{label} titre de {len(title)} caractères : coupé après ~60 dans le fil")
        if p == "bluesky" and not t.get("alt"):
            warnings.append(f"{label} pas de texte alternatif (alt) pour la vidéo")
        for k, v in (t.get("settings") or {}).items():
            if isinstance(v, str) and v.startswith("@upload:") and not (short / v[8:]).is_file():
                errors.append(f"{label} settings.{k} : fichier absent {v[8:]}")
    ok = not errors
    print(json.dumps({"ok": ok, "errors": errors, "warnings": warnings}, ensure_ascii=False, indent=2))
    sys.exit(0 if ok else 1)


def cmd_kit(args):
    short, _, pub = load(args.short)
    out = Path(args.out).resolve() if args.out else short / "upload-kit"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    lines = [f"# Kit de publication — {short.name}", "",
             "Chaque dossier contient la vidéo, la cover et les textes prêts à coller.", ""]
    for t in pub.get("targets", []):
        if t.get("skip"):
            continue
        p = t["platform"]
        folder = out / p
        folder.mkdir()
        for key in ("video", "cover"):
            if t.get(key):
                shutil.copy2(short / t[key], folder / Path(t[key]).name)
        (folder / "caption.txt").write_text(full_text(t) + "\n")
        if t.get("title"):
            (folder / "title.txt").write_text(t["title"] + "\n")
        if t.get("alt"):
            (folder / "alt.txt").write_text(t["alt"] + "\n")
        name, url, steps = UPLOAD.get(p, (p, "", []))
        date = t.get("date") or (pub.get("when") or {}).get("date")
        lines += [f"## {name}", "", f"Ouvrir {url}" + (f" — à publier le {date}" if date else ""), ""]
        lines += [f"{i}. {s}" for i, s in enumerate(steps, 1)] + [""]
    (out / "UPLOAD.md").write_text("\n".join(lines))
    print(f"kit prêt : {out}")


# ---------------------------------------------------------------- Postiz

def load_env():
    candidates = []
    if os.environ.get("SKF_SOCIAL_HOME"):
        candidates.append(Path(os.environ["SKF_SOCIAL_HOME"]) / ".env")
    cwd = Path.cwd()
    candidates += [p / ".env" for p in [cwd, *cwd.parents]]
    for path in candidates:
        if not path.is_file():
            continue
        values = {}
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                values[key.strip()] = value.strip().strip("'\"")
        if "POSTIZ_API_KEY" in values or "POSTIZ_URL" in values:
            for key, value in values.items():
                os.environ.setdefault(key, value)
            return


def api_base():
    url = os.environ.get("POSTIZ_URL", "http://127.0.0.1:4007").rstrip("/")
    if url.endswith("/public/v1"):
        return url
    return f"{url}/public/v1" if "api.postiz.com" in url else f"{url}/api/public/v1"


def request(method, path, body=None, params=None, raw=None, content_type=None):
    key = os.environ.get("POSTIZ_API_KEY")
    if not key:
        sys.exit("POSTIZ_API_KEY manquant : Postiz → Settings → Developers (Public API), puis dans .env — "
                 "ou utiliser `publish.py kit` pour publier à la main")
    url = api_base() + path + ("?" + urllib.parse.urlencode(params) if params else "")
    headers = {"Authorization": key, "Accept": "application/json"}
    data = raw
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    elif content_type:
        headers["Content-Type"] = content_type
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            return json.loads(resp.read().decode() or "null")
    except urllib.error.HTTPError as exc:
        sys.exit(f"Postiz {method} {path} → HTTP {exc.code}\n{exc.read().decode(errors='replace')[:2000]}")
    except urllib.error.URLError as exc:
        sys.exit(f"Postiz injoignable ({api_base()}) : {exc.reason}")


def upload(path: Path):
    boundary = uuid.uuid4().hex
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    head = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{path.name}\"\r\n"
            f"Content-Type: {mime}\r\n\r\n").encode()
    tail = f"\r\n--{boundary}--\r\n".encode()
    return request("POST", "/upload", raw=head + path.read_bytes() + tail,
                   content_type=f"multipart/form-data; boundary={boundary}")


def integrations():
    res = request("GET", "/integrations")
    return res if isinstance(res, list) else res.get("integrations", res)


def cmd_check(_):
    active = [i for i in integrations() if not i.get("disabled")]
    print(f"OK — {api_base()} — {len(active)} canal(aux) connecté(s)")


def cmd_integrations(args):
    items = integrations()
    if args.json:
        print(json.dumps(items, ensure_ascii=False, indent=2))
        return
    for i in items:
        flag = " (désactivé)" if i.get("disabled") else ""
        print(f"{i.get('id')}  {i.get('identifier', ''):<22} {i.get('name')}  @{i.get('profile')}{flag}")
    if not items:
        print("Aucun canal connecté (Postiz → Add Channel).")


def cmd_settings(args):
    print(json.dumps(request("GET", f"/integration-settings/{args.id}"), ensure_ascii=False, indent=2))


def identifier_matches(platform, identifier):
    identifier = identifier or ""
    return identifier == platform or identifier.startswith(platform + "-") or (platform == "instagram" and identifier.startswith("instagram"))


def cmd_bind(args):
    short, path, pub = load(args.short)
    items = [i for i in integrations() if not i.get("disabled")]
    changed = False
    for t in pub.get("targets", []):
        if t.get("integrationId") and any(i["id"] == t["integrationId"] for i in items):
            print(f"= {t['platform']:<10} déjà lié ({t['integrationId']})")
            continue
        found = [i for i in items if identifier_matches(t["platform"], i.get("identifier"))]
        if t.get("account") and len(found) > 1:
            wanted = t["account"].lower().lstrip("@")
            found = [i for i in found if wanted in (str(i.get("profile", "")).lower(), str(i.get("name", "")).lower())] or found
        if len(found) == 1:
            t["integrationId"] = found[0]["id"]
            changed = True
            print(f"+ {t['platform']:<10} → {found[0]['id']} ({found[0].get('name')})")
        elif not found:
            print(f"- {t['platform']:<10} aucun canal connecté dans Postiz")
        else:
            print(f"? {t['platform']:<10} {len(found)} canaux possibles : préciser « account » ou « integrationId »")
    if changed and args.write:
        path.write_text(json.dumps(pub, ensure_ascii=False, indent=2) + "\n")
        print("publish.json mis à jour")
    elif changed:
        print("(aperçu — relancer avec --write)")


def now_iso():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def cmd_send(args):
    short, path, pub = load(args.short)
    log_path = short / "publish-log.json"
    log = json.loads(log_path.read_text()) if log_path.is_file() else {"uploads": {}, "sends": []}
    done = {p for s in log["sends"] if s.get("ok") for p in s.get("platforms", [])}
    if pub.get("status") not in ("approved", "partial") and not args.dry_run:
        sys.exit(f"publish.json est en statut « {pub.get('status')} » : seul « approved » est envoyé.")
    when = pub.get("when") or {"type": "draft"}
    kind = args.type or when.get("type", "draft")
    only = set(args.only.split(",")) if args.only else None

    def media(rel):
        file = short / rel
        digest = hashlib.sha1(file.read_bytes()).hexdigest()
        cached = log["uploads"].get(rel)
        if cached and cached.get("sha1") == digest:
            return {"id": cached["id"], "path": cached["path"]}
        if args.dry_run:
            return {"id": f"<upload {rel}>", "path": f"<upload {rel}>"}
        res = upload(file)
        log["uploads"][rel] = {"id": res["id"], "path": res["path"], "sha1": digest}
        log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n")
        print(f"  envoyé {rel}")
        return {"id": res["id"], "path": res["path"]}

    def resolve(value):
        if isinstance(value, str) and value.startswith("@upload:"):
            return media(value[8:])
        if isinstance(value, dict):
            return {k: resolve(v) for k, v in value.items()}
        if isinstance(value, list):
            return [resolve(v) for v in value]
        return value

    groups, skipped = {}, []
    for t in pub.get("targets", []):
        p = t["platform"]
        reason = ("hors --only" if only and p not in only else "skip" if t.get("skip")
                  else "non lié à Postiz (publish.py bind)" if not t.get("integrationId")
                  else "déjà envoyé (--force pour renvoyer)" if p in done and not args.force else None)
        if reason:
            skipped.append((p, reason))
            continue
        date = now_iso() if kind == "now" else (args.date or t.get("date") or when.get("date") or now_iso())
        groups.setdefault(date, []).append(t)
    for p, reason in skipped:
        print(f"  saute {p:<10} {reason}")
    if not groups:
        sys.exit("Rien à envoyer.")

    for date, targets in groups.items():
        posts = []
        for t in targets:
            settings = {**SETTINGS.get(t["platform"], {"__type": t["platform"]}), **(t.get("settings") or {})}
            if t["platform"] == "youtube" and not settings.get("title"):
                settings["title"] = t.get("title", "")
            posts.append({"integration": {"id": t["integrationId"]},
                          "value": [{"content": full_text(t), "image": [media(t["video"])]}],
                          "settings": resolve(settings)})
        payload = {"type": kind, "date": date, "shortLink": False, "tags": [], "posts": posts}
        names = [t["platform"] for t in targets]
        if args.dry_run:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            print(f"(simulation — {kind} {date} — {', '.join(names)})")
            continue
        result = request("POST", "/posts", body=payload)
        log["sends"].append({"at": now_iso(), "type": kind, "date": date, "platforms": names, "ok": True, "response": result})
        log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n")
        print(f"OK — {kind} {date} — {', '.join(names)}")
    if args.dry_run:
        return
    sent = {p for s in log["sends"] if s.get("ok") for p in s.get("platforms", [])}
    remaining = [t["platform"] for t in pub["targets"] if not t.get("skip") and t["platform"] not in sent]
    pub["status"] = "partial" if remaining else {"now": "published", "schedule": "scheduled", "draft": "drafted"}[kind]
    path.write_text(json.dumps(pub, ensure_ascii=False, indent=2) + "\n")
    if remaining:
        print(f"restent : {', '.join(remaining)}")


def cmd_status(args):
    today = dt.datetime.now(dt.timezone.utc)
    start = args.start or (today - dt.timedelta(days=7)).strftime("%Y-%m-%dT00:00:00.000Z")
    end = args.end or (today + dt.timedelta(days=30)).strftime("%Y-%m-%dT23:59:59.000Z")
    res = request("GET", "/posts", params={"startDate": start, "endDate": end})
    for p in (res.get("posts", res) if isinstance(res, dict) else res):
        integ = p.get("integration") or {}
        print(f"{str(p.get('publishDate', '?'))[:16]}  {integ.get('providerIdentifier', integ.get('identifier', '?')):<14} "
              f"{p.get('state', p.get('status', '?')):<10} {p.get('releaseURL') or ''}  {p.get('id')}")


def main():
    load_env()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("validate"); p.add_argument("short"); p.set_defaults(fn=cmd_validate)
    p = sub.add_parser("kit"); p.add_argument("short"); p.add_argument("--out"); p.set_defaults(fn=cmd_kit)
    sub.add_parser("check").set_defaults(fn=cmd_check)
    p = sub.add_parser("integrations"); p.add_argument("--json", action="store_true"); p.set_defaults(fn=cmd_integrations)
    p = sub.add_parser("settings"); p.add_argument("id"); p.set_defaults(fn=cmd_settings)
    p = sub.add_parser("bind"); p.add_argument("short"); p.add_argument("--write", action="store_true"); p.set_defaults(fn=cmd_bind)
    p = sub.add_parser("send")
    p.add_argument("short"); p.add_argument("--only"); p.add_argument("--type", choices=["now", "schedule", "draft"])
    p.add_argument("--date"); p.add_argument("--dry-run", action="store_true"); p.add_argument("--force", action="store_true")
    p.set_defaults(fn=cmd_send)
    p = sub.add_parser("status"); p.add_argument("--from", dest="start"); p.add_argument("--to", dest="end"); p.set_defaults(fn=cmd_status)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
