#!/usr/bin/env python3
"""Free local steps of sequences/portrait-to-layers.md: a character portrait cut into named transparent layers.

Pillow and NumPy only. Every file it writes goes under --out; it reads only the files it is given.

  crop    --portrait P --map MAP --out D
          The face close-up the second colour map is drawn on: D/face-crop.png (square, 1024 px) and D/crop.json.
  masks   --portrait P --map MAP --face-map FACE_MAP --out D
          Merges the two maps into D/labels.png (one colour per part, what the cut uses), and writes the in-paint
          masks for the `mask` input (transparent = repainted, opaque = kept, the portrait's size): D/mask-face.png
          (the front hair), D/mask-eyes.png (for gaze), and the back-hair fallback's D/mask-backhair.png (the head)
          and D/mask-locks.png (the locks below it).
  layers  --portrait P --out D [--face-fill F] (--back-hair WHOLE | [--hair-fill B] [--locks-fill K])
          --back-hair is a picture of the whole back hair alone; the two fills are its fallback, never with it. A fill
          is left out only when masks said that in-paint is skipped. Cuts D/layers/<z>-<name>.png and
          D/layers/manifest.json (name, file, x, y, w, h, z; z 0 is the bottom), writes D/recomposed.png and
          D/layers-sheet.png (every layer, and the hair moved), and prints the recompose check as one JSON line. Run gaze and expressions again when it lists them in runAgain.
  gaze    --portrait P --out D --iris-fill I
          Completes each iris from the in-paint over D/mask-eyes.png and adds the eye opening as the irises' clip.
  expressions --portrait P --out D --variant mouth:<name>=<file> ... --variant eyes:<name>=<file> ...
          Cuts swap layers from edits of the portrait into D/layers/expressions/, listed under `swaps`.
  rig     --portrait P --out D
          D/character.psb (every layer at its place; each swap group's variants as hidden layers, its neutral an
          empty visible one; after gaze, the irises kept inside the eye opening, the whole irises as a hidden
          IridesWhole layer, and the opening as a hidden IridesClip layer for a Sprite Mask) and D/character.psb.json, the
          sidecar a rig script written from sequences/rig-2d-snippets.md reads in a Unity project: bones placed from the labels, the hair
          banded onto them, the swaps as categories.
"""

import argparse
import json
import os
import re
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

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

# The colour of each part in the maps the prompts ask for. Order is the label index.
PALETTE = {
    "back_hair": (0, 0, 255),
    "front_hair": (0, 255, 255),
    "face": (255, 255, 0),
    "neck": (255, 128, 0),
    "brows": (255, 0, 255),
    "eye_whites": (255, 255, 255),
    "irides": (0, 255, 0),
    "eyelines": (255, 0, 0),
    "mouth": (128, 0, 0),
    "body": (128, 128, 128),
    "background": (0, 0, 0),
}
NAMES = list(PALETTE)
FACE_DETAIL = ("brows", "eye_whites", "irides", "eyelines", "mouth")
CROP_SIDE = 1024
GROW_PX = 3  # a mask is grown this far past its part, so the in-paint covers the anti-aliased edge


def labels_of(map_path, size, scale=False):
    """Each pixel of a colour map to its nearest palette colour. Only the face close-up's map is scaled (`scale`): its
    square is scaled back to its box; every other map must be the portrait's size."""
    im = Image.open(map_path).convert("RGB")
    if scale and im.size != size and im.size[0] == im.size[1]:
        im = im.resize(
            size, Image.NEAREST
        )  # a square close-up, at another square size: same outlines
    same_size(map_path, im, size)
    px = np.asarray(im).astype(np.int32)
    cols = np.array([PALETTE[n] for n in NAMES])
    best = np.zeros(px.shape[:2], np.int64)
    best_d = np.full(px.shape[:2], np.iinfo(np.int64).max)
    for i, c in enumerate(
        cols
    ):  # one colour at a time: a full-size image stays within memory
        d = ((px - c) ** 2).sum(-1)
        closer = d < best_d
        best[closer], best_d[closer] = i, d[closer]
    return best


def near(img, ref_mask, tol):
    """Pixels of img within tol of img's median colour under ref_mask."""
    if not ref_mask.any():
        return np.zeros(img.shape[:2], bool)
    med = np.median(img[ref_mask][:, :3], axis=0)
    return np.abs(img[:, :, :3] - med).max(-1) < tol


