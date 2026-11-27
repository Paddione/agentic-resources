# Sequence: a 2D sprite sheet from one concept image, through a video

A user who said not to ask (SKILL.md, When the user says not to ask): every question
this file has you ask, but money, is your own call; say what you chose in the final reply.

A sprite sheet of a 2D animation (a walk, an idle, an attack) takes **two** paid
generations and one free local step: a concept sprite, a short video of that
sprite animating in place, and the frames of the video sampled into a grid.
The image is the cheap iteration surface, the video is the expensive step and
runs once, and the sheet costs nothing. Read this before proposing the plan;
the video-model and end-frame questions in step 2 and the layout rules in step
4 are what
users and agents get wrong.

```
concept sprite (.png)
   │  1. unity ai generate --model gemini-nano-banana-2-1 --prompt "..." --out sprite.png
   ▼
one approved frame  ── (optional, asked once) an end frame: the same file, or a second pose ──┐
   │                                                                                          │
   │  3. unity ai generate --model video-minimax-h3 --in sprite.png --in-param first_frame_image  (recommended)
   │         [--in <end>.png --in-param last_frame_image] --param duration=5 --param resolution=768P --out clip.mp4
   │     or: --model video-minimax-h3-fast  (same keys and params as H3; a walk only)
   │     or: --model video-seedance-2-5 --in sprite.png --in-param image
   │         [--in <end>.png --in-param last_frame_image] --param duration=4 --param generate_audio=false --out clip.mp4
   │     or: --model video-kling-v4-i2v --in sprite.png --in-param start_image
   │         [--in <end>.png --in-param end_image] --param duration=3 --param resolution=720p --out clip.mp4
   ▼
short clip of the sprite animating in place (.mp4)
   │  4. sample N frames evenly into a grid, locally (ffmpeg) → sheet.png, then unity ai sidecar derive sheet.png --from clip.mp4 ...
   ▼
sprite sheet (.png)   ← done, two paid generations
   │  5. offered: key the flat backdrop out locally (free) → sheet-keyed.png
   │     only when the key cannot: unity ai generate --model photoroom-bg-removal --in sheet.png --out sheet-cutout.png
   ▼
sheet on a transparent background
```

