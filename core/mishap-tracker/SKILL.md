---
name: mishap-tracker
description: 'Lokales Friction-Log als Schlussschritt von Runbook-Skills — jeder MISHAP_LOG-Eintrag landet auf stderr und in .mishaps.log (git common dir). Ticket-Verhalten aus repo.tickets in repo.yaml im Consumer-Repo-Root lesen: ohne Ticket-Backend wird nichts angelegt; nur-wenn-tickets brauchen incident/broken/security ein manuelles GitHub-Issue. Trigger: mishap, MISHAP_LOG, friction report, "report what went wrong", mishap-log.py, Schlussschritt von dev-flow-plan, dev-flow-execute, dev-flow-chore, infra-ops, incident-response.'
---

# mishap-tracker — lokales Friction-Log

> Skript-Verweise gelten nur-wenn das Repo sie führt (Bachelorprojekt-Profil); sonst das Repo-Äquivalent aus `repo.yaml` bzw. `AGENTS.md` des Repos. Lifecycle-Mechanik immer über `python3 ~/scripts/agent-workspace.py`.

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

Pro verifiziertem Mishap genau einen Aufruf des gemeinsamen Schreibers (alle Repos):

```bash
python3 ~/scripts/mishap-log.py --class <klasse> --severity <drift|suspicious|degraded|security> \
  --area <komponente> --title "<titel>" --detail "<beschreibung>" [--repo <pfad>]
```

Er hängt eine datierte Zeile mit Klasse an `<git-common-dir>/.mishaps.log` an und
spiegelt sie auf stderr:

```
<ISO-Zeit> [mishap] <severity> <klasse> <komponente> — <titel> :: <beschreibung>
```

- `--class` ist Pflicht und stammt aus dem festen Vokabular `classes:` in
  `~/mishaps.yaml`; unbekannte Klassen, Zeilenumbrüche und Secret-Muster weist
  der Schreiber mit Exit 2 ab und nennt die gültigen Klassen. Passt keine
  Klasse, `other` wählen.
- Erfolgs- und Abschlussmeldungen („alles grün“, „aufgelöst“) als
  `--class resolved-note` loggen; sie zählen nie als Vorfall.
- `broken`/`incident` → `--severity degraded`, `security` bleibt `security`.
- Nie von Hand in `.mishaps.log` schreiben: Zeilen ohne Klasse zählen im
  Report als `unclassified` und machen `G-MISHAP01` rot.
- Auswertung: `python3 ~/scripts/mishap-report.py --table`; wiederkehrende
  Klassen (≥ 2 in 30 Tagen) brauchen einen Fix oder eine begründete
  Schließung in `~/mishaps.yaml:closures`.
- Bachelorprojekt: `scripts/hooks/mishap-tracker.sh --friction … --class <klasse>`
  ist ein dünner Wrapper auf denselben Schreiber.

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
