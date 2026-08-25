# M2 Project Control

**Stand:** 25.08.2026  
**Status:** M2-S0 abgeschlossen; M2-Runtime läuft  
**Aktueller `main`:** `f20b257` (Merge von #118)

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

## M2-S0 — abgeschlossen

1. **#67 Planning** — Projektsteuerung auf G1=bestanden und die hier definierten Milestone-Grenzen synchronisiert.
2. **#68 Domain/Privacy** — Memory-, Comment-, HeartMoment- und Event-/Delete-Entscheidungen geschlossen.
3. **#69 Media** — Attachment-Relation, Limits, Validation, Retention, Uploadtransport und Orphan-Regeln geschlossen.
4. **#70 API** — Routen, DTOs, Error Codes, Concurrency, Pagination und Story-Sortierung in den versionierten Contract überführt.
5. **#78 Media-Metadaten** — M2-D14 (Strippen beim Ingest) und M2-D15 (eine abgeleitete Variante, kein Transcoding) entschieden. Beide waren als `BEFORE_CLIENTS` eingestuft, greifen aber in den Ingest-Pfad und wurden deshalb auf `BLOCKING` gehoben.
6. **#85 Media-Reihenfolge** — M2-D23: Bilder zuerst mit Pillow und pillow-heif, Video mitsamt ffmpeg als eigener Slice.

Offen bleiben nur `BEFORE_CLIENTS`-Punkte — M2-D10, D17, D18 und D21 —, die erst vor stabiler Web-/Android-Integration fällig sind und keinen Backend-Slice blockieren.

Während der Umsetzung kamen vier weitere `BLOCKING`-Entscheidungen dazu, die erst am Code oder am nächsten Slice sichtbar wurden. Alle wurden vor dem sie tragenden Code geschlossen, wie es die Runtime-Startregel verlangt:

- **M2-D23** (#85) — Reihenfolge und Parser der Medienverarbeitung.
- **M2-D24** (#79) — Lesezugriff auf noch ungebundene Attachments.
- **M2-D25** (#94) — Schreibrechte für Milestone.
- **M2-D22** (#104) — Owner-Ansicht für private HeartMoments. War als `BEFORE_CLIENTS` eingestuft, formt aber die Story-Route und wurde deshalb vor S7 auf `BLOCKING` gehoben — dieselbe Anhebung wie bei M2-D14 und M2-D15 in #78.

## Runtime-Startregel

Ein Runtime-Slice startet erst, wenn **alle für genau diesen Slice relevanten BLOCKING-Decisions** `DECIDED` sind und sein versionierter OpenAPI-Vertrag contract-testbar vorliegt. Runtime-Code entscheidet keine offene Frage stillschweigend: stößt ein Slice auf eine ungeklärte Frage, wird sie als Decision-Log-Eintrag geschlossen, nicht im Code beantwortet.

Diese Regel bleibt auch nach Abschluss von S0 in Kraft — sie gilt für jede neu auftauchende Frage, nicht nur für die ursprüngliche S0-Liste.

## Aktuelle GitHub-Arbeitspakete

- #88 — `[M2][Media] Video und Posterframes im Attachment-Lifecycle ergänzen` (S1-c)
- #102 — `[P1][Tooling] OpenAPI Generator für Web- und Android-Clients einführen`

Der Story-Vertrag ist mit seiner über `kind` diskriminierten Union der erste, bei dem handgepflegte Client-DTOs auf beiden Plattformen teuer würden. #102 wirkt deshalb am stärksten, solange die Clientflächen aus S8 noch nicht existieren.

#88 muss vor seiner Umsetzung die ffmpeg-Frage klären, weil ein Systembinary Container-Image und Installationsanleitung betrifft und sich dem `uv audit`-Gate entzieht. Ein Branch mit Vorarbeit besteht, ein Pull Request steht noch aus.

Noch nicht angelegt ist allein das Arbeitspaket für die dünnen Client-Referenzflows (S8). Mit S7 ist die M2-Domain vollständig; für G2 fehlt nur noch der End-to-End-Nachweis auf Web und Android.

#102 ist kein M2-Slice, sondern eine Tooling-Vorarbeit. Sie wirkt am stärksten, solange die Clientflächen aus S8 noch nicht existieren.

### Zusage aus #80 — erfüllt

Der in M2-D07 verlangte atomare Comment-Delete beim Wechsel `SHARED -> PRIVATE` hing an `_delete_dependent_comments` und war ohne Comments nicht beweisbar. Mit #97 ist die Cascade verdrahtet — zusätzlich abgesichert durch die Mapper-Listener in `comments/cascades.py` — und in `test_shared_to_private_loescht_comments_und_resurrected_nichts` belegt. Der Merkposten ist damit geschlossen.

### Geliefert

- #71 — Memory CRUD ohne Medien (PR #77). Validiert M2-Migrationstil, ProtectedPayload-Grenze, Tenant Guard, Autorregel, Optimistic Concurrency und signierten Keyset-Cursor auf einer medienfreien Fläche.
- #80 — HeartMoment mit Owner-only-Privacy (PR #84). Erster Typ mit echter Nutzerentscheidung zur Sichtbarkeit; `SHARED -> PRIVATE` als eigene atomare Operation, Emotion als ProtectedPayload.
- #79 — Attachment-Lifecycle für Bilder (PR #89). Statusautomat, LocalMediaStore, asynchrone Validierung mit Strippen nach M2-D14 und Thumbnail nach M2-D15, autorisiertes Lesen, Retention und Cleanup. Video bleibt nach M2-D23 fail-closed.
- #90 — Attachments an Memory und HeartMoment binden (PR #93). `MemoryAttachment` mit stabiler `position`, HeartMoment mit höchstens einem Attachment, atomares Bind/Unbind im Bindungsfenster aus M2-D20, keine Cross-Space- und keine Mehrfachbindung nach M2-D03.
- #94 — Milestone-Domain und API (PR #95). Eigenes Modell statt Typflag auf Memory; M2-D25 hält die Autorregel aus M2-D01 auch hier.
- #97 — Comments, Outbox und Notification Hook (PR #98). Create/List am Parent verschachtelt, Update/Delete space-scoped, enumerierte Targets, atomarer Outbox-Eintrag und idempotenter Retry. Schließt die Zusage aus #80.
- #87 — S3-kompatibler MediaStore-Adapter (PR #100). Presigned Upload und Read-URL mit den TTLs aus M2-D13, gegen denselben Contract-Test wie der lokale Adapter.
- #113 — Story Read Model und `/timeline` (PR #114). Abgeleitete Zeitleiste über Memory, Milestone und ausschließlich gemeinsame HeartMoments; Sortierschlüssel `(effectiveDate, createdAt, kindRank, id)` und Keyset-Cursor nach M2-D08. Private HeartMoments sind nie Story-Items, auch nicht für ihren Owner (M2-D22). Kein persistiertes Read Model.

## Aktive Statusquellen

Die laufenden Statusquellen sind auf denselben Stand synchronisiert:

- [`README.md`](../../README.md)
- [`docs/ROADMAP.md`](../ROADMAP.md)
- [`docs/IMPLEMENTATION-STATUS.md`](../IMPLEMENTATION-STATUS.md)

Historische Reviews bleiben bewusst unverändert und dürfen daher frühere Gate-Stände enthalten.
