#!/usr/bin/env bash
# Share resources across agent harnesses (additive, never overwrites real files):
#  - every skill in ~/.agents/skills is symlinked into each harness' skill dir
#  - ~/AGENTS.md is linked as the global context file where none exists
# Usage: share-agent-resources.sh [--dry-run]
set -euo pipefail

DRY=0; [[ ${1:-} == --dry-run ]] && DRY=1
MASTER="$HOME/.agents/skills"
SKILL_DIRS=(.claude/skills .codex/skills .config/opencode/skills .zcode/skills
            .gemini/config/skills .pi/agent/skills .qwen/skills .openclaw/skills)
CONTEXT_FILES=(.codex/AGENTS.md .qwen/QWEN.md .pi/agent/AGENTS.md)

run() { (( DRY )) && echo "[dry] $*" || "$@"; }

# Claude Code loads ~/.claude/skills/synced/<bucket>/<name> itself (as
# anthropic-skills:<name>); skip identical copies so Claude doesn't list the skill
# twice. Diverging copies (local additions) are still linked.
provided_by_synced() {
  local destdir="$1" name="$2" src="$3" bundled
  [[ "$destdir" == */.claude/skills ]] || return 1
  for bundled in "$destdir"/synced/*/"$name"; do
    [[ -d "$bundled" ]] && diff -rq "$bundled" "$src" >/dev/null 2>&1 && return 0
  done
  return 1
}

for d in "${SKILL_DIRS[@]}"; do
  dest="$HOME/$d"; run mkdir -p "$dest"
  for s in "$MASTER"/*/; do
    name=$(basename "$s")
    [[ $name == synced || ! -f $s/SKILL.md ]] && continue
    if [[ -e $dest/$name || -L $dest/$name ]]; then
      # replace dangling links only (e.g. stale Windows paths)
      [[ -L $dest/$name && ! -e $dest/$name ]] && run ln -sfn "$(realpath -s --relative-to="$dest" "$MASTER/$name")" "$dest/$name" && echo "fixed $d/$name"
      continue
    fi
    provided_by_synced "$dest" "$name" "$MASTER/$name" && { echo "skip  $d/$name (identical in synced bundle)"; continue; }
    run ln -s "$(realpath -s --relative-to="$dest" "$MASTER/$name")" "$dest/$name"; echo "link  $d/$name"
  done
done

for f in "${CONTEXT_FILES[@]}"; do
  [[ -e $HOME/$f || -L $HOME/$f ]] && continue
  run mkdir -p "$(dirname "$HOME/$f")"; run ln -s "$(realpath -s --relative-to="$(dirname "$HOME/$f")" "$HOME/AGENTS.md")" "$HOME/$f"; echo "link  $f"
done
