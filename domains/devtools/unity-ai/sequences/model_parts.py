#!/usr/bin/env python3
"""Free local steps of sequences/model-to-parts.md: a generated 3D model (a GLB: a tank, a gun turret, a wheeled
vehicle) split into rigid parts a game can move, each on its own node whose origin is its pivot, and measured.

NumPy only. It reads only the files it is given and writes only --out (and, with Blender, a temporary folder it
removes). Every coordinate is in the model's own space as the GLB places it (Y up, metres or whatever the file
uses), the space `inspect` reports and the plan's boxes are written in.

  inspect --model M [--axis x|y|z] [--box minx,miny,minz,maxx,maxy,maxz] [--slices N]
          Prints the model's bounds, its connected pieces (the largest first: centre, size, triangles, and whether it
          lies flat on the model's floor, a drop shadow the generator baked from its concept image) and a profile of
          its cross-section by height (width, depth and area of each slice: a turret's neck is where it narrows).
          --axis x|y|z slices along another axis (a barrel along its length); --box minx,miny,minz,maxx,maxy,maxz
          slices only that region, as a box face would cut it: each slice's `loops` (closed) and `open` (loops that do
          not close) are what a cut there would report, so a cut goes where `open` is 0.
          A model with more than one mesh node also gets `meshNodes` (each node's name and triangles): a model
          that already comes in parts, which a split would merge and cut again.
  split   --model M --plan P --out O [--overwrite] [--kernel numpy|auto|blender] [--blender PATH]
          Cuts the parts the plan names out of the model and writes O: a GLB with one node per part under the root
          (`Hull > Turret > Cannon`, `Body > WheelFL`), each node's translation its pivot, each mesh around its own
          pivot, the source's materials and textures copied as they are. Prints one JSON line: per part its
          triangles, its cut faces (loops closed or open), its pivot and where it came from, its bounce when it
          spins, the floor pieces it took, and the checks that failed. Exit 0 when every check passes, 3 when the
          split was written but a check failed, 2 when nothing was written (`error` says why, whatever went wrong).
          O must be new: never the model, and an existing file only with --overwrite (your own earlier split).
          --kernel numpy (the default) cuts in NumPy; auto retries a cut NumPy leaves open in Blender, when it is
          installed, and keeps the result with fewer open edges along the cut (a Blender failure keeps NumPy's, in
          `blenderError`); blender cuts with Blender alone. Blender is found on PATH or in its usual install
          folders (never the current folder), or named with --blender.

The plan (JSON, --plan):

  {"root": "Hull",
   "parts": [
     {"name": "Turret", "mode": "cut", "boxes": [{"min": [-0.3, 0.05, -0.3], "max": [0.3, 0.6, 0.35]}],
      "axis": "y", "pivot": "ring", "range": [-180, 180]},
     {"name": "Cannon", "parent": "Turret", "mode": "cut", "boxes": [{"min": [-0.05, 0.1, 0.3], "max": [0.05, 0.2, 1]}],
      "axis": "x", "pivot": "root", "range": [-20, 5]},
     {"name": "WheelFL", "mode": "pieces", "boxes": [{"min": [0.3, -0.5, 0.2], "max": [0.6, 0, 0.6]}],
      "axis": "x", "pivot": "hub", "spin": true}]}

  root    the name of what stays (the hull, the body, the base).
  mode    `cut` slices along the boxes' faces and closes every cut with a cap (fused parts: a turret on its hull, a
          barrel in its mantlet, a lid on its box); `pieces` lifts whole connected pieces whose centre is in a box
          (parts the generator already made separate: wheels, most propellers).
  boxes   one or more, axis-aligned, in model space. A cut part is the union of its boxes; a face that crosses the
          model cuts it there, so keep every face but the cut clear of the model.
  parent  the part it rides on (default: the root). Children are cut before their parents, so a barrel's box may
          sit inside its turret's.
  axis    `x`, `y`, `z` or a vector: what it turns about.
  pivot   `ring`: the centre of its cut faces that face up or down (a turret's ring; for a piece, the centre of its
          footprint); `root`: the centre of its cut faces that face sideways (a barrel's root), or of the cut loop on
          the box face when the cut did not close; `hub`: a spinning part's axle (the centre, seen along the axis, of
          its piece widest across the axis); {"edge": [x, y, z]}: the middle of the cut's edge farthest that way (a
          lid's or a hatch's hinge); or a point [x, y, z].
  spin    true for a part that turns full circles (a wheel, a propeller): its bounce is measured.
  range   degrees, the turn it makes, for the preview's sweep (default [-30, 30]; a spin turns a full circle).

A spinning `pieces` part keeps the piece widest across its axis (a tyre, a rim) and the pieces inside that piece's
swept cylinder; a piece reaching out of it (a suspension arm, a mudguard) stays on the parent. Floor pieces are never
taken by a `pieces` part; `"floor": "drop"` at the plan's top level also removes them from the root.

Checks (each failure is listed, by part, in `failed`):
  empty      the part took no triangles: its boxes miss the model.
  open-cut   open edges are left along a cut face (`seamOpenEdges`): the model's slice there does not close (the
             mesh is open there, or the cut runs off the face onto a neighbouring one), so that face has a hole.
  bounce     a spinning part's extreme point (its lowest for a wheel, its farthest sideways about a vertical axis)
             moves by more than BOUNCE_MAX of its radius over a full turn (`bounceMax` in the report): its pivot is
             off its axle, or it took a piece that is not round (a baked shadow, a mudguard).
  floor      the part holds a piece lying flat on the model's floor (a baked shadow).
  pivot      the pivot rule found nothing to read (no cap and no loop): the pivot fell back to the part's box centre.

Each part's node carries its motion in its glTF extras ({"unityAi": {"motion": {"axis": [...], "range": [...],
"spin": bool}}}), which `unity ai preview --png --views pivots,sweep` draws.
"""

import argparse
import json
import math
import os
import shutil
import struct
import subprocess
import sys
import tempfile

try:
    import numpy as np
except ImportError:
    if __name__ != "__main__":
        raise
    print(
        json.dumps(
            {
                "error": "NumPy is not installed for this Python: model_parts.py needs it, nothing was read or written",
                "missing": "numpy",
            }
        )
    )
    sys.exit(2)

BOUNCE_MAX = 0.06  # a wheel spun on its true axle measured 1 to 6% of its radius; one off its axle, 25 to 43%
FLOOR_THICK = 0.03  # a piece thinner than this share of the model's height ...
FLOOR_NEAR = 0.06  # ... whose bottom is within this share of the floor lies on the floor: a baked shadow
SPIN_REACH = (
    1.02  # a spinning part keeps pieces inside its widest piece's radius times this ...
)
SPIN_SIDE = (
    0.25  # ... and within this share of that radius past its sides along the axle
)
PROFILE_SLICES = 24
DEFAULT_RANGE = [-30.0, 30.0]
BLENDER_TIMEOUT = 600
MAX_TRIANGLES = (
    2_000_000  # a generated model is 10k to 50k: anything past this is not one
)

AXES = {"x": [1.0, 0.0, 0.0], "y": [0.0, 1.0, 0.0], "z": [0.0, 0.0, 1.0]}
FACE_NAMES = [
    "+x",
    "-x",
    "+y",
    "-y",
    "+z",
    "-z",
]  # a box face by its outward direction (+y is the top)
NAME_OK = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")


class PlanError(Exception):
    pass


# ── GLB in ─────────────────────────────────────────────────────────────────────────────────────────────────────

COMPONENT = {
    5120: np.int8,
    5121: np.uint8,
    5122: np.int16,
    5123: np.uint16,
    5125: np.uint32,
    5126: np.float32,
}
WIDTH = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}
NORMALIZED_SCALE = {
    np.int8: 127.0,
    np.uint8: 255.0,
    np.int16: 32767.0,
    np.uint16: 65535.0,
}


def read_glb(path):
    data = open(path, "rb").read()
    if len(data) < 20 or data[:4] != b"glTF":
        raise PlanError(f"{path} is not a GLB (binary glTF): convert it to .glb first")
    at, doc, binary = 12, None, b""
    while at + 8 <= len(data):
        length, kind = struct.unpack("<II", data[at : at + 8])
        chunk = data[at + 8 : at + 8 + length]
        if kind == 0x4E4F534A:
            doc = json.loads(chunk.decode("utf-8"))
        elif kind == 0x004E4942:
            binary = chunk
        at += 8 + length
    if doc is None:
        raise PlanError(f"{path} has no JSON chunk")
    required = set(doc.get("extensionsRequired", []))
    for ext in (
        "KHR_draco_mesh_compression",
        "EXT_meshopt_compression",
        "KHR_mesh_quantization",
    ):
        if ext in required:
            raise PlanError(
                f"{path} is compressed ({ext}): download it uncompressed, or open and re-save it first"
            )
    for buf in doc.get("buffers", [])[1:] + [
        b for b in doc.get("buffers", [])[:1] if "uri" in b
    ]:
        raise PlanError(
            f"{path} reads its data from another file ({buf.get('uri')}): use the .glb with everything inside"
        )
    return doc, binary


def view_bytes(doc, binary, index):
    v = doc["bufferViews"][index]
    start = v.get("byteOffset", 0)
    return binary[start : start + v["byteLength"]], v.get("byteStride")


