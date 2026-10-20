# Suite und CI

Lokal kuratierte Prüfhilfe; keine wiederhergestellte Upstream-Kopie. Repo-Regeln und expliziter Scope gehen vor.

CI-Trigger, Pfadfilter, Required Checks, Discovery und Artefakte gegen tatsächliche Jobs prüfen. Retries getrennt vom ersten Ergebnis ausweisen. Flakes brauchen Ursache und begrenzte Quarantäne. Coverage nur innerhalb derselben Population vergleichen; keine Prozentziele als Qualität ausgeben.

## Auditfragen

Laufen die betroffenen Tests überhaupt? Teilen unabhängige Läufe einen Dienst? Verstecken Skips oder Retries Fehler?

Suchsignale sind nur Kandidaten: `skip`, `xfail`, `only`, `sleep`, leere Assertions und gefangene Exceptions im Kontext prüfen. Ein Treffer allein ist kein Befund.
