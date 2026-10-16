#!/usr/bin/env python3
"""Check a content file against its CMS profile before anything is sent.

    validate_content.py <content.json> [--profile <name|path>]

Rules come from `profile.kinds.<kind>.fields` (see references/profile-format.md):
required, type, min_length / max_length, min_items / max_items, enum, pattern,
locales (a map that must hold every profile locale), and media slots
(file exists, format, dimensions, weight). Prints a JSON report; exit 0 when there's
no error (warnings allowed), 1 otherwise.
"""

import argparse
import json
import re
import struct
import sys
from pathlib import Path

from cms_profile import MISSING, get, load_content, load_profile, refs_in, walk

TYPES = {"string": str, "integer": int, "number": (int, float), "boolean": bool, "array": list, "object": dict}
PLACEHOLDER = re.compile(r"\b(TODO|TBD|lorem ipsum|XXX)\b|\[(?:à|to) (?:compléter|fill)\]", re.I)


def image_size(path: Path) -> tuple[int, int] | None:
    head = path.read_bytes()[:64 * 1024]
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", head[16:24])
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        chunk = head[12:16]
        if chunk == b"VP8X":
            return 1 + int.from_bytes(head[24:27], "little"), 1 + int.from_bytes(head[27:30], "little")
        if chunk == b"VP8 ":
            w, h = struct.unpack("<HH", head[26:30])
            return w & 0x3FFF, h & 0x3FFF
        if chunk == b"VP8L":
            bits = int.from_bytes(head[21:25], "little")
            return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    if head[:2] == b"\xff\xd8":
        i = 2
        while i < len(head) - 9:
            if head[i] != 0xFF:
                i += 1
                continue
            marker = head[i + 1]
            if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                h, w = struct.unpack(">HH", head[i + 5:i + 9])
                return w, h
            i += 2 + struct.unpack(">H", head[i + 2:i + 4])[0]
    return None


def check_fields(content: dict, rules: list[dict], profile: dict, errors: list, warnings: list) -> None:
    locales = profile.get("locales", [])
    for rule in rules:
        if isinstance(rule.get("enum"), str):  # "@icons" → the profile's `icons` list
            rule = {**rule, "enum": profile.get(rule["enum"].lstrip("@"), [])}
        path = rule["path"]
        matches = list(walk(content, path))
        if rule.get("when"):
            key, _, expected = rule["when"].partition("==")
            if str(get(content, key.strip(), None)) != expected.strip():
                continue
        if not matches or all(v in (None, "", [], {}) for _, v in matches):
            if rule.get("required"):
                errors.append(f"{path}: required")
            continue
        for where, value in matches:
            if value is None:
                continue
            kind = rule.get("type")
            if kind and not isinstance(value, TYPES[kind]):
                errors.append(f"{where}: expected {kind}, got {type(value).__name__}")
                continue
            if isinstance(value, str):
                if rule.get("required") and not value.strip():
                    errors.append(f"{where}: empty")
                if rule.get("max_length") == 0 and value:
                    errors.append(f"{where}: leave it out, the CMS fills it")
                elif "max_length" in rule and len(value) > rule["max_length"]:
                    errors.append(f"{where}: {len(value)} characters, max {rule['max_length']}")
                if "min_length" in rule and len(value.strip()) < rule["min_length"]:
                    warnings.append(f"{where}: {len(value.strip())} characters, expected at least {rule['min_length']}")
                if "pattern" in rule and not value.startswith("@") and not re.fullmatch(rule["pattern"], value):
                    errors.append(f"{where}: doesn't match {rule['pattern']}")
                if PLACEHOLDER.search(value):
                    errors.append(f"{where}: placeholder text left in")
            if isinstance(value, list):
                if "max_items" in rule and len(value) > rule["max_items"]:
                    errors.append(f"{where}: {len(value)} items, max {rule['max_items']}")
                if "min_items" in rule and len(value) < rule["min_items"]:
                    warnings.append(f"{where}: {len(value)} items, expected at least {rule['min_items']}")
                for i, item in enumerate(value):
                    if not isinstance(item, str):
                        continue
                    if len(item) > rule.get("item_max_length", len(item)):
                        errors.append(f"{where}.{i}: {len(item)} characters, max {rule['item_max_length']}")
                    if PLACEHOLDER.search(item):
                        errors.append(f"{where}.{i}: placeholder text left in")
            if "enum" in rule and value not in rule["enum"]:
                errors.append(f"{where}: {value!r} not in {rule['enum']}")
            if rule.get("locales"):
                missing = [loc for loc in locales if loc not in (value or {})]
                if missing:
                    errors.append(f"{where}: missing locale(s) {', '.join(missing)}")


