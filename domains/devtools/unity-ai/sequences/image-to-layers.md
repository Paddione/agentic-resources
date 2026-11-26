# Sequence: any 2D image cut into layers that move apart cleanly

A user who said not to ask (SKILL.md, When the user says not to ask): every question
this file has you ask, but money, is your own call; say what you chose in the final reply.

**Experimental.** Measured on five objects (Worked examples, at the end);
its rules and output may still change. Say so in the plan, before the
first quote.

A 2D animation moves parts of one picture: a character's arm swings over
its body, armour plates fall off a boss, a wall crumbles into chunks, a
ship's masts snap and its hull breaks in two, the layers of a background
slide past each other. No model returns layers. This route gets them from image models and
a local script, for any object: one **map** of the parts, then one
**in-paint** per part that covers another, then free local steps.

The model draws the map, never the parts: the picture repainted in flat
colours, one per part. The script cuts each part from the **original**
pixels with it, so the layers stack back into the picture exactly. The
only pixels a model paints into a layer are the ones a part hides (the
torso under the arm, the planks under an armour plate), through a mask, so that
**moving a part shows what is behind it**: the part under it, whole, or
the background, never a hole.

The motions decide everything else. Plan them first (step 2): which parts
move on their own, around what, how far, and what each one uncovers. A
part that moves on its own needs its own map colour; one that never leaves
another needs none.

```
picture.png (opaque, a plain background)
   │  1. picture:    the user's, or generate one (see 1)
   │  2. motions:    the motion plan, checked with the user          (free)
   │  3. parts:      parts.json from the plan                        (free)
   │  4. map:        generate --model gpt-image-2-5-sunburst --ref picture.png --param width=<W> --param height=<H> --out map.png
   │  5. masks:      image_layers.py masks  (free)                   → labels.png, mask-<part>.png per part that covers another
   │  6. in-paints:  generate --model gpt-image-2-5-sunburst --ref picture.png --in mask-<part>.png --in-param mask --param width=<W> --param height=<H> ... --out fill-<part>.png
   │  7. layers:     image_layers.py layers (free)                   → layers/*.png, manifest.json, layers.psb, layers-sheet.png
   │  8. pose:       image_layers.py pose   (free)                   → poses/<clip>.gif, poses/<clip>-gaps.png
   ▼
named layers that recompose into the picture; every part movable with what is behind it painted; each motion posed
```

Each paid step follows the normal flow (quote + consent, generate, then
look), and every `generate` runs as SKILL.md's Running `generate` says.
Pass `--param quality=high` on every call: the map is judged to the pixel,
and every in-paint must line up with the picture.

**Consent.** The in-paints need the masks, which need the map, so quote
the map alone, generate it, show it (the checkpoint between steps), run
`masks`, then quote the in-paints together. In the plan, give the count,
**one map plus one in-paint per part that covers another** (an arm over a
body and a forearm over the arm: 1 + 2 calls), plus a picture when one is
generated, and the plan's cost from live quotes with each call's real
params (`width`/`height` at the picture's size on the map and every
in-paint, since size changes the price and `layers` refuses a fill of
another size, and `quality=high` on every call). Only the first paid step has its input, so only its
quote is firm: price the rest as estimates the way SKILL.md's Check every
handoff says (a quote of that model with a placeholder input at that
call's size, the picture's, credits and
worst case, times the calls), and mark them so. Prices change, so never a
figure from memory or from this file. The user approves the quotes, not a
measured charge. A session budget covers the plan.

**Paths.** Pass the script every generated file by the path its `done`
event gives, never by the `--out` you asked for: a redo is not written
over the first file.

## The local script

`sequences/image_layers.py`, next to this file. It needs Python 3 with
Pillow **and** NumPy, checked before the plan and before anything is
spent, as `sequences/portrait-to-layers.md` (The local script) says; run
it the same way, `"<python>" <args> -E "<skill folder>/sequences/image_layers.py"
<step> ...`, every path absolute and quoted. With either one missing this
route stops before the map: say so in the plan, and install nothing.

