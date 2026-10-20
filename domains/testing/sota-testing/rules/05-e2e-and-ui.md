# Durchgängige Pfade

Lokal kuratierte Prüfhilfe; keine wiederhergestellte Upstream-Kopie. Repo-Regeln und expliziter Scope gehen vor.

E2E auf beobachtbare Nutzerergebnisse begrenzen. Stabile rollen-/labelbasierte Selektoren und zustandsbasierte Wartebedingungen verwenden. Auth und Daten isolieren. Für CLI-Flows Ausgaben, Dateien und Zustände prüfen, keine künstliche UI verlangen.

## Auditfragen

Belegt der Test das Ergebnis oder nur Klicks? Bleibt ein Fehlerzustand für Nutzer sichtbar?

Suchsignale sind nur Kandidaten: `skip`, `xfail`, `only`, `sleep`, leere Assertions und gefangene Exceptions im Kontext prüfen. Ein Treffer allein ist kein Befund.
