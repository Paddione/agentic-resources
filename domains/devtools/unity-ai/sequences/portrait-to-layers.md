# Sequence: a character portrait cut into named layers for 2D Animation

**Experimental.** Measured on five anime busts only, and its rules and output
may still change between releases; the rig (step 10) is the least proven
part: its Unity editor script is written for each project from the short
examples in `rig-2d-snippets.md`, checked by hand on one Unity and package
version. Say so in the plan, before the first quote, in one line:
"This route is experimental: it was tested on a few anime portraits, and the
rig step on one Unity version."

A user who said not to ask (SKILL.md, When the user says not to ask): every question
this file has you ask, but money, is your own call; say what you chose in the final reply.

Animating a portrait in 2D (Unity's 2D Animation package: bones, sprite
swaps, a head turn, a blink) needs it split into parts: back hair, body,
neck, face, eye whites, irises, eye lines, mouth, front hair, brows. No
model returns layers. This route gets them from image models and local
code: **four** paid generations for the layers (three
`gpt-image-2-5-sunburst`, one `gpt-image-2-5-flare`), then, if the user
wants them, one more for gaze and one per expression, and free local
steps between.

The model draws **maps**, never parts. A map is the portrait repainted in
flat colours, one per part; the local script cuts each part from the
**original** pixels with it, so the layers stack back into the portrait
exactly. The only pixels a model paints into a layer are the ones a part
hides (the forehead under the bangs, the iris under the lids), through a
mask, and the back hair, which is one generated picture of the whole back
hair so it never shows a cut end. Read this before proposing the plan: the size,
mask and "where an in-paint counts" rules below are what goes wrong.

```
portrait.png (opaque, a plain background)
   │  1. full map:   generate --model gpt-image-2-5-sunburst --ref portrait.png  --param width=<W> --param height=<H> --out map-full.png
   │  2. crop:       portrait_layers.py crop  (free)                → face-crop.png
   │  3. face map:   generate --model gpt-image-2-5-sunburst --ref face-crop.png --param width=1024 --param height=1024 --out map-face.png
   │  4. masks:      portrait_layers.py masks (free)                → labels.png, mask-face.png (+ fallback masks)
   │  5. face:       generate --model gpt-image-2-5-sunburst --ref portrait.png --in mask-face.png --in-param mask ... --out fill-face.png
   │  6. back hair:  generate --model gpt-image-2-5-flare --ref portrait.png --param background=opaque ... --out back-hair.png   (the whole back hair alone)
   │  7. layers:     portrait_layers.py layers (free)               → layers/*.png + layers/manifest.json
   │  8. gaze:       (optional) one in-paint over the eyes, then portrait_layers.py gaze
   │  9. faces:      (optional) one edit per mouth shape or eye state, then portrait_layers.py expressions
   │ 10. rig:        (optional) portrait_layers.py rig (free) → character.psb + its sidecar, rigged in the user's project by a script written from rig-2d-snippets.md
   ▼
named layers that recompose into the portrait, hidden areas filled, uncut back hair; swaps for speech and blinks; a rigged PSB
```

Each paid step follows the normal flow (quote + consent, generate, then
look), and every `generate` runs as SKILL.md's Running `generate` says.
Pass `--param quality=high` on every call: the maps are judged to the pixel,
and every edit must line up with the portrait.

**Consent.** The face map's input is cut from the full map, so the two
cannot be quoted together: quote the full map alone, generate it, show it
(the checkpoint between steps), then quote the face map. The face in-paint
and the back hair are quoted together after the masks, each at its own
model. In the plan, give the
count, **four** calls for the layers (three `gpt-image-2-5-sunburst`: the
full map, the face map and the face in-paint; one `gpt-image-2-5-flare`:
the back hair), plus one Sunburst in-paint for gaze and one Flare edit per
expression when the user wants them, and the plan's cost from live quotes
with each call's real params (`width`/`height` at the portrait's size, the
face map at 1024×1024, and `quality=high`: size changes the price). Only
the full map has its input at plan time, so only its quote is firm: price
the rest as estimates the way SKILL.md's Check every handoff says (a quote
of that model with a placeholder input at that call's size, credits and
worst case, or that model's earlier quote at that call's size), and mark
them so. Each consent
gives its own live quote. Prices change, so never a figure from memory or
from this file. The user approves the quotes, not a measured charge. A
session budget covers the plan. Expressions: one pilot edit first, checked
(step 9), before the rest are quoted.