def bbox(mask):
    ys, xs = np.nonzero(mask)
    return (
        (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
        if len(xs)
        else None
    )


def save_labels(labels, path):
    cols = np.array([PALETTE[n] for n in NAMES], np.uint8)
    Image.fromarray(cols[labels], "RGB").save(path)


MIN_BACK_HAIR = 0.002  # of the canvas: a back hair smaller than this is map noise (an anti-aliased front-hair edge)


MIN_LOCKS = 0.01  # of the canvas: front locks below the head smaller than this do not get their own in-paint


def back_hair_inpaint(L, hid_hair):
    """Whether the back-hair in-paint can add anything: the fill is matched against the back hair its mask leaves
    visible, so it needs some of it, more than noise."""
    visible = L["back_hair"] & ~hid_hair
    return bool(visible.sum() > MIN_BACK_HAIR * visible.size)


def attached(candidates, to):
    """The 4-connected parts of `candidates` that touch `to`: a patch that only reaches the part through another
    candidate pixel still counts, one that floats apart from it does not."""
    edge = grow(to, 1)
    out = np.zeros(candidates.shape, bool)
    for part in components(candidates):
        if edge.ravel()[part].any():
            out.ravel()[part] = True
    return out


ORNAMENT_MIN_PX = 20  # below this, an enclosed back-hair patch is an anti-aliased edge speck, left to despeckle
ORNAMENT_MAX = 0.005  # of the canvas: larger than any hair clip or ribbon on the bangs
ORNAMENT_COLOUR = 60  # how far (0-255, per channel) an ornament's colour sits from the visible back hair's


def enclosed_back_hair(labels, portrait):
    """A small patch of back hair the front hair surrounds, in a colour unlike the back hair's, is a hair ornament on
    the bangs that the map drew in the back hair's colour: it becomes front hair, so it moves with the bangs. A patch
    in the back hair's own colour is back hair seen through a gap between strands, and stays. Returns the labels and
    the pixels moved.

    Only the back hair the front hair encloses is searched: a flood from the canvas edge through everything that is
    not front hair marks the rest, so the large back hair costs no per-pixel search."""
    bh, fh = NAMES.index("back_hair"), NAMES.index("front_hair")
    H, W = labels.shape
    mask = labels == bh
    passable = labels != fh
    reached = np.zeros_like(passable)
    reached[0, :], reached[-1, :], reached[:, 0], reached[:, -1] = (
        passable[0, :],
        passable[-1, :],
        passable[:, 0],
        passable[:, -1],
    )
    while True:
        step = reached | (
            (
                shifted(reached, 1, 0)
                | shifted(reached, -1, 0)
                | shifted(reached, 0, 1)
                | shifted(reached, 0, -1)
            )
            & passable
        )
        if (step == reached).all():
            break
        reached = step
    enclosed = mask & ~reached
    hair = (
        np.median(portrait[mask & reached][:, :3], axis=0)
        if (mask & reached).any()
        else None
    )
    flat = labels.ravel().copy()
    moved = 0
    for part in components(enclosed):
        if not ORNAMENT_MIN_PX <= len(part) <= ORNAMENT_MAX * labels.size:
            continue
        colour = np.median(portrait.reshape(-1, portrait.shape[2])[part][:, :3], axis=0)
        if hair is not None and np.abs(colour - hair).max() < ORNAMENT_COLOUR:
            continue  # back hair through a gap in the bangs
        flat[part] = fh
        moved += len(part)
    return flat.reshape(H, W), moved


SPECK_PX = 40  # a part smaller than this is a map's edge pixel (red eye line into yellow skin reads as orange neck)


def despeckle(labels):
    """A small stray part of the body, neck, face or hair (an anti-aliased edge between two map colours read as a
    third part: a red eye line into yellow skin reads as orange neck) joins the part around it most. Each part is
    flooded whole (8-connected) before it is judged; a label's largest part is never merged, nor are the face
    details (eye lines, mouth, brows... are thin by nature), and the vote leaves the background out, so no visible
    pixel loses its layer. The masks are not touched: the in-paints were painted for them. Returns the labels and the
    pixels moved.

    Only pixels away from any 7x7 solid block of their own label are flooded: a part with such a block is never a
    speck, so the large parts cost no per-pixel search."""
    H, W = labels.shape
    flat = labels.ravel().copy()
    moved = 0
    bg = NAMES.index("background")
    steps = [(dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx]
    for i, name in enumerate(NAMES):
        if name == "background" or name in FACE_DETAIL:
            continue
        mask = labels == i
        solid = (
            np.asarray(
                Image.fromarray((mask * 255).astype(np.uint8)).filter(
                    ImageFilter.MinFilter(7)
                )
            )
            > 127
        )
        big = (grow(solid, 3) & mask).ravel()
        todo = (mask.ravel() & ~big).copy()
        parts = []
        for start in np.flatnonzero(todo):
            if not todo[start]:
                continue
            todo[start] = False
            stack, part, touches_big = [start], [], False
            while stack:
                k = stack.pop()
                part.append(k)
                y, x = divmod(k, W)
                for dy, dx in steps:
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < H and 0 <= xx < W:
                        j = yy * W + xx
                        if big[j]:
                            touches_big = True
                        elif todo[j]:
                            todo[j] = False
                            stack.append(j)
            if not touches_big:
                parts.append(part)
        if not big.any() and parts:
            parts.remove(
                max(parts, key=len)
            )  # the label's largest part is the part itself
        for part in parts:
            if len(part) >= SPECK_PX:
                continue
            idx = np.array(part)
            ys, xs = idx // W, idx % W
            ny = (ys[:, None] + np.array([d[0] for d in steps])).ravel()
            nx = (xs[:, None] + np.array([d[1] for d in steps])).ravel()
            ok = (ny >= 0) & (ny < H) & (nx >= 0) & (nx < W)
            around = flat[ny[ok] * W + nx[ok]]
            around = around[(around != i) & (around != bg)]
            if len(around):
                flat[idx] = np.bincount(around).argmax()
                moved += len(part)
    # A face detail (eye line, mouth, brow...) far from the face is an anti-aliased hair edge read as that colour:
    # left as is, it is a dot that stays behind on the clothes when the hair moves. It joins the part around it.
    face = flat.reshape(H, W) == NAMES.index("face")
    if face.any():
        fx0, fy0, fx1, fy1 = bbox(main_parts(face, 0.5))
        pad_x, pad_y = (fx1 - fx0) // 5, (fy1 - fy0) // 5
        zone = np.zeros((H, W), bool)
        zone[
            max(fy0 - pad_y, 0) : fy1 + pad_y, max(fx0 - pad_x, 0) : fx1 + pad_x
        ] = True
        zone = zone.ravel()
        details = [NAMES.index(k) for k in FACE_DETAIL]
        for i in details:
            for part in components(flat.reshape(H, W) == i):
                idx = np.array(part)
                if zone[idx].any():
                    continue
                ys, xs = idx // W, idx % W
                ny = (ys[:, None] + np.array([d[0] for d in steps])).ravel()
                nx = (xs[:, None] + np.array([d[1] for d in steps])).ravel()
                ok = (ny >= 0) & (ny < H) & (nx >= 0) & (nx < W)
                around = flat[ny[ok] * W + nx[ok]]
                around = around[(around != bg) & ~np.isin(around, details)]
                if len(around):
                    flat[idx] = np.bincount(around).argmax()
                    moved += len(part)
    return flat.reshape(H, W), moved


FLAT_FILL = 0.4  # an in-paint whose masked area is mostly one colour ...
FOREIGN = 48  # ... that no visible part of the character has (0-255 a channel) painted a blank, not what lies hidden


def blank_fill(fill, area, orig, L, extra=()):
    """The share of `area` the fill's most common colour takes, when that colour is far from every visible part's
    colour or the visible background's (a black blank on a pink-haired character on a light background), else 0. The
    background counts: behind a lock that hangs over it, the background is what an in-paint should paint. Cel shading is flat too, so flatness alone cannot
    tell; a blank in the character's own colour (black on black hair) is not caught."""
    if not area.any():
        return 0.0
    px = fill[:, :, :3][area]
    q = (px // 32).astype(np.int32)
    keys = q[:, 0] * 64 + q[:, 1] * 8 + q[:, 2]
    top = np.bincount(keys).argmax()
    share = float((keys == top).mean())
    colour = px[keys == top].mean(0)
    refs = [
        np.median(orig[:, :, :3][L[n] & ~area], axis=0)
        for n in ("back_hair", "front_hair", "face", "body", "background")
        + tuple(extra)
        if (L[n] & ~area).sum() > 100
    ]
    if share > FLAT_FILL and all(np.abs(colour - r).max() > FOREIGN for r in refs):
        return share
    return 0.0


def eyes_mask(L):
    """The gaze in-paint's mask: each eye's eye-white, iris and eye-line area, its box grown a third of its height
    upward (the iris's hidden top) and a quarter down, minus the front hair."""
    H, W = L["face"].shape
    eyes = main_parts(L["eye_whites"] | L["irides"] | L["eyelines"])
    mask = np.zeros((H, W), bool)
    for part in components(eyes):
        if len(part) < 0.1 * eyes.sum() / 2:
            continue
        ys, xs = np.divmod(np.array(part), W)
        x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
        h = y1 - y0 + 1  # y1 is inclusive
        mask[max(y0 - h // 3, 0) : y1 + 1 + h // 4, x0 : x1 + 1] = True
    return mask & ~L["front_hair"]


def head_bottom(L):
    """The lowest row of the face and neck (their main shapes: a stray neck-coloured pixel at the hem would make the
    whole picture "head"): below it the body covers the back hair anyway."""
    box = bbox(main_parts(L["face"] | L["neck"], 0.2))
    return box[3] if box else 0


def cmd_crop(a):
    W, H = Image.open(a.portrait).size
    labels = labels_of(a.map, (W, H))
    # The face's skin only: a white collar or ribbon can carry the eye whites' colour in a full-body map.
    box = bbox(labels == NAMES.index("face"))
    if box is None:
        sys.exit(
            "crop: the map has no face (yellow) region; look at the map and redraw it before going on"
        )
    x0, y0, x1, y1 = box
    side = int(max(x1 - x0, y1 - y0) * 1.25)
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2 - (
        y1 - y0
    ) // 10  # a little up: the brows sit under the bangs
    side = min(side, W, H)
    left = min(max(cx - side // 2, 0), W - side)
    top = min(max(cy - side // 2, 0), H - side)
    crop = (left, top, left + side, top + side)
    Image.open(a.portrait).convert("RGB").crop(crop).resize(
        (CROP_SIDE, CROP_SIDE), Image.LANCZOS
    ).save(os.path.join(a.out, "face-crop.png"))
    json.dump(
        {"box": crop, "side": CROP_SIDE}, open(os.path.join(a.out, "crop.json"), "w")
    )
    print(json.dumps({"faceCrop": os.path.join(a.out, "face-crop.png"), "box": crop}))


def cmd_masks(a):
    W, H = Image.open(a.portrait).size
    labels = labels_of(a.map, (W, H))
    crop = json.load(open(os.path.join(a.out, "crop.json")))["box"]
    x0, y0, x1, y1 = crop
    face_labels = labels_of(a.face_map, (CROP_SIDE, CROP_SIDE), scale=True)
    face_labels = np.asarray(
        Image.fromarray(face_labels.astype(np.uint8)).resize(
            (x1 - x0, y1 - y0), Image.NEAREST
        )
    ).astype(np.int64)
    # The close-up wins inside its box, except where it says background ("everything else" in its prompt): there the
    # full map keeps its body or ribbon, and a face detail the full map put there becomes body.
    region = labels[y0:y1, x0:x1]
    bg = NAMES.index("background")
    region = np.where(face_labels != bg, face_labels, region)
    stray = np.isin(region, [NAMES.index(n) for n in FACE_DETAIL]) & (face_labels == bg)
    region[stray] = NAMES.index("body")
    labels[y0:y1, x0:x1] = region
    labels, moved = enclosed_back_hair(labels, load_rgba(a.portrait))
    save_labels(labels, os.path.join(a.out, "labels.png"))
    L = {n: labels == i for i, n in enumerate(NAMES)}
    above = np.arange(H)[:, None] < head_bottom(L)

    def save_mask(edit, name):
        rgba = np.zeros((H, W, 4), np.uint8)
        rgba[:, :, 3] = np.where(edit, 0, 255)
        Image.fromarray(rgba, "RGBA").save(os.path.join(a.out, name))
        return int(edit.sum())

    head = L["face"] | L["neck"] | L["front_hair"]
    for n in FACE_DETAIL:
        head |= L[n]
    # The back hair is painted behind the head, and, in a call of its own, behind the front locks below it: when a
    # lock swings, more hair shows behind it, not the background. One mask for both came back painted flat black
    # twice on a character with long twin tails; the locks alone worked. (The body layer stays in front.)
    face_edit = grow(L["front_hair"], GROW_PX)
    hair_edit = grow(head & above, GROW_PX)
    locks_edit = grow(L["front_hair"] & ~above, GROW_PX)
    # An empty back-hair mask would be paid for and change nothing: stop before anything is written or quoted. An
    # empty face mask is a character with no front hair: its in-paint is skipped (`faceInpaint` false).
    if not hair_edit.any():
        sys.exit(
            "masks: the back-hair mask is empty (no face or neck in labels.png); look at the maps before quoting "
            "the in-paints"
        )
    out = {
        "labels": os.path.join(a.out, "labels.png"),
        "maskFace": save_mask(face_edit, "mask-face.png"),
        "maskBackHair": save_mask(hair_edit, "mask-backhair.png"),
        "maskLocks": save_mask(locks_edit, "mask-locks.png"),
        "maskEyes": save_mask(eyes_mask(L), "mask-eyes.png"),
        # Locks below the head worth a call: a few strands are left to the face in-paint's fill.
        "locksInpaint": bool(locks_edit.sum() > MIN_LOCKS * locks_edit.size),
        "faceInpaint": bool(face_edit.any()),
        "ornamentsMoved": moved,
        # No visible back hair: nothing to match a back-hair repaint against, so it would be paid for nothing.
        "backHairInpaint": back_hair_inpaint(L, hair_edit),
        "parts": {n: int(L[n].sum()) for n in NAMES if n != "background"},
    }
    print(json.dumps(out))


WHOLE_HAIR_MIN = (
    12  # 0-255 a channel: a pixel this close to the picture's background is background
)
WHOLE_HAIR_COVER = 0.7  # the share of the top third of the hair outline the picture must fill (else it is shifted)
WHOLE_HAIR_BG = 40  # 0-255: a border pixel this far from the hair's colour counts toward the picture's background


def whole_back_hair(path, L, orig, W, H):
    """The back-hair layer from a picture of the whole back hair alone (an edit of the portrait with everything else
    taken away, lined up with it): uncut, it reaches behind the head, the body and every lock, so a sway or a head
    turn never shows an end. The picture is the layer's colour everywhere; only thin strands of the portrait's back
    hair outside its outline keep the portrait's pixels."""
    full = load_rgba(path, (W, H))
    hair_ref = L["back_hair"]
    if not hair_ref.any():
        sys.exit(
            "layers: --back-hair needs some visible back hair in the maps to tell hair from background"
        )
    hair_colour = np.median(full[:, :, :3][hair_ref], axis=0)
    # The background: the picture's border pixels that are not nearer the hair (hair can reach a corner).
    border = np.zeros((H, W), bool)
    border[:12, :], border[-12:, :], border[:, :12], border[:, -12:] = (
        True,
        True,
        True,
        True,
    )
    to_hair = np.abs(full[:, :, :3] - hair_colour).max(-1)
    cand = border & (to_hair > WHOLE_HAIR_BG)
    bg = np.median(full[:, :, :3][cand if cand.any() else border], axis=0)
    to_bg = np.abs(full[:, :, :3] - bg).max(-1)
    # The hair's colours, shadow to highlight: the picture's own pixels inside the portrait's hair outline that are off
    # its background, in five bands of lightness. One colour, the visible back hair's (often its shadowed underside),
    # left a shaded pastel hair's highlights nearer a light grey background than that shadow: hair read as background.
    sample = (L["front_hair"] | L["back_hair"]) & (to_bg > WHOLE_HAIR_MIN)
    colours = [hair_colour]
    if sample.sum() >= 50:
        px = full[:, :, :3][sample]
        for band in np.array_split(px[np.argsort(px.mean(-1))], 5):
            colours.append(np.median(band, axis=0))
    to_hair = np.min([np.abs(full[:, :, :3] - c).max(-1) for c in colours], axis=0)
    # Hair: nearer one of the hair's colours than the background's, and off the background. Pastel, silver or white hair on
    # a light background is told apart by which colour a pixel is nearer, not by how far it is from the background.
    hair = (to_hair < to_bg) & (to_bg > WHOLE_HAIR_MIN)
    if (
        full[:, :, 3] < 250
    ).any():  # a transparent result: its alpha says where the hair is
        hair &= full[:, :, 3] > 127
    # A lone faint wisp far from solid hair is the background showing through: a pale ghost strand once it moves.
    hair &= grow(hair & ~grow(~hair, 2), 4)
    # Lined up: the back hair sits behind the whole head of hair, so it must fill the top third of the portrait's
    # hair outline (front and back hair). Measured against the visible back hair alone, a short-haired character's
    # few slivers below the ears passed a picture 100 px too low and refused a good one.
    outline = L["front_hair"] | L["back_hair"]
    ox0, oy0, ox1, oy1 = bbox(outline)
    crown = outline & (np.arange(H)[:, None] < oy0 + (oy1 - oy0) // 3)
    covered = (hair & crown).sum() / max(1, crown.sum())
    if covered < WHOLE_HAIR_COVER:
        sys.exit(
            f"layers: the --back-hair picture fills {covered:.0%} of the top of the portrait's hair (shifted, or hair "
            "it does not tell from its background): redo it, or use the --hair-fill and --locks-fill fallback"
        )
    # De-fringe its edge: an edge pixel lighter than the hair just inside it is blended with the background.
    inner = hair & ~grow(~hair, 3)
    if inner.any():
        inside = spread(full, inner, hair & ~inner, 4)
        pale = (
            hair & ~inner & (full[:, :, :3].mean(-1) > inside[:, :, :3].mean(-1) + 12)
        )
        full = np.where(pale[..., None], inside, full)
    blank = blank_fill(full, hair & ~L["back_hair"], orig, L)
    if blank:
        sys.exit(
            f"layers: the --back-hair picture is {blank:.0%} one colour, a blank: redo it"
        )
    # A thin strand of the portrait's back hair just outside the generated outline is real hair the picture left
    # out: it keeps the portrait's colour (the picture's own there is its background, a pale ghost strand).
    outside = L["back_hair"] & ~hair
    return (
        "back_hair",
        hair | L["back_hair"],
        np.where(outside[..., None], orig, full),
        False,
    )


def painted_background(fill, bg_ref, body_ref):
    """Where an in-paint painted background: close to the background's colour and nearer it than the clothes' (white
    clothes on a white background stay clothes), and joined to the background the portrait shows. Shaded cream knit
    can sit as close to a light grey background as to the clothes; a patch of it enclosed by the clothes is clothes.
    """
    if bg_ref.any() and body_ref.any():
        to_bg = np.abs(fill[:, :, :3] - np.median(fill[:, :, :3][bg_ref], axis=0)).max(
            -1
        )
        to_body = np.abs(
            fill[:, :, :3] - np.median(fill[:, :, :3][body_ref], axis=0)
        ).max(-1)
        looks = (to_bg < 20) & (to_bg < to_body)
    else:
        looks = near(fill, bg_ref, 20)
    return (looks & bg_ref) | attached(looks & ~bg_ref, bg_ref)


def nearer_hair(fill, orig, L, body_ref):
    """Where `fill` is nearer the hair's colour than the clothes': the hair as the portrait shows it (front and back,
    whichever is nearer, so the darker back of the head counts too) against the clothes the in-paint left visible.
    """
    if not body_ref.any():
        return np.zeros(fill.shape[:2], bool)
    to_body = np.abs(fill[:, :, :3] - np.median(fill[:, :, :3][body_ref], axis=0)).max(
        -1
    )
    to_hair = np.full(fill.shape[:2], np.inf)
    for part in ("front_hair", "back_hair"):
        if L[part].any():
            ref = np.median(orig[:, :, :3][L[part]], axis=0)
            to_hair = np.minimum(to_hair, np.abs(fill[:, :, :3] - ref).max(-1))
    return to_hair < to_body


def build_stack(a, W, H, L, orig, raw_back_hair):
    """The layers bottom to top, as (name, mask, colour, colour is the portrait), and the counts the check reports.
    `raw_back_hair`: the back hair of labels.png before despeckle, the one `masks` decided backHairInpaint on.
    """
    hid_face = (
        np.asarray(Image.open(os.path.join(a.out, "mask-face.png")))[:, :, 3] == 0
    )
    hid_hair = (
        np.asarray(Image.open(os.path.join(a.out, "mask-backhair.png")))[:, :, 3] == 0
    )
    # A fill left out is allowed only where masks said that in-paint is skipped: otherwise the part it fills (the
    # forehead under the bangs, the back of the head) would be a hole that the parts above hide from the checks.
    if hid_face.any() and not a.face_fill:
        sys.exit(
            "layers: mask-face.png hides the face under the front hair, and no --face-fill was given; run the face "
            "in-paint (masks said faceInpaint true) and pass its file"
        )
    # Decided on the labels masks saw, not the despeckled ones: a speck merged into the back hair must not ask
    # for an in-paint masks said adds nothing.
    if (
        back_hair_inpaint({"back_hair": raw_back_hair}, hid_hair)
        and not a.hair_fill
        and not a.back_hair
    ):
        sys.exit(
            "layers: the maps have back hair, and no --hair-fill was given; run the back-hair in-paint (masks said "
            "backHairInpaint true) and pass its file"
        )
    locks_path = os.path.join(a.out, "mask-locks.png")
    if a.back_hair:
        locks_path = (
            ""  # the whole back hair covers what the locks in-paint would paint
        )
    hid_locks = (
        np.asarray(Image.open(locks_path))[:, :, 3] == 0
        if os.path.exists(locks_path)
        else np.zeros((H, W), bool)
    )
    if hid_locks.sum() > MIN_LOCKS * hid_locks.size and not a.locks_fill:
        sys.exit(
            "layers: mask-locks.png covers long front locks, and no --locks-fill was given; run the locks in-paint "
            "(masks said locksInpaint true) and pass its file"
        )
    face_fill = load_rgba(a.face_fill, (W, H)) if a.face_fill else orig
    hair_fill = load_rgba(a.hair_fill, (W, H)) if a.hair_fill else orig
    locks_fill = load_rgba(a.locks_fill, (W, H)) if a.locks_fill else orig
    for fill, hid, name in (
        (face_fill, hid_face, "--face-fill"),
        (hair_fill, hid_hair, "--hair-fill"),
        (locks_fill, hid_locks, "--locks-fill"),
    ):
        blank = blank_fill(fill, hid, orig, L) if fill is not orig else 0.0
        if blank:
            sys.exit(
                f"layers: the {name} in-paint painted {blank:.0%} of its mask one colour that neither the character nor the background has, "
                "a blank, not what lies hidden: redo that in-paint (the checks cannot see it once "
                "the parts above cover it)"
            )
    hid_face &= bool(a.face_fill)
    hid_hair &= bool(a.hair_fill)
    hid_locks &= bool(a.locks_fill)
    skin = L["face"] | L["neck"]
    above = np.arange(H)[:, None] < head_bottom(L)
    # An in-paint is used only where its mask hid something and only where it painted that part's colour: it
    # re-renders the rest of the picture too, a few percent of pixels off.
    face_hidden = hid_face & ~skin & near(face_fill, skin & ~hid_face, 28) & above
    # Never below the chin: under long locks at the shoulders the in-paint paints clothes, and a cream cardigan passes
    # the skin test; taken as face, it would turn with the head and leave holes in the body under the locks.
    if L["face"].any():
        face_hidden &= np.arange(H)[:, None] <= np.nonzero(L["face"].any(1))[0].max()
    # Above the hairline the in-paint paints background; light skin can sit within the skin test of a light grey
    # background, so a painted pixel nearer the background's colour than the skin's is not face (pale wisps above
    # the head once the hair moves).
    if (L["background"] & ~hid_face).any() and (skin & ~hid_face).any():
        bg_c = np.median(face_fill[:, :, :3][L["background"] & ~hid_face], axis=0)
        skin_c = np.median(face_fill[:, :, :3][skin & ~hid_face], axis=0)
        to_bg_f = np.abs(face_fill[:, :, :3] - bg_c).max(-1)
        to_skin_f = np.abs(face_fill[:, :, :3] - skin_c).max(-1)
        # Background only when close to it and nearer it than the skin: with pale skin on a light background a
        # bare "nearer" would drop real forehead under the bangs on noise.
        face_hidden &= ~((to_bg_f < 20) & (to_bg_f < to_skin_f))
    hair_hidden = (
        hid_hair & ~L["back_hair"] & near(hair_fill, L["back_hair"] & ~hid_hair, 70)
    )
    # Strands too thin for the colour map: off-skin pixels inside the skin that the face in-paint paints as skin. They
    # join the front hair, and the face takes the in-paint under them.
    strands = (
        skin
        & hid_face  # only under the front hair's mask: blush and shading elsewhere stay in the skin
        & ~near(orig, skin, 25)
        & (np.abs(orig[:, :, :3] - face_fill[:, :, :3]).max(-1) > 30)
    )
    face_from_fill = face_hidden | strands
    # Long front strands also cover the clothes and the back hair below the head. The face in-paint repainted all
    # that its mask hid, so the body and the back hair take from it what it painted in their colour there; without
    # it, moving a strand shows a hole.
    # Only where the front hair itself lies (not the 3 px its mask grows onto the background). A painted pixel is
    # background only when it is close to the background's colour and nearer it than the clothes' (white clothes on
    # a white background stay clothes). The body may lie over back hair: it is drawn above it.
    bg_ref, body_ref = L["background"] & ~hid_face, L["body"] & ~hid_face
    under_strands = (
        hid_face & L["front_hair"] & ~painted_background(face_fill, bg_ref, body_ref)
    )
    # Joined to the visible body, however far a wide lock reaches over the clothes (a fixed reach from the body's
    # outline left square holes under long locks, which show once they move); not by height, as shoulders can rise
    # above the chin's row. Never what is nearer the hair's colour than the clothes': joined through a strand at the
    # collar, dark hair painted behind the bangs would otherwise pass for a dark jacket and take the whole head.
    body_hidden = attached(
        under_strands
        & ~L["body"]
        & ~skin
        & ~face_hidden
        & near(face_fill, body_ref, 40)
        & ~nearer_hair(face_fill, orig, L, body_ref),
        L["body"],
    )
    # Knit or cloth shading can sit outside the colour test, leaving pin holes in the body behind a strand that show
    # the back hair once the strand moves: close the body's small holes under the strands from the same in-paint.
    body_now = L["body"] | body_hidden
    # Padded with its own edge rows, so a hole that touches the bottom of the picture closes too.
    padded = np.pad(body_now, 13, mode="edge")
    closed = (~grow(~grow(padded, 12), 12))[13:-13, 13:-13]
    body_hidden |= (
        closed & ~body_now & hid_face & L["front_hair"] & ~skin & ~above
    )  # inside the body: never background
    low_hair = (
        under_strands
        & ~above
        & ~L["back_hair"]
        & ~hair_hidden
        & ~body_hidden
        & near(face_fill, L["back_hair"] & ~hid_face, 70)
    )
    # The locks in-paint: the back hair behind the locks, and the clothes where they crossed them. It wins over the
    # face in-paint there, which only painted what it could see behind the strands.
    lock_area = hid_locks & L["front_hair"] & ~above
    locks_hair = (
        lock_area
        & ~L["back_hair"]
        & near(locks_fill, L["back_hair"] & ~hid_hair & ~hid_locks, 70)
    )
    # As for the strands: never a repainted background (a white one passes for cream clothes), and next to the body.
    locks_bg = painted_background(
        locks_fill, L["background"] & ~hid_locks, L["body"] & ~hid_locks
    )
    locks_body = attached(
        lock_area
        & ~L["body"]
        & ~locks_hair
        & ~locks_bg
        & near(locks_fill, L["body"] & ~hid_locks, 40),
        L["body"] | body_hidden,
    )
    low_hair &= ~locks_hair & ~locks_body
    body_hidden = (body_hidden & ~locks_hair) | locks_body
    hair_colour = np.where(
        hair_hidden[..., None],
        hair_fill,
        np.where(
            locks_hair[..., None],
            locks_fill,
            np.where(low_hair[..., None], face_fill, orig),
        ),
    )
    # The jaw's outline is the face's: the map can give the line where face meets neck to the neck, and a head turn
    # then leaves a copy of it on the neck. Dark line art of the neck along the face goes to the face, and the neck
    # takes its own skin colour there from its nearest pixels, so nothing shows under the face as it turns.
    neck = L["neck"] & ~strands
    jaw = np.zeros(neck.shape, bool)
    if neck.any():
        lum = orig[:, :, :3].mean(-1)
        jaw = neck & grow(L["face"], 3) & (lum < np.median(lum[neck]) - JAW_LINE_DARKER)
    neck_colour = spread(orig, neck & ~jaw, jaw, 6) if jaw.any() else orig
    stack = (
        [
            (
                (
                    "back_hair",
                    L["back_hair"] | hair_hidden | low_hair | locks_hair,
                    hair_colour,
                    False,
                )
                if not a.back_hair
                else whole_back_hair(a.back_hair, L, orig, W, H)
            ),
            (
                "body",
                L["body"] | body_hidden,
                np.where(
                    locks_body[..., None],
                    locks_fill,
                    np.where(body_hidden[..., None], face_fill, orig),
                ),
                False,
            ),
            ("neck", neck, neck_colour, False),
            (
                "face",
                L["face"] | face_from_fill | jaw,
                np.where(face_from_fill[..., None], face_fill, orig),
                False,
            ),
        ]
        + [(n, L[n], orig, True) for n in ("eye_whites", "irides", "eyelines", "mouth")]
        + [
            ("front_hair", L["front_hair"] | strands, orig, True),
            # Brows last: anime brows are often drawn over the fringe, and under the hair a head turn doubles them.
            ("brows", L["brows"], orig, True),
        ]
    )
    counts = {
        "jawLineMoved": int(jaw.sum()),
        "strandsMoved": int(strands.sum()),
        "faceFilled": int(face_hidden.sum()),
        "backHairFilled": int(hair_hidden.sum() + low_hair.sum() + locks_hair.sum()),
        "bodyFilled": int(body_hidden.sum()),
    }
    return stack, counts


def shifted(a, dy, dx):
    """`a` moved by (dy, dx), the uncovered row and column zero (np.roll would wrap the opposite edge in)."""
    out = np.zeros_like(a)
    H, W = a.shape[:2]
    out[max(dy, 0) : H + min(dy, 0), max(dx, 0) : W + min(dx, 0)] = a[
        max(-dy, 0) : H + min(-dy, 0), max(-dx, 0) : W + min(-dx, 0)
    ]
    return out


# How far a layer runs under the parts above it. The back hair runs far under the body and the head: when it sways
# or the head turns, its end must stay hidden, not show as a cut edge at the shoulders.
RUN_UNDER = {"back_hair": 32}


JAW_LINE_DARKER = 50  # 0-255: a neck pixel along the face this much darker than the neck's skin is the jaw's line


def spread(colour, mask, fill, depth=GROW_PX):
    """`colour` with the pixels of `fill` taken from the nearest pixels of `mask`. The rings run through the whole band
    round `mask` (GROW_PX wide), whatever lies in it, so every band pixel is reached in at most GROW_PX rings and takes
    the colour of the layer's nearest edge; only the `fill` pixels are written. Cropped to the band, so it stays cheap.
    """
    band = grow(mask, depth) & ~mask
    write = fill & band
    if not write.any():
        return colour
    ys, xs = np.nonzero(band)
    y0, y1 = max(ys.min() - 1, 0), ys.max() + 2
    x0, x1 = max(xs.min() - 1, 0), xs.max() + 2
    rgb = colour[y0:y1, x0:x1, :3].copy()
    have = mask[y0:y1, x0:x1].copy()
    todo = band[y0:y1, x0:x1].copy()
    for _ in range(depth + 1):
        if not todo.any():
            break
        acc = np.zeros(rgb.shape, np.float32)
        n = np.zeros(rgb.shape[:2], np.float32)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dy or dx:
                    h = shifted(have, dy, dx)
                    acc += shifted(rgb, dy, dx) * h[..., None]
                    n += h
        ring = todo & (n > 0)
        rgb[ring] = acc[ring] / n[ring][:, None]
        have |= ring
        todo &= ~ring
    out = colour.copy()
    w = write[y0:y1, x0:x1]
    out[y0:y1, x0:x1, :3][w] = rgb[w]
    return out


def cut(stack, orig, out, whole_hair=False, bg=None):
    """Writes each layer cropped to its box, returns the manifest rows, the recomposed canvas and the full-size layers."""
    H, W = orig.shape[:2]
    rows, tiles = [], []
    canvas = np.zeros((H, W, 4), np.float32)
    above = [np.zeros((H, W), bool)] * len(stack)
    for z in range(len(stack) - 2, -1, -1):
        above[z] = above[z + 1] | stack[z + 1][1]
    for z, (name, mask, colour, from_orig) in enumerate(stack):
        # Only an edge onto a lower part or the background is softened. Toward the parts above it, a layer is hard and
        # runs GROW_PX under them, so their soft edge lies over an opaque one: no translucent seam between two parts.
        depth = (
            GROW_PX
            if (name == "back_hair" and whole_hair)
            else RUN_UNDER.get(name, GROW_PX)
        )
        near_above = grow(above[z], GROW_PX)
        hard = (mask & near_above) | (grow(mask, depth) & above[z])
        alpha = np.where(hard, 1.0, soften(mask)) * (
            orig[:, :, 3] / 255 if from_orig else 1
        )
        # The run-under takes the layer's own edge colour, spread outward, never the part above it: a band of front
        # hair on the face would show as soon as the hair moves.
        # A deep run-under takes its colour from a little inside the layer, not from its anti-aliased edge, which
        # carries the colour of the part it met (a cream sweater's edge on brown hair streaks it grey).
        source = mask & ~grow(~mask, 2) if depth > GROW_PX else mask
        # The run-under and the soft edge outside the mask both take the layer's own colour, never the neighbour's.
        colour = spread(colour, source, (hard | (alpha > 0)) & ~source, depth + 2)
        # De-fringe: an edge drawn onto the light background carries it, half blended, and shows as a pale ghost
        # strand once the part moves over something else. Such an edge pixel lighter than the layer just inside it
        # takes the inside colour; a dark outline (darker than inside) is line art and stays.
        if bg is not None:
            inner = mask & ~grow(~mask, 3)
            edge = mask & ~inner & grow(bg & ~mask, 3)
            if edge.any() and inner.any():
                inside = spread(colour, inner, edge, 4)
                lum_c, lum_i = colour[:, :, :3].mean(-1), inside[:, :, :3].mean(-1)
                pale = edge & (lum_c > lum_i + 12)
                colour = np.where(pale[..., None], inside, colour)
        im = Image.fromarray(
            np.dstack([colour[:, :, :3], alpha * 255]).clip(0, 255).astype(np.uint8),
            "RGBA",
        )
        box = im.getbbox()
        if box is None:
            continue
        fn = f"{z:02d}-{name}.png"
        im.crop(box).save(os.path.join(out, fn))
        rows.append(
            {
                "name": name,
                "file": fn,
                "x": box[0],
                "y": box[1],
                "w": box[2] - box[0],
                "h": box[3] - box[1],
                "z": z,
            }
        )
        fa = alpha[..., None]
        canvas[:, :, :3] = colour[:, :, :3] * fa + canvas[:, :, :3] * (1 - fa)
        canvas[:, :, 3] = alpha * 255 + canvas[:, :, 3] * (1 - alpha)
        tiles.append((name, im))
    return rows, canvas, tiles


def main_parts(mask, share=0.1):
    """`mask` without its stray bits: the parts at least `share` of its largest (an anti-aliased hair edge can read
    as a few mouth-coloured pixels anywhere on the map)."""
    parts = components(mask)
    if not parts:
        return mask
    keep = max(len(p) for p in parts) * share
    out = np.zeros(mask.size, bool)
    for p in parts:
        if len(p) >= keep:
            out[p] = True
    return out.reshape(mask.shape)


VARIANT_NAME = re.compile(r"[A-Za-z0-9_-]+")
EXPRESSION_CHANGE = 24  # 0-255: a variant pixel this far from the portrait's is part of the new expression


def eye_tops(eyes, W):
    """Per column, the top of the eye on that side: the two largest pieces of the eyes' layer, split halfway between
    their centres (one eye's top everywhere when only one piece is found)."""
    pieces = sorted(components(eyes), key=len, reverse=True)[:2]
    if len(pieces) < 2:
        return np.full(W, (pieces[0] // W).min())
    (ya, xa), (yb, xb) = (np.divmod(x, W) for x in pieces)
    if xa.mean() > xb.mean():
        (ya, xa), (yb, xb) = (yb, xb), (ya, xa)
    return np.where(np.arange(W) < (xa.mean() + xb.mean()) / 2, ya.min(), yb.min())


EYES_TOP_PAD = 2  # px: how far above the eyes' top an eye swap may reach (the anti-aliased edge of the lashes)
EXPRESSION_PAD = 6  # px of unchanged skin round each swap patch, so it covers the old mouth or eyes whole


def cmd_expressions(a):
    """Swap layers for a mouth or eyes from edits of the same portrait (one per shape, made to line up with it): each
    group's patch is the area any of its variants changed near that part, grown a little, minus the front hair (the
    bangs stay on top); every variant, and the portrait as `neutral`, is cut over that same patch, so they swap in
    place. Writes layers/expressions/<group>-<name>.png and adds them to manifest.json under `swaps`.
    """
    W, H = Image.open(a.portrait).size
    labels = labels_of(os.path.join(a.out, "labels.png"), (W, H))
    labels, _ = despeckle(labels)
    L = {n: labels == i for i, n in enumerate(NAMES)}
    orig = load_rgba(a.portrait)
    groups = {
        "mouth": main_parts(L["mouth"]),
        "eyes": main_parts(L["eye_whites"] | L["irides"] | L["eyelines"]),
    }
    variants = {}
    for spec in a.variant:
        group, _, rest = spec.partition(":")
        name, _, path = rest.partition("=")
        if group not in groups or not name or not path:
            sys.exit(
                f"expressions: --variant {spec!r}: write it as mouth:<name>=<file> or eyes:<name>=<file>"
            )
        if not VARIANT_NAME.fullmatch(name) or name == "neutral":
            sys.exit(
                f"expressions: --variant {spec!r}: a name is letters, digits, - and _, and not neutral (the portrait)"
            )
        if name in variants.get(group, {}):
            sys.exit(f"expressions: --variant {spec!r}: {group}:{name} is given twice")
        variants.setdefault(group, {})[name] = load_rgba(path, (W, H))
    manifest_path = os.path.join(a.out, "layers", "manifest.json")
    manifest = json.load(open(manifest_path))
    out_dir = os.path.join(a.out, "layers", "expressions")
    os.makedirs(out_dir, exist_ok=True)
    manifest.setdefault("swaps", {})
    report = {}
    for group, part in groups.items():
        if group not in variants or not part.any():
            continue
        # Near the part itself: within about half its height of it (each eye or the mouth, not a box round both
        # eyes, which reaches the hair at the temples). Skin, brows and the part only, never hair: the edit
        # re-renders a few percent of the picture, hair included, and hair in a swap would not move with the hair.
        x0, y0, x1, y1 = bbox(part)
        # A closed mouth is a thin line: its reach comes from its width, so an open "aa" fits.
        reach = max(
            6, min(max((y1 - y0) // 2, (x1 - x0) // 2 if group == "mouth" else 0), 60)
        )
        near_part = grow(part, reach)
        changed = np.zeros((H, W), bool)
        for img in variants[group].values():
            changed |= (
                np.abs(img[:, :, :3] - orig[:, :, :3]).max(-1) > EXPRESSION_CHANGE
            )
        hair = L["front_hair"] | L["back_hair"] | L["background"] | L["body"]
        patch = grow((changed & near_part) | part, EXPRESSION_PAD) & near_part & ~hair
        if group == "eyes":
            # Never above the eyes' top (their lashes included): an edit that closes or half-closes the eyes often
            # lowers the brows too, and those brows in the swap doubled the brows layer drawn above it. Lids that
            # close never rise above that line; the brows always come from their own layer.
            # Each eye at its own top: on a tilted head the lower eye's patch never reaches up to the higher eye's.
            patch &= np.arange(H)[:, None] >= eye_tops(part, W) - EYES_TOP_PAD
        alpha = soften(patch)
        rows = []
        for name, img in [("neutral", orig)] + list(variants[group].items()):
            im = Image.fromarray(
                np.dstack([img[:, :, :3], alpha * 255]).clip(0, 255).astype(np.uint8),
                "RGBA",
            )
            box = im.getbbox()
            fn = f"{group}-{name}.png"
            im.crop(box).save(os.path.join(out_dir, fn))
            rows.append(
                {
                    "name": name,
                    "file": "expressions/" + fn,
                    "x": box[0],
                    "y": box[1],
                    "w": box[2] - box[0],
                    "h": box[3] - box[1],
                    # neutral is the base layers themselves: a rig shows them (and the irises gaze moves), not this
                    # sprite, which only shows the patch the other states cover.
                    **({"base": True} if name == "neutral" else {}),
                }
            )
        # Drawn above the face details and under the front hair: z of the front hair, which the swap goes just below.
        manifest["swaps"][group] = {"under": "front_hair", "states": rows}
        report[group] = {
            "states": [r["name"] for r in rows],
            "patchPx": int(patch.sum()),
        }
    # Only the groups recut here are fresh: another group's swaps still come from the old labels.
    recut = {f"expressions:{g}" for g in report}
    pending = manifest.get("pending", [])
    if "expressions" in pending:
        pending = [p for p in pending if p != "expressions"] + [
            f"expressions:{g}" for g in manifest["swaps"]
        ]
    manifest["pending"] = [p for p in dict.fromkeys(pending) if p not in recut]
    if not manifest["pending"]:
        manifest.pop("pending")
    json.dump(manifest, open(manifest_path, "w"), indent=1)
    print(json.dumps({"manifest": manifest_path, "swaps": report}))


def cmd_gaze(a):
    """Irises that can move: each visible iris completed to its full ellipse with the in-paint's pixels (only those
    inside the ellipse, in the iris's colours, where the lid hid it), the eye whites made solid under it, and the
    eye's opening written as a clip (layers/irides-clip.png) the irises are drawn inside, as cel animation draws an
    iris under the lids. Rewrites the irides and eye_whites layers in place."""
    W, H = Image.open(a.portrait).size
    labels = labels_of(os.path.join(a.out, "labels.png"), (W, H))
    labels, _ = despeckle(labels)
    L = {n: labels == i for i, n in enumerate(NAMES)}
    orig = load_rgba(a.portrait)
    fill = load_rgba(a.iris_fill, (W, H))
    yy, xx = np.mgrid[0:H, 0:W]
    full = np.zeros((H, W), bool)
    for part in components(main_parts(L["irides"])):
        one = np.zeros(H * W, bool)
        one[part] = True
        x0, y0, x1, y1 = bbox(one.reshape(H, W))
        rx = (x1 - x0) / 2
        ry = max(
            rx * 1.15, (y1 - y0) / 2
        )  # an anime iris is a little taller than wide; the lid hides its top
        cx, cy = (
            x0 + x1
        ) / 2, y1 - ry  # its bottom shows below the lid, so it sets the centre
        full |= ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1
    visible = L["irides"]
    # The hidden top of an iris is often one flat dark shade of the iris colour: the iris and eye whites are
    # colours it may rightly be.
    blank = blank_fill(fill, full & ~visible, orig, L, extra=("irides", "eye_whites"))
    if blank:
        sys.exit(
            f"gaze: the iris in-paint painted {blank:.0%} of the hidden iris one colour, a blank: redo it"
        )
    hidden = full & ~visible & near(fill, visible, 90)
    iris_colour = np.where(hidden[..., None], fill, orig)
    # Whatever of the ellipse the in-paint did not paint in the iris's colours (its lid line, a lash) takes the
    # nearest iris colour, so the iris is whole and round.
    iris_colour = spread(iris_colour, visible | hidden, full & ~(visible | hidden), 12)
    iris = full | visible
    opening = grow(L["eye_whites"] | L["irides"], 1)
    # Inside the opening only: past it the white would show on the skin above a thin lid (the eye lines cover the lid,
    # not a strip beyond it), and the irises are clipped to the opening anyway.
    whites = L["eye_whites"] | (grow(iris, 2) & opening)
    white = (
        np.median(orig[:, :, :3][L["eye_whites"]], axis=0)
        if L["eye_whites"].any()
        else np.array([250, 250, 250])
    )
    white_colour = orig.copy()
    white_colour[:, :, :3][whites & ~L["eye_whites"]] = white
    out = os.path.join(a.out, "layers")
    manifest = json.load(open(os.path.join(out, "manifest.json")))

    def write(name, mask, colour):
        alpha = soften(mask)
        im = Image.fromarray(
            np.dstack([colour[:, :, :3], alpha * 255]).clip(0, 255).astype(np.uint8),
            "RGBA",
        )
        box = im.getbbox()
        for r in manifest["layers"]:
            if r["name"] == name:
                im.crop(box).save(os.path.join(out, r["file"]))
                r.update(
                    {
                        "x": box[0],
                        "y": box[1],
                        "w": box[2] - box[0],
                        "h": box[3] - box[1],
                    }
                )

    write("eye_whites", whites, white_colour)
    write("irides", iris, iris_colour)
    clip = Image.fromarray((opening * 255).astype(np.uint8), "L")
    box = clip.getbbox()
    clip.crop(box).save(os.path.join(out, "irides-clip.png"))
    for r in manifest["layers"]:
        if r["name"] == "irides":
            r["clip"] = {"file": "irides-clip.png", "x": box[0], "y": box[1]}
    manifest["pending"] = [p for p in manifest.get("pending", []) if p != "gaze"]
    if not manifest["pending"]:
        manifest.pop("pending")
    json.dump(manifest, open(os.path.join(out, "manifest.json"), "w"), indent=1)
    print(
        json.dumps(
            {
                "irisAdded": int(hidden.sum()),
                "irisPx": int(iris.sum()),
                "clip": "irides-clip.png",
            }
        )
    )


SIDECAR_VERSION = 1  # the rig sidecar's format: the recipe's step 10 tells a rig script to accept only this one
HEAD_PIVOT = 0.45  # of the way from the chin up to the eyes: where the head turns on the neck (about the ear lobes)


def rig_bones(L, W, H):
    """A bust and face skeleton placed from the labels, in PSD space (y down), parents first: the chain from the
    hips to the head, the face parts on the face, and each hair layer as a root at the crown and two segments a side,
    so hair bends toward its tips while its roots stay on the scalp. Also the skins (bands of the hair down the canvas,
    blending into each other) that weight the hair layers to those bones."""

    def box(mask, fallback):
        b = bbox(main_parts(mask, 0.2)) if mask.any() else None
        return b or fallback

    hx0, hy0, hx1, hy1 = box(L["front_hair"] | L["back_hair"], (0, 0, W, H // 2))
    fx0, fy0, fx1, fy1 = box(L["face"], (W // 3, H // 5, 2 * W // 3, H // 2))
    nx0, ny0, nx1, ny1 = box(L["neck"], (fx0, fy1, fx1, fy1 + H // 10))
    cx = (fx0 + fx1) / 2
    chin = fy1
    neck_base = max(ny1, chin + 10)
    eye_y = bbox(main_parts(L["irides"])) or (0, (fy0 + fy1) // 2, 0, (fy0 + fy1) // 2)
    eye_y = (eye_y[1] + eye_y[3]) / 2
    # The head turns on the top of the neck, about ear-lobe height, not on the chin: turned round the chin, the jaw's
    # corners by the ears swing furthest and uncover the neck beside them; round the neck's top they barely move, and
    # the chin sweeps over the neck, which the face covers.
    pivot = chin - (chin - eye_y) * HEAD_PIVOT
    bones = [
        ("Root", "", (cx, H - 4), (cx, neck_base)),
        ("Chest", "Root", (cx, neck_base), (cx, neck_base - (neck_base - chin) * 0.6)),
        ("Neck", "Chest", (cx, neck_base - (neck_base - chin) * 0.6), (cx, pivot)),
        ("Head", "Neck", (cx, pivot), (cx, hy0)),
        ("Face", "Head", (cx, chin - (chin - fy0) * 0.25), (cx, eye_y)),
        ("Irides", "Face", (cx, eye_y), (cx + (fx1 - fx0) * 0.08, eye_y)),
        (
            "Brows",
            "Face",
            (cx, eye_y - (chin - fy0) * 0.18),
            (cx, eye_y - (chin - fy0) * 0.3),
        ),
        (
            "Mouth",
            "Face",
            (cx, chin - (chin - fy0) * 0.22),
            (cx + (fx1 - fx0) * 0.08, chin - (chin - fy0) * 0.22),
        ),
    ]
    skins = []
    for name, part in (("FrontHair", "front_hair"), ("BackHair", "back_hair")):
        if not L[part].any():
            continue
        px0, py0, px1, py1 = (
            bbox(L[part]) if name == "FrontHair" else (hx0, hy0, hx1, max(hy1, H - 1))
        )
        root_y = hy0 + (hy1 - hy0) * 0.12
        band1 = min(max(eye_y, root_y + 20), py1 - 2)
        band2 = min(max(chin, band1 + 20), py1 - 1)
        crown = (cx, root_y)
        bones.append((f"{name}Root", "Head", crown, (cx, hy0)))
        for side, sx in (("L", (px0 + cx) / 2), ("R", (px1 + cx) / 2)):
            bones.append((f"{name}{side}1", f"{name}Root", (sx, band1), (sx, band2)))
            bones.append(
                (
                    f"{name}{side}2",
                    f"{name}{side}1",
                    (sx, band2),
                    (sx, max(py1, band2 + 10)),
                )
            )
        top = [{"bone": f"{name}Root", "y0": 0, "y1": band1}]
        if name == "FrontHair":
            # The fringe over the forehead sways on its own: the scalp stays on the root down to the face's top, then
            # a bangs bone over each eye, hinged at the hairline, carries the fringe down to the eyes.
            hairline = min(max(fy0, root_y + 20), band1 - 40)
            if hairline > root_y:
                for side, sx in (("L", (fx0 + cx) / 2), ("R", (fx1 + cx) / 2)):
                    bones.append(
                        (
                            f"{name}Bangs{side}",
                            f"{name}Root",
                            (sx, hairline),
                            (sx, band1),
                        )
                    )
                top = [
                    {"bone": f"{name}Root", "y0": 0, "y1": hairline},
                    {"bone": f"{name}BangsL|{name}BangsR", "y0": hairline, "y1": band1},
                ]
        skins.append(
            {
                "layer": name,
                "split_x": cx,
                "blend": max(20.0, (band2 - band1) * 0.4),
                "bands": top
                + [
                    {"bone": f"{name}L1|{name}R1", "y0": band1, "y1": band2},
                    {"bone": f"{name}L2|{name}R2", "y0": band2, "y1": H},
                ],
            }
        )
    return [
        {
            "name": n,
            "parent": p,
            "head": [round(float(h[0]), 1), round(float(h[1]), 1)],
            "tail": [round(float(t[0]), 1), round(float(t[1]), 1)],
        }
        for n, p, h, t in bones
    ], skins


# Which bone carries each layer rigidly (the hair layers are skinned in bands instead).
RIG_CARRY = {
    "Body": "Chest",
    "Neck": "Neck",
    "Face": "Head",
    "EyeWhites": "Face",
    "Irides": "Irides",
    "Eyelines": "Face",
    "Mouth": "Mouth",
    "Brows": "Brows",
}
RIG_NAMES = {
    "back_hair": "BackHair",
    "body": "Body",
    "neck": "Neck",
    "face": "Face",
    "eye_whites": "EyeWhites",
    "irides": "Irides",
    "eyelines": "Eyelines",
    "mouth": "Mouth",
    "front_hair": "FrontHair",
    "brows": "Brows",
}


def cmd_rig(a):
    """The layers as a rigged-ready PSB for Unity's 2D Animation: D/character.psb (every layer at its place, each
    expression group's variants as hidden layers and its `neutral` as an empty visible one; after gaze, the irises
    inside the eye opening, the whole irises as a hidden IridesWhole layer and the opening as a hidden IridesClip
    layer for a Sprite Mask), and D/character.psb.json,
    the sidecar a rig script (written from sequences/rig-2d-snippets.md) writes into the PSB importer: bones placed from the labels, the hair's
    skins, and the Sprite Library categories for the swaps."""
    W, H = Image.open(a.portrait).size
    labels = labels_of(os.path.join(a.out, "labels.png"), (W, H))
    labels, _ = despeckle(labels)
    L = {n: labels == i for i, n in enumerate(NAMES)}
    folder = os.path.join(a.out, "layers")
    manifest = json.load(open(os.path.join(folder, "manifest.json")))
    # A cut newer than gaze or the swaps leaves them stale: packing them would rig the old irises or patches.
    if manifest.get("pending"):
        sys.exit(
            f"rig: run {', '.join(manifest['pending'])} again first: layers cut the portrait again after them"
        )

    def place(row, x=None, y=None):
        canvas = np.zeros((H, W, 4), np.uint8)
        im = np.asarray(Image.open(os.path.join(folder, row["file"])).convert("RGBA"))
        x, y = row["x"] if x is None else x, row["y"] if y is None else y
        canvas[y : y + im.shape[0], x : x + im.shape[1]] = im
        return canvas

    def opening(row):
        # The eye opening gaze wrote (grey, white inside), as white with the opening as its alpha: a Sprite Mask's
        # shape, and what the irises are kept inside.
        clip = place({"file": row["clip"]["file"]}, row["clip"]["x"], row["clip"]["y"])
        mask = np.zeros((H, W, 4), np.uint8)
        mask[:, :, :3] = 255
        mask[:, :, 3] = clip[:, :, 0]
        return mask

    def clipped(row):
        # gaze completes each iris under the lids and writes the eye opening as its clip: the PSB layer is the
        # iris inside that opening, so at rest nothing draws over the lids.
        canvas = place(row)
        canvas[:, :, 3] = (
            canvas[:, :, 3].astype(np.uint16) * opening(row)[:, :, 3] // 255
        ).astype(np.uint8)
        return canvas

    def add_swaps():
        for group, swap in swaps.items():
            cat = group.capitalize()
            for st in swap["states"]:
                lname = f"{cat}_{st['name']}"
                if st.get("base"):
                    # neutral is the base layers: an empty sprite, so they (and the irises gaze moves) show
                    empty = np.zeros((H, W, 4), np.uint8)
                    x, y = st["x"] + st["w"] // 2, st["y"] + st["h"] // 2
                    empty[y, x] = (0, 0, 0, 1)
                    layers.append((lname, empty, True))
                else:
                    layers.append((lname, place(st), False))
                categories.append(
                    {"category": cat, "label": st["name"], "layer": lname}
                )
                carry[lname] = "Face"

    layers, carry, categories, helpers = [], {}, [], []
    swaps = manifest.get("swaps", {})
    rows = sorted(manifest["layers"], key=lambda r: r["z"])
    # The swaps go just under the front hair, as the manifest says; with no front hair, under the brows, or on top.
    above = next(
        (r["name"] for r in rows if r["name"] in ("front_hair", "brows")), None
    )
    for row in rows:
        name = RIG_NAMES.get(row["name"], row["name"])
        if row["name"] == above:
            add_swaps()
        layers.append((name, clipped(row) if row.get("clip") else place(row), True))
        if name in RIG_CARRY:
            carry[name] = RIG_CARRY[name]
        if row.get("clip"):
            # For the eyes to look around: the whole iris gaze completed, hidden, on the irises' own bone, and the
            # opening it shows through (a Sprite Mask on a child of the Face bone). The visible Irides is the rest pose.
            # The PSD Importer brings hidden layers in as visible sprites (it does not keep the hidden flag), so these
            # two go under everything: covered by the whole character, they show nothing until the user uses them.
            helpers.append(("IridesWhole", place(row), False))
            carry["IridesWhole"] = RIG_CARRY["Irides"]
            helpers.append(("IridesClip", opening(row), False))
            carry["IridesClip"] = "Face"
    if above is None:
        add_swaps()
    layers[:0] = helpers
    composite = np.zeros((H, W, 4), np.float32)
    for _, rgba, visible in layers:
        if visible:
            a_ = rgba[:, :, 3:4].astype(np.float32) / 255
            composite[:, :, :3] = rgba[:, :, :3] * a_ + composite[:, :, :3] * (1 - a_)
            composite[:, :, 3:4] = a_ * 255 + composite[:, :, 3:4] * (1 - a_)
    bones, skins = rig_bones(L, W, H)
    for b in bones:
        b["layers"] = [n for n, bone in carry.items() if bone == b["name"]]
    psb = os.path.join(a.out, "character.psb")
    write_psb(psb, W, H, layers, composite.clip(0, 255).astype(np.uint8))
    sidecar = {
        # The format the recipe's step 10 accepts (`version` is `1`): bump both together when the sidecar changes shape.
        "version": SIDECAR_VERSION,
        "width": W,
        "height": H,
        "bones": bones,
        "skins": skins,
        "categories": categories,
    }
    json.dump(sidecar, open(psb + ".json", "w"), indent=1)
    print(
        json.dumps(
            {
                "psb": psb,
                "sidecar": psb + ".json",
                "layers": [n for n, _, _ in layers],
                "bones": [b["name"] for b in bones],
                "skinned": [s["layer"] for s in skins],
                "swaps": sorted({c["category"] for c in categories}),
            }
        )
    )


def cmd_layers(a):
    if a.back_hair and (a.hair_fill or a.locks_fill):
        sys.exit(
            "layers: --back-hair replaces --hair-fill and --locks-fill (their fallback): pass one or the other"
        )
    W, H = Image.open(a.portrait).size
    old_manifest = os.path.join(a.out, "layers", "manifest.json")
    try:
        had = json.load(open(old_manifest)) if os.path.exists(old_manifest) else {}
    except ValueError:
        had = (
            {}
        )  # a truncated manifest: start afresh rather than fail the recovery command
    if had.get("source") != os.path.basename(a.portrait) or had.get("size") != [W, H]:
        had = {}  # --out last used for another portrait: nothing of it carries over
    raw = labels_of(os.path.join(a.out, "labels.png"), (W, H))
    labels, specks = despeckle(raw)
    L = {n: labels == i for i, n in enumerate(NAMES)}
    orig = load_rgba(a.portrait)
    stack, counts = build_stack(a, W, H, L, orig, raw == NAMES.index("back_hair"))
    counts["specksMerged"] = specks
    out = os.path.join(a.out, "layers")
    os.makedirs(out, exist_ok=True)
    rows, canvas, tiles = cut(
        stack, orig, out, whole_hair=bool(a.back_hair), bg=L["background"]
    )
    # The irides and eye whites are cut again from the portrait, so gaze's whole irises and clip are gone: say so.
    # The swaps are kept (cut from the portrait and its edits, not from these layers), and listed again.
    # Expressions are pending per group (`expressions:mouth`), so recutting one group leaves the other listed. An
    # older manifest's bare `expressions` stands for every group it has.
    groups_had = [f"expressions:{g}" for g in had.get("swaps", {})]
    rerun = list(
        dict.fromkeys(
            [p for p in had.get("pending", []) if p != "expressions"]
            + (groups_had if "expressions" in had.get("pending", []) else [])
            + (["gaze"] if any(r.get("clip") for r in had.get("layers", [])) else [])
            + (["gaze"] if os.path.exists(os.path.join(out, "irides-clip.png")) else [])
            + groups_had
        )
    )
    if rerun:
        counts["runAgain"] = list(dict.fromkeys(p.split(":")[0] for p in rerun))
        if any(p.startswith("expressions:") for p in rerun):
            counts["expressionGroups"] = [
                p.split(":")[1] for p in rerun if p.startswith("expressions:")
            ]
    json.dump(
        {
            "size": [W, H],
            "source": os.path.basename(a.portrait),
            "layers": rows,
            **({"swaps": had["swaps"]} if had.get("swaps") else {}),
            # Steps to run again after this cut, until they do (each clears its own).
            **({"pending": rerun} if rerun else {}),
        },
        open(os.path.join(out, "manifest.json"), "w"),
        indent=1,
    )
    Image.fromarray(canvas.clip(0, 255).astype(np.uint8), "RGBA").save(
        os.path.join(a.out, "recomposed.png")
    )
    full_diff = np.abs(canvas[:, :, :3] - orig[:, :, :3]).max(-1)
    # With a generated whole back hair, the back hair that shows is the generated picture by design: it is reported
    # on its own, so the check of every other part still says whether a map moved an outline.
    checked = ~L["background"] & ~(
        L["back_hair"] if a.back_hair else np.zeros_like(L["background"])
    )
    diff = full_diff[checked]
    if a.back_hair:
        counts["backHairMeanDiff"] = (
            round(float(full_diff[L["back_hair"]].mean()), 2)
            if L["back_hair"].any()
            else 0.0
        )
    # Coverage: inside the character the stack must be opaque wherever the portrait is (a seam would show the
    # background through it in Unity).
    # (The character's own outline onto the background is soft on purpose, so it is left out.)
    inside = ~grow(L["background"], GROW_PX)
    gap = (orig[:, :, 3] - canvas[:, :, 3])[inside] / 255
    # What a rig shows when the hair moves: the hair sways from where it is rooted, the crown, its tips trailing
    # (front and back the other way), rather than being taken off, which no animation does and which makes any face
    # look unlike itself. The hair is attached at the scalp: it never slides over the forehead.
    fh = bbox(L["front_hair"]) or (0, 0, W, H)
    crown = ((fh[0] + fh[2]) // 2, fh[1] + (fh[3] - fh[1]) // 8)
    moved = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    for name, im in tiles:
        if name == "front_hair":
            im = im.rotate(4, resample=Image.BICUBIC, center=crown)
        elif name == "back_hair":
            im = im.rotate(-3, resample=Image.BICUBIC, center=crown)
        moved = Image.alpha_composite(moved, im)
    write_sheet(
        tiles + [("hair moved", moved)],
        os.path.join(a.out, "layers-sheet.png"),
    )
    print(
        json.dumps(
            {
                "manifest": os.path.join(out, "manifest.json"),
                "layers": [r["name"] for r in rows],
                "recomposeMeanDiff": round(float(diff.mean()), 2),
                "recomposePctOver16": round(float((diff > 16).mean() * 100), 2),
                "recomposeAlphaPctUnder98": round(float((gap > 0.02).mean() * 100), 2),
                **counts,
            }
        )
    )


def write_sheet(tiles, path, tile=256):
    """Every layer on a checker, and the portrait without its front hair: what the in-paints add."""
    cells = []
    for name, im in tiles:
        im = im.copy()
        im.thumbnail((tile, tile * 3 // 2))
        bg = Image.new("RGBA", im.size, (200, 200, 200, 255))
        dr = ImageDraw.Draw(bg)
        for y in range(0, im.size[1], 16):
            for x in range(0, im.size[0], 16):
                if (x // 16 + y // 16) % 2:
                    dr.rectangle([x, y, x + 15, y + 15], fill=(235, 235, 235, 255))
        cells.append((name, Image.alpha_composite(bg, im)))
    tw, th = cells[0][1].size
    cols = 6
    sheet = Image.new(
        "RGB", (cols * tw, ((len(cells) + cols - 1) // cols) * (th + 22)), "white"
    )
    dr = ImageDraw.Draw(sheet)
    for i, (name, im) in enumerate(cells):
        x, y = (i % cols) * tw, (i // cols) * (th + 22)
        sheet.paste(im.convert("RGB"), (x, y + 22))
        dr.text((x + 4, y + 4), name, fill="black")
    sheet.save(path)


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, extra in (
        ("crop", ["map"]),
        ("masks", ["map", "face_map"]),
        ("layers", []),
        ("expressions", []),
        ("gaze", ["iris_fill"]),
        ("rig", []),
    ):
        s = sub.add_parser(name)
        s.add_argument("--portrait", required=True)
        s.add_argument("--out", required=True)
        for e in extra:
            s.add_argument("--" + e.replace("_", "-"), dest=e, required=True)
        if name == "layers":
            s.add_argument(
                "--face-fill",
                dest="face_fill",
                default=None,
                help="omit when masks said faceInpaint false",
            )
            s.add_argument(
                "--back-hair",
                dest="back_hair",
                default=None,
                help="a picture of the whole back hair alone, lined up with the portrait (replaces --hair-fill and --locks-fill)",
            )
            s.add_argument(
                "--locks-fill",
                dest="locks_fill",
                default=None,
                help="omit when masks said locksInpaint false",
            )
            s.add_argument(
                "--hair-fill",
                dest="hair_fill",
                default=None,
                help="omit when masks said backHairInpaint false",
            )
        if name == "expressions":
            s.add_argument(
                "--variant",
                action="append",
                default=[],
                help="mouth:<name>=<file> or eyes:<name>=<file>, an edit of the portrait; repeat it",
            )
    a = p.parse_args()
    os.makedirs(a.out, exist_ok=True)
    {
        "crop": cmd_crop,
        "masks": cmd_masks,
        "layers": cmd_layers,
        "expressions": cmd_expressions,
        "gaze": cmd_gaze,
        "rig": cmd_rig,
    }[a.cmd](a)


if __name__ == "__main__":
    main()
