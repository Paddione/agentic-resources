#!/usr/bin/env python3
"""Shared format helpers for the Google Slides connector scripts.

Pure, UI-free math extracted verbatim from ``slides_helper.py`` so both the
``outline`` and ``build`` commands (and future format scripts) share one
implementation: EMU/inch conversion, shape/text geometry, text-fit estimates,
overlap detection, style/alignment mapping, and saved-result JSON loading.

``slides_helper.py`` re-exports these names, so existing imports keep working.
Run ``python3 slides_format.py --self-test`` for the built-in property tests
(stdlib only, deterministic seed).
"""
import json
import re
import sys

EMU = 914400
AVG_CHAR_EM = 0.47      # average glyph width as a fraction of the font size (0.44-0.47 on paragraphs)
AVG_CHAR_EM_BOLD = 0.52 # bold is wider: 0.48-0.53 on titles, measured in a local Arial-metric font,
                        # not in Slides' own rendering; titles are usually bold
BULLET_INDENT_IN = 0.5  # width a bullet and its indent take from each line (not measured)
MIN_BODY_PT = 14        # smallest slide text outside a footer line (this skill's Design rule)
FOOTER_BAND_IN = 0.8    # a footer or source line sits in this band at the bottom of the slide
                        # (this skill's own convention, not a Google rule)
LINE_HEIGHT = 1.2       # line height as a multiple of the font size
ALIGN_NAMES = {"LEFT": "START", "RIGHT": "END"}  # familiar names for Slides' alignment values
BOX_PADDING_IN = 0.1    # default inner padding on each side of a text box
SHAPES = {"text": "TEXT_BOX", "rect": "RECTANGLE", "round_rect": "ROUND_RECTANGLE", "ellipse": "ELLIPSE"}


def unwrap(data):
    """Return the API JSON inside a saved tool result, however many wrappers it has.

    Accepts the raw API JSON, the {"content": "<json string>"} wrapper some apps save,
    and the list of content blocks others save, [{"type": "text", "text": "<json string>"}],
    whose text can itself be the {"content": ...} wrapper. Non-text blocks are ignored.
    """
    while True:
        if isinstance(data, dict) and isinstance(data.get("content"), (str, list)):
            # No Docs, Sheets or Slides resource has a top-level "content" field.
            data = data["content"]
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except ValueError:
                    sys.exit(f"the saved result is not JSON: {data[:200]!r}")
        elif isinstance(data, list):
            texts = [b["text"] for b in data
                     if isinstance(b, dict) and b.get("type") == "text" and isinstance(b.get("text"), str)]
            if not texts:
                sys.exit("the saved result has no text block to read")
            try:
                data = json.loads("".join(texts))
            except ValueError:
                # Several blocks that are not one JSON text together: use the first that parses.
                for t in texts:
                    try:
                        data = json.loads(t)
                        break
                    except ValueError:
                        continue
                else:
                    sys.exit(f"the saved result's text is not JSON: {texts[0][:200]!r}")
        else:
            return data


def read_json_file(path):
    try:
        # utf-8-sig also reads files that start with a byte-order mark, as some Windows tools write.
        with open(path, encoding="utf-8-sig") as f:
            text = f.read()
    except OSError as e:
        sys.exit(f"cannot read {path}: {e.strerror}")
    except UnicodeDecodeError:
        sys.exit(f"{path} is not UTF-8 text; save it as UTF-8")
    if not text.strip():
        sys.exit(f"{path} is empty")
    try:
        return json.loads(text)
    except ValueError as e:
        sys.exit(f"{path} is not JSON ({e}); it starts {text.strip()[:80]!r}")


def load_json(path):
    """Read a tool result the model or the app saved, unwrapped to the API's JSON object."""
    data = unwrap(read_json_file(path))
    if not isinstance(data, dict):
        sys.exit(f"{path} does not hold a JSON object")
    return data


