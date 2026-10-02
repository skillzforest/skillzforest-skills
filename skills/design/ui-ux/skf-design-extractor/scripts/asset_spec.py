#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lecture d'un cahier de tailles d'assets (Markdown, Excel .xlsx ou CSV) et
normalisation en assets-spec.json.

Chaque ligne du cahier décrit un FORMAT d'image (emplacement, ratio, taille à
produire, poids visé), pas une image unique : une même ligne peut couvrir
plusieurs images (toutes les cartes produit, par exemple).

Le parsing est volontairement tolérant : il produit un brouillon que Claude
relit et corrige (précisions, liens entre lignes) avant toute extraction.
"""
from __future__ import annotations

import csv
import json
import re
import unicodedata
from pathlib import Path

HEADER_KEYS = {
    "id": ("#", "n°", "no", "num", "numero", "id", "ligne", "ref", "reference"),
    "emplacement": ("emplacement", "usage", "placement", "element", "location", "image", "asset", "nom"),
    "displayed": ("largeur affichee", "affichee", "affichage", "displayed", "largeur max"),
    "format": ("format", "ratio", "proportion", "aspect"),
    "target": ("taille a produire", "taille", "resolution", "dimension", "export", "size"),
    "weight": ("poids", "weight", "kb", "ko"),
    "duration": ("duree", "duration"),
    "notes": ("remarque", "note", "commentaire", "precision", "comment"),
}
SIZE_RE = re.compile(r"(\d{2,5})\s*[×xX*]\s*(\d{2,5})")
RATIO_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*:\s*(\d+(?:[.,]\d+)?)")
WEIGHT_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(ko|kb|mo|mb|go|gb)\b", re.I)
LINE_REF_RE = re.compile(r"lignes?\s+((?:\d+\s*(?:,|et|&|and|\+)?\s*)+)", re.I)
QUALITY_RE = re.compile(r"qualit[ée]\s*:?\s*(\d{2,3})(?:\s*(?:[-–—à]|to)\s*(\d{2,3}))?", re.I)
MAX_IMAGE_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(ko|kb|mo|mb)\s*(?:par|per)\s*image", re.I)
MAX_VIDEO_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(ko|kb|mo|mb)\s*(?:par|per)\s*vid", re.I)
PRECISION_RE = re.compile(r"^\s*[-*]\s*\*{0,2}\s*lignes?\s+(\d+(?:\s*(?:,|et|&)\s*\d+)*)\s*\*{0,2}\s*:\s*\*{0,2}\s*(.+)$", re.I)


# --------------------------------------------------------------------------- #
# Utilitaires texte
# --------------------------------------------------------------------------- #
def norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", text).strip().lower()


def clean(text) -> str:
    if text is None:
        return ""
    text = str(text).replace("**", "").replace("`", "").replace(" ", " ")
    return re.sub(r"\s+", " ", text).strip()


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()


def to_kb(value: str, unit: str) -> float:
    number = float(value.replace(",", "."))
    unit = unit.lower()
    if unit in ("mo", "mb"):
        return number * 1024
    if unit in ("go", "gb"):
        return number * 1024 * 1024
    return number


def line_refs(text: str) -> list[int]:
    refs: list[int] = []
    for match in LINE_REF_RE.finditer(text):
        refs += [int(n) for n in re.findall(r"\d+", match.group(1))]
    return refs


def map_headers(cells: list[str]) -> dict[str, int]:
    """Associe chaque colonne connue à son index ; {} si ce n'est pas un en-tête."""
    mapping: dict[str, int] = {}
    for index, cell in enumerate(cells):
        label = norm(clean(cell))
        if not label:
            continue
        for key, words in HEADER_KEYS.items():
            if key in mapping:
                continue
            if any(label == w or (len(w) > 2 and w in label) for w in words):
                mapping[key] = index
                break
    has_core = "emplacement" in mapping and ("target" in mapping or "format" in mapping)
    return mapping if has_core else {}


# --------------------------------------------------------------------------- #
# Lecture des sources
# --------------------------------------------------------------------------- #
def split_md_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def read_markdown(text: str):
    """Renvoie (tables, texte_hors_tables). Une table = (heading, rows)."""
    tables, other = [], []
    heading = ""
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if re.match(r"^\s*#{1,6}\s", line):
            heading = clean(line.lstrip("# "))
        if line.strip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-{2,}", lines[i + 1]):
            rows = [split_md_row(line)]
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(split_md_row(lines[i]))
                i += 1
            tables.append((heading, rows))
            continue
        other.append(line)
        i += 1
    return tables, "\n".join(other)


