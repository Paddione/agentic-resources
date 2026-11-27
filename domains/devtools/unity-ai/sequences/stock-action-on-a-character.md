# Sequence: a stock action on a character with Meshy Animation

A user who said not to ask (SKILL.md, When the user says not to ask): every question
this file has you ask, but money, is your own call; say what you chose in the final reply.

`model3d-meshy-animation` takes a 3D character mesh and an action chosen
from a stock library, rigs the mesh and retargets that action onto it, in
**one paid call**. What comes back is a model carrying real motion, not a
still pose. Biped characters only: a creature that is not a biped follows
`creature-rig-and-animate.md`, and a motion written to the user's own
description follows `rig-and-retarget.md`.

Read this before proposing the plan. Three settings decide whether the
result is usable in Unity and what a library of actions costs, and the
defaults are wrong for a Unity project on the first and leave money on the
table on the other two.

## 1. When this is the route

It is the cheapest way to get a character moving, and the only one that
charges once:

| Ask | Route | Paid calls |
|---|---|---|
| A biped doing a move the stock library already has (walk, run, idle, attack, climb, dance) | this file | 1 |
| A biped doing a move described by the user, or taken from their own clip | `rig-and-retarget.md` (rig, then motion on that rig) | 2 |
| A character rigged now, animated later, or rigged for the user's own clips | `uthana-character-rig` (`rig-and-retarget.md`) or `model3d-tripo-rigging-v1` | 1 |
| A creature that is not a biped | `creature-rig-and-animate.md` | 1 plus clips written by the agent |

So: when the move the user describes is in the step 5 table, offer this
route first and say what it costs against the alternative. When it is not
in the table, look it up in the full library before ruling this route out:
the table is 80 of 656 actions, and the published page (step 5) has the
rest. `rig-and-retarget.md` is the route only when the library has nothing
that fits, or the user has a reference clip. Do not try to approximate a described
move with a stock action without saying that is what you are doing and
showing the user the action you picked.

The rig it produces is not a retarget target: `uthana-retarget` does not
accept it, the same as `model3d-meshy-rigging`.

## 2. Pass `skeleton_template=unity_humanoid`

**Always, for a model headed for a Unity project, unless the user asks
otherwise.** It costs nothing extra and it is the difference between a rig
Unity maps by itself and one a person maps by hand.

| | `meshyrig` (the default) | `unity_humanoid` |
|---|---|---|
| Joints | 24 | 66 with `include_fingers` (40 of them finger bones) |
| Fingers | none (see step 3) | none until `include_fingers` |
| Bone names | `Spine02`, `neck`, `LeftForeArm`: the Humanoid mapper has to guess at them | `Chest`, `UpperChest`, `LeftUpperArm`: Unity's own vocabulary, so Configure maps them |
| Armature root scale | `0.01`, which has to be undone in the project | none |
| Price | the same | the same |

There is no cost. Every skeleton names the clip after the action, the way
the default always has (`Armature|Casual_Walk|baselayer` for action 30), so
the file says which `action_id` it carries whatever template was asked for.
Meshy changed this on their side on 2026-11-17; before that `unity_humanoid`
returned every clip as `retarget_clip`, and advice written against that is
out of date.

- The token in the clip name is the action's **library key**
  (`Casual_Walk`), not its display name ("Casual Walk"). The key is the
  form the table in step 5 lists.
- Name each output file after the action anyway (`casual-walk.glb`). It is
  what makes a folder of actions readable, and the clip keeps its own name
  regardless: the CLI only names a clip that arrived without one.

Other templates in the enum (`mixamo`, `ue5_mannequin`, `blender_rigify_basic_human`
and the rest) exist for other tools; pick one only when the user names the
tool the character is going to.

**The one failure this setting has its own retry for**: some characters can
only be rigged on the default `meshyrig` and fail on every other template.
So when a job fails on `unity_humanoid` with fingers already off, and the
failure was released (`jobStatus: "Failed"` with `pointsCost: 0`, step 3),
re-run once without `skeleton_template` before calling the character
unriggable, and say the bones will need mapping by hand.

