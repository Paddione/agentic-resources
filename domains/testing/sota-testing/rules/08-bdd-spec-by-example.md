# Ziel und Beispiele

Lokal kuratierte Prüfhilfe; keine wiederhergestellte Upstream-Kopie. Repo-Regeln und expliziter Scope gehen vor.

Given beschreibt Zustand, When den fachlichen Auslöser, Then das beobachtbare Ergebnis. Anforderungen mit konkreten Erfolgs- und Fehlerbeispielen verknüpfen. Gherkin nur einsetzen, wenn eine gemeinsame fachliche Leserschaft davon profitiert.

## Auditfragen

Belegt jedes Szenario eine Anforderung? Wurde ein Klickskript statt eines Ergebnisses beschrieben?

Suchsignale sind nur Kandidaten: `skip`, `xfail`, `only`, `sleep`, leere Assertions und gefangene Exceptions im Kontext prüfen. Ein Treffer allein ist kein Befund.