Each paid step follows the normal flow (model shown to the user, save
location, quote + consent, generate, preview, then the checkpoint of the main
skill's Sequences section: the user looks at the result and chooses Use it /
Edit / Stop before the next step is quoted). Every `generate` runs as
SKILL.md's Running `generate` says: `--format ndjson`, stdout and stderr in
logs where that section puts them (next to `--out`, or under
`Logs/unity-ai/` when `--out` is under a project's `Assets/`), never piped
through a filter, and its own exit code acted on. The rules below are what is specific to this sequence.

The layout and playback rules in step 4 are the ones Unity AI Desktop
(Cocreate) applies in its own video detail panel, so a sheet made here matches
one saved there: same frame counts, same grid, same size cap, same default
frame rate.

## 1. The concept sprite

Generate with `gemini-nano-banana-2-1` (it paints an opaque background, which the
video step needs; a style the user asks for goes into the prompt; on a model whose `background` offers `opaque`, pass
`--param background=opaque`, since its default `auto` can return alpha). The
image becomes the first frame of a video, so it is drawn for that:

- **One pose, the neutral start of the motion**: standing for a walk, guard
  stance for an attack. The video moves it; the image does not animate.
- **The game's view**: side view for a platformer, three-quarter or top-down
  when the user says so. Put the view in the prompt.
- **Centred and well inside the frame**, arms and feet clear of the edges:
  the motion needs room, and a limb that leaves the frame is cropped in every
  frame of the sheet. For a motion in place (walk, run, idle, attack) the
  character fills about 70 percent of the frame's height: enough pixels for
  the cells, enough margin for a swing or a stride. When only the size or
  the position of an otherwise approved sprite is wrong, fix it locally for
  free (scale or shift the PNG on the same backdrop colour), not with a paid
  redraw, which changes the character too.
- **Small and low for a motion that travels.** A jump, a hop, a leap, a
  flip or a dash moves the character across the frame, and the video model
  sizes that travel to the character, not to the room left around it: a
  character drawn large in the middle of the frame jumps out of the top of
  it, and asking for a lower jump in the video prompt does not reliably
  bring it back. Put the travel room in the image: for vertical travel draw
  the character at about a third of the frame's height, standing in the
  lower third; for horizontal travel, off-centre on the side it starts from.
  The frames are cropped to the character's own area in step 4, so the
  small drawing costs no sheet resolution. A motion in place (walk, idle,
  attack, talk) keeps the centred framing above.
- **A plain, solid, evenly lit background, no ground shadow, no props**: the
  video model moves the character, not the backdrop, and the free key of
  step 5 needs a flat backdrop (without one, only the paid cut-out is
  left). A single flat colour that is not in the character (a plain green
  or magenta) makes the key easiest.
- **Aspect ratio of the video**: `--param aspect_ratio=1:1` for a square cell,
  `16:9` for a wide one. Choose it here and pass the same value to the video
  step: Kling Pro does not read the start frame's ratio, its `aspect_ratio`
  is its own parameter with a 16:9 default, and a square sprite sent without
  it comes back as a wide clip, padded or cropped, after the charge. Keep the
  resolution at the default `1K`: the video model caps each frame at 10 MB
  (step 3), and a 1K PNG is well inside it.

Checkpoint: preview, Annotate (key A) for changes, Use it / Edit / Stop.
Skip the cut-out offer here, on this document's authority: the sprite is a
character, which would trigger Offer a transparent background in SKILL.md,
but it is the first frame of a video, the video model takes an opaque frame,
and a transparent PNG would be composited on a background you did not
choose (SKILL.md's Not for list names this case). The cut-out comes at the
end, on the sheet.

## 2. The video model, then the end frame: two questions before the quote

**The video model.** Ask it ONCE, right after the sprite checkpoint and
before the end-frame question (whose keys depend on the answer), with the
question tool. Quote all four first, for free, so each answer carries its
figure (typical cost and worst case, as Plan to propose says). Offer them in
this order:

- **`video-minimax-h3` (Recommended)**: the best clean in-place cycle for
  its price: about as sharp as Seedance at under half its quote. On one
  knight sprite (2026-10-14) its walk stayed crisp in every sampled frame, kept the backdrop colour and drew no ground
  shadow, and its last sampled frame came closest to its first; its jump
  had a visible crouch, stayed well inside the frame and landed cleanly,
  but rose less than Kling V3 I2V Pro's. Its quote follows length and resolution:
  about 72 credits for 5 s at 768P, 114 for the default 5 s at 2K, 332 for 15 s
  at 2K, each with a worst case of the quote plus 20% (87, 137, 399). With
  reference videos, or more than five reference images, it quotes 240 with a
  worst case of 720, because those cost more than the length
  shows. One walk and one jump are all it has been checked on; the
  measured rules below come from Kling V3 I2V Pro clips, so on H3 they are a starting
  point, not a calibration.
- **`video-minimax-h3-fast`**: the cheapest clean walk, at under half H3's
  quote and about twice as fast. On a knight (2026-11-02) and a fox
  (2026-11-12) its walks were as clean as H3's, the fox's loop closer, but
  the knight's attack slashed and then held the lowered sword still for the
  second half of the clip, so the sheet did not loop. Offer it for a walk;
  for an attack or other fast motion, recommend H3. An idle is untested.
  It takes 480P or 768P (no 2K) and 4 to 15 s. Its quote follows length
  and resolution: about 32 credits for the default 5 s at 768P, 18 for 4 s at
  480P, 85 for 15 s at 768P, each with a worst case of the quote plus 20%
  (39, 22, 102). With reference videos, or more than five reference images,
  it quotes 60 with a worst case of 190.
- **`video-seedance-2-5`**: frames that stay sharp through fast motion, at
  about twice H3's quote for this sequence's clip (161 for 4 s at 720p against
  72). Its frames stay sharp through motion where Kling V3 I2V Pro's smear (on the
  same sprite and prompt, V3 Pro's airborne frames blurred and Seedance's did
  not; V3 Pro's clip was high bitrate, so the smear is the model, not
  compression). Its catalog figure (195) is only the typical clip: its quote
  follows the clip's length and resolution, about 75 credits for 4 s at
  480p, 161 for 4 s at 720p, 200 for 5 s at 720p, and up to about 2877 for
  30 s at 1080p, and its worst case is the quote plus 20%, at most 2880. Without
  `duration` it makes a 5 s clip; pass the length the motion needs. The Seedance
  clips charged before the October 2026 price change cost 15 (a walk, before
  this sequence existed), 27 (a 4 s hop) and 160 (a walk); at today's prices
  those are about six times as much. Say the quote and its worst case; the user
  plans on the quote and consents on the worst case. The measured rules below
  (start-pose hold, loop-score thresholds, backdrop shift, shadow remnant)
  come from Kling V3 I2V Pro clips; on Seedance they are a starting point, not a
  calibration. The 160-credit walk was checked against the start-pose,
  loop-closure and backdrop rules; the note beside each rule gives the
  result. Still
  untested on Seedance: the shadow remnant, the period pick, and any motion
  but a walk.
- **`video-kling-v4-i2v`**: the Kling option. On the same knight walk, knight
  attack and slime hop (2026-11-16, one take each) it left no ground shadow
  where Kling V3 I2V Pro left one on the walk and the hop, and its attack
  stayed side-on and returned to guard where V3 Pro turned toward the camera.
  It keeps the sprite's own aspect ratio. Its quote follows length and
  resolution: about 84 credits for 3 s at 720p (V3 Pro: about 62 without
  audio), 202 for its default 5 s at 1080p, with a worst case of the quote
  plus 20%. `video-kling-v3-i2v-pro`, the model this sequence was tuned on,
  still runs; the Kling parameters below are written for it, and V4's
  differences follow the H3 Fast paragraph. Use V3 Pro only when the user
  names it. The measured rules below (start-pose hold, loop-score
  thresholds, backdrop shift, shadow remnant) come from V3 Pro clips; on V4
  they are a starting point, not a calibration.

The end-frame question below uses whichever model was chosen: Seedance's
keys are `image` and `last_frame_image`, MiniMax H3's and H3 Fast's `first_frame_image`
and `last_frame_image`, Kling's `start_image` and `end_image`. Below, `<start key>` and `<end key>` stand for the chosen
model's pair.

**The end frame.** The chosen model takes an optional end frame. Ask about
it ONCE, before the video quote, with the question tool, and lead with the
default:

- **No end frame (Recommended)**: the start image only. The model is free on
  the motion. A sheet loops by playback, so the last sampled frame only has
  to be close to the first, not identical, and the even sampling of step 4
  never includes the very last frame of the clip anyway.
- **Loop back to the start**: the same sprite as `<end key>`. The clip is
  forced to return to the start pose, for a cycle that must close exactly.
  Say why it is not the default: a hard end frame pins the whole clip to the
  start pose and tends to flatten the motion into a small sway.
- **A different end pose**: a second image as `<end key>`, for a transition
  (idle to attack stance, standing to crouched, closed to open). The user
  names an existing file, or the chain adds an image step before the video:
  generate the end pose from the start sprite as a reference (`--ref
  sprite.png` on `gemini-nano-banana-2-1`, prompt "the same character, same
  framing, same background, now <pose>"), with its own checkpoint, then the
  video step takes both.

Only the third answer adds a step to the plan. Whatever the answer, the
start frame is uploaded by `--in sprite.png --in-param <start key>` (`image`
for Seedance, `first_frame_image` for H3 and H3 Fast, `start_image` for Kling). An end frame is a second pair in
the same run: `--in sprite.png --in-param <start key> --in <end>.png
--in-param <end key>` (`last_frame_image` or `end_image`) on the paid step;
quote it with the same two pairs (`quote` uploads nothing). Say the path in
one sentence.

## 3. The video step

Model: the one step 2 chose. The parameters below are written for
`video-kling-v3-i2v-pro`; for `video-seedance-2-5` apply the same intent to
its schema (`models show video-seedance-2-5`) with these differences, each of
which is rejected or wasted after the charge: the start frame goes in with
`--in-param image` and the end frame as `last_frame_image`; `duration` is an
integer with a minimum of 4, so a cycle is `duration=4`; leave `resolution`
at its 720p default, enough for sprite cells; `generate_audio=false` as for
Kling; and there is no `negative_prompt` and no `cfg_scale` (the schema is
`additionalProperties: false`, so either key fails the quote): put the
default exclusions list below into the prompt as plain wording ("no shadow,
no ground, no motion blur, ..."), and accept that a faint shadow may remain
for step 5 to remove. Leave `output_format` at `mp4` unless the user wants
`mov`: step 4 reads either, `mov` is larger. The bullets marked Kling only
do not apply to Seedance.

For `video-minimax-h3` (`models show video-minimax-h3`), the keys are
`first_frame_image` and `last_frame_image`, and the differences from
i2v-pro are: `duration` is an integer from 5 to 15, so a cycle is
`duration=5`; pass `--param resolution=768P`, enough for sprite cells (its
2K default costs more); `aspect_ratio` is ignored with a first frame, so the
sprite's own ratio is the clip's; it always adds a soundtrack and has no
`generate_audio` key, which step 4 ignores; and, like Seedance, there is no
`negative_prompt` and no `cfg_scale`, so the exclusions go into the prompt.
A last frame needs a first frame, and frames cannot be combined with its
reference inputs, which this sequence does not use. The bullets marked
i2v-pro only do not apply to it.

For `video-minimax-h3-fast` (`models show video-minimax-h3-fast`), everything
above for H3 applies, with two differences: `duration` runs from 4 to 15, and
`resolution` is `480P` or `768P` (default `768P`, no 2K), so pass
`--param duration=5 --param resolution=768P` as for H3; `480P` is cheaper but
gives smaller cells.

For `video-kling-v4-i2v` (`models show video-kling-v4-i2v`), the keys are
Kling's `start_image` and `end_image`, and the differences from i2v-pro are:
`duration` is an integer from 3 to 30, so a cycle is `duration=3`; pass
`--param resolution=720p`, enough for sprite cells (its 1080p default costs
half as much again); it follows the sprite's own aspect ratio and has no
`aspect_ratio` key; it always adds a soundtrack and has no `generate_audio`
key, which step 4 ignores; and there is no `negative_prompt` and no
`cfg_scale`, so the default exclusions list goes into the prompt as plain
wording ("no shadow, no ground, no motion blur, ..."). Its frames may be up
to 30 MB, against V3 Pro's 10 MB. The bullets marked i2v-pro only do not
apply to it, and neither does the `duration` bullet's string enum, which is
V3 Pro's schema.

Input constraints (from Pro's `params_schema`, `models show
video-kling-v3-i2v-pro`; re-read it, this is the state at the time of
writing): `prompt` and `start_image` are required, `start_image` and
`end_image` each say only "Max 10mb", and nothing else is stated, so the
frame's size and aspect are the agent's own care (step 1). State the check in
the quote line ("start frame 1.2 MB, under the 10 MB cap"). The cap is
enforced after the charge like every input constraint, and `quote` prices
the job without validating the payload.

Parameters:

- `--prompt`: what the character does, in place, and nothing else moves.
  Name the motion ("walks in place, a full walk cycle", "idle breathing,
  slight weight shift", "one sword swing and back to guard"), then the
  constraints that keep the frames usable: "camera locked, no camera
  movement, no zoom, the character stays centred and the same size, the
  background stays exactly as it is, no new objects, no text". Shorter and
  simpler motions give more consistent frames. For a motion that travels,
  bound it in words as well ("a small hop, about half its own height, the
  whole character stays inside the frame and never touches its edges"), on
  top of the small, low drawing of step 1; the prompt alone is not enough.
- `--param negative_prompt="..."` (Kling i2v-pro only): always set, "no X" in
  the positive prompt
  is weak for this model and the negative prompt is where it listens. The
  default list: "shadow, ground, motion blur, smear, ghosting, camera
  movement, pan, zoom, the character turning toward the camera, the
  character leaving the frame, text". It usually reduces the ground shadow
  and sometimes removes it; when a shadow remains, step 5 and rule 3 of
  step 6 take it out, so a faint shadow is not by itself a reason for an
  Edit.
- **A fast move** (Kling only; Seedance's clip is 4 s at the least) (a spin, a
  strike, a dash) covers its motion in a few of
  the clip's frames, so a 3 s clip gives few distinct poses of the move
  itself. The option, offered with the reason: `duration=5` and "in slow
  motion" in the prompt, then the clean-loop search picks the move out of
  the longer clip. Not the default: longer clips drift more, so it is for
  a move the 3 s clip showed too few poses of.
- `--param aspect_ratio=<the sprite's ratio>` (Kling i2v-pro only; Seedance,
  H3 and H3 Fast follow the first frame): the value chosen in step 1
  (`1:1`, `16:9` or `9:16`, the enum). Pro's default is 16:9 whatever the
  start frame is, so this is never left out.
- `--param duration=3`: the schema's `duration` is a string enum from "3" to
  "15" (default "5"), no minimum; the first value is the one for a cycle, a
  transition needs only as long as the move takes. Longer clips drift.
- `--param generate_audio=false`: the default is true, and the sound is
  thrown away with the frames.
- `--in <end>.png --in-param end_image` only when step 2 said so.
- `cfg_scale` (Kling i2v-pro only; 0 to 1, default 0.5) follows the start
  image and the prompt
  more closely when raised; leave it unless the first clip strayed from the
  sprite, then `0.7` on the Edit.

Checkpoint: the preview plays the clip (native player). Before asking,
look at the clip yourself as frames, for free: with ffmpeg, render a contact
strip of the N frames step 4 would take (`fps=<N>/<L>` and `tile=`, small
cells, to a scratch file, never next to the outputs) and read it; without
ffmpeg, run `unity ai preview "<clip>" --png --views frames` and read its
eight frames, evenly spaced over the clip. Those are not the N frames step 4
takes, so a brief edge touch or the exact frame where the motion starts can
fall between two of them: say so in the checkpoint when you rely on them,
and give the range as approximate. Two things are visible in the
strip that a playing clip hides, and both belong in the checkpoint question
as a recommendation, not left for the user to find in the sheet: a frame in
which the character touches or leaves an edge (a video Edit: revised
prompt, or back to step 1 for a smaller drawing), and a stretch of frames
in which nothing moves. Video models often hold the start pose for the
first second or so of a clip before the motion begins, and a sample of the
whole clip then spends half the sheet on copies of the first frame; note
where the motion starts and ends and propose that range for step 4. (One
Seedance walk showed no start-pose hold, on that clip only; the strip check
still applies on Seedance.) The
user judges the motion and whether the camera and background held still; a
drifting camera or a changing background is an Edit (revised prompt, same
start frame, new `--out`), not something step 4 fixes.

## 4. Frames to sheet: local, free, Cocreate's rules

No model does this; it is a local step with no quote and no consent, and it
never uploads anything. Tell the user it is free.

**Sampling.** N frames evenly spaced over the range the user wants (the part
of the clip in which the character moves, as read from the contact strip at
the clip's checkpoint; the whole clip only when it moves throughout), the
first sample at the start of the range and none at its very end, so a cycle
does not end on a copy of its first frame:

| Setting | Values |
|---|---|
| Frame count N | 4, 8, 12, 16, 24 or 32; **12** by default. 8 or 12 for a walk or idle, 16 to 32 for a fast or detailed move |
| Grid | every cell filled, `columns x rows = N` exactly, columns the divisor of N nearest to and not below its square root, left to right then top to bottom: 4 frames 2x2, 8: 4x2, 12: 4x3, 16: 4x4, 24: 6x4, 32: 8x4. A grid with a spare cell is allowed only when the sidecar carries `frameCount`, which the preview uses to skip the spare; a sheet without that field plays every cell |
| Size cap | the whole sheet at most **2048** px on either side (1K, 4K and 8K on request). Each frame is scaled to whole pixels first, so that `frame width x columns` and `frame height x rows` both fit the cap, then tiled; scaling the tiled sheet instead leaves cells the preview cannot cut on whole pixels. Never scaled up |
| Frame rate | **12** fps by default; 8, 15 or 24 on request. When the clean-loop search found the cycle, also offer the clip's own speed: N frames over a cycle of L seconds play at their real pace at N / L fps (12 frames over 1.1 s: about 11 fps), and say both numbers. Playback only: the sidecar's `fps` sets the preview's sheet strip when the sheet opens, and the strip's field changes it for the visit; nothing is written into the image |

Ask the frame count and the range in ONE question with the question tool
before sampling, with three answers: **find a clean loop for me**, in which
the agent picks the range from the clip's frames (below); the range you
read from the contact strip, stated in seconds; and the whole clip. Frame
count default pre-selected. The frame rate is set in the preview and changed
there. Which answer is marked Recommended follows the preflight's `tools`
reading: the search when a decoder (ffmpeg, on PATH or by the path the row
gave) and a pixel library (Pillow, or PowerShell's image library on Windows)
are both present, because it is free and finds the closing frame pair more
precisely than a range read by eye; the range read from the contact strip
otherwise, and the search is then not offered at all, since it cannot run.
The strip read at the clip checkpoint is what tells the user, before this
question, roughly where the motion is.

**Finding a clean loop.** A free, local search over the clip's frames, run
when the user chose it (the default when the tools are present), and offered
again at the sheet checkpoint whenever the cycle hitches or ends on copies.
It needs the same decoder as the ffmpeg path of this step and a pixel
library; without them the range is read by eye. Decode every frame of the clip to PNG
(ffmpeg `-vf fps=<the clip's own rate>` into a scratch folder, never next
to the outputs), then with Pillow (or PowerShell's image library) on the
frames:

1. **Where the motion is.** For each frame, the fraction of pixels that
   differ from the first frame by more than a small threshold (about 24 on
   0 to 255, on a downscaled copy for speed). The motion window is the
   first frame where that fraction rises above noise to the last frame
   where it is still above it; everything outside is the held pose.
2. **Where it closes.** A loop is a range whose frame after the last
   sample looks like its first sample. Inside the motion window, for each
   candidate start S among the first third of the window and each length
   L, in whole frames, from a quarter of a second (6 frames at 24 fps, and
   never fewer than N) up to `window_end - S`, so that S+L stays inside
   the window and the decoded frames, score the distance between frame S
   and frame S+L (mean absolute difference, same downscaled copy). A pair
   only counts as a loop when the range between them contains motion: some
   frame between S and S+L must be farther from S than the closure
   threshold below, or the pair is two frames of a held pose (the slow
   crouch before a jump) and its low score means nothing. Among the pairs
   that count, take the SHORTEST length whose score is within about 10
   percent of the best score of any length: that is the fundamental
   period. A 3 s clip of a walk holds two or three gait periods, and a
   search that starts at half the window finds a multiple of the period
   (two periods, 2.2 s, on a walk whose period was 1.17 s) and a sheet
   whose 8 frames cover two strides. For a move that returns to its pose
   once (a jump, a swing) the shortest good length is the whole move.
   Closure is judged against the clip's own contrast, never against the
   inter-frame noise floor: a video model never repeats a frame pixel for
   pixel, so "under twice the noise" is unreachable (on the walk, the best
   pair scored 4.8 against a floor of 0.6). Take the median distance
   between frames half a period apart, the most different poses of the
   cycle (14.9 on that walk); the loop closes when the pair's score is under
   half of it. When no pair does, the clip does not close: say so, and offer
   the motion window as the range with the note that the last frame will
   jump back to the first, or a video Edit with the same sprite as
   `<end key>` (`last_frame_image` or `end_image`, step 2's second answer,
   which forces the closure). Report
   the pair's score and that median together, so the user sees the margin.
   On Seedance the rule held once: the 160-credit walk's 1.5 s stride closed
   at 1.8, against a median of 6.2 between frames half a period apart
   (threshold 3.1).
3. **What stays in frame.** Over the N frames the chosen range would
   sample, reject a range in which the character's bounding box touches an
   edge, and prefer the next best pair; a range that cannot avoid it is a
   video Edit, reported as such.

Build the sheet from the winning range as usual, and in the reply say what
was found in plain words ("the character holds still for the first 1.3 s,
moves for 1.4 s and returns to its start pose at 2.7 s; the sheet takes 12
frames from 1.3 s to 2.7 s; the loop point matches to within <score>, and
the clip's own pace is about 9 fps against the 12 fps default") so the user
can judge the choice, not just the result. Record the range in the sheet's
sidecar (`--set "range=..."` on `sidecar derive`, below) so a
re-sample or a later session starts from it. The search picks a range, nothing more: the checkpoint on the sheet
still happens, and the user can still ask for another range by hand.

**Crop before you scale.** A 1K clip tiled 4 wide under the 2048 px cap
scales every frame to a quarter of its size, and a character that filled a
third of the frame ends up a few hundred pixels tall and soft. Most of what
is thrown away is backdrop. So crop every frame to the region the character
moves through, the same region for every frame (a per-frame crop would make
the character jump around the cell), and scale only what is left: find the
union of the character's bounding boxes over the N sampled frames (pixels
that are not the backdrop colour, with Pillow on the frames written as
PNGs, or read off the contact strip by eye), pad it by a few percent on
each side, and put it in the filter chain as `crop=<W>:<H>:<X>:<Y>` before
`scale`, with `<FW>` and `<FH>` then computed from the cropped size. The
cells come out as the crop's aspect, not the clip's, which is fine: the
sidecar's `sheet` is a grid, not a cell shape. The cut-out of step 5 is
unaffected, since the crop keeps a margin of backdrop. This step gives the
character two to three times the pixels for nothing; a paid image edit to
"make the character bigger" is never the answer to a small sprite.

**With ffmpeg** (on PATH, or by the full path the preflight's `tools` row
gave under `details.ffmpeg` when the running shell cannot see it; the
preflight, not a bare `ffmpeg -version`, decides this before the plan is
proposed, so the user knows up front whether this step is a command or by
hand), for N frames over a range starting at S seconds and lasting L
seconds, cropped to the character's region W x H at offset X, Y (Crop
before you scale, above), C columns, R rows:

```
ffmpeg -ss <S> -t <L> -i clip.mp4 -vf "fps=<N>/<L>,crop=<W>:<H>:<X>:<Y>,scale=<FW>:<FH>,tile=<C>x<R>:color=0x<the clip's backdrop>" -frames:v 1 sheet.png
```

`crop` comes before `scale`, and `<FW>` and `<FH>` below are computed from
the cropped size W x H, not from the clip's: a `scale` to the crop's aspect
without the `crop` distorts every cell. Leave `crop` out only when the
character already fills the frame.

`color=` paints a cell no frame fills (a spare cell of the grid) in the
backdrop colour, so it goes away with the cut-out; ffmpeg's default black
would survive step 5 as an opaque block. The colour is the clip's, read
from a corner of its first frame (the median of a 16 px corner patch), not
the value the prompt asked for: the video model paints its own shade (a
prompt's `#C35697` came back `#BF4E8A`; `#FF00FF` came back `#F740FC`; on
Seedance, a sprite's `#EB39F0` came back `#E736ED`), and
a spare cell in the prompt's colour survives the cut-out as a faint block.
The same measured colour is the key of step 5's ffmpeg fallback and of
step 6; step 5's own key is measured again, per cell, from the sheet.

`<FW>` and `<FH>` are the cropped frame's size in whole pixels: W x H itself
when `W x C` and `H x R` both fit the cap, otherwise both sides scaled down by
the same factor and rounded down to integers (`FW = floor(W x k)`, `FH =
floor(H x k)`, `k = min(cap / (W x C), cap / (H x R))`). The clip's own size,
which bounds the crop, comes from `ffprobe -v error -select_streams v:0
-show_entries stream=width,height -of csv=p=0 clip.mp4`, run by the path the
`tools` row gave under `details.ffprobe`; when that is null, `ffmpeg -i
clip.mp4` prints the stream's size and duration on stderr. The sheet is then
exactly `FW x C` by `FH x R`, and every cell boundary is on a pixel.

For the whole clip, S is 0 and L is the clip's duration (`ffprobe -v error
-show_entries format=duration -of csv=p=0 clip.mp4`). `fps=N/L` can yield
one frame more or fewer on a clip whose duration is not exact, so count
before tiling: `ffmpeg -ss <S> -t <L> -i clip.mp4 -vf "fps=<N>/<L>" -f null -`
prints `frame=` on its last progress line (the count does not depend on the
crop, so this command needs none); when it is not N, nudge L (a little
under for one too many, a little over for one too few) and count again, at
most three times. When it still does not land: one frame too many is
harmless, `tile` keeps the first N and `-frames:v 1` drops the rest; one too
few leaves a spare cell, so lengthen L toward the clip's end, or take the
next frame count down and say so. Then tile. Write to a new `--out`-style path, never over an existing
file.

**Without ffmpeg**: say so in the plan, and keep recommending this chain;
ffmpeg decides how step 4 is done, not which route is right. Offer, as a
question, the ways that exist: the user installs ffmpeg (name the one-line
install for their platform, e.g. `winget install Gyan.FFmpeg`, `brew
install ffmpeg`, `apt install ffmpeg`; you run nothing that installs), or
the two ways that need nothing installed: the video is opened in the
preview and its frames captured by hand, the sheet assembled from them in
an image editor, and the preview page's **Sprite sheet** tool (key S) then
slices and plays that grid image. The clean-loop search is not offered on
this path (it decodes with ffmpeg), so the range is read by eye in the
preview. Do not install anything on the user's machine for this step. When the user
installs ffmpeg during the session, the shell you already have does not see
it: a new terminal does, and so does the binary by its full path (on
Windows, winget puts a link under `%LOCALAPPDATA%\Microsoft\WinGet\Links`
and the build under `%LOCALAPPDATA%\Microsoft\WinGet\Packages`); look
there before reporting the install as failed.

**The sidecar.** Give the sheet its own sidecar before opening the preview,
with the command, never by hand (free, local):

```
unity ai sidecar derive sheet.png --from clip.mp4 --edit spritesheet --set modality=spritesheet --set sheet=4x3 --set frameCount=12 --set fps=12 --set "range={startSeconds:1.3,durationSeconds:1.4}"
```

(`range` is JSON; its key names may go unquoted, as here, so the argument
reads the same in every shell). It keeps the clip's provenance, records the sheet's own hash and the edit, and
leaves the clip's charge on the clip. The preview reads `modality` and
`sheet` and slices the sheet on its own (the launcher's `--sheet <C>x<R>`
does the same for one visit; the sidecar makes it stick), `frameCount` tells
it how many cells are frames (a spare cell is skipped) and `fps` sets its
strip's rate; `range` lets a re-sample or a later session start from the
same stretch of the clip.

Checkpoint: open the preview on the sheet (the strip plays it at the sidecar's
fps; Space to pause, `,` and `.` to step). The user judges the cycle:
a hitch is a frame count or range to change (free, re-run this step); a
character that changed size or drifted is a video Edit (step 3); a wrong pose
is an image Edit (step 1).

Judge the sheet by its **distinct poses**, never by how alike its frames
are. Step through the cells and count the poses that differ: a walk cycle of
8 frames with 4 poses and 4 near-copies is a sheet that barely moves, and a
similarity score would rate it above a sheet whose frames all differ, which
is the one that animates. When several cells are copies, the clip's motion
is too slow for the range: sample a shorter range around the motion, or
fewer frames, before anything paid is redone. Whenever the checkpoint ends
in a re-sample, the question offers the same three answers as the first
sampling: **find a clean loop for me** (the search above, recommended; when
the search already ran, say what it will do differently this time, e.g. a
different frame count or the second-best closing pair), a range the user
names, or the whole clip, and a re-sample is free however many times it
runs.

## 5. A transparent background: key the backdrop first, pay only when that fails

The video kept the background in every frame. The sprite was drawn on one
flat colour (step 1) so that this step can be free: offer a transparent
background once, as a local key of that colour, and offer the paid cut-out
below only when the key cannot do it. Say it is free, and that the paid
removal stays available.

**Key the flat backdrop, free.** No model, no upload, no credits. Run it with
Python 3 and Pillow (NumPy makes it take seconds on a 2048 px sheet), as the
preflight's `tools` reading says, on every cell of the sheet on its own,
from the sheet at its full size, never a downscaled copy:

1. **The key and its noise, per cell.** Take the pixels of a band along the
   cell's border, about 2 percent of its smaller side wide (the crop of
   step 4 kept a margin of backdrop all round). The key is their median
   colour, and the distance of a pixel from it is the root mean square of
   its three channel differences, on 0 to 1. When more than a quarter of
   the band is farther than 0.15 from the key, the border is not one flat
   colour (a scene, a gradient, a shadow across it): this step cannot key
   that cell, so say which cells and go to the paid cut-out. Otherwise the
   noise is the 90th percentile distance of the band pixels within 0.15
   (the backdrop's own grain; a foot touching the border is not noise).
2. **Clear only the backdrop joined to the cell's border.** A pixel is
   backdrop when it is within `max(0.12, 2 x noise)` of the key; make it
   transparent only when it connects, through other backdrop pixels, to
   the border (flood fill from the border, or label the backdrop mask's
   regions and keep those that touch it). Backdrop the character encloses
   (the gap between the legs, under an arm) stays by default: on a white,
   grey or black backdrop that is the character's own white collar or
   eye. Clear the enclosed regions too only on a saturated key colour the
   character does not use (a green or a magenta, whose highest and lowest
   channels differ by a third of the range or more), after looking at the
   cells: on a magenta key a pink cheek can be such a region.
3. **Un-blend the edge, two pixels in.** The pixels just inside the
   cleared area are a mix of character and backdrop. For each, take the
   character's colour beside it, `f`: the colour of the nearest pixel
   within 3 px that is deeper in (farther from the cleared area), not
   cleared and not backdrop; a ring pixel counts. Its alpha is how far it
   lies from the key toward that colour, `a = ((c - key) . (f - key)) /
   |f - key|^2` (`.` the dot product over the three channels) clamped to
   0..1. A pixel farther than 0.1 from the line through the key and `f`
   (the residual `(c - key) - a (f - key)` before the clamp, measured like
   `d`: the root mean square of its three channels, on 0 to 1) is not a mix
   of the two: give it the distance's alpha below instead. The nearest
   colour, not a mean, is what keeps a thin outline opaque: a mean reaches
   past it into the fill, and the outline fades. The backdrop's share comes
   out of its colour, `c = (c - (1 - a) x key) / a`, clamped to 0..1 (at a
   small `a` the division sends noise far outside it); a pixel at `a = 1`
   stays as it is,
   and so does backdrop the key kept (rule 2's enclosed regions can sit in
   the ring behind a thin wall): it is not a mix, and its `a = 0` would
   divide by zero.
   Skin beside skin projects to 1 and keeps its colour, where an alpha read
   from the distance alone turns the skin of a character with no outline
   into a yellow rim on a magenta key. When `f` is within 0.25 of the key
   (a character that shares the key's colour), there is no line to read:
   use the distance instead, `a = (d - hard) / (0.5 - hard)` (with `hard`
   the threshold of rule 2). Un-blend the whole two-pixel ring, not only
   the pixels just above `hard`: a cartoon's soft edge lies between its dark
   outline and the key, farther from the key than that, and left opaque it
   is a key-coloured fringe. This is what keeps a halo from forming, and it
   is why the key works on the sheet before any removal, not after.
4. **Despill, when the edge still leans to the key.** Video compression
   smears the key a pixel or two into the character's opaque edge. On the
   ring three pixels in from the cleared area, remove from each pixel's
   colour the part that leans toward the key's hue (its colour minus its
   grey mean, projected on the key's colour minus the key's grey mean,
   subtracted when positive). Off by default; turn it on when the
   two-ground check below shows a coloured rim. Leave it off for a
   character whose own colours lean to the key's hue (pink skin on a
   magenta key): it takes that lean out of them too, and their edge turns
   green.
5. **What it says.** The share of each cell made transparent, and every
   cell where an opaque pixel touches the cell's edge (the character runs
   out of the cell: the crop or the clip, not the key). A cell whose share
   is far from its neighbours' lost part of its character or kept part of
   the backdrop. Compare only the frames: a spare cell past the sidecar's
   `frameCount` is all backdrop and keys to fully transparent, as it
   should.

Output `sheet-keyed.png`, never over the sheet. Its sidecar comes from
`unity ai sidecar derive sheet-keyed.png --from sheet.png --edit backdrop-key
--detail "key #<hex>, tolerance <t>"` (`, enclosed` and `, despill` added to
the detail when on), so a later session knows the pixels were keyed locally
and with what. A ground shadow
the video model drew is darker than the key and survives it as an opaque
patch under the feet: rule 3 of step 6 takes it out, on the keyed sheet as
on a cut-out.

Check the keyed sheet as the cut-out below is checked: on two grounds,
then played. A halo or patches of the key's colour are fixed by keying
again from the sheet with the values tuned (a higher tolerance for patches,
despill for a coloured rim, enclosed for a gap between the legs that kept
its backdrop), free and as often as needed; a key that eats into the
character (it is close to the key's colour) wants a lower tolerance. Only
when a retune does not get there, or the border was not flat, is the paid
cut-out the answer. It is also the answer when the user declines the key
or does not like its result: offer it then, with its quote, rather than
another retune. Without Python and Pillow, ffmpeg's `colorkey` filter
(`-vf "colorkey=0x<key>:0.12:0.05,format=rgba"`, the key as the sheet's
measured colour) keys every pixel near the key, enclosed or not, with no
edge un-blend: fine on a saturated key the character does not use, checked
on two grounds like the rest. Its last number is the blend, and a larger
one thins colours near the key (on a test sheet at 0.1, a pink face on a
magenta key went partly transparent); otherwise go to the paid cut-out.

**The paid cut-out, when the key cannot.** Offer `photoroom-bg-removal` on
the finished sheet, once, through the cut-out flow of SKILL.md (quote,
"Remove the background? <N> credits ..."), one paid call for every frame at
once, output `sheet-cutout.png`. Preview the cut-out next to the sheet (two
paths on the launcher with `--sheet <C>x<R>`, which slices both) and look at
it on two grounds, not one: the page's dark stage shows a light halo and a
light ground (the Tile view, or a white image behind it) shows a dark one,
and a remnant of the backdrop hides on any ground close to its own colour.
Then play it: a cell the removal treated differently from its neighbours
reads as a flicker in the strip before it reads as a defect in a still. The
remover is a single-subject model and the sheet hands it N characters in one
picture, so check that every cell kept its character and none lost a thin
limb or a weapon edge; a cell that lost its character is not repaired by
running the sheet again. Cut that cell out on its own (crop, remove, paste
back at the same offset) or accept the sheet without it. `generate` writes
`sheet-cutout.png.unityai.json` itself, with the removal's `modelId`, `jobId` and
`pointsCost`, and it refuses to run when a sidecar already sits at that path, so
never copy or derive the sheet's sidecar there, before or after. Once the cut-out is done,
add to the generated sidecar only the fields that make it a sheet: `modality:
"spritesheet"`, `sheet`, `frameCount`, `fps` and `range`, read from the
sheet's sidecar (the clean-up's sidecar is derived from the cut-out's, so a
field dropped here is lost to every later step); leave every generated
field as it is.

When the user declines both, the sheet stays as it is and the background
colour of step 1 is what they will key out elsewhere.

## 6. Offer the edge clean-up on the cut-out

This step is for the paid cut-out. A fringe on a keyed sheet is fixed by
keying it again with the values tuned (step 5), not here; only rule 3, the
shadow remnant, applies to a keyed sheet as well, and only when a shadow
shows. On a keyed sheet it changes in three ways. Its key-hued test leaves
out near-black pixels (value under about a third of the range): video
compression tints a dark outline toward the key, and the test would bite
into the outline of the feet. Rule 2's smudge test runs inside rule 3's
band too, on every soft pixel whatever its hue: the key un-blended the
shadow's soft edge into dark grey that is no longer key-hued, and left
alone it is a faint ring under the feet. Last, the key's flood (step 5,
rule 2) runs again from the transparent area: backdrop the shadow walled
off, such as the gap between the legs, is joined to it now. On a white,
grey or black backdrop this pass cannot run: the key-hued test has no hue
to go by there and would take the character's own greys (armour, a white
collar) with the shadow. A keyed sheet with a ground shadow on such a
backdrop keeps the shadow and the backdrop it walls off between the legs,
so offer the paid cut-out for it.

A background removal leaves a thin fringe of the background colour along the
outlines, most of it in the semi-transparent edge pixels; on a magenta or
green backdrop it reads as a coloured halo over a dark background. Look at
one cell of the cut-out at 2x or more (the preview's Sprite sheet tool at a
high zoom, or a crop) before offering anything: a sheet with no visible
fringe needs no step. When there is one, offer the clean-up once, with the
free way first and the paid way as the alternative, and let the user pick or
decline:

**Free: recolour the fringe from its neighbours.** No model, no upload, no
credits. The key colour is the clip's backdrop as it came out, read from the
sheet before the cut-out (the median of the four 16 px corner patches),
never the colour the prompt asked for: the model paints its own shade of it,
and a key a few values off leaves the fringe in place. The rules, in order:

1. **Only soft pixels are candidates.** A pixel is fringe when its alpha is
   below about 240 AND its hue is within about 35 degrees of the key's (or,
   for a grey key, its saturation is low and its value near the key's).
   Opaque pixels are never touched, whatever their colour: on a magenta
   key, skin, pink hair and brown boots all lean toward the key, and a test
   over every visible pixel repaints them from their neighbours. That was
   this document's first rule, and it erased skin and boots on a character;
   do not bring it back as "lean toward the key" or "distance to the key".
2. **A smudge is deleted, a fringe is recoloured.** A candidate with no
   opaque pixel that is NOT key-coloured within 3 px is a floating remnant
   of the backdrop (the remover's own soft edge over nothing, or the soft
   rim of a shadow remnant that rule 3 is about to delete): set its alpha
   to 0. Seeding the test from every opaque pixel leaves the rim of the
   shadow green after the shadow itself is gone (11 thousand pixels on one
   sheet). A candidate next to clean opaque pixels is the character's edge
   with the backdrop bled into it: keep its alpha and take the colour of
   the nearest opaque pixel that is not key-coloured (the same set that
   seeds the smudge test; a 3x3 spread of those clean colours into the
   fringe, repeated until none is left, a dozen passes at most). Never
   spread from an opaque key-coloured pixel: where the shadow touches a
   foot, a rim pixel would copy the shadow's green and outlive rule 3. The
   soft edge stays soft; only its colour changes, and dark outlines survive
   because they are opaque.
3. **The shadow remnant, at the feet.** A ground shadow the video model
   drew survives the cut-out as opaque backdrop-coloured pixels under the
   character, and the remover may keep it whole (a solid ellipse in the
   backdrop colour, on a walk). It overlaps the feet: on that walk it began
   ten rows above the lowest paw pixel, so "below the lowest opaque row"
   leaves its top half. Take the band from 10 percent of the character's
   height above its lowest opaque non-key row down to the cell's bottom
   edge, per cell; in that band, an opaque key-hued pixel is made
   transparent. Nowhere else: the same test over the whole cell is rule 1's
   mistake again, and a character with feet in the backdrop's hue is the
   one case this rule cannot serve (say so, and skip it).
4. **Look before you show.** Crop one outline next to skin (or the
   character's lightest colour) from the cut-out and from the result, at
   2x or more, side by side; only when the halo is gone and the opaque
   pixels are byte-identical is the result shown to the user. A clean-up
   that changed an opaque pixel is a bug in the step, not a result to
   checkpoint.

Do not use "every semi-transparent pixel" as the test either: it recolours
the anti-aliased outline from the body and leaves a speckled edge.

Run it with Python 3 and Pillow, NumPy when present. Whether they exist is
the preflight's `tools` reading (`details.python`, `pillow`, `numpy`); on a
build whose doctor has no `tools` row, probe by hand with `python -E -c
"import sys;sys.path=[p for p in sys.path if p];import PIL"` (then
`python3`, and `py -3` on Windows, when that fails: the Windows Store stub
answers to `python` and prints nothing), and NumPy separately with the same
prefix and `import numpy`, since this step runs without it. `-E` ignores
`PYTHON*` variables and the first statement drops the current folder from
the import path, so a stray `zipfile.py` in the project is never run by a
probe; do not use `-I` for this, it also hides a Pillow installed with `pip
install --user`. Say which way the step is before
offering. On Windows without Python, PowerShell's built-in image library
(`System.Drawing`, in every Windows install) reads and writes the PNG and
its pixels, and the same recolour runs in seconds; a scripted loop over
`Bitmap` pixels is slow but the sheet is one image. Run it inline
(`powershell -NoProfile -Command "..."`, or a script block piped on stdin),
never as a saved `.ps1` that meets the execution policy: do not pass
`-ExecutionPolicy Bypass` and do not call `Set-ExecutionPolicy`, both change
a security setting nobody asked for. With ffmpeg and a Python
that lacks Pillow, ffmpeg dumps the PNG to raw RGBA (`-f rawvideo -pix_fmt
rgba`) and reads it back the same way, and plain Python runs the rules on
the bytes. Without any of these, this step is by hand in an image editor or
skipped; do not install anything.
The same holds for every free pixel step of this document (crop, scale,
the crop box of step 4): local first, with whatever the machine has, and
never a paid image edit for a resize. Output `sheet-cutout-clean.png`, never over the
cut-out. Its sidecar comes from `unity ai sidecar derive sheet-cutout-clean.png
--from sheet-cutout.png --edit edge-cleanup --detail "key #<hex>"` (the
removal's provenance still applies), so a later session knows the pixels
were touched after the generation. On a keyed sheet, where only rule 3 runs,
the output is `sheet-keyed-clean.png`, derived `--from sheet-keyed.png
--edit edge-cleanup --detail "shadow remnant"`: the key's values stay on
record in the edit before it. Preview it next to the cut-out at the same
`sheet` hint and check one cell at high zoom: the halo is gone and the
outline is unchanged.

Checkpoint, with the question tool: **keep** the cleaned sheet, **try the
paid edit** instead (below; the cleaned sheet stays on disk as a fallback,
the edit takes the original cut-out as its reference, not the cleaned one),
or **drop** it (delete `sheet-cutout-clean.png` and its sidecar; the cut-out
stands). The user has not seen the result when they choose the free way, so
the choice is made again here, on the result.

**Paid: an image edit.** `gemini-nano-banana-2-1` with `--ref sheet-cutout.png` and
a prompt of the form "remove the thin <colour> fringe along the outlines of
every sprite; keep every sprite, pose, size and position exactly as it is;
transparent background". Quote and consent as for any generation. Plan it
as three steps from the start, not one, and say so before the quote: the
model redraws the whole sheet, so frames can drift (check every cell against
the cut-out); it usually returns an opaque image on a background of its own
choosing, so a second `photoroom-bg-removal` on the result is the normal
second step: its input does not exist until the edit has run, so it cannot
be quoted with the first (Check every handoff and the Checkpoint rule in
SKILL.md); show it in the plan as a marked estimate, the model's typical
cost, and quote it with its own consent only after the user has seen the
edit's result at its checkpoint; and it may return the sheet at another
size, so the third step is a local scale back to the cut-out's exact pixel
size, or the grid no longer slices on whole pixels. This is the alternative for a fringe the free way leaves behind,
such as a translucent character whose own colour leans toward the key, or
the user's second choice after the free result's checkpoint. Output
`sheet-cutout-edit.png`; its sidecar is the one `generate` writes. Checkpoint
as for any generation: keep, Edit (a new prompt, another paid call) or stop,
and say which file is the final sheet in the report.

## Plan to propose

For "a sprite sheet of <character> <doing motion>", propose the plan before
the first quote and let the user trim it, with the quote of the first step
and the typical cost of the four video models from `models` as estimates,
marked as such, for the clip step 3 requests (MiniMax H3 about 72 for 5 s
at 768P, MiniMax H3 Fast about 32 for 5 s at 768P, Seedance about 161 for 4 s at 720p, Kling V4 about 84 for 3 s
at 720p; a longer or sharper clip costs more), so the user sees the recommended video's cost before paying for
the sprite. The model question itself, with the free quotes, stays after
the sprite checkpoint.

Two numbers, two uses. Consent is given on a quote's worst case, as
SKILL.md says, because that is the most the user can be charged. The route
is chosen on what a step typically costs: the catalog's cost for the model,
or the charge of a previous run in this folder's sidecars (`pointsCost`),
not on the quote's worst case, which can be many times the charge. For
Seedance, plan on its quote, which already follows the clip's length and
resolution (see its model bullet), rather than a past sidecar's charge for a
different clip. Report the settled charge as it is ("charged N"); do not
predict a charge above the quote.
Say both in the plan, per model ("MiniMax H3: plan on about 72 credits, H3 Fast
about 32, Seedance about 161, Kling V4 about 84, at most <worst case> if the service
charges the maximum"), and do not let a large worst case steer the user to the
one-image alternative on cost alone; its sheet is cheaper and usually
moves less (see What this sequence does not do).

**Preflight, before the first quote.** Free, seconds, and the failures it
catches otherwise cost credits:

- `models show gemini-nano-banana-2-1`, `models show video-seedance-2-5`,
  `models show video-minimax-h3`, `models show video-minimax-h3-fast`,
  `models show video-kling-v4-i2v` (and
  `photoroom-bg-removal`): the keys (`image` / `last_frame_image`,
  `first_frame_image` / `last_frame_image`, `start_image` / `end_image`,
  `generate_audio`, `duration`), the input limits, the duration range. A
  model missing from `unity ai models` still resolves with `show`; treat the
  listing and the quote as separate gates, as `models.md` says.
- The `tools` row of `unity ai doctor --format json`, read from its
  `details`, not from its code (the row carries one code for two tools, and
  ffmpeg's wins): `ffmpeg`, `ffmpegVersion` and `ffprobe` say whether step 4
  is a command or by hand (`ffmpegOnPath: false` with a path means a copy
  the running shell cannot see: run it by that path, and name the path to
  the user before the first run unless they installed it in this session;
  a path without an `ffmpegVersion` is `FFMPEG_UNUSABLE`, treat it as
  missing), and `python`, `pillow` and `numpy` whether the clean-loop
  search, the crop box and step 6 have Pillow (PowerShell's image library
  on Windows when Python is missing), and whether step 5's key runs with
  Pillow or falls back to ffmpeg's `colorkey` (it has no PowerShell path).
  Say which in the plan, and keep the
  recommendation of the chain either way (step 4, Without ffmpeg). On a
  build whose doctor has no `tools` row, or when the row itself failed with
  `DOCTOR_CHECK_ERROR` (advisory like the rest of the row, not a root cause
  to fix first), probe by hand: `ffmpeg -version`, and the isolated Python
  probes of step 6 (`-E`, the current folder dropped from `sys.path`, then
  `import PIL`; `python`, then `python3`, `py -3`).
- The four video models' catalog costs, for the plan. Step 2's questions are
  asked after the sprite checkpoint; the plan names the end-pose answer as
  the one that adds an image step.

1. Concept sprite: `gemini-nano-banana-2-1`, drawn as section 1 says (start pose,
   plain flat background, centred, or small and low for a motion that
   travels, the video's aspect). Checkpoint.
2. Video model question, then end frame question (section 2). Model
   recommended: `video-minimax-h3`, with the four quotes shown, H3 Fast
   offered for a walk, and Seedance offered when fast motion must stay sharp. End frame recommended: none. "A different
   end pose" adds an image step here, `--ref` on the approved sprite, with
   its own checkpoint.
3. Video, the model step 2 chose. Seedance: `--in sprite.png --in-param
   image`, `duration=4`. MiniMax H3: `--in sprite.png --in-param
   first_frame_image`, `duration=5`, `resolution=768P`; H3 Fast the same. Kling V4: `--in sprite.png --in-param
   start_image`, `duration=3`, `resolution=720p` (Kling i2v-pro, when the user
   names it: `aspect_ratio` the sprite's, `duration=3`, `negative_prompt` as
   section 3 says). All: prompt as section 3 says (on
   Seedance, H3, H3 Fast and Kling V4 with the exclusions in it), `generate_audio=false` (H3,
   H3 Fast and Kling V4 have no such key),
   the end frame only when step 2 asked for it. This is the last paid step of
   the normal plan. Checkpoint, with the contact strip read first.
4. Sheet: N frames (default 12, 4x3) over the range in which the character
   moves (found by the clean-loop search by default, or a range the user
   names from the contact strip), cropped to the character's region, 2048 px
   cap, 12 fps, locally with ffmpeg or by hand, plus the sidecar. Free.
   Checkpoint in the sheet strip; a re-sample offers the same three range
   answers.
5. Transparent background offered on the sheet: the flat backdrop keyed
   out locally (free, Python and Pillow, or ffmpeg's `colorkey`), and
   `photoroom-bg-removal`, one paid call, only when the key cannot do it.
6. Edge clean-up offered on the cut-out when a fringe shows: free with
   Python and Pillow, or a paid `gemini-nano-banana-2-1` edit. Checkpoint on the
   result: keep it, switch to the other way, or drop it.
7. Report every path (sprite, clip, sheet, keyed sheet or cut-out, clean-up), the cost of
   each paid step as quoted and as charged (the quote is an estimate; the
   charge, settled when the job finished, has ranged from well below the
   quote up to it, and can exceed it up to the accepted worst case),
   the org charged, the sheet layout, the range and fps, and the **Preview**
   block with the sheet selected.

## What this sequence does not do

- **No pixel-art pass.** A video model does not hold a pixel grid; if the
  user wants pixel art, the concept sprite is drawn in that style and the
  frames are what the video gives. Do not offer a pixelation step.
- **No Editor import settings.** Bringing the sheet into a Unity project,
  slicing it into sprites there and building an animation clip is the
  `unity-cli` skill's lane (SKILL.md, Bringing the result into a Unity
  project); this
  document stops at the file and its sidecar.
- **The one-image alternative** (a grid asked of the image model in one
  prompt, the model table in `models.md`) stays the cheap fallback for a user who
  wants no video: one call, weaker frame-to-frame consistency, cells that
  drift, and often fewer distinct poses than cells (an 8-cell walk with 4
  poses and 4 near-copies is a common result), so count the poses before
  calling it a cycle; the preview's Grid tool with its offsets helps line
  such a sheet up. Name it in the plan as the alternative, with its cost and
  that caveat; do not mix the two in one sheet.