def read_rows_xlsx(path: Path):
    try:
        import openpyxl
    except ImportError as exc:
        raise RuntimeError("openpyxl manquant : python3 -m pip install openpyxl") from exc
    workbook = openpyxl.load_workbook(path, data_only=True, read_only=True)
    tables, other = [], []
    for sheet in workbook.worksheets:
        rows = [["" if v is None else str(v) for v in row] for row in sheet.iter_rows(values_only=True)]
        rows = [r for r in rows if any(c.strip() for c in r)]
        tables.append((sheet.title, rows))
        other += [" ".join(r) for r in rows]
    return tables, "\n".join(other)


def read_rows_csv(path: Path):
    raw = path.read_text(encoding="utf-8-sig")
    try:
        dialect = csv.Sniffer().sniff(raw[:4096], delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    rows = [r for r in csv.reader(raw.splitlines(), dialect) if any(c.strip() for c in r)]
    return [(path.stem, rows)], raw


# --------------------------------------------------------------------------- #
# Interprétation
# --------------------------------------------------------------------------- #
def parse_rules(text: str) -> dict:
    rules: dict = {"format": "webp", "notes": []}
    quality = QUALITY_RE.search(text)
    if quality:
        low = int(quality.group(1))
        high = int(quality.group(2) or quality.group(1))
        rules["quality_min"], rules["quality_max"] = min(low, high), max(low, high)
    max_image = MAX_IMAGE_RE.search(text)
    if max_image:
        rules["max_image_kb"] = to_kb(max_image.group(1), max_image.group(2))
    max_video = MAX_VIDEO_RE.search(text)
    if max_video:
        rules["max_video_kb"] = to_kb(max_video.group(1), max_video.group(2))
    lowered = norm(text)
    if "pas de texte" in lowered or "no text" in lowered:
        rules["no_text_in_images"] = True
    margin = re.search(r"(\d{1,2})\s*%\s*de\s*marge", lowered)
    if margin:
        rules["subject_margin_pct"] = int(margin.group(1))
    if "svg n'est pas accepte" in lowered or "svg non accepte" in lowered:
        rules["svg_allowed"] = False
    return rules


def parse_precisions(text: str) -> dict[int, list[str]]:
    notes: dict[int, list[str]] = {}
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        match = PRECISION_RE.match(lines[i])
        if match:
            body = [match.group(2)]
            i += 1
            while i < len(lines) and lines[i].startswith((" ", "\t")) and not PRECISION_RE.match(lines[i]):
                body.append(lines[i].strip())
                i += 1
            sentence = clean(" ".join(body))
            for ref in [int(n) for n in re.findall(r"\d+", match.group(1))]:
                notes.setdefault(ref, []).append(sentence)
            continue
        i += 1
    return notes


def parse_item(cells: list[str], mapping: dict[str, int], kind: str, section: str, auto_id: int) -> dict | None:
    def cell(key):
        index = mapping.get(key)
        return clean(cells[index]) if index is not None and index < len(cells) else ""

    emplacement = cell("emplacement")
    target_txt = cell("target")
    format_txt = cell("format")
    raw_id = cell("id")
    if not emplacement:
        return None

    item_id = int(re.search(r"\d+", raw_id).group()) if re.search(r"\d+", raw_id) else auto_id
    page, _, component = emplacement.partition(" : ") if " : " in emplacement else ("", "", emplacement)
    item = {
        "id": item_id,
        "kind": kind,
        "section": section,
        "emplacement": emplacement,
        "page": page or None,
        "component": component,
        "slug": slugify(emplacement)[:60],
        "displayed": cell("displayed") or None,
        "format": format_txt or None,
        "ratio": None,
        "display_ratio": None,
        "target": None,
        "max_kb": None,
        "same_as": [],
        "variant_of": None,
        "extractable": kind == "image",
        "notes": [],
        "warnings": [],
    }

    size = SIZE_RE.search(target_txt)
    if size:
        item["target"] = {"width": int(size.group(1)), "height": int(size.group(2))}
    ratio = RATIO_RE.search(format_txt)
    if ratio:
        item["display_ratio"] = f"{ratio.group(1)}:{ratio.group(2)}".replace(",", ".")
    if item["target"]:
        item["ratio"] = round(item["target"]["width"] / item["target"]["height"], 4)
    elif ratio:
        item["ratio"] = round(float(ratio.group(1).replace(",", ".")) / float(ratio.group(2).replace(",", ".")), 4)

    weight_txt = " ".join(filter(None, [cell("weight"), cell("duration")]))
    weight = WEIGHT_RE.findall(weight_txt)
    if weight:
        value, unit = weight[-1]
        item["max_kb"] = to_kb(value, unit)

    lowered = norm(target_txt + " " + emplacement)
    refs = line_refs(target_txt)
    if refs and not item["target"]:
        item["same_as"] = refs
    elif ("meme image" in lowered or "same image" in lowered) and not refs:
        item["variant_of"] = "previous" if item["target"] else None
        if not item["target"]:
            item["same_as"] = ["previous"]
    elif refs and item["target"]:
        item["variant_of"] = refs[0]

    notes_txt = cell("notes")
    if notes_txt:
        item["notes"].append(notes_txt)
    if kind == "video":
        item["extractable"] = False
        item["warnings"].append("vidéo : non extractible depuis une maquette statique")
    elif item["same_as"]:
        item["extractable"] = False
    elif not item["target"]:
        item["warnings"].append("taille à produire non reconnue : compléter 'target'")
    return item


def parse_spec(path: str | Path) -> dict:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Cahier introuvable : {path}")
    suffix = path.suffix.lower()
    if suffix in (".md", ".markdown", ".txt"):
        tables, other = read_markdown(path.read_text(encoding="utf-8"))
    elif suffix in (".xlsx", ".xlsm"):
        tables, other = read_rows_xlsx(path)
    elif suffix in (".csv", ".tsv"):
        tables, other = read_rows_csv(path)
    else:
        raise ValueError(f"Format de cahier non pris en charge : {suffix} (md, xlsx, csv)")

    spec = {
        "spec_source": str(path),
        "generated_by": "skf-design-extractor",
        "rules": parse_rules(other),
        "items": [],
        "warnings": [],
    }
    precisions = parse_precisions(other)
    auto_id = 0

    for heading, rows in tables:
        header_index, mapping = None, {}
        for index, row in enumerate(rows[:10]):
            mapping = map_headers(row)
            if mapping:
                header_index = index
                break
        if header_index is None:
            continue
        heading_norm = norm(heading)
        kind = "video" if ("video" in heading_norm or "duration" in mapping) else "image"
        section = ""
        previous = None
        for row in rows[header_index + 1:]:
            filled = [clean(c) for c in row if clean(c)]
            if not filled:
                continue
            if len(filled) == 1 and len(row) > 2:
                section = filled[0]
                continue
            row_kind = "video" if re.search(r"vid[ée]o", norm(" ".join(row))) and kind == "video" else kind
            auto_id += 1
            item = parse_item(row, mapping, row_kind, section, auto_id)
            if not item:
                continue
            if item["variant_of"] == "previous":
                item["variant_of"] = previous["id"] if previous else None
            if item["same_as"] == ["previous"]:
                item["same_as"] = [previous["id"]] if previous else []
            item["notes"] += precisions.get(item["id"], [])
            spec["items"].append(item)
            previous = item

    ids = [i["id"] for i in spec["items"]]
    for duplicate in {i for i in ids if ids.count(i) > 1}:
        spec["warnings"].append(f"identifiant de ligne {duplicate} en double")
    known = set(ids)
    for item in spec["items"]:
        for ref in item["same_as"] + ([item["variant_of"]] if item["variant_of"] else []):
            if ref not in known:
                item["warnings"].append(f"référence à une ligne inconnue : {ref}")
        if item["variant_of"] and item["target"]:
            parent = next((p for p in spec["items"] if p["id"] == item["variant_of"]), None)
            if parent and parent.get("ratio") and abs(parent["ratio"] / item["ratio"] - 1) > 0.02:
                item["warnings"].append(
                    f"variante de la ligne {parent['id']} avec un ratio différent : recadrage supplémentaire"
                )
    if not spec["items"]:
        spec["warnings"].append(
            "aucune table reconnue : il faut au moins des colonnes Emplacement et Taille à produire (ou Format)"
        )
    return spec


def index_spec(spec: dict) -> dict[int, dict]:
    return {item["id"]: item for item in spec.get("items", [])}


def variants_of(spec: dict, item_id: int) -> list[dict]:
    """Lignes à produire à partir d'une même image : la ligne elle-même puis ses variantes."""
    items = index_spec(spec)
    result = [items[item_id]] if item_id in items and items[item_id].get("target") else []
    result += [i for i in spec["items"] if i.get("variant_of") == item_id and i.get("target")]
    return result


def save_spec(spec: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_spec(path: str | Path) -> dict:
    path = Path(path)
    if path.suffix.lower() == ".json":
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    return parse_spec(path)
