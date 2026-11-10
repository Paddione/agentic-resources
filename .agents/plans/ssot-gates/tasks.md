# Plan: AR-SSOT-Gates (5 Kandidaten)

Zweck: Alle 5 SSOT-Lücken aus der Graph-Analyse
(`~/dotfiles/.agents/goals/ssot-graph-luecken-inventur/PROGRESS.md`, alle
Belege verifiziert 2026-11-10) mit dem Muster YAML + Check + Map + Task
schließen. Ausgenommen per Auftrag: Single-Hub `fleet-workspace` +
`mcp-servers.json` (konsolidiert).

## Partial-Manifest (disjunkte Dateien)

| Partial | Dateien |
|---|---|
| p1-prompts | `runtimes/prompts/manifest.yaml`, `tests/test_prompts_consistency.py`, `docs/maps/prompts-map.md` |
| p2-toolset | `runtimes/toolset/capabilities.yaml` ODER `registry.json`-Eintrag `status: external` (P-Entscheid), `tests/test_toolset_refs.py` |
| p3-links | `runtimes/links.yaml`, `tests/test_link_matrix.py`, `docs/maps/skill-sync-map.md` |
| p4-vendor | `registry.json`-Erweiterung (`upstream`-Pflichtfelder), `tests/test_registry_consistency.py`-Erweiterung, `docs/maps/vendor-map.md` |
| p5-repoyaml | `tests/test_repo_yaml.py`, `docs/maps/repo-yaml-map.md` (+ ggf. `runtimes/profiles/manifest.yaml`) |
| p6-verify | keine Files: vorhandene Suites (`tests/`, 57/57-Stand halten) |

## Details je Partial

- **P1**: Manifest (`id, role, harness, version`), Check (jede `.md` in Manifest,
  jede Rolle im `roles.mjs`-Vokabular — Vokabular-Referenz prüfen, ggf. nur
  dokumentieren), Map generiert, Task-Eintrag wo AR Tasks definiert (P klärt).
- **P2**: Entscheid im Partial: lokale Minimal-`capabilities.yaml` vs. explizit
  `status: external → Bachelorprojekt` + `toolset_registry_path` in
  `repo.yaml.schema`. Tote Pfade (`toolset-curate/SKILL.md:165-173`) per
  `test_toolset_refs.py` fail-closed prüfen.
- **P3**: `links.yaml` (`master`, Matrizen project/home, Owner je Mechanismus,
  `agent-resources.py` = read-only-inventory), Check alle 3 Matrizen vs. YAML.
- **P4**: `upstream{source, revision, vendor_id}`-Pflicht bei
  `source: external`; `upstream.revision == lock.ref`; `gh-fix-ci`-Widerspruch
  (`vendor-lock.json:15-22` vs. `registry.json:106-109`) auflösen.
  `merged`-Skills: Vendor-Pflicht im Partial entscheiden + dokumentieren.
- **P5**: Beide Profile gegen Schema parsen; jeder `repo.*`-Schlüssel mind. 1×
  in `core/lifecycle/domains` referenziert (sonst toter Schlüssel → rot).
- **P6**: volle Suite grün (57/57-Stand nicht unterschreiten).

Abnahme je Partial: Check grün + Fixture rot. Danach STOPP.
