"""The cut of sequences/model_parts.py done by Blender, for `model_parts.py split --kernel blender` (or `auto` when
Blender is installed). Never run on its own: model_parts.py starts it as

  blender --background --factory-startup --python model_parts_blender.py -- <in.npz> <out.npz>

<in.npz> holds the triangles left to cut (P, N, UV, mat, cap, as model_parts.Soup) and one part's boxes (lo, hi);
<out.npz> gets the part and the rest as triangles again, cap triangles flagged, plus the cut report and the cut loop
points per box face. What Blender adds: the surface is welded first (one vertex where the generator split it at a UV
seam), bisected along every face of every box, the part separated from the rest, and each side's opening filled by
scanfill on its plane (rings with holes included), with Blender's hole fill for a cut that runs across two faces.
Uses the NumPy that ships inside Blender; nothing is installed.
"""

import json
import os
import sys

import bmesh
import bpy  # noqa: F401  (bmesh needs Blender's runtime)
import numpy as np

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model_parts as mp  # noqa: E402


def build(P, N, UV, mat, cap, piece, scale):
    """A bmesh of the triangles, welded by position; the triangles it could not make (repeated faces) apart."""
    bm = bmesh.new()
    flat = P.reshape(-1, 3)
    ids = mp.weld_ids(flat, scale).reshape(-1, 3)
    first = np.full(ids.max() + 1, -1)
    first[ids.ravel()[::-1]] = np.arange(flat.shape[0])[::-1]
    verts = [bm.verts.new(flat[i]) for i in first]
    bm.verts.ensure_lookup_table()
    uv = bm.loops.layers.uv.new("uv")
    nl = [bm.loops.layers.float.new(k) for k in ("nx", "ny", "nz")]
    fm = bm.faces.layers.int.new("mat")
    fc = bm.faces.layers.int.new("cap")
    fp = bm.faces.layers.int.new("piece")
    skipped = []
    for t in range(len(P)):
        a, b, c = ids[t]
        if a == b or b == c or a == c:
            continue  # no area once welded
        try:
            f = bm.faces.new((verts[a], verts[b], verts[c]))
        except ValueError:
            skipped.append(
                t
            )  # the same three corners as a face already made: a doubled shell
            continue
        f[fm] = int(mat[t])
        f[fc] = int(cap[t])
        f[fp] = int(piece[t])
        for k, loop in enumerate(f.loops):
            loop[uv].uv = UV[t, k]
            for j in range(3):
                loop[nl[j]] = float(N[t, k, j])
    bm.faces.ensure_lookup_table()
    return bm, (uv, nl, fm, fc, fp), np.array(skipped, np.int64)


def inside_any(co, lo, hi, eps):
    return bool(np.any(np.all((co >= lo - eps) & (co <= hi + eps), axis=1)))


def faces_near(bm, lo, hi, eps):
    out = []
    for f in bm.faces:
        cs = np.array([v.co for v in f.verts])
        if np.all(cs.max(0) >= lo - eps) and np.all(cs.min(0) <= hi + eps):
            out.append(f)
    return out


def on_face(co, b, f, lo, hi, eps):
    axis = f // 2
    value = hi[b][axis] if f % 2 == 0 else lo[b][axis]
    if abs(co[axis] - value) > eps:
        return False
    return all(lo[b][k] - eps <= co[k] <= hi[b][k] + eps for k in range(3) if k != axis)


def plane_of_edge(e, lo, hi, eps):
    """(box, face) both ends of a cut edge lie on, or None."""
    for b in range(len(lo)):
        for f in range(6):
            if on_face(e.verts[0].co, b, f, lo, hi, eps) and on_face(
                e.verts[1].co, b, f, lo, hi, eps
            ):
                return b, f
    return None