def accessor(doc, binary, index):
    a = doc["accessors"][index]
    if "sparse" in a:
        raise PlanError(
            "the model uses sparse accessors, which this script does not read"
        )
    dtype = COMPONENT[a["componentType"]]
    width = WIDTH[a["type"]]
    count = a["count"]
    if "bufferView" not in a:
        return np.zeros((count, width), np.float64)
    raw, stride = view_bytes(doc, binary, a["bufferView"])
    item = np.dtype(dtype).itemsize * width
    stride = stride or item
    start = a.get("byteOffset", 0)
    rows = np.frombuffer(
        raw, np.uint8, count=(count - 1) * stride + item if count else 0, offset=start
    )
    if stride == item:
        out = rows.view(dtype).reshape(count, width)
    else:
        idx = (np.arange(count)[:, None] * stride + np.arange(item)[None, :]).ravel()
        out = rows[idx].view(dtype).reshape(count, width)
    out = out.astype(np.float64)
    if a.get("normalized") and dtype in NORMALIZED_SCALE:
        out = np.maximum(out / NORMALIZED_SCALE[dtype], -1.0)
    return out


def quat_matrix(q):
    x, y, z, w = q
    return np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ]
    )


def node_matrix(node):
    if "matrix" in node:
        return np.array(node["matrix"], np.float64).reshape(4, 4).T
    m = np.eye(4)
    s = np.array(node.get("scale", [1, 1, 1]), np.float64)
    m[:3, :3] = quat_matrix(node.get("rotation", [0, 0, 0, 1])) * s[None, :]
    m[:3, 3] = node.get("translation", [0, 0, 0])
    return m


class Soup:
    """Triangles with their corners' attributes, in model space: P (n, 3, 3) positions, N normals, UV texture
    coordinates (zeros where the source had none), mat the source material (-1: none), cap whether a cut made it,
    piece the connected piece of the source it comes from (-1: a cap)."""

    def __init__(self, P, N, UV, mat, cap=None, piece=None):
        self.P, self.N, self.UV = P, N, UV
        self.mat = np.asarray(mat).astype(np.int64)
        self.cap = (
            np.zeros(len(P), bool) if cap is None else np.asarray(cap).astype(bool)
        )
        self.piece = (
            np.full(len(P), -1, np.int64)
            if piece is None
            else np.asarray(piece).astype(np.int64)
        )

    def __len__(self):
        return len(self.P)

    def take(self, sel):
        return Soup(
            self.P[sel],
            self.N[sel],
            self.UV[sel],
            self.mat[sel],
            self.cap[sel],
            self.piece[sel],
        )

    @staticmethod
    def join(parts):
        parts = [p for p in parts if p is not None and len(p)]
        if not parts:
            return Soup.empty()
        return Soup(
            *(
                np.concatenate([getattr(p, k) for p in parts])
                for k in ("P", "N", "UV", "mat", "cap", "piece")
            )
        )

    @staticmethod
    def empty():
        return Soup(
            np.zeros((0, 3, 3)),
            np.zeros((0, 3, 3)),
            np.zeros((0, 3, 2)),
            np.zeros(0, np.int64),
        )


def load_model(path):
    doc, binary = read_glb(path)
    scenes = doc.get("scenes") or [{"nodes": list(range(len(doc.get("nodes", []))))}]
    roots = scenes[doc.get("scene", 0)].get("nodes", [])
    soups, skinned, seen, triangles = [], False, set(), 0
    stack = [(i, np.eye(4)) for i in roots]
    while stack:
        index, parent = stack.pop()
        if index in seen:
            raise PlanError(
                f"{path}: node {index} is reached twice (its node tree loops or shares a child): not a valid glTF"
            )
        seen.add(index)
        node = doc["nodes"][index]
        world = parent @ node_matrix(node)
        if "skin" in node:
            skinned = True
        if "mesh" in node:
            for prim in doc["meshes"][node["mesh"]]["primitives"]:
                if prim.get("mode", 4) != 4:
                    continue
                attrs = prim["attributes"]
                pos = accessor(doc, binary, attrs["POSITION"])
                nor = (
                    accessor(doc, binary, attrs["NORMAL"])
                    if "NORMAL" in attrs
                    else None
                )
                uv = (
                    accessor(doc, binary, attrs["TEXCOORD_0"])
                    if "TEXCOORD_0" in attrs
                    else np.zeros((len(pos), 2))
                )
                idx = (
                    accessor(doc, binary, prim["indices"]).astype(np.int64).ravel()
                    if "indices" in prim
                    else np.arange(len(pos))
                )
                idx = idx[: len(idx) // 3 * 3].reshape(-1, 3)
                P = (pos @ world[:3, :3].T + world[:3, 3])[idx]
                if nor is None:
                    face = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
                    N = np.repeat(face[:, None, :], 3, axis=1)
                else:
                    normal_matrix = np.linalg.inv(world[:3, :3]).T
                    N = (nor @ normal_matrix.T)[idx]
                N = N / np.maximum(np.linalg.norm(N, axis=2, keepdims=True), 1e-12)
                triangles += len(idx)
                if triangles > MAX_TRIANGLES:
                    raise PlanError(
                        f"{path} has more than {MAX_TRIANGLES:,} triangles: decimate it first"
                    )
                mat = np.full(len(idx), prim.get("material", -1))
                soups.append(Soup(P, N, uv[idx], mat))
        for child in node.get("children", []):
            stack.append((child, world))
    if skinned:
        raise PlanError(
            "the model is skinned (rigged): a character or creature bends, it does not come apart; rig it instead"
        )
    soup = Soup.join(soups)
    if not len(soup):
        raise PlanError(f"{path} has no triangles")
    return doc, binary, soup


# ── Geometry helpers ───────────────────────────────────────────────────────────────────────────────────────────


def model_scale(soup):
    lo, hi = soup.P.reshape(-1, 3).min(0), soup.P.reshape(-1, 3).max(0)
    return lo, hi, float(np.linalg.norm(hi - lo)) or 1.0


def weld_ids(points, scale):
    """One id per distinct position (within 1e-6 of the model's size)."""
    q = np.round(points / (scale * 1e-6)).astype(np.int64)
    _, ids = np.unique(q, axis=0, return_inverse=True)
    return ids.ravel()


def pieces_of(soup, scale):
    """The connected pieces (triangles sharing a position): a label per triangle and the count."""
    ids = weld_ids(soup.P.reshape(-1, 3), scale).reshape(-1, 3)
    parent = list(range(int(ids.max()) + 1 if len(ids) else 0))

    def find(i):
        root = i
        while parent[root] != root:
            root = parent[root]
        while parent[i] != root:
            parent[i], i = root, parent[i]
        return root

    for a, b in np.concatenate([ids[:, [0, 1]], ids[:, [1, 2]]]).tolist():
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)
    roots = np.array([find(i) for i in ids[:, 0].tolist()])
    _, label = np.unique(roots, return_inverse=True)
    return label.ravel(), int(label.max() + 1) if len(label) else 0


def open_edge_ends(soup, scale):
    """The two ends (k, 2, 3) of every edge used by one triangle only (positions welded): a closed (watertight)
    surface has none."""
    if not len(soup):
        return np.zeros((0, 2, 3))
    flat = soup.P.reshape(-1, 3)
    ids = weld_ids(flat, scale).reshape(-1, 3)
    corner = np.arange(len(flat)).reshape(-1, 3)
    e = np.concatenate([ids[:, [0, 1]], ids[:, [1, 2]], ids[:, [2, 0]]])
    c = np.concatenate([corner[:, [0, 1]], corner[:, [1, 2]], corner[:, [2, 0]]])
    keep = e[:, 0] != e[:, 1]
    e, c = np.sort(e[keep], axis=1), c[keep]
    _, first, counts = np.unique(e, axis=0, return_index=True, return_counts=True)
    single = c[first[counts == 1]]
    return flat[single]


def open_edges(soup, scale):
    return len(open_edge_ends(soup, scale))


def seam_open(ends, face, scale):
    """How many of the open edges `ends` lie along a cut face (both ends on its plane, inside it): a cut whose cap
    closed it has none."""
    axis = FACE_NAMES.index(face["face"]) // 2
    lo, hi = np.asarray(face["min"]), np.asarray(face["max"])
    eps = scale * 1e-5
    on = np.abs(ends[:, :, axis] - face.get("_at", face["at"])) < eps
    for k in range(3):
        if k != axis:
            on &= (ends[:, :, k] >= lo[k] - eps) & (ends[:, :, k] <= hi[k] + eps)
    return int(on.all(axis=1).sum())