## 3. Fingers are free: `include_fingers=true`

It adds 40 finger bones (all five digits) at no extra charge, and a Unity
Humanoid avatar maps them. Offer it for any character whose hands are seen (a first-person
or third-person player, anything holding a weapon), and for anything that
gestures.

The catch: biped only, and **some characters can only be rigged without
fingers, in which case the whole job fails** rather than falling back. A
failed job may still be charged, so for a character whose hands are
low-poly, mitten-shaped or fused, say that before the quote and let the
user choose.

If a job fails with fingers on, read whether it was charged before saying
anything about credits, as SKILL.md's error handling sets out: an error
event carrying `jobStatus: "Failed"` with `pointsCost: 0` was released and
not charged, and the request may run again. Only that marker says so. On a
released failure, re-run once with `include_fingers` off before concluding
anything else is wrong; without it, treat the charge as standing, check
`unity ai credits`, and let the user decide whether to spend again.

## 4. Many actions on one character: `extract_armature` **with** `targetFormat=glb`

`extract_armature` returns the animation on its own: a file holding the
skeleton and the clip, with no mesh and no textures. About 70 KB as GLB
against about 10 MB for the whole character, **at the same price**.

**Always pass `--param targetFormat=glb` with it.** The two go together and
neither is optional. `extract_armature` on its own returns FBX, because that
is what the provider produces and the format is only converted when the call
asks for one. The model's stated default does not apply itself: a format
that is not asked for is not converted. Measured on the same action and the
same character:

| | File |
|---|---|
| `extract_armature`, no `targetFormat` | FBX, 223,724 bytes |
| `extract_armature` and `targetFormat=glb` | GLB, 69,608 bytes |

Three times the size for a parameter left off, on the one call whose whole
point is size. The same holds for the full first file, where GLB is also the
default this file assumes.

Past that, an action library is affordable in size, not in credits: every
call is charged whether or not the mesh comes back, so a library of N
actions is N charges either way. What it saves is N copies of the same
character on disk and in the project.

The pattern for a character that needs several actions:

1. The **first** action without `extract_armature`, with
   `targetFormat=glb`: that file carries the character, its textures and
   its rig.
2. **Every action after it** with
   `post_process_operation=extract_armature --param targetFormat=glb`:
   clip only, about 70 KB.
3. In the project, the first file is the model; each later clip plays on it.
   The bones must line up, so every call uses the same
   `skeleton_template` and the same `include_fingers`. Change either one and
   the clips no longer bind.

Say the plan this way before the first quote: one full file plus N minus
one clip-only files, N charges, and the size of each.

The model has no frame-rate option: `post_process_operation` takes
`extract_armature` or nothing. Change a clip's frame rate in the project.

## 5. Choosing the action

Actions are chosen by `action_id`, an integer. The ids are **not
contiguous** and the name is not an input: 656 actions run from id 0 to id
696. The table below is a working subset for game characters, grouped by
the library's own categories. The whole library, with a preview of each
action, is published by the provider at
https://docs.meshy.ai/en/api/animation-library; send the user there when
nothing below fits, and read the id from the page rather than guessing one.

Two things to know before reading the table:

- **In place.** 69 of the actions have a twin that plays the same move
  without travelling, named `<action>_inplace`, and the right-hand column
  gives that twin's id where one exists. An in-place clip is what a
  locomotion state machine wants: the game moves the character and the clip
  only cycles the legs. The travelling version is meant for a one-shot
  played with root motion, but measured clips from this model barely travel
  (`Casual_Walk` moved under 0.3 units over the whole clip), so check the
  clip's path with `--views path` before relying on its root motion. Pick
  the in-place id for anything that loops under player control, and say
  which of the two you picked.
- **The list is a snapshot**, taken on 2026-11-16. Its `sha256` over the
  action list was
  `ba720ef1097a3f19895c33134bdcd1db77df955f47fa69a35a37e1d5afb954ff` (656
  actions). The ids below have no guarantee beyond that: if an action comes
  back as something other than its name here, the library has moved, and the
  published page above is the authority. Scenario intend to expose the list
  through the service later, at which point this table gives way to it.