def check_media(content: dict, slots: dict, base: Path, errors: list, warnings: list) -> None:
    media = content.get("media", {})
    used = {ref.split(":", 1)[1] for ref in refs_in(content.get("record", {})) if ref.startswith("@media:")}
    for key in used - media.keys():
        errors.append(f"@media:{key} is used in the record but not declared in media")
    for key, slot in slots.items():
        entry = media.get(key)
        if not entry:
            if slot.get("required"):
                errors.append(f"media.{key}: required")
            continue
        file = (base / entry["file"]).resolve()
        if not file.is_file():
            errors.append(f"media.{key}: file not found {file}")
            continue
        if key not in used and not slot.get("standalone"):
            warnings.append(f"media.{key}: produced but not referenced by the record")
        size = file.stat().st_size
        if "max_bytes" in slot and size > slot["max_bytes"]:
            errors.append(f"media.{key}: {size} bytes, max {slot['max_bytes']}")
        if "target_bytes" in slot and size > slot["target_bytes"]:
            warnings.append(f"media.{key}: {size} bytes, aim for under {slot['target_bytes']}")
        formats = slot.get("formats")
        if formats and file.suffix.lower().lstrip(".") not in formats:
            errors.append(f"media.{key}: {file.suffix} not in {formats}")
        if slot.get("kind") == "image":
            dims = image_size(file)
            if dims is None:
                warnings.append(f"media.{key}: couldn't read the image size")
                continue
            w, h = dims
            if "min_width" in slot and w < slot["min_width"]:
                errors.append(f"media.{key}: {w}px wide, min {slot['min_width']}")
            if "ratio" in slot:
                rw, rh = (float(x) for x in slot["ratio"].split(":"))
                if abs(w / h - rw / rh) > 0.02:
                    errors.append(f"media.{key}: {w}×{h} isn't {slot['ratio']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("content")
    parser.add_argument("--profile")
    args = parser.parse_args()

    content, base = load_content(args.content)
    profile = load_profile(args.profile or content.get("profile", ""))
    kind = content.get("kind")
    spec = profile.get("kinds", {}).get(kind)
    errors: list[str] = []
    warnings: list[str] = []
    if spec is None:
        errors.append(f"kind {kind!r} not in profile ({', '.join(profile.get('kinds', {}))})")
    else:
        # Profile-wide rules and slots first, then the kind's own.
        rules = profile.get("fields", []) + spec.get("fields", [])
        slots = {**profile.get("media", {}), **spec.get("media", {})}
        check_fields(content, rules, profile, errors, warnings)
        check_media(content, slots, base, errors, warnings)
    unknown = [r for r in refs_in(content.get("record", {})) if r.startswith("@lookup:")
               and r.split(":")[1] not in profile.get("adapter", {}).get("lookups", {})]
    errors += [f"{r}: no such lookup in the profile" for r in unknown]
    print(json.dumps({"ok": not errors, "errors": errors, "warnings": warnings}, ensure_ascii=False, indent=2))
    sys.exit(0 if not errors else 1)


if __name__ == "__main__":
    main()
