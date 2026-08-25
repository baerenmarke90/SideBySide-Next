# M2 Project Control

**Stand:** 25.08.2026  
**Status:** M2-S0 aktiv; M2-Runtime noch durch S0-Entscheidungen gesperrt  
**Aktueller `main` bei Start:** `76f5f086e1228662c22147590d5e85eac70e6fb4`

## Verbindlicher Gate-Stand

Der datierte [G1 Gate Review nach Abschluss von #61](../reviews/2026-08-25-g1-gate-review-after-61.md) ist die aktuelle Gate-Entscheidung:

- **G1: BESTANDEN**
- **M2-S0: FREIGEGEBEN**
- interne M2-Domainimplementierung ist nach Abschluss der jeweils blockierenden S0-Entscheidungen zulässig
- öffentliche/Managed-Exposition ist noch nicht freigegeben; #59 und #60 bleiben Pre-Exposure-Gates
- #25 bleibt Repository-Hardening

Ältere datierte Reviews bleiben historische Snapshots und werden nicht umgeschrieben.

## Milestone-Grenzen

### M2 – Erinnern / Story Alpha

M2 liefert Domain und API für Attachment, Memory, HeartMoment, Milestone, Comment und Story sowie **minimale vertikale Referenzflows** auf Web und Android. Diese Referenzflows beweisen den kritischen End-to-End-Vertrag; sie bedeuten noch keine vollständige Client-Parität.

**G2-Mindestnachweis:**

- M2-Domain und versionierter API-Vertrag vollständig für den G2-Scope,
- Tenant-/Owner-only-/Media-Security-Gates grün,
- mindestens ein kritischer Memory/Media/Story-Flow auf Web und Android technisch validiert,
- keine hohe/kritische offene M2-Security-Lücke,
- Accessibility-/Privacy-Nachweis für die Referenzflows.

Globale Volltextsuche ist **nicht zwingender G2-Bestandteil**. Story benötigt für G2 mindestens `type`, `year`, `order`, `cursor` und `limit`. Eine globale `q`-Suche gehört grundsätzlich zu M4, sofern S0 sie nicht mit begründetem Beschluss enger für M2 benötigt.

### M3 – Planen & Private Area

Wishes, Plans, Places, Chapters, Collections und Private Area. Relation-Lifecycle wie `Wish -> Plan -> erlebt -> optional Chapter` wird vor Implementierung fachlich festgelegt. Private Area ist eine Security-Domain mit harter `OWNER_ONLY`-Semantik, kein rein visueller Ordner.

### M4 – Begleiten

Der Milestone bleibt fachlich zusammenhängend, wird aber intern in drei lieferbare Slices getrennt:

- **M4-A:** Search + Dashboard Read Models
- **M4-B:** Activity + Notifications
- **M4-C:** Reminders + Rules

### M5 – Client Completion & Parity

M5 vervollständigt Web und Android: vollständige Domainintegration, Navigation, Deep Links, Read Cache, Export/Import, Accessibility, Performance und systematische Feature-Parität. M2-Referenzflows werden hier produktreif vervollständigt.

### M6–M9

M6 Rich Features, M7 Integrationen, M8 freiwilliger Context und M9 Productization bleiben in ihrer Reihenfolge bestehen. M9 ist das Launch-Gate für Managed/Self-Hosted-Betrieb einschließlich Pre-Exposure-Härtungen, Backup/Restore, Update/Rollback, Retention/Löschung, Monitoring, Entitlements und Supportfähigkeit.

## Privacy-Begriffe

- `SHARED` / `PRIVATE`: öffentliche fachliche Domainwerte, wenn eine Ressource eine Nutzerentscheidung zur Sichtbarkeit besitzt.
- `SPACE_SHARED` / `OWNER_ONLY`: interne Authorization-/Privacy-Klassen.
- Clients schreiben `privacyClass` nicht redundant als zweite Wahrheitsquelle.
- `PRIVATE` wird serverseitig als `OWNER_ONLY` durchgesetzt; Clientfilter sind keine Sicherheitsgrenze.

## M2-S0 Arbeitsfolge

1. **#67 Planning:** aktive Projektsteuerung auf G1=bestanden und die hier definierten Milestone-Grenzen synchronisieren.
2. **#68 Domain/Privacy:** Memory-, Comment-, HeartMoment- und Event-/Delete-Entscheidungen schließen.
3. **#69 Media:** Attachment-Relation, Limits, Validation, Retention, Uploadtransport und Orphan-Regeln schließen.
4. **#70 API:** Routen, DTOs, Error Codes, Concurrency, Pagination und Story-Sortierung in den versionierten Contract überführen.
5. **#71 Memory Runtime:** erster medienfreier M2-Runtime-Slice nach Erfüllung seiner S0-Abhängigkeiten.

#68 und #69 dürfen nach stabiler #67-Grenze parallel vorbereitet werden. #70 konsumiert die Entscheidungen aus #68/#69. Runtime-Code entscheidet keine offene BLOCKING-Frage stillschweigend.

## Runtime-Startregel

M2 ist freigegeben, aber S0 ist noch nicht abgeschlossen. Ein Runtime-Slice startet erst, wenn **alle für genau diesen Slice relevanten BLOCKING-Decisions** `DECIDED` sind und sein versionierter OpenAPI-Vertrag contract-testbar vorliegt. Dadurch kann Memory CRUD ohne Medien vor Abschluss nicht relevanter späterer Cliententscheidungen beginnen, ohne Media-/Privacy-Fragen vorwegzunehmen.