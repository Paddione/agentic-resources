# Sequence: a 3D model split into rigid parts a game can move

A user who said not to ask (SKILL.md, When the user says not to ask): every question
this file has you ask, but money, is your own call; say what you chose in the final reply.

**Experimental.** Measured on twelve generated models (Worked examples, at the
end); its rules and output may still change. Say so in the plan, before the
first quote.

A game moves parts of a model: a tank's turret turns and its barrel lifts, a
gun turret's head turns, a vehicle's wheels spin, a chest's lid opens, a
propeller turns. As of 2026-11-09 no listed 3D model returns textured parts
that move; when one does (its description in `unity ai models list` says
so), prefer it to this route. This route takes one generated model (a GLB) and splits it with a free local script into
a **node tree** (`Hull > Turret > Cannon`, `Body > WheelFL ...`): every part
on its own node, the node's origin its **pivot**, so the game turns a node
and the part turns about the right point. Then it **measures** the result;
a split passes on numbers, never on looks alone.

It is a tool for easy wins, not one that splits anything. Offer it only
when every part the user wants moving is **rigid and turns on one axis**,
and is either **already a separate piece** of the mesh or meets the rest at
a **clean seam** (a narrow neck, a ring, a gap). Decline plainly otherwise
(step 1).

```
the intent (what moves, about what)
   │  1. offer or decline                                        (free)
   │  2. concept:  an image designed for the split (SKILL.md's Text to 3D, plus step 2)
   │  3. mesh:     model3d-tripo-p2 on the approved concept, as SKILL.md says
   │  4. read it:  model_parts.py inspect, preview --views pivots   (free)
   │  5. plan:     parts.json: a box per part, its mode, axis, pivot  (free)
   │  6. split:    model_parts.py split                              (free) → <stem>-parts.glb, the report
   │  7. check:    preview --png --views pivots,sweep                (free)
   ▼
a GLB whose nodes are the parts, pivots placed, every check passed
```

Steps 2 and 3 are SKILL.md's Text to 3D route: each paid step follows the
normal flow (quote and consent, generate, look). Everything after the mesh
is free and local: a box placed wrong costs a rerun of the script, never a
generation. When the user already has the model (a GLB), start at step 4.

## The local script

`sequences/model_parts.py`, next to this file. It needs Python 3 with
**NumPy** (not Pillow), checked before the plan and before anything is
spent: the preflight's `tools` reading gives the interpreter
(`details.python` plus the `args` of the usable `details.pythonCandidates`
entry) and whether `numpy` is there; or the probe of
`sequences/image-to-spritesheet.md` step 6 on a build without it. Run it as
`"<details.python>" <args> -E "<skill folder>/sequences/model_parts.py"
<step> ...`, every path absolute and quoted. With Python or NumPy missing
the split cannot run: say so in the plan, before anything is spent, and
install nothing. Offer the model as one piece instead (the ordinary 3D
route, which needs neither), its concept still designed for the split
(step 2), and tell the user that with Python 3 and NumPy installed
(`"<details.python>" <args> -m pip install numpy` when only NumPy is
missing; both are theirs to install) the same model can be split later,
from step 4. Run without NumPy, the script prints `"missing": "numpy"` in
its `error` line and exits 2.

Each step prints one JSON line. `split` exits 0 when every check passed, 3
when it wrote the file but a check failed (the report says which), 2 when it
wrote nothing (`error` says why: a bad plan, a broken, compressed or rigged
model, an `--out` that exists). Exit 2 is not always the plan: read `error`.

**Blender (optional, off by default).** `split` cuts in NumPy and never
starts Blender unless asked. `--kernel auto` lets it retry a cut NumPy
leaves open, when Blender is on PATH or in its usual install folder (never
the current folder), and keeps the result with fewer open edges along the
cut; the report's `kernel` names which one each part used, `openAlongCutBy`
the open edges each left, and `blenderError` why a retry failed (NumPy's
cut then stands). `--kernel blender` cuts with Blender alone; `--blender
<path>` names the executable. A Blender run can take minutes. Measured on
the bench: where the NumPy cut closes, Blender gives the same triangles about
fifteen times slower, and it closed none of the cuts NumPy left open: a cut
that stays open is a placement or a model problem, which steps 4 and 6 fix.
Never install Blender for this route, and never offer it as the fix for an
open cut.

