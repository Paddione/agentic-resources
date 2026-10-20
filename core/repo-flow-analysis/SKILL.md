---
name: repo-flow-analysis
description: Analysiert Repository- und Agent-Workflows auf Zielabweichungen, unterbrochene Übergaben und Fehlerpfade. Verbindet Soll/Ist-Abgleich, Codegraph, Breadboarding, Laufzeitbelege, Verhaltenstests und Mermaid. Für zusammenhängende Flow-Analysen, nicht für einzelne Diagramme oder bekannte Bugfixes.
---

# Repository-Flows analysieren

Ein Ablauf für O1–O6. Bestehende Fachskills bleiben zuständig; keine zweite Graph-, Test- oder Telemetrie-Infrastruktur installieren. Analyse erlaubt keine Produktänderungen, Deployments oder veröffentlichten Issues. Explizit beauftragte Skill-Updates bleiben erlaubt.

## Einstieg: Realität und Grenzen

Repo aus dem Auftrag bestimmen; bei mehreren plausiblen Repos gezielt klären und unabhängige Bestandsaufnahme fortsetzen. AGENTS.md, repo.yaml, HEAD, Dirty-State und verfügbare Werkzeuge lesen. Fremde Änderungen erhalten, Secrets weder ausgeben noch ohne bestätigtes Unlock lesen.

Vorhandene Skills und deren lokale Referenzen prüfen. Fehlende Ressourcen, nicht ausführbare Werkzeuge oder veraltete Installationsbehauptungen als Capability-Lücke führen. Installiert bedeutet weder lauffähig noch erfolgreich angewendet. Ein festes Datum oder ein historischer Skillname belegt keine Aktualität.

## Reihenfolge und Übergaben

| Schritt | Optionen / Fachskill | Übergabe |
| --- | --- | --- |
| 1. Soll und Inventar | O4: explore | Flow-ID, Akteur, Auslöser, gewünschtes Ergebnis, überprüfbares Erfolgskriterium und Quelle |
| 2. Ist aus Code | O1: codebase-memory + code-analyzer | Revision/Generation, Einstieg, echte Übergaben, Quellanker, Abdeckung und offene Beziehungen |
| 3. Durchgängigkeit | O3: breadboarding | Akteure/Orte, Operationen, Speicher, Kontroll- und Rückgabepfade, Abbruch und Wiederaufnahme |
| 4. Laufzeit | O5: vorhandene Logs/CI/Traces; trace-proof nur für AI-Telemetrie | Umgebung, Zeitraum, Filter, korrelierter Ablauf, Messabdeckung und fehlende Beobachtbarkeit |
| 5. Fehler und Prüfbarkeit | O6: sota-testing im Audit-Modus | Fehlerszenario, erwartetes Verhalten, vorhandener Test, sichere Prüfmöglichkeit, Ergebnis oder ungeprüft |
| 6. Diagramm und Befund | O2: mermaid-architecture-diagrams + O1: code-analyzer | gerendertes, geprüftes Diagramm pro Frage; priorisierte Befunde und kleinste nächste Schritte |

Die O-IDs bleiben stabil; sie sind keine Ausführungsreihenfolge. Bei neuen Widersprüchen gezielt zum betroffenen Schritt zurückkehren. Ein erster Diagrammentwurf darf früher helfen, wird aber erst nach Quellen- und Sichtprüfung als Ergebnis bezeichnet.

## Vollständigkeit begrenzen

Zuerst ein Flow-Inventar erstellen. Pro Flow den Status entdeckt / quellgeprüft / laufzeitgeprüft / fehlerszenariengeprüft / offen führen. Kritische oder häufig gestörte Übergaben zuerst vertiefen. Eine Stichprobe niemals als Analyse aller Flows verkaufen. Auch ohne Laufzeitdaten ist eine begrenzte statische Analyse möglich.

Für jeden Flow Soll und Ist getrennt halten. Ein Ziel braucht eine Nutzerangabe, Anforderung oder aktuelle Doktrin als Quelle; Vermutungen bleiben Hypothesen. Bei Widerspruch zwischen Doku, Konfiguration und Beobachtung den Widerspruch zeigen, nicht still eine Quelle zur Wahrheit erklären.

