# Follow-ups (offen, nach v1)

- vitest-`references/`: Home-Deltas gegen BP-Stand abgleichen (Upstream-Doku-Drift,
  Dateien identisch benannt, Inhalte teils neuer).
- Consumer-Umschaltung (erledigt 2026-10-20): Bachelorprojekt via
  `scripts/agent-skills/link-from-repo.py` (53 Skills), Home-Harnesses zeigen
  direkt aufs Repo (`~/.agents/skills/*` → `agentic-resources/...`), `dotfiles/`
  und `agent-resources/` via `runtimes/init.sh --layers all --profile dotfiles`
  (je 74 Skills × 3 Dirs + `repo.yaml`). `init.sh` folgt seit 2026-10-20 auch
  verlinkten Skill-Dirs (`find -L`) und verlinkt `references/` (Registry-Skill).
- `docs/agent-guide` + `docs/sdlc` (Bachelorprojekt-Prozessdoku) als
  `domains/`-Pack oder Consumer-seitig bewerten.
- Taskfile-Templates (`test:changed`, `freshness:*`, `workspace:validate`)
  als `runtimes/`-Muster extrahieren.
- Externe Upstream-Revisionen (`registry.json → upstream`) periodisch prüfen.
  Stand 2026-10-19: `obra/superpowers` aktuell (bb92a7774141).
  Neuere Heads bei `wshobson/agents` (0874a27b vs. 46891e7e) und
  `jablonkai/skills` (ced445b8 vs. 399d40ae) — Update nur per Review-Chore,
  beide Vendor-Kopien tragen lokale Kuratierung (LICENSE, agents/, evals/,
  examples.md), die erhalten bleiben muss.
