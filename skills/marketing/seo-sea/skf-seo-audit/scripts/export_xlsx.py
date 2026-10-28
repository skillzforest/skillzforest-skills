#!/usr/bin/env python3
"""Write an SEO audit as an Excel workbook (.xlsx), readable in Excel, Numbers, LibreOffice and Google Sheets.

Usage:
    python3 export_xlsx.py --crawl crawl.json [--actions actions.json] [--pagespeed pagespeed.json]
                           [--summary summary.json] --out audit.xlsx

- crawl.json: output of crawl.py (pages and findings).
- actions.json: the prioritized actions the agent wrote, a list of objects with the keys
  priority, who, action, page, problem, why, fix, check (any missing key is left empty).
- pagespeed.json: the JSON list printed by pagespeed.py (optional).
- summary.json: {"site", "date", "language", "lines": ["…", "…"]} for the first sheet (optional).

Sheets: Summary, Actions, Pages, Findings, Speed (when given). Header rows are frozen, filterable and colored
(SkillzForest palette). Standard library only: the file is assembled as Office Open XML by hand.
"""

import argparse
import datetime
import json
import sys
import zipfile
from xml.sax.saxutils import escape

INK = "FF192E3A"
TEAL = "FF236A62"
MIST = "FFDCE4E6"
PRIORITY_FILL = {"P1": "FFFBEBEB", "P2": "FFF9EEDA", "P3": "FFE7F1FB"}


def col_name(index):
    """0 -> A, 25 -> Z, 26 -> AA."""
    name = ""
    index += 1
    while index:
        index, rest = divmod(index - 1, 26)
        name = chr(65 + rest) + name
    return name


class Sheet:
    def __init__(self, title, headers, widths):
        self.title = title[:31]
        self.headers = headers
        self.widths = widths
        self.rows = []

    def add(self, values, style=0):
        self.rows.append((values, style))

    def xml(self):
        out = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
               '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">']
        if self.headers:
            out.append('<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" '
                       'activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>')
        out.append("<cols>" + "".join(
            f'<col min="{i + 1}" max="{i + 1}" width="{w}" customWidth="1"/>' for i, w in enumerate(self.widths)
        ) + "</cols><sheetData>")
        all_rows = ([(self.headers, 1)] if self.headers else []) + self.rows
        for r, (values, style) in enumerate(all_rows, start=1):
            cells = []
            for c, value in enumerate(values):
                ref = f"{col_name(c)}{r}"
                if value is None or value == "":
                    continue
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    cells.append(f'<c r="{ref}" s="{style}"><v>{value}</v></c>')
                else:
                    text = escape(str(value)).replace("\n", "&#10;")
                    cells.append(f'<c r="{ref}" s="{style}" t="inlineStr"><is><t xml:space="preserve">{text}</t></is></c>')
            out.append(f'<row r="{r}">{"".join(cells)}</row>')
        out.append("</sheetData>")
        if self.headers and self.rows:
            out.append(f'<autoFilter ref="A1:{col_name(len(self.headers) - 1)}{len(self.rows) + 1}"/>')
        out.append("</worksheet>")
        return "\n".join(out)


STYLES = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<fonts count="4">
  <font><sz val="11"/><color rgb="{INK}"/><name val="Calibri"/></font>
  <font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font>
  <font><b/><sz val="16"/><color rgb="{TEAL}"/><name val="Calibri"/></font>
  <font><b/><sz val="11"/><color rgb="{INK}"/><name val="Calibri"/></font>
</fonts>
<fills count="6">
  <fill><patternFill patternType="none"/></fill>
  <fill><patternFill patternType="gray125"/></fill>
  <fill><patternFill patternType="solid"><fgColor rgb="{TEAL}"/></patternFill></fill>
  <fill><patternFill patternType="solid"><fgColor rgb="{PRIORITY_FILL['P1']}"/></patternFill></fill>
  <fill><patternFill patternType="solid"><fgColor rgb="{PRIORITY_FILL['P2']}"/></patternFill></fill>
  <fill><patternFill patternType="solid"><fgColor rgb="{PRIORITY_FILL['P3']}"/></patternFill></fill>
