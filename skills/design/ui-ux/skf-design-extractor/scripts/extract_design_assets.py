#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
skf-design-extractor : extraction des assets graphiques d'une maquette statique.

Sous-commandes :
  info      Dimensions réelles et métadonnées de la maquette (après rotation EXIF).
  grid      Superpose une grille de coordonnées pour repérer les assets.
  zoom      Agrandit une zone avec une grille fine pour affiner les bords d'un asset.
  snap      Propose un cadrage serré d'un élément posé sur un fond uni.
  preview   Dessine les cadres du manifest sur la maquette (contrôle visuel).
  extract   Découpe et exporte les assets en WebP (ou valide seulement avec --dry-run).
  spec      Lit un cahier de tailles (md, xlsx, csv) et produit assets-spec.json.
  link      Relie plusieurs maquettes au cahier : couverture, doublons, rapport.

Avec un cahier, chaque asset porte un spec_id (numéro de ligne du cahier) :
l'export respecte le ratio, la taille à produire et le poids visé de la ligne,
et produit aussi les variantes déclarées (ex. version mobile). Aucun
agrandissement n'est fait par défaut : une maquette trop petite est signalée.

Les images de contrôle (grid, zoom, preview) sont écrites dans un dossier
temporaire, jamais dans le dossier de destination des assets.

Codes de sortie : 0 = OK, 1 = au moins un asset en erreur, 2 = erreur bloquante.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import tempfile
import unicodedata
from collections import Counter
from pathlib import Path

try:
    from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps, features
except ImportError:  # pragma: no cover
    sys.stderr.write(
        "Erreur : Pillow n'est pas installé. Installer avec : python3 -m pip install Pillow\n"
    )
    sys.exit(2)

sys.path.insert(0, str(Path(__file__).resolve().parent))
import asset_spec  # noqa: E402

Image.MAX_IMAGE_PIXELS = 300_000_000

ASSET_TYPES = (
    "photo",
    "illustration",
    "logo",
    "background",
    "texture",
    "decorative",
    "screenshot",
    "avatar",
    "icon",
)
LOSSLESS_TYPES = {"logo", "icon"}
DEFAULT_MIN_CONFIDENCE = 0.80
DEFAULT_QUALITY = 90
DEFAULT_SPEC_QUALITY = (75, 80)
DEFAULT_QUALITY_FLOOR = 60
RATIO_TOLERANCE = 0.02
DUPLICATE_HASH_DISTANCE = 10
DEFAULT_ROOT = Path("public/assets")
KEBAB_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
GENERIC_RE = re.compile(
    r"^(image|img|asset|picture|pic|photo|visual|visuel|element|item|crop|untitled)(-?\d+)?$"
)
CONTROL_DIR = Path(tempfile.gettempdir()) / "skf-design-extractor"

STATUS_LABELS = {
    "extract": "à extraire",
    "extracted": "extrait",
    "skip_low_confidence": "ignoré (confiance)",
    "skip_reconstruction": "ignoré (reconstruction)",
    "skip_duplicate": "doublon (non extrait)",
    "error": "ERREUR",
}
STATUS_COLORS = {
    "extract": (0, 200, 90, 255),
    "extracted": (0, 200, 90, 255),
    "skip_low_confidence": (255, 150, 0, 255),
    "skip_reconstruction": (230, 40, 40, 255),
    "skip_duplicate": (60, 130, 230, 255),
    "error": (200, 0, 200, 255),
}


class ManifestError(Exception):
    """Erreur de contenu du manifest assets.json."""


# --------------------------------------------------------------------------- #
# Utilitaires
# --------------------------------------------------------------------------- #
def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()
    return text or "maquette"


def load_source(path: Path):
    """Ouvre la maquette, applique l'orientation EXIF, renvoie (image, format)."""
    if not path.is_file():
        raise FileNotFoundError(f"Maquette introuvable : {path}")
    try:
        raw = Image.open(path)
        fmt = raw.format
        img = ImageOps.exif_transpose(raw)
        if img is None:  # anciennes versions de Pillow
            img = raw
        img.load()
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Impossible d'ouvrir {path} : {exc}") from exc
    return img, fmt


def pixels(img: Image.Image) -> list:
    """Liste des pixels, compatible Pillow < 12 et >= 12."""
    getter = getattr(img, "get_flattened_data", None) or img.getdata
    return list(getter())


def has_alpha(img: Image.Image) -> bool:
    return img.mode in ("RGBA", "LA", "PA", "RGBa", "La") or "transparency" in img.info


def to_output_mode(img: Image.Image) -> Image.Image:
    """RGBA si la source porte de la transparence, RGB sinon."""
    if has_alpha(img):
        return img if img.mode == "RGBA" else img.convert("RGBA")
    return img if img.mode == "RGB" else img.convert("RGB")