**Paths.** Pass the script every generated file by the path its `done`
event gives, never by the `--out` you asked for: a redo is not written
over the first file (it lands as `map-full-2.png`), and an old map fed to
the script wastes the credits just spent.

## The local script

`sequences/portrait_layers.py`, next to this file. It needs Python 3 with
Pillow **and** NumPy, checked before the plan and before anything is
spent: the preflight's `tools` reading gives the interpreter it checked,
`details.python` (a full path) plus the `args` of the usable
`details.pythonCandidates` entry (`-3` for the Windows `py` launcher, so
both are needed), and whether `pillow` and `numpy` are there (NumPy is
optional elsewhere, required here); or the probe of
`sequences/image-to-spritesheet.md` step 6 on a build without it. Run the
script as `"<details.python>" <args> -E "<skill folder>/sequences/portrait_layers.py"
<step> --portrait "<abs path>" --out "<abs dir>" ...`, every path absolute
and quoted (a user folder can hold a space). With Pillow or NumPy missing (either one
is enough) this route stops after the full map (the face map needs
`crop`): say so in the plan, offer the full map alone, and install
nothing.

`--out` is a working folder next to the portrait, chosen **once, before
`crop`**, and the same folder for every step: `<portrait stem>-layers/`,
or `-layers-2/` (then `-3/` ...) when that one already exists at that
moment. Later steps never pick again: `masks` and `layers` read what
`crop` and `masks` wrote there. The script writes over what is in its
folder, and an earlier session's layers are the user's. Each step prints one JSON line; a step that exits non-zero printed
why, and the next paid call is not quoted.

## 1. The portrait

The portrait is the reference of every call, so it is prepared once,
locally, and nothing else is used afterwards:

- **Opaque, on a plain light background.** One with transparency is
  flattened onto white first (a copy, `portrait.png` in the working folder).
- **A size the model draws at.** Every map and mask must be the portrait's
  exact size: pass `--param width=<W> --param height=<H>` equal to it. When
  `models show gpt-image-2-5-sunburst` does not allow that size, scale the
  copy locally to the closest allowed one of the same shape (1024×1536 for
  a portrait, 1024×1024 for a head) and work on the copy.
- **One character, facing the camera.** A three-quarter head works less
  well (untested); say so when the portrait is one.

## 2. The full map

