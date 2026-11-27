# Exit codes

Part of the unity-ai skill: `SKILL.md`, in the folder next to this file,
sends you here when a `unity ai` command exits non-zero. A section this file
names without a file (Troubleshooting, Known limitations, Generation
consent…) is a section of `SKILL.md`.

As of 2026-11-24:

- `0` success
- `2` bad arguments / unknown command; also `PROMPT_NOT_SUPPORTED` (`--prompt`
  on a model whose `params_schema` has no `prompt`: drop it, nothing was
  uploaded or quoted), `IN_PARAM_REQUIRED` (`--in` without `--in-param` on a
  model with no `asset_id` input: add the `--in-param` or `--ref` the
  remediation names), `INPUT_FORMAT_UNSUPPORTED` (a `--in` / `--ref` file of a
  type the model does not accept for that input, such as an FBX for a GLB-only
  rigging model: nothing uploaded or quoted; for an image, offer the free
  local conversion in "Converting an image" below; for another file, convert
  it to the type the message names, or offer that conversion to the user;
  then run it again),
  `PARAM_NEEDS_UPLOAD` (a local file given to an asset-id input as
  `--param <key>=<path>`: that key takes the id of an asset already on the
  service, so pass the file as `--in <file> --in-param <key>`, or `--ref
  <file>` for `reference_images`; an id from an earlier step still goes on
  `--param`), `REF_NOT_SUPPORTED` (`--ref` on a model with no
  `reference_images`: use the `--in-param` the remediation names),
  `IN_PARAM_REPEATED` (one `--in-param` key on more
  `--in` files than the input takes: one for a single asset id, the schema's
  `maxItems` for a list, counting ids already set with `--params`; nothing
  uploaded or quoted), `IN_PARAM_NOT_ASSET` (`--in-param` on an array of
  values such as `color_palette`: set it with `--params`, nothing uploaded or
  quoted) and `CONSENT_NEEDS_CONFIRMATION`
  (`consent set` without a terminal and without `--yes`, or an agent's `--yes`
  over limits confirmed at a terminal; nothing saved) and `BAD_PARAM` (a
  `--param` value for an array property that is not a list; nothing uploaded
  or priced, pass it as `--param "<key>=<id1>,<id2>"` or with `--params`)
- `3` auth (not signed in, token rejected, not a member of the org) — see the
  `AUTH_*` codes and `remediation[]` in Troubleshooting, in `SKILL.md`
