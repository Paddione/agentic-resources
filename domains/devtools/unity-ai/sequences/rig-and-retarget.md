# Sequence: rig a character and put a generated motion on it

A user who said not to ask (SKILL.md, When the user says not to ask): every question
this file has you ask, but money, is your own call; say what you chose in the final reply.

A rigged character that performs a generated motion takes **two** paid
generations when both are new and the motion comes from text or the user's
clip (acting it out adds the actor still and the take, see
`generated-video-to-motion.md`): rig
the character, then generate the motion
with the rig's id passed as `target_character_id`, and the motion comes back
already on that character. The standalone `uthana-retarget` step is a third
paid generation and is only for a motion that already exists (generated
earlier, or on another character). Read this before proposing the plan; the
ordering rule in step 1 and the two-versus-three distinction are what users
and agents get wrong, and the third job costs credits for nothing.

Every model in this document is for bipeds (a head, a torso, two arms, two
legs). A spider, a quadruped, an insect, a bird, a snake or a fish follows
`creature-rig-and-animate.md` instead.

```
character model (.glb / .fbx)
   │  1. unity ai generate --model uthana-character-rig --in <model> --in-param reference_model
   ▼
rigged character  ── partnerResultId = <character id> ──┐
                                                        │
video or text                                           ▼
   │  2. unity ai generate --model uthana-video-to-motion-3 (or uthana-text-to-motion-3)
   │         --param target_character_id=<character id>
   ▼
motion on the rigged character (.glb or .fbx)   ← done, two generations


Only when the motion already exists (its partnerResultId = <motion id> is known):
   3. unity ai generate --model uthana-retarget --param motion_id=<motion id> --param target_character_id=<character id>
   ▼
retargeted animation (.glb or .fbx)
```

