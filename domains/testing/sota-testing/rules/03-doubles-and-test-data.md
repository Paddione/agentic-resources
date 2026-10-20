# Doubles und Daten

Lokal kuratierte Prüfhilfe; keine wiederhergestellte Upstream-Kopie. Repo-Regeln und expliziter Scope gehen vor.

Eigene Logik real ausführen, externe Grenzen kontrolliert ersetzen. Ein Fake benötigt dieselben relevanten Vertragseigenschaften wie der reale Dienst. Pro Test unabhängige Daten und explizite Identitäten verwenden; Setup und Cleanup prüfen.

## Auditfragen

Testet ein Mock nur sich selbst? Teilen parallele Tests veränderliche Daten oder IDs?

Suchsignale sind nur Kandidaten: `skip`, `xfail`, `only`, `sleep`, leere Assertions und gefangene Exceptions im Kontext prüfen. Ein Treffer allein ist kein Befund.