def label_caps(soup, scale):
    """Give each cap no piece has claimed yet (-1: the caps the last cut made) the piece it closes, so a whole-piece
    part extracted after a cut takes its caps with it. A cap's corners lie on the cut surface's own vertices: each
    is looked up in a grid of the surface's vertices (cells of 1e-4 of the model's size, the 27 around it) and the
    triangle takes its corners' vote. Only a triangle none of whose corners touch the surface (a corner of a face's
    rectangle) is matched by the nearest vertex, against all of them. Returns the soup with `piece` set on them."""
    new = soup.cap & (soup.piece < 0)
    body = ~soup.cap
    if not new.any() or not body.any():
        return soup
    cell = scale * 1e-4
    bp = soup.P[body].reshape(-1, 3)
    bl = np.repeat(soup.piece[body], 3)
    keys = np.floor(bp / cell).astype(np.int64)
    _, first = np.unique(keys, axis=0, return_index=True)
    grid = {tuple(k): int(bl[i]) for k, i in zip(keys[first].tolist(), first.tolist())}
    corners = soup.P[new].reshape(-1, 3)
    near = np.full(len(corners), -1, np.int64)
    steps = [(i, j, k) for i in (-1, 0, 1) for j in (-1, 0, 1) for k in (-1, 0, 1)]
    for n, (x, y, z) in enumerate(np.floor(corners / cell).astype(np.int64).tolist()):
        for i, j, k in steps:
            hit = grid.get((x + i, y + j, z + k))
            if hit is not None:
                near[n] = hit
                break
    votes = near.reshape(-1, 3)
    pick = np.full(len(votes), -1, np.int64)
    for c in range(3):
        mine = votes[:, c]
        agree = (votes == mine[:, None]).sum(1)
        better = (mine >= 0) & ((pick < 0) | (agree >= 2))
        pick[better] = mine[better]
    lost = np.flatnonzero(pick < 0)
    if len(lost):
        centre = soup.P[new][lost].mean(1)
        step = max(1, 2_000_000 // len(bp))
        for i in range(0, len(lost), step):
            d = ((centre[i : i + step, None, :] - bp[None, :, :]) ** 2).sum(-1)
            pick[lost[i : i + step]] = bl[d.argmin(1)]
    piece = soup.piece.copy()
    piece[new] = pick
    return Soup(soup.P, soup.N, soup.UV, soup.mat, soup.cap, piece)


def floor_pieces(soup, label, count):
    lo, hi, _ = model_scale(soup)
    height = hi[1] - lo[1] or 1.0
    ys = soup.P[:, :, 1]
    y0 = np.full(count, np.inf)
    y1 = np.full(count, -np.inf)
    np.minimum.at(y0, label, ys.min(1))
    np.maximum.at(y1, label, ys.max(1))
    return (y1 - y0 < height * FLOOR_THICK) & (y0 - lo[1] < height * FLOOR_NEAR)


def piece_boxes(soup, label, count):
    lo = np.full((count, 3), np.inf)
    hi = np.full((count, 3), -np.inf)
    np.minimum.at(lo, label, soup.P.min(1))
    np.maximum.at(hi, label, soup.P.max(1))
    return lo, hi


def basis(axis):
    a = np.asarray(axis, np.float64)
    a = a / np.linalg.norm(a)
    u = (
        np.cross([0.0, 1.0, 0.0], a)
        if abs(a[1]) < 0.9
        else np.cross([1.0, 0.0, 0.0], a)
    )
    u /= np.linalg.norm(u)
    return a, u, np.cross(a, u)


def hub_of(points, axis):
    """The centre of `points` seen along the axis (their extent's middle across it) and along it."""
    a, u, w = basis(axis)
    pa, pu, pw = points @ a, points @ u, points @ w
    return (
        a * (pa.min() + pa.max()) / 2
        + u * (pu.min() + pu.max()) / 2
        + w * (pw.min() + pw.max()) / 2
    )


def bounce_of(points, pivot, axis, steps=24):
    """A full turn about (pivot, axis): how far the part's extreme point along a fixed direction across the axis
    moves, over its radius. The direction is down for a wheel (its lowest point, the one on the ground), sideways
    for a vertical axis (a rotor, a turntable). About 0 for a round part on its true axle, about 2e/r with the axle
    e off."""
    a = np.asarray(axis, np.float64) / np.linalg.norm(axis)
    d = points - pivot
    radial = d - np.outer(d @ a, a)
    radius = float(np.linalg.norm(radial, axis=1).max())
    if radius <= 0:
        return None, None
    g = np.array([0.0, -1.0, 0.0]) if abs(a[1]) <= 0.9 else np.array([1.0, 0.0, 0.0])
    g = g - a * (g @ a)
    g /= np.linalg.norm(g)
    if len(d) > 4000:
        d = d[:: len(d) // 4000 + 1]
    reach = []
    for k in range(steps):
        t = 2 * math.pi * k / steps
        c, s_ = math.cos(t), math.sin(t)
        turned = d * c + np.cross(a, d) * s_ + np.outer(d @ a, a) * (1 - c)  # Rodrigues
        reach.append((turned @ g).max())
    return (max(reach) - min(reach)) / radius, radius


# ── The cut ────────────────────────────────────────────────────────────────────────────────────────────────────


def box_planes(box):
    lo, hi = np.asarray(box["min"], np.float64), np.asarray(box["max"], np.float64)
    planes = []
    for k in range(3):
        n = np.zeros(3)
        n[k] = 1
        planes.append((n.copy(), hi[k]))
        planes.append((-n, -lo[k]))
    return planes  # in FACE_NAMES order


def clip_poly(poly, n, d):
    """Splits a convex polygon (rows: x y z nx ny nz u v) by the plane n.p = d: (the part with n.p <= d, the rest)."""
    dist = poly[:, :3] @ n - d
    out = dist > 0
    if not out.any():
        return poly, None
    if out.all():
        return None, poly
    ins, outs = [], []
    m = len(poly)
    for i in range(m):
        a, b = poly[i], poly[(i + 1) % m]
        da, db = dist[i], dist[(i + 1) % m]
        (outs if da > 0 else ins).append(a)
        if (da > 0) != (db > 0):
            # The same edge from either side gives the same point: endpoints in a fixed order.
            if tuple(a[:3]) > tuple(b[:3]):
                a, b, da, db = b, a, db, da
            t = da / (da - db)
            p = a + (b - a) * t
            ins.append(p)
            outs.append(p)
    ins = np.array(ins) if len(ins) >= 3 else None
    outs = np.array(outs) if len(outs) >= 3 else None
    return ins, outs


def fan(poly):
    return [np.array([poly[0], poly[i], poly[i + 1]]) for i in range(1, len(poly) - 1)]


def to_soup(tris, mats, pieces):
    if not tris:
        return Soup.empty()
    t = np.array(tris)
    N = t[:, :, 3:6]
    N = N / np.maximum(np.linalg.norm(N, axis=2, keepdims=True), 1e-12)
    return Soup(t[:, :, :3], N, t[:, :, 6:8], np.array(mats), None, np.array(pieces))


def split_by_boxes(soup, boxes, planes_of=None):
    """(the triangles inside the union of the boxes, those outside), the straddling ones clipped along the faces."""
    planes_of = planes_of or [box_planes(b) for b in boxes]
    inside = np.zeros(len(soup), bool)
    straddle = np.zeros(len(soup), bool)
    for planes in planes_of:
        n = np.array([p[0] for p in planes])
        d = np.array([p[1] for p in planes])
        dist = soup.P @ n.T - d  # (T, 3, 6)
        out = dist > 0
        all_in = ~out.any(axis=(1, 2))
        all_out = out.all(axis=1).any(axis=1)
        inside |= all_in
        straddle |= ~all_in & ~all_out
    straddle &= ~inside
    keep_in = [soup.take(inside)]
    keep_out = [soup.take(~inside & ~straddle)]
    tri_in, mat_in, tri_out, mat_out, pc_in, pc_out = [], [], [], [], [], []
    rows = np.concatenate([soup.P, soup.N, soup.UV], axis=2)
    for t in np.flatnonzero(straddle):
        rest = [rows[t]]
        for planes in planes_of:
            next_rest = []
            for poly in rest:
                for n, d in planes:
                    ins, outs = clip_poly(poly, n, d)
                    if outs is not None:
                        next_rest.append(outs)
                    poly = ins
                    if poly is None:
                        break
                if poly is not None:
                    for tri in fan(poly):
                        tri_in.append(tri)
                        mat_in.append(soup.mat[t])
                        pc_in.append(soup.piece[t])
            rest = next_rest
        for poly in rest:
            for tri in fan(poly):
                tri_out.append(tri)
                mat_out.append(soup.mat[t])
                pc_out.append(soup.piece[t])
    keep_in.append(to_soup(tri_in, mat_in, pc_in))
    keep_out.append(to_soup(tri_out, mat_out, pc_out))
    return Soup.join(keep_in), Soup.join(keep_out)


def cross_section(soup, axis, value):
    """The model's surface cut by the plane coord[axis] = value: segments chained into loops. Returns (closed loops,
    open chains), each a list of (points (k, 3), uv (k, 2), material)."""
    dist = soup.P[:, :, axis] - value
    pos = dist >= 0
    count = pos.sum(1)
    hit = np.flatnonzero((count == 1) | (count == 2))
    if not len(hit):
        return [], []
    p, uv, dd, sign = soup.P[hit], soup.UV[hit], dist[hit], pos[hit]
    # The vertex alone on its side, and its two edges.
    lone = np.where(count[hit] == 1, np.argmax(sign, axis=1), np.argmin(sign, axis=1))
    rows = np.arange(len(hit))
    ends = []
    for step in (1, 2):
        other = (lone + step) % 3
        a, b = p[rows, lone], p[rows, other]
        ua, ub = uv[rows, lone], uv[rows, other]
        da, db = dd[rows, lone], dd[rows, other]
        # A fixed order of the endpoints, so the triangles on both sides of an edge give the same point.
        swap = (a[:, 0] > b[:, 0]) | (
            (a[:, 0] == b[:, 0])
            & ((a[:, 1] > b[:, 1]) | ((a[:, 1] == b[:, 1]) & (a[:, 2] > b[:, 2])))
        )
        a, b = np.where(swap[:, None], b, a), np.where(swap[:, None], a, b)
        ua, ub = np.where(swap[:, None], ub, ua), np.where(swap[:, None], ua, ub)
        da, db = np.where(swap, db, da), np.where(swap, da, db)
        t = (da / (da - db))[:, None]
        pt = a + (b - a) * t
        pt[:, axis] = value
        ends.append((pt, ua + (ub - ua) * t))
    mats = soup.mat[hit]
    keys = {}
    segs = []
    seen = set()
    for i in range(len(hit)):
        ka, kb = ends[0][0][i].tobytes(), ends[1][0][i].tobytes()
        if ka == kb or (ka, kb) in seen or (kb, ka) in seen:
            continue
        seen.add((ka, kb))
        s = len(segs)
        segs.append((ka, kb, i))
        keys.setdefault(ka, []).append(s)
        keys.setdefault(kb, []).append(s)
    point = {}
    for i in range(len(hit)):
        point[ends[0][0][i].tobytes()] = (ends[0][0][i], ends[0][1][i])
        point[ends[1][0][i].tobytes()] = (ends[1][0][i], ends[1][1][i])
    used = np.zeros(len(segs), bool)
    closed, chains = [], []

    def walk(start_seg, start_key):
        order, mat_votes = [start_key], []
        key, s = start_key, start_seg
        while True:
            used[s] = True
            mat_votes.append(mats[segs[s][2]])
            ka, kb, _ = segs[s]
            key = kb if key == ka else ka
            if key == order[0]:
                return order, mat_votes, True
            order.append(key)
            nxt = [t for t in keys[key] if not used[t]]
            if not nxt:
                return order, mat_votes, False
            s = nxt[0]

    # Open chains first, from their ends, so a loop is never entered halfway along one.
    for key, ss in keys.items():
        if len(ss) == 1 and not used[ss[0]]:
            order, votes, _ = walk(ss[0], key)
            chains.append(order_points(order, point, votes))
    for s in range(len(segs)):
        if not used[s]:
            order, votes, ok = walk(s, segs[s][0])
            (closed if ok and len(order) >= 3 else chains).append(
                order_points(order, point, votes)
            )
    return closed, chains


def order_points(order, point, votes):
    pts = np.array([point[k][0] for k in order])
    uvs = np.array([point[k][1] for k in order])
    return pts, uvs, int(np.bincount(np.asarray(votes) + 1).argmax() - 1)


def signed_area(poly):
    x, y = poly[:, 0], poly[:, 1]
    return 0.5 * float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))


