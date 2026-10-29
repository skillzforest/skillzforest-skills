#!/usr/bin/env python3
"""Valide une charte relevée sur un site et en dérive les deux palettes des masters.

Entrée  : brand-profile.json (couleurs relevées, voir examples/brand-profile.example.json)
Sortie  : le même fichier enrichi de `palettes.slides`, `palettes.document` et `contraste`

Aucune couleur n'est inventée : les palettes ne contiennent que des couleurs du site,
éventuellement assombries ou éclaircies pour tenir le contraste WCAG, et chaque
ajustement est consigné. Les couleurs indispensables absentes arrêtent le script.

Usage : python3 brand_check.py brand-profile.json [--out brand-profile.json]
"""
import argparse
import colorsys
import json
import re
import sys

HEX = re.compile(r"^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
REQUIRED = ("fond_sombre", "fond_clair", "texte", "primaire")


def norm(value):
    if not value:
        return None
    m = HEX.match(str(value).strip())
    if not m:
        return None
    h = m.group(1)
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return "#" + h.upper()


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def to_hex(r, g, b):
    return "#" + "".join("%02X" % round(max(0, min(1, c)) * 255) for c in (r, g, b))


def luminance(h):
    def chan(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (chan(c) for c in rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return round((la + 0.05) / (lb + 0.05), 2)


def mix(a, b, t):
    ra, rb = rgb(a), rgb(b)
    return to_hex(*(x + (y - x) * t for x, y in zip(ra, rb)))


def reach(color, background, target):
    """Assombrit ou éclaircit `color` (teinte conservée) jusqu'au ratio `target` sur `background`."""
    if ratio(color, background) >= target:
        return color, False
    h, l, s = colorsys.rgb_to_hls(*rgb(color))
    darker = luminance(background) > 0.5
    for _ in range(100):
        l = l - 0.01 if darker else l + 0.01
        if l <= 0 or l >= 1:
            break
        candidate = to_hex(*colorsys.hls_to_rgb(h, l, s))
        if ratio(candidate, background) >= target:
            return candidate, True
    return None, True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("profile")
    ap.add_argument("--out")
    args = ap.parse_args()

    with open(args.profile, encoding="utf-8") as f:
        profile = json.load(f)

    colors = {k: norm(v) for k, v in (profile.get("couleurs") or {}).items()}
    missing = [k for k in REQUIRED if not colors.get(k)]
    if missing:
        print("Couleurs indispensables absentes ou invalides : " + ", ".join(missing), file=sys.stderr)
        print("Relever ces couleurs sur le site, ou les demander, avant de construire les masters.", file=sys.stderr)
        sys.exit(2)

    notes = []
    checks = []

    def check(label, fg, bg, target):
        r = ratio(fg, bg)
        checks.append({"paire": label, "texte": fg, "fond": bg, "ratio": r, "cible": target, "ok": r >= target})
        return r

    # Slides : on suit le fond dominant du site.
    theme = (profile.get("theme_site") or "").lower()
    if theme not in ("sombre", "clair"):
        theme = "sombre" if luminance(colors.get("fond_site") or colors["fond_sombre"]) < 0.4 else "clair"
    s_bg = colors["fond_sombre"] if theme == "sombre" else colors["fond_clair"]
    s_text = colors["texte"] if ratio(colors["texte"], s_bg) >= 4.5 else (
        colors["fond_clair"] if theme == "sombre" else colors["fond_sombre"])
    if s_text != colors["texte"]:
        notes.append("Slides : texte %s trop peu contrasté sur %s, remplacé par %s (couleur du site)." % (colors["texte"], s_bg, s_text))

    def on_bg(key, bg, target, label):
        c = colors.get(key)
        if not c:
            return None
        adj, changed = reach(c, bg, target)
        if adj is None:
            notes.append("%s : %s n'atteint jamais %s:1 sur %s, non utilisée pour du texte." % (label, c, target, bg))
            return None
        if changed:
            notes.append("%s : %s ajustée en %s pour atteindre %s:1 sur %s." % (label, c, adj, target, bg))
        return adj

    slides = {
        "fond": s_bg,
        "surface": mix(s_bg, s_text, 0.08),
        "bordure": colors.get("bordure") or mix(s_bg, s_text, 0.22),
        "texte": s_text,
        "texte_secondaire": on_bg("texte_secondaire", s_bg, 4.5, "Slides, texte secondaire") or mix(s_text, s_bg, 0.3),
        "primaire": on_bg("primaire", s_bg, 3.0, "Slides, primaire") or s_text,
        "secondaire": on_bg("secondaire", s_bg, 3.0, "Slides, secondaire"),
        "accent": on_bg("accent", s_bg, 3.0, "Slides, accent"),
    }
    slides["secondaire"] = slides["secondaire"] or slides["primaire"]
    slides["accent"] = slides["accent"] or slides["primaire"]
    if ratio(slides["texte_secondaire"], s_bg) < 4.5:
        slides["texte_secondaire"] = s_text

    # Document : toujours fond blanc, palette « fond clair ».
    d_bg = "#FFFFFF"
    dark_candidates = [colors.get("texte_fonce"), colors["fond_sombre"], colors["texte"]]
    d_text = next((c for c in dark_candidates if c and ratio(c, d_bg) >= 7), None)
    if not d_text:
        d_text, _ = reach(colors["fond_sombre"], d_bg, 7)
        notes.append("Document : texte courant dérivé de %s (%s)." % (colors["fond_sombre"], d_text))
    document = {
        "fond": d_bg,
        "texte": d_text,
        "texte_secondaire": mix(d_text, d_bg, 0.25),
        "titres": on_bg("primaire", d_bg, 4.5, "Document, titres") or d_text,
        "filet": on_bg("primaire", d_bg, 3.0, "Document, filets") or d_text,
        "lien": on_bg("secondaire", d_bg, 4.5, "Document, liens") or on_bg("primaire", d_bg, 4.5, "Document, liens") or d_text,
        "encadre_fond": mix(colors["primaire"], d_bg, 0.9),
    }
    if ratio(document["texte_secondaire"], d_bg) < 4.5:
        document["texte_secondaire"] = d_text

    check("Slides : texte / fond", slides["texte"], slides["fond"], 4.5)
    check("Slides : texte secondaire / fond", slides["texte_secondaire"], slides["fond"], 4.5)
    check("Slides : texte / surface", slides["texte"], slides["surface"], 4.5)
    check("Slides : primaire (titres, chiffres) / fond", slides["primaire"], slides["fond"], 3.0)
    check("Slides : accent / fond", slides["accent"], slides["fond"], 3.0)
    check("Document : texte / blanc", document["texte"], d_bg, 4.5)
    check("Document : texte secondaire / blanc", document["texte_secondaire"], d_bg, 4.5)
    check("Document : titres / blanc", document["titres"], d_bg, 4.5)
    check("Document : lien / blanc", document["lien"], d_bg, 4.5)
    check("Document : texte / encadré", document["texte"], document["encadre_fond"], 4.5)

    profile["palettes"] = {"theme_slides": theme, "slides": slides, "document": document}
    profile["contraste"] = checks
    profile.setdefault("a_verifier", [])
    for n in notes:
        if n not in profile["a_verifier"]:
            profile["a_verifier"].append(n)

    out = args.out or args.profile
    with open(out, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)

    print("Thème des slides : " + theme)
    for c in checks:
        print("%-45s %s sur %s  %5.2f:1 (cible %s)  %s" % (c["paire"], c["texte"], c["fond"], c["ratio"], c["cible"], "OK" if c["ok"] else "ÉCHEC"))
    for n in notes:
        print("Note : " + n)
    if not all(c["ok"] for c in checks):
        sys.exit(1)


if __name__ == "__main__":
    main()