`--out` is a working folder next to the picture, chosen **once, before
`masks`**: `<picture stem>-layers/`, or `-layers-2/` (then `-3/` ...) when
that one already exists. `layers` reads what `masks` wrote there. Each
step prints one JSON line; a step that exits non-zero printed why, and the
next paid call is not quoted.

## 1. The picture

- **Opaque, on a plain light background**, the object alone and whole in
  frame. One with transparency is flattened onto white first (a copy,
  `picture.png` in the working folder).
- **A size the model draws at.** The map and every mask must be the
  picture's exact size: pass `--param width=<W> --param height=<H>` equal
  to it. When `models show gpt-image-2-5-sunburst` does not allow that
  size, scale the copy locally to the closest allowed one of the same
  shape and work on the copy.
- **A flat view: side, front or top.** A part can only turn in the
  picture's plane; a three-quarter view turns badly.
- **Generated:** one `gpt-image-2-5-flare` call, `--param background=opaque`,
  the view and "clean bold outlines, flat shading, on a plain flat light
  grey background, no ground shadow" in the prompt. Separate, readable
  shapes for every part the plan moves cut cleaner than overlapping ones.

## 2. The motion plan

Before anything is spent, write the motions the object makes, as a table,
and show it to the user (Generation flow, the checkpoint between steps):
what they want animated, and what it implies. One row per motion:

| Motion | What moves, around what | How far | Makes sense? | What it uncovers |
|---|---|---|---|---|

Work out each row the way the object works, then check it against the
way the picture is drawn:

- **What moves on its own.** Each piece that moves relative to the rest is
  a part: a forearm that bends at the elbow is a part apart from the upper
  arm; a helmet that falls off is a part apart from the head; a mast that
  snaps is a part apart from the hull, and its sails, which only ride it,
  are not.
- **Around what.** The pivot is a joint inside the part (a shoulder, an
  elbow, a hinge, a mast's foot on the deck, a plate's lower bolts, an
  axle), never its middle unless it spins. Children ride their parent: a
  hand moves with its forearm, a mast with its hull, a plate with the
  body it is strapped to.
- **How far.** A range the joint allows (an elbow bends one way; a mast
  sways a degree or two before it snaps). A part's hidden end must stay
  hidden over the whole range: an upper arm's top stays inside the
  shoulder as the arm swings.
- **Makes sense?** Check the motion against how such an object behaves:
  breathing lifts the chest, not the hips; a plate breaks loose and drops,
  it does not fly up; a wall's chunks fall in the order their support
  goes; a hit pushes the body back and the loose pieces rattle after it.
  Say **No** for a motion the flat view cannot show (something turning
  around a vertical axis seen from the side, a head turning to profile):
  offer a flip, a swap of drawn states, or another view instead.
- **What is drawn over what.** Look at the picture before deciding the
  depths: it, not the object's name, says what is in front. A ship's masts
  drawn behind its railing are parts under the hull; a strap drawn over a
  plate belongs to the plate. Get it wrong and a part slides over what
  should hide it.
