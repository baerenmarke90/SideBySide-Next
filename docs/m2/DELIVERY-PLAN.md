# M2 Delivery Plan

**Ziel:** M2 als kleine, vertikale und unabhängig prüfbare Produktinkremente liefern  
**Stand:** 24.08.2026

Dieser Plan beginnt erst nach den offenen M0-/M1-Gates. Er legt keine Issue-Nummern an und verändert keine laufenden Issues #5–#11. Jedes Paket ist so geschnitten, dass genau ein Issue, ein Branch und ein Pull Request daraus entstehen kann.

## Eintrittstore

M2-Implementierung startet erst, wenn:

- Transport und Erstregistrierung für Self-Hosted sicher sind,
- Auth-, Tenant- und Concurrency-Invarianten über HTTP abgesichert sind,
- reproduzierbarer Build, Dependency-Scan und OpenAPI-Vertrag stehen,
- Provider- und Protected-Payload-Grenzen tragfähig sind,
- private Autorisierung und Beziehungsprofile abgeschlossen sind,
- die blockierenden M2-Entscheidungen im [Decision Log](./DECISION-LOG.md) geklärt sind.

## Lieferfolge

```text
S0 Readiness
   │
   ├── S1 Attachments ──┐
   │                    ├── S3 Memory + Medien ──┐
   └── S2 Memory CRUD ──┘                        │
                                                ├── S7 Story ── S8 Clients & Hardening
       S4 HeartMoment Privacy ───────────────────┤
       S5 Milestone ─────────────────────────────┤
       S6 Comments + Outbox ─────────────────────┘
```

S4 und S5 können nach S0 parallel zu S1–S3 vorbereitet werden. S7 startet erst, wenn alle vier Quelltypen und ihre Sichtbarkeitsregeln stabil sind.

## S0 – M2 Readiness & Vertragsentscheidungen

**Ergebnis:** implementierbarer, widerspruchsfreier M2-Vertrag.

**Lieferumfang**

- offene Punkte im Decision Log entscheiden,
- Domain- und Privacy-Invarianten bestätigen,
- OpenAPI-Schemas und Error Codes aus `API-DESIGN.md` übernehmen,
- Migration-/Indexplan einschließlich Rollback entwerfen,
- Security-Testfälle als ausführbare Teststruktur anlegen,
- M2-Observability- und Retention-Regeln festhalten.

**Akzeptanz**

- keine blockierende Entscheidung offen,
- API-Lint und Contract-Tests grün,
- Threat Review für Owner-only und Media abgeschlossen,
- jede spätere Slice hat klaren Contract und Testpfad.

## S1 – Attachment Foundation & MediaStore

**Ergebnis:** sichere, fachlich noch ungebundene Attachment-Lifecycle-Basis.

**Lieferumfang**

- `Attachment`-Persistenz und Statusmodell,
- `MediaStore`-Port plus Local- und S3-kompatibler Adapter,
- Create-Upload, Finalize, Validierung, autorisierter Read und Delete,
- zufällige Storage Keys, Größen-/MIME-/Dimensionsprüfungen,
- Cleanup für fehlgeschlagene und verwaiste Uploads,
- Adapter-Contract-Tests und Abuse-Tests.

**Akzeptanz**

- nur validierte Attachments erreichen `READY`,
- beide Adapter bestehen denselben Contract,
- Cross-Tenant-, MIME-Spoof- und Race-Tests grün,
- weder Bucket noch Local Storage sind unautorisiert lesbar.

**Nicht enthalten:** Galerie, Memory-UI, Thumbnailing sofern nicht entschieden.

## S2 – Memory CRUD ohne Medien

**Ergebnis:** Memories mit Autor, fachlichem Datum und sicherer Concurrency.

**Lieferumfang**

- Create/Get/List/Update/Delete,
- `happenedOn` getrennt von `createdAt`,
- Autorprojektion und Space-Scope,
- Protected-Payload-Grenze für Titel/Body,
- Optimistic Concurrency und Fehlervertrag,
- HTTP-, Tenant- und Berechtigungstests.

