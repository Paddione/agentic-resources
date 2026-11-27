# Sequence: a 3D character or prop that moves like 2D animation, in the game's style

A user who said not to ask (SKILL.md, When the user says not to ask): every question
this file has you ask, but money and writes to the user's project, is your own call; say
what you chose in the final reply. The project folder and every package to add (Rules for
the code) are still asked and wait for a yes, as SKILL.md requires.

**Experimental.** Measured on seven subjects (four bipeds, a goblin enemy, a
fox, a treasure chest), ten styles and a playable side-scroller in Unity 6000.6
with URP 17.6 and glTFast 6.21; its rules may still change. Say so in the plan,
before the first quote.

A 2D game wants characters that walk and idle like its own art: its colours,
its lines, its frame rate, seen the way its camera sees them. This route makes
them from a rigged 3D model rendered in that style. The style is the game's:
settle it with the user (step 2) and build the look for it (step 7); nothing in
this route fixes one. Next to a cut-out rig (bones on layered sprites,
`sequences/image-to-layers.md`), tell the user plainly what it trades:

- **Better:** joints never break (one skinned mesh), stock clips move
  naturally at once, limbs overlap and foreshorten correctly, and any new view
  or clip costs nothing more.
- **Worse:** it is a 3D look-alike of the concept, not the drawing itself (a
  face comes out simpler); no smears, redrawn poses or other hand-drawn
  tricks; cartoon timing needs clips written for it.

```
the cast, its motions and the game's style
   │  1. plan:     the lane, the motions per subject                     (free)
   │  2. style:    the game's look, as a list the user approves          (free)
   │  3. concept:  one image per subject in that style (`models.md`, Text to 3D)
   │  4. mesh:     model3d-tripo-p2, pbr off; count its parts           (paid, then free)
   │  5. motion:   a rig with stock clips, or a clip written locally     (paid or free)
   │  6. scene:    Unity: import, face, scale, camera                    (free)
   │  7. look:     a shader for that style, written in the project;
   │               one still approved before any frames                  (free)
   │  8. timing:   the style's drawings per second                       (free)
   │  9. frames:   GIFs and a scene that plays                           (free)
   │ 10. play:     when asked, a playable scene and a recorded trailer   (free)
   ▼
each subject's clips in the game's style, in the user's project and as GIFs
```

Every paid step follows the normal flow (quote and consent, generate, look).
Steps 6 to 9 write code into the user's Unity project: follow the Rules for
the code below.

## Rules for the code

- **Ask first.** Name the project, the folder you will add (one folder, such
  as `Assets/Look2D/`) and every package you would add (step 6), and wait for
  a yes. Never make a project unasked.
- **Write it for the project and the style in front of you**, from the hints
  below: they give what the code must do and the traps, not code to paste.
  Check each piece in the live Editor (the `unity-cli` skill) before building
  on it.
- **Look at the first frame** of every render batch before rendering the rest
  (step 9 has the trap that makes this worth it).
- **Three tries** per piece that fails to compile or throws: then delete only
  the folder you created, say so, report the errors, and hand over the GLBs.

## 1. Plan

Per subject, settle the motions and where each comes from:

| Subject | Motion source |
|---|---|
| Biped | `model3d-tripo-rigging-v1` presets (`biped:walk`, `biped:idle`, …): one paid call per clip, every call on one mesh returns the same skeleton, so each later preset is just one more clip on the same character. For a cast, one rig call per character and each move made once, shared (step 5) |
| Four legs | as `sequences/creature-rig-and-animate.md` routes them (read it first): every clip, the walk included, is written locally on that rig (step 5) |
| Other creatures | as `sequences/creature-rig-and-animate.md` routes them |
| Rigid prop (chest, crate, lamp) | no rig: a clip written locally on the whole model (step 5) |

What the stock biped presets really are, so the plan promises the right
thing:

| Preset | What it returns | Use |
|---|---|---|
| `idle` | 15 s, the weight shifting mostly sideways | reads nearly still in profile: say so, offer a locally written idle (step 5) |
| `walk`, `run` | an in-place cycle | as is; match the scene's speed to the stride (step 8) |
| `jump` | five small hops in a row, the hips moving up and down | take the airborne poses from its biggest hop; physics does the height (step 10) |
| `slash` | 6.6 s, a vertical combo | too long and vertical for a quick game attack; quick horizontal attacks are written locally (step 5) |
| `hurt` | 14 s cowering on the ground | a knocked-down pose, not a flinch; write the flinch locally (step 10) |

