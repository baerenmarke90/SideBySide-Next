# M2 Project Control

**Stand:** 26.08.2026  
**Status:** M2 abgeschlossen; G2 bestanden; M3 freigegeben  
**Aktueller `main`:** `3a7adc28643ef00de51db678ec77a82be652283d` (Merge von #170)

## Verbindlicher Gate-Stand

Der datierte [finale G2 Gate Review](../reviews/2026-08-26-g2-final-gate-review.md) ist die aktuelle Gate-Entscheidung:

- **G2: BESTANDEN**
- **M2: ABGESCHLOSSEN**
- **M3: FREIGEGEBEN**
- die M3-S0-Readiness ist abgeschlossen; alle M3-D01 bis M3-D32 stehen auf `DECIDED`
- M3-Runtime-Slices dürfen gemäß `docs/m3/README.md` und `docs/m3/DELIVERY-PLAN.md` beginnen, sobald der jeweilige produktive REST-/OpenAPI-Vertrag contract-testbar konkretisiert ist
- öffentliche/Managed-Exposition ist noch nicht freigegeben; #59 und #60 bleiben Pre-Exposure-Gates
- #25 bleibt Repository-Hardening

Ältere datierte Reviews bleiben historische Snapshots und werden nicht umgeschrieben. Insbesondere der frühere G2-Zwischenreview bleibt unverändert als Nachweis des damaligen, noch unvollständigen Gate-Stands erhalten.

## Milestone-Grenzen

### M2 – Erinnern / Story Alpha

M2 liefert Domain und API für Attachment, Memory, HeartMoment, Milestone, Comment und Story sowie **minimale vertikale Referenzflows** auf Web und Android. Diese Referenzflows beweisen den kritischen End-to-End-Vertrag; sie bedeuten noch keine vollständige Client-Parität.

Der G2-Mindestnachweis wurde vollständig erbracht:

- M2-Domain und versionierter API-Vertrag vollständig für den G2-Scope; Attachment/Media ist auf Bilder begrenzt,
- Tenant-/Owner-only-/Media-Security-Gates grün,
- realer kritischer Memory/Media/Story-Flow auf Web und Android gegen denselben SideBySide-Stack validiert,
- keine hohe/kritische offene M2-Security-/Privacy-/Datenintegritätslücke,
- aktuelle CI-, Secret-Scan-, Supply-Chain- und Deployment-Gates grün.

Die manuelle Accessibility-Abnahme ist bewusst **kein G2-Blocker mehr**. Sie wurde nicht als bestanden behauptet und bleibt Teil von M5/G4 als finale Client-/Release-QA.

Globale Volltextsuche ist kein G2-Bestandteil. Story benötigt für G2 `type`, `year`, `order`, `cursor` und `limit`; globale Suche gehört zu M4-A.

### M3 – Planen & Private Area

Wishes, Plans, Places, Chapters, Collections und Private Area. Die fachliche S0-Readiness ist abgeschlossen; alle M3-D01 bis M3-D32 stehen auf `DECIDED`. Verbindliche nächste Quelle ist das [M3 Technical Readiness Package](../m3/README.md) mit dem [M3 Delivery Plan](../m3/DELIVERY-PLAN.md).

Private Area ist eine Security-Domain mit harter `OWNER_ONLY`-Semantik, kein rein visueller Ordner. Runtime startet sliceweise und erst mit eindeutig contract-testbarem produktivem REST-/OpenAPI-Vertrag.

### M4 – Begleiten

Der Milestone bleibt fachlich zusammenhängend, wird aber intern in drei lieferbare Slices getrennt:

- **M4-A:** Search + Dashboard Read Models
- **M4-B:** Activity + Notifications
- **M4-C:** Reminders + Rules

### M5 – Client Completion & Parity

M5 vervollständigt Web und Android: vollständige Domainintegration, Navigation, Deep Links, Read Cache, Export/Import, Accessibility, Performance und systematische Feature-Parität. Die M2-Referenzflows werden hier produktreif vervollständigt; die verschobene manuelle Accessibility-Abnahme findet hier statt.

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
5. **#78 Media-Metadaten** — M2-D14 (Strippen beim Ingest) und M2-D15 (eine abgeleitete Variante, kein Transcoding) entschieden. Beide waren als `BEFORE_CLIENTS` eingestuft, griffen aber in den Ingest-Pfad und wurden deshalb auf `BLOCKING` gehoben.
6. **#85 Media-Reihenfolge** — M2-D23: Bilder zuerst mit Pillow und pillow-heif. Video wurde zunächst als eigener Slice vorgesehen und ist inzwischen als Future-Backlog #88 außerhalb von M2/G2 verschoben.

Die für M2 relevanten `BLOCKING`-Entscheidungen wurden vor dem jeweiligen Runtime-Code geschlossen. `BEFORE_CLIENTS`-Punkte zu Notification Preview, Export/Backup, Client-Cache und Suchindex werden in den zuständigen späteren Milestones behandelt.

Während der Umsetzung kamen vier weitere `BLOCKING`-Entscheidungen dazu, die erst am Code oder am nächsten Slice sichtbar wurden. Alle wurden vor dem sie tragenden Code geschlossen, wie es die Runtime-Startregel verlangt:

- **M2-D23** (#85) — Reihenfolge und Parser der Medienverarbeitung.
- **M2-D24** (#79) — Lesezugriff auf noch ungebundene Attachments.
- **M2-D25** (#94) — Schreibrechte für Milestone.
- **M2-D22** (#104) — Owner-Ansicht für private HeartMoments. War als `BEFORE_CLIENTS` eingestuft, formt aber die Story-Route und wurde deshalb vor S7 auf `BLOCKING` gehoben.

## Runtime-Startregel

Ein Runtime-Slice startet erst, wenn **alle für genau diesen Slice relevanten BLOCKING-Decisions** `DECIDED` sind und sein versionierter OpenAPI-Vertrag contract-testbar vorliegt. Runtime-Code entscheidet keine offene Frage stillschweigend: stößt ein Slice auf eine ungeklärte Frage, wird sie als Decision-Log-Eintrag geschlossen, nicht im Code beantwortet.

Diese Regel gilt auch für M3 und spätere Milestones. Der Abschluss eines Milestone-Gates ersetzt nicht die slice-spezifische Vertrags- und Reuse-Prüfung.

## M2-Lieferstand

### Geliefert

- #71 — Memory CRUD ohne Medien (PR #77). Validiert M2-Migrationstil, ProtectedPayload-Grenze, Tenant Guard, Autorregel, Optimistic Concurrency und signierten Keyset-Cursor auf einer medienfreien Fläche.
- #80 — HeartMoment mit Owner-only-Privacy (PR #84). Erster Typ mit echter Nutzerentscheidung zur Sichtbarkeit; `SHARED -> PRIVATE` als eigene atomare Operation, Emotion als ProtectedPayload.
- #79 — Attachment-Lifecycle für Bilder (PR #89). Statusautomat, LocalMediaStore, asynchrone Validierung mit Strippen nach M2-D14 und Thumbnail nach M2-D15, autorisiertes Lesen, Retention und Cleanup. Video bleibt fail-closed und ist außerhalb von M2/G2 in #88 vorgemerkt.
- #90 — Attachments an Memory und HeartMoment binden (PR #93). `MemoryAttachment` mit stabiler `position`, HeartMoment mit höchstens einem Attachment, atomares Bind/Unbind im Bindungsfenster aus M2-D20, keine Cross-Space- und keine Mehrfachbindung nach M2-D03.
- #94 — Milestone-Domain und API (PR #95). Eigenes Modell statt Typflag auf Memory; M2-D25 hält die Autorregel aus M2-D01 auch hier.
- #97 — Comments, Outbox und Notification Hook (PR #98). Create/List am Parent verschachtelt, Update/Delete space-scoped, enumerierte Targets, atomarer Outbox-Eintrag und idempotenter Retry. Schließt die Zusage aus #80.
- #87 — S3-kompatibler MediaStore-Adapter (PR #100). Presigned Upload und Read-URL mit den TTLs aus M2-D13, gegen denselben Contract-Test wie der lokale Adapter.
- #113 — Story Read Model und `/timeline` (PR #114). Abgeleitete Zeitleiste über Memory, Milestone und ausschließlich gemeinsame HeartMoments; Sortierschlüssel `(effectiveDate, createdAt, kindRank, id)` und Keyset-Cursor nach M2-D08. Private HeartMoments sind nie Story-Items, auch nicht für ihren Owner (M2-D22). Kein persistiertes Read Model.
- S8 — dünne Web-/Android-Referenzflows: geliefert.
- #144 — realer Web-/Android-G2-E2E-Nachweis gegen API, Worker, PostgreSQL und LocalMediaStore: geliefert.
- #147 / PR #170 — finaler G2 Gate Review: **G2: BESTANDEN**.

### Future-Backlog außerhalb von M2/G2

- #88 — `Future: Video-Uploads und Posterframes`

#88 wird nicht jetzt umgesetzt. Der Prototyp #109 wurde wegen eines Produktions-Images von rund 755 MiB sowie des zusätzlichen ffmpeg-Betriebs-, Supply-Chain- und Security-Aufwands bewusst ohne Merge geschlossen. `main` bleibt für MP4 und QuickTime fail-closed. Eine Wiederaufnahme benötigt eine neue Architektur- und Security-Entscheidung, die insbesondere ein separates optionales Processing-Modell statt eines aufgeblähten gemeinsamen Images bewertet.

### Zusage aus #80 — erfüllt

Der in M2-D07 verlangte atomare Comment-Delete beim Wechsel `SHARED -> PRIVATE` hing an `_delete_dependent_comments` und war ohne Comments nicht beweisbar. Mit #97 ist die Cascade verdrahtet — zusätzlich abgesichert durch die Mapper-Listener in `comments/cascades.py` — und in `test_shared_to_private_loescht_comments_und_resurrected_nichts` belegt. Der Merkposten ist damit geschlossen.

## G2 — abgeschlossen

Verbindliche Entscheidungsquelle ist der [finale G2 Gate Review](../reviews/2026-08-26-g2-final-gate-review.md). Er bewertet G2 ausdrücklich als **BESTANDEN**.

Damit ist M2 formal abgeschlossen. M3 ist der freigegebene nächste Milestone. Der erste geplante Runtime-Slice ist M3-S1 **Wish Foundation**; sein Vertrag und seine Verifikation werden im M3-Paket gesteuert.

## Aktive Statusquellen

Die laufenden Statusquellen sind auf denselben Stand synchronisiert:

- [`README.md`](../../README.md)
- [`docs/ROADMAP.md`](../ROADMAP.md)
- [`docs/IMPLEMENTATION-STATUS.md`](../IMPLEMENTATION-STATUS.md)
- [`docs/m2/PROJECT-CONTROL.md`](./PROJECT-CONTROL.md)

Aktuelle M3-Steuerung:

- [`docs/m3/README.md`](../m3/README.md)
- [`docs/m3/DELIVERY-PLAN.md`](../m3/DELIVERY-PLAN.md)

Historische Reviews bleiben bewusst unverändert und dürfen daher frühere Gate-Stände enthalten.