- `4` needs configuration (no CLI, no default org); also the spending limits:
  `QUOTE_REQUIRED` (past them, nothing submitted, a ticket to approve),
  `QUOTE_TICKET_INVALID` (the ticket cannot pay for this run, nothing
  submitted) and `CONSENT_FILE_UNREADABLE` (the limits file is damaged,
  nothing spent; how to repair it is the user's call); `NO_SEAT` (no Unity
  AI seat is assigned to the user in an org that has a subscription: an
  owner or manager of the org assigns one; access is per user, so never
  offer `--org`) and `NO_SUBSCRIPTION` (either no seat or no subscription,
  or, when the message says so, definitely no subscription; which fix applies,
  and whether anything is to be bought, is in Troubleshooting, "Can't
  generate");
  nothing was charged (the preflight refuses before anything is uploaded or
  quoted; a `NO_SUBSCRIPTION` from `generate`'s submit comes after the uploads
  and the quote, still before any charge): relay the message and stop, since a
  retry is refused again; and
  `CLI_NOT_ENABLED`
  (the organization the message names, the working one or the one the Points
  Billing setting charges, is not enabled for `unity ai` yet; nothing was
  charged: relay the message, stop and ask the user, since an unchanged retry
  is refused again. The error's `refusedOrgRole` says which: `working`, switch
  `--org` only to an org the user names, never by guessing; `paying`, `--org`
  does not help, the user changes the Points Billing setting; `both`, both
  steps are needed, as either alone is refused again: ask the user for each
  (the org to switch to, and the setting change). Its `remediation` then
  lists only that fix; without the field, the message says which applies)
- `6` the request failed: the service answered with an error
  (`COMMAND_FAILURE`, stderr carries the error and a `traceId`), a retired model
  (`COMMAND_FAILURE` whose `error` is `ModelRemoved`, nothing charged: relay the
  message and never retry that model; the error's `replacementModelId`, when
  present, is the model to use instead, so offer it and quote again with it), a parameter
  value or combination the model refuses (`COMMAND_FAILURE` whose `error` is
  `ModelParameterValidationFailed`, nothing charged: the message names the parameter and
  what is wrong with it, with the accepted values for a range or a list, so change that
  parameter and quote again; if it names no parameter the user set, relay the message and
  stop), an upload was
  refused before the request that spends (`UPLOAD_FAILED`, nothing charged), an input over
  the model's size limit (`INPUT_TOO_LARGE`: refused before upload or submit,
  nothing charged, so make the file smaller and run it again; or refused by the
  provider after submit: with `pointsCost: 0` the hold was released, run it again
  with a smaller file; without it the job may still be charged, so never run the
  same request again, keep the `jobId`, and make a new request with a smaller
  file, with its own quote; the same file is refused again either way), the generation
  request got no answer and may have been charged (`SUBMIT_UNCONFIRMED`,
  never retry blindly), a content filter blocked the job
  (`CONTENT_BLOCKED`, not charged, see Known limitations), or — after the charge — a job's asset could not be
  fetched or written (`DOWNLOAD_FAILED` / `WRITE_FAILED`, with the `jobId`,
  `assetId` and `orgId` that recover it; other jobs of the same generation still
  complete), or a job still running past the poll budget (`POLL_BUDGET_EXCEEDED`,
  with its `jobId`: not cancelled, may still be charged, never re-run the
  request; save it with the `jobs status` command in its remediation). From `jobs status`, 6 is a failed or blocked job (running
  it again only repeats the job's own error; for `CONTENT_BLOCKED`, see Known
  limitations), or a finished job's asset that could not be fetched or written
  (`DOWNLOAD_FAILED` / `WRITE_FAILED`): only for those two, run the command in
  the error's remediation again with a free `--out` (nothing new is charged),
  or a `COMMAND_FAILURE` whose remediation says the job's state is unknown
  (the service answered the wait or its follow-up read with an error): run the
  same `jobs status` again, and never re-run the generate that submitted it;
  also `CONSENT_FILE_BUSY` (other runs kept the limits file in use: run the same
  command again, never clear the limits for it) and `CONSENT_FILE_UNWRITABLE`
  (a change to it could not be written: check permissions, then retry);
  for `feedback`, `FEEDBACK_UNCONFIRMED` (it may be recorded: never resend,
  relay its `FeedbackId`); for `sidecar derive`, `FILE_UNREADABLE` (the new
  file or `--from` could not be read to hash it) and `WRITE_FAILED` (the
  sidecar could not be written) are local and charge nothing: fix what stderr
  names, then run the same command again
- `7` a free call (catalog, quote, balance, `jobs status`, also while it
  waits) got no answer from the service (`NETWORK_UNREACHABLE`); nothing was
  charged by it, retry is safe; for `feedback`, its request body was never sent
- `75` `jobs status`: the job has not finished yet. Without `--wait`, read it
  again later or save it with `--wait --out <path>`; with `--wait`, its
  21-minute wait ran out on a job still running (`JOB_NOT_FINISHED`, nothing
  failed and nothing new is charged): run the same command again.
  `generate` reports a job past its wait as `POLL_BUDGET_EXCEEDED` (exit 6)
  instead
- `77` insufficient Unity Credits (`INSUFFICIENT_POINTS`, nothing was submitted).
  The balance is checked against the quote's WORST CASE, not the quote: a
  user with 200 credits can be quoted 185 and still be refused when the worst
  case is 243. Relay the available credits and the worst case from the
  message, and say the full worst case must be available to start the job
  (it is held while the job runs; the charge itself is usually far lower).
  Where the credits come from: Troubleshooting, "Can't generate"
- `78` the user has not accepted the Unity AI terms of service
  (`TOS_NOT_ACCEPTED`, nothing was uploaded, quoted or charged; give the user
  the dashboard URL from the error and stop, never accept for them)
- `79` `jobs status`: no job by that id is visible (`JOB_NOT_FOUND`): another
  org (pass the `--org` the generation ran in), another user, an id copied
  wrong, or a job submitted seconds ago
- `6` with `MODEL_NOT_FOUND`: the model id does not exist (a typo, or a model
  removed from the catalog). Nothing was quoted or charged: take an id from
  `unity ai models`, or the nearest ids the error lists, never guess another
- `130` user declined the confirmation, chose to upgrade first at the update check's question (nothing spent), or Ctrl-C

