# Route 2: a shell but no browser tool

Part of the unity-ai skill: `show-result.md`, in the folder next to this
file, sends you here when the client has a shell but no browser tool
that loads `http://localhost` pages (route 2). "The launcher" is `unity ai preview`; routes 1
to 3 and the **Preview** block of the reply are in `show-result.md`, and a
section named without a file is a section of `SKILL.md`.

**A shell but no such browser tool** — any terminal agent. Today: Claude
Code in a terminal, Codex CLI, the Codex IDE extension. Run the launcher
with `--open`; it opens
the `preview:` URL in the user's default browser (the `fallback:` URL when
the server could not start). In a sandboxed client (Codex CLI) the opener
runs outside the workspace and triggers an approval prompt: request it,
and if the user declines, give them the URL to open themselves. Without
Node.js, `unity ai preview "<output path>" --open` still opens the
`fallback:` URL in the default browser; never build that URL yourself or
hand it to `start`, which drops everything after the `?`. From
`file://` the page shows images, audio and video but cannot read the
sidecar (hence the fields in the query), and 3D models, skyboxes and
materials need the served route or the file dropped onto the page — say
so when the asset is one of those.