def load_spec(path, name):
    """Read a spec the model wrote. It is never a saved tool result, so no unwrapping."""
    data = read_json_file(path)
    if not isinstance(data, dict):
        sys.exit(f"{path} must be a JSON object; see {name} in 'slides_helper.py --help'")
    return data


def mag(d):
    return (d or {}).get("magnitude", 0.0)


def text_of(text_obj):
    runs = []
    size = None
    for te in (text_obj or {}).get("textElements", []):
        tr = te.get("textRun")
        if tr:
            runs.append(tr.get("content", ""))
            fs = tr.get("style", {}).get("fontSize")
            if fs and size is None:
                size = fs.get("magnitude")
    return "".join(runs), size


def estimate_lines(text, width_in, size_pt, bold=False):
    usable = max(width_in - 2 * BOX_PADDING_IN, 0.1)
    em = AVG_CHAR_EM_BOLD if bold else AVG_CHAR_EM
    chars_per_line = max(int(usable * 72 / (size_pt * em)), 1)
    lines = 0
    for para in text.rstrip("\n").split("\n"):
        lines += max(1, -(-len(para) // chars_per_line))
    return lines


def needed_height_in(text, width_in, size_pt, bold=False, space_below_pt=0):
    paras = len(text.rstrip("\n").split("\n"))
    return (estimate_lines(text, width_in, size_pt, bold) * size_pt * LINE_HEIGHT
            + (paras - 1) * space_below_pt) / 72 + 2 * BOX_PADDING_IN


def geometry(el):
    """Rendered box in inches: x, y, w, h."""
    t = el.get("transform", {})
    sx, sy = t.get("scaleX", 1.0), t.get("scaleY", 1.0)
    x, y = t.get("translateX", 0.0), t.get("translateY", 0.0)
    if "table" in el:
        tb = el["table"]
        w = sum(mag(c.get("columnWidth")) for c in tb.get("tableColumns", []))
        h = sum(mag(r.get("rowHeight")) for r in tb.get("tableRows", []))
    else:
        w = mag(el.get("size", {}).get("width")) * sx
        h = mag(el.get("size", {}).get("height")) * sy
    return x / EMU, y / EMU, w / EMU, h / EMU


def kind_of(el):
    for k in ("shape", "table", "image", "sheetsChart", "line", "video", "elementGroup", "wordArt", "speakerSpotlight"):
        if k in el:
            return k
    return "?"


def overlaps(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ix = min(ax + aw, bx + bw) - max(ax, bx)
    iy = min(ay + ah, by + bh) - max(ay, by)
    return ix > 0.05 and iy > 0.05


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


def run_property_tests(seed=20261106, cases=500):
    """Stdlib-only property tests for the pure helpers; raises on failure."""
    import random
    rng = random.Random(seed)
    passed = 0

    def check(name, cond):
        nonlocal passed
        if not cond:
            raise AssertionError(f"property failed: {name}")
        passed += 1

    # emu/mag roundtrip: emu then /EMU recovers inches within half an EMU
    for _ in range(cases):
        inches = rng.uniform(0, 20)
        check("emu-roundtrip", abs(emu(inches) / EMU - inches) < 1 / EMU)
    check("emu-1in", emu(1.0) == EMU)

    # rgb: known values and range
    check("rgb-black", rgb("#000000") == {"red": 0.0, "green": 0.0, "blue": 0.0})
    check("rgb-white", rgb("#FFFFFF") == {"red": 1.0, "green": 1.0, "blue": 1.0})
    for _ in range(cases):
        h = "#%06X" % rng.randint(0, 0xFFFFFF)
        c = rgb(h)
        check("rgb-range", all(0.0 <= v <= 1.0 for v in c.values()))

    # estimate_lines: at least 1 per paragraph; wider box never needs more lines
    for _ in range(cases):
        n = rng.randint(1, 4)
        text = "\n".join("x" * rng.randint(0, 200) for _ in range(n))
        size = rng.choice([8, 12, 14, 24, 32])
        a = estimate_lines(text, 2.0, size)
        b = estimate_lines(text, 9.0, size)
        check("lines-positive", a >= n)
        check("lines-monotone-width", b <= a)
        check("lines-monotone-size", estimate_lines(text, 5.0, 8) <= estimate_lines(text, 5.0, 32))

    # needed_height_in: grows with text size and space_below, bounded below by padding
    for _ in range(cases):
        text = "y" * rng.randint(1, 120)
        h1 = needed_height_in(text, 5.0, 12)
        h2 = needed_height_in(text, 5.0, 32)
        h3 = needed_height_in(text, 5.0, 12, space_below_pt=12)
        check("height-positive", h1 >= 2 * BOX_PADDING_IN)
        check("height-monotone-size", h2 >= h1)
        check("height-monotone-space", h3 >= h1)

    # overlaps: reflexive, symmetric, disjoint when far apart
    for _ in range(cases):
        box = (rng.uniform(0, 9), rng.uniform(0, 5), rng.uniform(0.2, 3), rng.uniform(0.2, 2))
        check("overlap-reflexive", overlaps(box, box))
        other = (rng.uniform(0, 9), rng.uniform(0, 5), rng.uniform(0.2, 3), rng.uniform(0.2, 2))
        check("overlap-symmetric", overlaps(box, other) == overlaps(other, box))
    check("overlap-disjoint", not overlaps((0, 0, 1, 1), (5, 5, 1, 1)))

    # geometry: scale multiplies the EMU size; table sums column/row magnitudes
    el = {"size": {"width": {"magnitude": EMU}, "height": {"magnitude": EMU}},
          "transform": {"scaleX": 2.0, "scaleY": 3.0, "translateX": EMU, "translateY": 0.0}}
    check("geometry-scale", geometry(el) == (1.0, 0.0, 2.0, 3.0))
    tbl = {"transform": {"translateX": 0.0, "translateY": 0.0},
           "table": {"tableColumns": [{"columnWidth": {"magnitude": EMU}}],
                    "tableRows": [{"rowHeight": {"magnitude": EMU // 2}}]}}
    check("geometry-table", geometry(tbl) == (0.0, 0.0, 1.0, 0.5))

    # props/unwrap/text_of/kind_of/alignment/text_style spot checks
    p = props("s1", 0.5, 0.4, 9, 0.8)
    check("props-emu", p["size"]["width"] == {"magnitude": emu(9), "unit": "EMU"})
    check("unwrap-raw", unwrap({"a": 1}) == {"a": 1})
    check("unwrap-content", unwrap({"content": json.dumps({"b": 2})}) == {"b": 2})
    check("unwrap-blocks", unwrap([{"type": "text", "text": json.dumps({"c": 3})}]) == {"c": 3})
    t, s = text_of({"textElements": [{"textRun": {"content": "hi", "style": {"fontSize": {"magnitude": 12}}}}]})
    check("text_of", (t, s) == ("hi", 12))
    check("kind_of", kind_of({"table": {}}) == "table" and kind_of({}) == "?")
    check("alignment-names", alignment("left", "o", "k") == "START" and alignment("END", "o", "k") == "END")
    check("text_style-none", text_style({}, {"objectId": "o"}) is None)
    st = text_style({"size": 14, "bold": True}, {"objectId": "o"})
    check("text_style-fields", st["updateTextStyle"]["fields"] == "fontSize,bold")

    return passed


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true", help="run built-in property tests")
    ap.add_argument("--cases", type=int, default=500)
    ap.add_argument("--seed", type=int, default=20261106)
    args = ap.parse_args(argv)
    if not args.self_test:
        ap.print_help()
        return 2
    passed = run_property_tests(seed=args.seed, cases=args.cases)
    print(f"slides_format self-test: {passed} properties passed (seed={args.seed}, cases={args.cases})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
