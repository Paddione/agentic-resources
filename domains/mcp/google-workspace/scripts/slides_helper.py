#!/usr/bin/env python3
"""Helpers for the Google Slides connector (read_presentation / update_presentation).

Slides positions everything in EMU (914400 per inch), and an element's rendered
size is its `size` times its transform scale; a table's size comes from its
column widths and row heights instead. These commands handle that math.

Usage:
  slides_helper.py outline DECK.json
      One block per slide: object IDs, layout, each element's type, real
      position and size in inches, font size, and a text preview. Flags
      elements that run off the page, overlap another element, look too
      small for their text, or are empty placeholders.

  slides_helper.py build SPEC.json [--page 10x5.625] [--revision ID]
      Print update_presentation arguments (requests + writeControl) from an
      inch-based spec. See BUILD SPEC below. Warns on stderr about text that
      probably won't fit its box, text boxes and shapes under 14 pt outside a
      footer line, typed bullet marks, and elements that leave the page.

DECK.json is read_presentation output: the raw JSON, or a result the app saved to
disk, either the {"content": "<json string>"} wrapper or a list of content blocks,
[{"type": "text", "text": "<json string>"}]. A masked read is enough; see the skill
for the mask.

BUILD SPEC (JSON):
  {"slides": [
    {"id": "s4_slide",                 new slide ID (5-50 letters, digits, _, - or :; unique); omit "layout"
     "layout": "BLANK",                and set "existing": true to add to a slide
     "index": 3,                       optional insertion position (0-based)
     "elements": [
       {"id": "s4_title", "type": "text", "x": 0.5, "y": 0.4, "w": 9, "h": 0.8,
        "text": "Revenue grew 42%", "size": 32, "bold": true,
        "color": "#1F2937", "font": "Arial", "align": "START"},
       {"id": "s4_bar", "type": "rect", "x": 0.5, "y": 1.4, "w": 3, "h": 2,
        "fill": "#E8EEF7", "text": "optional label", "size": 14},
       {"id": "s4_table", "type": "table", "x": 0.5, "y": 1.4, "w": 9,
        "rows": [["Metric", "Q1"], ["ARR", "$4.2M"]], "header": true, "size": 14,
        "col_widths": [6, 3], "col_align": ["START", "END"]}
     ]}
  ]}
Types: text (TEXT_BOX), rect (RECTANGLE), round_rect (ROUND_RECTANGLE), ellipse, table.
Text keys: "bullets": true (one bullet per line; leave out typed "- "), "space_below": points
after each paragraph. Table keys: "col_widths" (inches, one per column), "col_align",
"header": true (bold first row), "header_fill" and "header_color" (first-row fill color and text color, as hex).
"""
import argparse
import json
import re
import sys
from pathlib import Path as _Path

sys.path.insert(0, str(_Path(__file__).resolve().parent))
from slides_format import (  # noqa: E402
    ALIGN_NAMES,
    AVG_CHAR_EM,
    AVG_CHAR_EM_BOLD,
    BOX_PADDING_IN,
    BULLET_INDENT_IN,
    EMU,
    FOOTER_BAND_IN,
    LINE_HEIGHT,
    MIN_BODY_PT,
    SHAPES,
    alignment,
    emu,
    estimate_lines,
    geometry,
    kind_of,
    load_json,
    load_spec,
    mag,
    needed_height_in,
    overlaps,
    props,
    read_json_file,
    rgb,
    text_of,
    text_style,
    unwrap,
)