def control_path(source: Path, suffix: str, explicit: str | None) -> Path:
    path = Path(explicit) if explicit else CONTROL_DIR / f"{slugify(source.stem)}-{suffix}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def get_font(size: int):
    for name in ("DejaVuSans.ttf", "Arial.ttf", "arial.ttf", "Helvetica.ttc", "LiberationSans-Regular.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def put_label(draw, x, y, text, font, canvas_size, fill=(255, 255, 255, 255), bg=(0, 0, 0, 200)):
    width, height = canvas_size
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    x = max(3 - left, min(x, width - right - 3))
    y = max(3 - top, min(y, height - bottom - 3))
    draw.rectangle((x + left - 3, y + top - 3, x + right + 3, y + bottom + 3), fill=bg)
    draw.text((x, y), text, font=font, fill=fill)


def auto_step(length: int, target: int) -> int:
    for step in (5, 10, 20, 25, 50, 100, 200, 250, 500, 1000):
        if length / step <= target:
            return step
    return 1000


def as_number(value, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ManifestError(f"'{field}' doit être un nombre (reçu : {value!r})")
    return float(value)


def error_exit(message: str) -> int:
    sys.stderr.write(f"Erreur : {message}\n")
    return 2


# --------------------------------------------------------------------------- #
# Planification : validation du manifest et calcul des cadres
# --------------------------------------------------------------------------- #
def fit_ratio(box, ratio, focus=(0.5, 0.5)):
    """Plus grand cadre au ratio demandé contenu dans box, centré sur focus.

    Ne sort jamais du cadre visible : aucun pixel n'est inventé.
    Renvoie (cadre, part de surface perdue).
    """
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    current = w / h
    if abs(current / ratio - 1) <= RATIO_TOLERANCE:
        return box, 0.0
    fx, fy = focus
    if current > ratio:  # trop large : on rogne gauche/droite
        new_w = max(1, round(h * ratio))
        left = x0 + round((w - new_w) * fx)
        inner = (left, y0, left + new_w, y1)
    else:  # trop haut : on rogne haut/bas
        new_h = max(1, round(w / ratio))
        top = y0 + round((h - new_h) * fy)
        inner = (x0, top, x1, top + new_h)
    lost = 1 - ((inner[2] - inner[0]) * (inner[3] - inner[1])) / (w * h)
    return inner, lost


def plan_spec_outputs(plan, raw, spec, name, primary_output, allow_upscale):
    """Calcule les fichiers à produire pour un asset rattaché à une ligne du cahier."""
    items = asset_spec.index_spec(spec)
    spec_id = raw.get("spec_id")
    if isinstance(spec_id, str) and spec_id.strip().isdigit():
        spec_id = int(spec_id)
    if spec_id not in items:
        raise ManifestError(f"spec_id {spec_id!r} absent du cahier")
    item = items[spec_id]
    if item["kind"] == "video":
        raise ManifestError(f"la ligne {spec_id} est une vidéo : non extractible depuis une maquette")
    if item.get("same_as"):
        canonical = item["same_as"][0]
        plan["messages"].append(f"ligne {spec_id} : même image que la ligne {canonical}, rattachement à la ligne {canonical}")
        spec_id = canonical
        if spec_id not in items:
            raise ManifestError(f"ligne de référence {spec_id} absente du cahier")
        item = items[spec_id]
    if item.get("variant_of"):
        plan["messages"].append(f"ligne {spec_id} : variante de la ligne {item['variant_of']}, rattachement au parent")
        spec_id = item["variant_of"]
        item = items[spec_id]
    plan["spec_id"] = spec_id
    plan["spec_label"] = item["emplacement"]

    wanted = raw.get("spec_variants")
    variants = asset_spec.variants_of(spec, spec_id)
    if isinstance(wanted, list):
        variants = [v for v in variants if v["id"] in wanted]
    if not variants:
        raise ManifestError(f"la ligne {spec_id} n'a pas de taille à produire exploitable")

    focus = raw.get("focus", [0.5, 0.5])
    if (
        not isinstance(focus, (list, tuple))
        or len(focus) != 2
        or not all(isinstance(v, (int, float)) and 0 <= v <= 1 for v in focus)
    ):
        raise ManifestError("'focus' doit être [x, y] avec des valeurs entre 0 et 1")

    rules = spec.get("rules", {})
    q_min = rules.get("quality_min", DEFAULT_SPEC_QUALITY[0])
    q_max = rules.get("quality_max", DEFAULT_SPEC_QUALITY[1])
    if "quality" in raw:
        q_max = int(as_number(raw["quality"], "quality"))
        q_min = min(q_min, q_max)
    global_max = rules.get("max_image_kb")

    outputs = []
    for variant in variants:
        tw, th = variant["target"]["width"], variant["target"]["height"]
        ratio = tw / th
        crop, lost = fit_ratio(plan["box"], ratio, tuple(focus))
        cw, ch = crop[2] - crop[0], crop[3] - crop[1]
        flags = []
        if lost > RATIO_TOLERANCE:
            shown = variant.get("display_ratio") or item.get("display_ratio")
            frame_ratio = (plan["box"][2] - plan["box"][0]) / (plan["box"][3] - plan["box"][1])
            shown_value = None
            if shown and ":" in shown:
                a, b = shown.split(":")
                shown_value = float(a) / float(b)
            if shown_value and abs(shown_value / frame_ratio - 1) <= 0.05 and abs(shown_value / ratio - 1) > RATIO_TOLERANCE:
                flags.append(
                    f"la maquette n'affiche qu'un cadrage {shown} de ce visuel {tw}:{th} : recadré en {cw}x{ch} "
                    f"({lost:.0%} du visible perdu), l'image complète doit venir de la source"
                )
            else:
                flags.append(
                    f"recadrage {cw}x{ch} au ratio {tw}:{th} : {lost:.0%} du visuel visible perdu"
                )
        if cw >= tw * 0.99:
            export = (tw, th)
        elif allow_upscale:
            export = (tw, th)
            flags.append(f"agrandi x{tw / cw:.2f} depuis {cw}x{ch} (--allow-upscale) : qualité de placeholder")
        else:
            export = (cw, ch)
            flags.append(
                f"résolution insuffisante : {cw}x{ch} disponibles pour {tw}x{th} demandés (x{tw / cw:.2f} manquant)"
            )
        budgets = [b for b in (variant.get("max_kb"), global_max) if b]
        file = primary_output if variant["id"] == spec_id else f"{name}-{tw}x{th}.webp"
        outputs.append(
            {
                "file": file,
                "spec_id": variant["id"],
                "target": [tw, th],
                "crop": list(crop),
                "export": list(export),
                "max_kb": min(budgets) if budgets else None,
                "quality_range": [q_min, q_max],
                "lossless": False,
                "flags": flags,
            }
        )
    return outputs


def plan_assets(manifest, image_size, min_conf=None, cli_padding=None, rescale=False, spec=None,
                allow_upscale=False):
    """Valide le manifest et renvoie (plans, avertissements, seuil de confiance)."""
    if not isinstance(manifest, dict):
        raise ManifestError("la racine du manifest doit être un objet JSON")
    assets = manifest.get("assets")
    if not isinstance(assets, list):
        raise ManifestError("'assets' doit être une liste")

    img_w, img_h = image_size
    warnings: list[str] = []
    scale_x = scale_y = 1.0
    declared_w, declared_h = manifest.get("width"), manifest.get("height")
    if declared_w is None or declared_h is None:
        warnings.append("width/height absents du manifest : dimensions réelles utilisées")
    else:
        declared_w = as_number(declared_w, "width")
        declared_h = as_number(declared_h, "height")
        if (round(declared_w), round(declared_h)) != (img_w, img_h):
            if not rescale:
                raise ManifestError(
                    f"le manifest déclare {declared_w:g}x{declared_h:g} mais la maquette fait "
                    f"{img_w}x{img_h}. Corriger les coordonnées ou relancer avec --rescale."
                )
            scale_x, scale_y = img_w / declared_w, img_h / declared_h
            warnings.append(
                f"coordonnées remises à l'échelle {declared_w:g}x{declared_h:g} -> {img_w}x{img_h}"
            )

    defaults = manifest.get("defaults") or {}
    if not isinstance(defaults, dict):
        raise ManifestError("'defaults' doit être un objet")
    if min_conf is None:
        min_conf = defaults.get("min_confidence", DEFAULT_MIN_CONFIDENCE)
    min_conf = as_number(min_conf, "min_confidence")
    if not 0 <= min_conf <= 1:
        raise ManifestError("min_confidence doit être compris entre 0 et 1")
    default_padding = cli_padding if cli_padding is not None else defaults.get("padding", 0)

    plans = []
    seen_names: set[str] = set()
    seen_outputs: set[str] = set()

    for index, raw in enumerate(assets):
        plan = {"index": index, "name": f"assets[{index}]", "status": None, "messages": []}
        plans.append(plan)
        try:
            if not isinstance(raw, dict):
                raise ManifestError("chaque asset doit être un objet")
            name = raw.get("name")
            if not isinstance(name, str) or not name:
                raise ManifestError("'name' manquant")
            plan["name"] = name
            if not KEBAB_RE.match(name):
                raise ManifestError(f"nom '{name}' invalide : lowercase kebab-case attendu")
            if GENERIC_RE.match(name):
                plan["messages"].append("nom générique : préférer un nom métier")
            if name in seen_names:
                raise ManifestError(f"nom '{name}' en double")
            seen_names.add(name)

            asset_type = raw.get("type")
            if asset_type not in ASSET_TYPES:
                plan["messages"].append(
                    f"type '{asset_type}' non standard (attendu : {', '.join(ASSET_TYPES)})"
                )

            x = round(as_number(raw.get("x"), "x") * scale_x)
            y = round(as_number(raw.get("y"), "y") * scale_y)
            w = round(as_number(raw.get("width"), "width") * scale_x)
            h = round(as_number(raw.get("height"), "height") * scale_y)
            if w <= 0 or h <= 0:
                raise ManifestError("width et height doivent être > 0")

            output = raw.get("output") or f"{name}.webp"
            if (
                not isinstance(output, str)
                or not output.lower().endswith(".webp")
                or "/" in output
                or "\\" in output
                or output.startswith(".")
            ):
                raise ManifestError(f"'output' invalide ({output!r}) : nom de fichier .webp simple attendu")

            confidence = as_number(raw.get("confidence"), "confidence")
            if not 0 <= confidence <= 1:
                raise ManifestError("'confidence' doit être compris entre 0 et 1")

            requires_reconstruction = raw.get("requires_reconstruction", False)
            if not isinstance(requires_reconstruction, bool):
                raise ManifestError("'requires_reconstruction' doit être true ou false")

            padding = raw.get("padding", default_padding)
            padding = int(as_number(padding, "padding"))
            if padding < 0:
                raise ManifestError("'padding' doit être >= 0")

            quality = raw.get("quality", DEFAULT_QUALITY)
            quality = int(as_number(quality, "quality"))
            if not 1 <= quality <= 100:
                raise ManifestError("'quality' doit être compris entre 1 et 100")
            lossless = raw.get("lossless", asset_type in LOSSLESS_TYPES)
            if not isinstance(lossless, bool):
                raise ManifestError("'lossless' doit être true ou false")

            plan.update(
                type=asset_type,
                x=x,
                y=y,
                width=w,
                height=h,
                output=output,
                confidence=confidence,
                requires_reconstruction=requires_reconstruction,
                padding=padding,
                quality=quality,
                lossless=lossless,
                reason=raw.get("reason"),
                reconstruction_reason=raw.get("reconstruction_reason"),
            )

            if x < 0 or y < 0 or x + w > img_w or y + h > img_h:
                raise ManifestError(
                    f"cadre hors limites : ({x},{y}) {w}x{h} dépasse l'image {img_w}x{img_h}"
                )

            box = (max(0, x - padding), max(0, y - padding), min(img_w, x + w + padding), min(img_h, y + h + padding))
            plan["box"] = box
            if padding and box != (x - padding, y - padding, x + w + padding, y + h + padding):
                plan["messages"].append("padding réduit au bord de l'image")

            if raw.get("spec_id") is not None:
                if spec is None:
                    raise ManifestError("spec_id renseigné mais aucun cahier : passer --spec ou renseigner 'spec'")
                outputs = plan_spec_outputs(plan, raw, spec, name, output, allow_upscale)
            else:
                if spec is not None:
                    plan["messages"].append("hors cahier : export brut sans contrainte de taille")
                outputs = [
                    {
                        "file": output,
                        "spec_id": None,
                        "target": None,
                        "crop": list(box),
                        "export": [box[2] - box[0], box[3] - box[1]],
                        "max_kb": None,
                        "quality_range": [quality, quality],
                        "lossless": lossless,
                        "flags": [],
                    }
                ]
            for out in outputs:
                if out["file"] in seen_outputs:
                    raise ManifestError(f"fichier de sortie '{out['file']}' en double")
                seen_outputs.add(out["file"])
            plan["outputs"] = outputs

            duplicate_of = raw.get("duplicate_of")
            if requires_reconstruction:
                plan["status"] = "skip_reconstruction"
                reason = raw.get("reconstruction_reason")
                if reason:
                    plan["messages"].append(f"reconstruction : {reason}")
            elif duplicate_of:
                plan["status"] = "skip_duplicate"
                plan["duplicate_of"] = duplicate_of
                plan["messages"].append(f"même image que {duplicate_of} (source retenue ailleurs)")
            elif confidence < min_conf:
                plan["status"] = "skip_low_confidence"
                plan["messages"].append(f"confiance {confidence:.2f} < seuil {min_conf:.2f}")
            else:
                plan["status"] = "extract"
        except ManifestError as exc:
            plan["status"] = "error"
            plan["messages"].append(str(exc))

    return plans, warnings, min_conf


def load_manifest(path: Path):
    if not path.is_file():
        raise FileNotFoundError(f"Manifest introuvable : {path}")
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        raise ManifestError(f"JSON invalide dans {path} : {exc}") from exc


def resolve_source(manifest: dict, manifest_path: Path, explicit: str | None) -> Path:
    if explicit:
        return Path(explicit)
    candidates = []
    for key in ("source_path", "source"):
        value = manifest.get(key)
        if isinstance(value, str) and value:
            candidates += [Path(value), manifest_path.parent / value]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        "maquette source introuvable : passer --source ou renseigner 'source_path' dans le manifest"
    )


def resolve_spec(manifest: dict, manifest_path: Path, explicit: str | None):
    """Cahier de l'option --spec, sinon champ 'spec' du manifest (relatif au manifest)."""
    value = explicit or manifest.get("spec")
    if not value:
        return None
    candidates = [Path(value)] if explicit else [manifest_path.parent / value, Path(value)]
    for candidate in candidates:
        if candidate.is_file():
            return asset_spec.load_spec(candidate)
    raise FileNotFoundError(f"cahier introuvable : {value}")


def load_context(args, manifest_path: Path | None = None):
    """Charge manifest, maquette, cahier et calcule le plan."""
    if manifest_path is None:
        manifest_path, _ = resolve_paths(args)
    manifest = load_manifest(manifest_path)
    source = resolve_source(manifest, manifest_path, getattr(args, "source", None))
    img, _ = load_source(source)
    spec = resolve_spec(manifest, manifest_path, getattr(args, "spec", None))
    defaults = manifest.get("defaults") or {}
    allow_upscale = getattr(args, "allow_upscale", False) or bool(defaults.get("allow_upscale"))
    plans, warnings, min_conf = plan_assets(
        manifest, img.size, getattr(args, "min_confidence", None), getattr(args, "padding", None),
        getattr(args, "rescale", False), spec, allow_upscale,
    )
    return manifest, source, img, spec, plans, warnings, min_conf


def resolve_paths(args):
    out_dir = Path(args.output) if getattr(args, "output", None) else None
    if args.manifest:
        manifest_path = Path(args.manifest)
    elif out_dir:
        manifest_path = out_dir / "assets.json"
    else:
        raise ManifestError("préciser --manifest ou --output")
    if out_dir is None:
        out_dir = manifest_path.parent
    return manifest_path, out_dir


# --------------------------------------------------------------------------- #
# Rapport
# --------------------------------------------------------------------------- #
def print_report(plans, warnings, min_conf, out_dir, dry_run, as_json, spec=None):
    counts = Counter(p["status"] for p in plans)
    if as_json:
        payload = {
            "dry_run": dry_run,
            "output_dir": str(out_dir),
            "min_confidence": min_conf,
            "spec": spec.get("spec_source") if spec else None,
            "warnings": warnings,
            "counts": dict(counts),
            "assets": [{k: v for k, v in p.items() if k != "index"} for p in plans],
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False, default=list))
        return

    mode = "SIMULATION (--dry-run) : aucune image écrite" if dry_run else "EXTRACTION"
    print(f"skf-design-extractor : {mode}")
    print(f"Destination : {out_dir}   Seuil de confiance : {min_conf:.2f}")
    if spec:
        print(f"Cahier : {spec.get('spec_source')}")
    for warning in warnings:
        print(f"  ! {warning}")
    print()
    print(f"{'NOM':<30} {'TYPE':<12} {'LIGNE':<6} {'CADRE':<11} {'POSITION':<13} {'CONF':>5}  STATUT")
    for p in plans:
        size = f"{p['width']}x{p['height']}" if "width" in p else "-"
        pos = f"({p['x']},{p['y']})" if "x" in p else "-"
        conf = f"{p['confidence']:.2f}" if "confidence" in p else "-"
        line = str(p.get("spec_id") or "-")
        print(
            f"{p['name'][:30]:<30} {str(p.get('type', '-'))[:12]:<12} {line:<6} {size:<11} {pos:<13} "
            f"{conf:>5}  {STATUS_LABELS.get(p['status'], p['status'])}"
        )
        for message in p["messages"]:
            print(f"{'':<4}- {message}")
        if p["status"] in ("extract", "extracted") or (p["status"] == "error" and p.get("outputs")):
            for out in p.get("outputs", []):
                target = f" cible {out['target'][0]}x{out['target'][1]}" if out["target"] else ""
                budget = f", <= {out['max_kb']:g} Ko" if out["max_kb"] else ""
                line = f"{'':<4}-> {out['file']} : {out['export'][0]}x{out['export'][1]}{target}{budget}"
                if "kb" in out:
                    line += f" | écrit {out['kb']:.1f} Ko, qualité {out['quality']}"
                print(line)
                for flag in out["flags"]:
                    print(f"{'':<8}! {flag}")
    print()
    summary = ", ".join(f"{STATUS_LABELS.get(k, k)} : {v}" for k, v in counts.items())
    flagged = sum(1 for p in plans for o in p.get("outputs", []) if o["flags"] and p["status"] in ("extract", "extracted"))
    print(f"Total {len(plans)} asset(s) : {summary or 'aucun'}" + (f" | {flagged} fichier(s) avec alerte" if flagged else ""))