def close(bm, layers, lo, hi, eps, outward):
    """Fills the side's openings along the boxes' faces. `outward` +1 for the part (caps face out of the box), -1 for
    the rest. Returns {(box, face): {"loops": filled regions, "openEdges": edges left open}}."""
    uv, nl, fm, fc, fp = layers
    groups = {}
    for e in bm.edges:
        if e.is_boundary:
            key = plane_of_edge(e, lo, hi, eps)
            if key:
                groups.setdefault(key, []).append(e)
    report = {}
    made = []
    for (b, f), edges in groups.items():
        n = [0.0, 0.0, 0.0]
        n[f // 2] = 1.0 if f % 2 == 0 else -1.0
        before = set(bm.faces)
        bmesh.ops.triangle_fill(
            bm, use_beauty=True, use_dissolve=False, edges=edges, normal=n
        )
        new = [x for x in bm.faces if x not in before]
        made += [(x, (b, f)) for x in new]
        report[(b, f)] = {"new": new}
    # A cut that runs across a box's edge onto the next face is not flat: Blender's hole fill closes what is left.
    left = [e for e in bm.edges if e.is_boundary and plane_of_edge(e, lo, hi, eps)]
    if left:
        before = set(bm.faces)
        bmesh.ops.holes_fill(bm, edges=left, sides=0)
        new = [x for x in bm.faces if x not in before]
        bmesh.ops.triangulate(bm, faces=new)
        new = [x for x in bm.faces if x not in before]
        for x in new:
            key = plane_of_edge(x.edges[0], lo, hi, eps) or (0, 0)
            made.append((x, key))
            report.setdefault(key, {"new": []})["new"].append(x)
    centre = (lo + hi) / 2
    for face, (b, f) in made:
        # The cap's colour: one texel of the surface beside it (the first neighbouring surface loop found).
        texel, material = None, 0
        for e in face.edges:
            for lf in e.link_faces:
                if lf is not face and not lf[fc]:
                    texel, material = lf.loops[0][uv].uv.copy(), lf[fm]
                    break
            if texel is not None:
                break
        face.normal_update()
        away = np.array(face.calc_center_median()) - centre[b]
        if np.dot(np.array(face.normal), away) * outward < 0:
            face.normal_flip()
        face[fc] = 1
        face[fp] = -1
        face[fm] = material
        for loop in face.loops:
            if texel is not None:
                loop[uv].uv = texel
            for j in range(3):
                loop[nl[j]] = face.normal[j]
    for key in report:
        caps = set(report[key]["new"])
        regions, seen = 0, set()
        for x in caps:
            if x in seen:
                continue
            regions += 1
            stack = [x]
            while stack:
                y = stack.pop()
                if y in seen:
                    continue
                seen.add(y)
                stack += [
                    z
                    for e in y.edges
                    for z in e.link_faces
                    if z in caps and z not in seen
                ]
        open_left = sum(
            1
            for e in bm.edges
            if e.is_boundary and plane_of_edge(e, lo, hi, eps) == key
        )
        report[key] = {"loops": regions, "openEdges": open_left}
    for e in bm.edges:
        if e.is_boundary:
            key = plane_of_edge(e, lo, hi, eps)
            if key and key not in report:
                report[key] = {"loops": 0, "openEdges": 0}
            if key:
                report[key]["openEdges"] = report[key].get("openEdges", 0)
    return report


def triangles(bm, layers):
    uv, nl, fm, fc, fp = layers
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    P, N, UV, mat, cap, piece = [], [], [], [], [], []
    for f in bm.faces:
        f.normal_update()
        P.append([list(l.vert.co) for l in f.loops])
        ns = []
        for l in f.loops:
            n = np.array([l[nl[j]] for j in range(3)])
            ln = np.linalg.norm(n)
            ns.append(n / ln if ln > 1e-9 else np.array(f.normal))
        N.append(ns)
        UV.append([list(l[uv].uv) for l in f.loops])
        mat.append(f[fm])
        cap.append(bool(f[fc]))
        piece.append(f[fp])
    if not P:
        return mp.Soup.empty()
    return mp.Soup(
        np.array(P, np.float64),
        np.array(N, np.float64),
        np.array(UV, np.float64),
        np.array(mat),
        np.array(cap),
        np.array(piece),
    )


def main():
    src, dst = sys.argv[sys.argv.index("--") + 1 :][:2]
    z = np.load(src)
    P, N, UV, mat, cap, piece = z["P"], z["N"], z["UV"], z["mat"], z["cap"], z["piece"]
    lo, hi, scale = z["lo"], z["hi"], float(z["scale"])
    eps = scale * 1e-6
    bm, layers, skipped = build(P, N, UV, mat, cap, piece, scale)
    for b in range(len(lo)):
        for f in range(6):
            axis = f // 2
            value = hi[b][axis] if f % 2 == 0 else lo[b][axis]
            co = [0.0, 0.0, 0.0]
            co[axis] = value
            no = [0.0, 0.0, 0.0]
            no[axis] = 1.0
            near = faces_near(bm, lo[b], hi[b], eps)
            if not near:
                continue
            geom = (
                list({e for x in near for e in x.edges})
                + list({v for x in near for v in x.verts})
                + near
            )
            bmesh.ops.bisect_plane(
                bm,
                geom=geom,
                dist=eps * 0.1,
                plane_co=co,
                plane_no=no,
                clear_outer=False,
                clear_inner=False,
            )
    bm.faces.ensure_lookup_table()
    in_part = [
        inside_any(np.array(f.calc_center_median()), lo, hi, eps) for f in bm.faces
    ]
    part, rest = bm.copy(), bm.copy()
    part.faces.ensure_lookup_table()
    rest.faces.ensure_lookup_table()
    bmesh.ops.delete(
        part,
        geom=[part.faces[i] for i, k in enumerate(in_part) if not k],
        context="FACES",
    )
    bmesh.ops.delete(
        rest, geom=[rest.faces[i] for i, k in enumerate(in_part) if k], context="FACES"
    )
    lay = lambda m: (  # noqa: E731
        m.loops.layers.uv["uv"],
        [m.loops.layers.float[k] for k in ("nx", "ny", "nz")],
        m.faces.layers.int["mat"],
        m.faces.layers.int["cap"],
        m.faces.layers.int["piece"],
    )
    part_report = close(part, lay(part), lo, hi, eps, +1)
    rest_report = close(rest, lay(rest), lo, hi, eps, -1)
    faces, loops = [], {}
    for (b, f) in sorted(set(part_report) | set(rest_report)):
        pr, rr = part_report.get((b, f), {}), rest_report.get((b, f), {})
        open_edges = pr.get("openEdges", 0) + rr.get("openEdges", 0)
        entry = {
            "face": mp.FACE_NAMES[f],
            "box": int(b),
            "at": round(float(hi[b][f // 2] if f % 2 == 0 else lo[b][f // 2]), 5),
            "loops": int(pr.get("loops", 0)),
            "open": int(open_edges > 0),
        }
        if open_edges:
            entry["openEdges"] = int(open_edges)
            entry["openWhy"] = "the model is open here"
        faces.append(entry)
        pts = [np.array(v.co) for v in part.verts if on_face(v.co, b, f, lo, hi, eps)]
        loops[f"loop_{b}_{f}"] = np.array(pts) if pts else np.zeros((0, 3))
    inside, outside = triangles(part, lay(part)), triangles(rest, lay(rest))
    if len(skipped):
        extra = mp.Soup(
            P[skipped],
            N[skipped],
            UV[skipped],
            mat[skipped],
            cap[skipped],
            piece[skipped],
        )
        boxes = [{"min": lo[b].tolist(), "max": hi[b].tolist()} for b in range(len(lo))]
        ei, eo = mp.split_by_boxes(extra, boxes)
        inside, outside = mp.Soup.join([inside, ei]), mp.Soup.join([outside, eo])
    np.savez(
        dst,
        inP=inside.P,
        inN=inside.N,
        inUV=inside.UV,
        inMat=inside.mat,
        inCap=inside.cap,
        inPiece=inside.piece,
        outP=outside.P,
        outN=outside.N,
        outUV=outside.UV,
        outMat=outside.mat,
        outCap=outside.cap,
        outPiece=outside.piece,
        faces=json.dumps(faces),
        **loops,
    )


main()