**Idle, look and react**

| `action_id` | Action | Category / sub-category | In place |
|---|---|---|---|
| 0 | `Idle` | DailyActions / Idle | - |
| 11 | `Idle_02` | DailyActions / Idle | - |
| 2 | `Alert` | DailyActions / LookingAround | - |
| 36 | `Confused_Scratch` | DailyActions / Idle | - |
| 317 | `Shrug` | DailyActions / Interacting | - |
| 59 | `Victory_Cheer` | BodyMovements / Acting | - |

**Walking**

| `action_id` | Action | Category / sub-category | In place |
|---|---|---|---|
| 30 | `Casual_Walk` | WalkAndRun / Walking | 613 |
| 1 | `Walking_Woman` | WalkAndRun / Walking | - |
| 106 | `Confident_Walk` | WalkAndRun / Walking | - |
| 115 | `Quick_Walk` | WalkAndRun / Walking | - |
| 559 | `Sneaky_Walk` | WalkAndRun / Walking | 671 |
| 563 | `Stylish_Walk` | WalkAndRun / Walking | 675 |
| 119 | `Slow_Orc_Walk` | WalkAndRun / Walking | 669 |
| 112 | `Monster_Walk` | WalkAndRun / Walking | - |
| 558 | `Limping_Walk` | WalkAndRun / Walking | 645 |
| 111 | `Injured_Walk` | WalkAndRun / Walking | 637 |
| 551 | `Carry_Heavy_Object_Walk` | WalkAndRun / Walking | 611 |
| 560 | `Spear_Walk` | WalkAndRun / Walking | 672 |
| 544 | `Walk_Backward` | WalkAndRun / Walking | 679 |
| 549 | `Crawl_Backward` | WalkAndRun / Walking | 622 |

**Running and crouching**

| `action_id` | Action | Category / sub-category | In place |
|---|---|---|---|
| 16 | `RunFast` | WalkAndRun / Running | - |
| 14 | `Run_02` | WalkAndRun / Running | - |
| 509 | `Lean_Forward_Sprint` | WalkAndRun / Running | 644 |
| 531 | `Sprint_and_Sudden_Stop` | WalkAndRun / Running | - |
| 13 | `Jump_Run` | WalkAndRun / Running | - |
| 524 | `Cautious_Crouch_Walk_Forward` | WalkAndRun / CrouchWalking | 616 |
| 523 | `Cautious_Crouch_Walk_Backward` | WalkAndRun / CrouchWalking | 615 |

**Turning and swimming**

| `action_id` | Action | Category / sub-category | In place |
|---|---|---|---|
| 572 | `Walk_Turn_Left` | WalkAndRun / TurningAround | - |
| 583 | `Walk_Turn_Right` | WalkAndRun / TurningAround | - |
| 576 | `Idle_Turn_Left` | WalkAndRun / TurningAround | - |
| 586 | `Idle_Turn_Right` | WalkAndRun / TurningAround | - |
| 569 | `Swim_Forward` | WalkAndRun / Swimming | - |
| 568 | `Swim_Idle` | WalkAndRun / Swimming | - |

**Jumping, falling, climbing**

| `action_id` | Action | Category / sub-category | In place |
|---|---|---|---|
| 466 | `Regular_Jump` | BodyMovements / Jumping | - |
| 471 | `Jump_Over_Obstacle` | BodyMovements / Jumping | - |
| 463 | `Run_and_Jump` | BodyMovements / Jumping | - |
| 459 | `Run_Jump_and_Roll` | BodyMovements / PerformingStunt | - |
| 452 | `Backflip` | BodyMovements / PerformingStunt | - |
| 429 | `Parkour_Vault` | BodyMovements / VaultingOverObstacle | - |
| 441 | `Climb_Stairs` | BodyMovements / Climbing | - |
| 438 | `Ladder_Climb_Loop` | BodyMovements / Climbing | - |
| 449 | `Climb_Up_Rope` | BodyMovements / Climbing | - |
| 478 | `Bar_Hang_Idle` | BodyMovements / HangingfromLedge | - |
| 502 | `Fall1` | BodyMovements / FallingFreely | - |
| 506 | `Dive_Down_and_Land` | BodyMovements / FallingFreely | - |