# --------------------------------------------------------------------------- #
# Export WebP
# --------------------------------------------------------------------------- #
def encode_webp(image: Image.Image, out: dict, floor: int):
    """Encode en respectant le budget de poids ; renvoie (octets, qualité, alertes)."""
    if out["lossless"]:
        buffer = io.BytesIO()
        image.save(buffer, "WEBP", lossless=True, quality=100, method=6)
        return buffer.getvalue(), "lossless", []
    q_min, q_max = out["quality_range"]
    budget = out["max_kb"] * 1024 if out["max_kb"] else None
    qualities = list(range(q_max, q_min - 1, -1))
    if budget:
        qualities += list(range(q_min - 2, floor, -2)) + [floor]
    data, quality = b"", q_max
    for quality in qualities:
        buffer = io.BytesIO()
        image.save(buffer, "WEBP", quality=quality, method=6)
        data = buffer.getvalue()
        if not budget or len(data) <= budget:
            break
    flags = []
    if budget and len(data) > budget:
        flags.append(f"poids {len(data) / 1024:.0f} Ko > {out['max_kb']:g} Ko même à la qualité {quality}")
    elif quality < q_min:
        flags.append(f"qualité abaissée à {quality} (plage {q_min}-{q_max}) pour tenir le poids")
    return data, quality, flags


