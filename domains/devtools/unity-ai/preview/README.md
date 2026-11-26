# Asset preview page

`index.html` is a single static page that previews assets produced by
`unity ai generate`; `open.mjs` is the one-command launcher for it (see below).
No build step, no server: open it straight from disk in
any Chromium-based browser (Chrome, Edge, the browser panes of AI clients)
and point it at the generated files. Local images, audio and video need no
network.

The page itself makes one kind of outside request: the 3D, skybox and material
viewers load three.js 0.160.0 (MIT license) from the public unpkg CDN,
`https://unpkg.com`, the first time one of them is shown. Like any CDN, unpkg
sees that request. Every module, transitive imports included, is
integrity-pinned in the import map, so a tampered download is refused. Offline
or with the CDN blocked, those three viewers report that the library could not
be loaded and everything else keeps working. The page fetches nothing else on
its own: the Appearance panel's font choices use a font only when it is
installed on the machine. An asset you point it at by an `http(s)` URL (a
remote `?file=`, for instance) is loaded from that URL's host, as any web page
would.

It exists so that an AI agent can *show* a result instead of describing it,
and so nobody has to write a throwaway HTML page per generation.

## Opening it

Pass the asset path in the query string. Windows and POSIX paths both work,
as do `file://` URLs. Paths relative to the page work only when the page is
opened from disk; served by `serve.mjs`, the page has no folder of its own, so
use absolute paths there (relative paths inside a `gallery.js` still resolve
against that file's folder).

```
index.html?file=C:\Users\me\Desktop\frog.png
index.html?file=/Users/me/Desktop/frog.png&file=/Users/me/Desktop/frog-2.png
```

From a terminal:

```bash
# Windows (cmd / PowerShell)
start "" "file:///C:/path/to/preview/index.html?file=C:/out/frog.png&model=gemini-nano-banana-2-1&cost=12"
# macOS
open "file:///path/to/preview/index.html?file=/out/frog.png&model=gemini-nano-banana-2-1&cost=12"
```

Quote the URL: `&` is special to every shell.

You can also drop files onto the page, or use **Add…** → **Add files** (type paths, or
browse with the icon) or **Add folder** (type a folder path, or browse,
optionally with subfolders; a browsed folder waits in the dialog for **Add**, so
the subfolder choice can still be made). A dropped folder asks the same subfolder
question first, then opens as a folder (Chromium-based browsers; Firefox has
no folder handles). What shows out of a folder is the Library setting's call:
files with a sidecar, or every file the viewer can show (Settings → Library,
or `?all=1` for one visit); a file you add yourself always shows. A browsed or dropped
folder is read by the page itself, sidecars included, so it works even from
`file://`. Dropping an asset together with its `<asset>.unityai.json`
sidecar fills the generation panel automatically. Browsers hide the location
of picked or dropped files; when served, the page asks `serve.mjs` to search
the folders it already shows, then your Downloads, Desktop, Documents,
Pictures, Videos, Music and OneDrive folders (or the `--root` folders) for a
file with the same name and size, which also finds its sidecar.
Assets loaded by path (`?file=`, `gallery.js`, typed paths) need no search.
The search also runs when a picked file or folder is added, so real paths and
sidecars show up in the details panel by themselves.

## One command for any client: `open.mjs`

`open.mjs` is the launcher an agent (or you) runs after a generation. The
`unity ai` CLI runs it for you: `unity ai preview <file-or-folder>…` takes the
same arguments and runs the copy shipped beside the binary, so no skill path is
needed (and without Node.js it still prints the `fallback:` URL). It
starts `serve.mjs` when no instance answers on the port, scoped to the folders
of the files it is given, reads the sidecar, and prints the two URLs that
cover every client, plus status lines when there is something to say:

```bash
node open.mjs C:/out/frog.png --orgName my-studio
# preview:  http://127.0.0.1:8380/?file=C:/out/frog.png&orgName=my-studio&dir=C:/out
# fallback: file:///…/preview/index.html?file=C:/out/frog.png&orgName=my-studio&modelId=gemini-nano-banana-2-1&pointsCost=12&…
# server:   started serve.mjs on port 8380, serving files under C:\out
```

Every line is `<key>:  <value>`; the keys are `preview`, `fallback`, `server`,
`note` (something worth knowing, not fatal), `browser` (with `--open`) and
`sidecar` (a sidecar that is not JSON). All of those go to stdout; a failure
uses the same keys on stderr and a non-zero exit.

- Give the `preview:` line to a browser tool that loads `http://localhost`
  (Claude Desktop's pane, the Codex / ChatGPT desktop app's `@Browser`), or
  add `--open` to launch the default browser on it (`start` / `open` /
  `xdg-open`).
- The `fallback:` line needs no server: it is the page from disk, with the
  sidecar fields already in the query, since a `file://` page cannot read a
  sidecar itself. Several files each keep their own fields (through the
  page's `items=` parameter), so no asset is shown with another one's model,
  cost or ids. `--open` falls back to this URL when the server could not
  start.
- Several paths show several files; a folder path becomes `dir=`. When every
  file given lives in the same folder, the `preview:` URL also carries that
  folder as `dir=` after the files, so the new files are selected and the
  folder's other generated assets stay listed even in a fresh browser tab;
  `--no-dir` shows the given files alone. `--root <dir>` adds a folder to
  what the server may serve, on top of the folders the shown files live in (a
  running restricted instance is widened too) — for a material whose maps
  live elsewhere. `--port <n>` changes the port. Any other `--key value` pair
  is passed through as a query parameter (`--sheet 4x2`, `--modality skybox`).
- Exit codes: `0` a URL was printed and every requested step worked; `1` the
  server was wanted and did not start, or `--open` could not launch a browser
  (the URLs are still printed); `2` bad arguments, including a missing or
  unreadable path, `--file` / `--dir` passed as flags (files and folders are
  plain arguments), and a file sitting at the root of a drive, which the
  launcher refuses to serve (`serve.mjs --all` is the explicit way to serve a
  whole drive).

Known client limits the launcher works around: Claude Desktop's pane renders
`file://` pages as static snapshots; the Codex desktop app's browser refuses
`file://` on Windows and may need `127.0.0.1` allowed once in its Settings >
Browser; Codex CLI has no browser and asks for approval before `--open` can
run the opener outside its sandbox.

## Inside an AI client's browser pane (optional server)

Some clients' built-in browser panes only run JavaScript for `http://localhost`
pages and show `file://` pages as static snapshots (Claude Desktop does this;
the Codex desktop app refuses `file://` outright on Windows).
For those, `serve.mjs` is a dependency-free Node script that serves this
folder on loopback, exposes local files read-only under `/fs/`, and lists
folders under `/ls/` for `?dir=`:

```bash
node serve.mjs 8380 --root C:/out
# then open http://127.0.0.1:8380/?file=C:/out/frog.png&model=gemini-nano-banana-2-1&cost=12
```

The `?file=` contract is identical to the `file://` case; the page rewrites
local paths to `/fs/<path>` when it notices it is served. Running the script
again while an instance is up exits immediately with "already running", or adds
the new `--root` folder to the running instance.
`--root <dir>` (repeatable) is required and limits which folders it will serve,
list, search or write to. `--all` instead serves any local file you can read;
any local process can talk to a loopback server, so that mode is opt-in. In
every mode: loopback only, requests from other origins or local ports refused,
network paths refused, served files never run as the page's origin, and only
`gallery.js` is served as a script.

The page itself can never add a folder: `POST /__root` refuses browsers, since a
folder's `gallery.js` runs as the page's origin. A folder typed into **Add a
folder** that the server does not serve gets a status naming the served folders
and a **Copy add command** button (the command is in its tooltip, not in the
status): `node open.mjs "<folder>" --root "<folder>" --port <port>`, which
widens the running instance on that port. When the server no longer answers,
the command also passes the served folders as `--root "<served>"...`, so it
starts the server again with the same roots; a live server keeps its own, and
a served folder deleted since would otherwise stop open.mjs at `not found:`.
On Windows the folder needs its drive (`/out` would be on the terminal's
drive, not necessarily the server's). The user runs it, or asks their agent to.
While the status is up, the page asks for the folder every two seconds (for up
to ten minutes, while the tab is visible) and lists it as soon as the server
serves it, so no second Add is needed. If the server refuses it for another
reason meanwhile (renamed, unreadable) or ten minutes pass, the status says so
instead. The server refuses by where a path would be, before
looking for it, so the status also comes for a mistyped folder or a file: the
folder is a `--root` too, so open.mjs stops at `not found:` or `--root needs a
folder` instead of serving a file's parent. Only a folder typed into the page
gets that command: a `?dir=` link to an unserved folder shows the plain error,
and a relative path or a whole drive gets no command. That is not a security
check, since a folder's `gallery.js` can fill and submit the dialog or draw a
notice of its own; the agent therefore builds the command from the folder the
user names, never from what the page shows (see SKILL.md).

The server does not stay around for ever: it exits after 60 minutes without
a request (`--idle <minutes>`; `0` keeps it up until stopped, which is for a
user who asked for that, never a default an agent picks). A visible page pings it
every 5 minutes, so a tab you are looking at keeps it alive, and shows
"Preview server stopped" as a notice at the foot of the viewer when a ping fails, with the `open.mjs`
command (this folder's launcher, the tab's folders, the port, the same `--idle`)
and a Copy button so you can restart it yourself. An asset opened after that,
whose bytes the page could not fetch from the server says the server stopped
instead of a load error (a file that arrived but does not decode, or a dropped
file, keeps its own message), and loads by itself once the server answers
again. A hidden or closed tab lets it go. `open.mjs --idle <minutes>` passes the limit on to the server it starts,
or sets it on the one already running (`POST /__idle`); the limit then stays
on that server across later runs, and `--idle default` puts the default back.
A server from before this lifetime existed is not reused, since it can neither
be stopped from here nor made to exit: the launcher starts on the next free
port, prints that preview URL, and names the old process for you to end.
`node open.mjs --stop` (or `POST /__quit` from a local process) stops the
server at once; it sweeps the same port range the launcher may have moved
to, so it finds the server wherever it landed. The next `open.mjs` run
starts it again, and its `server:` line says why the previous server on that
port stopped: by itself (`no request for 60 min`), with `--stop`, in a crash
(its error line), or without saying why, when its process was closed from
outside (with the app that started it, by a kill or by a restart). A preview URL
alone cannot start a stopped server; run `open.mjs` again for a working one.

You never need the server when opening the page in a normal browser.

### What the server writes

Only one route writes anything: `POST /annotate`, behind Annotate → **Save and
copy for the agent** (and **Save image with marks** in the image's menu). It writes exactly two names next to an existing,
allowed image — `<image>.annotations.json` and `<image>.annotated.png` — and
never touches the image itself. Everything else is read-only.

The server's console output (its start lines, the folders it serves, and the
line saying it stopped and why, or a crash's error) goes to
`unity-ai-preview-<port>.log` in the temp folder when `open.mjs` started it,
appended and started over past 256 KB. `open.mjs` writes that file, by
handing the server the file as its output; the server opens nothing itself.
No request is logged; the only file paths in it are the folders it serves
and the annotation files Save writes. A log that is not a regular file owned
by the user (a symlink, or a file another user created in a shared `/tmp`) is
neither read nor written, and the server then runs unlogged.

### The URL follows the view

Folders and files added through the page (Add… → Add folder or Add files, the
folder picker, drops once their path is known) are written back into the
query string as `dir=` and `file=`, so a reload or a bookmarked link brings
the same set back. Removing an asset from a listed folder keeps the folder
listed and names the file in `hide=`: the folder's listings skip it, also after
a reload, while files added to the folder later and **Include subfolders**
still apply. **Settings → Library → Show removed (N)** brings the removed
files back, as does naming one again (`file=`, Add files) or `&reset=1`.

The view also sticks to its tab: opening another `?file=` URL in the same
tab (an agent showing the next result) adds that file to what the tab
already showed and selects it, instead of replacing everything. Add
`&reset=1` to start from a clean view.

### A file rewritten in place

When the tab comes back into focus (from the terminal or the editor), the page
lists its folders again. A file with a new size or modification time, such as a
sprite sheet a clean-up step rewrote under the same name, then shows its new
bytes: the tile, the opened view, and any material or model that uses it (a
map, a texture or a buffer beside a model). Files that appeared meanwhile join
the library, and so does a file whose sidecar was written since. The check
leaves the selection and the status line alone, and runs at most once every
two seconds.

## PNG files, and a page with the asset in it: `unity ai preview --png`

An agent that can only read an image, or one whose preview opens in a browser it
never sees, gets the preview as PNG files:

```bash
unity ai preview C:/out/frog.glb C:/out/croak.wav --png --format json
```

For each asset the CLI writes a copy of this page with the asset (and its
sidecar) embedded as base64 blocks at the top of `<head>`:
`<script type="application/octet-stream" data-embed="asset|sidecar" data-name="…">`.
A page opened from disk cannot read a local file, but it can read its own
content: at start-up the blocks become files handed to the same path as a drop,
so the 3D viewer, the waveform and the sidecar's fields all work with no
server. A model's companions go in too, under their path relative to the model
(`data-embed="companion"`): a `.gltf`'s buffers and images, an OBJ's `.mtl` and
the maps it names, the images an FBX names beside it or in its `.fbm` folder. The
loaders ask for them beside the model, and the page answers from the embedded
copies. A motion saved without its mesh gets its character embedded too
(`data-embed="character"`, with `data-how="given"` for `--character <file>` or
`"sidecar"` for the glTF or GLB beside it whose sidecar's `partnerResultId` is the
motion's `params.target_character_id`; a `.gltf` character's own buffers and
images go in as `data-embed="character-companion"`, under their path relative to
it and apart from the motion's), and is drawn on it as in the viewer (3D
models, below): every view, the motion views included, is then of the character
playing the clip, and `details.onCharacter` gives the character's `file`, how it
was `found`, and how many of the motion's `channels` were `matched` to its nodes
(or `why` it was not used). Double-clicked, that copy is the full preview.

The CLI then opens the copy with `?capture=1` in a headless Microsoft Edge or
Google Chrome it starts for the run (its own empty profile, driven over the
DevTools protocol) and calls `window.unityAiCapture(views, { clips })`. The page draws each
image into its own canvas at a fixed size and returns it as a PNG data URL, so
the images hold no panels and do not depend on a window. `--views <name>,...`
picks the images (the agent asks for the ones that answer its question); without
it, a sound gives `waveform` and `spectrogram`, a model `view` and `turntable`, a
panorama its `view`, an image itself (and its `view` when it is a panorama), a
video its `frames`; `exposure`, `seam`, `sheet`, an image's `silhouette` and a
model's `gloss`, `rig`, `poses`, `path`, `feet`, `pivots` and `sweep` are drawn only when asked for. `--clip <name|index|all>` (repeatable)
picks the clips a model's motion views are drawn for: a clip's name (exactly, else the one clip whose name matches
ignoring case), its index from 0 in `details.clips`' order, or `all`; repeats collapse. Without it, the motion views
are the first clip's, as before. With it, each chosen clip in turn is played as the viewer's clip menu plays it and
gets its own `poses`, `path` and `feet`, written as `<stem>.<view>.clip<index>-<name>.png` with `clip` (`index`,
`name`) in the image's manifest row (a skip of a motion view names its clip too), and `details.motionByClip` lists
every chosen clip: `index`, `name`, `duration`, and its `motion` numbers (below), or `why` they could not be read.
`details.motion` stays the first chosen clip's. Asked for without `--views`, a model draws its defaults and the three
motion views; with `--views`, at least one of them must be named. A clip the model has not fails that asset with the
clips it has (`0 stand, 1 Walk Cycle`); a model with no clip draws its other views and lists the motion views in
`details.skipped`, as without `--clip`. Each asset draws the names its kind has and
leaves out the others; an asset that has none of them fails with the list of its
own. A model view the model cannot have (`skeleton` with no bones, `parts` with
one mesh, `uv` with no UVs, `rig` with no skinned mesh, a motion view with no clip,
`feet` with no limb that reaches the ground, `sweep` with no moving part) is left out and listed in `details.skipped` with why
(a `skip:` line in the text output); when every view asked for is one of those,
the asset fails with the reasons.

| Asset | Images |
|---|---|
| image | `image`: itself over a checkerboard, at most 1024 px on its longer side, never enlarged · `sheet` (a sprite sheet): the frames cut on its grid (`--sheet 4x2`, or the sidecar's `sheet`; `frameCount` drops spare cells), 1536 px wide at most and up to 4 times enlarged without smoothing, each on the checkerboard with its index (0 first, as Unity names a sliced sheet's sprites), the box of its opaque pixels and the frames' common baseline dashed; an empty frame is outlined in red · `silhouette` (a concept's pose, on a transparent background): the image over the checkerboard with a line every other band of 40 across the silhouette, each labelled at the right with how many separate pieces it cuts (two legs apart: 2; arm, body, arm: 3), the widest row in blue; an image with no transparent background is skipped |
| sound | `waveform`: 1200 × 240, the name, duration, channels and peak, a dBFS scale (0, −6, −12, −24), clips in red, the silence at both ends shaded with its length · `spectrogram`: 1200 × 400, 20 Hz to 20 kHz on a log scale over time, colour from −100 to 0 dBFS (a full-scale sine is 0) · `loop`: 1200 × 300, the last and first 30 ms side by side as the signal itself, joined at the loop point, with the jump there · `loudness`: 1200 × 240, short-term loudness (3 s, ITU-R BS.1770) every 100 ms from −60 to 0 LUFS, the integrated value dashed |
| video | `frames`: eight frames evenly spaced, 4 × 2 tiles of 320 × 240, each with its time |
| 3D model | `view`: 1024 × 768, the view the viewer opens on; `turntable`: eight views 45° apart around the vertical axis, 4 × 2 tiles of 320 × 240. The clip stays on its first frame and nothing spins, so two runs draw the same pictures · `gloss` (asked for by name, never by default): the material check, 1536 × 1648, three rows (the front, a three-quarter view 35° around, the top third up close, where a character's face is) by three columns, the model's roughness times 1.0, 1.5 and 2.0, each a 512 × 512 tile on grey in the viewer's lighting plus a key light by the camera, so a glossy surface catches a highlight; `roughness` lists the factors. three multiplies the roughness map by the material's roughness and clamps at 1, as glTFast's `roughnessFactor` does in Unity, so a column shows that factor on import: where x1.0 looks wet or plastic and x1.5 or x2.0 reads right, the map is too glossy for the material. It renders its own copy of the model, in the bind pose, so the view's materials are unchanged · `uv`: 1536 × 768, the UV layout (every mesh's triangles at their UV coordinates in the 0–1 square, over the colour map when there is one; stacked islands show brighter, and the outlines are left out above 50,000 triangles; with no colour map the islands are laid over rather than added up, since meshes coloured by their materials may share the square harmlessly; meshes whose materials use different colour maps get a square per map, up to 4, labelled with their materials) beside the model wearing a lettered checker in place of its materials · `skeleton`: 1536 × 768, the bones over the mesh as a ghost, from the front (+Z) and the side (+X), named up to 30 bones · `parts`: 1024 wide, the model taken apart (each mesh moved away from the centre; a rigged mesh stays where its bones put it), then the 16 largest meshes alone in 256 × 192 tiles, numbered as in `details.parts` · `materials`: 1024 wide, one sphere per material (up to 12) with its colour, metalness, roughness and maps · `rig`: 1024 × 768, does each limb own its skin: four 512 × 384 tiles, front, side and the convention's view with the mesh see-through, each vertex coloured by the limb whose 30° bend moves it most (grey: the body) and the bones over it, then every limb bent at once, solid · the motion views, of the first clip (the one the viewer opens on; `details.motion.clips` counts them): `poses`: the clip at eight evenly spaced times, 4 × 2 tiles of 320 × 240 with the bones over the mesh, each tile labelled with its time (`times` in its row); each tile follows the model at one scale for all, the largest pose's · `path`: 1536 × 768, the hips' path from above and from the side (along the way it travels, with the floor as a line), the feet's paths faint beside it, the start green and the end red, on a metre grid · `feet`: 1536 × 768, each leg's foot height over the clip against the floor: the green band is on the ground, the red area under it, each leg named with whether it moves, its lowest point and its slide · the moving-part views (asked for by name, never by default), for a model split into rigid parts whose nodes carry a motion in their glTF extras (`{"unityAi": {"motion": {"axis": [x, y, z], "range": [min, max], "spin": bool}}}`, as the model-to-parts sequence writes them): `pivots`: 1536 × 1024, the model in three orthographic views (front from +Z, side from +X, top from +Y), 512 × 512 each, with a grid in the file's own units labelled on the edges, textured on the top row and each moving part in its own colour on the bottom row (grey: what stays) with its pivot as a dot and its axis as a line; a model with no moving part gets the same layout, to read a box's corners off · `sweep`: each moving part, one row of four 320 × 240 tiles, turned to the start, middle and end of its range and back to 0 (a spinning part to 0, 90, 180 and 270°; a part whose file gives no range at -30 to 30, labelled so, and `range: null` in the details), the rest of the model at rest, at most 8 rows |
| panorama | `view`: 1024 × 576, the viewer's opening view; a 2:1 image a skybox model made gets its `image` and this `view` · `exposure` (`.hdr`, `.exr`): the whole panorama flat at −2, −1, 0, +1 and +2 EV through the viewer's tone mapping, five 1024 × 512 rungs, its range written on the 0 EV one · `seam`: 1024 × 512, the right edge against the left edge, full height, joined at a dashed line and stretched across, so a step where the panorama wraps shows |

`unityAiCapture()` never rejects: it returns `{ ok, error, details, images,
timing }`, where `details` is what the details panel says, as data (size,
duration, channels, mesh statistics, bounds, clips (`animations`: the names; `clips`: each name and `duration`), the gap to the ground,
missing textures) and `timing` the milliseconds each step took. A model's
`details.camera` is the convention's camera (below); with `uv`, `parts` or
`materials`, `details.uv` (`withUv` of `meshes`, the meshes `missing` UVs, and
`outsideUnitSquare`, the share of UV coordinates outside 0–1, and `textureSpaces`, how many colour maps the meshes use), `details.parts`
(each mesh's name, triangles, materials and whether it is rigged) and
`details.pivots` (with `pivots` or `sweep`: each moving part's name, pivot and axis in model space, and its range as the file gives it (null when none) or `spin`; the pivots image's row carries the model's `bounds` and the sweep's the `parts` and angles drawn), `details.materials` (name, colour, the metalness and roughness factors, opacity
and maps; a map whose image never came in says `(not loaded)`) list what those
views drew. A generator leaves the factors at 1 and puts the values in the maps:
`metalnessFromMap` and `roughnessFromMap` are the median of the whole map (blue
and green, as glTF packs them) times the factor, and the sphere's label shows them,
marked `map`. The median takes in the padding between islands too, so an atlas
with wide black padding, or a small metal part on cloth, reads lower than the
surface it paints: confirm on the sphere. With `rig`,
`details.rig` gives `bones`, `limbs` and `legs`, each limb's `movedShare` (the share
of the mesh its first bone's 30° bend moves, about two axes across the bone so a
bone that runs along its own X still bends, in `limbList`; a chain whose branches are all under half its
length, a hand or a paw, is bent whole with them), `maxLimbShare` (the largest, the head aside: a big head is a
large share by design), `over` (the limbs past 0.4), `headLimb` (the limb left out as the head when none is named
head or neck: no leg, and reaching clearly highest at rest), `sharedShare` (moved by more than one limb's bend) and
`unskinned` (limbs whose bend moves nothing). Each bend skins only the vertices weighted to that limb's bones. An image's
`silhouette` gives `details.silhouette`: `span` (its width over its height),
`widestRow` and `widestAt` (that row's filled width over the height, and how far up it
is), `feet` (the most pieces in the bottom 12%), `legsApart` (the share of the bottom
fifth's rows in two or more pieces), `coverage` and `pieces` (each of the 40 bands,
bottom up). With
`poses`, `path` or `feet`, `details.motion` holds the numbers all three come from
(one sampling of the first clip, or of each clip `--clip` picks, 30 times a second up to 900 samples, so a clip
over 30 s is sampled more coarsely and its `slide`, `plantedShare` and `loopGap`
shift with it): `clip`, `clips`, `duration`,
`samples`; `size` (the rest pose's largest side) and `ground`, the floor the feet
and `belowGround` are measured against: the y = 0 plane when the rest pose or the
clip's first frame stands near it (a Uthana rig rests with its hips at the origin,
half under the plane, and its clip lifts the character onto it), else the rest
pose's low point; `restGround` is the rest pose's low point (a low point is the 1st
percentile of the mesh's vertices, so a few stray vertices do not decide; a
clip-only motion with a skeleton and no mesh is measured on its joints, its size their
box and its low point the lowest joint, unless it is drawn on its character, which is then measured);
`hipsBone` (a bone named Hips, Hip or Pelvis, else the shallowest whose name ends
so and names no side: `LeftHip` is a thigh's joint) and `hipsTravel` (the farthest the hips get from where they start;
the model's middle when it has no bones), `hipsSpeed`, `loopGap` (the end's distance
from the start in metres: near 0 for a cycle, the travel for a walk); `limbs` and
`limbsMoving`, `legs` and `legsMoving` (both null, with `legsWhy`, when no limb
reaches the ground: no leg found is never every leg moving); `belowGround` (the most, as a share of
`size`, that the clip takes the mesh's low point under the floor) and
`closestToGround`; `maxBoneDeg`; and `limbList`, each limb with whether it is a leg,
whether it moves, and for a leg its `foot`, `lowest` and `highest` points over the
clip, `plantedShare` and `slide` (its median speed along the ground while planted;
an in-place clip slides by design). The rest pose is the file's own, before a clip
moves anything. A limb is a terminal chain of bones at least a tenth of `size` long,
measured joint to joint; a short subtree under its last joint (fingers, toes) is
part of it, and a twist or roll bone beside another (`L_ThighTwist01`) is no branch.
A leg is a limb whose lowest point at rest is within 15% of `size` of `restGround`;
glTF stores joints, not bone ends, so a joint with nothing below it is taken to
end one parent segment further on. A limb moves when its tip leaves its place
in the frame of the bone it hangs from (the hips for a leg, the chest for a front
leg or an arm; its position and rotation taken out, so a rig turning as a whole or a
spine bending moves no limb of its own) by 5% of `size`. These rules were set on 52 generated rigs
and clips across eight body types, where they matched a Blender reading of the
same files. A
panorama's `details.panorama` gets `range` with `exposure` (`peak` and `median`
luminance, `stops` between them (null when the median is 0, as on a dome that is
mostly black), `overOne`, the share of pixels above 1.0, never rounded to 0 when
some are, and `overOneCount`, how many: a
"HDRi" with none is an LDR image in an HDR file; the peak and `overOne` read
every pixel, the median a sample; a NaN or negative texel counts as black) and
`seamJump` with `seam` (the step across the wrap, averaged down the rows, over the
90th percentile of the same step between neighbouring columns in the 16 on each
side, on log luminance for an HDR: about 1 or under is ordinary, over 3 a seam that
shows; null when it cannot be measured). A sprite sheet's `details.sheet` gives its
grid, `frames`, `frameWidth`, `frameHeight`, `transparent`, `emptyFrames` and
`baselineSpread`, how many pixels the frames' lowest opaque rows spread over (the
feet jumping); with no transparent pixel the sprite cannot be told from its
background, and both are null ("could not tell", not "none"). A sound's
`details.audio` also holds the numbers its views draw, whichever views were
asked for. The views and the loudness come from one decode at 48 kHz; the peak,
the overs, the clips and the silence are read at a WAV's own rate when it is not 48 kHz
(`statsRate`), because a resample overshoots a full-scale peak and rings
around a clipped run. Other formats are read on the 48 kHz decode.
- `peakDbfs`: null for a file that is all zeros.
- `overs`: samples more than 1 dB past full scale (a float WAV or a lossy decode can
  hold them with no run at full scale), which a 16-bit copy cuts off. Under 1 dB is
  left to a resample's ringing.
- `clips`: stretches of at least 3 samples in a row at full scale (closer than
  10 ms count as one), with the first 20 as `clipTimes` (`[start, end]` in seconds),
  and `clippedSeconds`, the stretches' total length, which tells two takes that
  both clip apart.
- `leadingSilence`, `trailingSilence`: seconds under `silenceThresholdDbfs` (−60).
- `integratedLufs`: gated (ITU-R BS.1770-4, with its published 48 kHz
  K-weighting). Null under 400 ms, which BS.1770 does not define, or when every
  block is under the −70 LUFS gate. `ungatedLufs` is the whole file's loudness
  with no gate, for a short sound.
- `loopJump`: the bend across the loop point (`|x[i+1] − 2x[i] + x[i−1]|` where
  the end meets the start) over the 99th percentile of the same bend in the 30 ms
  on each side. A loop that carries on reads about 1 or under, however bright it
  is; a click reads many times that; silence at the junction reads 0. The
  `loop` view's label says "no click" at 3 or under and "a click" above.
- `container`: what the file really is, from its first bytes (`wav`, `mp3`,
  `ogg`, `flac`, `mp4`, `aiff`; null for another format), and
  `containerMismatch` when its extension says otherwise (an MP3 named `.wav`:
  Unity reads by extension).

The spectrogram analyses windows half a window apart across the whole sound and
keeps the loudest per column, so a short event in a long sound shows. It
analyses each channel on its own and keeps the louder, so channels in opposite
phase do not cancel. A sound longer than 10 minutes is refused as data ("too long
for the sound views") before the decode: about 230 MB for a stereo one at the
limit. The image shows where; the numbers decide whether it passes. The CLI checks
every image (a lowercase view name, at most 4096 px a side, PNG bytes) and
writes `<asset name>.<view>.png` beside the page, in a new
`unity-ai-preview/png-<time>-<id>` folder of the temp folder (`unity-ai-preview-<user>`,
readable by that user alone, off Windows, where the temp folder is shared); folders older than
a day are cleared on the next run. Off Windows that folder is used only when it is a real
folder, mode 0700, that the user can write in (never one another user made first, or a link,
and never for root, which cannot tell); otherwise each run gets a private
`unity-ai-preview-png-…` folder of its own, which is not cleared. An asset that fails is an
entry with `ok: false` and its `error`, and the run goes on; when the browser cannot be
restarted after an asset broke it, the assets left are listed as `not attempted`. A model's
companions are only files inside its own folder, named without a drive, a UNC path or a `..`
that climbs out, and reached through no link: anything else is left to show as missing,
unopened. 3D models and panoramas fetch three.js from
unpkg, as the interactive page does. Assets over 64 MB are not embedded
(`UNITY_AI_PREVIEW_PNG_MAX_MB` changes the cap). When Node.js is there, such an
asset is captured through a preview server of the run's own instead: the
launcher (`open.mjs`) starts it on a free port, never reusing (and widening) a
server already running, with a 5-minute idle limit; the capture opens its link
with `capture=1`, and the server reads the asset, its companions and its sidecar
itself, so there is no cap and no copy. Its entry has `served: true`, the
`servedPort`, and no `page` (the link stops with the server). That port alone is stopped when the run
ends; a run killed mid-way leaves a server that stops by itself 5 minutes later.
Without Node.js the asset fails, saying so.

### Comparing two captures

Every model view follows one convention, so a capture of an asset before a step
(a retexture, a remesh, a rig) and one after it line up:

- **Camera:** a 40° vertical field of view, from the front (+Z, glTF's forward),
  19.29° to the right and 15.81° above, aimed at the middle of the framed box (the
  model on its first frame, the ground point under it and, while it is near, the
  origin), 1.9 times the box's largest side in front of the target (2.09 times
  along the line of sight: `details.camera.distance`). `turntable` turns that camera
  around the vertical in 45° steps; `skeleton` turns it to the front (0°) and the
  side (90°); `parts` frames the same direction on the taken-apart model and on
  each part; `poses` keeps the direction and the distance (from the largest
  pose) and follows the model from tile to tile. `details.camera` gives the field of view, the yaw, the pitch, the
  distance and the target. A view that cannot be drawn (it throws, say on a mesh
  too large) is listed in `details.skipped` as `could not be drawn: …`, and the
  other views are kept.
- **Lighting:** the studio room for reflections, a sky and ground fill, and a
  light just above the camera that follows it; ACES tone mapping at an exposure
  of 1. The `materials` spheres use the same lights, from the material viewer's
  camera.
- **The rest:** the first frame of the first clip (the motion views move through
  it and put it back), the ground grid on (off in `parts`), no wireframe and no
  bones except in `skeleton` and `poses`, the `#1e1e22`
  background, a fixed size per view and a pixel ratio of 1.

The framing comes from the model's own bounds, so the images line up while the
bounds stay the same. Compare `details.bounds` and `details.camera` first: when
they differ, the step changed the model's size or where it sits, and the framing
moved with it. An image keeps its own pixels (at most 1024 px on its longer side,
never enlarged, `scale` in its row) over the same checkerboard, with no exposure
or colour change, so two images compare as they are.

## Query parameters

| Parameter | Meaning |
|---|---|
| `file` (repeatable; aliases `f`, `path`) | Asset to preview. Several `file=` fill the library; exactly one opens itself. |
| `items` | JSON array of `{ path, …meta }` objects, for per-asset metadata in one URL. |
| `dir` (repeatable) | A folder to open: its generated assets (files with a `.unityai.json` sidecar), details from each sidecar, plus its `gallery.js` if there is one. Add `&all=1` to show every previewable file for this visit (Settings → Library does it for good). Needs the page served (a page opened from disk cannot list folders). **Add…** → **Add folder** does the same interactively. |
| `gallery` | Path to a `gallery.js` history file (see below). |
| `material` | JSON `{ name, albedo, normal, roughness, metallic, height, ao, emissive }` with paths, for a lit PBR material preview. |
| `sheet` | Slice a sprite sheet on load: `sheet=4x2` (cols × rows) or `sheet=8` (one row). |
| `frameCount`, `fps` | With `sheet`: play only the first `frameCount` cells (a grid with a spare cell), at `fps`. Without them the sheet plays every cell at the strip's last rate; a layout typed into the strip plays every cell again. `frames` is an alias of `frameCount`. |
| `modality` | `sprite`, `texture`, `skybox`, `sound`, `music`, `model3d`, … — overrides the guess from the file extension and decides how the asset is viewed (`skybox` opens the 360° viewer, `spritesheet` slices). |
| `character` | The character a motion saved without its mesh is drawn on: a path to its glTF or GLB, absolute or relative to the motion's folder. Without it, the character is found by the sidecars' ids (see 3D models below). A model that has a mesh ignores it. `unity ai preview --character <file>` passes it and serves the file's folder. |
| `modelId`, `prompt`, `pointsCost`, `createdAt`, `jobId`, `assetId`, `bytes`, `sidecar` | Generation details shown in the right-hand panel; these are the sidecar's own field names. Short aliases for hand-typed URLs: `model`, `cost`, `created`, `job`, `asset`. |
| `orgName` | Display name of the organization charged (shown as-is). |
| `org` | Numeric id of that organization (shown in parentheses after the name). |

Plain parameters apply to every `file=` in the URL; use `items` when assets
need different metadata.

## `gallery.js` — groupings a sidecar cannot hold (optional)

You rarely need one. Assets open by path or by folder (`?dir=`), and their
details, prompt included, come from the `.unityai.json` sidecar the
generator writes. Two things a per-asset sidecar cannot say: which images form
a PBR material, and how a sprite sheet is laid out. `gallery.js` is where those
can be kept; `?dir=` reads it automatically when it sits in the folder.

Open the page with no parameters and it loads a `gallery.js` sitting next to
it; pass `?gallery=<path>` to load one from anywhere else on this machine. The
file must be named `gallery.js` and be local (it runs with the page's
privileges, so remote URLs and other script files are refused). It is plain
JavaScript so the browser can read it from disk, and it is append-only:

```js
window.UNITY_AI_GALLERY = window.UNITY_AI_GALLERY || [];
window.UNITY_AI_GALLERY.push({ path: "frog.png", modelId: "gemini-nano-banana-2-1", prompt: "cute frog", pointsCost: 12, orgName: "my-team", org: "1234567890123", sheet: "4x2" });
// Values here win over the sidecar's; the sidecar fills whatever is missing.
```

Relative paths resolve against the gallery file's own folder, so a
`gallery.js` inside an output folder can list its siblings by name.

## Two levels

The page is a library and one asset, and they take turns, the way a phone app
pushes a page and pops it. The **library** is a grid of every generation with
its own bar: a search box (`/` focuses it, `Esc` clears, `Enter` opens the first
match), a **Show** type filter, a count, and a **Tile size** slider (rows always
fill; the size is remembered). A click selects a tile and the details panel
follows; a double-click (or `Enter`) opens it; each tile's **⋯** button opens
the same menu as a right-click. Several tiles can be selected at once:
`Ctrl`+click adds or removes one, `Shift`+click (or `Shift`+arrow) takes a
range, `Ctrl+A` takes every tile shown and `Esc` lets go; the count says how
many. The menu on one of them then copies all their paths or links (one per
line) or removes them all from the view, and `C` and `Delete` act on all of
them. Only tiles still shown are acted on. Every word
of a search must appear in the name, path, kind, prompt, model, modality, org,
job or asset id, output type or parameters; a material stays when one of its
maps matches. Search and filter are session-only. Nested folders (`deep=1`)
stay flat: every asset is a tile tagged with the subfolder it came from. A
listed folder with nothing at its top level says so and offers **Include
subfolders**.

With an **asset open**, the header centres its name, with **All assets** on
the left as the way back. The details are a sidebar when the pane is wide.
When it is narrow they open as a sheet over the stage (`I`), or, with
**Settings → Appearance → Layout → Under the view** on, they sit
under it, in the library as well as with an asset open: the view is square,
the details fill the room under it at the full width, and `I` hides them as in
the wide layout. The gap
between the view and the details is a grip: drag it to give the view the
height you want (remembered), double-click it for square again. A strip under the stage is the library as a contact sheet, in its
current order, filter included, with the open asset marked and kept in view;
when the open asset is one output of a batch, its siblings lead the strip in
output order, a divider between them and the rest. A tile opens its asset,
and the arrows at the strip's two ends (or ←/→, ↑/↓) step through the
library in its order. The first header button, `Esc` or `Backspace` go back to
the library, which lands on the tile that was open. The moves are browser history,
so the mouse Back / Forward buttons retrace them. The **details panel** (`I`)
sits beside the stage when the pane is wide enough and opens as a sheet over
it when it is not (below about 730 px, which is most side panes); its
visibility beside the stage is remembered, and so is its width: the gap
between the stage and the panel is a grip (double-click for the default). It lists the asset (path with Copy,
type, size, bytes, sidecar, marks) and the generation (model, cost, prompt with
Copy, every parameter, inputs, which output of a multi-output run the file is,
ids, date), and the shortcuts. Status messages appear as a toast at the foot of
the viewer and fade; an error stays until the next one.

**Settings**, under the header's last icon, is one tabbed popover: **Library**
(whether files without a sidecar show; off by default, so a texture Unity
extracted next to a model, or a screenshot dropped in the folder, stays out of
the library; files you name yourself always show; and **Include subfolders**,
which lists the open folders' subfolders too, and every folder added after),
**Appearance** (the design dials) and **Shortcuts** (`?` opens it there). Both
Library switches are remembered; `?all=1` and `?deep=1` in the address are the
same switches for one visit.

Everything else is decided by the asset's type: its sidecar modality, the
`sheet=` hint, or an HDR or EXR extension; never the shape of a plain image.
There is no button to declare an image a material. Two views can be chosen by
hand: the **Sprite sheet** tool (`S`) slices any image, for a sheet with no
sidecar, assembled from single sprites or sampled from a video, and **View as
360°** (`O`) wraps any image exactly twice as wide as it is tall, with **View
as image** (`O`) in the 360° strip to put it back flat. An image whose
metadata says panorama opens in 360° whatever its size, and stays under
Skyboxes when shown flat.

## Features by modality

**Images / sprites** (the current focus). The image sits on one checkerboard,
front and centre; its tools float over it in a strip at the top-left corner
(rule *toolbars* of the design system). When the stage is too narrow for the
strip, its trailing tools fold into a caret menu.
- Zoom from 5 % to 6400 %: 25 % per `+`/`−` press, about 10 % per mouse-wheel
  notch, anchored at the cursor, snapping to 100 % on the way; **Fit** (`F`)
  recentres, **1:1** (`0`) shows actual pixels. Drag to pan freely. **Pixelated**
  (`P`, nearest-neighbour) is automatic for small images and high zooms.
- **Grid** (`G`) overlays a pixel grid; its strip sets the cell size in source
  pixels (2 or more) and a horizontal and vertical offset, wrapped at the cell,
  so the lines can be aligned with a sheet that has a margin. It hides itself
  when the cells would be under 4 screen pixels, where the lines crowd out the
  image, and says so.
- **Flip** horizontally / vertically (`H`, `V`): viewing aids, the file is
  untouched.
- **Tile** (`T`) repeats the image in a grid to check its seams, 2 to 8 across
  and down from its strip; **Seams** (`E`) outlines each repeat.
- **Annotate** (`A`): point at things for the AI agent. Its strip holds the
  marks — pin, box, ellipse, arrow, free-hand stroke — in six colours, **Hide
  marks**, **Undo**, **Clear** and **Save and copy for the agent**. Each mark is
  numbered and carries a note written in place next to the number: a fresh
  mark opens it; later, click the mark's text (or its “add a note…”
  placeholder) to edit it; click a mark to select it. Hovering shows the drag
  handles: the number (or the outline) moves the mark, corner handles resize a
  box or ellipse, an arrow's head and tail move independently (`Del` removes a
  mark, `Ctrl+Z` undoes, `Esc` deselects, or leaves when nothing is selected).
  Marks show only while Annotate is on; Hide marks peeks at the bare image
  without leaving the tool. Right-click the image for **Copy image with marks**
  (a PNG on the clipboard, to paste into a chat), **Copy image** (bare) and
  **Save image with marks** (the two files below when served, a download
  otherwise); the browser's own "Copy Image" would copy the bare file. The
  marks live in image pixels and follow zoom, pan and flips; the middle mouse
  button pans while the tool is on. Nothing is drawn into the image file.
  **Save and copy for the agent** first writes `<image>.annotations.json`
  (pixels, percentages, 3×3 region words, notes, the sidecar's prompt and
  model, the same text) and `<image>.annotated.png` (a copy with the marks
  burnt in, downscaled to 2048 px on the long side; the JSON's `px` values
  refer to the original size) next to the file when the page is served, then
  puts a numbered text list on the clipboard (positions as percentages from the
  top-left, region words like `top-right`) to paste into the chat. Saved marks
  come back when the image is opened again.
- **Sprite sheets** slice themselves: a `spritesheet` modality or a `sheet=`
  hint (`4x2`, or `8` for one row), or the **Sprite sheet** tool (`S`) on any
  image, opens the sheet strip, with the layout, a
  minimap (click a tile to jump to that frame), play / pause (`Space`), frame
  stepping (`,` `.`), FPS and loop. The layout is remembered per asset.
- Dimensions, aspect ratio and the generation details, in the details panel.

**Sound / music / speech**: native player plus a waveform (click it to
seek); duration and channel count in the details panel. The library tile
is a bar waveform of the same peaks, so sounds can be told apart before
they are opened. The waveform needs the file's bytes, so it appears for
dropped files and through `serve.mjs`, not for `?file=` paths opened from
disk: there the **Audio** row of the details says why and how to get one
(the page does not even try, since the browser would only log a CORS error,
and no other way reaches the samples of a file the page opened from disk),
and the tile keeps its speaker glyph.

Sounds play without being opened: a sound tile's ▶ button (or `Space` on the
selected tile) plays it in place, its waveform coloured as it plays with a
playhead (as in the opened view), and `Space` plays or pauses an opened sound
too. One sound plays at a time.
While one plays, moving to another sound (the arrows, a click, opening it,
back to the library) plays that one, so a batch is reviewed with `Space` once
and then one key per sound; pausing, or moving to an asset that is not a
sound, ends the review.

**Video**: native video player. The library tile is the clip's first
frame; duration and frame size in the details panel. A frame drawn from a
`file://` clip taints the canvas, so a `?file=` path keeps the film glyph.

**Skyboxes / panoramas** (`.hdr`, `.exr`, `modality=skybox`, a 2:1 image whose
sidecar names a skybox model but no modality, or any 2:1 image switched with
**View as 360°**, `O`) in a 360° viewer built on
three.js, loaded from the unpkg CDN on first use (every module is
integrity-pinned in the page's import map, so a tampered download is refused;
the same modules power the 3D and material viewers):
- Drag to look around, wheel to zoom (field of view); the floating strip holds
  **Auto-rotate** (`R`) and **Reset view** (`F`). Tilt stops about 12° short of
  straight up / down, where every equirectangular image pinches and generators
  leave the nadir messy.
- The 360° strip: **Mapping**, *Full sphere* (360° × 180°, horizon in the middle
  row, as in HDRIs) or *Dome* (360° × 90°, horizon on the bottom row, as most
  generated skyboxes are). Wrapping a dome as a sphere pulls the horizon down to
  your feet and stretches everything. The page picks automatically by looking at
  the pixels: a full sphere's top and bottom rows converge on the poles and are
  nearly uniform, a dome's bottom row carries the horizon. Override with the
  dropdown; the choice is kept per asset. **Exposure** in EV: true exposure with
  ACES tone mapping for HDR files, a brightness scale for LDR images; 0 EV to
  start, remembered per asset.
- Same disk limitation as 3D: from `file://`, drop the file or use `serve.mjs`.

**3D models (glTF / GLB, FBX and OBJ)** in a three.js viewer:
- Lit so every side reads: a studio environment for the reflections (metal
  still reads as metal), with its light panels on all four walls, plus a soft
  sky and ground fill and a light just above the camera that follows the
  orbit. The viewer, the hover orbit and the library tiles share this setup,
  and PBR materials use the same studio.
- Drag to orbit, wheel to zoom, right-drag to pan. The strip over the view
  holds **Surface**, **Wireframe** (`W`), **Skeleton** (`B`) and **Ground**
  (`G`), then **Auto-rotate** (`R`) and **Reset view** (`F`), which reframes
  the model. Inspect the triangles of a retopologized mesh, or the bones of a
  rigged one; with the surface off and the skeleton on, the mesh stays as a
  translucent ghost. Wireframe and bones follow the animation.
- **Ground** (on by default, remembered) draws a grid on the `y = 0` plane
  with the world axes (red X, green Y, blue Z) at the file's origin, sized to
  cover the model and, when it is near, that origin (a prop authored far from
  its origin is framed alone), and swaps the transparency checkerboard for a plain background
  while it shows, so the grid lines read. A character's feet can be checked
  against the floor: a rig whose origin is at
  the hips sits half under it, an animation whose hips key lifts the body
  stands on it. The button's tooltip states the measured gap between the
  model's lowest point and the plane. The view is framed on the pose the
  clip starts in, on the ground under the model and on the origin, so a body
  the animation raises out of its bind pose does not leave the frame when the
  clip plays; the Bounds field in the details keeps the bind pose.
- Animations embedded in the file: a transport at the foot of the view picks
  the clip, plays / pauses (`Space`) and scrubs.
- A motion saved without its mesh (a glTF with clips and no mesh, such as a
  motion generated with `no_mesh=true`) is drawn on the character it was made
  for: that character's mesh and skeleton play the motion's clips, each channel
  bound to the character's node of the same name. The character is the file
  `character=` names (an absolute path, or one relative to the motion's
  folder), else the glTF or GLB beside the motion whose sidecar's `partnerResultId` is
  the motion's `params.target_character_id` (the rig it was generated on;
  found when the page is served). The **Character** row of the details names
  it, says how it was found and how many of the motion's channels found a node
  (`3 of 4 channels matched`); the mesh, bounds and rig rows are then the
  character's. With no character found, one with no mesh, or none of the
  channels matching, the motion is shown on its own as before (the row says why
  when a character was found but not used).
- Details panel: bounds (w × h × d in metres), triangle / vertex / mesh /
  material counts, bone count, animation list.
- Library tiles are rendered from the model itself (a 3/4 view, studio
  lighting), one model at a time, once per session. Hover a model's tile and
  drag to turn it; the angle you leave it at becomes its thumbnail and is where
  the live view resumes next time.
- Reading a 3D file needs more than displaying an image, and browsers refuse
  that for `file://` paths. From disk, drop the `.glb`, `.fbx` or `.obj` onto
  the page; with `serve.mjs` it just works.
- An OBJ reads its MTL libraries (`mtllib`) and their textures from beside
  the file, with the materials rebuilt as PBR: non-metal, roughness from the
  shininess (`Ns`), which is all MTL carries. OBJ has no unit, so its numbers
  read as metres. A missing `.mtl` is named in the details (**Material
  library**) and the model opens in a default grey; a file without normals is
  given smooth ones. A dropped `.obj` comes without the files beside it, so
  its `.mtl` is not read: open it by its path on a served page (`?file=`).
- An FBX comes in at Unity's import scale (the file's unit scale × 0.01, so
  a centimetre file reads in metres) with its materials rebuilt as PBR, in the
  same studio light as a GLB. Textures it names are read from beside the file.
  FBX has no metallic or roughness channel; when the exporter left those maps
  in the file as textures named for the channel (Blender's FBX IO does, so a
  Uthana rig of a Tripo mesh keeps its steel), they go back on
  the material, otherwise roughness comes from the shininess exponent and the
  surface is shown as non-metal. The **Materials** row of the details says
  which, as a warning when no metallic map could be recovered.

Right-click a tile or the image (or use the tile's **⋯**) for **Open**, **Copy
path**, **Copy link** (the file's URL, to paste into another browser) and
**Remove from view** (`Delete`; the tile goes, the file stays); on the image
the same menu also offers the copy / save with marks actions. The page never
opens anything outside the browser: paste the copied path into your file
manager to get to the folder.

**PBR materials** (three.js, same lazy load as skyboxes): the maps of one
generation, lit and inspected on a sphere, cube, plane or cylinder.
- Outputs of one multi-output generation (the sidecar's `output.generationId`
  and `output.type`: normal, height, smoothness, metallic, ambient occlusion)
  are filed under a material automatically, with the generation's input image
  as albedo when it is loaded too, so a converter's maps show up as one tile
  with nothing to hand-write; a smoothness map feeds the roughness channel
  inverted, and maps with no channel here (edge) fold in with them.
- Studio environment lighting, drag to orbit, wheel to zoom, **Auto-rotate**
  (`R`), **Reset view** (`F`); the material strip sets the **Shape**, the
  **Tiling** repeat count and the **Bump** strength for height and normal maps.
- From a URL: `?material={"name":"cobblestone","albedo":"C:/…/cobblestone.png","normal":"C:/…/cobblestone_n.png"}`.
  In `gallery.js`: `{ name: "cobblestone", maps: { albedo: "cobblestone.png", normal: "cobblestone_n.png" } }`.
- The material's channel files are rows in the details panel, and its tile in
  the library carries an "N maps" toggle that unfolds them as tiles of their own.

## Limits

- A page opened from disk (`file://`) can display local images, audio and
  video but cannot *read* their bytes, so the tools that need them (the
  audio waveform, the annotated PNG export, the 3D, skybox and material
  viewers) only work on files dropped onto the page, through `serve.mjs`, or in
  the copy `unity ai preview --png` writes with the asset embedded.
- Opening the page over `http(s)` while pointing at `file://` assets is
  blocked by browsers. Serve the assets from the same server, or open the
  page from disk.
- From `file://`, the `.unityai.json` sidecar is not read automatically
  (same browser restriction): pass its fields as parameters or drop it with
  the asset. Through `serve.mjs` the sidecar next to the file is read on its
  own, including for picked files once they have been located.

## Tests

The page and its server are covered by two suites kept outside this folder, in
the tool's source tree: everything under the skill folder ships, so the tests
do not live here. The source tree's README says how to run them.
