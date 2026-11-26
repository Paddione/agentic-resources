# Sequence: a character motion from a generated video

A user who said not to ask (SKILL.md, When the user says not to ask): every question
this file has you ask, but money, is your own call; say what you chose in the final reply.

A biped motion comes from text (`uthana-text-to-motion-3`, the default) or
from a video of a person doing it (`uthana-video-to-motion`). When the user
has no clip, the video can be generated: one still of a neutral actor, a
short image-to-video take of the actor performing the move, then the take
converted to motion. The user calls this "act it out". The take is where
mistakes are caught: a wrong take is redone before the conversion is
charged (step 4). This route is an extra
answer at two points of the motion step (`motion-source.md`),
never a replacement for text; read this document only once the user has
chosen it.

```
neutral actor still (.png)
   │  2. unity ai generate --model gpt-image-2-5-flare --param background=opaque
   │         --param width=1536 --param height=864 --out actor.png
   ▼
one approved start frame
   │  3. unity ai generate --model video-kling-v3-i2v-pro --in actor.png --in-param start_image
   │         --param aspect_ratio=16:9 --param duration=5 --param generate_audio=false --out take.mp4
   ▼
5 s take of the actor performing the move (.mp4)
   │  4. contact sheet of the take, read locally (free); a wrong take is regenerated here, not converted
   ▼
approved take
   │  5. unity ai generate --model uthana-video-to-motion --in take.mp4 --in-param video_reference.asset_id
   │         [--param target_character_id=<rig partnerResultId>] --out motion.glb
   ▼
motion (.glb or .fbx)   ← done, three paid generations (the still is reused across takes)
```