- **Breaking apart.** A piece that breaks during the motion (a hull in two,
  a door off its hinges, a statue's arm) is two or more parts in the map,
  divided along the break the user wants ("a jagged crack from the top of
  the hull to its bottom, between the third and fourth cannon ports"). The
  pieces sit side by side (`"hides": []`), and what shows in the break is
  the background.
- **What it uncovers.** Where the part moves off the background, the
  background shows (nothing to paint). Where it moves off another part,
  that part must go on behind it and is painted by the in-paint (step 6).
  A part that never leaves another (a badge sewn on a jacket) uncovers
  nothing: give it `"hides": []` (step 3) and save an in-paint.
  Pieces that only sit side by side (the chunks of a wall, the tiles of
  a floor) touch but cover nothing: `"hides": []` on each, no in-paint.
  A part that covers another only where the plan never shows it (a hull's
  railing over the foot of a mast that breaks at the deck) gets
  `"hides": []` too.
- **Physics.** A piece falls no later than what holds it up (a chunk
  above a falling one, a plate when its hull half drops), and falls faster
  and faster; something tall topples from its foot (a mast, a tree), slow
  at first; a break lets each piece's broken end drop first (the two
  halves of a hull rise into a V); a body reacts to what leaves it (a hull
  lurches when a mast snaps, a boss recoils when hit); a layer of a
  parallax background slides faster the nearer it is. Space the events so
  each one reads (a few tenths of a second apart).

Motions that need parts the picture cannot give are said, with what it
would take, never quietly dropped: wheels spinning on a vehicle whose
wheels and track are one shape (each wheel its own part), a crate's inside
that no side of it shows (an inside drawn as a separate picture), a ship
sinking (water in the picture, as a part in front of the hull, with the
hull's bottom painted behind it; without water the pieces can only fall
out of the frame), a sail filling with wind (a swap of two drawn states:
a part changing shape is a new drawing, not a move).

## 3. The parts file

`parts.json` in the working folder, from the plan:

```
{"parts": [{"name": "body", "colour": "#0000FF", "z": 0},
           {"name": "upper-arm", "colour": "#00FF00", "z": 1},
           {"name": "forearm", "colour": "#FF0000", "z": 2},
           {"name": "badge", "colour": "#FFFF00", "z": 3, "hides": []}],
 "background": "#000000"}
```

- `name`: letters, digits, `-` and `_`; it names the layer. Never
  `background` (the script's name for what no part covers): call a back
  layer `sky`, `backdrop` or `far`.
- `colour`: the part's flat colour in the map, at least 64 apart on some
  channel from every other colour and the background (the script refuses
  closer ones). Pure, saturated colours: `#FF0000`, `#00FF00`, `#0000FF`,
  `#FFFF00`, `#FF00FF`, `#00FFFF`, `#FF8000`, `#8000FF`, `#808080`,
  `#FFFFFF`; black for the background.
- `z`: required: a whole number from 0, one per part; draw order, 0 at the back.
  A part drawn over another has the higher `z` (only a lower `z` is
  covered, so the script refuses a missing, fractional (2.5), negative or
  shared one; 2.0 reads as 2).
- `hides`: leave it out. The script works it out from the map: a part
  that touches a part under it covers it, and gets an in-paint mask for
  it; a part that touches only the background covers nothing. Give a list
  only to override that (`[]` for a part that never leaves the one under
  it).
- A background to keep as a layer (parallax: sky, far hills, near hills)
  is a part like any other, at the back; `background` is then a colour
  the map does not use.

## 4. The map

`--ref picture.png`, the picture's size, this prompt with one line per part
of the parts file, each described by **what it is and where it ends**, in
the picture's own terms:

```
Turn this illustration into a flat-colour segmentation map of exactly the same size and framing. Keep every outline exactly where it is in the original; do not move, redraw or restyle anything. Fill each region with one solid colour, no shading, no lines, no gradients, no anti-aliasing:
- <part> (<what it is, what belongs to it, where it ends>): <colour name> <#RRGGBB>
- ...
- background: black #000000
```

Say where two touching parts divide ("the back mast, from where it rises
above the hull's railing to its top"), and give every small piece to the
part it moves with ("its sails, yards, flag, rope ladder and every rigging
line running from it down to the hull"; "the strap and buckle on the
helmet's side"): a piece left unnamed lands in some part's colour or in the
background.

Look at the map beside the picture (preview both): every part one solid
colour, the outlines where the picture's are, every moving part in its own
colour. Three things the model does that `masks` corrects, so they are
no reason to redo a map: lines drawn in black inside the object (a
wheel's hub, the cracks of a wall) go to the part around them; specks of
one part's colour inside another (rivets, seams) go to the part around
them; and the background seen through a part (the sky between a mast and
its rigging, filled solid as sail) goes back to the background, except
the inside of a part mostly in the background's own colour (a white part
outlined on white: one enclosed patch), which stays; many enclosed gaps (a
fence with rails, a ladder) still go. A map
with a part missing, two parts in one colour, or a division in the wrong
place is redone, saying what went wrong (a new paid call, and it makes
the masks and every in-paint stale: Redoing a step); never feed one on.

**One map redo a run.** Every reason to redo the map shares it: this
checkpoint, a part listed in `missing`, a colour `masks` refuses (step
5), and a map found wrong later, at `layers` or `pose` (Redoing a step).
Whichever comes first uses it; a refusal fixed by adding a part (free) is
no failed map and uses nothing. A new picture starts a fresh run, with
its own redo. When the redone map fails again, stop and show the user the
map and what is wrong, with the choices: add the piece as a part (free,
only for a refused colour that is a piece of its own, not a soft map),
one more map (on its own live quote and consent; found at `layers` or
`pose`, it forces every in-paint again too, quoted as an estimate: the
Redo table), or stop.

## 5. masks

```
image_layers.py masks --image picture.png --map map.png --parts parts.json --out <dir>
```

It refuses a map that painted a piece in a colour no part has, with the
colour, its pixels, how many pieces and the box of the largest (a blurred
edge between two parts, and a small lighter or darker patch inside a
part, pass). Look at that box: when it is a piece the plan moves on its
own, add it to `parts.json` in that colour, with a name and a `z`: give
it N + 1, where N is the `z` of the part it is on, and add 1 to every
other part whose `z` is N + 1 or more (step 3: each part its own whole
`z`), and run `masks` again (free). When the box runs along an
edge, or the colour is a mix of the parts around it, the map is soft:
redo it in flat colours. Otherwise redo the map naming that piece's part.
Either redo is the run's one map redo (step 4). A
part added that way can cover another, so `masks` may list a mask the
plan did not count: before quoting the in-paints, restate their count
and estimate to the user.

Read its line: `parts` (the pixels of each; a part listed in `missing` is
not in the map: redo the map), `specksMoved` and `seeThroughPx` (the
corrections of step 4, in pixels), `seeThroughKept` (per part more than
half the background's colour, the pixels and box of the enclosed
background-coloured patches it kept: right for a white part on white; gaps open to the background
or to the picture's edge always go to it, so compare a kept part with the picture and redo the map
when its kept patches are really gaps), `onlyBackgroundBehind` (parts that
uncover only background), and `masks`, one per part that covers another (reaching over `over`: each part above it
that hides it but not all it hides, and so on up, so they can move
together), with
`paint` (the parts to paint behind it) and `behind` (how many edge pixels
touch each). Check it against the plan's "What it uncovers" column: a part
the plan moves off another part must have a mask for it. Each mask is one
in-paint.

## 6. The in-paints

One call per mask: `--ref picture.png --in <mask> --in-param mask`, the
picture's size:

```
Inpaint only the transparent area of the mask. In it, paint what lies behind <the part> (and <each part in `over`>), as if they were lifted away: <each part in `paint`, continued the way it would go on: its shape, its edges, what shows where the part sat>, and the plain <background colour> background where nothing is behind. Same clean outlines, shading and colours as the rest of the picture. Paint every masked pixel, never a flat or black fill, and draw none of <the part> (and <the parts in `over`>). Keep everything outside the masked area exactly as it is.
```

Paint behind a part only what continues there (the sky, the slopes, the
planks): never a new object (a cloud, a bush, a bolt) the plan did not
ask for. Hidden at rest, it peeks out at the part's edge as the part
moves and flickers in and out.

Name what a hidden part would show under its cover: a bald head under a
helmet, the bare shoulder under a pauldron, the planks under an armour
plate, the side of a torso under an arm. Ask the model to **paint** what lies behind, never to
**remove** the part: asked to remove a large area, it can return the mask
filled flat. Look at each in-paint before `layers`: no check catches a
new object, or an edge the model invented where the part's edge was (a
step in a hull under a plate). Redo that one call once (a new paid call:
Redoing a step), saying what to leave out; when the model draws it again,
keep the better one and say so.

## 7. layers

```
image_layers.py layers --image picture.png --parts parts.json --out <dir> --fill <part>=fill-<part>.png ...
```

One `--fill` per mask. It cuts every layer from the picture's pixels, adds
to each hidden part the in-paint pixels that continue it (its own colours,
joined to what shows of it), and writes `layers/<z>-<name>.png`,
`layers/manifest.json` (each layer's box, `z`, `hides` and pixels
`filled`; a top-level `stale` is housekeeping for the next run: ignore
it), `layers.psb` (every layer at its place, for Unity's PSD
Importer), `recomposed.png` and `layers-sheet.png`. Layer files the last run
wrote and this one no longer does (a `z` renumbered) are removed, as the
old `manifest.json` lists them; any other file in `layers/` stays.

Each part keeps its whole drawn outline, so it moves with it: the map's
edge runs inside the line, and `layers` gives the line's outer half to the
part it outlines (against another part, where the in-paint painted that
part instead; against the background, where the picture is not the
background's colour). That is why every mask reaches 6 px past its part.

It refuses, with the redo to ask for:
- a fill that left a part riding on the occluder (`over`) in place;
- a fill that is mostly one colour nothing in the picture has (a blank);
- a fill that redrew the part itself in place instead of what is behind;
- a fill that painted none of a hidden part it touches;
- a part that covers another with no `--fill`.

Redo that one in-paint once, as the message says (a new paid call:
Redoing a step). A part it covers only
along a short stretch of its edge (a strap's end under a plate's rim) and
that the in-paint did not paint is listed under `filled.notFilled`, not
refused. A layer file from the last run it could not remove (held open by
Unity or a viewer) is listed in `staleKept` (and kept in the manifest, so
the next run tries again): an outdated copy, delete it by hand before
importing the folder. One in `caseKept` is the current layer whose name's
case could not be fixed: keep it, and rename it to the manifest's name
(the next run tries the rename again, and reports it until it works).
`staleUnchecked` true means the last run's manifest could not be read, so
nothing was cleaned up: tell the user to check `layers/` for outdated
files. Then check: `recomposeMeanDiff` under 3 (the layers stack back
into the picture; 0.0 is usual), and
`layers-sheet.png`: every layer alone, and the parts that cover another
moved aside, with no hole where they were.

## 8. The motions, checked

Write the plan's motions as `motion.json` in the working folder and pose
them (free):

```
{"pivots":  {"<part>": [x, y], ...},
 "parents": {"<child>": "<parent>", ...},
 "axes":    {"<part>": [1, 0]},
 "clips": [{"name": "<motion>", "fps": 20,
            "keys": [{"t": 0, "<part>": {"rot": 0}},
                     {"t": 0.5, "<part>": {"rot": 8, "slide": -20, "dx": 0, "dy": -4}}, ...]}]}
```

```
image_layers.py pose --out <dir> --motion motion.json
```

- `pivots`: each moving part's joint, in the picture's pixels (read it off
  the picture or `labels.png`: a shoulder, a hinge, a mast's foot, a
  plate's lower bolts). A part with none turns about its box's centre.
- `parents`: what rides what (a forearm on its upper arm, a mast on its
  hull); a child moves with its parent.
- `axes`: the direction a part slides along (`slide`), turned with it: a
  piston, a drawer, a blade drawn from its sheath.
- `view` (optional): a camera, `[x0, y0, x1, y1]`, for a scene that fills
  its frame (a parallax background): the frames are cropped to it, so give
  it a margin as wide as the farthest move, and every transparent pixel
  inside it counts as a gap.
- Per key: `rot` degrees counter-clockwise on screen, `dx`/`dy` pixels,
  `slide` pixels. Each value is eased between the keys that name it, and
  held before its first key and after its last.
- One clip per row of the plan, at both ends of its range, and one that
  plays the whole story when the user asked for one (both masts, both
  plates, then the hull).
- **A fall** is a run of keys a short step apart (0.15 s) with `dy`
  growing as the square of the time since it started (`dy = 700 t²` at a
  1024 px picture, about a gravity), and its `dx` and `rot` growing
  evenly; a part that leaves the frame needs no last key past it.
- **A wait** before an event is two keys with the same values (a plate
  still at 0 s and at 0.4 s, falling after).
- **Slower or faster:** multiply every `t` (twice the `t`, half the
  speed); keep `fps`, so the clip stays smooth.

It writes `poses/<clip>.gif` and `poses/<clip>-gaps.png`, the frame where
most opened with the openings in magenta, and prints `mostGapPx` and
`gapShare` per clip. Look at every GIF and gap image: an opening is fine
where two parts move apart, or a part leaves background it was drawn over.
It is a fault where a part leaves another part with nothing painted
behind it: a hole or a sliver in a part (its in-paint, step 6), or two
parts that move as one in the map (step 4). Show the GIFs to the user: they
are the result of this route.

## Redoing a step

Each step feeds the next, so a redo is never only its own call. Every redo
is a new paid call: quote it live and ask for consent again, as for the
first (a session budget covers it while it lasts). The later calls a redo
forces take inputs that do not exist yet (new masks), so they cannot be
quoted up front: give their count as an estimate, each forced call (the
map and the in-paints, all `gpt-image-2-5-sunburst`) priced at the
picture's size, the new picture's after a picture redo (a
placeholder-input quote, or that model's last quote at that size); the
redone step itself has its own live quote. Then run the normal flow
again from the redone step, each consent on its own live quote.

| Redo | Forces | Calls it forces |
|---|---|---|
| An in-paint | `layers` and `pose` again (free) | 1 |
| The map, at its checkpoint or on a `masks` refusal | `masks` again | 1 |
| The map, after the in-paints ran | `masks` again, so every in-paint (painted for the old masks), then `layers` and `pose` | 1 + one per in-paint |
| The picture | everything that ran after it: the map, `masks`, every in-paint that ran | 1 + the map's 1 + one per in-paint that ran |

## Worked examples

What each one took; the motions are the plan's rows, posed by step 8.

| Object | Parts (`z` from the back) | `hides` | In-paints | Motions |
|---|---|---|---|---|
| A boss in armour | body, chest plate, pauldron, helmet | worked out: each piece covers the body (the pauldron also the plate's strap) | 3: the tunic, the bare shoulder, the head | breathing; a hit that rattles the plates on their straps; the helmet, pauldron and plate falling off one by one, the body recoiling at each |
| A stone wall | six chunks | `[]` on each: side by side | none | a hit that shakes the struck chunks; a crumble: the struck chunk bursts, the one above drops, the side chunks tip out on their outer corners and fall |
| A parallax background | sky, mountains, hills, foreground trees and grass | worked out: each layer covers the one behind | 3: plain sky, the mountains' slopes, the hills | a pan, each layer at its depth's speed, inside a `view` with a 130 px margin |
| A ship | two masts (with sails, rigging, flags), hull, two plates | `[]` on the masts and the hull (masts drawn behind the railing); the plates worked out | 2: the planks under each plate | bobbing with the masts out of step; a mast snapping at the deck and toppling with the hull lurching; the plates dropping |
| The same ship, breaking up | two masts, the hull's back and front halves (split along a jagged crack in the map), two plates | `[]` on masts and halves | the same 2 | both masts topple, both plates drop, then the halves tip into a V, part and fall away |

## Limits

- One object or one scene in a flat view; an object on a plain
  background. Measured on the five objects above and one vehicle.
- What no side of the picture shows (an inside, a back, a hull's bottom
  under water) is not painted: it needs its own picture, or a part in
  front that the in-paint can paint behind.
- An in-paint can invent an edge or an object no check catches: each one
  is looked at (step 6).
- The layers are cut and posed; bones, weights and Unity clips are not
  made here, and the GIFs are previews.
