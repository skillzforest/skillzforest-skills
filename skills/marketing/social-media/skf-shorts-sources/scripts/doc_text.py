#!/usr/bin/env python3
"""Extract the plain text of office documents for reading (stdlib only).

    doc_text.py <file>... [--out <folder>] [--max-chars 60000]

Handles .docx, .pptx (slide by slide), .xlsx (shared strings and inline text),
.odt / .odp, .html, .md, .txt, .csv, .json, .rtf (rough). PDFs: read them directly
with the agent's file reader, or `pdftotext` when installed — this script calls it
when it is on the PATH. Writes <out>/<name>.txt when --out is given, otherwise prints.
"""
import argparse
import html
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


def xml_text(xml: str, para_tags=("w:p", "a:p", "text:p", "text:h")):
    for tag in para_tags:
        xml = xml.replace(f"</{tag}>", "\n")
    xml = re.sub(r"<w:tab/>|<w:br/>", " ", xml)
    return html.unescape(re.sub(r"<[^>]+>", "", xml))


def docx(path):
    with zipfile.ZipFile(path) as z:
        parts = [n for n in z.namelist() if re.match(r"word/(document|header\d*|footer\d*|footnotes)\.xml", n)]
        return "\n".join(xml_text(z.read(n).decode("utf8", "ignore")) for n in sorted(parts, key=lambda n: n != "word/document.xml"))


def pptx(path):
    with zipfile.ZipFile(path) as z:
        slides = sorted((n for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml", n)),
                        key=lambda n: int(re.search(r"(\d+)", n.rsplit("/", 1)[1]).group(1)))
        out = []
        for i, n in enumerate(slides, 1):
            out.append(f"--- slide {i} ---\n" + xml_text(z.read(n).decode("utf8", "ignore")).strip())
            notes = n.replace("slides/slide", "notesSlides/notesSlide")
            if notes in z.namelist():
                out.append("[notes] " + xml_text(z.read(notes).decode("utf8", "ignore")).strip())
        return "\n".join(out)


def xlsx(path):
    with zipfile.ZipFile(path) as z:
        strings = []
        if "xl/sharedStrings.xml" in z.namelist():
            xml = z.read("xl/sharedStrings.xml").decode("utf8", "ignore")
            strings = [html.unescape(re.sub(r"<[^>]+>", "", si)) for si in re.findall(r"<si>(.*?)</si>", xml, re.S)]
        inline = []
        for n in z.namelist():
            if n.startswith("xl/worksheets/sheet"):
                inline += [html.unescape(t) for t in re.findall(r"<t[^>]*>([^<]*)</t>", z.read(n).decode("utf8", "ignore"))]
        return "\n".join(strings + inline)


def odf(path):
    with zipfile.ZipFile(path) as z:
        return xml_text(z.read("content.xml").decode("utf8", "ignore"))


def htmldoc(path):
    text = path.read_text(errors="replace")
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", text, flags=re.S | re.I)
    text = re.sub(r"</(p|div|h\d|li|tr|br)>", "\n", text, flags=re.I)
    return html.unescape(re.sub(r"<[^>]+>", "", text))


def pdf(path):
    if shutil.which("pdftotext"):
        done = subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True, text=True)
        if done.returncode == 0:
            return done.stdout
    return None


def rtf(path):
    text = path.read_text(errors="replace")
    text = re.sub(r"\\par[d]?", "\n", text)
    return re.sub(r"\\[a-z]+-?\d* ?|[{}]", "", text)


READERS = {".docx": docx, ".pptx": pptx, ".xlsx": xlsx, ".odt": odf, ".odp": odf, ".html": htmldoc, ".htm": htmldoc,
           ".pdf": pdf, ".rtf": rtf}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--out")
    ap.add_argument("--max-chars", type=int, default=60000)
    args = ap.parse_args()
    out = Path(args.out) if args.out else None
    if out:
        out.mkdir(parents=True, exist_ok=True)
    for raw in args.files:
        path = Path(raw)
        reader = READERS.get(path.suffix.lower())
        try:
            text = reader(path) if reader else path.read_text(errors="replace")
        except (zipfile.BadZipFile, KeyError, OSError) as exc:
            print(f"! {path}: {exc}", file=sys.stderr)
            continue
        if text is None:
            print(f"! {path}: PDF — lire le fichier directement (pdftotext absent)", file=sys.stderr)
            continue
        text = re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t]+", " ", text)).strip()
        clipped = len(text) > args.max_chars
        text = text[: args.max_chars] + ("\n[…coupé]" if clipped else "")
        if out:
            target = out / (path.stem + ".txt")
            target.write_text(text + "\n")
            print(f"{path} → {target} ({len(text)} caractères{', coupé' if clipped else ''})")
        else:
            print(f"===== {path} =====\n{text}\n")


if __name__ == "__main__":
    sys.exit(main())
