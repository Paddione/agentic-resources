---
name: mishap-tracker
description: 'Lokales Friction-Log als Schlussschritt von Runbook-Skills — jeder MISHAP_LOG-Eintrag landet auf stderr und in .mishaps.log (git common dir). Ticket-Verhalten aus repo.tickets in repo.yaml im Consumer-Repo-Root lesen: ohne Ticket-Backend wird nichts angelegt; nur-wenn-tickets brauchen incident/broken/security ein manuelles GitHub-Issue. Trigger: mishap, MISHAP_LOG, friction report, "report what went wrong", scripts/hooks/mishap-tracker.sh, Schlussschritt von dev-flow-plan, dev-flow-execute, dev-flow-chore, infra-ops, incident-response.'
---

# mishap-tracker — lokales Friction-Log

Sammelt Ausführungs-Mishaps **lokal** (stderr + `.mishaps.log` im git common
dir, `git rev-parse --git-common-dir`). Kein Sammel-Container, kein Cycle,
kein Carry-over. Ob zusätzlich ein Ticket angelegt wird, steht in
`repo.tickets` in `repo.yaml` im Consumer-Repo-Root — der Skill erfindet kein
Backend. Aufruf als letzter Schritt von Runbook-Skills, die ein `MISHAP_LOG`
führen. Der Rollup-Automat ist entfernt (`mishap-rollup.sh`,
`ticket.sh rollup-container`, `mishap-buffer.json` in alten Plänen sind
Altlasten, kein aktueller Weg).

## Input

Der aufrufende Skill sammelt ein `MISHAP_LOG` — pro Eintrag:

- `type`: `broken` | `degraded` | `suspicious` | `security` | `drift`
- `title`: kurze, umsetzbare Zusammenfassung
- `description`: was beobachtet wurde und warum es zählt
- `component`: betroffenes Subsystem (z. B. `skills/<name>`, `kubeconfig`)

Runbooks tragen am Dateianfang nur den Zwei-Zeilen-Verweis (ein `MISHAP_LOG`
führen, siehe `mishap-tracker` §Input); die Semantik lebt hier: pro Anomalie,
unerwartetem Zustand, kaputter Komponente, Security-Bedenken oder
Config-Drift — auch wenn irrelevant für die aktuelle Aufgabe — einen Eintrag
mit den vier Feldern anlegen und diesen Skill ganz am Ende aufrufen.

Leeres Log: melden und stoppen — nichts zu tracken.

## Schritt 0: Verifizieren (False-Positive-Guard)

Vor jedem Eintrag Anspruch konkret prüfen:

| Mishap-Typ | Pflichtprüfung |
|---|---|
| `broken` (Import-Cycle) | `grep -r 'import.*<file>' <target>` |
| `broken` (Datei fehlt/veraltet) | `ls` oder `git show HEAD:<file>` |
| `drift` (Versions-Mismatch) | aktuellen Wert per kubectl/grep prüfen |
| `suspicious` (unerwarteter Zustand) | Befehl ausführen, der den Zustand zeigt |
| `security` | immer melden, nie unterdrücken |

Widerspricht die Prüfung der Beobachtung: Mishap streichen und
`[mishap-tracker] SKIP <title> — verified false positive: <reason>` loggen.
Nicht prüfbare Mishaps (z. B. kein Cluster-Zugriff) aufnehmen, aber
`[UNVERIFIED — <reason>]` in die Description schreiben.

## Schritt 1: Klassifizieren

| Typ | Severity | Verhalten |
|---|---|---|
| `incident` | `major` | lokal loggen + siehe Schritt 3 (nur-wenn-tickets) |
| `broken` | `major` | Alias für `incident` |
| `security` | `critical` | Alias für `incident` |
| `degraded` | `minor` | lokal loggen, verwerfen |
| `suspicious` | `minor` | lokal loggen, verwerfen |
| `drift` | `trivial` | lokal loggen, verwerfen |

## Schritt 2: Lokal loggen

Pro verifiziertem Mishap eine Zeile an `.mishaps.log` anhängen und auf stderr
spiegeln:

```
[mishap] <type> <component> — <title> :: <description>
```

Ist der Hook-Skript vorhanden (Pfad über `repo.task_runner` in `repo.yaml`
auflösen, z. B. `scripts/hooks/mishap-tracker.sh`):

```bash
bash <hook-pfad> --friction "<titel>: <beschreibung> [<komponente>]" --severity <minor|major|critical>
```

Das Skript schreibt nach stderr und hängt an `.mishaps.log` an (Exit 0, kein
Backend, kein Buffer). `--ticket` gilt als Legacy-No-op mit Warnung. Sonst
direkt anhängen — kein Buffer, kein Flush.

`incident`/`broken`/`security` zusätzlich als lauten Block drucken — sie
brauchen einen Menschen, keine Automatik meldet sie:

```
!!! MISHAP <type> <component> — <title>
    <description>
```

Ohne aufrufenden Skill-Kontext (kein `MISHAP_LOG`) den einzelnen Eintrag
genauso loggen.

## Schritt 3: Nur-wenn-tickets

`repo.tickets` aus `repo.yaml` im Consumer-Repo-Root lesen:

- `github`: `incident`/`broken`/`security` mit Handlungsbedarf brauchen
  zusätzlich ein **manuelles** GitHub-Issue (Label `incident`). Alles andere
  endet in `.mishaps.log`.
- `none`: alles endet in `.mishaps.log` + stderr, nichts wird angelegt
  (kein Ticket-Backend vorhanden).

## Schritt 4: Summary

Melden: Anzahl geloggter Mishaps (nach Typ); ob ein GitHub-Issue angelegt
wurde (manuell, nur-wenn-tickets); dass alle Einträge in `.mishaps.log`
stehen und dort enden; offene `incident`/`broken`/`security`-Einträge, die
einen Menschen brauchen.

## Verwandte Skills

| Skill | Beziehung |
|-------|-----------|
| `operations-management` | Routing-Hub — dispatcht operative Arbeit |
| Alle Runbooks | Nutzer — jedes Skill schließt mit Mishap-Report |