On any non-zero exit, capture stderr and include it in what you report. If the
remediation did not fix it, or the failure makes no sense, run `unity ai
doctor --format json` (Troubleshooting, in `SKILL.md`) before trying anything else. For
exit 6, relay the `traceId` to the user — it is the only support-actionable
evidence — and, after a charge, the `jobId`, plus the `assetId` when the
run got as far as emitting one: the asset still exists server-side. An error
carrying `billingFailed: true` is a job that completed but whose credits charge
could not be confirmed: say the charge is unconfirmed, never that the credits
were spent or that it was free. Never re-run a `generate` that exited 6 after `submitted`
(the two exceptions follow this paragraph); the
job may be charged. What you offer instead, as one question with buttons, is
fixed, and the first option comes first: **save it** (free, no new charge:
`unity ai jobs status <jobId> --wait --out <path>` for each `jobId` the
output showed without a `done`, with the same `--org` and `--model` and a free `--out`; it
waits for a job still running, exits 75 if it is still running after 21
minutes (run it again), and exits 6 with the job's own error when the
job itself failed), **generate again** (a new job and a new charge, which a
session budget does not cover, so it gets its own quote and consent), or
**stop** (report the `jobId`, and the `assetId` only when the output
carried one: a token expiry or a status failure before the asset response
emits the `jobId` alone, and an id you did not see is one you must not
write; say that the credits were spent on an asset the service still holds).
For `WRITE_FAILED` the cause is local (a full disk, a locked or read-only
`--out`, a permissions error, named on stderr): say it, and have the user
fix the target or choose a writable `--out` before saving it again. A build
whose `unity ai help` has no `jobs` command answers it with exit 2: offer
`unity plugin upgrade ai` for it rather than any other recovery, and never
present a re-run as a retry of the same job.

Two kinds of failed job are exceptions to that menu, and only when they are
the run's only errors (`blockedJobs` plus `releasedJobs` equals `failed` in
the summary). Both were not charged (`pointsCost: 0`):

- `CONTENT_BLOCKED`: refused by a content filter. Say so
  plainly, quoting the filter's reason, then follow Known limitations,
  Content filters: it says which revised prompt to offer and that it runs
  only after the user says yes.
- Released (`jobStatus: "Failed"`, counted in `releasedJobs`): the service
  failed the job before its deadline and released its credits hold. Say so,
  check `unity ai credits`, then offer the same request again as a new
  generation under the usual quote and consent; it runs only after the user
  says yes. A failed job without that marker is not released, whatever its
  message says. One released failure is the exception to offering the same
  request: when the message says the model ran out of room before it finished,
  the request asked for more than the model can produce in one result. Running
  it again unchanged may fail the same way, so do not offer it. Offer a smaller request instead: fewer figures or frames per image,
  a shorter prompt with fewer rules, or, for an animation, the sprite-sheet
  sequence (`sequences/image-to-spritesheet.md`: one sprite, a short clip of it,
  the frames sampled into a grid) instead of drawing every frame in one image.

When the run also had other failures, or delivered some jobs (`done`
events), report the delivered files and apply the rule above: a full re-run
would charge the delivered jobs again.

## Converting an image

When `INPUT_FORMAT_UNSUPPORTED` names an image the model does not take (a
WebP, AVIF, BMP, TIFF or GIF where it accepts PNG or JPEG, say), offer to
convert it locally before anything else. It is free and quick, but it
writes a new file, so ask first: name the source, the format and the path
it writes, and run it only after the user says yes.

It needs a Python with Pillow, the `tools` row of `unity ai doctor`
(`PYTHON_IMAGING_MISSING` there means it is not installed: give the user
the row's install line and let them choose, or let them convert the file
in their own editor). With Pillow present, write the copy beside the
original, never over it or over any other file, in the first format the
error accepts, PNG when it takes PNG. Before the ask, check the target path:
when `<source name>.png` (or its `.unityai.json`) already exists, it is
another file the user keeps, so pick a free name (`hero-converted.png`,
then `hero-converted-2.png`) and name that path in the ask. The command
refuses an existing target all the same:

```
python -c "import os, sys; from PIL import Image; os.path.exists(sys.argv[2]) and sys.exit('exists: ' + sys.argv[2]); im = Image.open(sys.argv[1]); im.seek(0); im.save(sys.argv[2])" "<source>" "<target>.png"
```

Use the interpreter the `tools` row names in its `details` (`python3`, or
`py -3` on Windows, where `python` is not it). For JPEG, which has no
transparency, convert the image first (`im.convert('RGB')`) and tell the
user its transparent areas lose their transparency; prefer PNG when the
model takes both. An animated GIF or WebP keeps only its first frame: say
so. An older Pillow may not read AVIF, and none reads HEIC without a
plugin: when `Image.open` or `save` fails, relay its message and offer the
user's own editor instead. When the source was generated (it has a
`.unityai.json` sidecar beside it), give the copy its own with `unity ai
sidecar derive <copy> --from <source> --edit format-convert --detail "<old>
to <new>"`; a user's own image has none, and the copy needs none. Then pass
the new file to the same `quote` or `generate`, which
quotes again as usual, and keep the original untouched.