`--ref portrait.png`, this prompt, the portrait's size. Front or back
hair is decided by **what the hair is drawn over**, never by its name: a
twin tail or a long lock that hangs over the shoulders, arms or clothes is
front hair; only hair those parts hide is back hair. Labelled back hair, a
lock drawn over a sleeve ends up under the body layer, and the sleeve's
outline cuts across it as soon as the hair moves. Name the character's
locks in those words where the prompt has them, and its hair ornaments
(ribbons, bows, clips): an ornament stays whole with the hair it sits on,
so it moves with that hair (a clip on the bangs is front hair, a ribbon on
a twin tail that hangs in front is front hair too). Name each one and
**its colour** in both map prompts ("the leaf clip on the bangs: pure cyan
#00FFFF"): told only "the colour of the hair it sits on", the model can
pick the wrong hair. **Glasses** go with the eye lines: name the frames,
bridge and arms in that line of both prompts ("and the glasses frames:
the rims, the bridge and the arms; the lenses are clear, so colour what is
seen through them"), and say the eye whites, irises and skin are seen
through the lenses. The frames then sit above the eyes and turn with the
face, and gaze moves the irises behind them (measured on thin oval
frames). `masks` also moves a patch of back hair that the
front hair surrounds into the front hair (`ornamentsMoved`):

```
Turn this character illustration into a flat-colour segmentation map of exactly the same size and framing. Keep every outline exactly where it is in the original; do not move, redraw or restyle anything. Fill each region with one solid colour, no shading, no lines, no gradients, no anti-aliasing:
- back hair (only hair that the head, neck, shoulders or clothes are drawn over, hiding part of it): pure blue #0000FF
- front hair (bangs, and every lock, strand or tail that is drawn over the face, shoulders, arms or clothes): pure cyan #00FFFF
- hair ornaments (ribbons, bows, clips): the colour of the hair they sit on, never their own
- face skin (face, ears): pure yellow #FFFF00
- neck and chest skin: orange #FF8000
- eyebrows: pure magenta #FF00FF
- eye whites (sclera): white #FFFFFF
- irises and pupils: pure green #00FF00
- eye lines and eyelashes: pure red #FF0000
- mouth: dark red #800000
- clothing and body: grey #808080
- background: black #000000
```

The colours are the script's palette: change one and the cut reads it as
another part. Look at the map next to the portrait (preview both) before
going on: the outlines sit where the portrait's do, the face is one yellow
region, and nothing is restyled. The small parts (brows, eye lines, mouth)
are rough here; step 3 redraws them. `gemini-nano-banana-2-1` was measured
too and returned another size and mixed up the brows; it is not offered.

## 3. The face close-up map

`portrait_layers.py crop --portrait "<portrait>" --map "<full map, its done path>" --out "<dir>"`
(every placeholder an absolute path, as The local script says) writes `face-crop.png` (the face from the map's yellow region, square,
scaled to 1024) and `crop.json`. Generate on it, `--ref face-crop.png`,
1024×1024:

```
Turn this close-up of a character's face into a flat-colour segmentation map of exactly the same size and framing. Keep every outline exactly where it is; do not move, redraw or restyle anything. Fill each region with one solid colour, no shading, no lines, no gradients, no anti-aliasing:
- face skin (face, ears, cheeks, blush): pure yellow #FFFF00
- neck skin: orange #FF8000
- front hair (bangs, and every lock or strand drawn over the face or the clothes): pure cyan #00FFFF
- back hair (only hair that the head or the clothes are drawn over): pure blue #0000FF
- hair ornaments (ribbons, bows, clips): the colour of the hair they sit on
- eyebrows (only the thin brow strokes): pure magenta #FF00FF
- eye whites (sclera only): white #FFFFFF
- irises and pupils: pure green #00FF00
- eye lines, eyelashes and eyelid creases: pure red #FF0000
- mouth (only the lips and the line between them): dark red #800000
- everything else (clothing, background): black #000000
```

At twice the size the brows, eye whites and irises come out close to a
hand-made split (measured against one: irises 0.97, eye whites 0.89, brows
0.76 overlap).

## 4. The masks

`portrait_layers.py masks --portrait "<portrait>" --map "<full map, its done path>"
--face-map "<face map, its done path>" --out "<dir>"` merges the maps into `labels.png` (the
close-up wins inside its box) and writes the masks, the portrait's size:
`mask-face.png` (the front hair, grown 3 px), used by step 5, and two
fallback masks for when the whole back hair (step 6) cannot be made:
`mask-backhair.png` (the head above the shoulders) and `mask-locks.png`
(the front locks below it). Transparent is
repainted, opaque is kept: the model's `mask` input reads them that way,
and it must match the first `--ref`'s size. A character with no front
hair (slicked back, short) has an empty `mask-face.png`: `faceInpaint` is
false in the step's line, the face in-paint is skipped (three calls: take
it out of the estimate), and `layers` runs without `--face-fill`. A character with no
visible back hair (none outside the masks, or only a few stray pixels) has
`backHairInpaint` false: the whole back hair (step 6) has nothing to line
up with and is skipped with its fallback (one call fewer), and `layers`
runs without `--back-hair`. `layers` refuses a fill left
out when its in-paint was not skipped. An
empty back-hair mask (no face or neck in the maps) stops the step with an
error: look at the maps, never quote an in-paint for an empty mask. A
map that is not the portrait's size is refused too, with the `--param
width/height` to redo it with.

## 5. The face in-paint

`--ref portrait.png --in mask-face.png --in-param mask`, the portrait's
size:

```
Inpaint only the transparent area of the mask. In it, paint what lies behind the pink front hair (the bangs and every lock and twin tail in front of the face, shoulders and clothes), in the same anime style, colours and lighting as the rest of the picture: the forehead and face skin, the ears and the sides of the face, the neck, the clothes and shoulders behind the long locks, and the pink back hair behind the head. Paint every masked pixel with that picture, never a flat or black fill, and draw no front hair. Keep the eyes, eyebrows, mouth, face outline and everything outside the masked area exactly as they are.
```

Say the character's own hair colour, locks and clothes where this says
pink. Ask the model to **paint** what lies behind, not to remove the hair:
asked to remove a large area, it can return the mask filled flat black.
`layers` refuses an in-paint whose masked area is mostly one colour that
neither the character nor the background has (that blank passes every
other check, hidden under the parts above); redo that one call once.
Look at the forehead before `layers`: the model can also **paint the
fringe again** inside the mask (measured on a boy with a thick wavy
fringe), which no check catches and which leaves the fringe's shape with
nothing behind it. Redo that call once, saying the transparent area is
exactly where the fringe is drawn, to remove it as if lifted away and
paint the bare forehead up to the hairline, with the hair behind combed
back. The
model re-renders the whole picture, outside the mask too (3–4% of pixels
measurably changed): an in-paint is never a layer on its own. The script
takes from it only what its mask hid, and only where it painted that
part's colour.

## 6. The whole back hair

Skipped when `masks` said `backHairInpaint` false (step 4).

One edit of the portrait (`gpt-image-2-5-flare`, `--ref portrait.png`, the
portrait's size, `--param background=opaque`, no mask) that keeps only the back hair, whole, as if
everything in front of it were see-through. It lines up with the portrait
(no shift on any of 8 edits measured), and as one piece it runs behind the
head, the body and every lock, so a sway or a head turn never shows its
end:

```
Edit this exact character illustration into a reference of her back hair alone: keep only the hair that is behind her head, drawn whole and uncut, as it would look if the face, neck, bangs, front locks, body and clothes were transparent: the inner layer of the chestnut-brown hair seen from the front, the back and underside of the hair behind the head, a little darker and in shadow, with no fringe and no strands falling forward over where the face was, falling straight down past where the shoulders and the clothes were, to the same length as the longest locks. Keep the same canvas size, framing, outline and position, so the hair lines up with the original pixel for pixel, in the same anime style and colours. No face, no skin, no eyes, no bangs, no front locks, no clothes, no hair clip: only the back hair on the same plain background.
```

Say the character's own hair and what to leave out. Ask for the **inner
layer** behind the head, darker and with no fringe: asked only for "the
back hair", the model can draw the whole hairstyle with its fringe
strands, which reads as a second copy of the front hair once they move. Lay it over the
portrait at half opacity before using it: its outline must follow the
portrait's hair. `layers` tells hair from background by which colour a
pixel is nearer (so pastel, silver or white hair on a light background
works), and refuses a picture that fills under 70% of the top of the portrait's
hair, front and back (shifted, or unread): redo it once, adding that the
head keeps exactly the same size and place (the top of the hair at the
same height, the same width at the temples and ears, the same outline,
not bigger and not lower), or use the fallback. Measured: one in two
first pictures for a wavy-haired character came back larger and lower;
the redo lined up. That picture is the whole back-hair layer, in its own
colours (a patch of the portrait's back hair beside it shows as a seam once
it moves); only thin strands of the portrait's back hair outside its
outline keep their own colour.

**Fallback,** when this edit is blocked or does not line up: two
more paid calls, `gpt-image-2-5-sunburst` in-paints like step 5 (quote
them live at the portrait's size with `quality=high`, credits and worst
case, on top of the edit already paid), in-paints `mask-backhair.png` (the head) and `mask-locks.png` (the locks),
each its own call, passed as `layers --hair-fill` and `--locks-fill`. One
mask for both came back flat black twice on a portrait with long twin
tails; the locks alone worked. A head mask that covers the whole head
outline (the map put the crown in the front hair) can come back black too:
then say the back hair behind the head is not painted.

## 7. The layers, and the check

`portrait_layers.py layers --portrait "<portrait>" --out "<dir>"
[--face-fill "<face in-paint, its done path>"] --back-hair "<whole back
hair, its done path>"` (or, the fallback, `--hair-fill` and `--locks-fill`
instead of `--back-hair`), the face fill only when `masks` said that
in-paint runs (`faceInpaint`), writes `layers/<z>-<name>.png`
(each cropped to its box) and `layers/manifest.json`: `size`, then per
layer `name`, `file`, `x`, `y` (its box in the portrait), `w`, `h` and `z`
(0 is the bottom). It moves hair strands too thin for the map from the face
to the front hair; merges specks (an anti-aliased edge read as a third
part, such as a red eye line into yellow skin read as orange neck) into
the part around them; and, where long front strands cover the clothes or
the back hair below the head, gives the body and the back hair what the
face in-paint painted there (`bodyFilled`). For that, the face in-paint's
prompt names the clothes behind the strands too. It prints the check:

- `recomposeMeanDiff`, `recomposePctOver16`: the layers stacked again
  against the portrait, over the character. Measured on one portrait: 0.7
  mean, 1.4% of pixels off by more than 16, on the soft edges. The back
  hair is left out of it with `--back-hair` (its generated shading is not
  the portrait's by design) and reported as `backHairMeanDiff`. A mean well
  above that (one measurement, not a calibrated limit) points to a map
  that moved an outline: look at `labels.png` against the portrait, and
  redo from that map (Redoing a step, below).
- `recomposeAlphaPctUnder98`: inside the character, how much of the stack
  is not opaque. A layer is hard toward the parts above it and runs under
  them, so it is 0 when the cut worked; anything else is a seam that shows
  the background through it in Unity.
- `layers-sheet.png`: every layer on a checker, and the portrait with **its
  hair moved** (the front hair swung a few degrees, the back hair the other
  way), which is what a rig shows and what the in-paints and the back hair
  are for. Read it before showing it: a hole, a cut end, a second face, or
  hair painted over the skin is a failed step; redo that one call.

Checkpoint, with the question tool, the sheet shown: **use the layers**,
**redo a step** (name which, and how many calls it forces, as an
estimate with its worst case), or **stop**.

### Redoing a step

Each step feeds the next, so a redo is never only its own call. The later
calls take inputs that do not exist yet (a new crop, new masks), so they
cannot be quoted up front: give the count below as an estimate, each
call priced with its own model and size (a placeholder-input quote, or
that model's earlier quote at the same size): every call the table
forces is a `gpt-image-2-5-sunburst` call at the portrait's size, except
the face map at 1024×1024 and a redo of the whole back hair, the
`gpt-image-2-5-flare` edit (step 6). Then run the normal flow again from the
redone step, each consent on its own live quote.

| Redo | Forces | Calls it forces |
|---|---|---|
| An in-paint, or the whole back hair | `layers` again, then `gaze` and `expressions` again if they ran (free: `layers` names them in `runAgain`) | 1 |
| The face map | `masks` again, so the face in-paint (painted for the old mask), the fallback in-paints if they were used (their masks change too), and the gaze in-paint if it ran | 2 (1 with no face in-paint; +2 with the fallback; +1 with gaze) |
| The full map | `crop` again (the face box moves), the face map, `masks`, the face in-paint, the fallback in-paints if they were used, and the gaze in-paint if it ran | 3 (2 with no face in-paint; +2 with the fallback; +1 with gaze) |

The order is the normal one: the map alone, checkpoint; the face map,
checkpoint; then the in-paints after `masks`: the face in-paint, and the
fallback in-paints (`mask-backhair.png`, `mask-locks.png`) if they were
used, since their masks change too. The whole back hair (the Flare edit)
takes no mask: a map redo reuses it, and it is quoted only when it is the
step being redone. Gaze and expressions are cut from `labels.png`.
After a map redo, if gaze ran, its mask can change: run step 8 again with
a new iris in-paint (the table's one call, quoted live), never the old
one. The expression edits are kept and only cut again, free: never pay
for new expression edits for a map redo. `runAgain` names the steps,
and `expressionGroups` the expression groups to cut again (each with
every variant); a group stays listed until it is cut. The free steps run
again into the same `--out`.

## 8. Gaze (optional)

So the eyes can look around, each iris must be whole, the part under the
upper lid too. `masks` wrote `mask-eyes.png` (each eye's area, grown up
toward the lid, minus the front hair; `maskEyes` is its size, and 0 means
no eyes were found: look at the maps, quote nothing). One in-paint with
`gpt-image-2-5-sunburst`, `--ref portrait.png --in mask-eyes.png
--in-param mask`, the portrait's width and height, `--param
quality=high`:

```
Inpaint only the transparent area of the mask, over her two eyes. In it, draw each eye with the whole iris as a complete round circle, the top of the iris fully visible and not hidden by the upper eyelid, the pupil and highlights as in the original, on clean white eye whites, in the same anime style and colours. Keep the iris the same size and in exactly the same place. Paint every masked pixel, never a flat or black fill. Keep everything outside the masked area exactly as it is.
```

`portrait_layers.py gaze --portrait "<portrait>" --out "<dir>" --iris-fill
"<its done path>"` keeps the visible iris and takes from the in-paint only
the hidden part of each iris's ellipse (the in-paint redraws the whole
eye, wider and restyled: never use more of it), makes the eye whites solid
under it, and adds `clip` to the irides row of the manifest: the eye
opening, which the irises are drawn inside (a sprite mask in Unity), so a
glance never shows an iris on the skin.

Judge gaze from the irides layer (the manifest's `irides` row,
`layers/<z>-irides.png`), never from `layers-sheet.png`, which `layers`
writes before `gaze` runs. It failed when `gaze` refuses the in-paint
(it exits with a message ending "a blank: redo it": check the map's irides
first anyway, as below) or the layer shows a hidden iris top in one flat
or smeared shade, with no pupil or highlight carried up. A gaze failure
gets one redo in all: if the map's irides are wrong (too small, cut by the
hair), the face map, offered with the question tool and its row's estimate
as step 7's **redo a step** is (the new iris in-paint it forces is part of
that redo); if they look right, the in-paint, on its own quote. Still bad
after that one redo: stop and show the user rather than pay again.

## 9. Expressions (optional)

Mouth shapes for speech and eye states come from **edits of this same
portrait**, one per shape (`gpt-image-2-5-flare`, `--ref portrait.png`, the
portrait's size, `--param background=opaque`), each changing only the
mouth or the eyes:

```
Edit this exact character illustration and change only her expression; keep everything else identical: the same framing, size, pose, head position and angle, hair, hair clip, clothes, colours, line art and plain background, so the new picture lines up with the original pixel for pixel. Change only the mouth and the eyes as described: <one shape>.
```

Shapes measured: mouth wide open "aa" with upper teeth; small round "oh";
wide flat "ee" with teeth; open smile; eyes gently closed (a blink); half
closed; closed in a happy arc. All 7 came back aligned (no shift; only the
mouth or eyes changed, besides 2–4% line-art noise). Run **one pilot**
first and lay it over the portrait before quoting the rest.

`portrait_layers.py expressions --portrait "<portrait>" --out "<dir>"
--variant "mouth:<name>=<done path>" ... --variant "eyes:<name>=<done
path>"` (a name is letters, digits, `-` and `_`; pass **every** variant
of a group each time, the pilot included, since a group passed is cut
again whole; a group not passed keeps its swaps) cuts each group over one
patch (what its variants changed near the
mouth or the eyes, grown 6 px, minus the front hair), the portrait as
`neutral` too, into `layers/expressions/<group>-<state>.png`, listed in the
manifest under `swaps` (drawn just under the front hair). The `neutral`
state is marked `base: true`: it is the base layers themselves, so a rig
shows the base layers (with the irises gaze moves) for it, never that
sprite. A non-neutral eye state covers the eye layers while shown. An eye
state is cut no higher than the top of its own eye (each eye at its own
top, so a tilted head works): eye states that close or narrow the eyes
work, but one that **widens** them (surprise, raised lids) loses the lids
above that line, so it is out of scope: say so when one is asked for.

## 10. Rig for 2D Animation (optional, free)

`portrait_layers.py rig --portrait "<portrait>" --out "<dir>"` writes
`<dir>/character.psb` (every layer at its place, the expression swaps as
hidden layers) and `<dir>/character.psb.json`, the rig sidecar: a bust and
face skeleton placed from the labels, the hair layers banded onto bone
chains from the scalp to the tips, and the swaps as categories. Run it
after `layers` (and after `gaze` and `expressions` if they ran), and again
after any of them runs again; it refuses while `layers` lists steps to run
again. Its line names the `layers`, `bones`, `skinned` layers and `swaps`.
After `gaze`, the PSB's visible `Irides` is kept inside the eye opening
(nothing draws over the lids at rest), and two helper layers come with it,
at the very bottom of the stack (the PSD Importer shows hidden layers, so
everything else covers them): `IridesWhole`, the whole irises `gaze`
completed, on the irises' own bone, and `IridesClip`, the opening, on the
face. For the eyes to look around, the user hides `Irides`, gives
`IridesWhole` `Irides`' sorting order and sets its renderer to Visible
Inside Mask, and adds the mask on the face **bone**, not on a
layer: in the scene, a new GameObject made a child of the `Face` bone,
the one under the `Head` bone (Unity may show it as `Face_1`, since a
layer has the same name), at `IridesClip`'s rest position, with a Sprite Mask of
the `IridesClip` sprite, and `IridesClip` itself hidden. A layer's
GameObject never moves (its mesh does), so a mask put on one stays behind
when the head turns: rotate `Head` once with the mask on to check.

To rig that PSB in the user's Unity project, with no Skinning Editor pass,
write a small Unity editor script from `sequences/rig-2d-snippets.md` (read
it first: its snippets import every layer as a sprite, place bones, bind a
part rigidly or over several bones, and set up swap categories). Its
**Rules for the script** apply (ask first, which project, editor only, what
the script may read and write, the header, three tries), then:

1. **Packages.** The project needs `com.unity.2d.animation` and
   `com.unity.2d.psdimporter`. Read its `Packages/manifest.json`; when
   either is missing, ask before adding it there.
2. **Copy** the PSB and its sidecar into one folder under `Assets/` (for
   example `Assets/Characters/<name>/`, a `<name>` of letters, digits, `-`
   and `_` only), keeping the pair's names (the sidecar is `<psb>.json`).
3. **Write the script** in the guide's `Assets/Editor/Rig2D/` (reuse
   `Rig2D.cs` when it is there; the entry point is `Rig2D.Portrait.cs`).
   It reads the sidecar and maps it onto the snippets:
   - `version` is `1`; refuse any other (the sidecar's shape changed).
   - `bones`: `name`, `parent` (empty for the root), `head` and `tail` in
     PSD pixels: the guide's `Bones` with `psdHeight` = the sidecar's
     `height`.
   - every layer listed in a bone's `layers` is bound rigidly to it
     (`BindRigid`);
   - every layer in `skins` bends (`BindWeighted`). Its `weights` gets a
     point `p` in y-up pixels: take `y = height - p.y` (PSD pixels, as the
     bands are). Each of the layer's `bands` then weighs
     `clamp01(min(y - (y0 - blend / 2), (y1 + blend / 2) - y) / blend)`
     (0.5 at `y0` and `y1`; with `blend` 0, 1 inside `[y0, y1]` and 0
     outside); a band's `bone` `"A|B"` means `A` where `p.x` is left of
     `split_x` and `B` right of it. Pass the first band's bone as
     `fallback`, for a point no band reaches;
   - `categories` (`category`, `label`, `layer`) are the guide's
     `Categories`.
   Log each layer no bone carries, and end with the guide's line:
   `[Rig2D] rigged <psb>: <n> bones; unrigged: <layers, or none>`.
4. **Run it.** With the project closed: `unity run "<project>" --log-file
   "<log>" -- -executeMethod <Class>.<Method> -psb
   "Assets/Characters/<name>/character.psb"` (batch mode is automatic).
   With it open in an Editor, batch mode cannot open the project: run the
   method in that Editor (the Unity CLI's way to run code in a live
   Editor), or ask the user to close it. **Read the log:** the rig worked
   only if it has the `[Rig2D] rigged` line; name any layers after
   `unrigged:` to the user (they stay still). An exception, or no such
   line, is a failed rig: say what the log says. `executeMethod class ...
   could not be found` with no `error CS` line means the script was not
   compiled: a 2D package is missing, or the asmdef is not beside the
   script (its define constraints then leave it out without a word).
5. **Compile errors.** `error CS` lines in your script are yours to fix
   (the guide was checked on Unity 6000.6 with 2D Animation 16.0.1 and PSD
   Importer 15.0.1; on other versions a member can be renamed or moved).
   Errors in other files are the project's own scripts failing: tell the
   user and change nothing there; never change the project's package
   versions without asking. After three tries (a compile error and a run
   that throws both count), delete `Assets/Editor/Rig2D/` if you created
   it (only that folder), say so, report the errors, and give the user
   the PSB alone, which 2D Animation imports with every layer in place,
   to rig in the Skinning Editor.
6. **Hair that hangs.** Rigged, the hair turns with the head like a
   helmet. Offer the guide's `HangingChain` (section 7): a runtime script
   outside the `Editor` folder, so it compiles into the user's game build,
   added to the character's instance in their scene and saved as a prefab
   variant; say so, and write it only after a yes. List the hair chains'
   bones: from the
   sidecar, `FrontHairL1`, `FrontHairR1`, `BackHairL1`, `BackHairR1` at
   gravity 0.6 and their `…2` tips at 0.5 (Unity adds `_1` to a bone that
   shares a layer's name). Leave the bangs bones out: on their own band
   under a still scalp, bangs that swing tear the fringe at the part and
   seam across the forehead. The hair then keeps hanging when the head
   tilts and swings a little after each move; rotate `Head` in Play mode
   to check.

The PSB then imports as one character: drag it into a scene and rotate its
`Head` bone, and the face parts turn with it while the hair bends from the
scalp. The `Mouth` and `Eyes` categories swap the expressions; their
`neutral` is an empty sprite, so the base layers (and the irises gaze
moves) show for it.

## Limits, say them in the plan

- **The back hair is the generated picture.** Its shading is not the
  portrait's (`backHairMeanDiff`), so what shows of it differs slightly in
  a still frame.
- **Under wide hair motion, a few stray edge pixels can remain** where a
  map's edge met another colour; the edges blended with the background are
  de-fringed, so they are rare. Watch a test motion before rigging.
- **Brows over the fringe** (drawn through the hair, a common anime style)
  are the top layer, above the front hair, so a head turn does not double
  them; the map must give them their own colour where they cross the hair.
- **The rig is for front-facing busts.** Skin weights come from
  horizontal bands only (hair and necks that hang), the left and right
  hair chains split on one vertical line (a symmetric front view), and the
  hair layers get a plain grid mesh. Arms, tails, very wide hair, a 3/4
  view or chibi and full-body proportions need another rig. It makes no
  animation clip: the user animates the bones and swaps.
- **Measured on anime portraits only** (long and short hair, a ponytail,
  wavy hair, a fringe over the brows, glasses, pastel hair on a light
  background). Other styles and realistic faces are untested: say so, and
  look harder at the maps.
- **The content filter can refuse a portrait as a look-alike** of a known
  character or a real person, at the first call that takes it as input
  (the full map), for nothing charged: very common combinations (silver
  hair and a school uniform, an auburn bob with round glasses) were
  refused twice in five characters. Show the user the reason. When the
  portrait is the user's own design, offer a revised one (an unusual hair
  colour or outfit), as for any blocked prompt; when it depicts a real
  person or an existing character, relay the refusal and suggest no way
  around it.
- Faint traces of the thinnest strands can stay on the forehead once the
  front hair moves; they are in the sheet's last picture.
