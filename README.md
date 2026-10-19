# agentic-resources

Monorepo für alle agentischen Ressourcen: Skills, Lifecycle, Domänen-Packs,
Runtimes und Prompts. Jedes Folgeprojekt erbt per Live-Symlink statt per Fork.

## Layout

- `core/` — harness-neutrale Basis-Skills (`git-workflow`, Hygiene, Response,
  `references/` als Shared Hub).
- `lifecycle/` — `dev-flow-*`: Planen, Ausführen, Chores, E2E.
- `domains/<pack>/` — opt-in Domänen (`testing`, `gitops`, `ml-training`,
  `website`, `data`, `devtools`, `formats`, `research`, `mcp`, `web`, `misc`,
  `projects/` für projekt-spezifische Beispiele).
- `runtimes/` — `init.sh`, `repo.yaml.schema`, Profile, Skripte, Prompts.
- `registry.json` — alle Skills mit Herkunft (`merged`, `home`,
  `bachelorprojekt`) und ggf. Upstream-Revision.
- `staging/` — Arbeitsablage für Merges, kein Vererbungsinhalt.

## Vererbung (live)

```bash
./runtimes/init.sh --repo <pfad> --layers core,lifecycle,domains/testing --profile bachelorprojekt
```

Verlinkt die Layer als Symlinks (additiv, überschreibt nie echte Dateien) und
legt `repo.yaml` aus dem Profil an. `--layers all` für alles, `--dry-run` für
Vorschau. Geteilte Skills lesen Repo-Spezifika (Branch, Scopes, Tickets,
generierte Artefakte, Task-Runner) aus `repo.yaml` im Consumer-Root; siehe
`runtimes/repo.yaml.schema`.

## Konventionen

- Deutsch, prägnant, kein Deko. Frontmatter (`name`, `description`) ist Pflicht.
- Keine harten Repo-Annahmen in geteilten Dateien — parametrisieren statt forken.
- Externe Herkunft in `registry.json` unter `upstream` festhalten.