def point_in_poly(pt, poly):
    x, y = pt
    xs, ys = poly[:, 0], poly[:, 1]
    xn, yn = np.roll(xs, -1), np.roll(ys, -1)
    cross = (ys > y) != (yn > y)
    with np.errstate(divide="ignore", invalid="ignore"):
        xi = xs + (y - ys) * (xn - xs) / (yn - ys)
    return bool(np.count_nonzero(cross & (x < xi)) % 2)


def segments_cross(p, q, a, b):
    """Whether segment p-q properly crosses any of the segments a[i]-b[i]."""

    def orient(o, s, t):
        return (s[..., 0] - o[..., 0]) * (t[..., 1] - o[..., 1]) - (
            s[..., 1] - o[..., 1]
        ) * (t[..., 0] - o[..., 0])

    d1, d2 = orient(a, b, p), orient(a, b, q)
    d3, d4 = orient(p, q, a), orient(p, q, b)
    return bool(np.any((d1 * d2 < 0) & (d3 * d4 < 0)))


def bridge_holes(outer, holes):
    """One polygon (a list of indices into the stacked points) with each hole joined to the outer ring by a
    two-way cut, so ear clipping can fill a ring with holes (the bore of a barrel, a hollow turret)."""
    pts = [outer] + holes
    offsets = np.cumsum([0] + [len(p) for p in pts])
    allpts = np.concatenate(pts)
    ring = list(range(len(outer)))
    edges_a, edges_b = [], []
    for h, hole in enumerate(holes):
        idx = offsets[h + 1] + np.arange(len(hole))
        edges_a.append(allpts[idx])
        edges_b.append(allpts[np.roll(idx, -1)])
    order = sorted(range(len(holes)), key=lambda h: -holes[h][:, 0].max())
    for h in order:
        hole = holes[h]
        m = int(np.argmax(hole[:, 0]))
        hidx = [offsets[h + 1] + (m + k) % len(hole) for k in range(len(hole))]
        M = allpts[hidx[0]]
        ring_pts = allpts[ring]
        a = np.concatenate([ring_pts] + edges_a)
        b = np.concatenate([np.roll(ring_pts, -1, axis=0)] + edges_b)
        best = None
        for i in np.argsort(np.linalg.norm(ring_pts - M, axis=1)):
            P = ring_pts[i]
            keep = ~(
                np.all(a == P, axis=1)
                | np.all(b == P, axis=1)
                | np.all(a == M, axis=1)
                | np.all(b == M, axis=1)
            )
            if not segments_cross(M, P, a[keep], b[keep]):
                best = i
                break
        if best is None:
            best = int(np.argmin(np.linalg.norm(ring_pts - M, axis=1)))
        ring = ring[: best + 1] + hidx + [hidx[0], ring[best]] + ring[best + 1 :]
    return allpts, ring


def ear_clip(points, ring):
    """Triangles (index triples) filling the counter-clockwise polygon `ring` (indices into `points`)."""
    ring = list(ring)
    tris = []
    guard = 0
    while len(ring) > 3 and guard < 10 * len(points) + 100:
        guard += 1
        P = points[ring]
        prev, nxt = np.roll(P, 1, axis=0), np.roll(P, -1, axis=0)
        cross = (P[:, 0] - prev[:, 0]) * (nxt[:, 1] - prev[:, 1]) - (
            P[:, 1] - prev[:, 1]
        ) * (nxt[:, 0] - prev[:, 0])
        cut = None
        for i in np.argsort(-cross):
            if cross[i] <= 0:
                break
            a, b, c = prev[i], P[i], nxt[i]
            others = np.ones(len(ring), bool)
            others[[i - 1, i, (i + 1) % len(ring)]] = False
            q = P[others]
            q = q[
                ~(
                    np.all(q == a, axis=1)
                    | np.all(q == b, axis=1)
                    | np.all(q == c, axis=1)
                )
            ]
            if len(q):
                d1 = (b[0] - a[0]) * (q[:, 1] - a[1]) - (b[1] - a[1]) * (q[:, 0] - a[0])
                d2 = (c[0] - b[0]) * (q[:, 1] - b[1]) - (c[1] - b[1]) * (q[:, 0] - b[0])
                d3 = (a[0] - c[0]) * (q[:, 1] - c[1]) - (a[1] - c[1]) * (q[:, 0] - c[0])
                if np.any((d1 >= 0) & (d2 >= 0) & (d3 >= 0)):
                    continue
            cut = i
            break
        if cut is None:
            # Nothing is a clean ear (a self-touching loop from overlapping shells): take the flattest corner, so the
            # fill always ends.
            cut = int(np.argmin(np.abs(cross)))
        n = len(ring)
        tri = (ring[cut - 1], ring[cut], ring[(cut + 1) % n])
        if abs(cross[cut]) > 0:
            tris.append(tri)
        del ring[cut]
    if len(ring) == 3:
        tris.append(tuple(ring))
    return tris


def fill_loops(loops2d):
    """Even-odd fill of closed 2D loops: a loop inside an odd number of others is a hole of the one around it.
    Returns (points (k, 2), triangles (m, 3)) with every triangle counter-clockwise."""
    loops = [l for l in loops2d if len(l) >= 3 and abs(signed_area(l)) > 0]
    depth, parent = [0] * len(loops), [None] * len(loops)
    areas = [abs(signed_area(l)) for l in loops]
    for i, li in enumerate(loops):
        containers = [
            j
            for j, lj in enumerate(loops)
            if j != i and areas[j] > areas[i] and point_in_poly(li[0], lj)
        ]
        depth[i] = len(containers)
        if containers:
            parent[i] = min(containers, key=lambda j: areas[j])
    all_pts, all_tris, base = [], [], 0
    for i, li in enumerate(loops):
        if depth[i] % 2:
            continue
        outer = li if signed_area(li) > 0 else li[::-1]
        holes = [
            lj if signed_area(lj) < 0 else lj[::-1]
            for j, lj in enumerate(loops)
            if parent[j] == i and depth[j] % 2
        ]
        pts, ring = bridge_holes(outer, holes)
        tris = ear_clip(pts, ring)
        all_pts.append(pts)
        all_tris.extend((a + base, b + base, c + base) for a, b, c in tris)
        base += len(pts)
    if not all_pts:
        return np.zeros((0, 2)), np.zeros((0, 3), np.int64)
    return np.concatenate(all_pts), np.array(all_tris, np.int64).reshape(-1, 3)


def clip_loop(poly, lo, hi):
    """A 2D loop clipped to the rectangle lo..hi (Sutherland-Hodgman); None when nothing is left."""
    for k in range(2):
        for sign, edge in ((1, hi[k]), (-1, lo[k])):
            if poly is None or len(poly) < 3:
                return None
            d = sign * (poly[:, k] - edge)
            if (d <= 0).all():
                continue
            out = []
            m = len(poly)
            for i in range(m):
                a, b = poly[i], poly[(i + 1) % m]
                da, db = d[i], d[(i + 1) % m]
                if da <= 0:
                    out.append(a)
                if (da <= 0) != (db <= 0):
                    t = da / (da - db)
                    q = a + (b - a) * t
                    q[k] = edge
                    out.append(q)
            poly = np.array(out) if len(out) >= 3 else None
    return poly


def nudge_boxes(source, boxes, scale):
    """Moves a box face that lies exactly on a flat surface of the model (a deck, a floor) a hair outward, so the
    surface stays on one side of the cut instead of going with the part."""
    flat = source.P.reshape(-1, 3)
    step = scale * 1e-5
    for b in boxes:
        for k in range(3):
            for key, sign in (("min", -1), ("max", 1)):
                for _ in range(8):
                    if not np.any(np.abs(flat[:, k] - b[key][k]) < step * 0.1):
                        break
                    b[key][k] += sign * step
    return boxes


