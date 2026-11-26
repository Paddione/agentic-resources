# Sequence: where a biped motion comes from

A user who said not to ask (SKILL.md, When the user says not to ask): every question
this file has you ask, but money, is your own call; say what you chose in the final reply.

This holds for any biped motion step, after a rig (`rig-and-retarget.md`)
or alone. A biped motion comes from text (`uthana-text-to-motion-3`, the
default), from the user's own clip (`uthana-video-to-motion`), or it can be
acted out: a generated video of an actor doing the move, converted with
video to motion (`generated-video-to-motion.md`, read only once the user
picks it). The agent does not choose that route on its own. It is offered
at two points, and the user picks. Every Uthana model is biped only; a
creature that is not a biped follows `creature-rig-and-animate.md`.

**The source**, asked once with the question tool when the plan is
proposed, since the answer changes its steps and cost: with the rig plan,
before the rig is quoted, when a rig comes first; else before the motion
is quoted. Only when the request does not already say: a user who attached
or named a clip, or named text to motion or acting it out (a generated
video of it), has answered, and the motion step goes ahead on that answer
without the question. Describing the move ("a tired walk") is not an
answer, since every request does that, and neither is asking for video to
motion without a clip: that still chooses between Use my clip and Act it
out. The question:

- **Describe it (Recommended)**: text to motion, one generation.
- **Use my clip**: the user's own video, converted as is.
- **Act it out**: `generated-video-to-motion.md`. Charges about 2.5 times
  text (about 140 credits for the first motion against 49 to 61), and its
  quotes and worst case are higher too (three paid steps); the take is shown before it is converted, and it suits a posture,
  a style or a balance move better than precise steps.

Text stays the recommended answer whatever the ask: the third answer adds a
choice, it does not move the default.

**The motion checkpoint** (Use it / Edit / Stop on a motion result, text
or video to motion, that ends a sequence, the last step included; a motion
generated on its own gets one closing line instead, as SKILL.md's
Checkpoint between steps says: for a text result, revise the prompt or act
it out; for a result from a clip or a take, another clip or take, or text
to motion). A "without stopping" waiver covers this checkpoint too, and the
reply carries that closing line. When the user rejects a text result, Edit offers two
answers: **revise the prompt** and **act it out instead**. Mark one
Recommended from the user's own reason for rejecting, not from the agent's
reading of the motion:

| The user says the result is wrong in | Recommend | Why (trial, 2026-10-07) |
|---|---|---|
| Its posture, style or mood ("hunched", "too generic", "not tired enough") | act it out | video led by about 21 points; text leaned walks and idles 8 to 16 degrees forward and drifted to a generic idle |
| Its balance ("floats", "sinks", "fell over") | act it out | video led by about 8 points, a small lead from one trial and inside its noise (one more sample moves a score by about 25); text floated or sank the body by 15 to 25 cm and turned a stumble into a fall onto the hands |
| Its count, side or order ("two jumps", "wrong leg", "punches swapped"), or anything else | revise the prompt | text led by about 21 points on exact moves; a video model makes these same mistakes and the conversion copies them, while a prompt that states the move precisely fixed them more often |

The trial: 12 motions, two samples per route, Uthana's default character.
Overall the routes tied (about 76 of 100 each).