The rigging presets were quoted 42 credits (worst case 71, the hold) and
charged 59 on every one of 13 runs. Read the worst case from the quote's
`worstCase`, not from a rule of thumb: here it is not the quote plus 20%. Say
all three before consent ("quoted 42, worst case 71, charged 59 on every run so
far"). The expected spend of a cast is 59 per rig, but spending limits check
the worst case: a per-run limit needs 71, and each rig in flight reserves 71
against the daily limit until it settles, so N rigs run one at a time need
59 x (N - 1) + 71 of daily room, and N run at once need 71 x N.

## 2. Style

Settle the look before the first concept, because it shapes the concept
too. Take it from what the user points at, in this order: the game's own art
(a screenshot or a sprite they name), a reference image they give, their
words. Write it as a short list and ask the user to approve it (Approve /
Revise), filling only what the source shows and naming the rest as your
assumption:

| Choice | Range |
|---|---|
| Camera | strict side view, a slight three-quarter, top-down at an angle; orthographic for a 2D game |
| Shading | none (flat, unlit), a number of flat bands (two or three is common), soft gradient, or only what the texture paints |
| Shadow tone | darker of the same colour, tinted (cool, warm, a fixed shadow colour), how dark |
| Lines | none, an outer outline, outline plus inner lines; colour (ink black, a darker shade of the fill, coloured); width in pixels at the game's resolution; steady or boiling (a small per-drawing wobble) |
| Colour | the textures as they are, more saturated, or a limited palette (the game's, if it has one) |
| Timing | smooth, on twos (12 drawings a second), on threes (8), or the game's own rate |
| Light | where the key light comes from in the game's art (it decides where the shaded side falls) |

The style carries to every subject of the cast: approve it once.

## 3. Concept

The Text to 3D rules of `models.md` hold (one approved image, a transparent
background, a biped in an A-pose with empty hands). For this route add:

- **The style's colour in the prompt**, and **no painted shading** whenever
  the shader shades: "flat even colours with no painted shading, no
  highlights, no cast shadows, even flat lighting". The mesh's texture copies
  what the image paints, and painted shading fights the shader's.
- **A creature in the pose `creature-rig-and-animate.md` asks for**
  (three-quarter, the view its rigger was measured on), with "exactly one
  tail, held straight out behind the body, its whole length clearly separated
  from the body and the legs". From a three-quarter view the reconstruction
  once rebuilt the far side of a tail as a second tail: when step 4 counts a
  doubled part, redraw the concept from the side, turned only about 15° toward
  the camera, legs apart so all four show. That side view was checked on a
  creature rigger since retired, so check the rig it gives (step 5).
- **A prop from a low three-quarter view**, standing on its base.

A `background=transparent` result can carry a faint halo at partial alpha and
colour hidden under alpha 0, which shows as a glow in some viewers. Look at it
on mid-grey, not black. The free fix: alpha below 128 to 0, alpha from 128 to
255, colour zeroed where alpha is 0; carry the cleaned file forward.

## 4. Mesh

`model3d-tripo-p2 --in <concept> --in-param reference_image --param pbr=false`
(add `--param face_limit=20000` for a creature): `pbr=false` gives one flat
base-colour material, which suits a stylised shader. Keep PBR only when the
style wants the model's real materials.

Then **count its parts** on the turntable (`--views view,turntable`) against
the concept, item by item: heads, ears, arms, legs, tails, accessories. Put
the count in the `checked:` line ("1 head, 2 ears, 4 legs, 1 tail: matches the
concept"). A blob or a colour patch you cannot name is a part until proven
otherwise: a doubled tail showed only as a white blob at the hip and a second
white tip at some angles. A mismatch fails the mesh; the fix is a revised
concept and a new mesh, offered with their quotes, never a rig on it.

## 5. Motion

**Stock clips.** After each rig, read `--views rig,poses` with the motion and
rig numbers of `show-result.md`'s tables, plus two checks for this route:

- **Chains against the body plan:** one chain per leg and one per tail. A
  chain more than the plan has is a duplicated part step 4 missed.
- **`legsMoving` equals `legs`** on any walk, stock or written locally. When
  legs stay still (a quadruped once came back with its front legs parented to
  the head, unnamed `bone_<n>` chains, 2 of 4 legs moving), the free fix is,
  per still front leg, a swing at the shoulder bone and a fold at the wrist
  while the foot travels forward, timed a quarter step after the hind foot on
  the same side (sample the hind feet's positions over the clip to find when
  each reaches furthest forward and the step length). Over a stock walk, add it
  as a local clip on top; in a walk written locally, add the swing to that
  walk itself.

**Share the stock moves across a cast of bipeds.** Every Tripo Rigging 1.0
rig came back with the same 41 bone names, so a move made on one character
plays on the others. Give each other character a fitted copy: the source's bone
rotations, with the hip movement scaled by the ratio of the two characters' hip
heights (the clip also stores the source's bone positions, which would impose
its proportions). Measured against each character's own stock walk: the same
height (0.995 against 0.997), the same stride speed and the same foot contact.
Each character then needs one rig call and one GLB, and each new move one call
for the whole cast. Look at a body built very differently from the source (a
much stockier or smaller one): a walk borrowed from another character left a
stocky one 7% lower. A creature keeps its own rig and moves.

**Clips written locally** (an idle, a prop's hop, an attack, a crouch, the fix above):

- **Key every bone's position as well as its rotation**, at the rest pose's
  values. A clip that keys rotations only leaves the hips where the previous
  clip put them: an attack started from a run lunged forward by the run's
  hip offset.

- **Rotate about world axes, not bone axes.** A creature rig's bone axes
  point anywhere. Express each movement as a turn about an axis of the
  world (up for a head turn, the axis across the body for a nod or a tail
  raise), taken from the character in its bind pose, and carry it into the
  bone's parent space before adding it to the bone's rest rotation. Then a
  raise of the tail or a nod reads in profile whatever the rig.
- **Bones that carry more than their name says:** turning a head bone can
  swing limbs parented under it (the case above); turn the next bone up the
  chain instead.
- **An idle that reads in profile:** breathing at the chest (about ±1.5°, two
  breaths a loop), a head turn toward the camera and back (about 20°), an ear
  flick, a tail wave travelling down the chain (amplitude growing toward the
  tip, a phase lag per bone). Four seconds loops well.
- **Quick attacks:** pose the arm and the weapon by aiming each segment at a
  direction in the character's frame (forward, up, toward the camera), on top
  of the idle stance, and key the result. Keep the blade direction in the
  screen plane: a blade swung toward the camera foreshortens and looks short
  and bent. Turn the hand so the blade's broad side faces the camera. A few
  variants of the same length (7 drawings, about 0.3 s) read better than one
  repeated: a sweep, a backhand, a thrust.
- **A crouch:** lower the hips and solve each leg as a two-bone chain to the
  foot's planted position, the knee bending forward; the head keeps its
  rotation so the eyes stay level. A crouch-walk is the same pose with each foot
  planted half the cycle (sliding back at the walking speed) and lifted forward
  the other half.
- **A rigid prop:** put the model under a pivot at the base of its bounds, and
  animate a child: a hop with an anticipation squash, a stretched take-off, an
  apex, a stretched fall, a landing squash and a rebound, keeping the volume
  (the sides widen as the height squashes, and narrow as it stretches), with a
  few degrees of tilt. About 1.25 s. One mesh cannot open a lid: say so.

## 6. Scene

- **Packages:** glTFast (`com.unity.cloud.gltfast`) to import GLB, and the
  render pipeline the project already uses (the hints below are written for
  URP); each package asked for first (Rules).
- **Facing:** the yaw that shows the style's view differs per file. A static
  mesh and the same mesh rigged came back 90° apart, and a mesh drawn from
  three-quarter keeps that turn (its body along the line between the hind and
  front leg roots). Render the bind pose at four yaws and look, rather than
  assuming one.
- **Scale:** every generated model is about 1 unit at its largest. Scale
  animals, props and smaller enemies against the characters (a fox at 0.6, a
  goblin at 0.8, a chest at 0.42 next to 1-unit people).
- **A held weapon on a rig without finger bones:** the fingers cannot close,
  so seat the grip inside the hand: find the palm from the hand bone's own
  vertices (their longest spread is the fingers, the next the knuckles' width,
  the least the palm's facing), put the grip across the palm's middle with the
  blade out on the thumb side, and turn the palm away from the camera so the
  fingers are drawn over the grip. A generated sword came back toy-like
  (large ball pommel, short blade, painted stripes); a simple model built for
  the 2D read (a long slim blade, a crossguard, flat colours) looked better.
- **Camera and background:** as the style says; a plain background for the
  checks and the GIFs.

## 7. Look: hints for a shader in the game's style

Write the shader in the project (HLSL, or Shader Graph with a custom
function), with only what the approved style asks for. Then render **one
still** of a character in it, next to the same pose with the model's own
material, and get the user's approval (or the game's art beside it) before
any frames: it is free, and every frame inherits it.

- **Flat or unlit:** the base colour, with no lighting term; the lines and the
  timing carry the 2D feel.
- **Bands:** pick a flat tone from how much each surface faces the main
  light, with one threshold per band (hard steps, not a ramp), tinted as the
  style's shadow tone. Soften each band edge over about one screen pixel so it
  does not crawl from drawing to drawing. Leave out specular and received
  shadows unless the style draws them.
- **Light placement decides whether bands show.** In a side view, a light near
  the camera leaves almost every visible surface in the lit band; one from the
  character's front and above, nearly side-on to the camera, splits a profile
  into a lit front, a mid side and a shaded back. Place it where the game's art
  puts its light.
- **Smoothed normals, baked into the tangent channel:** weld vertices that
  share a position, average their normals, then run about 8 passes of
  averaging over mesh neighbours, and store the result as tangents (which skin
  with the mesh). Bands lit with them stay large clean shapes on bumpy detail
  (curly hair broke into blobs before this), and an outline pushed along them
  has no gaps where UV seams split the normals.
- **Outline:** an inverted hull: a second pass that draws the model's back
  faces pushed out along the smoothed normals, by an amount set in screen
  pixels, so the line keeps the style's width however far or small the model
  is. In URP that second pass must be one URP draws in addition to the main
  one, and the shader needs a depth pass too. Inner lines, where the style
  draws them, need a screen-space edge pass (where depth or normals jump)
  instead or as well.
- **Boil:** vary the line width a little per drawing with a noise of the
  vertex position and the drawing number.
- **Palette:** a limited palette maps each output colour to its nearest
  palette entry (in the shader, or as a post step).
- **Texture:** generated textures still carry some painted soft shading
  (cloth folds, hair); say so rather than fight it.

**Hints by style family.** Ten styles were built this way on the same cast;
what each family needed beyond the parts above:

| Family | What makes it read, and the trap |
|---|---|
| Cel bands with an ink line | the light placement and the smoothed normals above; one example that read as drawn: three bands (shadow about two-thirds as bright, tinted cool), a near-black line about 4.5 px at 1080p, on twos |
| Pixel art | render the camera into a small target (about 270 px tall) and show it scaled up with no smoothing, the interface kept at full resolution; for the palette, snap each colour's brightness and keep its hue (snapping each colour channel apart turns brown into red and blue); let the darkest step be the line's ink, or black hair and boots turn grey; sample the texture sharp (a blurrier sample bleeds colour between the texture's islands) |
| Printed patterns (halftone dots, hatching, stipple, chalk grain) | lay the pattern out in screen pixels scaled to the screen height, so it keeps its size on every character and at any resolution; move it each drawing for a living texture, or hold it for print; keep the grain coarse enough to read at game size, or it reads as noise |
| Monochrome (pencil, ink) | brightness only, paper and ink both neutral grey: any tint brings colour back |
| Silhouette and rim | ink fill with a hard rim where the surface turns away from the camera, limited to the side away from the key light; no texture colour |
| Glow (neon) | a dark body and a glow in each part's own hue at full brightness, so dark materials glow too; keep the glow band narrow or the figure looks lit |
| Painterly (watercolour) | transparent washes that leave paper bare on the lit fronts, pigment pooling darker at the edges, grain only in the lighter washes; dark colours stay dense, or they turn into grey mottling |
| Paper cut-out | each piece in flat paper colour with a soft fibre grain fixed to the object, a white cut edge in place of an ink line, and a drop shadow offset down and to one side and pushed back in depth so it falls on the layers behind |

Judge a style on the level as well as on the characters: a stipple
(risograph) print looked fine on a figure and turned the ground and hills into
noise, and the user rejected it. Each style also sets its own background,
drawings per second and line wobble. Let the user switch between candidate
styles live in the scene (a dropdown over the view, the arrow keys looping
through them) before one is approved.

## 8. Timing

Smooth timing plays the clip as it is. Held drawings (on twos, on threes)
pose the character only at drawing times (12 a second on twos, 8 on threes)
and hold each pose until the next: in Play mode, a component on the character
samples its clip at those times, with the character's animator turned off so
it does not overwrite the pose. For rendered frames, use a whole number of
drawings per loop, spread evenly over the clip's length, so the loop has no
seam where it wraps.

An in-place walk is a treadmill: in a side-scroller the background moves, not
the character. To check foot slide, move the character forward at the
planted foot's backward speed (measure it from the foot bones while they are
lowest) and measure how far a planted foot still drifts.

## 9. Frames and the scene that plays

- **Offscreen renders from Editor code draw stale skinning:** a camera
  rendered into a texture outside Play mode showed the bind pose, although
  the clip had been sampled. Each drawing, bake every skinned mesh into a
  plain mesh with the same materials, hide the skinned one, and render that.
- **GIFs:** one shared palette for all frames, no dithering (flat colour stays
  flat, nothing flickers), and a contact sheet beside each GIF to check every
  drawing at once.
- **A scene to watch:** save the generated materials and smoothed meshes as
  assets (made in memory, they vanish with the scene), put each subject with
  its clip in one scene, and play it. Play mode needs the Editor focused or
  Run In Background on.

## 10. A playable scene and a trailer (when asked)

What a side-scroller built on these characters needed:

- **Turning in place.** Each clip carries the hips at some offset from the
  model's origin (the run, 0.6 units forward); turning around mirrors it, a
  visible jump. Measure each clip's average hip offset and cancel it.
- **Turn like a sprite:** mirror the model rather than rotate it 180°, so a
  weapon stays in the near hand.
- **Run speed** equals the run clip's stride, so the feet do not slide.
- **Jump:** physics does the height. Pick the airborne pose from the jump
  clip by the vertical speed (rising before the peak, falling after), and hold
  the hips where the idle has them. What made it feel good: a quick rise
  (about 0.35 s to the top), a faster fall, a short hop when the button is
  released early, a short grace time after running off a ledge and before
  landing, and a stretch on take-off and squash on landing, all in held
  drawings.
- **Attacks** on the mouse (or the game's button), drawn on ones (24 a
  second) when the style holds drawings, so a 0.3 s move still reads; each one
  different from the last, a click near the end queuing the next.
- **Crouch:** shrink the collider; while something is above, keep the
  player down and refuse a jump or an attack until there is room to stand.
- **An enemy:** walks toward the player at its stride speed and stops just
  short; on a hit, a flinch written locally (recoil, knock-back, a white flash
  for a drawing or two); down after a few hits (a cowering clip), back up a
  few seconds later.
- **Check the level against the character:** an overhang lower than the
  player's height blocks them, a gap wider than a jump drops them, and a prop
  next to an overhang can trap them crouched. A prop the sword hits looks wrong: hits are
  for enemies.

Recording a trailer:

- Fix the frame rate (Unity's capture frame rate) and save a screenshot every
  frame, so the take does not depend on how fast the machine renders; encode
  the frames to an MP4 with ffmpeg (the doctor's `tools` row says where it is).
- Drive the player with simulated input from a script that reacts to where
  the player is (jump at the edge, swing when the enemy is in reach), and
  retry a jump until the player is in the air: a fixed timeline drifts.
- In the Unity Editor, simulated keyboard input is dropped while Unity is not
  focused (the Input System's play-mode and background settings): set them for
  the take and put them back after.
- Keep the ground flat for a demo take, change the style every one or two
  seconds, and hide every hint but the style name.

## Checks before calling it done

Read the frames yourself, then report each with what you saw:

- Each subject's part count matches its concept (step 4).
- Every leg moves on every walk (`legsMoving` and the frames).
- The frames match the approved style still: line width and colour, the
  number of bands, the palette, the timing.
- Lines, where the style has them, are continuous, with no gaps at seams or
  joints.
- Bands, where the style has them, are large clean shapes, with no blobs or
  crawling edges.
- Foot drift at stride speed, per step (on a 1-unit biped, 0.8 to 1.7 cm was
  invisible at game size; a clip that holds its first frames drifts more on
  the step across its loop point).
- Idles read from the style's camera.
- Facing and scale are consistent across the cast.
- In a playable scene: turning does not move the body, an attack does not
  lunge, and every gap, overhang and prop on the route can be passed.
