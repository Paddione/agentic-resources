# agentic-resources

Monorepo für alle agentischen Ressourcen: Skills, Lifecycle, Domänen-Packs,
Runtimes und Prompts. Jedes Folgeprojekt erbt per Live-Symlink statt per Fork.

## Layout

- `core/` — harness-neutrale Basis-Skills (`git-workflow`, Hygiene, Response,
  `references/` als Shared Hub).
- `lifecycle/` — `dev-flow-*`: Planen, Ausführen, Chores, E2E.
- `domains/<pack>/` — opt-in Domänen (`testing`, `gitops`, `ml-training`,
  `brand-site`, `data`, `devtools`, `formats`, `research`, `mcp`, `web`, `misc`,
  `projects/` für projekt-spezifische Beispiele). `brand-site` bündelt die
  Bachelorprojekt-Markenauftritte; `web` generisches Artefakt-Tooling.
- `domains/formats/`, `domains/web/`, `domains/mcp/`, `domains/misc/morning`,
  `domains/research/` sind vendored (ehemals Symlink-Packs auf den lokalen
  Home-Skill-Store); Klone sind vollständig.
- `runtimes/` — `init.sh`, `repo.yaml.schema`, Profile, Skripte, Prompts.
- `registry.json` — alle Skills mit Herkunft (`merged`, `home`,
  `bachelorprojekt`) und ggf. Upstream-Revision.
- `vendor-lock.json` — gelockte Upstream-Commits der Vendor-Skills.
  `runtimes/scripts/vendor-sync.py status|update|check` hebt sie per
  3-Wege-Merge an; `.github/workflows/vendor-sync.yml` läuft nächtlich je
  Gruppe: Upstreams aus `trusted_owners` (eigene Repos) mergen nach grünen
  Tests automatisch, externe Upstreams kommen als PR zur Prüfung, Konflikte
  als Draft-PR.
- `staging/` — Arbeitsablage für Merges, kein Vererbungsinhalt.
- `AGENTS.md` + `CLAUDE.md` — zentrale Anleitungsdateien (geteilte
  Doktrin: Layer-Modell, Skill-Konventionen, Consumer-Vertrag, Workflows).

## Vererbung (live)

```bash
./runtimes/init.sh --repo <pfad> --layers core,lifecycle,domains/testing --profile bachelorprojekt
```

Verlinkt die Layer als Symlinks (additiv, überschreibt nie echte Dateien) und
legt `repo.yaml` aus dem Profil an. `--layers all` für alles, `--dry-run` für
Vorschau. Projekt-Ziele: `.agents/skills`, `.claude/skills`,
`.codex/skills`, `.opencode/skills`, `.zcode/skills`; `--harness`
verlinkt zusätzlich Home (`~/.agents/skills`, `~/.claude/skills`,
`~/.codex/skills`, `~/.config/opencode/skills`, `~/.zcode/skills`,
`~/.gemini/config/skills`, `~/.pi/agent/skills`, `~/.qwen/skills`,
`~/.openclaw/skills` — wie `share-agent-resources.sh`). OpenCode-Pfad
weicht bewusst ab (Projekt `.opencode/`, Home `.config/opencode/`);
`.gemini`/`.pi`/`.qwen`/`.openclaw` bleiben Home-only.
Anleitungsdateien vererben nach demselben Muster: Repos ohne eigene
`AGENTS.md`/`CLAUDE.md` symlinken beide Namen hierher; Repos mit eigenen
Dateien (Bachelorprojekt) verweisen per Abschnitt auf diese Dateien. Geteilte Skills lesen Repo-Spezifika (Branch, Scopes, Tickets,
generierte Artefakte, Task-Runner) aus `repo.yaml` im Consumer-Root; siehe
`runtimes/repo.yaml.schema`.

## Konventionen

- Deutsch, prägnant, kein Deko. Frontmatter (`name`, `description`) ist Pflicht.
- Keine harten Repo-Annahmen in geteilten Dateien — parametrisieren statt forken.
- Externe Herkunft in `registry.json` unter `upstream` festhalten.