**Akzeptanz**

- Autor und Partner sehen nur erlaubte Space-Daten,
- Autor kann gemäß entschiedenem Vertrag ändern/löschen,
- veraltete Version führt deterministisch zu `409`,
- Logs/Events enthalten keinen geschützten Inhalt.

## S3 – Memory mit mehreren Medien

**Ergebnis:** eine Memory kann mehrere autorisierte Medien geordnet darstellen.

**Lieferumfang**

- Attachment-Relation und stabile Reihenfolge,
- atomare Bind-/Unbind-Operationen,
- Galerieprojektion für Web und Android,
- Parent-Delete-/Finalize-Race behandeln,
- fehlende/fehlerhafte Medien tolerant darstellen.

**Akzeptanz**

- keine Cross-Space-Bindung,
- Reihenfolge bleibt über Update und Read stabil,
- gelöschte/ungültige Parents hinterlassen keine sichtbaren Orphans,
- kein Attachment verleiht mehr Sichtbarkeit als sein Parent.

## S4 – HeartMoment mit Owner-only Privacy

**Ergebnis:** `SHARED` und `PRIVATE` sind in jedem Zugriffspfad korrekt getrennt.

**Lieferumfang**

- CRUD mit Emotion, Visibility, Datum und optionalem Attachment,
- Owner-only Policy als zentral wiederverwendbare Regel,
- Listen-/Search-/Projection-Filter,
- Privacy-safe Fehlersemantik,
- vollständige Canary- und indirekte Leak-Tests.

**Akzeptanz**

- Partner kann private Einträge weder direkt noch indirekt erkennen,
- Wechsel `SHARED → PRIVATE` entfernt Kommentar-/Story-/Cache-Sichtbarkeit gemäß Vertrag,
- optionales Attachment folgt exakt der Parent-Sichtbarkeit,
- Export-, Event- und Notification-Pfade sind geprüft.

## S5 – Milestone

**Ergebnis:** Milestones sind ein eigenständiges fachliches Modell.

**Lieferumfang**

- CRUD, Autor und `happenedOn`,
- Tenant-/Concurrency-/Protected-Payload-Regeln,
- Projektion für Story und spätere Chapter/Recap-Anknüpfung,
- HTTP- und Isolationstests.

**Akzeptanz**

- keine versteckte Wiederverwendung von Memory-Tabellen oder Typflags,
- Story-relevante Felder sind stabil,
- spätere Erweiterungen erfordern keine M2-Datenmigration aus einem Sammelmodell.

## S6 – Comments, Outbox & Notification Hook

**Ergebnis:** Kommentare funktionieren nur auf erlaubten Shared Targets und erzeugen zuverlässig ein minimales Ereignis.

**Lieferumfang**

- enumerierte Targets `MEMORY`, `MILESTONE`, `HEART_MOMENT`,
- Create/List/Update/Delete gemäß Autorenregel,
- zentrale Target-Existenz- und Sichtbarkeitsprüfung,
- atomarer Outbox-Eintrag bei Kommentar auf fremdem Shared Content,
- idempotente Worker-/Notification-Schnittstelle.

**Akzeptanz**

- kein Kommentar auf private oder fremde Inhalte,
- Domainänderung und Outbox committen atomar,
- Retry erzeugt keine doppelten fachlichen Notifications,
- Event/Preview enthält keine unerlaubten Inhalte.

## S7 – Story Read Model

**Ergebnis:** eine abgeleitete, performante Zeitleiste ohne private Leaks.

**Lieferumfang**

- Query Service für Memory, Milestone und ausschließlich Shared HeartMoment,
- Autor- und Attachment-Projektion,
- Filter `type`, `year`, `q`, `order`, `cursor`, `limit`,
- stabile Cursor-Pagination und Monatsgruppen,
- Query-/Indexanalyse mit realistischen Datenmengen.

**Akzeptanz**