## 1. Offer or decline

Before any quote, write the parts the user wants moving as a table and
check each row:

| Part | Moves how (axis) | Separate piece or clean seam? | Offer? |
|---|---|---|---|

| Offer | Decline, and say what instead |
|---|---|
| A turret turning on its hull, a gun turret's head on its base (yaw, a ring or neck under it) | A character or creature bending: rig it (SKILL.md, Rigging; `sequences/creature-rig-and-animate.md`) |
| A barrel or arm lifting at its root (pitch at a mantlet, a trunnion, a hinge) | A door, hatch or bonnet that opens onto an inside the model never had (a cab, an engine bay): the cut shows a flat cap, not an interior; offer it closed, or a separate model of the inside |
| Wheels, rollers, a propeller, a rotor spinning (a separate piece, or one at a hub) | A part fused along a long overhanging surface (a tank track wrapped round its wheels, a sail on its rigging): no clean seam to cut |
| A lid or a flap on a hinge (a chest, a crate, a mailbox) | A part that changes shape (a track that bends, a cloth, a spring): a swap of models or a rig |
| A lever or a hatch on an outside hinge (a signal arm, a hatch lid that shows nothing under it) | A generation defect in the way (a wheel fused to the body, a shadow wedge baked onto it, step 6): regenerate the concept |

Say which rows are offered and which declined, and why, before quoting.
When every row is declined, nothing is generated for this route.

## 2. The concept, designed for the split

When the intent is known before the model is made, the concept prompt
(SKILL.md, Text to 3D goes through one image: one image model call, a
transparent background, three-quarter front view, the camera at the object's
own height, never from above) adds, for each part that will move:

- **A turret or head that turns:** "sits on a clearly visible narrow round
  turret ring, with a dark gap all around between the turret and the flat
  deck". The ring becomes the cut, and its round cap the pivot.
- **A barrel that lifts:** "comes straight out of a round mantlet (or a
  horizontal pivot drum), and stays well clear of the hull".
- **Wheels:** "each one solid tyre and hub, standing clear of the body with
  visible empty space between every wheel and the body and its wheel
  arches". A wheel then comes back as its own piece.
- **A vehicle whose wheels spin: an exact side view**, "the camera at the
  wheels' height, the wheels seen as full circles", not the three-quarter
  view. The 3D model keeps the ellipse a three-quarter view draws: the same
  truck came back with oval tyres from three-quarter concepts (they bounce
  7 to 15% over a turn and fail step 6) and round ones from a side view (1.8
  to 2.7%). From a side view the model's front is the vehicle's side, turned
  90° about the vertical (SKILL.md, the concept's view becomes the model's
  orientation): say so in the plan, and turn it on import (a node rotation in
  Unity), never by redrawing.
- **Always:** "whole object in frame on a fully transparent background: no
  ground, no floor, no cast shadow, no reflection". The 3D model bakes a
  drawn shadow into flat pieces on its floor, and once into a wedge fused to
  a wheel.
- **A vehicle:** "original, invented design, not based on any real brand or
  model". A concept that looks like a real car is refused by the 3D model
  (`CONTENT_BLOCKED`, nothing charged).

Look at the concept before the mesh is quoted (SKILL.md): each moving part
visibly separate or on its ring, no shadow. A concept that misses is
regenerated as `-v2`, an image, never reconstructed.

## 3. The mesh

`model3d-tripo-p2` on the approved concept, `--param face_limit=10000`, as
SKILL.md says, then its facing check. Its meshes are many connected pieces
(about 50 to 170): a wheel is usually one piece, a turret is usually fused
to its hull. `model3d-tripo3-1` with `generate_parts` returns 40 to 60
semantic parts, but untextured, as open shells, with every pivot at the
origin; a retexture keeps them only as one texture per part. It is not this
route's source.

## 4. Read the model (free)

```
model_parts.py inspect --model "<model.glb>"
unity ai preview "<model.glb>" --png --views pivots
```

