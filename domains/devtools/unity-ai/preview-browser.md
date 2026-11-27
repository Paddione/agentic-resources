# Route 1: a browser tool that loads localhost pages

Part of the unity-ai skill: `show-result.md`, in the folder next to this
file, sends you here when the client has a browser tool that loads
`http://localhost` pages (route 1). "The launcher" is `unity ai preview`; routes 1
to 3 and the **Preview** block of the reply are in `show-result.md`, and a
section named without a file is a section of `SKILL.md`.

**A browser tool that loads `http://localhost` pages** — any client with
a "navigate to URL" tool. Today: the pane of Claude Desktop, and of Claude
Code running inside it (`navigate` / `preview_start`); the Codex / ChatGPT
desktop app's built-in browser (`@Browser`). Navigate it to the `preview:`
URL exactly as the launcher printed it, for every generation: the page
keeps whatever the user already had in that tab (folders, other files)
and adds what the URL names, with the new file selected. Never append
`&reset=1` unless the user asks for a clean view. If the tool
refuses `http://localhost` pages or Node.js is missing, fall through to
route 2 instead of stopping. When the launcher prints no `preview:` line
(the server could not start), fall through the same way with its
`fallback:` URL, and say that 3D models, skyboxes and materials need the
server. Client notes:
- *Claude Desktop*: navigating opens a closed pane and renders a card in
  the reply with an **Open** button that shows the pane tab. It does NOT
  unhide a hidden pane (nor does `tabs_select`), and the tool reports
  "opened" either way: after navigating, call `tabs_context`; if it says
  the pane is hidden, tell the user to press Open on the card above. The
  pane shows `file://` pages as static snapshots (no scripts), so the
  `fallback:` URL is useless there. The user gets BOTH ways to look, every
  time, as the **Preview** block described in `show-result.md`, under reporting: the
  pane (already navigated), the same `preview:` URL as a link, which
  Claude Desktop opens in the user's default browser, and the command that
  brings the preview back once the server has exited. Neither
  replaces the other — some users work in the pane, others want a full
  window — so never drop one because the other worked. When the user asks
  to open it in their browser, run the launcher again with `--open`.
- *Codex / ChatGPT desktop app*: on Windows its browser refuses `file://`
  URLs, so the `fallback:` URL is useless there too, and it may refuse
  `127.0.0.1` until the user allows that site once in the app's browser
  settings. A refusal is a permission prompt, not a missing capability:
  ask the user to allow it and navigate again rather than switching to
  route 2.
