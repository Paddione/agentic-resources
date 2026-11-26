#!/usr/bin/env python3
"""Free local steps of sequences/image-to-layers.md: any 2D image (a character, a vehicle, a prop, a boss, a background)
cut into named transparent layers from a flat-colour map, the parts each one hides filled from an in-paint.

Pillow and NumPy only. Every file it writes goes under --out; it reads only the files it is given. The parts come from
a parts file the agent writes per request (--parts, JSON):

  {"parts": [{"name": "body", "colour": "#0000FF", "z": 0},
             {"name": "arm", "colour": "#FF0000", "z": 1}],
   "background": "#000000"}

`colour` is the part's flat colour in the map, `z` its draw order: required, a whole number from 0 (the bottom), one
per part. `background` is not a part name (it is what no part covers). What a part covers is worked out
from the map: where it touches a part drawn under it (a lower `z`), that part goes on behind it, and is filled from the
part's in-paint, so moving the part shows the other one whole; where it touches only the background, nothing is
behind it and moving it shows the background. `hides` overrides that with the parts it covers (`[]`: none).
`background` is the map's colour for what is no part (left transparent); to keep a background as a layer (parallax),
list it as a part.

  masks   --image I --map MAP --parts P --out D
          D/labels.png (each pixel's part), what each part's edge touches (`behind`: the parts under it and the
          background, in pixels) and so what it hides, and for every part that hides another D/mask-<part>.png (the
          part and the parts riding on it, `over`, grown 6 px over their outline; transparent = repainted) for an
          in-paint of what lies behind them. Prints the masks to in-paint.
  layers  --image I --parts P --out D [--fill <part>=<in-paint> ...]
          Cuts D/layers/<z>-<name>.png from the image's own pixels, fills what each occluder hid from its in-paint,
          writes D/layers/manifest.json (name, file, x, y, w, h, z, hides, filled; and `stale`, housekeeping: files
          an earlier run could not remove or rename, for the next run to try again), D/layers.psb (every layer at its
          place), D/recomposed.png and D/layers-sheet.png (every layer, and the occluders moved aside), and prints the
          checks as one JSON line. It reads the last run's D/layers/manifest.json and, after writing the new one,
          removes the layer files it listed that this run no longer writes (`staleKept`: any it could not remove).
  pose    --out D --motion M
          Poses the layers of D through each clip of the motion file M (JSON, below) and writes D/poses/<clip>.gif
          and, for the frame where most opened, D/poses/<clip>-gaps.png (the gaps in magenta). A gap is a pixel inside
          the object's outline (gaps up to 2 * LINE_PX closed) that is transparent in the pose, and not a gap the object
          has at rest, carried along by the part nearest it. An opening is either two parts moved apart, or a part
          moved off a background it was drawn over (both meant to show the background), or a part moved off another
          part that was not painted behind it (a hole: its in-paint). Only the image tells which. Prints, per clip,
          the most gap pixels and their share of the object.

  {"pivots":  {"forearm": [412, 300], "upper-arm": [380, 210]},
   "parents": {"forearm": "upper-arm"},
   "axes":    {"forearm": [1, 0]},
   "clips": [{"name": "wave", "fps": 20,
              "keys": [{"t": 0, "forearm": {"rot": 0}},
                       {"t": 0.5, "forearm": {"rot": 40}, "upper-arm": {"rot": 10, "dy": -4}},
                       {"t": 1.0, "forearm": {"rot": 0}}]}]}

  Per part and key: `rot` degrees counter-clockwise on screen about its pivot, `dx`/`dy` pixels (y down), `slide`
  pixels along its axis (`axes`, turned with the part). `view` ([x0, y0, x1, y1], optional) is a camera: the
  frames are cropped to it, and every transparent pixel inside it is a gap (a scene that fills its frame, a
  parallax background panned inside a margin). A field holds its value between the keys that name it
  (eased), and before the first and after the last; a part never named stays at rest. A child moves with its
  parent; pivots are in the picture's pixels at rest. A part with no pivot turns about its box's centre.
"""

import argparse
import json
import math
import os
import re
import sys

import numpy as np
from PIL import Image, ImageDraw

# The shared helpers sit next to this script. It runs from the skill folder, which ships: never leave bytecode there.
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from layers_common import (  # noqa: E402
    components,
    grow,
    load_rgba,
    same_size,
    soften,
    write_psb,
)

GROW_PX = 6  # a mask is grown this far past its part, so the in-paint covers its drawn outline (4-6 px measured)
FILL_TOL = 40  # 0-255 a channel: an in-paint pixel this close to one of a hidden part's shades is that part
FLAT_FILL = 0.4  # an in-paint whose masked area is mostly one colour ...
FOREIGN = 48  # ... that no visible part has (0-255 a channel) painted a blank, not what lies hidden
SAME_TOL = 16  # 0-255 a channel: an in-paint pixel this close to the image's own pixel there is the occluder redrawn
REPAINT = 0.5  # an in-paint that painted the occluder itself over this share of its area redrew it, not what is behind
LINE_PX = 6  # gaps up to twice this wide between parts are drawn lines: what they enclose is inside the image
HOLE_SHARE = 0.05  # ... unless it is larger than this share of the parts: a real hole, which stays background
SPECK_SHARE = 0.0005  # a patch of one part this small (a share of the picture) inside another is a speck of a line
EDGE_SHARE = 0.1  # a fill that paints none of a part it hides is refused when that part is this share of its edge
ONE_INSIDE = 0.8  # an outlined part's enclosed plain area is one patch (its inside); a lattice's is many gaps
SEE_THROUGH_SHARE = 0.5  # in a part more than this share the background's colour, enclosed patches stay: its colour
SEE_THROUGH_PX = 200  # a patch the map calls a part but the picture shows as plain background, at least this big
TOUCH_PX = (
    20  # a part whose edge runs along a lower part for this many pixels covers it there
)
PALETTE = 24  # colours kept per part, to tell its pixels from another part's
COLOUR_GAP = 64  # 0-255 a channel: two map colours closer than this are too easy for the model to mix up
OFF_SHARE = 0.002  # a map whose pixels this share or more are no part's colour (antialiased edges aside) is refused
BLEND_TOL = 24  # 0-255 a channel: a pixel this near a blend of two map colours, or a part colour's lighter or darker shade
BLEND_PX = 6  # a blend pixel is a soft edge only this near both colours' own pixels
SHADE_PX = 16  # a part's shade is a highlight only when that part closes around it (a patch up to 2 * this across)
MAX_FRAMES = (
    600  # a clip longer than this (30 s at 20 fps) is a t written in milliseconds
)
PART_NAME = re.compile(r"[A-Za-z0-9_-]+")
LAYER_FILE = re.compile(
    r"\d{2,}-" + PART_NAME.pattern + r"\.png"
)  # every name layer_file writes


def layer_file(z, name):
    """A layer's file name, <z>-<name>.png (z 0 or more, at least two digits): LAYER_FILE matches every one."""
    return f"{z:02d}-{name}.png"


def hex_colour(text, where):
    m = re.fullmatch(r"#?([0-9A-Fa-f]{6})", str(text).strip())
    if not m:
        sys.exit(f"{where}: {text!r} is not a #RRGGBB colour")
    v = m.group(1)
    return tuple(int(v[i : i + 2], 16) for i in (0, 2, 4))