def cmd_outline(args):
    deck = load_json(args.deck)
    pw = mag(deck.get("pageSize", {}).get("width")) / EMU or 10.0
    ph = mag(deck.get("pageSize", {}).get("height")) / EMU or 5.625
    layouts = {l["objectId"]: l.get("layoutProperties", {}).get("name") for l in deck.get("layouts", [])}
    print(f"revisionId: {deck.get('revisionId')}  page: {pw:.2f} x {ph:.2f} in  slides: {len(deck.get('slides', []))}")
    for n, slide in enumerate(deck.get("slides", [])):
        lid = slide.get("slideProperties", {}).get("layoutObjectId")
        print(f"\n[{n}] slide {slide['objectId']}  layout {layouts.get(lid, lid)}")
        boxes = []
        for el in slide.get("pageElements", []):
            k = kind_of(el)
            x, y, w, h = geometry(el)
            flags = []
            detail = ""
            if k == "shape":
                sh = el["shape"]
                ph_type = sh.get("placeholder", {}).get("type")
                text, size = text_of(sh.get("text"))
                label = sh.get("shapeType", "")
                if ph_type:
                    label += f" placeholder={ph_type}"
                    if not text.strip():
                        flags.append("EMPTY PLACEHOLDER (shows prompt text in the editor; fill or delete)")
                preview = text.strip().replace("\n", " / ")
                if len(preview) > 60:
                    preview = preview[:57] + "..."
                size_txt = f"{size:g}pt" if size else "inherited size"
                detail = f"{label} {size_txt} {preview!r}"
                if text.strip() and size and needed_height_in(text, w, size) > h + 0.05:
                    flags.append(f"TEXT MAY OVERFLOW (needs ~{needed_height_in(text, w, size):.2f} in)")
            elif k == "table":
                tb = el["table"]
                cells = []
                for row in tb.get("tableRows", []):
                    cells.append([text_of(c.get("text"))[0].strip() for c in row.get("tableCells", [])])
                detail = f"{tb.get('rows')}x{tb.get('columns')} first row {cells[0] if cells else []}"
            elif k == "sheetsChart":
                detail = f"chart {el['sheetsChart'].get('chartId')} from {el['sheetsChart'].get('spreadsheetId')}"
            if x < -0.01 or y < -0.01 or x + w > pw + 0.01 or y + h > ph + 0.01:
                flags.append("OFF PAGE")
            for other_id, other_box in boxes:
                if overlaps((x, y, w, h), other_box):
                    flags.append(f"OVERLAPS {other_id}")
            boxes.append((el["objectId"], (x, y, w, h)))
            flag_txt = ("  !! " + "; ".join(flags)) if flags else ""
            print(f"  {el['objectId']:<16} {k:<11} x={x:.2f} y={y:.2f} w={w:.2f} h={h:.2f}  {detail}{flag_txt}")


SHAPES = {"text": "TEXT_BOX", "rect": "RECTANGLE", "round_rect": "ROUND_RECTANGLE", "ellipse": "ELLIPSE"}


def rgb(h):
    h = h.lstrip("#")
    return {"red": int(h[0:2], 16) / 255, "green": int(h[2:4], 16) / 255, "blue": int(h[4:6], 16) / 255}


def emu(inches):
    return int(round(inches * EMU))


def props(page_id, x, y, w, h):
    return {"pageObjectId": page_id,
            "size": {"width": {"magnitude": emu(w), "unit": "EMU"},
                     "height": {"magnitude": emu(h), "unit": "EMU"}},
            "transform": {"scaleX": 1, "scaleY": 1, "translateX": emu(x), "translateY": emu(y), "unit": "EMU"}}


def text_style(el, target):
    style, fields = {}, []
    if "size" in el:
        style["fontSize"] = {"magnitude": el["size"], "unit": "PT"}
        fields.append("fontSize")
    if "bold" in el:
        style["bold"] = el["bold"]
        fields.append("bold")
    if "italic" in el:
        style["italic"] = el["italic"]
        fields.append("italic")
    if "color" in el:
        style["foregroundColor"] = {"opaqueColor": {"rgbColor": rgb(el["color"])}}
        fields.append("foregroundColor")
    if "font" in el:
        style["fontFamily"] = el["font"]
        fields.append("fontFamily")
    if not fields:
        return None
    return {"updateTextStyle": {**target, "textRange": {"type": "ALL"}, "style": style, "fields": ",".join(fields)}}


def alignment(value, oid, key):
    """Slides' alignment value for a spec's align or col_align entry; LEFT and RIGHT are accepted."""
    a = str(value).upper()
    a = ALIGN_NAMES.get(a, a)
    if a not in ("START", "CENTER", "END", "JUSTIFIED"):
        sys.exit(f"{oid}: {key} value {value!r} must be START, CENTER, END or JUSTIFIED")
    return a


