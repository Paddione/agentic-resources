# Strategie und Grenzen

Lokal kuratierte Prüfhilfe; keine wiederhergestellte Upstream-Kopie. Repo-Regeln und expliziter Scope gehen vor.

Priorisiere nach Schaden bei Fehlverhalten und Häufigkeit. Lege die verantwortliche Testebene pro Verhalten fest: lokale Logik als Unit, echte I/O-Verträge als Integration, wenige durchgängige Kernpfade als E2E. Graph-Erreichbarkeit ist keine Testabdeckung.

## Auditfragen

Welche kritische Übergabe hat keinen Verhaltensbeleg? Welche Logik wird mehrfach teuer auf UI-Ebene geprüft?

Suchsignale sind nur Kandidaten: `skip`, `xfail`, `only`, `sleep`, leere Assertions und gefangene Exceptions im Kontext prüfen. Ein Treffer allein ist kein Befund.
