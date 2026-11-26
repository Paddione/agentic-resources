# Sequence: rig and animate a creature that is not a biped

A user who said not to ask (SKILL.md, When the user says not to ask): every question
this file has you ask, but money, is your own call; say what you chose in the final reply.

A spider, a dog, a horse, an insect, a bird, a snake or a fish gets no
Uthana motion: every Uthana model is biped only (SKILL.md's model table).
`model3d-tripo-rigging-v2-5` is the only rigger with creature rig types,
and it holds up for some body plans and not others. `model3d-meshy-rigging`
is a character rigger (its `height_meters` is a person's height, and it scales
the result to it, 1.7 m by default) that has not been checked on creatures: do
not offer it for one. It returns the rig in a still pose (a single-keyframe
clip), never a motion. Read this before
proposing the plan: a rig that does not hold up spends credits and leaves
the user with a model that deforms badly, when the agent could have rigged
it itself.

## 1. Decide the body plan, then route

Name the creature's body plan before any quote and take its row. The rig
types and presets are the `rig_type` and `animation` enums of `models show
model3d-tripo-rigging-v2-5`; read them there before the quote.

Every row assumes the mesh came from a concept in the row's pose (step 3):
the rows below were measured that way, and a creature drawn in a natural
pose (mid-stride, legs tucked, coiled, wings folded) rigged worse in every
body plan that was compared.

| Body plan | Examples | Unity AI rig | Preset clip | Then |
|---|---|---|---|---|
| Biped | person, robot, goblin, upright animal | `uthana-character-rig` (`rig-and-retarget.md`), or `model3d-tripo-rigging-v1` | Uthana text or video to motion; or a v1 preset (`biped:idle`, `walk`, `run`, `dive`, `climb`, `jump`, `slash`, `shoot`, `hurt`, `fall`, `turn`) | as `rig-and-retarget.md` says |
| Four legs, upright gait | dog, wolf, cat, horse | `rig_type=quadruped` | `quadruped:walk` | other clips by the agent (steps 4 and 5) |
| Fins | fish, eel, shark | `rig_type=aquatic` | `aquatic:march` (a swim down the body) | other clips by the agent |
| No legs, on land | snake, worm | `rig_type=serpentine` | **none**: leave `animation` unset (`serpentine:march` moves part of the spine and dips under the ground) | every clip by the agent |
| Six legs, eight legs | beetle, ant, spider, scorpion | `rig_type=hexapod` or `octopod`, rig only | **none**: leave `animation` unset | every clip by the agent |
| Wings | bird, bat | `rig_type=avian`, rig only | **none**: the model list has no avian preset | every clip by the agent |

Edge cases: a lizard sprawls (legs out to the side), so the quadruped walk
reads as wrong even on a good rig; a crab walks sideways with claws, which
neither the octopod rig nor the tetrapod gait below covers: both get a
local rig (step 4), with the gait written for them.

Why the rows are what they are (2026-10-26, plugin 0.1.0-alpha.17: a
conforming and a natural concept per body plan, a mesh from each, every
rigger and preset the model list allows, judged with `--views rig` and
`--views poses,feet` and played in Unity):

- `rigging-v1` presets drive every limb in all 11 clips, and every preset call on the same mesh returns the same skeleton, so all of them play on one character.
- The quadruped rig keeps each leg's skin on that leg (14% of the mesh per leg at most), and its walk moves all four legs, 3.6% of the model's size into the ground. Its head bones also carry part of the neck and shoulders. From a mid-stride concept, one leg came back unskinned and the walk went 10% through the floor.
- The aquatic rig and march work on a straight, side-view fish; a bent one left half its chains still.
- The hexapod, octopod and avian rigs skin each limb to itself from a concept with the limbs spread (at most a third of the mesh per limb, a spider's legs one colour each in the rig view). An earlier run (2026-10-05) that did not control the concept's pose found them bleeding into the body. Their presets fail either way: `hexapod:walk` and `octopod:walk` move about half the legs and swing others through the floor (31% and 38% of the size).
- The serpentine rig is a clean spine; its march moves part of it and dips 5% under the ground, and a coiled concept left a bone unskinned.
- Rigging 2.5 returns a different skeleton on every run of the same mesh (bone count and names), so clips written for one of its rigs do not play on another: rig once, then write every clip on that rig.

So a rig-only row is quoted as a rig, never "to try a preset". A rig type
or preset that `models show` lists and this table does not is treated as a
local rig (step 4) until it has been checked the way step 6 describes. A
creature between two plans (a centaur,
a dragon that walks and flies) gets the row of the body the user most wants
animated, said in the plan.

## 2. Check that a lane exists before anything is spent

Every row but the biped promises clips written by the agent, and a body
plan no Unity AI rig covers (a crab, a sprawling lizard) a rig too. Before
the first quote, find the lane that will do it:

- **Blender:** `blender --version` answers (or the user names the
  executable). Headless runs (`blender -b -P script.py -- <args>`) need no
  window.
- **The Unity Editor:** reachable through the `unity-cli` skill (SKILL.md,
  Bringing the result into a Unity project).

When neither is available, say so in the plan: the result stops at the rig
plus its preset clip (quadruped, aquatic), or at a rig that does not move
at all (serpentine, hexapod, octopod, avian: no working preset), and the user
decides whether that is still worth the credits; offer to drop such a rig
before it is quoted.

## 3. The mesh

When the user already has the creature as a GLB or FBX, that file is the
mesh: skip this step and go to step 4 or step 7 with it, checking it as
SKILL.md checks any upload. Generate a mesh only when the user needs one.

A new mesh is worth generating for every creature, as SKILL.md's "Text to 3D
goes through one image" says: one approved concept image from the table's
recommended image model, then `model3d-tripo-p2` once on the image approved
last (`--in <approved.png> --in-param reference_image`). Two things differ
for a creature that will be rigged:

- **The view is three-quarter, not the front view SKILL.md asks for**, so
  every limb shows in the one image (a front view hides a horse's back legs).
  Name the camera's height in the prompt: "three-quarter view from the front,
  the camera low, about 20 degrees above the ground, not from above". "From
  slightly above" drew a spider almost from the top, and a top view becomes
  the mesh's front (SKILL.md, the concept's view becomes the model's
  orientation). A fish is the exception: its row asks for a side view, the
  view the aquatic rig was measured on, so the mesh comes back with its side
  as its front, turned 90° about the vertical. Say so in the plan and turn it
  back 90° on import (step 7), never by asking for a front-view fish.
- **The pose for the body plan**, every limb separate: limbs that touch are
  rebuilt as one lump of mesh that no rigger can split.

| Body plan | Pose in the prompt | `--views silhouette` passes when |
|---|---|---|
| Four legs | standing square on all four legs, legs straight, vertical and slightly apart so none overlap, head level, tail held out behind | some row cuts 4 pieces (every leg on its own) |
| Six or eight legs | all the legs spread evenly out from the body, apart so none cross or touch, the body raised off the ground | some row cuts at least 6, or 8, pieces |
| Wings | standing upright on both legs, wings spread fully open to the sides, tail fanned | `span` 1.2 or more |
| No legs | lying stretched out in one gentle S curve, no part touching another, head slightly raised | `span` 2.0 or more |
| Fins | side view, body straight, fins and tail spread | `span` 1.2 or more |

Check the concept with `unity ai preview "<concept.png>" --png --views
silhouette` before the mesh is quoted (it needs the transparent background,
`--param background=transparent` on the image model); a concept that misses
is regenerated as `-v2`, never reconstructed. In the 2026-10-26 run these
numbers told every conforming concept from its natural control (a tucked
spider: 5 pieces at most; a coiled snake: `span` 1.3). The mesh keeps the
concept's pose: look at its turntable before the rig is quoted.

SKILL.md's rule against loose accessories applies to held or separate
things (a web, prey, a perch, a rider: each its own asset); a tail, fins and
wings are body and stay. Pass `--param face_limit=20000` (`model3d-tripo-p2`
takes 48 to 50000; the riggers' schemas state no face cap): a dense mesh
slows every later step, local rigging included.

## 4. The local route (no Unity AI rig)

For a body no Unity AI rig covers, and whenever a paid rig fails step 6,
the agent rigs,
skins and animates the mesh itself, free, in the lane step 2 found. This is
the path that works for these bodies today. Set the expectation in one
line: keyframed loops that read well at game distance, editable afterwards,
not motion capture. Ask which clips the game needs (walk, idle, turn,
attack, hit, death) before writing any.

**In Blender** (`bpy`, headless), what worked on a spider mesh from
`model3d-tripo-p2` (eight legs, abdomen, head with fangs). The sizes below
are fractions of the body's width in the top view (`W`, the body's extent
across the leg ring), so they hold at any mesh scale:

1. Weld the mesh first (`bmesh.ops.remove_doubles`, distance 1e-5): generated
   meshes are split at UV seams, and automatic weights fail on them ("Bone
   Heat Weighting: failed to find solution").
2. Find the body as what survives a morphological opening of the top-view
   silhouette (legs are thin, the body is not; a grid of about 3% of `W`,
   opened by about 4 cells), and the legs as the connected pieces of the mesh outside it.
   Radial sampling around the body centre misassigns curved legs and parts
   of the body; a 3D opening of the filled mesh loses a hollow abdomen.
3. Trace each leg's chain from where it touches the body to its tip (four to
   five bones following the leg), parented to a body bone. Tell head from
   abdomen by the leg attachments: the abdomen is the body mass away from
   them.
4. Skin with automatic weights (`parent_set(type='ARMATURE_AUTO')`), then
   pin every vertex inside the body silhouette and more than about 10% of
   `W` from a leg line to the body bones only: bone heat lets a front leg's first bone
   reach into the head and fangs.
5. Write each clip as an action, push each to its own NLA track, and export
   to a new file (`export_nla_strips=True`), never over the generated one:
   its sidecar describes that file. Export GLB, not FBX: Blender's FBX
   export dropped the generated mesh's textures (the spider imported white
   in Unity), while the GLB kept them. When the rig came from Tripo and
   Blender only adds clips, the Blender GLB carries the mesh, the rig and
   every clip: it replaces the Tripo file as the model in the project.

It took several iterations to get there; check each one with step 6 rather
than by eye, and show the user the rig with the legs colour-coded by bone
before writing clips.

**In the Unity Editor**, through the `unity-cli` skill: the same steps in C#
(bones as Transforms, a `SkinnedMeshRenderer` with bind poses), with no
automatic weights to lean on: weight each leg vertex by its distance to
that leg's bone segments, falling off over about a leg's thickness, and
pin the body vertices to the body bones as item 4 says. Then clips as step
5 says.

## 5. Writing clips on a rig

**Read the skeleton first.** Get the bone names and hierarchy from the file:
the glTF's `nodes` and `skins` (a few lines of Python), a Transform walk in
the Editor, or `bpy`. The preview's Skeleton toggle (key B) draws bone lines
and a count, without names or hierarchy, so it cannot map chains. Tripo
names some chains (`Spine_*`, `Head_*`, `Tail_*`, `0_Left_Limb_*`) and
leaves the rest as generic `bone_N`, different on every run. Map each limb
to its chain; when the chains do not match the planned limbs one to one,
stop before writing any clip and show the user the tree.

**Clips in the Editor** (C#):

- Import the model first (step 7) and write curves against it: each
  binding's `path` is `AnimationUtility.CalculateTransformPath(bone,
  animatorRoot)`.
- Rotation curves come as a complete set per bone: all four
  `m_LocalRotation.x/y/z/w`, or all three `localEulerAnglesRaw.x/y/z`. A
  partial set gives wrong or no motion with no error.
- Each key is the bone's bind-pose `localRotation` times the offset for that
  frame, never the offset alone.
- Looping is set through `AnimationUtility.GetAnimationClipSettings` /
  `SetAnimationClipSettings` (`loopTime`); `AnimationClip` has no settable
  `loopTime`.
- Save under `Assets/` next to the model, after checking
  `AssetDatabase.LoadAssetAtPath` for an existing clip of that name (pick a
  new name or ask, never overwrite). Then check that every
  `AnimationUtility.GetCurveBindings` path resolves on the model.
- Look at each clip yourself before the next, in the Editor without Play
  mode: `clip.SampleAnimation` on an instance created with
  `HideFlags.HideAndDontSave` and destroyed afterwards, measuring how far
  each leg tip (for a snake or a fish, each chain) travels relative to the
  bone it hangs from and how far the lowest vertex goes under the ground. The
  preview reads only clips inside a GLB, glTF or FBX, never a separate
  `.anim`, so `unity ai preview "<file>" --png --views poses,feet` checks a
  clip only once it is exported with the rig (every leg moves:
  `details.motion.legsMoving` against `legs`, or for a snake or a fish some
  chain: `limbsMoving`; `legs` null on a legged creature means no leg was
  found, so look at `poses`; `belowGround` under 0.05). Play mode runs the user's own game scripts:
  enter it only after the user agrees.

**Gaits to start from**, as phase offsets within one loop (0 to 1), legs
numbered front to back, with the share of the loop each foot is on the
ground (the duty factor):

- Eight legs: alternating tetrapod, L1, R2, L3, R4 at 0 and R1, L2, R3, L4 at 0.5; duty about 0.65.
- Six legs: alternating tripod, L1, R2, L3 at 0 and R1, L2, R3 at 0.5; duty about 0.65.
- Four legs, walk: left hind 0, left fore 0.25, right hind 0.5, right fore 0.75; duty about 0.75 so three feet stay down. Trot: diagonals at 0 and 0.5, duty about 0.5.
- No legs: a travelling sine wave of side-to-side rotation down the spine, about one and a half wavelengths over the body, phase increasing toward the tail.
- Fish: the same wave, amplitude growing toward the tail, the front third nearly still.

During the stance a foot moves back along the ground; during the swing it
lifts and comes forward. On the quadruped rig keep head turns small (its
head bones carry part of the shoulders).

## 6. Check a rig before building on it (free)

A rig, paid or local, is judged from the file before any clip is built on
it, and the result is said to the user:

- **Each limb owns its skin**: `unity ai preview "<rig.glb>" --png --views
  rig` bends each limb on its own and colours the mesh by the limb that
  moves it (ten colours: past ten limbs they repeat, so a spider with
  pedipalps is judged on `details.rig.limbList`, not the colours). A limb in `details.rig.over` (its bend moves over 40% of the
  mesh) is skin bleeding into the body, the head aside (`headLimb` names
  the limb taken for it on a rig with generic bone names), `unskinned` a
  limb that moves nothing, and `legs` under the animal's
  count legs fused or folded at rest. A local rig (no Unity AI file yet) is
  checked the same way once exported to GLB. A snake or a fish has no legs:
  its limbs are halves of the spine (and fins), so `legs` counts chains that
  lie on the floor and `over` and `maxLimbShare` are large on a clean rig
  (88% on the snake here); judge only `unskinned` on those.
- **The clip moves what it should**: `--views poses,feet` on a file with a
  clip; `details.motion.legsMoving` against `legs` (on a snake or a fish,
  `limbsMoving` at least 1 instead), and `belowGround` under 0.05. A preset that fails here is dropped, and its clip written locally
  on the same rig.

When a paid rig fails, switch to the local route with the mesh you already
have. Do not re-run the rig hoping for a better skeleton: it changes from
run to run, each run is charged, and the earlier charges stand. A rig that
fails from a natural-pose concept is better fixed at the concept (step 3),
with its own quote. The one
re-rig worth quoting is a wrong `rig_type` (a quadruped rigged as hexapod).
SKILL.md's generic rig Edit (`auto_rig`, `output_format`) does not apply to
this rigger. A redo of an earlier step (a better concept image, a new mesh)
gets its own quote and consent like any step.

## 7. The paid rig and the import

Run it as SKILL.md's Running `generate` says: `--format ndjson`, stdout
and stderr in logs where that section puts them (next to `--out`, or under
`Logs/unity-ai/` when `--out` is under a project's `Assets/`), never piped
through a filter, and its own exit code acted on.

```
# bash; PowerShell form, the <consent> flag and the <log> / <err log> paths in SKILL.md, Running `generate`
unity ai generate --model model3d-tripo-rigging-v2-5 \
  --in <mesh.glb> --in-param reference_model \
  --param rig_type=<type from the step 1 table> --param animation=<its preset> \
  --param targetFormat=glb --out <path>.glb --format ndjson <consent> \
  --billed-to <payer from the accepted quote> > <log> 2> <err log>
```

- With `animation` set, the one file returned carries the rig and the
  clip. Do not pass `include_rigged_model=true`: the file then comes back
  without the clip. Leave `animation` unset for every row step 1 marks rig
  only, and for serpentine.
- `targetFormat` is `glb` or `fbx` (default `glb`). A GLB needs glTFast in a
  Unity project and an FBX imports without its metal (SKILL.md, Bringing the
  result into a Unity project).
- A Tripo rig returns no `partnerResultId` and is never a Uthana retarget
  target.

In the Editor the rigged file is the model, and the import depends on its
format:

- **GLB** (glTFast): no Rig tab and no avatar to set. The importer brings
  the clips in as Mecanim clips and puts an Animator on the model; clips
  bind by transform path.
- **FBX** (Unity's model importer): Rig tab, Animation Type **Generic**,
  Avatar Definition **Create From This Model** (a Humanoid avatar needs a
  biped bone mapping and cannot be configured on such a skeleton), **Root
  node** set to the root bone, and the looping clips marked Loop Time. From
  C#: `ModelImporter.animationType`, `avatarSetup`, `motionNodeName`, and
  `clipAnimations` copied from `defaultClipAnimations` with `loopTime` set,
  then `SaveAndReimport`. A reimport can outlast a 30 s command timeout;
  read the settings back afterwards rather than trusting the call.
- **A fish** (either format), drawn from the side in step 3, comes back with
  its side as its front: rotate the model's root in the prefab (or the
  instance's parent) 90° about Y so the head points along +Z, and check it
  in the Scene view, the head on the blue axis, before wiring the Animator.

Either way, choose **Apply Root Motion** on the Animator explicitly: the
preset walk travels in place, so leave it off unless the game moves the
creature from the clip. Clips added in Blender come back inside the Blender
GLB, which becomes the model (step 4); its bone paths can differ from the
Tripo file's (Blender may add an armature node), so a controller built on
the old file is rebuilt on the new one. Only a clip that arrives as a
separate FBX, on an FBX model, imports as a clip source with Avatar
Definition **Copy From Other Avatar** pointing at the model's avatar. Either
way, check that every curve's path resolves on the model before wiring it.
Then, through the `unity-cli`
skill: an Animator Controller with one state per clip, the parameters the
game drives (a `Speed` float for idle and walk, an `Attack` trigger), the
transitions, and the controller on the creature's Animator.

## Plan to propose

For "a <creature> that walks / attacks / idles", before the first quote:

1. The body plan and its row (step 1), with what Unity AI will and will not
   do for it, and the lane that will write the clips (step 2).
2. The user's own GLB or FBX when they have one; otherwise a concept image
   in the body plan's pose (step 3), its silhouette checked, then approved.
3. Only without the user's mesh: `model3d-tripo-p2` with `face_limit=20000`.
4. `model3d-tripo-rigging-v2-5` with the row's `rig_type`: with its preset
   clip for four legs and fins, rig only for the others; then the check of
   step 6. A body no Unity AI rig covers: the local route (step 4).
5. The clips the user named, written by the agent (free), each shown.
6. The import and the Animator Controller (step 7), when the user wants the
   creature in their project.
7. Report every path and cost, and which clips are generated and which are
   hand-written.
