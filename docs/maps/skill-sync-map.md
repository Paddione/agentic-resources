# skill-sync-map — generiert aus runtimes/links.yaml (P3).
Master: `~/.agents/skills`

| Mechanismus | Quelle | Owner/Rolle | Ziele |
|---|---|---|---|
| init.sh | `runtimes/init.sh` | consumer-linker: verlinkt Layer-Skills additiv in Consumer-Projekt (+ optisch --harness Home) | 5 Dirs (+ harness: 9) |
| share-agent-resources.sh | `runtimes/scripts/share-agent-resources.sh` | home-linker: verlinkt Master-Skills additiv in Home-Harness-Dirs (+ Kontextdateien) | 8 Dirs (+ kontext: 3) |
| agent-resources.py | `runtimes/scripts/agent-resources.py` | read-only-inventory: inventarisiert Home-Ressourcen (scan/check), kein Schreiber im Sync-Sinn | 8 Dirs |

## Divergenzen (Absicht, kein Drift)
- share-agent-resources.sh kennt ~/.agents/skills nicht als Ziel: das ist die Master-Quelle.
- Plugin-Caches (.codex/.claude/plugins/cache) nur im Inventar, nie Link-Ziele (provider-verwaltet).
- .opencode weicht bewusst ab: Projekt .opencode/skills vs. Home .config/opencode/skills.