def caps_for(source, part_boxes, b, scale):
    """The caps of box b's faces: the source's cross-section on each face's plane, kept inside the face and outside
    the part's other boxes. Returns (part caps, rest caps, per-face report, cut-loop points per face)."""
    box = part_boxes[b]
    lo, hi = np.asarray(box["min"], np.float64), np.asarray(box["max"], np.float64)
    planes = box_planes(box)
    smin, smax = source.P.reshape(-1, 3).min(0), source.P.reshape(-1, 3).max(0)
    part_caps, rest_caps, faces, loop_points = [], [], [], {}
    eps = scale * 1e-7
    for f, (n, d) in enumerate(planes):
        axis = f // 2
        value = hi[axis] if f % 2 == 0 else lo[axis]
        if value <= smin[axis] + eps or value >= smax[axis] - eps:
            continue  # the face is clear of the model: nothing to cut
        others = [k for k in range(3) if k != axis]
        closed, chains = cross_section(source, axis, value)

        def touches(pts):
            plo, phi = pts.min(0), pts.max(0)
            return all(plo[k] <= hi[k] and phi[k] >= lo[k] for k in others)

        # A closed loop counts when some of the area it bounds is on the face (its bounds overlapping is not enough:
        # an L-shaped slice can reach round the face); each is clipped to the face here, so where a cut runs across
        # two faces both caps end on the same points.
        rect = (lo[others], hi[others])
        clipped = []
        for c in closed:
            if touches(c[0]):
                l2 = clip_loop(c[0][:, others], *rect)
                if l2 is not None and abs(signed_area(l2)) > (scale * 1e-5) ** 2:
                    clipped.append((c, l2))
        closed = [c for c, _ in clipped]
        chains = [c for c in chains if touches(c[0])]
        # A chain that only crosses the face's edge region with its far ends outside is still open on this face:
        # keep only the chains with a point inside the face.
        def inside_face(pts):
            m = np.ones(len(pts), bool)
            for k in others:
                m &= (pts[:, k] >= lo[k] - eps) & (pts[:, k] <= hi[k] + eps)
            return m

        chains = [c for c in chains if inside_face(c[0]).any()]
        if not closed and not chains:
            continue
        inner = [c[0][inside_face(c[0])] for c in closed + chains]
        loop_points[f] = (
            np.concatenate([p for p in inner if len(p)])
            if any(len(p) for p in inner)
            else np.zeros((0, 3))
        )
        face = {
            "face": FACE_NAMES[f],
            "at": round(float(value), 5),
            "_at": float(
                value
            ),  # the plane itself, for the seam check (dropped from the report)
            "loops": len(closed),
            "open": len(chains),
        }
        if chains:
            ends = np.concatenate([c[0][[0, -1]] for c in chains])
            on_edge = np.zeros(len(ends), bool)
            for k in others:
                on_edge |= (np.abs(ends[:, k] - lo[k]) < scale * 1e-4) | (
                    np.abs(ends[:, k] - hi[k]) < scale * 1e-4
                )
                on_edge |= (ends[:, k] < lo[k]) | (ends[:, k] > hi[k])
            face["openWhy"] = (
                "runs off the face" if on_edge.all() else "the model is open here"
            )
        faces.append(face)
        if not closed:
            continue
        pts2, tris = fill_loops([l2 for _, l2 in clipped])
        if not len(tris):
            continue
        P3 = np.zeros((len(pts2), 3))
        P3[:, others] = pts2
        P3[:, axis] = value
        # The cap's colour: one texel of the surface where the cut is, at the loop point nearest the cut's middle.
        allp = np.concatenate([c[0] for c in closed])
        alluv = np.concatenate([c[1] for c in closed])
        allmat = np.concatenate([np.full(len(c[0]), c[2]) for c in closed])
        near = int(np.argmin(np.linalg.norm(allp - allp.mean(0), axis=1)))
        uv, mat = alluv[near], allmat[near]
        tri = P3[tris]
        # Counter-clockwise in (others[0], others[1]) faces +axis when (others[0], others[1], axis) is right-handed.
        right = (others[0], others[1], axis) in ((0, 1, 2), (1, 2, 0), (2, 0, 1))
        if right != (n[axis] > 0):
            tri = tri[:, ::-1]
        count = len(tri)
        caps = Soup(
            tri,
            np.broadcast_to(n, (count, 3, 3)).copy(),
            np.broadcast_to(uv, (count, 3, 2)).copy(),
            np.full(count, mat),
            np.ones(count, bool),
        )
        # Inside the face only, and not where another box of the part reaches (that is inside the part).
        side = [box_planes(box)[k] for k in range(6) if k // 2 != axis]
        caps, _ = split_by_boxes(caps, None, [side])
        for k, other in enumerate(part_boxes):
            if k != b and len(caps):
                _, caps = split_by_boxes(caps, [other])
        if not len(caps):
            continue
        caps.cap[:] = True
        part_caps.append(caps)
        rest_caps.append(
            Soup(
                caps.P[:, ::-1].copy(),
                -caps.N,
                caps.UV.copy(),
                caps.mat.copy(),
                np.ones(len(caps), bool),
            )
        )
    return Soup.join(part_caps), Soup.join(rest_caps), faces, loop_points


def numpy_cut(source, boxes, scale):
    """(part, rest, faces report, loop points by (box, face)) for a cut part."""
    nudge_boxes(source, boxes, scale)
    part, rest = split_by_boxes(source, boxes)
    caps_in, caps_out, faces, loops = [], [], [], {}
    for b in range(len(boxes)):
        ci, co, fr, lp = caps_for(source, boxes, b, scale)
        caps_in.append(ci)
        caps_out.append(co)
        for f in fr:
            f["box"] = b
        faces.extend(fr)
        for f, pts in lp.items():
            loops[(b, f)] = pts
    return Soup.join([part] + caps_in), Soup.join([rest] + caps_out), faces, loops


# ── Blender (optional): the same cut with Blender's bisect and fill ────────────────────────────────────────────


def usable_blender(path):
    """`path` as an absolute, existing Blender executable, or None. On Windows only a .exe counts: a .bat or .cmd
    named blender in some folder is not Blender."""
    if not path:
        return None
    path = os.path.abspath(path)
    if not os.path.isfile(path):
        return None
    if sys.platform == "win32" and not path.lower().endswith(".exe"):
        return None
    return path


def find_blender(explicit=None):
    """Blender's absolute path: `explicit` (a path, or a name looked up on PATH), else `blender` on PATH, else its
    usual install folders. PATH only: Windows' own lookup tries the current folder first, which is usually the
    user's project, where downloaded files land."""
    path_only = os.environ.get("PATH", "")
    if explicit:
        named = (
            explicit
            if os.path.dirname(explicit)
            else shutil.which(explicit, path=path_only)
        )
        return usable_blender(named)
    found = usable_blender(shutil.which("blender", path=path_only))
    if found:
        return found
    candidates = []
    if sys.platform == "win32":
        for var in ("ProgramFiles", "ProgramFiles(x86)"):
            root = os.environ.get(var, "")
            if not os.path.isabs(root):
                continue
            base = os.path.join(root, "Blender Foundation")
            if os.path.isdir(base):
                for d in sorted(os.listdir(base), reverse=True):
                    candidates.append(os.path.join(base, d, "blender.exe"))
            candidates.append(
                os.path.join(
                    root, "Steam", "steamapps", "common", "Blender", "blender.exe"
                )
            )
    elif sys.platform == "darwin":
        candidates.append("/Applications/Blender.app/Contents/MacOS/Blender")
    else:
        candidates += [
            "/usr/bin/blender",
            "/snap/bin/blender",
            os.path.expanduser("~/blender/blender"),
        ]
    return next(
        (c for c in map(usable_blender, candidates) if c and os.path.isabs(c)), None
    )


def blender_cut(blender, source, boxes, scale):
    """The cut done by Blender (model_parts_blender.py, run headless): its bisect splits the surface along the boxes,
    the part is separated from the rest, and each side's opening is filled (scanfill, holes included). Same return
    as numpy_cut."""
    nudge_boxes(source, boxes, scale)
    work = tempfile.mkdtemp(prefix="model-parts-")
    try:
        src, dst = os.path.join(work, "in.npz"), os.path.join(work, "out.npz")
        lo = np.array([b["min"] for b in boxes], np.float64)
        hi = np.array([b["max"] for b in boxes], np.float64)
        np.savez(
            src,
            P=source.P,
            N=source.N,
            UV=source.UV,
            mat=source.mat,
            cap=source.cap,
            piece=source.piece
            + 1,  # 0 is what Blender gives the faces it makes: back as -1, a cap
            lo=lo,
            hi=hi,
            scale=scale,
        )
        script = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "model_parts_blender.py"
        )
        cmd = [
            blender,
            "--background",
            "--factory-startup",
            "--python-exit-code",
            "1",
            "--python",
            script,
            "--",
            src,
            dst,
        ]
        try:
            r = subprocess.run(
                cmd, capture_output=True, text=True, timeout=BLENDER_TIMEOUT
            )
        except subprocess.TimeoutExpired:
            raise PlanError(f"Blender did not finish the cut in {BLENDER_TIMEOUT} s")
        except OSError as e:
            raise PlanError(f"Blender could not be started ({blender}): {e}")
        if r.returncode != 0 or not os.path.isfile(dst):
            tail = "\n".join((r.stdout + r.stderr).strip().splitlines()[-12:])
            raise PlanError(
                f"Blender could not cut the part (exit {r.returncode}): {tail}"
            )
        z = np.load(dst, allow_pickle=False)
        part = Soup(
            z["inP"], z["inN"], z["inUV"], z["inMat"], z["inCap"], z["inPiece"] - 1
        )
        rest = Soup(
            z["outP"],
            z["outN"],
            z["outUV"],
            z["outMat"],
            z["outCap"],
            z["outPiece"] - 1,
        )
        faces = json.loads(str(z["faces"]))
        loops = {}
        for key in z.files:
            if key.startswith("loop_"):
                _, b, f = key.split("_")
                loops[(int(b), int(f))] = z[key]
        return part, rest, faces, loops
    finally:
        shutil.rmtree(work, ignore_errors=True)


# ── The plan ───────────────────────────────────────────────────────────────────────────────────────────────────