def export_outputs(plan, base: Image.Image, out_dir: Path, floor: int):
    for out in plan["outputs"]:
        target = out_dir / out["file"]
        tmp = target.with_name(target.stem + ".tmp.webp")
        try:
            image = base.crop(tuple(out["crop"]))
            if list(image.size) != out["export"]:
                image = image.resize(tuple(out["export"]), Image.LANCZOS)
            data, quality, flags = encode_webp(image, out, floor)
            tmp.write_bytes(data)
            os.replace(tmp, target)
            out.update(path=str(target), kb=len(data) / 1024, quality=quality, mode=image.mode)
            out["flags"] += flags
        except Exception as exc:  # noqa: BLE001
            if tmp.exists():
                tmp.unlink()
            raise RuntimeError(f"{out['file']} : {exc}") from exc


# --------------------------------------------------------------------------- #
# Sous-commandes
# --------------------------------------------------------------------------- #
def cmd_info(args) -> int:
    source = Path(args.source)
    img, fmt = load_source(source)
    name = slugify(source.stem)
    print(
        json.dumps(
            {
                "source": source.name,
                "source_path": str(source),
                "format": fmt,
                "width": img.width,
                "height": img.height,
                "mode": img.mode,
                "has_alpha": has_alpha(img),
                "webp_support": bool(features.check("webp")),
                "suggested_name": name,
                "default_output": str(DEFAULT_ROOT / name),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def cmd_grid(args) -> int:
    source = Path(args.source)
    img, _ = load_source(source)
    width, height = img.size
    step = args.step or auto_step(max(width, height), 16)
    base = img.convert("RGBA")
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = get_font(max(12, round(max(width, height) / 90)))
    line_width = max(1, round(max(width, height) / 1600))
    color = (255, 0, 200, 150)

    for x in range(0, width, step):
        draw.line([(x, 0), (x, height)], fill=color, width=line_width)
        put_label(draw, x + 3, 3, str(x), font, base.size)
        put_label(draw, x + 3, height, str(x), font, base.size)
    for y in range(0, height, step):
        draw.line([(0, y), (width, y)], fill=color, width=line_width)
        put_label(draw, 3, y + 3, str(y), font, base.size)
        put_label(draw, width, y + 3, str(y), font, base.size)

    out = control_path(source, "grid", args.out)
    Image.alpha_composite(base, overlay).convert("RGB").save(out)
    print(json.dumps({"preview": str(out), "step": step, "width": width, "height": height}, ensure_ascii=False))
    return 0


def cmd_zoom(args) -> int:
    source = Path(args.source)
    img, _ = load_source(source)
    width, height = img.size
    x0, y0 = max(0, args.x - args.margin), max(0, args.y - args.margin)
    x1 = min(width, args.x + args.width + args.margin)
    y1 = min(height, args.y + args.height + args.margin)
    if x1 <= x0 or y1 <= y0:
        return error_exit("zone de zoom vide ou hors de l'image")

    region = img.convert("RGBA").crop((x0, y0, x1, y1))
    white = Image.new("RGBA", region.size, (255, 255, 255, 255))
    region = Image.alpha_composite(white, region)
    scale = args.scale or max(1, min(8, 1400 // max(region.size)))
    big = region.resize((region.width * scale, region.height * scale), Image.NEAREST)

    overlay = Image.new("RGBA", big.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = get_font(13)
    step = args.step or auto_step(max(region.size), 20)
    color = (255, 0, 200, 140)
    start_x = -(-x0 // step) * step
    for sx in range(start_x, x1, step):
        px = (sx - x0) * scale
        draw.line([(px, 0), (px, big.height)], fill=color, width=1)
        put_label(draw, px + 2, 2, str(sx), font, big.size)
    start_y = -(-y0 // step) * step
    for sy in range(start_y, y1, step):
        py = (sy - y0) * scale
        draw.line([(0, py), (big.width, py)], fill=color, width=1)
        put_label(draw, 2, py + 2, str(sy), font, big.size)

    bx0, by0 = (args.x - x0) * scale, (args.y - y0) * scale
    bx1, by1 = bx0 + args.width * scale, by0 + args.height * scale
    draw.rectangle((bx0, by0, bx1 - 1, by1 - 1), outline=(0, 200, 90, 255), width=2)

    out = control_path(source, f"zoom-{args.x}-{args.y}", args.out)
    Image.alpha_composite(big, overlay).convert("RGB").save(out)
    print(
        json.dumps(
            {"preview": str(out), "region": [x0, y0, x1, y1], "scale": scale, "grid_step": step},
            ensure_ascii=False,
        )
    )
    return 0


def cmd_snap(args) -> int:
    source = Path(args.source)
    img, _ = load_source(source)
    width, height = img.size
    m = args.margin
    search = (
        max(0, args.x - m),
        max(0, args.y - m),
        min(width, args.x + args.width + m),
        min(height, args.y + args.height + m),
    )
    region = to_output_mode(img).convert("RGB").crop(search)
    rw, rh = region.size
    if rw < 3 or rh < 3:
        return error_exit("zone de recherche trop petite ou hors de l'image")

    border = (
        pixels(region.crop((0, 0, rw, 1)))
        + pixels(region.crop((0, rh - 1, rw, rh)))
        + pixels(region.crop((0, 0, 1, rh)))
        + pixels(region.crop((rw - 1, 0, rw, rh)))
    )
    buckets = [(r // 8, g // 8, b // 8) for r, g, b in border]
    bucket, count = Counter(buckets).most_common(1)[0]
    members = [px for px, bk in zip(border, buckets) if bk == bucket]
    bg = tuple(sum(px[i] for px in members) // len(members) for i in range(3))
    uniformity = count / len(border)

    diff = ImageChops.difference(region, Image.new("RGB", region.size, bg)).convert("L")
    mask = diff.point(lambda v: 255 if v > args.tolerance else 0)
    if not args.no_denoise:
        mask = mask.filter(ImageFilter.MedianFilter(3))
    bbox = mask.getbbox()

    result = {
        "search_area": list(search),
        "background": "#%02x%02x%02x" % bg,
        "background_uniformity": round(uniformity, 2),
        "warnings": [],
    }
    if uniformity < 0.6:
        result["warnings"].append("fond peu uniforme : suggestion peu fiable, vérifier avec zoom")
    if not bbox:
        result["suggested"] = None
        result["warnings"].append("aucun élément distinct du fond détecté")
    else:
        left, top, right, bottom = bbox
        result["suggested"] = {
            "x": search[0] + left,
            "y": search[1] + top,
            "width": right - left,
            "height": bottom - top,
        }
        if left == 0 or top == 0 or right == rw or bottom == rh:
            result["warnings"].append(
                "le contenu touche le bord de la zone de recherche : élargir --margin ou vérifier "
                "qu'un élément voisin n'est pas inclus"
            )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def cmd_preview(args) -> int:
    _, source, img, _, plans, warnings, _ = load_context(args)
    base = img.convert("RGBA")
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    size = max(base.size)
    font = get_font(max(12, round(size / 100)))
    line_width = max(2, round(size / 700))
    drawable = sorted((p for p in plans if "x" in p), key=lambda p: -(p["width"] * p["height"]))
    for p in drawable:
        color = STATUS_COLORS.get(p["status"], (200, 0, 200, 255))
        x, y, w, h = p["x"], p["y"], p["width"], p["height"]
        draw.rectangle((x, y, x + w - 1, y + h - 1), fill=color[:3] + (35,))
        if "box" in p and p["padding"]:
            bx0, by0, bx1, by1 = p["box"]
            draw.rectangle((bx0, by0, bx1 - 1, by1 - 1), outline=color[:3] + (140,), width=1)
        for out in p.get("outputs", []):
            if out["target"] and out["crop"] != list(p["box"]):
                cx0, cy0, cx1, cy1 = out["crop"]
                draw.rectangle((cx0, cy0, cx1 - 1, cy1 - 1), outline=(255, 255, 255, 230), width=1)
        draw.rectangle((x, y, x + w - 1, y + h - 1), outline=color, width=line_width)
        label = p["name"]
        if p.get("spec_id"):
            label += f" [L{p['spec_id']}]"
        if "confidence" in p:
            label += f" ({p['confidence']:.2f})"
        put_label(draw, x + 4, y + 4, label, font, base.size, bg=color[:3] + (220,))

    out_path = control_path(source, "preview", args.out)
    Image.alpha_composite(base, overlay).convert("RGB").save(out_path)
    print(json.dumps({"preview": str(out_path), "warnings": warnings,
                      "legend": {"vert": "à extraire", "orange": "confiance insuffisante",
                                 "rouge": "reconstruction requise", "bleu": "doublon",
                                 "violet": "erreur", "blanc fin": "recadrage au ratio du cahier"}},
                     ensure_ascii=False))
    return 0


def cmd_extract(args) -> int:
    manifest_path, out_dir = resolve_paths(args)
    _, _, img, spec, plans, warnings, min_conf = load_context(args, manifest_path)

    if not args.dry_run and any(p["status"] == "extract" for p in plans):
        if not features.check("webp"):
            return error_exit("Pillow est installé sans support WebP (libwebp manquante)")
        out_dir.mkdir(parents=True, exist_ok=True)
        base = to_output_mode(img)
        for p in plans:
            if p["status"] != "extract":
                continue
            try:
                export_outputs(p, base, out_dir, args.quality_floor)
                p["status"] = "extracted"
            except RuntimeError as exc:
                p["status"] = "error"
                p["messages"].append(f"échec de l'export : {exc}")

    print_report(plans, warnings, min_conf, out_dir, args.dry_run, args.json, spec)
    return 1 if any(p["status"] == "error" for p in plans) else 0


def cmd_spec(args) -> int:
    spec = asset_spec.parse_spec(args.file)
    out = Path(args.out) if args.out else None
    if out:
        asset_spec.save_spec(spec, out)
    if args.json or not out:
        print(json.dumps(spec, indent=2, ensure_ascii=False))
        return 0
    print(f"Cahier : {args.file} -> {out}")
    rules = spec["rules"]
    print("Règles : " + ", ".join(f"{k}={v}" for k, v in rules.items() if k != "notes"))
    print()
    print(f"{'#':>4}  {'TYPE':<6} {'TAILLE':<11} {'RATIO':<7} {'POIDS':>8}  {'LIEN':<14} EMPLACEMENT")
    for item in spec["items"]:
        size = f"{item['target']['width']}x{item['target']['height']}" if item["target"] else "-"
        ratio = f"{item['ratio']:.2f}" if item["ratio"] else "-"
        weight = f"{item['max_kb']:g} Ko" if item["max_kb"] else "-"
        link = ""
        if item["same_as"]:
            link = "= L" + ",".join(map(str, item["same_as"]))
        elif item["variant_of"]:
            link = f"variante L{item['variant_of']}"
        print(f"{item['id']:>4}  {item['kind']:<6} {size:<11} {ratio:<7} {weight:>8}  {link:<14} {item['emplacement'][:70]}")
        for note in item["notes"]:
            print(f"{'':<8}note : {note[:150]}")
        for warning in item["warnings"]:
            print(f"{'':<8}! {warning}")
    for warning in spec["warnings"]:
        print(f"! {warning}")
    return 0


def dhash(image: Image.Image, box) -> int:
    small = image.crop(tuple(box)).convert("L").resize((9, 8), Image.LANCZOS)
    values = pixels(small)
    bits = 0
    for row in range(8):
        for col in range(8):
            bits = (bits << 1) | (values[row * 9 + col] > values[row * 9 + col + 1])
    return bits


def expand_manifests(items: list[str]) -> list[Path]:
    paths: list[Path] = []
    for item in items:
        path = Path(item)
        if path.is_dir():
            paths += sorted(path.rglob("assets.json"))
        else:
            paths.append(path)
    unique = []
    for path in paths:
        if path.resolve() not in [u.resolve() for u in unique]:
            unique.append(path)
    if not unique:
        raise FileNotFoundError("aucun assets.json trouvé")
    return unique


def asset_state(plan, manifest_dir: Path) -> tuple[str, list[dict], list[str]]:
    """État réel d'un asset : fichiers présents sur disque et alertes."""
    files, alerts = [], []
    if plan["status"] not in ("extract", "extracted"):
        return {
            "skip_reconstruction": "à fournir (reconstruction)",
            "skip_low_confidence": "à confirmer (confiance)",
            "skip_duplicate": "doublon",
            "error": "erreur",
        }.get(plan["status"], plan["status"]), files, list(plan["messages"])
    present = 0
    for out in plan.get("outputs", []):
        path = manifest_dir / out["file"]
        entry = {"file": out["file"], "spec_id": out["spec_id"], "target": out["target"], "path": str(path)}
        flags = list(out["flags"])
        if path.is_file():
            present += 1
            with Image.open(path) as written:
                entry["size"] = list(written.size)
            entry["kb"] = round(path.stat().st_size / 1024, 1)
            if out["target"] and entry["size"] != out["target"]:
                flags = [f for f in flags if not f.startswith(("résolution", "agrandi"))]
                flags.append(f"{entry['size'][0]}x{entry['size'][1]} au lieu de {out['target'][0]}x{out['target'][1]}")
            if out["max_kb"] and entry["kb"] > out["max_kb"]:
                flags.append(f"{entry['kb']:g} Ko > {out['max_kb']:g} Ko")
        entry["alerts"] = flags
        alerts += [f"{out['file']} : {f}" for f in flags]
        files.append(entry)
    if present == len(files) and files:
        state = "produit"
    elif present:
        state = "partiellement produit"
    else:
        state = "prêt à extraire"
    return state, files, alerts


def cmd_link(args) -> int:
    manifests = expand_manifests(args.manifests)
    spec = asset_spec.load_spec(args.spec) if args.spec else None
    mockups, assets = [], []

    for manifest_path in manifests:
        ns = argparse.Namespace(source=None, spec=args.spec, min_confidence=args.min_confidence,
                                padding=None, rescale=False, allow_upscale=False)
        manifest, source, img, manifest_spec, plans, warnings, _ = load_context(ns, manifest_path)
        spec = spec or manifest_spec
        mockup = manifest.get("mockup") or slugify(source.stem)
        mockups.append({"mockup": mockup, "page": manifest.get("page"), "source": str(source),
                        "manifest": str(manifest_path), "assets": len(plans), "warnings": warnings})
        for plan in plans:
            state, files, alerts = asset_state(plan, manifest_path.parent)
            record = {
                "mockup": mockup,
                "asset": plan["name"],
                "ref": f"{mockup}/{plan['name']}",
                "type": plan.get("type"),
                "spec_id": plan.get("spec_id"),
                "state": state,
                "files": files,
                "alerts": alerts,
                "confidence": plan.get("confidence"),
                "duplicate_of": plan.get("duplicate_of"),
                "frame": [plan.get("x"), plan.get("y"), plan.get("width"), plan.get("height")],
                "area": plan.get("width", 0) * plan.get("height", 0),
            }
            if "box" in plan:
                record["_hash"] = dhash(img, plan["box"])
            assets.append(record)

    # Doublons probables entre maquettes (empreinte perceptuelle des cadres)
    hints = []
    declared = {(a["ref"], a["duplicate_of"]) for a in assets if a["duplicate_of"]}
    hashed = [a for a in assets if "_hash" in a]
    for i, first in enumerate(hashed):
        for second in hashed[i + 1:]:
            distance = bin(first["_hash"] ^ second["_hash"]).count("1")
            if distance > DUPLICATE_HASH_DISTANCE:
                continue
            if (first["ref"], second["ref"]) in declared or (second["ref"], first["ref"]) in declared:
                continue
            keep = first if first["area"] >= second["area"] else second
            other = second if keep is first else first
            hints.append({"assets": [first["ref"], second["ref"]], "distance": distance,
                          "suggestion": f"garder {keep['ref']} (cadre le plus grand), marquer {other['ref']} en duplicate_of"})
    for record in assets:
        record.pop("_hash", None)

    # Couverture du cahier
    items_out, off_spec = [], [a for a in assets if a["spec_id"] is None]
    if spec:
        pages = {asset_spec.norm(m["page"]): m["mockup"] for m in mockups if m.get("page")}
        for item in spec["items"]:
            entry = {k: item.get(k) for k in ("id", "kind", "section", "emplacement", "page", "target", "max_kb",
                                              "same_as", "variant_of", "notes")}
            if item["kind"] == "video":
                entry["status"] = "vidéo : hors maquette statique"
                entry["occurrences"] = []
            elif item.get("same_as"):
                entry["status"] = "même fichier que " + ", ".join(f"L{r}" for r in item["same_as"])
                entry["occurrences"] = []
            else:
                parent = item.get("variant_of") or item["id"]
                occurrences = []
                for record in assets:
                    if record["spec_id"] != parent:
                        continue
                    files = [f for f in record["files"] if f["spec_id"] == item["id"]]
                    occurrences.append({"ref": record["ref"], "state": record["state"], "files": files,
                                        "alerts": [a for f in files for a in f.get("alerts", [])] if files
                                        else record["alerts"]})
                entry["occurrences"] = occurrences
                states = Counter(o["state"] for o in occurrences)
                if states.get("produit") or states.get("partiellement produit"):
                    produced = states.get("produit", 0) + states.get("partiellement produit", 0)
                    entry["status"] = f"produit ({produced} image(s))"
                elif states.get("prêt à extraire"):
                    entry["status"] = f"prêt à extraire ({states['prêt à extraire']} image(s))"
                elif occurrences and all(o["state"] == "doublon" for o in occurrences):
                    entry["status"] = "doublons seulement : source retenue manquante"
                elif occurrences:
                    entry["status"] = "à fournir par le designer"
                elif item.get("page") and asset_spec.norm(item["page"]) in pages:
                    entry["status"] = f"non trouvé dans la maquette {pages[asset_spec.norm(item['page'])]}"
                else:
                    entry["status"] = "absent des maquettes fournies"
                if item.get("variant_of"):
                    entry["status"] = f"variante de L{item['variant_of']} : " + entry["status"]
            items_out.append(entry)

    out_dir = Path(args.out) if args.out else Path(os.path.commonpath([str(m.parent.resolve()) for m in manifests]))
    if len(manifests) == 1 and not args.out:
        out_dir = manifests[0].parent.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    result = {
        "generated_by": "skf-design-extractor",
        "spec_source": spec.get("spec_source") if spec else None,
        "rules": spec.get("rules") if spec else None,
        "mockups": mockups,
        "items": items_out,
        "assets": assets,
        "off_spec": [a["ref"] for a in off_spec] if spec else [],
        "duplicate_hints": hints,
    }
    map_path = out_dir / "assets-map.json"
    report_path = out_dir / "assets-report.md"
    map_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report_path.write_text(render_link_report(result), encoding="utf-8")
    print(json.dumps({"map": str(map_path), "report": str(report_path), "mockups": len(mockups),
                      "assets": len(assets), "spec_items": len(items_out), "duplicate_hints": len(hints)},
                     ensure_ascii=False))
    return 1 if any(a["state"] == "erreur" for a in assets) else 0


def md_cell(text) -> str:
    return str(text).replace("|", "/").replace("\n", " ")


def render_link_report(result: dict) -> str:
    lines = ["# Rapport d'extraction des assets", ""]
    if result["spec_source"]:
        lines.append(f"Cahier : `{result['spec_source']}`")
    lines.append(f"Maquettes : {', '.join(m['mockup'] + (' (' + m['page'] + ')' if m.get('page') else '') for m in result['mockups'])}")
    lines.append("")

    if result["items"]:
        lines += ["## Couverture du cahier", "",
                  "| # | Emplacement | Taille | Statut | Images | Alertes |", "|---|---|---|---|---|---|"]
        for item in result["items"]:
            size = f"{item['target']['width']} × {item['target']['height']}" if item.get("target") else ""
            refs = "<br>".join(
                o["ref"] + (" : " + ", ".join(f["file"] for f in o["files"]) if o["files"] else f" ({o['state']})")
                for o in item["occurrences"]
            )
            alerts = "<br>".join(sorted({a for o in item["occurrences"] if o["state"] != "doublon" for a in o["alerts"]}))
            lines.append(f"| {item['id']} | {md_cell(item['emplacement'])} | {size} | {md_cell(item['status'])} "
                         f"| {md_cell(refs) if refs else ''} | {md_cell(alerts)} |")
        lines.append("")

    blocked = [a for a in result["assets"] if a["state"] in ("à fournir (reconstruction)", "à confirmer (confiance)")]
    if blocked:
        lines += ["## À fournir ou à confirmer", ""]
        for asset in blocked:
            lines.append(f"- **{asset['ref']}** (L{asset['spec_id'] or '-'}) : {asset['state']}. {'; '.join(asset['alerts'])}")
        lines.append("")

    flagged = [a for a in result["assets"] if a["state"] in ("produit", "prêt à extraire", "partiellement produit") and a["alerts"]]
    if flagged:
        lines += ["## Alertes sur les fichiers produits", ""]
        for asset in flagged:
            for alert in asset["alerts"]:
                lines.append(f"- {asset['ref']} : {alert}")
        lines.append("")

    if result["duplicate_hints"]:
        lines += ["## Doublons probables entre maquettes", ""]
        for hint in result["duplicate_hints"]:
            lines.append(f"- {' et '.join(hint['assets'])} (écart {hint['distance']}/64) : {hint['suggestion']}")
        lines.append("")

    if result["off_spec"]:
        lines += ["## Hors cahier", "", "Extraits sans contrainte de taille : à ajouter au cahier si besoin.", ""]
        lines += [f"- {ref}" for ref in result["off_spec"]]
        lines.append("")

    lines += ["## Détail par maquette", "", "| Maquette | Asset | Ligne | État | Fichiers |", "|---|---|---|---|---|"]
    for asset in result["assets"]:
        files = ", ".join(
            f"{f['file']} ({f['size'][0]}×{f['size'][1]}, {f['kb']:g} Ko)" if "size" in f else f["file"]
            for f in asset["files"]
        )
        lines.append(f"| {asset['mockup']} | {asset['asset']} | {asset['spec_id'] or '-'} | {asset['state']} | {md_cell(files)} |")
    lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="extract_design_assets.py",
        description="Extraction des assets graphiques d'une maquette JPG/PNG (crop exact, export WebP).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("info", help="dimensions et métadonnées de la maquette")
    p.add_argument("source")
    p.set_defaults(func=cmd_info)

    p = sub.add_parser("grid", help="maquette avec grille de coordonnées (contrôle)")
    p.add_argument("source")
    p.add_argument("--step", type=int, help="pas de la grille en px (auto par défaut)")
    p.add_argument("--out", help="chemin de l'image de contrôle (défaut : dossier temporaire)")
    p.set_defaults(func=cmd_grid)

    for name, func, helptext in (
        ("zoom", cmd_zoom, "agrandit une zone avec grille fine (contrôle)"),
        ("snap", cmd_snap, "propose un cadrage serré sur fond uni"),
    ):
        p = sub.add_parser(name, help=helptext)
        p.add_argument("source")
        for coord in ("x", "y", "width", "height"):
            p.add_argument(f"--{coord}", type=int, required=True)
        if name == "zoom":
            p.add_argument("--margin", type=int, default=24, help="marge affichée autour du cadre (px)")
            p.add_argument("--scale", type=int, help="facteur d'agrandissement (auto par défaut)")
            p.add_argument("--step", type=int, help="pas de la grille en px source (auto par défaut)")
            p.add_argument("--out", help="chemin de l'image de contrôle")
        else:
            p.add_argument("--margin", type=int, default=16, help="élargissement de la zone de recherche (px)")
            p.add_argument("--tolerance", type=int, default=28, help="écart au fond (0-255) considéré comme contenu")
            p.add_argument("--no-denoise", action="store_true", help="désactive le filtre anti-bruit JPEG")
        p.set_defaults(func=func)

    for name, func, helptext in (
        ("preview", cmd_preview, "dessine les cadres du manifest (contrôle)"),
        ("extract", cmd_extract, "découpe et exporte les assets en WebP"),
    ):
        p = sub.add_parser(name, help=helptext)
        p.add_argument("--manifest", help="chemin de assets.json (défaut : <output>/assets.json)")
        p.add_argument("--output", help="dossier de destination des assets")
        p.add_argument("--source", help="chemin de la maquette (défaut : source_path/source du manifest)")
        p.add_argument("--min-confidence", type=float, help="seuil de confiance (défaut : 0.80)")
        p.add_argument("--padding", type=int, help="padding par défaut des assets qui n'en définissent pas")
        p.add_argument("--rescale", action="store_true",
                       help="remet à l'échelle si width/height du manifest diffèrent de la maquette")
        p.add_argument("--spec", help="cahier de tailles (md, xlsx, csv ou assets-spec.json)")
        p.add_argument("--allow-upscale", action="store_true",
                       help="agrandit les crops trop petits jusqu'à la taille du cahier (placeholder)")
        if name == "extract":
            p.add_argument("--dry-run", action="store_true", help="valide et affiche le plan sans écrire d'image")
            p.add_argument("--json", action="store_true", help="rapport au format JSON")
            p.add_argument("--quality-floor", type=int, default=DEFAULT_QUALITY_FLOOR,
                           help="qualité WebP minimale tolérée pour tenir le poids visé (défaut : 60)")
        else:
            p.add_argument("--out", help="chemin de l'image de contrôle")
        p.set_defaults(func=func)

    p = sub.add_parser("spec", help="lit un cahier de tailles et produit assets-spec.json")
    p.add_argument("file", help="cahier .md, .xlsx ou .csv")
    p.add_argument("--out", help="chemin du assets-spec.json à écrire (sinon affichage JSON)")
    p.add_argument("--json", action="store_true", help="affiche le JSON même avec --out")
    p.set_defaults(func=cmd_spec)

    p = sub.add_parser("link", help="relie les maquettes au cahier : couverture, doublons, rapport")
    p.add_argument("manifests", nargs="+", help="fichiers assets.json ou dossiers à parcourir")
    p.add_argument("--spec", help="cahier (sinon le champ 'spec' des manifests)")
    p.add_argument("--out", help="dossier où écrire assets-map.json et assets-report.md")
    p.add_argument("--min-confidence", type=float, help="seuil de confiance (défaut : 0.80)")
    p.set_defaults(func=cmd_link)
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (FileNotFoundError, ValueError, ManifestError, RuntimeError) as exc:
        return error_exit(str(exc))


if __name__ == "__main__":
    sys.exit(main())