Each step follows the normal flow (model shown to the user, save location,
quote + consent, generate, preview, then the checkpoint of the main skill's
Sequences section: the user looks at the rig in the preview, Skeleton
button, and chooses Use it / Edit / Stop before the motion
step is quoted). Before each checkpoint, look yourself: `unity ai preview
"<file>" --png --views skeleton` for a rig (the joints inside the mesh at the
knees, elbows and hips), `--views poses,path,feet` for a motion (the move asked
for, a walk going straight, every leg moving, nothing under the floor), and read
`details.motion` by the table in `show-result.md`. Lead the checkpoint with what you saw. Every `generate` runs as SKILL.md's Running `generate`
says: `--format ndjson`, stdout and stderr in logs where that section puts
them (next to `--out`, or under `Logs/unity-ai/` when `--out` is under a
project's `Assets/`), never piped through a filter, and its own exit code
acted on. The rules below are what
is specific to this sequence.

A note on what the preview shows for these files: a Uthana rig has its
origin at the hips, so with the preview's Ground grid on (key G) the bind
pose stands half below the plane; a Uthana motion on that rig keys the hips
up by the leg length, so the animated file stands on the plane with no
offset baked into the mesh. Say so when the user asks whether the result
is offset from the ground: the rig alone is, the animation is not, and in
the Unity Editor a Humanoid import with root position Y baked into the pose
handles the rig's offset.

## 1. The rig must be a Uthana rig

`uthana-retarget` retargets onto a character **that Uthana rigged**. It takes
ids, not files: `target_character_id` is the id Uthana assigned when
`uthana-character-rig` processed the model. A character rigged by another
rigging model (`model3d-tripo-rigging-v1`, or a rig that came with the file) has
no such id and cannot be a retarget target, however good the rig is.

So when the plan includes retargeting, rig with `uthana-character-rig`, even if
the character was generated or rigged elsewhere first: that is what gives it a
Uthana character id. If the user wants a Tripo rig AND a retargeted motion,
explain the constraint before spending anything: the motion is retargeted onto
the Uthana character, and the Tripo rig is a separate asset.

**The concept's pose matters little for a biped.** A T-pose or an A-pose,
front view (`models.md`, "Text to 3D goes through one image") keeps the arms
off the body; in the 2026-10-26 run a T-pose, an A-pose and a relaxed
adventurer all rigged cleanly with Uthana, Tripo Rigging 1.0 and Meshy, and
walked alike. A chibi rigged and moved too; its head is half the mesh.

**Tripo Rigging 1.0's presets serve one character.** Each preset
(`--param animation=biped:<name>`) is a paid call that rigs the mesh again,
but calls on the same uploaded mesh return the same skeleton (all 11 presets
on one mesh shared it, and a run clip from its own call played on the walk's
character in Unity), so a set of presets is one character with several
clips: keep the first file as the character and take the clips from the
others. Tripo's creature rigger does not do this (`creature-rig-and-animate.md`).

**Meshy Rigging returns its rig in a still pose** (a single-keyframe clip)
and adds no motion: a rig for clips written locally, never a source of
motion.

**A file that already has a skeleton keeps it**, even with `auto_rig=true`
(a Tripo-rigged, Mixamo or user-rigged file). Every motion on such a character,
and every retarget onto it, stays GLB, the default: its FBX comes back
collapsed (NaN `Root` and `Hip` keys) and is still charged. FBX is fine only on
a character Uthana rigged from an unrigged mesh; when you cannot tell whether
the input had a skeleton, keep GLB. A GLB needs glTFast in a Unity
project (SKILL.md, Bringing the result into a Unity project).

The rig input is `reference_model` (an uploaded asset id): `--in <model.glb>
--in-param reference_model`. Accepted inputs: GLB and FBX. Output format:
`--param output_format=glb|fbx` (default glb).

**Uthana caps the input size** at 30 MiB (Uthana's API documentation).
`models show uthana-character-rig` prints it as `x-max-file-size-mb` on
`reference_model`, and the CLI refuses a larger `--in` file with
`INPUT_TOO_LARGE` before uploading it (nothing uploaded, quoted or charged).
The generate request enforces the same limit before anything is held; a
service that does not check it yet submits the job, and the provider then
fails it with `INPUT_TOO_LARGE` and `the provided file is too large` (the job
failed: with `pointsCost: 0` its hold was released and the request can run
again with a smaller file; without it the job may still be charged, so never
run the same request again: keep the `jobId` and make a new request with a
smaller file). Either way the same file is refused again, so check the file
size BEFORE the quote (the preflight under
Plan to propose), and note that a `quote` proves nothing about the payload:
it prices the job, it does not validate the file.

A generated mesh is usually over that cap when its geometry is dense, not
because of its textures: `model3d-tripo3-1` with a `face_limit` near a million
produces tens of MiB before textures are counted, and lowering
`texture_quality` does not fix it. The exception is
`model3d-hunyuan-3d-pro-3-1` with `enable_pbr=true`: its full-size PNG maps
alone took a measured character to 48 MB (1.3 MB of it mesh), where the
default, without PBR, came to 20 MB. For a Hunyuan character that will be
rigged, leave `enable_pbr` off. Two remedies for dense geometry, by when the
mesh exists:

- **Not generated yet:** cap the face count at generation.
  `model3d-tripo-p2` (the recommended model, see "Text to 3D goes
  through one image" in `models.md`) has `texture_quality` but no `geometry_quality`; its
  density is set with `--param face_limit=<48-50000>`, and 10000 applies
  when it is unset. `model3d-tripo3-1` takes `face_limit` too and also applies
  10000 when it is unset, while a mesh generated with a high limit can still be
  over the cap. A limit in the low tens of thousands keeps a
  character well under the cap, so pass one when the plan ends in a Uthana
  rig, and measure the output before the rig quote.
- **Already generated and over the cap:** `model3d-tripo-retopo` (`--in
  <model> --in-param reference_model --param face_limit=<1000-20000>`)
  rebuilds the topology at a game-ready face count and bakes the textures
  onto it (`bake` is on by default), which takes such a mesh under the cap
  with room to spare (quote it: it costs more than the Uthana rig). It is a normal step of
  this sequence whenever the measured size says so, so the chain for a
  generated character is:

```
concept image → image to 3D (face_limit set) → [retopo when still over the cap] → Uthana rig → motion
```

When the character model comes from elsewhere and is already under the cap,
skip the retopo.

## 2. Ids travel as `partnerResultId`

The Uthana models return, besides the file, an id of their own for the result.
`generate` reports it as `partnerResultId`:

- in the `done` event (`--format json|ndjson`) and on the human `done:` line;
- in the sidecar next to the file (`<out>.unityai.json`, field
  `partnerResultId`), so it survives the session.

Which id it is depends on the model that produced it:

| Produced by | `partnerResultId` is | Feed it to |
|---|---|---|
| `uthana-character-rig` | a character id | `target_character_id` |
| `uthana-video-to-motion-3`, `uthana-text-to-motion-3`, `uthana-retarget` | a motion id | `motion_id` |

Take the ids from the events or the sidecars; never ask the user to hunt for
them, and never guess one. The ids are for the commands, not for the user: in
a plan line, a quote, a consent question or a report, name the asset the way
the user knows it, "the rigged plague doctor (`plague-doctor-rig.glb`)" or
"the walk from step 3", and keep the id out of the sentence. An opaque
string like `cdLorZpQsGPF` in "generate the walk on character cdLorZpQsGPF"
tells the user nothing and reads as a mistake. The ids appear once, in the
final report, next to the file they belong to, for reuse in a later session.
A `done` event without `partnerResultId` has two readings, by model:

- A model that assigns none (Tripo rigs, every non-Uthana model): expected.
  That result cannot be a `target_character_id` or a `motion_id`.
- A Uthana rig or motion model on a plugin build that reports the field: a
  service fault after a paid step. Every Uthana job returns the id on
  success. STOP the sequence there: report the charged step with its
  `jobId`, `assetId`, credits and file path, say the id the next step needs
  did not arrive, and do not run the next step (it would fail or be refused)
  and do not re-run the charged step without the user's consent to a second
  charge. The `jobId` is what support needs.
- A Uthana model on a plugin build too old to report the field: the id was
  never emitted, so it is not recoverable from the file or the sidecar. Stop
  the same way, and say which case it is: the two look identical after the
  charge but mean different things to the user, so do not present a guess as
  a diagnosis. The discriminator is the plugin version (`partnerResultId`
  arrived in 0.1.0-alpha.9), which is why it is checked before the first paid
  step (the preflight under Plan to propose) rather than inferred from a
  missing field afterwards.

Either way the rig FILE is fine and usable outside this sequence: it is a
standard skinned GLB or FBX, so a Humanoid import in the Unity Editor can
retarget any humanoid motion onto it through Mecanim without Unity Credits.
Offer that when the id is missing, instead of re-running the paid rig.

After a charge, a `DOWNLOAD_FAILED` or `WRITE_FAILED` error event carries the
same `partnerResultId` beside `jobId` and `assetId`: the id is usable for the
next step even when the file did not land.

The ids are opaque strings, digits-only ones included: pass them as
`--param motion_id=<id>`; the CLI keeps them as text because the schema
declares them strings. It fetches the model definition first to know that,
and refuses (a coded error before the quote, nothing charged) when the
definition cannot be fetched, rather than guessing: relay that error, do not
retry with a different spelling of the id.

To reuse a character or motion from an earlier session, read the
`partnerResultId` from its sidecar. If a sidecar predates this field (older
plugin), the id is not recoverable from the file: re-run that step (a paid
generation, with consent) or ask the user whether they kept the id.

## 3. The motion step

`uthana-video-to-motion-3` takes the video as a nested object, so the upload flag
needs the dotted key: `--in <clip.mp4> --in-param video_reference.asset_id`.
Video requirements (from the model's schema and help text): 2 to 60 seconds,
24 to 120 fps, 300 to 4096 px, one person, full body visible, stable camera,
plain background, both feet on the ground at the start. A generated video
should be checked against these before it is uploaded; a clip that breaks them
produces a poor motion and still costs credits. The quote is a flat 147 (worst
case 440) whatever the clip's length, but the charge follows it: about 6
credits a second as charged on 2026-11-13 (31 for 5 s), up to 7.2 at the
provider's announced rate (432 for 60 s). For a clip over 20 s, say before
consent that the charge will be above the quote.

Where the motion comes from (text, the user's clip, or acting it out) and
what a rejected text result offers are in `motion-source.md`: the source is
asked once unless the request answers it, and text stays the recommended
answer.

`uthana-text-to-motion-3` takes `--prompt`. Both return a motion on Uthana's
default character; the motion is what carries over, the default character does
not.

`uthana-text-to-motion-3`'s `length` (4 to 10 s) sets both the duration and
the price: 49 credits at 4 s and 122 at 10 s, about 12 credits a
second. Its default, and what it makes when left out, is 4 s. Ask for the
length the game needs and quote with that `length`: the quote follows it (49
at 4 s, 98 at 8 s, 122 at 10 s), so say that figure at consent; the worst case
is the quote plus 20% (59 at 4 s, 147 at 10 s).

Both motion models take `target_character_id` directly: pass the rig's
`partnerResultId` there and the motion comes back on the user's character.
That is the normal path, two generations in all. Step 4 (standalone retarget)
is only for a motion that already exists. Both default to GLB (section 1).

For several motions on one character, generate each with the same
`target_character_id`: every motion file then carries the same rigged mesh,
textures and skeleton, byte for byte, so the motions drive one character in
Unity and each extra motion is only its clip (about 120 KB of a 5.5 MB file).
So once one full motion is saved with the character, generate each further
motion with `--param no_mesh=true` as well: it comes back as the clip
alone, a GLB of about 120 KB with the same joints (names, hierarchy and rest
pose) as the saved character and no mesh or textures, at the same price.
Leave it off for the first motion, which brings the character itself. A
clip-only file plays only on that saved character: in Unity it imports as a
Generic clip, and goes in the character's Animator Controller as a state next
to the first motion's clip. The base is that first motion, not the
`uthana-character-rig` file: imported without an animation, the rig file's
root is its skeleton, so the clips' joint paths find nothing on it. The
preview needs no base: `unity ai preview` draws a clip-only motion on the
rig saved beside it (the glTF or GLB whose `partnerResultId` is the motion's
`target_character_id`), or on the file `--character` names, matching the
clip to the rig's joints by name. A game that loads GLBs at runtime (glTFast) needs
legacy clips there, since a player cannot build Mecanim clips.
`model3d-tripo-rigging-v1` presets behave the same on one input model; a
`model3d-rodin-hyper3d-rigging` or `model3d-meshy-rigging` run rigs the model
again each time, with a different skeleton, so motions from separate runs do
not share a rig. A saved motion's clip is named after its file
(`knight-walk`), since Uthana leaves it unnamed.

## 4. The retarget step (existing motion only)

```
# bash; PowerShell form, the <consent> flag and the <log> / <err log> paths in SKILL.md, Running `generate`
unity ai generate --model uthana-retarget \
  --param motion_id=<motion partnerResultId> \
  --param target_character_id=<rig partnerResultId> \
  --out <path>.glb --format ndjson <consent> \
  --billed-to <payer from the accepted quote> > <log> 2> <err log>
```

Use it when the motion was generated before the rig existed, or to move a
motion onto a second character; when both rig and motion are still to be
generated, pass `target_character_id` to the motion model instead (step 3)
and skip this step. No prompt and no file input: only the two ids (plus
`output_format` glb|fbx, default glb, see section 1 before choosing FBX, and
`no_mesh=true` for the animation alone, delivered as GLB). Run `unity ai
quote` with the same params first, as for any generation. The result itself
carries a motion `partnerResultId`, so a retargeted motion can be retargeted
again onto another character.

## When `unity ai models` does not list the Uthana models

The catalog a CLI sees is scoped per client, and the rig and retarget models
may be missing from `unity ai models` on some deployments while `unity ai
models show uthana-character-rig` and `models show uthana-retarget` still
resolve. Check with `models show <id>` before telling the user a capability
does not exist; if `show` resolves the model, quote it: the catalog listing
and the quote are separate gates, and a model missing from the listing still
quotes and generates. A refused quote is never "not available here": it means
the params failed the model's schema (fix them against `models show`) or the
model is genuinely gone (`show` fails too). Relay the coded error verbatim
and, only when the model is gone, offer the in-engine alternative (a Humanoid
rig in the Unity Editor can retarget any humanoid motion through Mecanim,
without Unity Credits).

Driving an open Editor for that alternative is the `unity-cli` skill's job,
not this one's, and it needs the `com.unity.pipeline` package in the project:
when the user picks that alternative, hand over as the main skill says
(Bringing the result into a Unity project), which says how to read
`unity status` and that the package install is offered and waits for a yes.
That section also says what to tell
the user when a rig or motion saved as FBX goes into a project: it imports
without its metal, and how that is put back at import time.

## Plan to propose

For "a rigged character doing <motion>", propose the plan before the first
quote and let the user trim it, with the cost of each step from `quote`.

**Preflight, before the first quote.** Both checks are free and take seconds;
each failure they catch otherwise shows up after a paid step, with the credits
gone:

- **Plugin build.** Read the version: `unity ai doctor --format json`
  first (its `binary-identity` check carries it; the command exists from
  0.1.0-alpha.8 and its absence, the usage banner on stderr, already says
  the build is older than that), else `unity-ai --version`. The plugin is
  dispatched as a managed copy that is usually not on PATH, so
  `unity-ai` as a bare command may not resolve at all: command-not-found is
  the "version cannot be read" branch, not an error to retry. The chain
  depends on `partnerResultId`, which `generate` reports from
  0.1.0-alpha.9; a build before that rigs the character and charges for it
  but never returns the character id, so the motion step cannot follow. On
  an older build, or when the version cannot be read, say so BEFORE anything
  is spent and offer the choice: upgrade first (`unity plugin upgrade ai`,
  then read the version again), or skip Uthana and take the in-Editor path
  (a Humanoid rig in the Unity Editor retargets any humanoid motion through
  Mecanim, without Unity Credits; driving the Editor is the `unity-cli`
  skill's job). There is no binary to inspect, so the version string is the
  only signal. Do not start the chain and look for the field afterwards.
- **Input constraints.** Before the rig quote, run `models show
  uthana-character-rig` and read what the definition says about the input
  (formats, keys, any limit in the description or `params_schema`), then
  the limits this document records that the definition does not (section 1:
  the size cap). Read the size of the file that will be uploaded, compare it,
  and state the result in the quote line: "input <size>, under the <cap>
  cap". Over the cap, the plan includes the retopo step below; the rig is
  not quoted until the retopo output is measured. A GLB's size is either
  geometry or textures and the remedies differ (retopo or a face limit
  against `texture_quality`), so when a file is over the cap and it is not a
  dense generated mesh, look at what fills it before choosing the fix.

1. Character model: an existing file, or image to 3D exactly as `models.md`'s
   "Text to 3D goes through one image" says (one approved concept image,
   `model3d-tripo-p2`, no multiview). This plan ends in a rig, so the
   concept image is drawn without accessories, as that subsection says:
   say it BEFORE the image is generated.
2. Retopo with `model3d-tripo-retopo` when the measured model is over the
   rig's size cap (a mesh generated with a high `face_limit` can be; section 1
   says how to avoid that at generation): `--in <model> --in-param
   reference_model --param face_limit=<1000-20000>`. Measure the output
   before the next quote.
3. Rig with `uthana-character-rig` (not Tripo, because the motion step takes
   a Uthana character id).
4. Motion on that character, from the user's answer to where it comes from
   (`motion-source.md`): `uthana-text-to-motion-3` from text (recommended),
   `uthana-video-to-motion-3` from their clip, or from a generated take
   (Act it out, `generated-video-to-motion.md`), each with
   `--param target_character_id=<rig partnerResultId>`. This is the last paid
   step of the normal plan, and it still gets the checkpoint (SKILL.md's
   Checkpoint between steps runs it on a motion that ends a sequence),
   unless the user waived checkpoints ("without stopping").
5. `uthana-retarget` only when the motion already exists (generated earlier,
   or wanted on a second character). Never add it to a plan where step 4 can
   take the character id.
6. Look at the result yourself (`--views poses,path,feet`), then preview it
   for the user (the preview page plays GLB animations), and report every
   path, cost and the ids.