def read_plan(path):
    try:
        plan = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise PlanError(f"cannot read the plan {path}: {e}")
    if (
        not isinstance(plan, dict)
        or not isinstance(plan.get("parts"), list)
        or not plan["parts"]
    ):
        raise PlanError('the plan needs "parts": a list of at least one part')
    root = plan.get("root", "Root")
    names = [root]
    for p in plan["parts"]:
        if not isinstance(p, dict):
            raise PlanError(
                f"each part is an object with a name, boxes and the rest, not {p!r}"
            )
        name = p.get("name")
        if not isinstance(name, str) or not name or set(name) - NAME_OK:
            raise PlanError(f"part name {name!r}: letters, digits, - and _ only")
        if name in names:
            raise PlanError(f"part name {name!r} is used twice (the root is {root!r})")
        names.append(name)
    for p in plan["parts"]:
        p.setdefault("parent", root)
        if p["parent"] not in names or p["parent"] == p["name"]:
            raise PlanError(
                f"{p['name']}: parent {p['parent']!r} is not the root or another part"
            )
        mode = p.setdefault("mode", "cut")
        if mode not in ("cut", "pieces"):
            raise PlanError(f"{p['name']}: mode must be cut or pieces, not {mode!r}")
        boxes = p.get("boxes")
        if not isinstance(boxes, list) or not boxes:
            raise PlanError(
                f"{p['name']}: boxes must be a list of one or more {{\"min\": [x, y, z], \"max\": [x, y, z]}}"
            )
        for b in boxes:
            try:
                lo, hi = [float(v) for v in b["min"]], [float(v) for v in b["max"]]
            except (KeyError, TypeError, ValueError):
                raise PlanError(
                    f"{p['name']}: each box is {{\"min\": [x, y, z], \"max\": [x, y, z]}}"
                )
            if len(lo) != 3 or len(hi) != 3 or any(h <= l for l, h in zip(lo, hi)):
                raise PlanError(
                    f"{p['name']}: a box's max must be above its min on every axis ({b})"
                )
            b["min"], b["max"] = lo, hi
        axis = p.get("axis", "y")
        axis = AXES.get(axis, axis) if isinstance(axis, str) else axis
        try:
            axis = np.array(axis, np.float64)
            assert axis.shape == (3,) and np.linalg.norm(axis) > 0
        except (AssertionError, ValueError, TypeError):
            raise PlanError(f"{p['name']}: axis must be x, y, z or [x, y, z]")
        p["axis"] = (axis / np.linalg.norm(axis)).tolist()
        pivot = p.setdefault("pivot", "hub" if p.get("spin") else "ring")
        ok = (
            pivot in ("ring", "root", "hub")
            or (isinstance(pivot, list) and len(pivot) == 3)
            or (
                isinstance(pivot, dict)
                and isinstance(pivot.get("edge"), list)
                and len(pivot["edge"]) == 3
            )
        )
        try:
            if isinstance(pivot, list):
                p["pivot"] = [float(v) for v in pivot]
            elif isinstance(pivot, dict) and ok:
                pivot["edge"] = [float(v) for v in pivot["edge"]]
                if not any(pivot["edge"]):
                    ok = False
        except (TypeError, ValueError):
            ok = False
        if not ok:
            raise PlanError(
                f'{p["name"]}: pivot must be ring, root, hub, {{"edge": [x, y, z]}} or [x, y, z], with numbers'
            )
        p["spin"] = bool(p.get("spin", False))
        rng = p.get("range", [-180.0, 180.0] if p["spin"] else DEFAULT_RANGE)
        if not (
            isinstance(rng, list)
            and len(rng) == 2
            and all(isinstance(v, (int, float)) for v in rng)
            and rng[0] < rng[1]
        ):
            raise PlanError(f"{p['name']}: range must be [min, max] in degrees")
        p["range"] = [float(rng[0]), float(rng[1])]
    seen = {root}
    order = []
    pending = list(plan["parts"])
    while pending:
        ready = [p for p in pending if p["parent"] in seen]
        if not ready:
            raise PlanError(
                "the parts' parents loop: " + ", ".join(p["name"] for p in pending)
            )
        for p in ready:
            seen.add(p["name"])
            order.append(p)
            pending.remove(p)
    plan["root"] = root
    plan["floor"] = plan.get("floor", "keep")
    if plan["floor"] not in ("keep", "drop"):
        raise PlanError('"floor" must be keep or drop')
    return plan, order


def depth_of(name, by_name, root):
    d = 0
    while name != root:
        name = by_name[name]["parent"]
        d += 1
    return d


# ── The pivots ─────────────────────────────────────────────────────────────────────────────────────────────────


def cap_centroid(soup, facing):
    sel = soup.cap.copy()
    if not sel.any():
        return None
    n = soup.N[:, 0]
    vertical = np.abs(n[:, 1]) > 0.9
    sel &= vertical if facing == "updown" else ~vertical
    if not sel.any():
        return None
    P = soup.P[sel]
    area = 0.5 * np.linalg.norm(np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]), axis=1)
    if area.sum() <= 0:
        return None
    return (P.mean(1) * area[:, None]).sum(0) / area.sum()


