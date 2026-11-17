#!/usr/bin/env python3
"""Check a short's source kit before production (stdlib only).

    validate_kit.py shorts/<slug>[/kit.json] [--strict]

Errors (must be fixed): missing idea, product or platforms, unknown platform, brand
colors missing or not #RRGGBB, unreadable text (contrast below 4.5:1 for text on bg
and accentText on accent, WCAG AA), a file listed but absent, no visual at all, a fact
without source. Warnings: muted text below 3:1, music or video of unknown licence,
no logo, no font file (system fonts will be used), fewer than 3 facts, a video
without duration. Prints {"ok": bool, "errors": [], "warnings": []}; exit code 1 when
not ok (or when --strict and there are warnings).
"""
import json
import re
import sys
from pathlib import Path

PLATFORMS = {"youtube", "tiktok", "instagram", "x", "bluesky", "linkedin", "threads", "facebook"}
COLORS = ("bg", "bg2", "text", "muted", "accent", "accentText")
HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")


def luminance(hex_color):
    def channel(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    path = Path(sys.argv[1])
    if path.is_dir():
        path = path / "kit.json"
    strict = "--strict" in sys.argv
    short = path.parent
    kit = json.loads(path.read_text())
    errors, warnings = [], []

    idea, product, brand = kit.get("idea") or {}, kit.get("product") or {}, kit.get("brand") or {}
    if not idea.get("subject"):
        errors.append("idea.subject manquant : l'idée à illustrer en une phrase")
    if not (idea.get("cta") or {}).get("text"):
        warnings.append("idea.cta.text manquant : quelle action demander à la fin de la vidéo ?")
    if not product.get("name"):
        errors.append("product.name manquant")
    platforms = kit.get("platforms") or []
    if not platforms:
        errors.append("platforms vide : choisir au moins un réseau")
    for p in platforms:
        if p not in PLATFORMS:
            errors.append(f"plateforme inconnue « {p} » (connues : {', '.join(sorted(PLATFORMS))})")

    colors = brand.get("colors") or {}
    for name in COLORS:
        value = colors.get(name)
        if not value:
            errors.append(f"brand.colors.{name} manquant")
        elif not HEX.match(value):
            errors.append(f"brand.colors.{name} = « {value} » : attendu #RRGGBB")
    if all(HEX.match(colors.get(n, "")) for n in COLORS):
        for fg, bg, need, level in (("text", "bg", 4.5, errors), ("text", "bg2", 4.5, errors),
                                    ("accentText", "accent", 4.5, errors), ("muted", "bg", 3.0, warnings)):
            ratio = contrast(colors[fg], colors[bg])
            if ratio < need:
                level.append(f"contraste {fg}/{bg} = {ratio:.1f}:1 < {need}:1 — illisible sur mobile")
    fonts = brand.get("fonts") or {}
    if not fonts.get("display") or not fonts.get("body"):
        errors.append("brand.fonts.display et brand.fonts.body requis (familles CSS, avec repli : « Inter, sans-serif »)")
    if not brand.get("fontFiles"):
        warnings.append("aucun fichier de police : la vidéo utilisera les polices système (fetch_font.py)")
    if not brand.get("logo"):
        warnings.append("pas de logo : le nom de la marque sera écrit à la place")
    else:
        logo = next((a for a in kit.get("assets") or [] if a.get("file") == brand["logo"]), None)
        if logo and logo.get("width") and not brand["logo"].endswith(".svg") and logo["width"] < 400:
            warnings.append(f"logo de {logo['width']} px de large : flou en vidéo — chercher un SVG ou une version ≥ 600 px")

    files = [("brand.logo", brand.get("logo"))] + [(f"brand.fontFiles[{i}]", f.get("file")) for i, f in enumerate(brand.get("fontFiles") or [])]
    files += [(f"assets[{a.get('id')}]", a.get("file")) for a in kit.get("assets") or []]
    for label, rel in files:
        if rel and not re.match(r"https?://", rel) and not (short / rel).is_file():
            errors.append(f"{label} : fichier absent {rel}")
    for label, rel in files[:1 + len(brand.get("fontFiles") or [])]:
        if rel and not re.match(r"https?://", rel) and not rel.startswith("assets/"):
            errors.append(f"{label} : le fichier doit être sous assets/ ({rel})")

    assets = kit.get("assets") or []
    visuals = [a for a in assets if a.get("kind") in ("image", "video")]
    if not visuals and not brand.get("logo"):
        errors.append("aucun visuel (capture, image, vidéo, logo) : la vidéo n'aurait que du texte")
    for a in assets:
        if a.get("kind") in ("audio", "video", "image") and a.get("licence", "unknown") == "unknown" and a.get("origin") != "site":
            warnings.append(f"{a.get('id')} {a.get('file')} : licence inconnue — à confirmer avant publication")
        if a.get("kind") == "video" and not a.get("duration"):
            warnings.append(f"{a.get('id')} {a.get('file')} : durée inconnue")

    facts = kit.get("facts") or []
    for f in facts:
        if not f.get("source"):
            errors.append(f"fait sans source : « {f.get('text', '')[:60]} »")
    if len(facts) < 3:
        warnings.append(f"{len(facts)} fait(s) seulement : 3 à 8 faits sourcés donnent un script plus fort")

    ok = not errors and not (strict and warnings)
    print(json.dumps({"ok": ok, "errors": errors, "warnings": warnings}, ensure_ascii=False, indent=2))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
