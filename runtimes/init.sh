#!/usr/bin/env bash
# init.sh — Consumer-Anbindung an agentic-resources (live, additiv).
# Verlinkt gewählte Layer als Symlinks in die Skill-Verzeichnisse der
# Harnesses und legt repo.yaml aus einem Profil an. Überschreibt NIEMALS
# echte Dateien — nur fehlende Pfade werden verlinkt, dangling Links repariert.
# Usage: init.sh --repo <pfad> [--layers core,lifecycle|all] [--profile <name>] [--dry-run]
set -euo pipefail

REPO=""; LAYERS="core,lifecycle"; PROFILE=""; DRY=0; HARNESS=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo) REPO="$2"; shift 2;;
    --layers) LAYERS="$2"; shift 2;;
    --profile) PROFILE="$2"; shift 2;;
    --harness) shift; HARNESS=1;;
    --dry-run) DRY=1; shift;;
    *) echo "unknown flag: $1" >&2; exit 2;;
  esac
done
[[ -z "$REPO" ]] && { echo "usage: init.sh --repo <pfad> [--layers ...] [--profile ...]" >&2; exit 2; }
[[ -d "$REPO" ]] || { echo "kein Verzeichnis: $REPO" >&2; exit 2; }

AR="$(cd "$(dirname "$0")/.." && pwd)"
run() { (( DRY )) && echo "[dry] $*" || "$@"; }

# Layer auflösen: "all" oder Kommaliste aus core, lifecycle, domains/<pack>.
# -L folgt verlinkten Skill-Dirs (z.B. domains/formats/docs -> synced/docs),
# damit auch diese als Skills verlinkt werden.
resolve_layers() {
  if [[ "$LAYERS" == "all" ]]; then
    find -L "$AR" -name SKILL.md -not -path "*/staging/*" | xargs -n1 dirname
  else
    for l in ${LAYERS//,/ }; do
      if [[ "$l" == domains/* ]]; then echo "$AR/$l"
      else find -L "$AR/$l" -maxdepth 2 -name SKILL.md 2>/dev/null | xargs -n1 dirname
      fi
    done
  fi
}

# Skill-Verzeichnisse: Standard ist NUR das Consumer-Repo (Projektebene).
# --harness verlinkt zusaetzlich auf Home-Ebene (Maschinen-Setup, kein Projekt-Default).
# Matrix: Home-Ziele == share-agent-resources.sh SKILL_DIRS + ~/.agents/skills (Master).
# Projekt-Ziele sind deren Gegenstuecke mit gleichem <root>/skills-Layout.
# .opencode weicht bewusst ab: Projekt .opencode/skills (Plugin-Konvention),
# Home .config/opencode/skills — Scope-Unterschied, kein Widerspruch.
# .gemini/.pi/.qwen/.openclaw bleiben Home-only (eigene Projekt-Layouts,
# unverifiziert); Plugin-Caches (.codex/plugins, .claude/plugins) sind
# provider-verwaltet und nie Link-Ziele.
HARNESS_DIRS=()
if (( HARNESS )); then
  HARNESS_DIRS=("$HOME/.agents/skills" "$HOME/.claude/skills" "$HOME/.codex/skills" "$HOME/.config/opencode/skills" "$HOME/.zcode/skills" "$HOME/.gemini/config/skills" "$HOME/.pi/agent/skills" "$HOME/.qwen/skills" "$HOME/.openclaw/skills")
fi
PROJECT_DIRS=("$REPO/.agents/skills" "$REPO/.claude/skills" "$REPO/.codex/skills" "$REPO/.opencode/skills" "$REPO/.zcode/skills")

link_skill() {
  local src="$1" destdir="$2" name
  name="$(basename "$src")"
  # "synced" ist kein Skill (Harness-Bundle-Dir); "references" (core/references)
  # ist per registry.json ein Skill und wird wie jeder andere verlinkt.
  [[ "$name" == "synced" ]] && return 0
  if [[ -e "$destdir/$name" || -L "$destdir/$name" ]]; then
    # replace dangling links only (e.g. stale paths)
    [[ -L "$destdir/$name" && ! -e "$destdir/$name" ]] && run ln -sfn "$(realpath -s --relative-to="$destdir" "$src")" "$destdir/$name" && echo "fixed $destdir/$name -> $src"
    return 0
  fi
  run ln -s "$(realpath -s --relative-to="$destdir" "$src")" "$destdir/$name"
  echo "link $destdir/$name -> $src"
}

while read -r skill; do
  [[ -z "$skill" ]] && continue
  for d in "${HARNESS_DIRS[@]}" "${PROJECT_DIRS[@]}"; do
    [[ -d "$d" || "$d" == "$REPO"* ]] || continue
    [[ -d "$d" ]] || run mkdir -p "$d"
    link_skill "$skill" "$d"
  done
done < <(resolve_layers)

# repo.yaml aus Profil seeden (nur wenn keins existiert).
if [[ -n "$PROFILE" && ! -f "$REPO/repo.yaml" ]]; then
  [[ -f "$AR/runtimes/profiles/$PROFILE.yaml" ]] || { echo "unbekanntes Profil: $PROFILE" >&2; exit 2; }
  run cp "$AR/runtimes/profiles/$PROFILE.yaml" "$REPO/repo.yaml"
  echo "repo.yaml aus Profil $PROFILE angelegt"
fi
echo "fertig."
