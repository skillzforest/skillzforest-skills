"""Shared helpers: load a CMS profile and a content file, walk dotted paths, fill
templates and resolve `@media:` / `@lookup:` references. Standard library only.

Paths:     "record.page_content.texts.*.headline"   * = every key of a map / item of a list
Templates: "{{record.slug}}" alone → the value itself (any type); inside a longer
           string → its text. Unknown paths → an error, never a silent empty string.
"""

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROFILES = HERE.parent / "profiles"
TEMPLATE = re.compile(r"\{\{\s*([^}]+?)\s*\}\}")
MISSING = object()


def load_profile(name_or_path: str) -> dict:
    path = Path(name_or_path).expanduser()
    if not path.is_file():
        path = PROFILES / f"{name_or_path}.json"
    if not path.is_file():
        available = ", ".join(sorted(p.stem for p in PROFILES.glob("*.json")))
        raise SystemExit(f"profile not found: {name_or_path} (available: {available})")
    profile = json.loads(path.read_text())
    profile["_path"] = str(path)
    return profile


def load_content(path: str) -> tuple[dict, Path]:
    file = Path(path).expanduser().resolve()
    return json.loads(file.read_text()), file.parent


def get(data, dotted: str, default=MISSING):
    """One value at a dotted path (no wildcards); `default` when absent."""
    current = data
    for part in dotted.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        elif isinstance(current, list) and part.isdigit() and int(part) < len(current):
            current = current[int(part)]
        else:
            if default is MISSING:
                raise KeyError(dotted)
            return default
    return current


def walk(data, dotted: str, prefix: str = ""):
    """Every (concrete path, value) matching a path that may hold `*`."""
    if not dotted:
        yield prefix.rstrip("."), data
        return
    head, _, rest = dotted.partition(".")
    if head == "*":
        items = data.items() if isinstance(data, dict) else enumerate(data) if isinstance(data, list) else []
        for key, value in items:
            yield from walk(value, rest, f"{prefix}{key}.")
    elif isinstance(data, dict) and head in data:
        yield from walk(data[head], rest, f"{prefix}{head}.")
    elif isinstance(data, list) and head.isdigit() and int(head) < len(data):
        yield from walk(data[int(head)], rest, f"{prefix}{head}.")


def render(value, context: dict):
    """Fill `{{…}}` templates, recursively, keys included."""
    if isinstance(value, str):
        whole = TEMPLATE.fullmatch(value.strip())
        if whole:
            return get(context, whole.group(1))
        return TEMPLATE.sub(lambda m: str(get(context, m.group(1))), value)
    if isinstance(value, list):
        return [render(v, context) for v in value]
    if isinstance(value, dict):
        return {render(k, context): render(v, context) for k, v in value.items()}
    return value


def resolve_refs(value, resolver):
    """Replace `@media:<key>` and `@lookup:<name>:<key>` strings (values and keys)."""
    if isinstance(value, str) and value.startswith(("@media:", "@lookup:")):
        return resolver(value)
    if isinstance(value, list):
        return [resolve_refs(v, resolver) for v in value]
    if isinstance(value, dict):
        return {resolve_refs(k, resolver): resolve_refs(v, resolver) for k, v in value.items()}
    return value


def refs_in(value, found: set | None = None) -> set:
    found = set() if found is None else found
    if isinstance(value, str) and value.startswith(("@media:", "@lookup:")):
        found.add(value)
    elif isinstance(value, list):
        for v in value:
            refs_in(v, found)
    elif isinstance(value, dict):
        for k, v in value.items():
            refs_in(k, found)
            refs_in(v, found)
    return found


def condition(expr: str | None, context: dict) -> bool:
    """`path` truthy · `!path` falsy · `path == text` · `path != text`, joined by `&&`."""
    if not expr:
        return True
    if "&&" in expr:
        return all(condition(part, context) for part in expr.split("&&"))
    match = re.fullmatch(r"\s*(\S+)\s*(==|!=)\s*(.+?)\s*", expr)
    if match:
        left = get(context, match.group(1), None)
        equal = str(left) == match.group(3).strip("'\"")
        return equal if match.group(2) == "==" else not equal
    negate = expr.strip().startswith("!")
    value = get(context, expr.strip().lstrip("!"), None)
    return not value if negate else bool(value)
