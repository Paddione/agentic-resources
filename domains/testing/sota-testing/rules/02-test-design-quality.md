# Aussagekraft und Determinismus

Lokal kuratierte Prüfhilfe; keine wiederhergestellte Upstream-Kopie. Repo-Regeln und expliziter Scope gehen vor.

Ein Test muss bei relevant falschem Verhalten scheitern. Prüfe Ergebnis, Status und Nebenwirkung statt nur Quelltext oder Mock-Aufrufe. Kontrolliere Uhr, Zufall und externe Dienste. Ein erfolgreicher echter Netzwerkaufruf beweist keine Isolation. Egress-Proben nur in isolierter Umgebung.

## Auditfragen

Könnte die Assertion auch bei kaputter Implementierung bestehen? Werden Exceptions verschluckt oder Sleeps als Synchronisierung benutzt?

Suchsignale sind nur Kandidaten: `skip`, `xfail`, `only`, `sleep`, leere Assertions und gefangene Exceptions im Kontext prüfen. Ein Treffer allein ist kein Befund.