- `inspect`: the model's bounds; its `largestPieces` (each piece's centre,
  size and triangles; `floor: true` marks one lying flat on the floor, a
  baked shadow); and `profile`, its cross-section by height: each slice's
  extent, its closed `loops` and its `open` ones. A turret's neck is where the
  slices narrow.
- `meshNodes` (only when the model has more than one mesh node): each node's
  name and triangles. When those names read as the parts the request needs
  (`Turret`, `Wheel_FL`, not `mesh_0`, `mesh_1`), the model already comes in
  parts: a split would merge them and cut them again by your boxes. Say so,
  and offer the model as it is (its pivots are wherever its nodes put them:
  look with `--views pivots` or in Unity); split only for measured pivots,
  each part's box around its node.
- `--views pivots` draws the model from the front (+Z), the side (+X) and
  the top (+Y), orthographic, on a grid in the file's own units labelled on
  the edges: read every box corner off it, never guess one.
- **Where to cut:** `inspect --box minx,miny,minz,maxx,maxy,maxz` slices
  only the box face's region, so each row is what a cut there would report.
  Put a cutting face where `open` is 0 and the loop count is the part's own
  (a turret's neck is one loop or a few). A cut one slice off can leave twelve
  loops open (a measured case: the sci-fi turret, Worked examples). `--axis z`
  slices along a barrel.

## 5. The plan

`<stem>-parts.json` next to the model:

```
{"root": "Hull",
 "parts": [
   {"name": "Turret", "mode": "cut", "boxes": [{"min": [-0.21, 0.062, -0.3], "max": [0.21, 0.4, 0.2]}],
    "axis": "y", "pivot": "ring", "range": [-180, 180]},
   {"name": "Cannon", "parent": "Turret", "mode": "cut", "boxes": [{"min": [-0.09, 0.08, 0.13], "max": [0.07, 0.19, 0.6]}],
    "axis": "x", "pivot": "root", "range": [-20, 5]},
   {"name": "WheelFL", "mode": "pieces", "boxes": [{"min": [0.25, -0.43, 0.19], "max": [0.5, 0.02, 0.53]}],
    "axis": "x", "pivot": "hub", "spin": true}]}
```

- `root`: what stays (the hull, the body, the base). `name`: letters,
  digits, `-` and `_`; it names the node, which a game script finds by name.
- `mode`: **`pieces`** whenever the part is already separate (most wheels and
  propellers, and a turret designed for the split as in step 2): it lifts
  whole pieces whose centre is in a box, so the box only has to hold the
  centre, and nothing is cut. Prefer it to a cut: on the bench the same
  tank's barrel passed as a piece and failed as a cut (its root is an open
  shell). **`cut`** when it is fused (a turret on its
  hull, a barrel in its mantlet, a lid): it slices along the box and closes
  both sides with a cap that takes one texel of the colour beside the cut
  (the hull gets a roof where the turret stood, seen when it turns).