def pivot_for(p, soup, loops, scale, hub=None, ring=None):
    rule = p["pivot"]
    if isinstance(rule, list):
        return np.array(rule, np.float64), "given"
    if rule == "hub":
        if hub is not None:
            return hub, "hub"
        return hub_of(soup.P.reshape(-1, 3), p["axis"]), "hub"
    loop_pts = {f: pts for (b, f), pts in loops.items() if len(pts)}
    if isinstance(rule, dict):
        direction = np.array(rule["edge"], np.float64)
        direction /= np.linalg.norm(direction) or 1.0
        pts = soup.P[soup.cap].reshape(-1, 3)
        source = "cap edge"
        if not len(pts) and loop_pts:
            pts, source = np.concatenate(list(loop_pts.values())), "cut loop edge"
        if not len(pts):
            pts, source = soup.P.reshape(-1, 3), "part edge"
        along = pts @ direction
        near = pts[along >= along.max() - scale * 0.01]
        return (near.min(0) + near.max(0)) / 2, source
    if rule == "ring":
        c = cap_centroid(soup, "updown")
        if c is not None:
            return c, "ring cap"
        flat = [pts for f, pts in loop_pts.items() if f // 2 == 1]
        if flat:
            pts = np.concatenate(flat)
            return (pts.min(0) + pts.max(0)) / 2, "cut loop"
        if p["mode"] == "pieces":
            if ring is not None:
                return ring, "ring piece"
            pts = soup.P.reshape(-1, 3)
            y0 = pts[:, 1].min()
            foot = pts[pts[:, 1] <= y0 + scale * 0.01]
            c = (foot.min(0) + foot.max(0)) / 2
            c[1] = y0
            return c, "footprint"
        return None, None
    if rule == "root":
        c = cap_centroid(soup, "side")
        if c is not None:
            return c, "root cap"
        side = [pts for f, pts in loop_pts.items() if f // 2 != 1]
        if side:
            pts = np.concatenate(side)
            return (pts.min(0) + pts.max(0)) / 2, "cut loop"
        return None, None
    return None, None


def ring_piece(part, axis, source, label, count, floor, scale):
    """The round piece a separate turning part sits on (a turret ring, a neck collar), on either side of the seam:
    round about the axis, flat along it (a ring, not the part's own shell), at the part's lowest point, at least a
    third of the part's width. Its centre seen along
    the axis, at the part's seat; None when there is none."""
    a, u, w = basis(axis)
    pts = part.P.reshape(-1, 3)
    seat = (pts @ a).min()
    pu, pw = pts @ u, pts @ w
    width = min(np.ptp(pu), np.ptp(pw))
    height = np.ptp(source.P.reshape(-1, 3) @ a) or 1.0
    best, best_width = None, 0.0
    for m in range(count):
        if floor[m]:
            continue
        q = source.P[label == m].reshape(-1, 3)
        qa, qu, qw = q @ a, q @ u, q @ w
        du, dw = np.ptp(qu), np.ptp(qw)
        if (
            min(du, dw) < width / 3
            or abs(du - dw) > 0.1 * max(du, dw)
            or np.ptp(qa) > 0.4 * min(du, dw)
        ):
            continue  # not round about the axis, too small, or too tall for a ring (the part's own shell)
        if qa.max() < seat - 0.05 * height or qa.min() > seat + 0.05 * height:
            continue
        cu, cw = (qu.min() + qu.max()) / 2, (qw.min() + qw.max()) / 2
        if not (pu.min() <= cu <= pu.max() and pw.min() <= cw <= pw.max()):
            continue  # a collar elsewhere at the same height (another turret's ring): not under this part
        if min(du, dw) > best_width:
            best_width = min(du, dw)
            best = (
                u * (qu.min() + qu.max()) / 2 + w * (qw.min() + qw.max()) / 2 + a * seat
            )
    return best


def spin_pieces(soup, label, members, axis):
    """The spinning part's pieces: the one widest across the axle and the ones inside its swept cylinder. Returns
    (kept piece ids, left piece ids, hub)."""
    a, u, w = basis(axis)
    best, best_width = None, -1
    for m in members:
        pts = soup.P[label == m].reshape(-1, 3)
        width = min(np.ptp(pts @ u), np.ptp(pts @ w))
        if width > best_width:
            best, best_width = m, width
    main = soup.P[label == best].reshape(-1, 3)
    hub = hub_of(main, axis)
    d = main - hub
    along = d @ a
    radius = np.linalg.norm(d - np.outer(along, a), axis=1).max()
    a0, a1 = along.min(), along.max()
    kept, left = [best], []
    for m in members:
        if m == best:
            continue
        d = soup.P[label == m].reshape(-1, 3) - hub
        al = d @ a
        r = np.linalg.norm(d - np.outer(al, a), axis=1)
        inside = (
            (al >= a0 - radius * SPIN_SIDE)
            & (al <= a1 + radius * SPIN_SIDE)
            & (r <= radius * SPIN_REACH)
        )
        (kept if inside.all() else left).append(m)
    return kept, left, hub


# ── GLB out ────────────────────────────────────────────────────────────────────────────────────────────────────


def write_glb(path, doc, binary, nodes):
    """`nodes`: [{"name", "parent" (index or None), "pivot" (world), "soup", "extras"}], parents before children."""
    out = {
        "asset": {"version": "2.0", "generator": "unity ai model_parts.py"},
        "scene": 0,
    }
    chunks = []
    offset = 0

    def add_view(data, target=None):
        nonlocal offset
        pad = (-offset) % 4
        if pad:
            chunks.append(b"\0" * pad)
            offset += pad
        view = {"buffer": 0, "byteOffset": offset, "byteLength": len(data)}
        if target:
            view["target"] = target
        chunks.append(data)
        offset += len(data)
        out.setdefault("bufferViews", []).append(view)
        return len(out["bufferViews"]) - 1

    def add_accessor(arr, kind, component, target, minmax=False):
        data = np.ascontiguousarray(arr).tobytes()
        acc = {
            "bufferView": add_view(data, target),
            "componentType": component,
            "count": len(arr),
            "type": kind,
        }
        if minmax:
            acc["min"] = arr.min(0).tolist()
            acc["max"] = arr.max(0).tolist()
        out.setdefault("accessors", []).append(acc)
        return len(out["accessors"]) - 1

    # Images, textures, samplers and materials as the source had them; image bytes copied unchanged.
    for key in ("samplers", "textures", "materials"):
        if doc.get(key):
            out[key] = json.loads(json.dumps(doc[key]))
    if doc.get("images"):
        out["images"] = []
        for img in doc["images"]:
            img = dict(img)
            if "bufferView" in img:
                data, _ = view_bytes(doc, binary, img["bufferView"])
                img["bufferView"] = add_view(bytes(data))
            out["images"].append(img)
    used = [
        e
        for e in doc.get("extensionsUsed", [])
        if not e.startswith(("KHR_draco", "EXT_meshopt", "KHR_mesh_quant"))
    ]
    if used:
        out["extensionsUsed"] = used
    required = [e for e in doc.get("extensionsRequired", []) if e in used]
    if required:
        out["extensionsRequired"] = required

    out["nodes"], out["meshes"] = [], []
    for i, node in enumerate(nodes):
        local = node["pivot"] - (
            nodes[node["parent"]]["pivot"] if node["parent"] is not None else 0
        )
        entry = {"name": node["name"], "translation": [float(v) for v in local]}
        if node.get("extras"):
            entry["extras"] = node["extras"]
        soup = node["soup"]
        if len(soup):
            prims = []
            for m in np.unique(soup.mat):
                sel = soup.mat == m
                P = (soup.P[sel] - node["pivot"]).reshape(-1, 3).astype(np.float32)
                N = soup.N[sel].reshape(-1, 3).astype(np.float32)
                UV = soup.UV[sel].reshape(-1, 2).astype(np.float32)
                rows = np.concatenate([P, N, UV], axis=1)
                uniq, inverse = np.unique(rows, axis=0, return_inverse=True)
                attrs = {
                    "POSITION": add_accessor(
                        uniq[:, :3], "VEC3", 5126, 34962, minmax=True
                    ),
                    "NORMAL": add_accessor(uniq[:, 3:6], "VEC3", 5126, 34962),
                    "TEXCOORD_0": add_accessor(uniq[:, 6:8], "VEC2", 5126, 34962),
                }
                prim = {
                    "attributes": attrs,
                    "indices": add_accessor(
                        inverse.ravel().astype(np.uint32), "SCALAR", 5125, 34963
                    ),
                    "mode": 4,
                }
                if m >= 0:
                    prim["material"] = int(m)
                prims.append(prim)
            out["meshes"].append({"name": node["name"], "primitives": prims})
            entry["mesh"] = len(out["meshes"]) - 1
        out["nodes"].append(entry)
    for i, node in enumerate(nodes):
        if node["parent"] is not None:
            out["nodes"][node["parent"]].setdefault("children", []).append(i)
    out["scenes"] = [{"nodes": [i for i, n in enumerate(nodes) if n["parent"] is None]}]
    blob = b"".join(chunks)
    blob += b"\0" * ((-len(blob)) % 4)
    out["buffers"] = [{"byteLength": len(blob)}]
    text = json.dumps(out, separators=(",", ":")).encode("utf-8")
    text += b" " * ((-len(text)) % 4)
    total = 12 + 8 + len(text) + 8 + len(blob)
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, total))
        f.write(struct.pack("<II", len(text), 0x4E4F534A) + text)
        f.write(struct.pack("<II", len(blob), 0x004E4942) + blob)
    os.replace(tmp, path)


# ── Commands ───────────────────────────────────────────────────────────────────────────────────────────────────


def r3(v):
    return [round(float(x), 4) for x in v]


def mesh_nodes(doc):
    """Every node that carries a mesh, with its name and triangle count (read from the accessors, no data)."""
    accessors = doc.get("accessors", [])
    out = []
    for i, node in enumerate(doc.get("nodes", [])):
        if "mesh" not in node:
            continue
        tris = 0
        for prim in doc["meshes"][node["mesh"]]["primitives"]:
            if prim.get("mode", 4) != 4:
                continue
            ref = prim.get("indices", prim["attributes"].get("POSITION"))
            if ref is not None and ref < len(accessors):
                tris += int(accessors[ref].get("count", 0)) // 3
        out.append({"name": node.get("name") or f"node {i}", "triangles": tris})
    return out


def cmd_inspect(a):
    doc, _, soup = load_model(a.model)
    nodes = mesh_nodes(doc)
    lo, hi, scale = model_scale(soup)
    label, count = pieces_of(soup, scale)
    floor = floor_pieces(soup, label, count)
    plo, phi = piece_boxes(soup, label, count)
    tris = np.bincount(label, minlength=count)
    order = np.argsort(-np.linalg.norm(phi - plo, axis=1))
    pieces = [
        {
            "piece": int(i),
            "centre": r3((plo[i] + phi[i]) / 2),
            "size": r3(phi[i] - plo[i]),
            "triangles": int(tris[i]),
            **({"floor": True} if floor[i] else {}),
        }
        for i in order[:40]
    ]
    axis = "xyz".index(a.axis)
    others = [k for k in range(3) if k != axis]
    blo, bhi = lo.copy(), hi.copy()
    if a.box:
        try:
            v = [float(x) for x in a.box.split(",")]
            assert len(v) == 6 and all(v[k] < v[k + 3] for k in range(3))
        except (ValueError, AssertionError):
            raise PlanError(
                "--box is minx,miny,minz,maxx,maxy,maxz with each max above its min"
            )
        blo, bhi = np.array(v[:3]), np.array(v[3:])
    eps = scale * 1e-7
    profile = []
    for k in range(a.slices):
        t = blo[axis] + (bhi[axis] - blo[axis]) * (k + 0.5) / a.slices
        closed, chains = cross_section(soup, axis, t)

        def meets(pts):
            m = np.ones(len(pts), bool)
            for j in others:
                m &= (pts[:, j] >= blo[j] - eps) & (pts[:, j] <= bhi[j] + eps)
            return m.any()

        closed = [c for c in closed if meets(c[0])]
        chains = [c for c in chains if meets(c[0])]
        row = {
            "xyz"[axis]: round(float(t), 4),
            "loops": len(closed),
            "open": len(chains),
        }
        pts = [c[0] for c in closed + chains]
        if pts:
            allp = np.concatenate(pts)
            for j in others:
                row["xyz"[j]] = r3([allp[:, j].min(), allp[:, j].max()])
            row["area"] = round(
                float(sum(abs(signed_area(c[0][:, others])) for c in closed)), 5
            )
        profile.append(row)
    print(
        json.dumps(
            {
                "triangles": len(soup),
                "min": r3(lo),
                "max": r3(hi),
                "openEdges": open_edges(soup, scale),
                "pieces": count,
                "floorPieces": int(floor.sum()),
                "largestPieces": pieces,
                "profile": profile,
                **({"meshNodes": nodes[:40]} if len(nodes) > 1 else {}),
            }
        )
    )


