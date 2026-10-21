---
name: opencode-git-workflow
description: 'Pointer to the git-workflow SSOT for opencode sessions. Use when committing, pushing, creating a PR, or finishing work on any branch in opencode; the full lifecycle (pull-first, commit conventions, freshness guard, CI fix loop, worktree cleanup) lives in git-workflow — read that skill next.'
---

# opencode-git-workflow — Verweis auf die SSOT

**Der Inhalt dieses Skills steht in [`git-workflow`](../../core/git-workflow/SKILL.md)
(SSOT; vom Repo-Root zusätzlich über `.agents/skills/git-workflow/` bzw.
`.opencode/skills/git-workflow/` erreichbar). Lies dort weiter und folge dem
Ablauf von dort.**

## Warum hier nur ein Verweis steht [T900024]

Diese Datei war bis T900024 eine **unabhaengige Kopie** von
`.claude/skills/git-workflow/SKILL.md` — 319 gegen 321 Zeilen, mit inhaltlicher
Drift in beide Richtungen. Die auffaelligste: die Claude-Code-Fassung zitierte
`T069/T070`, wo hier `T003069/T003070` stand. Nachweisbar richtig sind die
sechsstelligen IDs (`.agents/plans/2026-08-14-batch-git-worktree-integrity/`);
die kurzen waren Kuerzungsfehler. Wer zwei Kopien pflegt, pflegt am Ende zwei
verschiedene Ablaeufe — und merkt es erst, wenn eine Session dem falschen folgt.

Die Zusammenfuehrung ist in die SSOT gelaufen. Uebernommen wurde daraus auch der
Abschnitt **„Worktree-Erstellung"** (die git-crypt-Einschraenkung des
opencode-Plugins `worktree_create`), der nur in dieser Fassung stand.

**Kein zweiter Ablauf:** T900077 hatte die Symlinks unter `.opencode/skills/`
einmalig durch echte Verzeichnisse ersetzt (SSOT-Flip); der Vendor-Sync stellt
sie seither wieder als Symlinks auf diese Quelle her — gepflegt wird genau
eine Datei. Dieses Verweis-Dokument hält alle bestehenden Referenzen auf den
Skill-Namen `opencode-git-workflow` (OVERVIEW.md, `docs/agent-guide/registry/tools.yaml`,
`docs/agent-guide/20-werkzeuge.md`) gueltig, ohne einen zweiten Ablauf zu definieren.

## Framework mapping

| Framework | Availability |
|-----------|-------------|
| **Claude Code** | Use `git-workflow` directly |
| **opencode** | Full — this entry redirects to `.opencode/skills/git-workflow/SKILL.md` |
| **agy** | Full — treat the opencode path as authoritative |