Each paid step follows the normal flow (model shown to the user, save
location, quote + consent, generate, preview, then the checkpoint of the main
skill's Sequences section). Every `generate` runs as SKILL.md's Running
`generate` says: `--format ndjson`, stdout and stderr in logs next to
`--out`, never piped through a filter, and its own exit code acted on. The
rig, the ids and `target_character_id` work exactly as
`rig-and-retarget.md` says; this document only adds the video route to its
motion step.

Every Uthana model is biped only. A creature that is not a biped follows
`creature-rig-and-animate.md`, and this route does not apply to it.

## 1. Where it is offered

`motion-source.md`: the source question (Describe it, recommended; Use my clip; Act it out) and the second
Edit answer at the motion checkpoint, with the table that says which to
recommend. The agent does not choose this route on its own; this document
starts once the user has picked it at either point.

## 2. The start frame: a neutral actor, not the user's character

The video is a performance to capture, not a render of the character: the
conversion wants a person, and the motion lands on the user's rig in step 5.
So the start frame is a plain human actor whatever the character looks like
(a robot, a goblin and a knight all get the same actor). Generate it once
with `gpt-image-2-5-flare` and `--param background=opaque` (the video model
takes an opaque frame), and reuse it for every take of the session:

- An invented person who resembles no real or famous one, never a photo of
  a real person. When the user's request names a real person ("walk like
  <a celebrity>"), the take prompt describes the move instead of naming
  them: real people are a common reason a generation is blocked.
- One person in plain, fitted grey athletic clothes, no props, hair tied
  back, arms relaxed at the sides: loose clothing and props hide the limbs
  the conversion has to track.
- Three-quarter view, full body, standing on both feet: the conversion
  needs both feet on the ground at the start.
- An empty studio with a visible floor and back wall, evenly lit, no
  shadows to speak of, no other people, no text. Not a plain or
  transparent backdrop: the conversion places the body against the floor
  and the wall. Clothes and walls in contrasting tones (grey clothes on a
  light wall, not grey on grey), so the outline stays clear.
- The camera at chest or eye height, level: a high or low angle comes back
  as a slanted animation.
- Any human build works; a cartoon or non-human figure is harder for the
  conversion, which is one more reason the actor is not the character.
- **The body fills about half the frame's height, centred, with headroom.**
  A first version at about 80 percent cropped every jump at its apex; the
  move needs room inside the frame, and a body that leaves the frame is a
  body the conversion cannot track. Asking for "about half the frame" is
  not enough: that wording came back at 86 percent. Describe a wide shot
  instead; this gave 45 percent: "a wide shot of an empty photo studio with
  one person standing small in the middle of the frame: the person is only
  about half the image height, with a large area of empty back wall above
  the head and open floor all around ... the camera at chest height, level,
  far from the person".
- **16:9, set by size**: `--param width=1536 --param height=864`.
  `gpt-image-2-5-flare` has no aspect ratio parameter, only `width` and
  `height` (default 1024x1024, both multiples of 16, so 1920x1080 is
  refused), and a square still is reframed by the 16:9 take, which undoes
  the framing above. A 1536x864 PNG is well under the take's 10 MB cap on
  its start frame.

Before the take is quoted, read the saved still's size from the file
(Pillow, PowerShell's image library, or ffprobe; the preview's details
panel, key I, shows it to the user as Size): it must be 1536x864. A still of any other size is regenerated with the size
params, never sent to the take, which would pad or crop it and can cut off
the headroom. Then look at the still and judge the body's height against
the frame's: from head to feet it spans about half the height, with clear
wall above. A body over about 60 percent is regenerated with the wide-shot
wording above before any take is quoted.

These regenerations are the agent's own, so they are capped like takes
(step 4), within a session budget or not: at most two stills regenerated on size or
framing, three charged stills in all. Past the cap, or once a still passes,
go to the checkpoint with the last still, say what is still off (its size
or the body's height) and the running spend on stills ("third still, 6
credits spent on stills so far"); a still of the wrong size is still never
sent to the take, so Use it is not offered for one.

Checkpoint: preview, Use it / Edit / Stop. The still costs a couple of
credits and serves every motion of the session, so get it right once.

## 3. The take

Model: `video-kling-v3-i2v-pro`, the one the trial measured (23 of 24 takes
met the constraints below and came back about 1920x1080 (1912x1084 in the
trial, exactly 1920x1080 on 4 of 4 takes in a later run), 24 fps, 5.04 s,
inside the conversion's limits). Newer video models may hold limbs and counts
better; one that has not been checked against step 4's gate is offered as an
alternative, named as unchecked, never as the default, and only once ffprobe
can confirm its takes run at 24 fps or more: Kling's 24 sits exactly on the
conversion's minimum, and a model that returns 23.976 fps is charged for the
take and then refused by the conversion. Read `models show
video-kling-v3-i2v-pro` first: `duration` is a string enum, `aspect_ratio`
its own parameter with a 16:9 default.

- `--in actor.png --in-param start_image`.
- `--prompt`: the move, one sentence, then the constraints: "a single take
  filmed on a tripod at chest height, the camera locked off, no camera
  movement, no zoom, one person, the whole body and both feet in frame
  throughout, starts standing on both feet, real-time speed, the studio
  stays exactly as it is". Name the parts the evidence says go wrong: the
  count ("one jump"), the side ("kicks with the right leg"), the order
  ("left jab, then right cross"), the end ("ends back in a guard stance").
- `--param negative_prompt="camera movement, pan, zoom, cut, cropping, the
  person leaving the frame, a second person, slow motion, text"`.
- `--param aspect_ratio=16:9`, `--param duration=5`,
  `--param generate_audio=false`.

Check the take against the conversion's input limits before step 5; the
limits are the ones `rig-and-retarget.md` section 3 lists from `models show
uthana-video-to-motion`. Read the take's duration, frame rate and size with
`ffprobe -v error -select_streams v:0 -show_entries
stream=width,height,r_frame_rate:format=duration -of csv=p=0 take.mp4`, run
by the path the `tools` row of `unity ai doctor --format json` gives under
`details.ffprobe`. A take outside a limit is regenerated, never converted: it
still uploads and still charges. Without ffprobe, ask the user to read the
Video row of the preview's details panel (key I): it shows the duration and
the size, not the frame rate, so say the frame rate was not checked. The
Kling takes of the trial all came back at 24 fps, inside the limits.

## 4. Contact sheet, then regenerate the take, not the motion

No take in the trial was screened before its conversion, and every
video-route failure it recorded was already visible in the take: two
straight-legged jumps for one tucked jump, a lunge that ended in sword
slashes, the wrong leg kicking, punches out of order, and a background that
shifted mid-clip. So every take is checked before it is converted.

**With ffmpeg** (on PATH, or by the full path the `tools` row gives under
`details.ffmpeg`; for `FFMPEG_NOT_ON_PATH`, name that path to the user
before the first run, as SKILL.md's Troubleshooting says), render a contact
sheet of 16 frames to a scratch file, never next to the outputs, and read
it:

```
ffmpeg -i take.mp4 -vf "fps=16/<duration>,scale=320:-2,tile=4x4" -frames:v 1 <scratch>/take-sheet.png
```

`<duration>` is the take's own, from the ffprobe line in step 3 (5.04 s,
not 5). `scale` keeps each cell 320 px wide, so the sheet is about 1280 px
across and readable; without it a 4x4 sheet of full frames is 7648 px wide.
`-frames:v 1` writes the one sheet even when the rate yields a seventeenth
frame. `image-to-spritesheet.md` step 4 has the same command in full (frame
count check, crop, cap) when a finer sheet is needed.

This sheet shows the count, framing and background, but **not the side**:
with the actor at half the frame height, the person is about 80 px tall in
a 320 px cell, too small to tell a left leg from a right. When the ask names
a side, check it on two closer views, cropped to the area the actor moves
through (read it off the first sheet):

```
# the actor about 4x larger than in the first sheet
ffmpeg -i take.mp4 -vf "fps=16/<duration>,crop=<W>:<H>:<X>:<Y>,scale=300:-2,tile=4x4" -frames:v 1 <scratch>/take-sheet-crop.png
# one full-resolution frame at the move (cell n of a 16-cell sheet is at (n-1) x <duration>/16 s)
ffmpeg -ss <seconds> -i take.mp4 -frames:v 1 -vf "crop=<W>:<H>:<X>:<Y>" <scratch>/take-frame.png
```

Work out which way the actor faces first: in a three-quarter or profile
view, the side nearer the camera is the actor's right when they face
image-right, their left when they face image-left. Then judge the limb by
what it hides or overlaps (a kicking leg nearer the camera hides the
standing hip). Say in the checkpoint how the side was read; when it cannot
be read, say so rather than passing the take on it.

**Without ffmpeg**, look at the take with `unity ai preview "<take>" --png
--views frames` and read the PNG: eight frames evenly spaced over the take,
4 x 2 cells of 320 x 240, each with its time. It needs Edge or Chrome, not
ffmpeg. Eight samples are half the sheet above and as small, so a fast move
can fall between two of them and a left leg cannot be told from a right:
check what they show (the count, the body and both feet in frame, a still
camera and background) and say which points they could not settle. Those
points are the user's: open the take in the preview, give them those items
of the list below, and ask them to confirm each. When the capture cannot run
either (`BROWSER_NOT_FOUND`), the whole list is the user's. Never report a
take as checked when nobody looked at it.

Check, in the sheet (or ask the user to), and say what was found in the
checkpoint question:

- the count of hits, steps, jumps or spins the user asked for;
- which hand or leg does each part, and the order of the parts;
- the whole body and both feet in frame in every cell;
- one person, the camera and the background still;
- feet on the floor in the first cell.

A take that fails is regenerated with a revised prompt (same start frame,
new `--out`), at the take's price, not converted: the conversion copies the
take's mistake and charges for it. Two limits keep the loop bounded:

- Two failed takes on the same point mean the video model does not do that
  move.
- Three charged takes per motion in all, whatever they failed on.

At either, stop generating takes and offer text to motion with a prompt
that states the move precisely (tucked, both knees to the chest, one jump),
or a stop. Every take checkpoint states the running spend on takes for this
motion ("third take, 288 credits spent on takes so far"). A take refused with
`CONTENT_BLOCKED` was not charged and does not count toward either limit;
handle it as SKILL.md's Known limitations, Content filters says: it picks the
revised prompt and runs it only after the user says yes.

## 5. The conversion

```
# bash; PowerShell form, the <consent> flag and the <log> / <err log> paths in SKILL.md, Running `generate`
unity ai generate --model uthana-video-to-motion \
  --in take.mp4 --in-param video_reference.asset_id \
  [--param target_character_id=<rig partnerResultId>] \
  --out <path>.glb --format ndjson <consent> \
  --billed-to <payer from the accepted quote> > <log> 2> <err log> && rc=0 || rc=$?
echo "exit $rc"
```

Act on that exit code and on the `error` event's `code` as SKILL.md's
Running `generate` says: it is what tells a charge that must not be re-run
(`SUBMIT_UNCONFIRMED`) from a failure that may be.

`target_character_id` puts the motion straight onto a Uthana rig, as
`rig-and-retarget.md` section 3 says; without it the motion comes on Uthana's
default character. Keep GLB on a character that kept its own skeleton
(`rig-and-retarget.md` section 1). The done event carries a motion
`partnerResultId` like any Uthana motion.

Set expectations in the plan, before the quote, and check the result for
them yourself with `unity ai preview "<motion>" --png --views poses,path,feet`
(`path` shows drift, `feet` sliding and how high the feet leave the ground),
then for the user in the preview with the ground grid on (key G): the
conversion is noisier than text-to-motion on the same move.

- **Foot sliding** on moves done in place: 6 to 17 cm/s in the trial, against
  2 to 4 for text. Plan on foot locking in the Editor or a trim of the
  sliding stretch.
- **Jitter** up to about 2.5 times text's on fast moves.
- **Airborne height exaggerated**: a hop of about 20 cm became close to a
  metre of flight. A jump whose height matters is checked against the take.
  Text to motion does it too (a later run's tucked jump hung for 1.75 s
  about 0.8 m up), so say it in the plan for any jump, on either route.

None of these is fixed by converting the same take again. A take that is
right with a noisy result is the user's call: keep it and clean it up in the
Editor, or try text to motion.

## Costs

From two runs (the trial on 2026-10-07, and a test on 2026-10-08 that
recorded quotes and worst cases; the take was quoted 13, worst case 39, until
its price was raised on 2026-10-16 so long clips are charged in full; the
text-to-motion and take quotes follow their params as of 2026-10-23, and the
conversion was quoted 42, worst case 126, until 2026-10-26). Prices rose about
sixfold (Uthana about twofold) in the October 2026 price change; the charges
below were measured before it, so the Charged column is the old charge and
the sentence after the table converts it. Quote every step, these are for the
plan only:

| Step | Quote | Worst case | Charged before the price change |
|---|---|---|---|
| Actor still, once per session | 11 | 67 | 2 (both runs) |
| Take | follows length and audio: 100 for 5 s without audio, 147 with | the quote plus 20%: 120, 177 | 16 (both runs) |
| Conversion | 122 | 366 | 17 (both runs) |
| Text to motion, for comparison | follows `length`: 49 at the default 4 s, 98 at 8 s, 122 at 10 s | the quote plus 20%: 59, 118, 147 | 27 (3 of 3, 2026-10-08); 33 (23 of 24, trial) |

So at today's prices the first motion acted out charges about 140 credits
(still, take, conversion), each later one on the same still about 130, plus
about 96 per extra take; one text-to-motion charges about 49 to 61. The take's
quote follows its length and audio (100 for 5 s without audio, up to 433 for
15 s with audio). The conversion charges by the take's length, about 6 credits
a second (about 31 for a 5 s take, 90 for 15 s), whatever its quote of 122: say
that at consent with its worst case of 366. Consent
is still given on the worst case, as SKILL.md says. A rejected take costs
about 96; a rejected conversion costs about 31 and the take behind it.

## What is not known yet

- The trial used Uthana's default character only. Motions on a rig made from
  a generated mesh (a Tripo or Uthana rig of a `model3d-tripo-p2` character)
  were not measured on either route.
- One rater, two samples per motion: one more sample can move a motion's
  score by about 25 points, so a route that loses one motion narrowly has
  not lost it.
- The contact-sheet gate of step 4 was not part of the trial; the failures
  it would have caught were.

## Plan to propose

Once the user has answered **Act it out** (`motion-source.md`),
at either point:

Preflight, free: `models show` for `gpt-image-2-5-flare`,
`video-kling-v3-i2v-pro` and `uthana-video-to-motion` (keys, duration enum,
input limits); the plugin build and the rig, as `rig-and-retarget.md`'s
preflight says when the motion goes onto a rig; and whether ffmpeg and
ffprobe are there for the take check (the `tools` row of `unity ai doctor
--format json`, its `details`). Without them, say in the plan that the user
checks each take (step 4).

1. The noise to expect from the conversion (step 5), in one line.
2. When the motion goes onto the user's character: the rig steps of
   `rig-and-retarget.md`, first (already done when the answer came at the
   motion checkpoint).
3. Start frame: the neutral actor, once (step 2). Checkpoint.
4. Take: Kling i2v-pro, 5 s, the prompt of step 3. Contact sheet read
   before the checkpoint; a failing take is regenerated (step 4).
5. Conversion of the approved take, with `target_character_id` when there
   is a Uthana rig. Your own look at `--views poses,path,feet` first, then
   the checkpoint in the preview, ground grid on.
6. Report every path, each step as quoted and as charged, the takes that were
   rejected and why, and the ids next to their files.
