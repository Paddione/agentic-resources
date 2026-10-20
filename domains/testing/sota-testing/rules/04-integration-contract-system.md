# Integration und Verträge

Lokal kuratierte Prüfhilfe; keine wiederhergestellte Upstream-Kopie. Repo-Regeln und expliziter Scope gehen vor.

Serializer, DB-Transaktionen, Dateirechte, Broker-ACK und Prozess-Exitcodes gegen die passende reale Grenze prüfen. Isolierte Testdienste verwenden. Verträge müssen Produzent und Konsument abdecken. Gesammelte Testzahl, Skips und Filter gemeinsam mit Exitcode erfassen.

## Auditfragen

Ist ein grüner Lauf leer oder reduziert? Stimmen Fehlerformat, Rückgabewert und Retry-Verhalten auf beiden Seiten überein?

Suchsignale sind nur Kandidaten: `skip`, `xfail`, `only`, `sleep`, leere Assertions und gefangene Exceptions im Kontext prüfen. Ein Treffer allein ist kein Befund.