RENUMBER = "give it N + 1, where N is the z of the part it is on, and add 1 to every other part whose z is N + 1 or more"


def load_parts(path):
    """The parts file, checked: names safe for file names, unique and never `background`; colours distinct; `z` a whole
    number from 0, one per part; `hides` naming other parts."""
    try:
        spec = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError) as e:
        sys.exit(f"--parts {path}: {e}")
    parts = spec.get("parts") or []
    if not parts:
        sys.exit(f"--parts {path}: no parts")
    names = [p.get("name") for p in parts]
    for n in names:
        if not isinstance(n, str) or not PART_NAME.fullmatch(n):
            sys.exit(f"--parts {path}: part name {n!r}: letters, digits, - and _ only")
    if len(set(names)) != len(names):
        sys.exit(f"--parts {path}: a part name is given twice")
    if "background" in names:
        sys.exit(
            f"--parts {path}: 'background' names what no part covers: call the back layer something else (sky, "
            "backdrop, far)"
        )
    zs = [p.get("z") for p in parts]
    for p, z in zip(parts, zs):
        if "z" not in p:
            sys.exit(
                f"--parts {path}: {p['name']} has no z: give every part its own whole z (0 at the back)"
            )
        if isinstance(z, float) and z.is_integer():
            z = p["z"] = int(z)
        if not isinstance(z, int) or isinstance(z, bool) or z < 0:
            sys.exit(
                f"--parts {path}: {p['name']}'s z must be a whole number, 0 or more (0 at the back), got {z!r}"
            )
    zs = [p["z"] for p in parts]
    for z in sorted(set(zs)):
        shared = [p["name"] for p in parts if p["z"] == z]
        if len(shared) > 1:
            sys.exit(
                f"--parts {path}: {' and '.join(shared)} share z {z}: each part needs its own, as only a lower z is "
                f"covered (to put a part just above another, {RENUMBER})"
            )
    out = []
    for p in parts:
        hides = p.get("hides")
        if hides is not None and not isinstance(hides, list):
            sys.exit(
                f"--parts {path}: {p['name']}'s hides must be a list of part names"
            )
        unknown = [h for h in hides or [] if h not in names or h == p["name"]]
        if unknown:
            sys.exit(
                f"--parts {path}: {p['name']} hides {unknown}, which are not other parts"
            )
        out.append(
            {
                "name": p["name"],
                "colour": hex_colour(p.get("colour"), p["name"]),
                "z": p["z"],
                "hides": hides,
            }
        )
    bg = hex_colour(spec.get("background", "#000000"), "background")
    colours = [p["colour"] for p in out] + [bg]
    for i, c in enumerate(colours):
        for d in colours[i + 1 :]:
            if max(abs(x - y) for x, y in zip(c, d)) < COLOUR_GAP:
                sys.exit(
                    f"--parts {path}: colours {c} and {d} are too close for the model to keep apart ({COLOUR_GAP} a channel)"
                )
    return sorted(out, key=lambda p: p["z"]), bg


def what_is_behind(parts, labels):
    """Each part's edge: how many of its border pixels touch each lower part, and the background. A part with no
    `hides` in the parts file hides the lower parts it touches for TOUCH_PX or more: they go on behind it, and moving
    it must show them, not a hole. Fills in `hides` (and `inferred`) in place; returns the edges.
    """
    bg = len(parts)
    edges = {}
    for i, p in enumerate(parts):
        area = labels == i
        ring = grow(area, 2) & ~area
        e = {"background": int((ring & (labels == bg)).sum())}
        for j, q in enumerate(parts):
            if q["z"] < p["z"]:
                n = int((ring & (labels == j)).sum())
                if n:
                    e[q["name"]] = n
        edges[p["name"]] = p["edges"] = e
        p["inferred"] = p["hides"] is None
        if p["hides"] is None:
            p["hides"] = [
                n for n, c in e.items() if n != "background" and c >= TOUCH_PX
            ]
    return edges


def riding(parts, p):
    """The parts p's in-paint must also paint behind: each part above p that hides p, or a part already in the set,
    but not everything p hides (a buckle on a plate, over the body; a gem on that buckle), grown until it stops: moved
    together, they would otherwise show a hole in the body where they sat, which no in-paint painted."""
    over, grew = set(), True
    while grew:
        grew = False
        for c in parts:
            if (
                c["name"] not in over
                and c["z"] > p["z"]
                and ({p["name"]} | over) & set(c["hides"])
                and set(p["hides"]) - set(c["hides"])
            ):
                over.add(c["name"])
                grew = True
    return sorted(over, key=lambda n: next(q["z"] for q in parts if q["name"] == n))


def paint_area(parts, vis, p):
    """What part p's in-paint must paint behind: its own pixels and those of the parts riding on it."""
    area = vis[p["name"]].copy()
    for n in riding(parts, p):
        area |= vis[n]
    return area


def map_pixels(map_path, size):
    """The map's RGB pixels (int32), checked to be the picture's size."""
    im = Image.open(map_path).convert("RGB")
    same_size(map_path, im, size)
    return np.asarray(im).astype(np.int32)


def labels_of(map_path, size, colours, px=None):
    """Each pixel of the map to its nearest listed colour (an index into `colours`)."""
    if px is None:
        px = map_pixels(map_path, size)
    best = np.zeros(px.shape[:2], np.int64)
    best_d = np.full(px.shape[:2], np.iinfo(np.int64).max)
    for i, c in enumerate(colours):
        d = ((px - np.array(c)) ** 2).sum(-1)
        closer = d < best_d
        best[closer], best_d[closer] = i, d[closer]
    return best


def soft_pixels(px, colours, labels, cand):
    """Of the `cand` pixels (in np.nonzero order), those where the map is soft rather than a new colour: a blend of two
    listed colours within BLEND_PX of both colours' own pixels, or a part colour's lighter or darker shade in a patch
    that part closes around (SHADE_PX). The last colour is the background's: it gets no shades."""
    own = [(labels == i) & ~cand for i in range(len(colours))]
    by = [grow(o, BLEND_PX) for o in own]
    ends = [np.array(c, np.float32) for c in colours]
    ys, xs = np.nonzero(cand)
    v = px[ys, xs].astype(np.float32)

    def on_segment(a, b):
        ab = b - a
        t = np.clip(((v - a) @ ab) / max(1.0, float(ab @ ab)), 0, 1)
        return np.abs(v - (a + t[:, None] * ab)).max(-1) < BLEND_TOL

    soft = np.zeros(len(v), bool)
    for i in range(len(colours)):
        for j in range(i + 1, len(colours)):
            soft |= on_segment(ends[i], ends[j]) & by[i][ys, xs] & by[j][ys, xs]
    for i in range(len(colours) - 1):  # parts only: no shade of the background
        inside = ~grow(~grow(own[i], SHADE_PX), SHADE_PX)[ys, xs]
        for e in (np.zeros(3, np.float32), np.full(3, 255, np.float32)):
            soft |= on_segment(ends[i], e) & inside
    return soft


