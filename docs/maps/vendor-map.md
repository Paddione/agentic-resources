# vendor-map — Herkunft doppelt geführt: registry.json ↔ vendor-lock.json (P4)

Richtung (fail-closed in `tests/test_registry_consistency.py`):

- `registry.json` klassifiziert die direkte Lieferbeziehung (`source`).
- `vendor-lock.json` ist die verwaltete Wahrheit für direkt vendored Skills
  (`vendor-sync.py check` grün). Bei `source: external` gewinnt der Lock:
  `upstream.revision == lock.ref`, `upstream.path == lock.path`,
  `upstream.vendor_id == lock-Schlüssel`.
- `upstream`-Pflichtfelder bei `source: external`: `source`, `revision`, `vendor_id`.
  `vendor_id` = vendor-lock-Schlüssel falls geführt, sonst Upstream-Repo-Slug.

## Aufgelöste Widersprüche

- `gh-fix-ci`: Lock sagt `openai/skills` (direkt vendored), Registry sagte
  `bachelorprojekt` → Registry auf `external` + upstream aus Lock korrigiert.
- `frontend-design`: `upstream.revision` wich vom Lock ab → auf `lock.ref` gesetzt.

## Entschieden und dokumentiert

- `merged`-Skills (14×, z. B. `git-workflow`, `skill-creator`): aus home +
  Bachelorprojekt zusammengeführt, keine einzelne Vendor-Herkunft → keine
  upstream-Pflicht. Lock-Einträge wo vorhanden bleiben verwaltet, ändern die
  Klassifikation nicht.
- 27 lock-geführte Skills mit Quelle `bachelorprojekt`/`home`/`merged` (u. a. alle
  `huggingface-*`, `gitops-*`, `vitest*`): als via Bachelorprojekt ererbt
  eingefroren (`NON_EXTERNAL_LOCK_TRACKED` im Check). Neue lock-geführte
  nicht-externe Skills fallen rot heraus und erzwingen eine Entscheidung.
- Direkt-externe Skills ohne Lock (`breadboarding`, `mermaid-architecture-diagrams`):
  upstream-Pflicht erfüllt, `vendor_id` = Upstream-Repo-Slug.
