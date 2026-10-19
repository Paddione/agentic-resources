# Fortsetzungs-Kontrakt für angefangene Branches

Referenz zu `dev-flow-execute`. Fortschritt lebt in Repo-Dateien (Commits, `phase-events.log`), nicht in einer DB. Ticket-Pfad (Hold-Gate, `reclaim`, Factory-Events) nur bedingt, siehe unten.

Der Kontrakt gilt für **Mensch und Automation gleichermaßen**. Es gibt bewusst keinen zweiten Ausführungs-Skill (E1).

## Fortsetzung statt Neubeginn

Liegt auf dem Branch bereits Arbeit, wird sie **fortgesetzt**, nicht wiederholt.

- **Erledigte Partials erkennt allein die `phase-events.log`-Auswertung** (`.agents/plans/<slug>/phase-events.log`, Zeilen `<phase> <state> …`). Keine zweite Fortschrittsquelle (keine Commit-Betreffs, keine Plan-Checkboxen) — zwei Quellen driften auseinander, ohne Regel, welche gewinnt.
- **Der Worktree entsteht, bevor das Partial-Manifest gelesen wird.** Sonst liegt `.agents/plans/<slug>/tasks.d/` noch nicht auf Platte, `readPartials` liefert nichts, und der LLM-Decompose-Fallback erzeugt die volle Taskliste — bereits geleistete Arbeit wiederholt sich.
- **Jeder Rückfall auf LLM-Decompose wird protokolliert**, ebenso Fehlschläge der Log-Abfrage und übersprungene Partials. Stille Fallbacks sehen aus wie der Normalfall.

## Der Branch ist anderswo ausgecheckt

Hält ein anderer Worktree den Branch, **zurückstellen statt blockieren**: Slot freigeben, später regulär wieder aufgreifen. Kein `blocked`-Status — ohne Queue gibt es nichts, das ihn auswertet.

Erkannt an Markerzeile `branch in use` und **Exit-Code 3** aus `scripts/worktree-create.sh`. Die Erkennung sitzt bewusst im Skript, nicht als Regex auf `git worktree add`-Meldungen (Wortlaut wechselt je git-Version).

Für den menschlichen Ausführer: **ein Branch, der kurz nicht anläuft, ist kein Defekt, sondern eine belegte Ressource.**

## Manuelle Übernahme

Wer einen angefangenen Branch manuell übernimmt, liest zuerst `phase-events.log` und die Commits — dann derselbe Kontrakt: fortsetzen, nicht wiederholen. Kein Readiness-Flag, kein Übernahmeschutz.

## Nur mit Ticket-Backend (`repo.tickets` gesetzt)

- **Hold-Gate:** `readiness.execution_released=false` bleibt Default; Freigabe ist menschliche Entscheidung. Fortsetzungsfähigkeit ersetzt die Freigabe nicht.
- **`reclaim` ist Notausstieg**, kein Regelweg; keine Automatik löst ihn aus.
- Factory/Watchdog/`queue.sh`/`unfactory`-Abschnitte sind historisch und nicht auszuführen.

## Was davon testbar ist

**Struktur und Verzweigung**: Aufrufreihenfolge, Markerzeile, Exit-Code, Abwesenheit harter Abbrüche im Fremdbesitz-Zweig. Kein DB-Roundtrip — das ist Absicht.