</fills>
<borders count="2">
  <border/>
  <border><bottom style="thin"><color rgb="{MIST}"/></bottom></border>
</borders>
<cellStyleXfs count="1"><xf/></cellStyleXfs>
<cellXfs count="7">
  <xf fontId="0" fillId="0" borderId="1" applyBorder="1"><alignment vertical="top" wrapText="1"/></xf>
  <xf fontId="1" fillId="2" borderId="0" applyFont="1" applyFill="1"><alignment vertical="center" wrapText="1"/></xf>
  <xf fontId="2" fillId="0" borderId="0" applyFont="1"/>
  <xf fontId="0" fillId="3" borderId="1" applyFill="1"><alignment vertical="top" wrapText="1"/></xf>
  <xf fontId="0" fillId="4" borderId="1" applyFill="1"><alignment vertical="top" wrapText="1"/></xf>
  <xf fontId="0" fillId="5" borderId="1" applyFill="1"><alignment vertical="top" wrapText="1"/></xf>
  <xf fontId="3" fillId="0" borderId="0" applyFont="1"><alignment vertical="top" wrapText="1"/></xf>
</cellXfs>
<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>"""

PRIORITY_STYLE = {"P1": 3, "P2": 4, "P3": 5}

LABELS = {
    "fr": {
        "summary": "Synthèse", "actions": "Actions", "pages": "Pages", "findings": "Constats", "speed": "Vitesse",
        "title": "Audit SEO", "date": "Date", "pagesCrawled": "Pages explorées", "findingsCount": "Constats",
        "actionHeaders": ["Priorité", "Qui", "Action", "Page", "Problème", "Pourquoi", "Que faire", "Comment vérifier"],
        "pageHeaders": ["URL", "Statut", "Langue", "Title", "Longueur title", "Meta description", "Longueur description",
                        "H1", "Canonical", "Hreflang", "Images sans alt", "JSON-LD", "Poids HTML (Ko)"],
        "findingHeaders": ["Gravité", "Règle", "Page", "Détail"],
        "speedHeaders": ["URL", "Stratégie", "Performance", "SEO", "LCP", "CLS", "TBT", "LCP réel (ms)", "INP réel (ms)"],
    },
    "en": {
        "summary": "Summary", "actions": "Actions", "pages": "Pages", "findings": "Findings", "speed": "Speed",
        "title": "SEO audit", "date": "Date", "pagesCrawled": "Pages crawled", "findingsCount": "Findings",
        "actionHeaders": ["Priority", "Who", "Action", "Page", "Problem", "Why", "What to do", "How to check"],
        "pageHeaders": ["URL", "Status", "Language", "Title", "Title length", "Meta description", "Description length",
                        "H1", "Canonical", "Hreflang", "Images without alt", "JSON-LD", "HTML weight (KB)"],
        "findingHeaders": ["Severity", "Rule", "Page", "Detail"],
        "speedHeaders": ["URL", "Strategy", "Performance", "SEO", "LCP", "CLS", "TBT", "Field LCP (ms)", "Field INP (ms)"],
    },
}


def build(args):
    with open(args.crawl, encoding="utf-8") as handle:
        crawl = json.load(handle)
    actions = json.load(open(args.actions, encoding="utf-8")) if args.actions else []
    speed = json.load(open(args.pagespeed, encoding="utf-8")) if args.pagespeed else []
    summary = json.load(open(args.summary, encoding="utf-8")) if args.summary else {}
    lang = summary.get("language", "fr")
    L = LABELS.get(lang, LABELS["en"])

    sheets = []

    s = Sheet(L["summary"], None, [28, 110])
    s.add([f"{L['title']} — {summary.get('site', crawl.get('site', ''))}"], 2)
    s.add([L["date"], summary.get("date", datetime.date.today().isoformat())], 6)
    s.add([L["pagesCrawled"], crawl.get("crawled", len(crawl.get("pages", [])))], 6)
    s.add([L["findingsCount"], len(crawl.get("findings", []))], 6)
    s.add([L["actions"], len(actions)], 6)
    s.add([""])
    for line in summary.get("lines", []):
        s.add(["", line])
    sheets.append(s)

    s = Sheet(L["actions"], L["actionHeaders"], [9, 10, 40, 38, 48, 40, 52, 40])
    order = {"P1": 0, "P2": 1, "P3": 2}
    for a in sorted(actions, key=lambda a: order.get(a.get("priority"), 9)):
        s.add([a.get("priority"), a.get("who"), a.get("action"), a.get("page"), a.get("problem"), a.get("why"),
               a.get("fix"), a.get("check")], PRIORITY_STYLE.get(a.get("priority"), 0))
    sheets.append(s)

    s = Sheet(L["pages"], L["pageHeaders"], [55, 8, 9, 50, 9, 60, 9, 40, 45, 30, 9, 9, 10])
    for p in crawl.get("pages", []):
        title, desc = p.get("title") or "", p.get("description") or ""
        s.add([p.get("final") or p.get("url"), p.get("status"), p.get("lang"), title, len(title) if title else None,
               desc, len(desc) if desc else None, " | ".join(p.get("h1") or []), p.get("canonical"),
               ", ".join(sorted((p.get("hreflang") or {}).keys())), p.get("imagesWithoutAlt"), p.get("jsonld"),
               round(p.get("bytes", 0) / 1024) if p.get("bytes") else None])
    sheets.append(s)

    s = Sheet(L["findings"], L["findingHeaders"], [10, 26, 60, 80])
    rank = {"high": 0, "medium": 1, "low": 2, "info": 3}
    for f in sorted(crawl.get("findings", []), key=lambda f: rank.get(f["severity"], 9)):
        s.add([f["severity"], f["rule"], f["page"], f.get("detail")])
    sheets.append(s)

    if speed:
        s = Sheet(L["speed"], L["speedHeaders"], [55, 10, 12, 8, 10, 10, 10, 14, 14])
        for row in speed:
            field = row.get("field") or {}
            s.add([row["url"], row.get("strategy"), row.get("performance"), row.get("seo"), row["lab"].get("LCP"),
                   row["lab"].get("CLS"), row["lab"].get("TBT"), field.get("LCP_ms"), field.get("INP_ms")])
        sheets.append(s)

    with zipfile.ZipFile(args.out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                   '<Default Extension="xml" ContentType="application/xml"/>'
                   '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                   '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
                   + "".join(f'<Override PartName="/xl/worksheets/sheet{i + 1}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' for i in range(len(sheets)))
                   + "</Types>")
        z.writestr("_rels/.rels",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
                   "</Relationships>")
        z.writestr("xl/workbook.xml",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                   'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'
                   + "".join(f'<sheet name="{escape(sh.title)}" sheetId="{i + 1}" r:id="rId{i + 1}"/>' for i, sh in enumerate(sheets))
                   + "</sheets>"
                   + (f'<definedNames>' + "".join(
                       f'<definedName name="_xlnm._FilterDatabase" localSheetId="{i}" hidden="1">\'{escape(sh.title)}\'!$A$1:${col_name(len(sh.headers) - 1)}${len(sh.rows) + 1}</definedName>'
                       for i, sh in enumerate(sheets) if sh.headers and sh.rows) + "</definedNames>")
                   + "</workbook>")
        z.writestr("xl/_rels/workbook.xml.rels",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   + "".join(f'<Relationship Id="rId{i + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i + 1}.xml"/>' for i in range(len(sheets)))
                   + f'<Relationship Id="rId{len(sheets) + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
                   "</Relationships>")
        z.writestr("xl/styles.xml", STYLES)
        for i, sh in enumerate(sheets):
            z.writestr(f"xl/worksheets/sheet{i + 1}.xml", sh.xml())
    return sheets


def main():
    parser = argparse.ArgumentParser(description="SEO audit as an Excel workbook.")
    parser.add_argument("--crawl", required=True)
    parser.add_argument("--actions")
    parser.add_argument("--pagespeed")
    parser.add_argument("--summary")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    sheets = build(args)
    print(f"{args.out}: " + ", ".join(f"{sh.title} ({len(sh.rows)} rows)" for sh in sheets))
    return 0


if __name__ == "__main__":
    sys.exit(main())
