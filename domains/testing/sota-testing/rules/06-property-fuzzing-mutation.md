# Eigenschaften und Gegenproben

Lokal kuratierte Prüfhilfe; keine wiederhergestellte Upstream-Kopie. Repo-Regeln und expliziter Scope gehen vor.

Eigenschaften aus realen Invarianten ableiten: Idempotenz, Roundtrip oder gültige Zustandsübergänge. Fuzzing auf untrusted Parsergrenzen konzentrieren. Mutation nur für konkrete Unsicherheit, in isolierter Kopie und mit nachgewiesener Rücknahme. Keine Host-Firewall oder Live-Konfiguration verändern.

## Auditfragen

Welche Gegenprobe widerlegt die behauptete Absicherung? Ist nach der Probe der Ausgangszustand wiederhergestellt?

Suchsignale sind nur Kandidaten: `skip`, `xfail`, `only`, `sleep`, leere Assertions und gefangene Exceptions im Kontext prüfen. Ein Treffer allein ist kein Befund.
