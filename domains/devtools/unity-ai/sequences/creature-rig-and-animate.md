# Sequence: rig and animate a creature that is not a biped

A user who said not to ask (SKILL.md, When the user says not to ask): every question
this file has you ask, but money, is your own call; say what you chose in the final reply.

A spider, a dog, a horse, an insect, a bird, a snake or a fish gets no
Uthana motion: every Uthana model is biped only (the model table in `models.md`).
`model3d-rodin-hyper3d-rigging` is the creature rigger: a skeleton template
for four legs, for wings, for a winged dragon and for an upright tailed
monster, the automatic one for fins, and one built from a description of the
body for six or eight legs and snakes (step 1). `model3d-meshy-rigging`
is a character rigger (its `height_meters` is a person's height, and it scales
the result to it, 1.7 m by default) that has not been checked on creatures: do
not offer it for one. It returns the rig in a still pose (a single-keyframe
clip), never a motion. Read this before
proposing the plan: a rig that does not hold up spends credits and leaves
the user with a model that deforms badly, when the agent could have rigged
it itself.

## 1. Decide the body plan, then route

Name the creature's body plan before any quote and take its row. The
templates and stock clips are the `bone_template` and `animations` enums of
`models show model3d-rodin-hyper3d-rigging`; read them there before the quote.

Every row assumes the mesh came from a concept in the row's pose (step 3):
the rows below were measured that way, and a creature drawn in a natural
pose (mid-stride, legs tucked, coiled, wings folded) rigged worse in every
body plan that was compared.

| Body plan | Examples | Unity AI rig | Stock clip | Then |
|---|---|---|---|---|
| Biped | person, robot, goblin, upright animal | `uthana-character-rig` (`rig-and-retarget.md`), or `model3d-tripo-rigging-v1` | Uthana text or video to motion; or a v1 preset (`biped:idle`, `walk`, `run`, `dive`, `climb`, `jump`, `slash`, `shoot`, `hurt`, `fall`, `turn`) | as `rig-and-retarget.md` says |
| Four legs, upright gait | dog, wolf, cat, horse | `bone_template=quadruped` | **none**: `canine_000025` walks, but stretches the hind quarters (step 1) | every clip by the agent (steps 4 and 5) |
| Wings | bird, bat | `bone_template=bird` | **none checked** (`bird_` ids) | every clip by the agent |
| Dragon: four legs and wings | western dragon, wyvern with legs | `bone_template=dragon` | none checked | every clip by the agent |
| Upright monster with a tail | upright tailed monster, lizard-man | `bone_template=kaiju` | none checked | every clip by the agent |
| Fins | fish, eel, shark | `bone_template=auto` | **none checked** (`fish_` ids) | every clip by the agent |
| No legs, on land | snake, worm | `bone_template=custom`, `skeleton_description` "a snake: one spine chain from head to tail tip, no limbs" | none | every clip by the agent |
| Six legs, eight legs | beetle, ant, spider, scorpion | `bone_template=custom`, `skeleton_description` naming the legs, e.g. "a beetle with six legs, two antennae and mandibles" | none | every clip by the agent |

Every row passes the concept image the mesh was made from as
`reference_image`: the rigger rebuilds the textures from it and drops the
mesh's own. Edge cases: a lizard sprawls (legs out to the side), so a
quadruped gait reads as wrong even on a good rig; a crab walks sideways with
claws, which no template covers: both get a local rig (step 4), with the gait
written for them.

Why the rows are what they are (2026-11-13, through Scenario directly: the
rigging theme's six conforming concepts, a `model3d-tripo-p2` mesh from each
at 20,000 faces, each rigged by Rodin and by the deprecated Tripo Rigging 2.5, judged with `unity ai preview --png --views rig,poses,feet`; the
asset-quality COMPARE.md):

- Rodin skins every limb to itself: the worst limb moves 14% (wolf), 15%
  (beetle, hawk), 20% (spider) and 21% (fish) of the mesh, with no unskinned
  bone, and the snake comes back as one spine chain. Tripo 2.5 on the same
  meshes left 24 bones unskinned on the wolf and 3 on the beetle, let one
  beetle limb move 39% of the mesh, and split the snake's spine 77/23.
- Its skeletons are small and named (33 bones on the wolf and the hawk:
  `Neck`, `LeftShoulder`, `RightUpLeg`, `Tail1`), so clips map to chains
  without guessing.