def cmd_build(args):
    spec = load_spec(args.spec, "BUILD SPEC")
    unknown = sorted(set(spec) - {"slides"})
    if unknown:
        print(f"WARNING: ignored top-level key(s) that BUILD SPEC does not define: {', '.join(unknown)}; see 'slides_helper.py --help'",
              file=sys.stderr)
    try:
        pw, ph = (float(v) for v in args.page.lower().split("x"))
    except ValueError:
        sys.exit("--page takes the page width and height in inches, such as 10x5.625")
    reqs, seen, warnings = [], set(), []

    def check_id(oid):
        if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_:-]{4,49}", oid):
            sys.exit(f"object ID {oid!r} must be 5 to 50 characters: letters, digits, _, - or :, "
                     "starting with a letter, digit or _")
        if oid in seen:
            sys.exit(f"object ID {oid!r} is used twice")
        seen.add(oid)

    for s in spec.get("slides", []):
        sid = s["id"]
        if not s.get("existing"):
            check_id(sid)
            cs = {"objectId": sid, "slideLayoutReference": {"predefinedLayout": s.get("layout", "BLANK")}}
            if "index" in s:
                cs["insertionIndex"] = s["index"]
            reqs.append({"createSlide": cs})
        for el in s.get("elements", []):
            oid = el["id"]
            check_id(oid)
            x, y, w = el["x"], el["y"], el["w"]
            if el["type"] == "table":
                rows = el["rows"]
                nrows, ncols = len(rows), max(len(r) for r in rows)
                size = el.get("size", 12)
                row_h = el.get("row_h", size * LINE_HEIGHT / 72 + 0.2)
                h = el.get("h", row_h * nrows)
                widths = el.get("col_widths") or [w / ncols] * ncols
                if len(widths) != ncols:
                    sys.exit(f"{oid}: col_widths gives {len(widths)} width{'s' if len(widths) != 1 else ''} for a table with "
                             f"{ncols} columns; give one per column")
                if el.get("col_align") and len(el["col_align"]) != ncols:
                    n_align = len(el["col_align"])
                    sys.exit(f"{oid}: col_align gives {n_align} value{'s' if n_align != 1 else ''} for a table with "
                             f"{ncols} columns; give one per column")
                col_align = [alignment(a, oid, "col_align") if a else None
                             for a in (el.get("col_align") or [None] * ncols)]
                reqs.append({"createTable": {"objectId": oid, "elementProperties": props(sid, x, y, w, h),
                                             "rows": nrows, "columns": ncols}})
                if el.get("col_widths"):
                    for c, cw_in in enumerate(widths):
                        reqs.append({"updateTableColumnProperties": {"objectId": oid, "columnIndices": [c],
                            "tableColumnProperties": {"columnWidth": {"magnitude": emu(cw_in), "unit": "EMU"}},
                            "fields": "columnWidth"}})
                    if abs(sum(widths) - w) > 0.01:
                        warnings.append(f"{oid}: col_widths add up to {sum(widths):.2f} in, but the table's w is "
                                        f"{w:.2f} in; the table will be {sum(widths):.2f} in wide")
                for r, row in enumerate(rows):
                    for c, val in enumerate(row):
                        if val == "" or val is None:
                            continue
                        loc = {"rowIndex": r, "columnIndex": c}
                        reqs.append({"insertText": {"objectId": oid, "cellLocation": loc, "text": str(val)}})
                        cell_el = {**el, "bold": bool(el.get("header")) and r == 0}
                        if r == 0 and el.get("header_color"):
                            cell_el["color"] = el["header_color"]
                        st = text_style(cell_el, {"objectId": oid, "cellLocation": loc})
                        if st:
                            reqs.append(st)
                        align = col_align[c]
                        if align:
                            reqs.append({"updateParagraphStyle": {"objectId": oid, "cellLocation": loc,
                                                                  "textRange": {"type": "ALL"},
                                                                  "style": {"alignment": align},
                                                                  "fields": "alignment"}})
                        cw = widths[c]
                        if needed_height_in(str(val), cw, size, cell_el["bold"]) > row_h + 0.05:
                            warnings.append(f"{oid} cell ({r},{c}) text may wrap past the row height; the row will grow")
                if el.get("header_fill"):
                    reqs.append({"updateTableCellProperties": {
                        "objectId": oid,
                        "tableRange": {"location": {"rowIndex": 0, "columnIndex": 0}, "rowSpan": 1, "columnSpan": ncols},
                        "tableCellProperties": {"tableCellBackgroundFill": {"solidFill": {"color": {"rgbColor": rgb(el["header_fill"])}}}},
                        "fields": "tableCellBackgroundFill.solidFill.color"}})
            else:
                h = el["h"]
                shape = SHAPES.get(el["type"])
                if not shape:
                    sys.exit(f"unknown element type {el['type']!r}")
                reqs.append({"createShape": {"objectId": oid, "shapeType": shape, "elementProperties": props(sid, x, y, w, h)}})
                if "fill" in el:
                    reqs.append({"updateShapeProperties": {"objectId": oid, "shapeProperties": {
                        "shapeBackgroundFill": {"solidFill": {"color": {"rgbColor": rgb(el["fill"])}}},
                        "outline": {"propertyState": "NOT_RENDERED"}},
                        "fields": "shapeBackgroundFill.solidFill.color,outline.propertyState"}})
                footer = h <= 0.5 and y + h >= ph - FOOTER_BAND_IN
                if el.get("text"):
                    typed = re.compile(r"(•|- |\* |– )")
                    if not footer and any(typed.match(line.lstrip()) for line in el["text"].split("\n")):
                        if el.get("bullets"):
                            warnings.append(f"{oid}: lines start with typed bullet marks (•, -, –, *); \"bullets\": true "
                                            "adds its own, so remove them")
                        else:
                            warnings.append(f"{oid}: lines start with typed bullet marks (•, -, –, *); remove them "
                                            "and set \"bullets\": true")
                    reqs.append({"insertText": {"objectId": oid, "text": el["text"]}})
                    st = text_style(el, {"objectId": oid})
                    if st:
                        reqs.append(st)
                    para = {}
                    if "align" in el:
                        para["alignment"] = alignment(el["align"], oid, "align")
                    if "space_below" in el:
                        para["spaceBelow"] = {"magnitude": el["space_below"], "unit": "PT"}
                    if para:
                        reqs.append({"updateParagraphStyle": {"objectId": oid, "textRange": {"type": "ALL"},
                                                              "style": para, "fields": ",".join(para)}})
                    if el.get("bullets"):
                        reqs.append({"createParagraphBullets": {"objectId": oid, "textRange": {"type": "ALL"},
                                                                "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE"}})
                    size = el.get("size", 14)
                    text_w = w - (BULLET_INDENT_IN if el.get("bullets") else 0)
                    if size < MIN_BODY_PT and not footer:
                        warnings.append(f"{oid}: {size} pt is below the {MIN_BODY_PT} pt minimum for slide text; "
                                        "use a larger size, or make it a footer line: at most 0.5 in tall, ending "
                                        f"within {FOOTER_BAND_IN} in of the bottom of the slide")
                    need = needed_height_in(el["text"], text_w, size, el.get("bold", False), el.get("space_below", 0))
                    if need > h + 0.05:
                        warnings.append(f"{oid}: text likely needs ~{need:.2f} in of height, box is {h:.2f} in; "
                                        "Slides will not shrink it")
            if x < 0 or y < 0 or x + w > pw + 0.001 or y + h > ph + 0.001:
                warnings.append(f"{oid}: box ({x}, {y}, {w} x {h:.2f}) leaves the {pw} x {ph} in page")
    if not reqs:
        sys.exit(f"{args.spec} produced no requests; see BUILD SPEC in 'slides_helper.py --help'")
    out = {"requests": reqs}
    if args.revision:
        out["writeControl"] = {"requiredRevisionId": args.revision}
    print(json.dumps(out))
    for w_ in warnings:
        print("WARNING: " + w_, file=sys.stderr)


def main():
    import signal
    if hasattr(signal, "SIGPIPE"):  # Windows has no SIGPIPE
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    if hasattr(sys.stdout, "reconfigure"):  # print UTF-8 even where the console default isn't
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("outline")
    p.add_argument("deck")
    p.set_defaults(func=cmd_outline)
    p = sub.add_parser("build")
    p.add_argument("spec")
    p.add_argument("--page", default="10x5.625")
    p.add_argument("--revision")
    p.set_defaults(func=cmd_build)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
