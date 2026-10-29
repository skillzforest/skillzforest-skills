#!/usr/bin/env python3
"""Turn a Google Slides deck into a branded one: background, title and body colors, font, accent bar, footer.

Usage:
    python3 brand_deck.py presentation.json [--brand ../references/brand.json] > requests.json

presentation.json is the answer of GOOGLESLIDES_PRESENTATIONS_GET (or the Slides API presentations.get) with at least
`pageSize` and `slides(objectId,pageElements(objectId,size,transform,shape(shapeType,placeholder,text)))`.
The output is the `requests` list to send to GOOGLESLIDES_PRESENTATIONS_BATCH_UPDATE (presentations.batchUpdate).

The first slide gets the "cover" style, the last one the "closing" style, the others "content". On each slide, the
title is the TITLE / CENTERED_TITLE placeholder, or else the first shape holding text. Standard library only.
"""

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_BRAND = os.path.join(HERE, "..", "references", "brand.json")
EMU_PER_PT = 12700


def rgb(hex_color):
    value = hex_color.lstrip("#")
    return {"red": int(value[0:2], 16) / 255, "green": int(value[2:4], 16) / 255, "blue": int(value[4:6], 16) / 255}


def has_text(element):
    text = element.get("shape", {}).get("text", {})
    return any("textRun" in part and part["textRun"].get("content", "").strip() for part in text.get("textElements", []))


def main():
    parser = argparse.ArgumentParser(description="Branding requests for a Google Slides deck.")
    parser.add_argument("presentation", help="presentations.get JSON (file path, or - for stdin)")
    parser.add_argument("--brand", default=DEFAULT_BRAND, help="brand JSON (default: references/brand.json)")
    args = parser.parse_args()

    with (sys.stdin if args.presentation == "-" else open(args.presentation, encoding="utf-8")) as handle:
        deck = json.load(handle)
    deck = deck.get("data", deck)  # accept a raw Composio response too
    with open(args.brand, encoding="utf-8") as handle:
        brand = json.load(handle)
    colors = brand["colors"]

    width = deck.get("pageSize", {}).get("width", {}).get("magnitude", 9144000)
    height = deck.get("pageSize", {}).get("height", {}).get("magnitude", 5143500)
    slides = deck.get("slides", [])
    requests = []

    for index, slide in enumerate(slides):
        kind = "cover" if index == 0 else "closing" if index == len(slides) - 1 and len(slides) > 2 else "content"
        style = brand["slides"][kind]
        page = slide["objectId"]

        requests.append({
            "updatePageProperties": {
                "objectId": page,
                "pageProperties": {"pageBackgroundFill": {"solidFill": {"color": {"rgbColor": rgb(colors[style["background"]])}}}},
                "fields": "pageBackgroundFill.solidFill.color",
            }
        })

        texts = [e for e in slide.get("pageElements", []) if "shape" in e and has_text(e)]
        title = next((e for e in texts if e["shape"].get("placeholder", {}).get("type") in ("TITLE", "CENTERED_TITLE")), None)
        title = title or (texts[0] if texts else None)
        for element in texts:
            is_title = element is title
            requests.append({
                "updateTextStyle": {
                    "objectId": element["objectId"],
                    "textRange": {"type": "ALL"},
                    "style": {
                        "fontFamily": brand["font"],
                        "foregroundColor": {"opaqueColor": {"rgbColor": rgb(colors[style["title" if is_title else "body"]])}},
                        "bold": True if is_title else None,
                    },
                    "fields": "fontFamily,foregroundColor" + (",bold" if is_title else ""),
                }
            })
            # Shapes drawn by the markdown importer may have their own fill: make it transparent.
            requests.append({
                "updateShapeProperties": {
                    "objectId": element["objectId"],
                    "shapeProperties": {"shapeBackgroundFill": {"propertyState": "NOT_RENDERED"}},
                    "fields": "shapeBackgroundFill.propertyState",
                }
            })

        # Accent bar: a short capability-green rule at the top left, as on the brand's cards.
        bar = f"{page}_sf_bar"
        requests.append({
            "createShape": {
                "objectId": bar,
                "shapeType": "RECTANGLE",
                "elementProperties": {
                    "pageObjectId": page,
                    "size": {"width": {"magnitude": 72 * EMU_PER_PT, "unit": "EMU"}, "height": {"magnitude": 6 * EMU_PER_PT, "unit": "EMU"}},
                    "transform": {"scaleX": 1, "scaleY": 1, "translateX": 36 * EMU_PER_PT, "translateY": 24 * EMU_PER_PT, "unit": "EMU"},
                },
            }
        })
        requests.append({
            "updateShapeProperties": {
                "objectId": bar,
                "shapeProperties": {
                    "shapeBackgroundFill": {"solidFill": {"color": {"rgbColor": rgb(colors[style["accent"]])}}},
                    "outline": {"propertyState": "NOT_RENDERED"},
                },
                "fields": "shapeBackgroundFill.solidFill.color,outline.propertyState",
            }
        })

        # Footer: brand name and page number, small, bottom left.
        footer = f"{page}_sf_footer"
        requests.append({
            "createShape": {
                "objectId": footer,
                "shapeType": "TEXT_BOX",
                "elementProperties": {
                    "pageObjectId": page,
                    "size": {"width": {"magnitude": width - 72 * EMU_PER_PT, "unit": "EMU"}, "height": {"magnitude": 20 * EMU_PER_PT, "unit": "EMU"}},
                    "transform": {"scaleX": 1, "scaleY": 1, "translateX": 36 * EMU_PER_PT, "translateY": height - 30 * EMU_PER_PT, "unit": "EMU"},
                },
            }
        })
        requests.append({"insertText": {"objectId": footer, "text": f"{brand['footer']}   {index + 1}/{len(slides)}"}})
        requests.append({
            "updateTextStyle": {
                "objectId": footer,
                "textRange": {"type": "ALL"},
                "style": {
                    "fontFamily": brand["font"],
                    "fontSize": {"magnitude": 9, "unit": "PT"},
                    "foregroundColor": {"opaqueColor": {"rgbColor": rgb(colors[style["body"]])}},
                },
                "fields": "fontFamily,fontSize,foregroundColor",
            }
        })

    # Drop the null "bold" left on body text so the API does not reject the field mask.
    for request in requests:
        style = request.get("updateTextStyle", {}).get("style")
        if style and style.get("bold") is None:
            style.pop("bold", None)

    json.dump(requests, sys.stdout, ensure_ascii=False)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