- The stock clips are numbered, not named. Of the 35 `canine_` and six `leanhooved_` clips baked on the wolf and read with `--views poses,feet`, `canine_000025` is a forward walk (2 s, all four legs moving, foot slide at most 0.16 m/s, travelling about 0.6 of the body's size, so it plays with root motion or drifts); `canine_000021` walks a few steps then lies down, `canine_000011` is a play bow, `canine_000029` sits and stands, `canine_000001` is a standing idle. Baked on the wolf through the CLI on dev (2026-11-16), it walks, but on most frames a sheet of mesh stretches between the hind legs and the tail: the skin holds when one limb bends at a time (the rig view) and tears in a full stride. So no stock clip is offered; a clip written for the rig is checked with `--views poses` for the same stretching.
- A template rig repeats: five quadruped runs on the same wolf returned the same 33 bones, names and order, so a clip baked on one run plays on another. A `custom` rig does not: two beetle runs returned 37 and 27 bones with different names, so rig once and write every clip on that rig.
- `dragon` on a four-legged winged dragon skins four legs, two wings, a tail and the neck apart (worst limb 10%); `kaiju` on an upright tailed monster skins two legs, two arms, a tail and the neck (worst 19%, the tail's skin reaching the front of the hips).
- `bone_template=custom` with a fish description failed at the provider
  (charged 60 units); `auto` on the same mesh rigged it. The snake, beetle
  and spider rigged with `custom`.
- The rigged model is about centred on its origin, 45% to 65% of its height
  below y = 0 (a negative `groundGap` in the preview; the same in a Unity
  6000.3 import through glTFast, where every bone and the baked clips' curves
  resolved): lift it on import (step 7).

So a row is quoted as a rig, never "to try a stock clip". A template that `models show` lists and this table does not is treated as a local rig (step 4) until it has been checked the way step 6 describes. A
creature between two plans (a centaur, a dragon that walks and flies) gets
the row of the body the user most wants animated, said in the plan.

## 2. Check that a lane exists before anything is spent

Every row but the biped promises clips written by the agent, and a body
plan no Unity AI rig covers (a crab, a sprawling lizard) a rig too. Before
the first quote, find the lane that will do it:

- **Blender:** `blender --version` answers (or the user names the
  executable). Headless runs (`blender -b -P script.py -- <args>`) need no
  window.
- **The Unity Editor:** reachable through the `unity-cli` skill (SKILL.md,
  Bringing the result into a Unity project).

When neither is available, say so in the plan: the result stops at a rig
that does not move, and the user
decides whether that is still worth the credits; offer to drop such a rig
before it is quoted.

## 3. The mesh

When the user already has the creature as a GLB or FBX, that file is the
mesh: skip this step and go to step 4 or step 7 with it, checking it as
SKILL.md checks any upload. Generate a mesh only when the user needs one.
Rodin takes a GLB only: an FBX (or OBJ, STL) is converted to GLB first in
the step 2 lane (Blender's glTF export), or goes to the local route (step 4),
and never reaches Rodin as is. The Rodin rig still needs a `reference_image` beside it: ask for the concept
the model was made from, or an image of the creature in the same pose and
colours. With none, offer to make one (an image edit of the model's preview
`view` PNG, its own quote) or the local route (step 4); say that Rodin
rebuilds the textures from that image, so a mismatched one repaints the
model.

A new mesh is worth generating for every creature, as "Text to 3D
goes through one image" in `models.md` says: one approved concept image from the table's
recommended image model, then `model3d-tripo-p2` once on the image approved
last (`--in <approved.png> --in-param reference_image`). Two things differ
for a creature that will be rigged:

- **The view is three-quarter, not the front view `models.md` asks for** (Text to 3D goes through one image), so
  every limb shows in the one image (a front view hides a horse's back legs).
  Name the camera's height in the prompt: "three-quarter view from the front,
  the camera low, about 20 degrees above the ground, not from above". "From
  slightly above" drew a spider almost from the top, and a top view becomes
  the mesh's front (`models.md`, the concept's view becomes the model's
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
| Dragon (four legs and wings) | standing square on all four legs, legs apart, wings spread fully open to the sides, tail held out behind, three-quarter view from the front, the camera low | `feet` 4 and `span` 1.2 or more (the bench dragon: 4, 1.23) |
| Upright monster with a tail | standing on two thick legs apart, the tail resting behind, arms held out from the body, front three-quarter view | `feet` 3 or more when the tail rests on the ground (two legs and the tail tip) and `legsApart` 1 (the bench monster: 3 and 1; no natural-pose control measured yet) |

Describe an original creature in the image prompt (its body, tail, skin and
colours), never a franchise or genre name: GPT Image 2.5 refused "a giant
kaiju monster" at its output filter after the call was made, and an
original "stone-skinned lava monster" in the same pose went through.

Check the concept with `unity ai preview "<concept.png>" --png --views
silhouette` before the mesh is quoted (it needs the transparent background,
`--param background=transparent` on the image model); a concept that misses
is regenerated as `-v2`, never reconstructed. In the 2026-10-26 run these
numbers told every conforming concept from its natural control (a tucked
spider: 5 pieces at most; a coiled snake: `span` 1.3). The mesh keeps the
concept's pose: look at its turntable before the rig is quoted.

The rule against loose accessories in `models.md` applies to held or separate
things (a web, prey, a perch, a rider: each its own asset); a tail, fins and
wings are body and stay. Pass `--param face_limit=20000` (`model3d-tripo-p2`
takes 48 to 50000; the rigger takes files up to 100 MB): a dense mesh
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
   its sidecar describes that file. Give the export its own with `unity ai
   sidecar derive <new>.glb --from <generated>.glb --edit blender-export
   --detail "<clips added>"`. Export GLB, not FBX: Blender's FBX
   export dropped the generated mesh's textures (the spider imported white
   in Unity), while the GLB kept them. When the rig came from Rodin and
   Blender only adds clips, the Blender GLB carries the mesh, the rig and
   every clip: it replaces the Rodin file as the model in the project.

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
and a count, without names or hierarchy, so it cannot map chains. Rodin's
templates name their chains (`Neck`, `LeftShoulder`, `RightUpLeg`, `Tail1`);
a custom skeleton's names follow the description. Map each limb
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
lifts and comes forward. Keep head turns small until the rig view shows
the neck's skin stops at the shoulders.

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
  lie on the floor; judge only `unskinned` on those (Rodin's snake is one
  chain, so it reports one limb and no share).
- **The clip moves what it should**: `--views poses,feet` on a file with a
  clip; `details.motion.legsMoving` against `legs` (on a snake or a fish,
  `limbsMoving` at least 1 instead), and `belowGround` under 0.05. A stock clip that fails here is dropped, and its clip written locally
  on the same rig.

When a paid rig fails, switch to the local route with the mesh you already
have. Do not re-run the rig hoping for a better skeleton: each run is
charged, and the earlier charges stand. A rig that fails from a natural-pose
concept is better fixed at the concept (step 3), with its own quote. The
re-rigs worth quoting are a wrong `bone_template` (a quadruped rigged as a
bird) and a `custom` rig the provider rejected, re-run with `auto`.
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
unity ai generate --model model3d-rodin-hyper3d-rigging \
  --in <mesh.glb> --in-param reference_model \
  --in <concept.png> --in-param reference_image \
  --param bone_template=<template from the step 1 table> \
  [--param skeleton_description="<the body, with custom only>"] \
  --out <path>.glb --format ndjson <consent> \
  --billed-to <payer from the accepted quote> > <log> 2> <err log>
```

- The file is a GLB with the rig and any `animations` baked in, one clip each. Leave `animations` unset unless the user asks to try a stock clip; check any with step 6 (and `--views poses` for stretched skin) before it is used.
- `material` is `PBR` (default) or `Shaded`; the textures come from
  `reference_image`, never from the mesh.
- A Rodin rig returns no `partnerResultId` and is never a Uthana retarget
  target.

In the Editor the rigged file is the model, and the import depends on its
format:

- **Lift it to the ground first**: the rigged model's feet sit below its
  origin (step 1). Instantiate it, read the lowest point of its
  `SkinnedMeshRenderer` bounds (`bounds.min.y`, negative), and move a parent
  of the model up by that much so the feet rest on y = 0.
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

Either way, choose **Apply Root Motion** on the Animator explicitly: clips written in place leave it off unless the game moves the creature
from the clip. Clips added in Blender come back inside the Blender
GLB, which becomes the model (step 4); its bone paths can differ from the
Rodin file's (Blender may add an armature node), so a controller built on
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
2. The user's own GLB or FBX when they have one (an FBX converted to GLB),
   with an image of the creature for Rodin's `reference_image` (step 3); otherwise a concept image
   in the body plan's pose (step 3), its silhouette checked, then approved.
3. Only without the user's mesh: `model3d-tripo-p2` with `face_limit=20000`.
4. `model3d-rodin-hyper3d-rigging` with the row's `bone_template` (and
   `skeleton_description` for `custom`), the approved concept as
   `reference_image`, rig only; then the check of step 6. A body no Unity AI
   rig covers: the local route (step 4).
5. The clips the user named, written by the agent (free), each shown.
6. The import and the Animator Controller (step 7), when the user wants the
   creature in their project.
7. Report every path and cost, and which clips are generated and which are
   hand-written.