## Beweiskette

Jede Beziehung als source-verified, runtime-observed, inferred oder unknown kennzeichnen. Graph-Frische und Abdeckung nach codebase-memory prüfen; bei Lücken begrenzte Quellprüfung verwenden. Shell-Aufrufe, dynamische Registrierung und Harness-Hooks benötigen oft Konfigurationsbelege zusätzlich zum Aufrufgraphen.

Laufzeitbelege derselben Revision/Umgebung bevorzugen. Ältere Belege ausdrücklich datieren. Aggregierte Harness-Ereignisse beweisen weder eine erfolgreiche Restore-Kette noch Remote-Ingestion. Leere Logs beweisen keinen ausgefallenen Dienst; unbekannte Tokenwerte sind keine Nullwerte. Logs nur als bereinigte Metadaten erfassen.

Unterscheide bestätigten Defekt, Zielabweichung, Beobachtbarkeitslücke und ungeprüfte Annahme. Fehlende Graph-Kante, hohe Kopplung oder fehlender Test allein beweisen keinen Defekt. Severity und Confidence getrennt begründen; Gegenbelege prüfen.

## Fehlerpfade und sichere Prüfung

Je nach Flow untersuchen: fehlende Quelle/Berechtigung, bestehendes Ziel, unterbrochener Schritt, Wiederholung, Teilzustand, konkurrierender Zugriff und Wiederaufnahme. Nur relevante Szenarien wählen, keine starre Fehlerquote.

Vor Tests Fixtures und Cleanup prüfen. Vorhandene lokale, isolierte Tests bevorzugen; Befehle aus repo.yaml/Repo-Doktrin ableiten. Keine produktiven Fehler injizieren, Dienste neu konfigurieren, fremden Indexer starten oder reale Benutzerdaten bereinigen. Reproducer dürfen temporäre isolierte Verzeichnisse verwenden. Testvorschlag und tatsächlich ausgeführter Test bleiben getrennt.

## Diagrammwahl

- Sequenz: Übergaben, Rückmeldungen, Wartezeiten und Fehlerzweige.
- Zustand: erlaubte Übergänge, Teilzustände, Abbruch, Wiederholung und Wiederaufnahme.
- Datenfluss: Herkunft, Schreib-/Lesepfade und konkurrierende Wahrheiten.
- Soll/Ist: unterschiedliche Wege zum belegten Ziel.

Ein Diagramm beantwortet eine konkrete Frage. Node-/Edge-IDs im Belegregister auf path:line oder Laufzeit-ID abbilden. Unbekannte Beziehungen explizit beschriften. Semantische Farben verwenden; dekorative Glas-/Schattenvorgaben sind für Analyse nicht erforderlich. Breadboarding auf CLI-/Agent-Flows übertragen: sichtbares Ergebnis kann CLI-Ausgabe, Datei oder nachprüfbarer Zustand sein; kein UI künstlich erfinden.

Mit dem Zielrenderer rendern und Bild ansehen. Nur bei tatsächlichen Darstellungsfehlern korrigieren; kein sinnloser Pflicht-Änderungsdurchlauf. Renderer fehlt: vorhandene Alternative prüfen, Installation innerhalb des autorisierten Umfangs durchführen oder Diagramm ausdrücklich als ungeprüften Entwurf führen.

## Abschluss und Handoff

Liefern: Scope/Revision, Flow-Inventar mit Prüfstatus, Soll/Ist und Belege, geprüfte Diagramme, priorisierte Befunde nach code-analyzer, ausgeführte Prüfungen und Grenzen. Für jeden Befund Auswirkung, kleinste Maßnahme und überprüfbares Akzeptanzkriterium nennen. Keine Produktfixes automatisch aus der Analyse ableiten oder ausführen. Ohne expliziten Berichtswunsch genügt Chat; für beauftragte Repo-Artefakte deren lokale Dokumentationskonvention nutzen.