**Melee and weapons**

| `action_id` | Action | Category / sub-category | In place |
|---|---|---|---|
| 4 | `Attack` | Fighting / AttackingwithWeapon | - |
| 89 | `Combat_Stance` | Fighting / AttackingwithWeapon | - |
| 97 | `Left_Slash` | Fighting / AttackingwithWeapon | - |
| 240 | `Thrust_Slash` | Fighting / AttackingwithWeapon | - |
| 105 | `Triple_Combo_Attack` | Fighting / AttackingwithWeapon | - |
| 198 | `Punch_Combo` | Fighting / Punching | - |
| 191 | `Left_Jab_from_Guard` | Fighting / Punching | - |
| 207 | `Roundhouse_Kick` | Fighting / Punching | - |
| 224 | `Archery_Shot` | Fighting / AttackingwithWeapon | - |
| 98 | `Run_and_Shoot` | Fighting / AttackingwithWeapon | - |
| 170 | `Standing_Reload` | Fighting / Transitioning | - |

**Defence, damage, death**

| `action_id` | Action | Category / sub-category | In place |
|---|---|---|---|
| 138 | `Block1` | Fighting / Blocking | - |
| 147 | `Sword_Parry` | Fighting / Blocking | - |
| 158 | `Roll_Dodge` | Fighting / Transitioning | - |
| 178 | `Hit_Reaction` | Fighting / GettingHit | - |
| 7 | `BeHit_FlyUp` | Fighting / GettingHit | - |
| 187 | `Knock_Down` | Fighting / Dying | - |
| 8 | `Dead` | Fighting / Dying | - |

**Spellcasting**

| `action_id` | Action | Category / sub-category | In place |
|---|---|---|---|
| 125 | `Charged_Spell_Cast` | Fighting / CastingSpell | - |
| 127 | `Charged_Ground_Slam` | Fighting / CastingSpell | - |

**Interacting and object handling**

| `action_id` | Action | Category / sub-category | In place |
|---|---|---|---|
| 290 | `Wave_One_Hand` | DailyActions / Interacting | - |
| 28 | `Big_Wave_Hello` | DailyActions / Interacting | - |
| 50 | `Phone_Call_Gesture` | DailyActions / Interacting | - |
| 285 | `open_door` | DailyActions / Interacting | - |
| 284 | `Collect_Object` | DailyActions / PickingUpItem | - |
| 276 | `Male_Bend_Over_Pick_Up` | DailyActions / PickingUpItem | - |

**Sitting, standing, sleeping**

| `action_id` | Action | Category / sub-category | In place |
|---|---|---|---|
| 344 | `Stand_Up1` | DailyActions / Transitioning | - |
| 52 | `Sit_to_Stand_Transition_F` | DailyActions / Transitioning | - |
| 57 | `Stand_to_Sit_Transition_M` | DailyActions / Transitioning | - |
| 267 | `Sleep_Normally` | DailyActions / Sleeping | - |

**Dancing and exercise**

| `action_id` | Action | Category / sub-category | In place |
|---|---|---|---|
| 591 | `Hip_Hop_Dance` | Dancing / Dancing | - |
| 596 | `ymca_dance` | Dancing / Dancing | - |
| 64 | `All_Night_Dance` | Dancing / Dancing | - |
| 22 | `FunnyDancing_01` | Dancing / Dancing | - |
| 326 | `jumping_jacks` | DailyActions / WorkingOut | - |

## 6. The quote and the run