def cmd_split(a):
    if (
        os.path.exists(a.out)
        and os.path.exists(a.model)
        and os.path.samefile(a.out, a.model)
    ):
        raise PlanError(
            "--out is the model itself: the split never writes over the generated model"
        )
    if os.path.exists(a.out) and not a.overwrite:
        raise PlanError(
            f"--out {a.out} exists: name a new file (<stem>-parts-2.glb), or pass --overwrite for your own earlier split"
        )
    plan, order = read_plan(a.plan)
    doc, binary, soup = load_model(a.model)
    lo, hi, scale = model_scale(soup)
    by_name = {p["name"]: p for p in plan["parts"]}
    root = plan["root"]
    kernel = a.kernel
    blender = None
    if kernel in ("auto", "blender") and any(p["mode"] == "cut" for p in plan["parts"]):
        blender = find_blender(a.blender)
        if kernel == "blender" and not blender:
            raise PlanError(
                "--kernel blender: Blender was not found (pass --blender <path to the executable>)"
            )

    label, count = pieces_of(soup, scale)
    soup.piece = label
    floor = floor_pieces(soup, label, count)
    floor_ids = np.flatnonzero(floor)
    rest = soup
    results, soups, hubs, loops_of = {}, {}, {}, {}

    def take_pieces(p):
        nonlocal rest
        # A cap no piece claimed (-1) counts as a piece of its own, past the source's (never taken).
        rest_label = np.where(rest.piece >= 0, rest.piece, count)
        plo, phi = piece_boxes(rest, rest_label, count + 1)
        with np.errstate(invalid="ignore"):
            centres = (plo + phi) / 2
        present = (np.bincount(rest_label, minlength=count + 1) > 0)[:count]
        members = []
        for m in np.flatnonzero(present & ~floor):
            c = centres[m]
            if any(
                all(b["min"][k] <= c[k] <= b["max"][k] for k in range(3))
                for b in p["boxes"]
            ):
                members.append(int(m))
        left = []
        if p["spin"] and members:
            members, left, hub = spin_pieces(rest, rest_label, members, p["axis"])
            hubs[p["name"]] = hub
        take = np.isin(rest_label, members)
        soups[p["name"]] = rest.take(take)
        rest = rest.take(~take)
        results[p["name"]] = {
            "pieces": len(members),
            **({"piecesLeft": len(left)} if left else {}),
        }
        loops_of[p["name"]] = {}

    def cut_with(name, source, p, report=None):
        """One kernel's cut, with the face report every kernel shares: the source's slice on each face (loops
        closed and open, why open, from the NumPy analysis) and the open edges left along it in this result."""
        if name == "blender":
            part, rest, _, _ = blender_cut(blender, source, p["boxes"], scale)
            if report is None:
                report = numpy_cut(source, p["boxes"], scale)
            faces, loops = [dict(f) for f in report[2]], report[3]
        else:
            part, rest, faces, loops = numpy_cut(source, p["boxes"], scale)
            faces = [dict(f) for f in faces]
        # Watertight along the cut: open edges left on each cut face, on the part's side and the rest's.
        part_ends, rest_ends = open_edge_ends(part, scale), open_edge_ends(rest, scale)
        for f in faces:
            box = p["boxes"][f.pop("box", 0)]
            f["min"], f["max"] = box["min"], box["max"]
            f["seamOpenEdges"] = seam_open(part_ends, f, scale) + seam_open(
                rest_ends, f, scale
            )
            del f["min"], f["max"]
            f.pop("_at", None)
            f.pop("openEdges", None)
        return part, rest, faces, loops

    kernels_used = set()

    def cut_part(p):
        nonlocal rest
        # NumPy first (or Blender alone with --kernel blender); with auto, a cut NumPy leaves open is tried again in
        # Blender, and the one with fewer open edges along the cut is kept (compared on those edges alone).
        first = "blender" if kernel == "blender" else "numpy"
        best = cut_with(first, rest, p) + (first,)
        seam = lambda r: sum(f["seamOpenEdges"] for f in r[2])  # noqa: E731
        tried, blender_error = None, None
        if kernel == "auto" and blender and seam(best):
            # Blender is a retry here: if it fails, the NumPy cut stands and the failure is reported.
            try:
                other = cut_with("blender", rest, p, best[:4]) + ("blender",)
                tried = {"numpy": seam(best), "blender": seam(other)}
                if seam(other) < seam(best):
                    best = other
            except PlanError as e:
                blender_error = str(e)
        part, rest, faces, loops, used = best
        rest = label_caps(rest, scale)
        kernels_used.add(used)
        soups[p["name"]] = part
        loops_of[p["name"]] = loops
        results[p["name"]] = {
            "kernel": used,
            "faces": faces,
            **({"openAlongCutBy": tried} if tried else {}),
            **({"blenderError": blender_error} if blender_error else {}),
        }

    # Children before their parents, whatever their mode: whole pieces first from the untouched model, except a
    # whole-piece part with a cut part under it, which waits for that cut (a cannon cut from a separate turret).
    def under(q, ancestor):
        while q["parent"] != root:
            if q["parent"] == ancestor:
                return True
            q = by_name[q["parent"]]
        return False

    waits = {
        q["name"]
        for q in order
        if q["mode"] == "pieces"
        and any(c["mode"] == "cut" and under(c, q["name"]) for c in order)
    }
    deepest = lambda q: -depth_of(q["name"], by_name, root)  # noqa: E731
    for p in sorted(
        [q for q in order if q["mode"] == "pieces" and q["name"] not in waits],
        key=deepest,
    ):
        take_pieces(p)
    for p in sorted(
        [q for q in order if q["mode"] == "cut" or q["name"] in waits], key=deepest
    ):
        (cut_part if p["mode"] == "cut" else take_pieces)(p)

    if plan["floor"] == "drop":
        rest = rest.take(~np.isin(rest.piece, floor_ids))
    soups[root] = rest

    # Pivots and checks.
    report_parts, failed = [], []
    pivots = {root: np.array([(lo[0] + hi[0]) / 2, lo[1], (lo[2] + hi[2]) / 2])}
    if len(rest):
        rlo, rhi = rest.P.reshape(-1, 3).min(0), rest.P.reshape(-1, 3).max(0)
        pivots[root] = np.array([(rlo[0] + rhi[0]) / 2, rlo[1], (rlo[2] + rhi[2]) / 2])
    for p in order:
        name, part = p["name"], soups[p["name"]]
        r = {
            "name": name,
            "parent": p["parent"],
            "mode": p["mode"],
            "triangles": len(part),
            "capTriangles": int(part.cap.sum()),
            **results[name],
        }
        fails = []
        if not len(part):
            fails.append("empty")
            pivots[name] = pivots[p["parent"]].copy()
        else:
            pv, src = pivot_for(
                p,
                part,
                loops_of[name],
                scale,
                hubs.get(name),
                ring_piece(part, p["axis"], soup, label, count, floor, scale)
                if p["mode"] == "pieces" and p["pivot"] == "ring"
                else None,
            )
            if pv is None:
                bl, bh = part.P.reshape(-1, 3).min(0), part.P.reshape(-1, 3).max(0)
                pv, src = (bl + bh) / 2, "box centre (fallback)"
                fails.append("pivot")
            pivots[name] = pv
            r["pivot"], r["pivotFrom"] = r3(pv), src
            r["axis"], r["spin"] = r3(p["axis"]), p["spin"]
            if p["spin"]:
                bounce, radius = bounce_of(part.P.reshape(-1, 3), pv, p["axis"])
                if bounce is not None:
                    r["bounce"], r["radius"] = round(bounce, 4), round(radius, 4)
                    r["bounceMax"] = BOUNCE_MAX
                    if bounce > BOUNCE_MAX:
                        fails.append("bounce")
            else:
                r["range"] = p["range"]
            if any(f["seamOpenEdges"] for f in r.get("faces", [])):
                fails.append("open-cut")
            on_floor = int(np.isin(part.piece, floor_ids).sum())
            if on_floor:
                r["floorTriangles"] = on_floor
                fails.append("floor")
            r["openEdges"] = open_edges(part, scale)
        r["failed"] = fails
        failed += [f"{name}: {f}" for f in fails]
        report_parts.append(r)

    nodes = [{"name": root, "parent": None, "pivot": pivots[root], "soup": rest}]
    index = {root: 0}
    for p in order:
        index[p["name"]] = len(nodes)
        motion = {"axis": r3(p["axis"]), "spin": p["spin"]}
        if not p["spin"]:
            motion["range"] = p["range"]
        nodes.append(
            {
                "name": p["name"],
                "parent": index[p["parent"]],
                "pivot": pivots[p["name"]],
                "soup": soups[p["name"]],
                "extras": {"unityAi": {"motion": motion}},
            }
        )
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    write_glb(a.out, doc, binary, nodes)
    print(
        json.dumps(
            {
                "out": os.path.abspath(a.out),
                "kernels": sorted(kernels_used) or ["none"],
                "blender": blender,
                "trianglesIn": len(soup),
                "pieces": count,
                "floorPieces": int(floor.sum()),
                "sourceOpenEdges": open_edges(soup, scale),
                "root": {
                    "name": root,
                    "triangles": len(rest),
                    "pivot": r3(pivots[root]),
                    "openEdges": open_edges(rest, scale),
                },
                "parts": report_parts,
                "failed": failed,
                "pass": not failed,
            }
        )
    )
    return 3 if failed else 0


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    ip = sub.add_parser("inspect")
    ip.add_argument("--model", required=True)
    ip.add_argument(
        "--axis",
        choices=("x", "y", "z"),
        default="y",
        help="the slices' direction (default y: by height)",
    )
    ip.add_argument(
        "--box",
        help="minx,miny,minz,maxx,maxy,maxz: slice only this region (a box face's extent)",
    )
    ip.add_argument("--slices", type=int, default=PROFILE_SLICES)
    sp = sub.add_parser("split")
    for arg in ("--model", "--plan", "--out"):
        sp.add_argument(arg, required=True)
    sp.add_argument(
        "--kernel",
        choices=("numpy", "auto", "blender"),
        default="numpy",
        help="numpy (default); auto: retry a cut NumPy leaves open in Blender when installed; blender: every cut",
    )
    sp.add_argument(
        "--overwrite",
        action="store_true",
        help="write over --out when it exists (never when it is the model)",
    )
    sp.add_argument(
        "--blender",
        help="the Blender executable, when it is not on PATH or in its usual place",
    )
    a = ap.parse_args()
    try:
        if a.cmd == "inspect":
            cmd_inspect(a)
            return 0
        return cmd_split(a)
    except PlanError as e:
        print(json.dumps({"error": str(e)}))
        return 2
    except (
        OSError,
        ValueError,
        KeyError,
        IndexError,
        TypeError,
        AttributeError,
        struct.error,
        np.linalg.LinAlgError,
    ) as e:
        # A file that is not what it says (a broken GLB, an accessor past its buffer, a malformed plan): the same
        # contract as a refused plan, exit 2 with why, never a traceback.
        print(json.dumps({"error": f"{type(e).__name__}: {e}"}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