def off_colour(px, colours, labels):
    """A piece the model painted in a colour no part has: every pixel snaps to its nearest listed colour, so it would
    be merged into a neighbour without a word. Counted: pixels COLOUR_GAP or more a channel from every listed colour,
    past the 2 px of an antialiased edge, and not where the map is only soft (soft_pixels: judged by place as well as
    colour). At OFF_SHARE of the map or more, the most common such colour is returned: its mean colour, its pixel
    count, the box [x0, y0, x1, y1] of its largest piece, and how many pieces it has (largest_piece)."""
    near = to_shades(px, colours)
    cand = near >= COLOUR_GAP
    if cand.sum() < OFF_SHARE * cand.size:
        return None
    soft = soft_pixels(px, colours, labels, cand)
    ys, xs = np.nonzero(cand)
    far = np.zeros(cand.shape, bool)
    far[ys[~soft], xs[~soft]] = True
    far = ~grow(~far, 2)
    if far.sum() < OFF_SHARE * far.size:
        return None
    q = (px[far] // 32).astype(np.int64)
    keys, counts = np.unique(q[:, 0] * 64 + q[:, 1] * 8 + q[:, 2], return_counts=True)
    k = int(keys[counts.argmax()])
    kq = (px // 32).astype(np.int64)
    piece = far & (kq[..., 0] * 64 + kq[..., 1] * 8 + kq[..., 2] == k)
    mean = px[piece].mean(0).round().astype(int)
    count, box = largest_piece(piece)
    return "#%02X%02X%02X" % tuple(mean), int(piece.sum()), box, count


def largest_piece(mask):
    """How many pieces `mask` has and the box [x0, y0, x1, y1] of the largest, counted on a copy at most 256 px a
    side (a block is set when any of its pixels is), so the flood fill stays small on a large map."""
    H, W = mask.shape
    f = max(1, -(-max(H, W) // 256))
    h, w = -(-H // f), -(-W // f)
    pad = np.zeros((h * f, w * f), bool)
    pad[:H, :W] = mask
    small = pad.reshape(h, f, w, f).any((1, 3))
    pieces = components(small)
    yy, xx = np.divmod(max(pieces, key=len), w)
    box = [
        int(xx.min()) * f,
        int(yy.min()) * f,
        min(W, (int(xx.max()) + 1) * f),
        min(H, (int(yy.max()) + 1) * f),
    ]
    return len(pieces), box


def plain_background(labels, bg, orig):
    """Where the picture shows the plain background (within SAME_TOL of its main colours), or None when the map
    shows no background to learn it from (a scene that fills its frame)."""
    background = labels == bg
    if background.sum() < 0.01 * labels.size:
        return None
    return to_shades(orig, shades(orig, background, min_share=0.05)) <= SAME_TOL


def close_lines(labels, bg, plain=None):
    """The map's drawn lines inside the image (an eye's outline, the gaps between a chain's links, a seam between two
    parts) given to the part around them: the model draws them in the background's colour, black, and a layer cut
    from them would be full of holes. Inside means not reached from the image's edge once gaps up to 2 * LINE_PX
    wide are closed (those gaps are lines too); an inside patch larger than HOLE_SHARE of the parts is a real hole (it
    shows what is behind the image) and stays background, and so does any pixel where the picture shows the plain
    background (`plain`): the sky seen between ropes is no drawn line."""
    bgm = labels == bg
    sil = ~grow(~grow(~bgm, LINE_PX), LINE_PX)
    pad = Image.fromarray(
        np.pad(bgm & ~sil, 1, constant_values=True).astype(np.uint8) * 255
    )
    ImageDraw.floodfill(pad, (0, 0), 128)
    enclosed = bgm & (np.asarray(pad)[1:-1, 1:-1] != 128)
    cap = HOLE_SHARE * (~bgm).sum()
    lines = bgm & sil
    for part in components(enclosed & ~sil):
        if len(part) <= cap:
            lines.ravel()[part] = True
    if plain is not None:
        lines &= ~plain
    out = labels.copy()
    left = lines.copy()
    while left.any():
        took = False
        for i in range(bg):
            reach = grow(out == i, 1) & left
            if reach.any():
                out[reach], left[reach], took = i, False, True
        if not took:
            break
    return out


def despeckle(labels, bg):
    """Small patches of one part inside another given to the part around them: the model draws a rivet, a seam or a
    fold line in a neighbour's colour, and as a part those specks would cut holes in the layer around them and make
    the two parts look as if they touched. A patch counts when it is smaller than SPECK_SHARE of the picture and is not
    its part's main patch; it goes to the other part it touches most (a speck on a part's rim touches the background
    too), or to the background when it touches no other part (a stray dot). Twice over, so a speck freed by its
    neighbours' moving goes too."""
    H, W = labels.shape
    cap = SPECK_SHARE * H * W
    out = labels.copy()
    moved = 0
    for i in [k for _ in range(2) for k in range(bg)]:
        patches = components(out == i)
        biggest = max((len(q) for q in patches), default=0)
        for part in patches:
            # The part's own main patch stays, however small the part (a gem, a button).
            if len(part) > cap or len(part) == biggest:
                continue
            ys, xs = np.divmod(part, W)
            y0, y1 = max(0, ys.min() - 2), min(H, ys.max() + 3)
            x0, x1 = max(0, xs.min() - 2), min(W, xs.max() + 3)
            local = np.zeros((y1 - y0, x1 - x0), bool)
            local[ys - y0, xs - x0] = True
            ring = grow(local, 1) & ~local
            around = out[y0:y1, x0:x1][ring]
            if not around.size:
                continue
            values, counts = np.unique(
                around[(around != i) & (around != bg)], return_counts=True
            )
            out[ys, xs] = values[counts.argmax()] if values.size else bg
            moved += len(part)
    return out, moved


def see_through(labels, bg, plain):
    """What the map called a part where the picture shows the plain background through it (the sky between a mast
    and its rigging, the gaps of a fence, the space under an arm): the model fills an outline's inside solid. A patch
    of SEE_THROUGH_PX or more within SAME_TOL of the background's colours goes to the background; a thin line in it
    (a rope, a bar) is not the background's colour and stays. Only on a plain background (one the map shows).
    One exception, judged by shape as well as colour: a patch enclosed by the part's own outline (it reaches the
    map's background through no gap) in a part more than SEE_THROUGH_SHARE the background's colour is that part's
    colour (a white part outlined on white), and stays, when it is the part's one inside (ONE_INSIDE of its enclosed
    patches); many enclosed gaps (a fence with rails, a ladder) go to the background. The picture's frame counts as background: a gap open only
    through it (rigging cut by the edge) is no enclosed patch. Returns the labels, the pixels moved, and per part kept
    so its kept pixels and their box [x0, y0, x1, y1] (the agent checks them against the picture)."""
    if plain is None:
        return labels, 0, {}
    background = labels == bg
    mostly = np.zeros(labels.shape, bool)
    kept = []
    for i in range(bg):
        own = labels == i
        if own.any() and (plain & own).sum() > SEE_THROUGH_SHARE * own.sum():
            mostly |= own
            kept.append(i)
    edge = grow(background, 1)
    edge[[0, -1], :] = True
    edge[:, [0, -1]] = True
    out = labels.copy()
    moved, stayed = 0, np.zeros(labels.shape, bool)
    held = {}  # per mostly-background part: its enclosed patches, judged together below
    for part in components(plain & ~background):
        if len(part) < SEE_THROUGH_PX:
            continue
        if not edge.ravel()[
            part
        ].any():  # enclosed: a mostly-background part may keep it
            stay = mostly.ravel()[part]
            if stay.any():
                owner = int(np.bincount(labels.ravel()[part[stay]]).argmax())
                held.setdefault(owner, []).append(part[stay])
            part = part[~stay]
        out.ravel()[part] = bg
        moved += len(part)
    # An outlined part (a white ghost) encloses one patch, its inside; a lattice mapped solid (a fence with rails, a
    # ladder) encloses many gaps of a size: those are see-through after all.
    for owner, patches in held.items():
        sizes = [len(x) for x in patches]
        if max(sizes) >= ONE_INSIDE * sum(sizes):
            for x in patches:
                stayed.ravel()[x] = True
        else:
            for x in patches:
                out.ravel()[x] = bg
                moved += len(x)
    report = {}
    for i in kept:
        mine = stayed & (labels == i)
        if mine.any():
            rows, cols = np.flatnonzero(mine.any(1)), np.flatnonzero(mine.any(0))
            report[i] = {
                "px": int(mine.sum()),
                "box": [
                    int(cols[0]),
                    int(rows[0]),
                    int(cols[-1]) + 1,
                    int(rows[-1]) + 1,
                ],
            }
    return out, moved, report


def attached(candidates, to):
    """The 4-connected parts of `candidates` that touch `to`: a patch joined to the visible part, never a floating one."""
    edge = grow(to, 1)
    out = np.zeros(candidates.shape, bool)
    for part in components(candidates):
        if edge.ravel()[part].any():
            out.ravel()[part] = True
    return out


def shades(img, mask, min_share=0.005):
    """A part's own colours: its pixels reduced to `colours` by median cut, so a part of several materials (skin, cloth,
    leather, steel) keeps each one, shadow to highlight. Lightness bands of the whole part would average those
    materials into colours it does not have. A colour under `min_share` of the pixels is a stray (an outline's edge, a
    speck), not one of the part's."""
    px = img[:, :, :3][mask].astype(np.uint8)
    if len(px) < 20:
        return [np.median(px, axis=0)] if len(px) else []
    if len(px) > 200_000:
        px = px[:: len(px) // 200_000 + 1]
    q = Image.fromarray(px.reshape(-1, 1, 3), "RGB").quantize(
        min(PALETTE, len(px)), method=Image.Quantize.MEDIANCUT
    )
    used, n = np.unique(np.asarray(q), return_counts=True)
    pal = np.array(q.getpalette()[: 3 * (used.max() + 1)], float).reshape(-1, 3)
    keep = n >= min_share * n.sum()
    return list(pal[used[keep]]) if keep.any() else list(pal[used])


def to_shades(img, cols):
    """Per pixel, the distance (0-255, the largest channel) to the nearest of `cols`."""
    if not cols:
        return np.full(img.shape[:2], np.inf)
    return np.min([np.abs(img[:, :, :3] - c).max(-1) for c in cols], axis=0)


def blank_share(fill, area, refs):
    """The share of `area` the fill's most common colour takes, when that colour is far from every reference colour
    (a flat black over a pastel object), else 0: a blank passes every other check, hidden under the parts above.
    """
    if area.sum() < 50:
        return 0.0
    px = fill[:, :, :3][area]
    q = (px // 32).astype(np.int32)
    keys = q[:, 0] * 64 + q[:, 1] * 8 + q[:, 2]
    top = np.bincount(keys).argmax()
    share = float((keys == top).mean())
    colour = px[keys == top].mean(0)
    if share > FLAT_FILL and all(np.abs(colour - r).max() > FOREIGN for r in refs):
        return share
    return 0.0


def cmd_masks(a):
    parts, bg = load_parts(a.parts)
    W, H = Image.open(a.image).size
    os.makedirs(a.out, exist_ok=True)
    colours = [p["colour"] for p in parts] + [bg]
    mpx = map_pixels(a.map, (W, H))
    raw = labels_of(a.map, (W, H), colours, mpx)
    off = off_colour(mpx, colours, raw)
    if off:
        sys.exit(
            f"masks: the map paints {off[1]} px in {off[0]}, which is no part's colour nor the background's, in "
            f"{off[3]} piece(s), the largest within [x0, y0, x1, y1] {off[2]}: when that piece moves on its own, add "
            f"it to --parts as a part in {off[0]}, with a name and a z ({RENUMBER}), "
            "and run masks again (free); when the box runs along an edge or the colour is a mix of its neighbours, "
            "the map is soft: redo it in flat colours only; else redo the map naming that piece's part"
        )
    plain = plain_background(raw, len(parts), load_rgba(a.image))
    labels, specks = despeckle(close_lines(raw, len(parts), plain), len(parts))
    labels, seen, kept = see_through(labels, len(parts), plain)
    Image.fromarray(np.array(colours, np.uint8)[labels], "RGB").save(
        os.path.join(a.out, "labels.png")
    )
    counts = {p["name"]: int((labels == i).sum()) for i, p in enumerate(parts)}
    edges = what_is_behind(parts, labels)
    vis = {q["name"]: labels == i for i, q in enumerate(parts)}
    masks = []
    for p in parts:
        if not p["hides"] or not vis[p["name"]].any():
            continue
        mask = grow(paint_area(parts, vis, p), GROW_PX)
        rgba = np.zeros((H, W, 4), np.uint8)
        rgba[:, :, 3] = np.where(mask, 0, 255)
        path = os.path.join(a.out, f"mask-{p['name']}.png")
        Image.fromarray(rgba, "RGBA").save(path)
        masks.append(
            {
                "occluder": p["name"],
                "mask": path,
                "px": int(mask.sum()),
                "paint": p["hides"],
                "over": riding(parts, p),
                "behind": edges[p["name"]],
                "inferred": p["inferred"],
            }
        )
    missing = [n for n, c in counts.items() if c == 0]
    print(
        json.dumps(
            {
                "labels": os.path.join(a.out, "labels.png"),
                "parts": counts,
                "specksMoved": specks,
                "seeThroughPx": seen,
                "seeThroughKept": {parts[i]["name"]: v for i, v in kept.items()},
                "onlyBackgroundBehind": [
                    p["name"] for p in parts if not p["hides"] and counts[p["name"]]
                ],
                "missing": missing,
                "masks": masks,
            }
        )
    )


def hidden_parts(parts, vis, background, orig, fills):
    """What each occluder hid: in its mask, the in-paint pixels that are not the image's own pixels there (the
    occluder redrawn), nearer one of the hidden parts' shades than the background's or another hidden part's, joined to that part's visible pixels (a floating patch is a
    guess), and the gaps the part then encloses. The mask is paint_area: the occluder and the parts riding on it.
    Refuses a blank fill, and one that painted the occluder again instead of what lies behind it. Unchanged pixels in a
    colour the occluder shares with a part it hides (a flat sleeve over the same cloth) are no redraw, unless they are
    its drawn outline, which kept in place is refused. A rider left in place (its pixels unchanged and unlike every
    hidden part) is refused by name; one in a hidden part's colour is not.
    """
    H, W = background.shape
    part_shades = {n: shades(orig, vis[n]) for n in vis}
    # The background is plain: only its main colours (a stray patch the map calls background is no colour of it).
    bg_shades = shades(orig, background, min_share=0.05)
    refs = [c for n in vis for c in part_shades[n]] + bg_shades
    hidden = {n: np.zeros((H, W), bool) for n in vis}
    rim = {n: np.zeros((H, W), bool) for n in vis}
    colour = (
        {}
    )  # per hidden part: (flat pixel indices, occluder) for each stretch of in-paint it takes
    report = {}
    for p in parts:
        occ = p["name"]
        if occ not in fills:
            continue
        fill, area = fills[occ], paint_area(parts, vis, p)
        mask = grow(area, GROW_PX)
        blank = blank_share(fill, area, refs)
        if blank:
            sys.exit(
                f"layers: the --fill for {occ} painted {blank:.0%} of its mask one colour no part has, a blank: redo it"
            )
        cand = {h: to_shades(fill, part_shades[h]) for h in p["hides"]}
        nearest = np.min(list(cand.values()), axis=0)
        # The occluder redrawn is its own pixels again, in place; a part behind it can share its colours (a sleeve
        # over a shirt of the same cloth), so the occluder's shades are no test.
        same = (
            np.abs(fill[..., :3].astype(np.int16) - orig[..., :3].astype(np.int16)).max(
                -1
            )
            <= SAME_TOL
        )
        d_bg = to_shades(fill, bg_shades)
        # Unchanged pixels in a colour the occluder shares with a part it hides (a flat sleeve over a shirt of the same
        # cloth) are no sign of a redraw: what is behind looks the same there. Only the occluder's other colours count.
        # Only when the unchanged pixels would otherwise read as a redraw: elsewhere they are the occluder's own lines.
        shared = (
            same
            & (to_shades(fill, part_shades[occ]) <= SAME_TOL)
            & (nearest <= SAME_TOL)
        )
        if (area & same).sum() <= REPAINT * area.sum():
            shared = np.zeros_like(same)
        else:
            # The occluder's drawn outline (its edge band, away from its main colour) is its own even in a shared colour
            # (the part behind has dark outlines too): kept unchanged, the in-paint redrew it.
            main = np.median(orig[area][:, :3], axis=0)
            lines = (
                area
                & grow(~area, LINE_PX)
                & (np.abs(orig[..., :3] - main).max(-1) > FILL_TOL)
            )
            shared &= ~lines
            if (lines & same).sum() > REPAINT * max(1, lines.sum()):
                sys.exit(
                    f"layers: the --fill for {occ} kept {occ}'s outline, so it redrew {occ} instead of what lies "
                    "behind: redo it, asking to paint what is hidden as if the part were lifted away"
                )
        # The parts riding on the occluder are in its mask (`over`): an in-paint that left one in place left a hole under
        # it in what lies behind, which no other check catches.
        for n in riding(parts, p):
            # A rider in the colour of the part behind (a shirt-coloured patch on a sleeve over the shirt) matches the
            # picture once correctly painted: only its pixels unlike every hidden part count.
            kept = float(
                (vis[n] & same & (nearest > SAME_TOL)).sum() / max(1, vis[n].sum())
            )
            if kept > REPAINT:
                sys.exit(
                    f"layers: the --fill for {occ} kept {n}, riding on {occ}, over {kept:.0%} of it: redo it, asking "
                    f"to paint what lies behind {occ} and {n} as if both were lifted away"
                )
        riders = np.zeros_like(same)
        for n in riding(parts, p):
            riders |= vis[n]
        painted_rider = riders & (
            nearest <= SAME_TOL
        )  # a rider correctly painted in a hidden part's colour
        repaint = float(
            (area & same & ~shared & ~painted_rider).sum() / max(1, area.sum())
        )
        if repaint > REPAINT:
            sys.exit(
                f"layers: the --fill for {occ} painted {occ} itself over {repaint:.0%} of it, not what lies behind: redo "
                "it, asking to paint what is hidden as if the part were lifted away"
            )
        for h, d in cand.items():
            # A shared-colour pixel continues the part behind (only when the gate above let shared through).
            inner = shared & (d <= SAME_TOL)
            take = (
                mask
                & ~vis[h]
                & (d < FILL_TOL)
                & (d <= nearest)
                & (~same | inner)
                & (d < d_bg)
            )
            take = attached(take, vis[h])
            # The occluder's own outline: the map's edge runs inside the drawn line, so the line's outer half is
            # labelled the part behind and would stay on it, a seam, when the occluder moves. Just outside the
            # occluder (the GROW_PX the mask reaches), wherever the in-paint is not the picture's pixel, the picture's
            # pixel is the occluder's edge: it goes to the occluder, and the hidden part takes the in-paint there.
            # (Not by colour: the hidden part has dark outlines of its own.)
            # The occluder's own outline only: a rider's outline stays the rider's (area takes in the riders).
            edge_band = grow(vis[occ], GROW_PX) & vis[h] & ~same
            # An occluder along a good share of the part it hides that fills none of it painted something else there: a
            # blank in a colour the image has (black by dark outlines), or the wrong part. Moving it would show a hole.
            # Along a short stretch (a strap's end under a plate's rim), nothing of it behind is plausible: reported.
            edge = p.get("edges") or {}
            share = edge.get(h, 0) / max(1, sum(edge.values()))
            if not take.any() and share < EDGE_SHARE:
                report.setdefault("notFilled", {})[f"{occ}>{h}"] = round(share, 3)
                continue
            if not take.any() and (grow(area, GROW_PX + 1) & vis[h]).any():
                sys.exit(
                    f"layers: the --fill for {occ} painted none of {h} behind it: redo it, asking for {h} continued "
                    "behind, never a flat fill"
                )
            # Judged above on what it painted under the occluder; its outline band is taken only from a fill that passed.
            rim[occ] |= edge_band
            take |= edge_band
            # What the shade test left out inside the part (its outlines and dark shading next to the occluder, a
            # pinhole): mask pixels the part now encloses, up to 2 * LINE_PX wide, unless painted as background. Moving
            # the occluder would open them as slivers.
            region = vis[h] | hidden[h] | take
            closed = ~grow(~grow(region, LINE_PX), LINE_PX)
            take |= closed & mask & ~region & ~(d_bg < d)
            hidden[h] |= take
            colour.setdefault(h, []).append((np.flatnonzero(take), occ))
            report.setdefault(occ, {})[h] = int(take.sum())
    return hidden, colour, report, rim


def outer_rims(parts, vis, background, orig):
    """Each part's outline against the background: the map's edge runs inside the drawn line, so the line's outer
    half is labelled background and a moved part would leave it behind. Background pixels within GROW_PX of a part
    that are not the background's colour go to that part, the frontmost first."""
    bg_shades = shades(orig, background, min_share=0.05)
    drawn = background & (to_shades(orig, bg_shades) > FILL_TOL)
    out, claimed = {}, np.zeros(background.shape, bool)
    for p in sorted(parts, key=lambda q: -q["z"]):
        n = p["name"]
        out[n] = grow(vis[n], GROW_PX) & drawn & ~claimed
        claimed |= out[n]
    return out


def tidy_stale(folder, stale, written):
    """Remove the last run's layer files this run did not write. A stale name that is the same file as one just written
    (os.path.samefile: on a case-insensitive disk, Windows or default macOS, 02-Turret.png is 02-turret.png; a link to
    a new layer) is kept, and a case-only variant is renamed to the manifest's name, so the folder still reads on a
    case-sensitive disk. Returns two lists: files that could not be removed (outdated copies of a part that a glob or
    the Unity import would still pick up: delete by hand), and current layers whose case could not be fixed (keep
    them; rename by hand)."""
    left, case = [], []
    paths = [os.path.join(folder, w) for w in written]
    for fn in stale:
        path_ = os.path.join(folder, fn)
        try:
            if not os.path.isfile(path_):
                continue
            same = [
                w for w in paths if os.path.exists(w) and os.path.samefile(path_, w)
            ]
        except OSError as e:
            print(
                f"layers: could not check {fn} in {folder} ({e}): left as it is; delete it by hand if outdated",
                file=sys.stderr,
            )
            left.append(fn)
            continue
        if same:
            w = os.path.basename(same[0])
            if fn != w and fn.lower() == w.lower():
                try:
                    if w not in os.listdir(folder):
                        os.replace(path_, same[0])
                except OSError as e:
                    case.append(fn)
                    print(
                        f"layers: {fn} is the current layer {w} with its case differing, and could not be renamed "
                        f"({e}): keep it, and rename it to {w} by hand",
                        file=sys.stderr,
                    )
            continue
        try:
            os.remove(path_)
        except OSError as e:
            left.append(fn)
            print(
                f"layers: could not remove {fn}, an outdated layer, from {folder} ({e}): delete it by hand",
                file=sys.stderr,
            )
    return left, case


def cmd_layers(a):
    parts, bg = load_parts(a.parts)
    W, H = Image.open(a.image).size
    orig = load_rgba(a.image)
    lab_path = os.path.join(a.out, "labels.png")
    if not os.path.exists(lab_path):
        sys.exit(f"layers: {lab_path} is missing: run masks first, into the same --out")
    colours = [p["colour"] for p in parts] + [bg]
    labels = labels_of(lab_path, (W, H), colours)
    what_is_behind(parts, labels)
    vis = {p["name"]: labels == i for i, p in enumerate(parts)}
    background = labels == len(parts)
    fills = {}
    for spec in a.fill or []:
        name, _, path = spec.partition("=")
        if name not in vis or not path:
            sys.exit(
                f"layers: --fill {spec!r}: write it as <occluder part>=<in-paint file>"
            )
        if not next(p for p in parts if p["name"] == name)["hides"]:
            sys.exit(f"layers: {name} hides nothing: drop its --fill")
        fills[name] = load_rgba(path, (W, H))
    missing = [
        p["name"]
        for p in parts
        if p["hides"] and vis[p["name"]].any() and p["name"] not in fills
    ]
    if missing:
        sys.exit(
            f"layers: no --fill for {missing}: each part that hides another needs the in-paint of its mask"
        )
    hidden, hidden_colour, report, rim = hidden_parts(
        parts, vis, background, orig, fills
    )
    outer = outer_rims(parts, vis, background, orig)

    os.makedirs(os.path.join(a.out, "layers"), exist_ok=True)
    # Files are named <z>-<name>.png and a z can change between runs (a part added under the others). The last run's
    # layer files, as its manifest lists them, are removed once the new manifest is written: only names of that form,
    # never a file of the user's, and a run that fails first leaves the old manifest.
    manifest = os.path.join(a.out, "layers", "manifest.json")
    stale, unchecked = [], False
    try:
        old = json.load(open(manifest, encoding="utf-8"))
        if not isinstance(old, dict) or not isinstance(old.get("layers"), list):
            raise ValueError("no list of layers")
        listed = [r.get("file") for r in old["layers"] if isinstance(r, dict)]
        earlier = old.get("stale") or []  # left by an earlier run
        if not isinstance(earlier, list):
            raise ValueError("stale is no list")
        stale = listed + [fn for fn in earlier if isinstance(fn, str)]
    except FileNotFoundError:
        pass  # a first run
    except (OSError, ValueError, TypeError) as e:
        unchecked = True
        print(
            f"layers: could not read the last run's {manifest} ({e}): its layer files, if any, stay; delete outdated "
            "ones by hand",
            file=sys.stderr,
        )
    stale = [fn for fn in stale if isinstance(fn, str) and LAYER_FILE.fullmatch(fn)]
    rows, layers = [], []
    canvas = np.zeros((H, W, 4), np.float32)
    for p in parts:
        n = p["name"]
        mask = vis[n] | hidden[n] | rim[n] | outer[n]
        if not mask.any():
            continue
        # Softened outward only: inside the part stays opaque, so a line 2-3 px wide (a rope, a rigging line) keeps
        # its full strength instead of fading into half-transparency.
        alpha = np.maximum(mask.astype(np.float32), soften(mask))
        colour = np.array(orig)
        flat = colour.reshape(-1, 4)  # a view: colour is a fresh C-contiguous array
        for idx, occ in hidden_colour.get(n, []):
            flat[idx] = fills[occ].reshape(-1, 4)[idx]
        rgba = np.dstack([colour[:, :, :3], alpha * 255]).clip(0, 255).astype(np.uint8)
        im = Image.fromarray(rgba, "RGBA")
        box = im.getbbox()
        fn = layer_file(p["z"], n)
        im.crop(box).save(os.path.join(a.out, "layers", fn))
        rows.append(
            {
                "name": n,
                "file": fn,
                "x": box[0],
                "y": box[1],
                "w": box[2] - box[0],
                "h": box[3] - box[1],
                "z": p["z"],
                "hides": p["hides"],
                "filled": int(hidden[n].sum()),
            }
        )
        layers.append((n, rgba, True))
        a_ = alpha[..., None]
        canvas[:, :, :3] = colour[:, :, :3] * a_ + canvas[:, :, :3] * (1 - a_)
        canvas[:, :, 3:] = a_ + canvas[:, :, 3:] * (1 - a_)
    doc = {"size": [W, H], "source": os.path.basename(a.image), "layers": rows}
    json.dump(doc, open(manifest, "w"), indent=1)
    stale_kept, case_kept = tidy_stale(
        os.path.join(a.out, "layers"), stale, [r["file"] for r in rows]
    )
    if (
        stale_kept or case_kept
    ):  # carried on, so the next run tries again and still reports them
        doc["stale"] = stale_kept + case_kept
        json.dump(doc, open(manifest, "w"), indent=1)
    # Recompose: the layers over the image's own background must give the image back.
    out = canvas[:, :, :3] + orig[:, :, :3] * background[..., None] * (
        1 - canvas[:, :, 3:]
    )
    Image.fromarray(out.clip(0, 255).astype(np.uint8), "RGB").save(
        os.path.join(a.out, "recomposed.png")
    )
    fg = ~background
    diff = np.abs(out - orig[:, :, :3]).max(-1)
    psb = os.path.join(a.out, "layers.psb")
    write_psb(
        psb,
        W,
        H,
        layers,
        np.dstack([out, canvas[:, :, 3:] * 255]).clip(0, 255).astype(np.uint8),
    )
    sheet(layers, orig, parts, os.path.join(a.out, "layers-sheet.png"))
    print(
        json.dumps(
            {
                "manifest": manifest,
                "psb": psb,
                "layers": [r["name"] for r in rows],
                "filled": report,
                "staleKept": stale_kept,
                "caseKept": case_kept,
                "staleUnchecked": unchecked,
                "recomposeMeanDiff": (
                    round(float(diff[fg].mean()), 2) if fg.any() else 0.0
                ),
                "recomposePctOver16": (
                    round(float((diff[fg] > 16).mean() * 100), 2) if fg.any() else 0.0
                ),
            }
        )
    )


def sheet(layers, orig, parts, path):
    """Every layer on a checker, then the layers with each occluder moved aside: a hole or a cut there is a failed fill."""
    H, W = orig.shape[:2]
    tw = 256
    th = int(H * tw / W)
    tiles = [(n, Image.fromarray(rgba, "RGBA")) for n, rgba, _ in layers]
    moved = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    occluders = {p["name"] for p in parts if p["hides"]}
    for n, im in tiles:
        moved.alpha_composite(im, (W // 12, -H // 30) if n in occluders else (0, 0))
    tiles.append(("occluders moved", moved))
    cols = 6
    out = Image.new(
        "RGB",
        (cols * tw, ((len(tiles) + cols - 1) // cols) * (th + 18)),
        (255, 255, 255),
    )
    d = ImageDraw.Draw(out)
    check = Image.new("RGBA", (tw, th), (235, 235, 235, 255))
    cd = ImageDraw.Draw(check)
    for y in range(0, th, 16):
        for x in range(0, tw, 16):
            if (x // 16 + y // 16) % 2:
                cd.rectangle([x, y, x + 15, y + 15], fill=(205, 205, 205, 255))
    for k, (name, im) in enumerate(tiles):
        x, y = (k % cols) * tw, (k // cols) * (th + 18)
        tile = check.copy()
        tile.alpha_composite(im.resize((tw, th)))
        out.paste(tile.convert("RGB"), (x, y + 18))
        d.text((x + 4, y + 3), name, fill=(0, 0, 0))
    out.save(path)


MOVES = ("rot", "dx", "dy", "slide")


def number(x):
    """A finite JSON number (json.load accepts NaN and Infinity; a bool is no number)."""
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def load_motion(path, names):
    try:
        spec = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError) as e:
        sys.exit(f"--motion {path}: {e}")
    for key in ("pivots", "parents", "axes"):
        for n in spec.get(key) or {}:
            if n not in names:
                sys.exit(
                    f"--motion {path}: {key} names {n!r}, which is no layer ({', '.join(names)})"
                )
    parents = spec.get("parents") or {}
    for n, parent in parents.items():
        if parent not in names:
            sys.exit(f"--motion {path}: {n}'s parent {parent!r} is no layer")
        seen, at = {n}, parent
        while at:
            if at in seen:
                sys.exit(f"--motion {path}: the parents loop through {at}")
            seen.add(at)
            at = parents.get(at)
    view = spec.get("view")
    if view is not None and not (
        isinstance(view, list)
        and len(view) == 4
        and all(number(v) for v in view)
        and view[0] < view[2]
        and view[1] < view[3]
    ):
        sys.exit(f"--motion {path}: view must be [x0, y0, x1, y1], x0 < x1 and y0 < y1")
    clips = spec.get("clips") or []
    if not clips:
        sys.exit(f"--motion {path}: no clips")
    for c in clips:
        if not PART_NAME.fullmatch(str(c.get("name", ""))):
            sys.exit(
                f"--motion {path}: clip name {c.get('name')!r}: letters, digits, - and _ only"
            )
        fps = c.get("fps", 20)
        if not number(fps) or fps < 1:
            sys.exit(
                f"--motion {path}: clip {c['name']}: fps must be a number, 1 or more"
            )
        keys = c.get("keys") or []
        for k in keys:
            if not isinstance(k, dict) or not number(k.get("t")):
                sys.exit(
                    f"--motion {path}: clip {c['name']}: every key needs a number t"
                )
            for n, v in k.items():
                if n == "t":
                    continue
                if not isinstance(v, dict):
                    sys.exit(
                        f"--motion {path}: clip {c['name']}, t {k['t']}: {n!r} must be an object of {MOVES}"
                    )
                for f, x in v.items():
                    if f not in MOVES or not number(x):
                        sys.exit(
                            f"--motion {path}: clip {c['name']}, t {k['t']}, {n}: {f!r}={x!r}: only {MOVES}, as numbers"
                        )
        if len(keys) < 2 or any(b["t"] <= a["t"] for a, b in zip(keys, keys[1:])):
            sys.exit(
                f"--motion {path}: clip {c['name']} needs two or more keys, in rising t"
            )
        frames = (keys[-1]["t"] - keys[0]["t"]) * fps
        if frames > MAX_FRAMES:
            sys.exit(
                f"--motion {path}: clip {c['name']} is {frames:.0f} frames, over {MAX_FRAMES}: t is in seconds; "
                "for a clip that long, shorten it (split it in two) or lower its fps"
            )
        for k in keys:
            for n in k:
                if n != "t" and n not in names:
                    sys.exit(
                        f"--motion {path}: clip {c['name']} moves {n!r}, which is no layer"
                    )
    return spec


def key_value(keys, part, field, t):
    """The part's field at time t: eased between the keys that name it, held before the first and after the last."""
    named = [(k["t"], k[part][field]) for k in keys if field in k.get(part, {})]
    if not named:
        return 0.0
    if t <= named[0][0]:
        return float(named[0][1])
    for (t0, v0), (t1, v1) in zip(named, named[1:]):
        if t <= t1:
            u = (t - t0) / (t1 - t0)
            u = u * u * (3 - 2 * u)
            return v0 + (v1 - v0) * u
    return float(named[-1][1])


def local_matrix(pivot, axis, move):
    """The part's move in its parent's frame, a 3x3 matrix on (x, y, 1): a turn about the pivot, then a slide along the
    turned axis and a shift. `move` is (rot, dx, dy, slide)."""
    rot, dx, dy, slide = move
    a = np.radians(rot)
    c, s_ = np.cos(a), np.sin(a)
    # Counter-clockwise on screen, where y points down.
    r = np.array([[c, s_, 0], [-s_, c, 0], [0, 0, 1]])
    px, py = pivot
    to = np.array([[1, 0, -px], [0, 1, -py], [0, 0, 1]])
    back = np.array([[1, 0, px], [0, 1, py], [0, 0, 1]])
    ax, ay = r[:2, :2] @ np.array(axis, float)
    shift = np.array([[1, 0, dx + slide * ax], [0, 1, dy + slide * ay], [0, 0, 1]])
    return shift @ back @ r @ to


def pose_frame(layers, spec, keys, t, size):
    """Every layer moved to its pose at time t (each child after its parent's move), drawn in z order."""
    W, H = size
    world = {}
    parents = spec.get("parents") or {}

    def matrix(n):
        if n not in world:
            L = layers[n]
            pivot = (spec.get("pivots") or {}).get(n) or [
                L["x"] + L["w"] / 2,
                L["y"] + L["h"] / 2,
            ]
            axis = (spec.get("axes") or {}).get(n) or [1, 0]
            m = local_matrix(
                pivot,
                axis,
                tuple(key_value(keys, n, f, t) for f in ("rot", "dx", "dy", "slide")),
            )
            world[n] = (matrix(parents[n]) @ m) if n in parents else m
        return world[n]

    canvas = Image.new("RGBA", (W, H))
    for n in sorted(layers, key=lambda n: layers[n]["z"]):
        L = layers[n]
        # From a canvas pixel back to the layer's own pixel: the inverse of its move, then its offset.
        inv = np.array([[1, 0, -L["x"]], [0, 1, -L["y"]], [0, 0, 1]]) @ np.linalg.inv(
            matrix(n)
        )
        moved = L["image"].transform(
            (W, H), Image.AFFINE, tuple(inv[:2].ravel()), resample=Image.BICUBIC
        )
        canvas.alpha_composite(moved)
    return canvas, {n: matrix(n) for n in layers}


def moved_mask(mask, m):
    """A canvas-sized mask moved by the world matrix `m`."""
    inv = np.linalg.inv(m)
    im = Image.fromarray(mask.astype(np.uint8) * 255).transform(
        mask.shape[::-1], Image.AFFINE, tuple(inv[:2].ravel()), resample=Image.BILINEAR
    )
    return np.asarray(im) > 0


def rest_gap_owners(layers, rest_gaps, size):
    """Each gap the object has at rest (a concave edge, the space between two wheels), given to the nearest layer, so
    it moves with that layer: only a gap that opens counts, not one the object carries along.
    """
    W, H = size
    alpha = {}
    for n, L in layers.items():
        a = np.zeros((H, W), bool)
        a[L["y"] : L["y"] + L["h"], L["x"] : L["x"] + L["w"]] = (
            np.asarray(L["image"])[:, :, 3] > 40
        )
        alpha[n] = a
    owners = {n: np.zeros((H, W), bool) for n in layers}
    left = rest_gaps.copy()
    for _ in range(4 * LINE_PX):
        if not left.any():
            break
        for n in layers:
            alpha[n] = grow(alpha[n], 1)
            took = alpha[n] & left
            owners[n] |= took
            left &= ~took
    return owners


def gaps_of(canvas):
    """Transparent pixels inside the object's outline (gaps up to 2 * LINE_PX closed), and the object's area. Found
    on a half-size copy (a pose has dozens of frames; the full-size closing took a second each), then scaled back.
    """
    W, H = canvas.size
    a = np.asarray(canvas.getchannel("A").reduce(2)) > 40
    closed = ~grow(~grow(a, LINE_PX // 2), LINE_PX // 2)
    gaps = (closed & ~a).repeat(2, 0).repeat(2, 1)
    full = np.zeros((H, W), bool)
    full[: gaps.shape[0], : gaps.shape[1]] = gaps[:H, :W]
    return full & (np.asarray(canvas)[:, :, 3] <= 40), int(a.sum()) * 4


def cmd_pose(a):
    manifest = os.path.join(a.out, "layers", "manifest.json")
    try:
        man = json.load(open(manifest, encoding="utf-8"))
    except (OSError, ValueError) as e:
        sys.exit(f"pose: {manifest}: {e} (run layers first)")
    W, H = man["size"]
    layers = {
        row["name"]: dict(
            row,
            image=Image.open(os.path.join(a.out, "layers", row["file"])).convert(
                "RGBA"
            ),
        )
        for row in man["layers"]
    }
    spec = load_motion(a.motion, list(layers))
    view = spec.get("view")
    if view:
        x0, y0 = max(0, int(view[0])), max(0, int(view[1]))
        x1, y1 = min(W, int(view[2])), min(H, int(view[3]))
        if x0 >= x1 or y0 >= y1:
            sys.exit(f"pose: view {view} is outside the {W}x{H} picture")
        inside = np.zeros((H, W), bool)
        inside[y0:y1, x0:x1] = True
    rest_gaps, area = gaps_of(pose_frame(layers, spec, [], 0, (W, H))[0])
    owners = rest_gap_owners(layers, rest_gaps, (W, H))
    os.makedirs(os.path.join(a.out, "poses"), exist_ok=True)
    scale = min(1.0, 768 / max(W, H))
    report = {}
    for clip in spec["clips"]:
        keys, fps = clip["keys"], float(clip.get("fps", 20))
        t0, t1 = keys[0]["t"], keys[-1]["t"]
        n = max(2, int(round((t1 - t0) * fps)) + 1)
        frames, worst = [], (-1, 0.0, None, None)
        for i in range(n):
            t = t0 + (t1 - t0) * i / (n - 1)
            cv, world = pose_frame(layers, spec, keys, t, (W, H))
            carried = np.zeros((H, W), bool)
            for name, own in owners.items():
                if own.any():
                    carried |= moved_mask(own, world[name])
            if view:
                # A camera's frame must be filled: every transparent pixel in it is a gap.
                gaps = inside & (np.asarray(cv)[:, :, 3] <= 40)
            else:
                gaps = gaps_of(cv)[0] & ~grow(carried, 1)
            if gaps.sum() > worst[0]:
                worst = (int(gaps.sum()), t, cv, gaps)
            bg = Image.new("RGBA", (W, H), (205, 205, 210, 255))
            bg.alpha_composite(cv)
            if view:
                bg = bg.crop((x0, y0, x1, y1))
            frames.append(
                bg.convert("RGB").resize(
                    (int(bg.width * scale), int(bg.height * scale)), Image.LANCZOS
                )
            )
        gif = os.path.join(a.out, "poses", f"{clip['name']}.gif")
        # One palette for the whole clip, undithered: a palette per frame, dithered, makes still areas (a sky's
        # gradient) shimmer from frame to frame, which reads as the layers flickering.
        # Its colours from frames across the whole clip: one frame alone misses parts that leave or arrive.
        picks = frames[:: max(1, len(frames) // 8)]
        sheet_ = Image.new("RGB", (picks[0].width, picks[0].height * len(picks)))
        for i, f in enumerate(picks):
            sheet_.paste(f, (0, i * f.height))
        pal = sheet_.quantize(256, method=Image.Quantize.MEDIANCUT)
        frames = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
        frames[0].save(
            gif,
            save_all=True,
            append_images=frames[1:],
            duration=int(1000 / fps),
            loop=0,
        )
        shot = Image.new("RGBA", (W, H), (205, 205, 210, 255))
        shot.alpha_composite(worst[2])
        px = np.asarray(shot).copy()
        px[worst[3]] = (255, 0, 255, 255)
        if view:
            px = px[y0:y1, x0:x1]
        gap_png = os.path.join(a.out, "poses", f"{clip['name']}-gaps.png")
        Image.fromarray(px, "RGBA").save(gap_png)
        report[clip["name"]] = {
            "gif": gif,
            "frames": n,
            "mostGapPx": worst[0],
            "gapShare": round(worst[0] / max(1, area), 4),
            "atT": round(worst[1], 3),
            "gaps": gap_png,
        }
    print(json.dumps({"restGapPx": int(rest_gaps.sum()), "clips": report}))


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("masks")
    for arg in ("--image", "--map", "--parts", "--out"):
        m.add_argument(arg, required=True)
    lp = sub.add_parser("layers")
    for arg in ("--image", "--parts", "--out"):
        lp.add_argument(arg, required=True)
    lp.add_argument(
        "--fill",
        action="append",
        help="<occluder part>=<in-paint file>, one per part that hides another",
    )
    pp = sub.add_parser("pose")
    for arg in ("--out", "--motion"):
        pp.add_argument(arg, required=True)
    a = ap.parse_args()
    {"masks": cmd_masks, "layers": cmd_layers, "pose": cmd_pose}[a.cmd](a)


if __name__ == "__main__":
    main()