One step, so the normal flow: `quote`, the user's consent on that quote,
then `generate`. Run it as SKILL.md's Running `generate` says: `--format
ndjson`, stdout and stderr in logs where that section puts them, never
piped through a filter, and its own exit code acted on.

```
# bash; PowerShell form, the <consent> flag and the <log> / <err log> paths in SKILL.md, Running `generate`
unity ai generate --model model3d-meshy-animation \
  --in <character.glb> --in-param reference_model \
  --param action_id=<id from the step 5 table> \
  --param skeleton_template=unity_humanoid \
  [--param include_fingers=true] \
  [--param height_meters=<n>] \
  [--param post_process_operation=extract_armature] \
  --param targetFormat=glb \
  --out <action-name>.glb --format ndjson <consent> \
  --billed-to <payer from the accepted quote> > <log> 2> <err log>
```

- `reference_model` takes a GLB.
- `height_meters` is the character's height in metres, 1.7 by default, and
  the rig is scaled to it. Set it for anything that is not person-sized (a
  child, a gnome, an ogre) or the proportions come back wrong.
- `targetFormat` is `glb` or `fbx`. **Pass it on every call**: left off, the
  file comes back in whatever the provider produced, which is FBX, and a
  format that is not asked for is not converted (step 4). Ask for `fbx` only
  when the user wants a Humanoid avatar set up on import or to hand-edit the
  rig; step 8 covers both.
- A failed job can still be charged, so do not re-run on a whim: read the
  error first. Steps 2 and 3 cover the failures with a known retry.

## 7. Check the result before building on it (free)

Judge the file, not the thumbnail, and say what you found:

- `unity ai preview "<out>.glb" --png --views rig` colours the mesh by the
  limb that moves it. A limb in `details.rig.over` is skin bleeding into
  the body and `unskinned` a limb that moves nothing.
- `--views poses,feet` on the clip: `belowGround` under 0.05, and
  `details.motion.legsMoving` judged against the action you asked for, as
  the table of numbers in `show-result.md` says. Both legs move on a walk, run, climb or
  jump, and a leg left still there fails (`limbList` names it). An idle, a
  gesture, a seated action or an upper-body move such as a wave, a punch or
  a spell cast moves few legs by design, and that is not a defect; on those,
  judge the clip from `poses`.
- On an `extract_armature` file there is no mesh to colour, so `rig` says
  nothing useful, and the clip means nothing on its own. Draw it on the
  character instead, which is free and comes before any import:
  `unity ai preview "<clip>.glb" --character "<first file>.glb" --png
  --views poses,feet`. `details.onCharacter` says how many of the motion's
  `channels` matched the character's nodes; few or none is a clip that will
  not bind, which is the `skeleton_template` or `include_fingers` drifting
  between calls (step 4). Catch that here rather than in the project.

When the rig fails, the mesh is usually the cause (fused limbs, a natural
pose, arms against the body). Do not re-run the same call hoping for a
better skeleton: each run is charged. A character made for rigging is
generated in an A-pose or T-pose, as the 3D table in `models.md` says
(`--param pose_mode=a-pose`), and a re-generated character gets its own
quote and consent.

## 8. Import into Unity

- **GLB** (glTFast): no Rig tab. The importer brings the clip in as a
  Mecanim clip and puts an Animator on the model. For a Humanoid avatar,
  which is what `unity_humanoid` is for, convert to FBX or set the avatar up
  in the project from the imported hierarchy.
- **FBX** (Unity's model importer): Rig tab, Animation Type **Humanoid**
  with `unity_humanoid` (Configure should map every bone without help, which
  is the point of step 2), or **Generic** on the default template. Mark the
  looping clips Loop Time: a walk, run, idle or in-place cycle loops; a
  one-shot attack, jump or death does not.
- For a library built with `extract_armature`, the clip-only files are
  imported for their animation alone; the first file is the model they play
  on.

## Plan to propose

Before the first quote, one line per step with its model, the charge, and
the two settings that are not defaults, so the user approves the real plan:

```
1. Character  <the mesh you have, or a generation step of its own>
2. Action     model3d-meshy-animation, action_id <id> (<name>),
              skeleton_template=unity_humanoid, include_fingers=<on|off>,
              targetFormat=glb
              <and, from the second action on, post_process_operation=extract_armature>
```

For a library, list the actions by name and id, say it is one charge each,
and say which one is the full character file.