- `boxes`: axis-aligned, in the model's units. For a cut, **only the cutting
  face crosses the model**: the turret's bottom face at the ring; its other
  faces clear of everything (past the barrel's tip, above the top, beside the
  hull's fenders). A face that crosses something else takes it with the part.
  Several boxes make one part (their union). A face lying exactly on a flat
  surface is moved a hair outward by the script.
- `parent`: the part it rides on (default the root). A child is cut before
  its parent, so a barrel's box may sit inside its turret's.
- `axis`: `x`, `y`, `z` or `[x, y, z]`. A turret `y`; a barrel lifting
  sideways across it (`x` when the model faces +Z); wheels their axle.
- `pivot`: `ring` (the centre of the cut faces facing up or down: a
  turret's ring; for a `pieces` part, the centre of the round, flat ring or
  collar it sits on, else its footprint), `root` (the centre of
  the cut faces facing sideways: a barrel's root; the cut loop's centre when
  the cut did not close), `hub` (a spinning part: the centre, seen along the
  axis, of its piece widest across the axis), `{"edge": [0, 0, -1]}` (the
  middle of the cut's edge farthest that way: a lid's hinge at its back), or a
  point `[x, y, z]`. Prefer a rule to a point: the rules read the geometry.
- `spin: true` for a part that turns full circles; `range` the degrees a
  limited part turns (the sweep draws them; default `[-30, 30]`). Angles
  turn right-handed about the axis (thumb along it, the fingers curl the
  positive way): with the model facing +Z, a barrel on `x` lifts at
  negative angles, so `[-20, 5]` is up 20°, down 5°. A generated model
  does not always face +Z, so check it in the `sweep` view, whose third
  tile is the range's end. The bench covered turrets, barrels and wheels:
  for any other part (a lid, a hatch, a rotor), check its sweep the same
  way before calling it done.
- `"floor": "drop"` at the top level also removes the baked floor shadows
  from the root. Offer it when `inspect` reports floor pieces.

A spinning `pieces` part keeps its piece widest across the axle (the tyre)
and the pieces inside that piece's swept cylinder; a piece reaching out of it
(a suspension arm, a mudguard) stays on the body (`piecesLeft` counts them).

## 6. Split, and read the report (free)

```
model_parts.py split --model "<model.glb>" --plan "<stem>-parts.json" --out "<stem>-parts.glb"
```

`--out` is new: `<stem>-parts.glb`, or `-parts-2.glb` when that exists.
The script refuses the generated model as `--out`, and an existing file
unless `--overwrite` is passed: pass it only to redo your own earlier split
of this route (the next try of the same plan).

The report gives, per part: `triangles`, its `faces` (each box face that cut:
`loops` closed, `open` loops that did not close with `openWhy`, and
`seamOpenEdges`, edges left open along the cut on either side), its `pivot`
and `pivotFrom`, `bounce` for a spinning part, `floorTriangles`, and
`failed`. **The split passes only when `pass` is true:**

| Check | Means | Fix (free: edit the plan, split again) |
|---|---|---|
| `open-cut` | open edges left along a cut face (`seamOpenEdges`): the model's slice there does not close, so the face has a hole that shows when the part turns | `openWhy` "runs off the face": another box face crosses the model, move it clear. "the model is open here": move the cutting face to a slice `inspect --box` shows closed (step 4) |
| `bounce` | a spinning part's lowest point (its farthest sideways for a vertical axis: a rotor) moves by more than `bounceMax` (6%) of its radius over a turn (a true wheel measured 1 to 6%, one off its axle 25 to 43%) | a piece that is not round went with it (a shadow wedge, a mudguard): shrink the box, or it is a defect (decline that wheel, or regenerate the concept) |
| `floor` | a baked shadow piece went with the part | shrink the box above the floor |
| `empty` | the part took nothing | the box misses the model: read the grid again |
| `pivot` | the rule found nothing to read; the pivot fell back to the box centre | use another rule, or a point read off the grid |

Three tries a part, then stop and show the user the report and the pivots
view, with the choices: keep the part as it is (say what fails), drop it,
or regenerate the concept (a paid step, quoted). Never call a failing split
done.

## 7. Check it (free)

```
unity ai preview "<stem>-parts.glb" --png --views pivots,sweep
```

- `pivots`: each part in its own colour (grey: the root), its pivot a dot,
  its axis a line. A turret's dot on its ring, a barrel's at its root, a
  wheel's at its hub, every line along the motion.
- `sweep`: each moving part turned through its range (a spin to 0, 90, 180
  and 270°). Look for a part that turns through the body, a cap that shows
  where it should not, a hole, or a piece left behind (a turret's front
  wedge still on the hull).

Show the user both images with the numbers: the result of this route is the
GLB plus these measures.

## 8. In Unity

What follows was checked with glTFast (6.20, URP) in a WebGL build. Another
importer, an FBX conversion or another engine may convert axes and names
differently: there, turn one part in the scene and check it against the
`sweep` view before giving the user code or numbers.

With glTFast, each part imports as a child GameObject named as the plan
names it, whose pivot is its origin; the root (Hull, Body) becomes the
prefab root and takes the file's name. glTF is right-handed and Unity
left-handed, so glTFast mirrors X on import: a turn by `angle` about the plan's axis
`[x, y, z]` is
`transform.localRotation = Quaternion.AngleAxis(-angle, new Vector3(-x, y, z))`
in the parent's space (the script writes no rotation on any node). Used
as is, the plan's axis and angle turn a Y or Z part the wrong way: a
barrel's `[-10, 30]` would dip 30° into the hull. The motions are not clips: the GLB carries the parts and their
pivots, the game or an Animator moves them. The node extras
(`{"unityAi": {"motion": {"axis", "range", "spin"}}}`) are there for tools that read
them.

## Limits

- Rigid parts turning on one axis each. A part that bends, slides (along a
  line or a curve) or opens onto an inside is out of scope (step 1): the
  plan, the node extras and the `sweep` view only describe a turn.
- A cut face is flat and takes one texel of colour: right for a ring, a
  mantlet or a lid's rim, wrong for a large surface the player will look at
  for long.
- Generated meshes are open in places; a cut through an open spot stays open
  (the check says so). Blender closed none of those on the bench: the fix
  is another cut placement (step 4) or a regenerated model.
- The pivots are measured, not chosen: a part the model drew off-centre (an
  oval tyre, a wheel set askew) is reported, not fixed.
- A split model is a tree of rigid meshes, not one skinned mesh: it is not
  an input for a rigging model (`model3d-tripo-rigging-v1`,
  `model3d-meshy-rigging`, `uthana-character-rig`) or a third-party
  auto-rigger. Rig the unsplit model, or move the parts' nodes in the game.

## Worked examples

Bench run of 2026-11-09, `model3d-tripo-p2` at `face_limit=10000`; every number
from `split`'s report. "New" models had their concept written as step 2 says.

| Model | Parts (mode) | Tries | Result |
|---|---|---|---|
| Tank (new, three-quarter concept with a ring gap) | turret, barrel (`pieces`: the ring gap made them separate) | 1 | Pass. Turret on its ring disc's centre, barrel at its mantlet. The same barrel as a `cut` failed: its root is an open shell |
| Gun turret, steampunk (new) | head, barrels (`pieces`) | 2 | Pass. Try 1 put the head's pivot 9 cm off its neck (a hanging pipe pulled its footprint): now the neck collar's centre |
| Monster truck (new, three-quarter) | 4 wheels (`pieces`) | 1 | Fail, bounce 7 to 11%: oval tyres (radius 0.159 to 0.177 round each wheel). A second three-quarter concept asking for "perfectly circular wheels": 7.5 to 15% |
| Monster truck (new, side view) | 4 wheels (`pieces`) | 1 | Pass, bounce 1.8 to 2.7%; the model came back turned 90°, as expected |
| Tractor (new, three-quarter) | 2 front wheels (`pieces`), 2 rear (`cut`) | 3 | Front 5.0% and 6.8% (one just over); rear wheels fused with the axle and mudguards into one piece: 20% bounce and open cuts after three tries. Declined, regenerate from a side view |
| Tank, cartoon | turret, barrel (`cut`) | 1 | Pass: one ring loop, the bored barrel two loops, no open edge along either cut |
| Gun turret, sci-fi | head, barrels (`cut`) | 2 | Try 1 cut at y 0.005: 12 loops open. `inspect --box` showed y 0.015 to 0.025 closed: pass there |
| Tank, realistic | turret, barrel (`cut`) | 2 | Barrel passes. Turret declined: low, wide, overhanging the hull on many open shells; no slice across its seam closes (1 to 34 loops open at every height) |
| Buggy, toy | 4 wheels (`pieces`) | 1 | 4.9 to 6.2% (one just over): slightly oval tyres. 3 floor pieces (baked shadows) left on the body |
| Rover, six wheels | 6 wheels (`pieces`) | 1 | Pass, 1.2 to 2.1%; the mudguard pieces reaching out of each tyre left on the body |
| Cart, wooden | 2 spoked wheels (`pieces`) | 1 | Right 1.9%; left 34%: a shadow wedge fused to it. Declined (a generation defect) |

A request to open a sports car's doors was declined at step 1 (the inside was
never modelled); nothing was generated for it.
