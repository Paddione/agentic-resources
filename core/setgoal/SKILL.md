---
name: setgoal
description: Vage Anfrage in genau einer Fragerunde mit Empfehlungen klären und als idealen Goal-Prompt zur Ablage mit dem goal-Skill übergeben.
---

# Setgoal

Halbgare Anfrage in einen setzbaren Ziel-Prompt verwandeln. Danach nichts implementieren.

## Ablauf

Anfrage und governing Repo-Dateien lesen. Keine breite Suche nach hypothetischen Unklarheiten.

Genau eine Fragerunde stellen: 3 bis 5 Fragen, jede mit Empfehlung und einem Satz Begründung. Dann auf die Antwort warten. Keine zweite Runde, außer die Antwort öffnet einen neuen Sperrpunkt.

Danach den idealen Goal-Prompt ausgeben: Objective, Erfolgskriterien, Scope und Nicht-Ziele, Randbedingungen. Format so wählen, dass er direkt in den goal-Skill oder ein natives Muse-Goal passt.

## Regeln

Entdeckbare Fakten selbst recherchieren; nur Eigner-Entscheidungen fragen. Bereits genannte Fakten nie erneut fragen. Persistenz nur über den goal-Skill und nur auf Wunsch. Ohne Antwort keinen Prompt erfinden.