- `PRIVATE` wird vor Suche, Count, Gruppierung und Cursorbildung ausgeschlossen,
- Sortierung und Tie-Breaker entsprechen der Entscheidung,
- Seiten sind stabil und duplikatfrei,
- Read Model ist abgeleitet und keine zweite fachliche Wahrheitsquelle.

## S8 – Erste Web-/Android-Flows & Hardening

**Ergebnis:** derselbe Kernflow funktioniert Ende-zu-Ende auf beiden Clients.

**Lieferumfang**

- Story ansehen, Memory erstellen, mehrere Medien hinzufügen,
- HeartMoment bewusst als Shared oder Private anlegen,
- Lade-/Leer-/Fehler-/Offline-Read-Zustände,
- Accessibility, dynamische Schrift, Touch Targets und Tastaturfluss,
- Cache-Leerung bei Logout/Space-Wechsel,
- End-to-End- und Release-Smoke-Tests.

**Akzeptanz**

- Web und Android verwenden denselben veröffentlichten API-Vertrag,
- Privacy-Entscheidung ist vor dem Speichern verständlich,
- keine Offline-Schreibillusion,
- Kernflow ist mit Screenreader/Tastatur bzw. TalkBack bedienbar.

## Issue-fertige Arbeitspakete

Die folgenden Titel können nach S0 direkt als Issues angelegt werden:

1. **[M2][Media] Attachment-Lifecycle und MediaStore-Contract implementieren**
2. **[M2][Media] LocalMediaStore und S3MediaStore gegen gemeinsamen Contract absichern**
3. **[M2][Memory] Memory CRUD, ProtectedPayload und Concurrency liefern**
4. **[M2][Memory] Mehrere Attachments und geordnete Galerie integrieren**
5. **[M2][Privacy] HeartMoment Shared/Private mit vollständigem Owner-only-Schutz liefern**
6. **[M2][Milestone] Eigenständiges Milestone-Modell und API liefern**
7. **[M2][Comments] Zulässige Targets, Outbox und Notification Hook implementieren**
8. **[M2][Story] Abgeleitetes Read Model mit Suche und Cursor-Pagination liefern**
9. **[M2][Web] Story-, Memory- und Privacy-Kernflow integrieren**
10. **[M2][Android] Story-, Memory- und Privacy-Kernflow integrieren**
11. **[M2][Security] Cross-Tenant-, Owner-only- und Media-Abuse-Suite abschließen**
12. **[M2][Release] Performance, Accessibility und Observability abnehmen**

Jedes Issue übernimmt relevante Zeilen aus der [Security Test Matrix](./SECURITY-TEST-MATRIX.md) als Akzeptanzkriterien. Querschnittsarbeit wird nicht in einem Sammel-PR versteckt.

## PR-Regeln

- ein Issue, ein Branch, ein fachlicher Zweck,
- Migration und Rollback im selben PR wie das Modell,
- Vertrag zuerst oder im selben PR; Clients nie gegen undokumentierte Endpunkte,
- keine Auth-/Tenant-Logik pro Controller duplizieren,
- Security-Tests müssen vor Merge rot demonstrierbar und danach grün sein,
- neue Entscheidungen werden im Decision Log nachgeführt,
- Screens und API werden gemeinsam gegen Leer-, Fehler- und Berechtigungszustände geprüft.

## M2 Exit Criteria

M2 ist abgeschlossen, wenn:

- alle sechs Domänenbausteine produktiv nutzbar sind,
- Web und Android mindestens einen vollständigen Memory-/Media-/Story-Flow teilen,
- private HeartMoments alle Leak-Tests bestehen,
- Local- und S3-Medien denselben Sicherheitsvertrag erfüllen,
- OpenAPI, Migrationen, Observability und Betriebsdokumentation aktuell sind,
- keine kritische oder hohe Security-Lücke offen ist,
- Performancebudgets und Accessibility-Abnahme erfüllt sind,
- echte E2EE weiterhin weder behauptet noch architektonisch verbaut wird.
