# Berechtigungen und Missbrauch

Lokal kuratierte Prüfhilfe; keine wiederhergestellte Upstream-Kopie. Repo-Regeln und expliziter Scope gehen vor.

Relevante Identität×Methode×Pfad-Fälle prüfen: anonym, berechtigt, fremder Nutzer/Tenant, falsche Rolle. Validierung, Injection, SSRF, Limits und Idempotenz nach Angriffsfläche auswählen. Reale DB-Rolle und Poolergrenzen beachten. Ausschließlich autorisierte isolierte Ziele testen, keine Secrets ausgeben.

## Auditfragen

Verweigert der Server fremde Ressourcen auch bei manipulierten IDs? Prüft der Test die echte Berechtigungsgrenze statt nur UI-Sichtbarkeit?

Suchsignale sind nur Kandidaten: `skip`, `xfail`, `only`, `sleep`, leere Assertions und gefangene Exceptions im Kontext prüfen. Ein Treffer allein ist kein Befund.
