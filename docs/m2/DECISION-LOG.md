# M2 Decision Log

**Stand:** 25.08.2026  
**Regel:** Eine offene Frage wird nicht stillschweigend im Code entschieden.

Dieses Log trennt Spezifikationsaussagen von Umsetzungsvorschlägen. `PROPOSED` ist nicht bindend. `DECIDED` benötigt Datum, Entscheider und Verweis auf ADR, Spec oder Issue.

## Status und Priorität

- `OPEN` – Entscheidung fehlt.
- `PROPOSED` – bevorzugte Option liegt vor, Freigabe fehlt.
- `DECIDED` – verbindlich dokumentiert.
- `BLOCKING` – vor der ersten betroffenen Implementation entscheiden.
- `BEFORE_CLIENTS` – vor stabiler Web-/Android-Integration entscheiden.
- `LATER` – bewusst nach M2 verschiebbar, solange die Grenze offen bleibt.

## Entscheidungen

| ID | Priorität | Status | Owner | Frage | Vorschlag / nächste Aktion |
|---|---|---|---|---|---|
| M2-D01 | BLOCKING | DECIDED | Product + Domain | Darf der Partner eine Memory des Autors ändern oder löschen? | Nein. Beide aktiven Partner lesen gemeinsame Memories; Update/Delete bleiben ausschließlich beim unveränderlichen Autor. Siehe Entscheidung unten / #68. |
| M2-D02 | BLOCKING | DECIDED | Domain + API | Erhalten Kommentare ein `version`-Feld für Optimistic Concurrency? | Ja. Editierbare Comments erhalten `version`; Update/Delete verlangen dieselbe If-Match-/409-Semantik wie andere veränderbare Ressourcen. Siehe #68. |
| M2-D03 | BLOCKING | DECIDED | Domain + Data | Wie werden mehrere Attachments gebunden: exklusive Ownership, Wiederverwendung, Join-Entity und Sortierreihenfolge? | Exklusive Bindung an höchstens einen Parent; MemoryAttachment mit stabiler `position`; keine Cross-Space-/Mehrfachbindung. Siehe #69. |
| M2-D04 | BLOCKING | DECIDED | Security + Product | Welche MIME-Typen, Dateigrößen, Pixelgrenzen und Videodauern gelten je Plattform? | JPEG/PNG/WebP/HEIC/HEIF ≤25 MiB/40 MP/12k px; MP4/QuickTime ≤250 MiB/180 s/4K; Memory ≤20 Attachments/500 MiB. Siehe #69. |
| M2-D05 | BLOCKING | DECIDED | Backend + Ops | Erfolgt Media-Validierung synchron beim Finalize oder asynchron? Welche internen Zustände sind nötig? | Asynchron; `PENDING/UPLOADING/VALIDATING/READY/FAILED/DELETING/DELETE_FAILED`. Siehe #69. |
| M2-D06 | BLOCKING | DECIDED | Security + Privacy | Wird Emotion bei HeartMoment als Metadatum oder ProtectedPayload klassifiziert? | ProtectedPayload. Emotion ist sensibler Beziehungsinhalt und darf nicht als Analytics-/Event-/Log-Metadatum verwendet werden. Siehe #68. |
| M2-D07 | BLOCKING | DECIDED | Domain + Privacy | Was geschieht mit Kommentaren beim Wechsel eines HeartMoment von `SHARED` zu `PRIVATE`? | Wechsel ist nur als atomare Privacy-Operation zulässig; vorhandene Kommentare werden in derselben DB-Transaktion gelöscht. Keine Partnerprojektion darf danach verbleiben. Siehe #68. |
| M2-D08 | BLOCKING | DECIDED | API + Data | Welche Story-Sortierung gilt bei fehlendem `happenedOn`, und welcher Tie-Breaker stabilisiert Cursor? | `effectiveDate = happenedOn ?? UTC_DATE(createdAt)`; Schlüssel `(effectiveDate, createdAt, kindRank, id)`, vollständige Keyset-Pagination; Cursor opak/integritätsgeschützt. Siehe #70. |
| M2-D09 | BLOCKING | DECIDED | API | Exakte Routen, Nesting und DTO-Namen? | Space-scoped Routenkatalog und DTOs sind in `API-DESIGN.md`/`API-CONTRACT.json` eingefroren. Parent-Comments sind verschachtelt; Update/Delete per Space-scoped Comment-ID. Siehe #70. |
| M2-D10 | BEFORE_CLIENTS | OPEN | Product + Privacy | Welche Notification Preview darf ein Kommentar zeigen? | Standardmäßig generisch; Content-Auszug nur nach expliziter Privacy-Freigabe. |
| M2-D11 | BLOCKING | DECIDED | Data + Privacy | Delete-, Retention- und Cascade-Regeln für Entity, Relation, Blob, Event und Audit? | Domain-Anteil #68 plus Media-Anteil #69 entschieden: fachliche Entität sofort unsichtbar; Comments atomar; letzte Mediareferenz setzt `DELETING`; Providercleanup async/idempotent; `DELETE_FAILED` retrybar/messbar. |
| M2-D12 | BLOCKING | DECIDED | Backend + Ops | Wie lange bleiben unvollständige/fehlgeschlagene Uploads erhalten? | PENDING/UPLOADING/FAILED 24 h; Cleanup mindestens stündlich; DELETE_FAILED bis Erfolg/manuellem Eingriff. Siehe #69. |
| M2-D13 | BLOCKING | DECIDED | Security + Media | Direct Upload oder serverseitiger Stream je Local-/S3-Adapter? | Local: autorisierter Serverstream. S3: presigned Upload ≤10 min; Read URL ≤5 min. Domain-/Finalize-Autorisierung serverkontrolliert. Siehe #69. |
| M2-D14 | BLOCKING | DECIDED | Privacy + Product | Werden EXIF, GPS und weitere eingebettete Metadaten entfernt? | Ja, beim Ingest. Der Validierungsjob extrahiert eine Allowlist technischer Felder nach ProtectedPayload und speichert danach ausschliesslich die bereinigte Datei. Siehe #78. |
| M2-D15 | BLOCKING | DECIDED | Media + Product | Sind Thumbnailing, Transcoding und Poster Frames Teil von M2? | Je eine abgeleitete Variante: Bild-Thumbnail und Video-Posterframe. Transcoding ist nicht Teil von M2. Siehe #78. |
| M2-D16 | BLOCKING | DECIDED | Architecture + Security | Minimales Schema je M2-Domain-Event? | Envelope: `eventId`, `eventType`, `occurredAt`, `spaceId`, `actorId`, `resourceType`, `resourceId`, `resourceVersion`; event-spezifisch nur IDs, sichere Zustände/Kategorien und technische Zeitpunkte. Keine ProtectedPayload, Dateinamen, URLs oder Emotion. Siehe #68. |
| M2-D17 | BEFORE_CLIENTS | OPEN | Product + Privacy | Welche privaten Daten enthält persönlicher Export, gemeinsamer Export oder Backup? | Owner-Export und Partnerexport strikt trennen; Private niemals in Partnerexport. |
| M2-D18 | BEFORE_CLIENTS | OPEN | Client + Security | Welche Cache-/Offline-Retention gilt für private Inhalte auf Web und Android? | Owner-/Space-gebundene Caches, vollständige Löschung bei Logout/Space-Wechsel, kein Offline Write. |
| M2-D19 | LATER | PROPOSED | Architecture | Wie bleibt E2EE nachrüstbar, ohne heute echte E2EE vorzutäuschen? | ProtectedPayload und opaque MediaStore beibehalten; Key Management ausdrücklich außerhalb M2. |
| M2-D20 | BLOCKING | DECIDED | Domain | Kann ein Attachment ohne Parent `READY` sein und wie lange? | Ja, nur Owner und maximal 60 min ab `readyAt`; danach `DELETING`; Bind-vs-Cleanup wird serialisiert. Siehe #69. |
| M2-D21 | BEFORE_CLIENTS | OPEN | Search + Privacy | Wird M2-Suche direkt in Postgres oder über separaten Index umgesetzt? | Globale Volltextsuche ist nicht G2-pflichtig und liegt grundsätzlich in M4; falls früher benötigt, neue explizite Gate-Entscheidung. |
| M2-D22 | BEFORE_CLIENTS | OPEN | Product + UX | Ist der Owner-Bereich für private HeartMoments Teil der gemeinsamen Story-Route oder eine getrennte Ansicht? | Getrennte, klar markierte Owner-Ansicht reduziert versehentliche Offenlegung. |

## Verbindliche Domain-/Privacy-Grundsätze für M2

- Öffentliche Domain-/API-Sprache verwendet `visibility = SHARED | PRIVATE`, wo eine Ressource beide Sichtbarkeiten unterstützt.
- `SPACE_SHARED` und `OWNER_ONLY` bleiben interne Authorization-/Persistenzklassen; Clients schreiben `privacyClass` nicht als zweite Wahrheitsquelle.
- `PRIVATE` ist keine nachträgliche UI-Filterung. Nichtberechtigte Zeilen werden bereits in der autorisierten Datenabfrage ausgeschlossen.
- ProtectedPayload ist eine Architektur- und Leckagegrenze, keine Behauptung echter E2EE.
- Memory und Milestone sind gemeinsamer Space-Inhalt; HeartMoment kann `SHARED` oder `PRIVATE` sein; Comment besitzt keine unabhängige Sichtbarkeit und erbt die Erreichbarkeit des Parents.
- Autor-/Owner-IDs sind nach Erstellung unveränderlich. Normale Updates dürfen Ownership nicht übertragen.

## Entschiedene Einträge

### M2-D01 – Schreibrechte für Memory
Status: DECIDED  
Datum: 2026-08-25  
Entscheider: Product + Domain / Projektentscheidung #68  
Entscheidung: Eine Memory ist gemeinsamer, für beide aktiven Space-Partner lesbarer Inhalt. Update und Delete dürfen ausschließlich durch den unveränderlichen `authorId` erfolgen. Der Partner darf die Memory weder inhaltlich noch über nicht-inhaltliche Felder verändern oder löschen. Eine spätere Kollaborationsfunktion benötigt eine neue explizite Domainentscheidung und darf diese Regel nicht stillschweigend aufweichen.  
Begründung: Geteilte Lesbarkeit ist keine Schreibvollmacht. Die Autorregel verhindert überraschende Änderungen/Löschungen persönlicher Erinnerungen und liefert eine einfache, testbare Ownership-Grenze.  
Folgen: Create setzt `authorId` aus dem Authorization Context. Read/List erlauben beide aktiven Space-Mitglieder. Update/Delete benötigen Membership + autorisierte Ressourcenabfrage + Autorprüfung + aktuelle Version. Fremder Space bleibt 404; sichtbare Memory eines Partners mit fehlender Schreibberechtigung folgt der bestehenden 403-vs-404-Konvention für bekannte gemeinsame Ressourcen. Web/Android dürfen Partnern keine aktive Edit/Delete-Aktion anbieten.  
Tests: Autor CRUD; Partner read/list; Partner update/delete abgelehnt; fremder Space 404; stale author update/delete 409; `authorId` nicht mutierbar.  
Verweise: #68, `DOMAIN-MODEL.md`, `PROJECT-CONTROL.md`.

### M2-D02 – Optimistic Concurrency für Comments
Status: DECIDED  
Datum: 2026-08-25  
Entscheider: Domain + API / Projektentscheidung #68  
Entscheidung: Comments sind editierbare Entitäten und erhalten ein persistiertes `version`-Feld. Update und Delete verlangen `If-Match` nach derselben API-Konvention wie andere veränderbare M1/M2-Ressourcen; stale Version ergibt deterministisch `409 RESOURCE_VERSION_CONFLICT`. Nur der unveränderliche Comment-Autor darf Body ändern oder Comment löschen.  
Begründung: Ohne Versionierung wäre Comment-Edit ein isolierter Last-write-wins-Sonderfall und würde die globale Concurrency-Invariante brechen.  
Folgen: Comment DTO liefert `version`/ETag; Create startet mit Version 1; jede persistierte Änderung erhöht die Version. Parent-Privacy/Delete kann Comments als serverseitige Domainoperation atomar entfernen und benötigt dabei kein vom Comment-Autor geliefertes If-Match.  
Tests: author update/delete; partner denied; stale update/delete 409; Parent-Cascade trotz Comment-Ownership; Cross-Space 404.  
Verweise: #68, `DOMAIN-MODEL.md`, bestehende API-Concurrency-Konvention.

### M2-D06 – HeartMoment Emotion ist ProtectedPayload
Status: DECIDED  
Datum: 2026-08-25  
Entscheider: Security + Privacy / Projektentscheidung #68  
Entscheidung: `emotion` wird zusammen mit HeartMoment-`text` als ProtectedPayload klassifiziert. Der Wert darf über die autorisierte Ressourcen-API an berechtigte Clients geliefert werden, ist aber kein allgemeines Metadatum und darf nicht in Analytics, Logs, Notification-Previews, Domain-Event-Payloads, Metriklabels oder Suchindizes außerhalb der geschützten Inhaltsgrenze kopiert werden.  
Begründung: Emotion beschreibt sensiblen Beziehungsinhalt und kann unabhängig vom Text private Rückschlüsse ermöglichen. Für Sortierung, Tenant-Isolation oder Routing ist der Klarwert nicht erforderlich.  
Folgen: Persistenz muss die ProtectedPayload-Abstraktion respektieren; zukünftige Verschlüsselbarkeit darf nicht von Klartext-Emotion in Indizes/Events abhängen. Filter nach Emotion ist nicht Teil des M2-Vertrags.  
Tests: Events/Logs enthalten Emotion nicht; private HeartMoment bleibt vollständig owner-only; Serialisierung liefert Emotion nur nach erfolgreicher Ressourcenauthorisierung.  
Verweise: #68, `DOMAIN-MODEL.md`, `SECURITY-TEST-MATRIX.md`.

### M2-D07 – SHARED zu PRIVATE bei HeartMoment
Status: DECIDED  
Datum: 2026-08-25  
Entscheider: Domain + Privacy / Projektentscheidung #68  
Entscheidung: Ein Wechsel `SHARED -> PRIVATE` ist eine atomare Domainoperation. In derselben DB-Transaktion werden die Privacy-Klasse auf `OWNER_ONLY` gesetzt und sämtliche Comments dieses HeartMoments fachlich gelöscht. Nach Commit darf keine Partner-Sichtbarkeit über Comment-, Story-, Activity-, Notification-, Cache- oder Event-Projektionen bestehen. Der API-Response verrät dem Partner nach dem Wechsel weder Comment-Anzahl noch frühere private Zustände. Ein Wechsel `PRIVATE -> SHARED` stellt gelöschte Comments nicht wieder her.  
Begründung: Comments sind gemeinschaftliche Inhalte auf einem zuvor gemeinsamen Parent. Ein bloßes Verstecken würde Retention-/Wiederfreigabe-Semantik komplizieren und könnte Partnerdaten später unerwartet erneut sichtbar machen. Die Löschung ist die klarste Privacy-Grenze.  
Folgen: Die UI muss vor `SHARED -> PRIVATE` allgemein warnen, dass vorhandene Kommentare entfernt werden. Sie darf keine fremden privaten Daten offenlegen. Projektionen/Consumer erhalten nur sichere IDs/Zustandsänderungen.  
Tests: Wechsel und Comment-Delete atomar; Rollback erhält alten Zustand vollständig; Story/Partner-GET nach Commit ohne Leak; PRIVATE->SHARED resurrected nichts; Race mit Comment-Create wird serialisiert/konfliktfrei abgewehrt.  
Verweise: #68, `DOMAIN-MODEL.md`, `SECURITY-TEST-MATRIX.md`.

### M2-D11 – Fachliche Delete-/Retention-Regeln
Status: DECIDED (DOMAIN); Media-Anteil siehe Ergänzung unten  
Datum: 2026-08-25  
Entscheider: Data + Privacy / Projektentscheidung #68  
Entscheidung: Fachliches Delete macht die Ressource mit erfolgreichem Commit sofort nicht mehr lesbar. Story ist ein nicht persistiertes Read Model und benötigt keine eigene Löschung. Comments sind abhängige Domainobjekte und werden beim Delete ihres Parents atomar in derselben DB-Transaktion gelöscht. Domain-Events/Audit dürfen die zur technischen Nachvollziehbarkeit notwendigen IDs, Typen, Versionen, Actor-/Space-Bezug, Zeitpunkt und sichere Zustände behalten, aber keine ProtectedPayload. Physische Blob-Löschung, Orphan-Retention und Cleanup-Retry werden separat in #69 entschieden.  
Begründung: Privacy verlangt sofortige fachliche Unsichtbarkeit; externe Storage-I/O darf gleichzeitig nicht unzuverlässig an die DB-Transaktion gekoppelt werden.  
Folgen: Parent-Delete und Comment-Cascade sind eine DB-Transaktion. Cleanup wird event-/jobbasiert und idempotent. Historische Events dürfen nicht als Schattenkopie gelöschter Inhalte dienen.  
Tests: nach Commit 404/keine Listen-/Story-Zeile; Transaktionsrollback stellt Parent+Comments wieder her; Event enthält keine ProtectedPayload; Storage-Cleanup-Fehler macht gelöschte Domainressource nicht wieder sichtbar.  
Verweise: #68, #69, `DOMAIN-MODEL.md`, `MEDIA-PIPELINE.md`.

### M2-D16 – Minimales M2-Domain-Event-Schema
Status: DECIDED  
Datum: 2026-08-25  
Entscheider: Architecture + Security / Projektentscheidung #68  
Entscheidung: Jedes M2-Domain-Event verwendet mindestens den Envelope `eventId`, `eventType`, `occurredAt`, `spaceId`, `actorId`, `resourceType`, `resourceId`, `resourceVersion`. Event-spezifische Payload darf ausschließlich weitere IDs, technische Zeitpunkte und explizit als sicher klassifizierte Zustände/Kategorien enthalten. Verboten sind ProtectedPayload-Felder, Comment-Body, Memory-/Milestone-Titel und -Body, HeartMoment-Text/-Emotion, Originaldateinamen, Storage Keys, Download-URLs sowie unnötige personenbezogene Metadaten. Delete-Events dürfen die letzte bekannte Ressourcen-ID/Version und `deletedAt` enthalten, nicht den gelöschten Inhalt.  
Begründung: Consumer brauchen stabile Routing-/Invalidierungsdaten, nicht den sensiblen Inhalt. Ein kleiner Envelope reduziert Leckage in Outbox, Logs, Retries und Observability und hält spätere Verschlüsselung möglich.  
Folgen: Notification-/Activity-Consumer laden benötigte Darstellung nach eigener Autorisierung oder verwenden generische Texte; sie dürfen keinen sensiblen Snapshot aus dem Event erwarten. `PRIVATE` HeartMoment erzeugt keine partnergerichtete Activity/Notification.  
Tests: Schema-/Contract-Test pro Eventtyp; Negativtests gegen verbotene Keys/Werte; private Events erzeugen keine Partnerprojektion; Outbox und Logs enthalten keine ProtectedPayload.  
Verweise: #68, `DOMAIN-MODEL.md`, `SECURITY-TEST-MATRIX.md`.

### M2-D03 – Attachment-Bindung
Status: DECIDED  
Datum: 2026-08-25  
Entscheider: Domain + Data / Projektentscheidung #69  
Entscheidung: Ein Attachment gehört genau einem Space und Owner und darf in M2 höchstens an eine Domainressource gebunden werden. Memory verwendet eine explizite `MemoryAttachment`-Relation mit eindeutiger nullbasierter `position`; HeartMoment maximal ein Attachment. Wiederverwendung desselben Attachment-Datensatzes an mehreren Parents sowie Cross-Space-Bindung sind verboten.  
Begründung: Exklusive Bindung hält Parent-Autorisierung und Cleanup eindeutig und vermeidet Many-to-Many-Privacy-Races.  
Folgen: Bindung verlangt Owner + schreibbaren Parent im selben Space + READY innerhalb Bindungsfenster und erfolgt atomar.  
Verweise: #69, `MEDIA-PIPELINE.md`.

### M2-D04 – Media-Allowlist und Limits
Status: DECIDED  
Datum: 2026-08-25  
Entscheider: Security + Product / Projektentscheidung #69  
Entscheidung: Bilder JPEG/PNG/WebP/HEIC/HEIF bis 25 MiB, 40 MP und 12.000 px/Kante. Videos MP4/QuickTime bis 250 MiB, 180 Sekunden und 3840×2160. Memory maximal 20 Attachments und 500 MiB; HeartMoment maximal eins. Alle anderen Typen fail-closed.  
Begründung: Kleine Positivliste deckt typische Smartphone-Medien ab und begrenzt Parser-, Speicher- und DoS-Risiko.  
Folgen: Server prüft tatsächliche Bytes/MIME/Größe/Dimension/Dauer; Clientwerte sind nur UX.  
Verweise: #69, `MEDIA-PIPELINE.md`, `SECURITY-TEST-MATRIX.md`.

### M2-D05 – Asynchrone Validierung und Zustände
Status: DECIDED  
Datum: 2026-08-25  
Entscheider: Backend + Ops / Projektentscheidung #69  
Entscheidung: `finalizeUpload` setzt atomar `VALIDATING` und reiht einen idempotenten Job ein. Interne Zustände sind `PENDING`, `UPLOADING`, `VALIDATING`, `READY`, `FAILED`, `DELETING`, `DELETE_FAILED`.  
Begründung: Medienparser und Provider-I/O gehören nicht in eine lange HTTP-/DB-Transaktion; derselbe Contract funktioniert für Local und S3.  
Folgen: Clients behandeln Finalize nicht als Uploaderfolg und beobachten Status; paralleles Finalize wird serialisiert.  
Verweise: #69, `MEDIA-PIPELINE.md`.

### M2-D11 – Media Delete/Cleanup Ergänzung
Status: DECIDED (MEDIA)  
Datum: 2026-08-25  
Entscheider: Data + Privacy / Projektentscheidung #69  
Entscheidung: Wird die letzte zulässige Parent-Referenz entfernt oder ein Orphan fällig, markiert die DB das Attachment atomar `DELETING`. Providerlöschung erfolgt außerhalb der fachlichen Transaktion idempotent per Job. Fehler führen zu `DELETE_FAILED` und wiederholtem Retry/Alarm; sie machen Domaininhalt nie wieder sichtbar.  
Begründung: Externes Storage-I/O darf die DB-Transaktion nicht unzuverlässig koppeln.  
Folgen: Cleanup ist beobachtbar; Metadaten werden erst nach erfolgreichem Providercleanup final entfernt/terminalisiert.  
Verweise: #69, #68, `MEDIA-PIPELINE.md`.

### M2-D12 – Upload-Retention
Status: DECIDED  
Datum: 2026-08-25  
Entscheider: Backend + Ops / Projektentscheidung #69  
Entscheidung: PENDING ohne Abschluss, UPLOADING ohne Finalize und FAILED werden nach 24 Stunden cleanup-fällig. Cleanup läuft mindestens stündlich. `DELETE_FAILED` hat keine automatische Vergessensfrist und bleibt bis Erfolg oder manuellem Eingriff sichtbar/metriciert.  
Begründung: 24 Stunden tolerieren mobile Unterbrechungen, verhindern aber dauerhafte Orphans.  
Folgen: Retention basiert auf serverseitigen Zeitpunkten, nie Clientzeit.  
Verweise: #69, `MEDIA-PIPELINE.md`.

### M2-D13 – Upload-/Read-Transport
Status: DECIDED  
Datum: 2026-08-25  
Entscheider: Security + Media / Projektentscheidung #69  
Entscheidung: LocalMediaStore nimmt Uploads über autorisierte serverseitige Streamingroute entgegen. S3MediaStore darf presigned Upload-URLs mit maximal 10 Minuten TTL verwenden. Reads: Local serverseitig autorisiert streamen; S3 erst nach Parent-Autorisierung als signierte URL mit maximal 5 Minuten TTL. Bucket/Storage bleiben privat.  
Begründung: Adapter dürfen Transport optimieren, aber nicht Domainautorisierung oder Finalize umgehen.  
Folgen: URLs/Signaturen nicht loggen/persistieren; Restfenster nach Rechteentzug ist bei S3 auf höchstens 5 Minuten begrenzt und als Trade-off dokumentiert.  
Verweise: #69, `MEDIA-PIPELINE.md`.

### M2-D20 – READY ohne Parent
Status: DECIDED  
Datum: 2026-08-25  
Entscheider: Domain / Projektentscheidung #69  
Entscheidung: Ein READY Attachment darf maximal 60 Minuten ab `readyAt` ungebunden bleiben und ist in dieser Zeit nur für seinen Owner verwaltbar. Danach wird es cleanup-fällig. Bindung und Cleanup werden über Statusprüfung/Row Lock serialisiert.  
Begründung: Ein kurzes Fenster entkoppelt Upload und Parentmutation, ohne dauerhaft lesbare Orphans zu schaffen.  
Folgen: Nach erfolgreicher Bindung folgt Lebensdauer dem Parent; kein Partnerzugriff allein aufgrund READY.  
Verweise: #69, `MEDIA-PIPELINE.md`.

### M2-D08 – Story-Sortierung und Cursor
Status: DECIDED  
Datum: 2026-08-25  
Entscheider: API + Data / Projektentscheidung #70  
Entscheidung: Story verwendet `effectiveDate = happenedOn ?? UTC_DATE(createdAt)` und den vollständigen Keyset-Schlüssel `(effectiveDate, createdAt, kindRank, id)`. `kindRank` ist `MEMORY=1`, `HEART_MOMENT=2`, `MILESTONE=3`. ASC/DESC wenden dieselbe Richtung auf das vollständige Tupel an. Der Cursor ist opak, versioniert, integritätsgeschützt und an Space sowie `type`/`year`/`order` gebunden.  
Begründung: Ein vollständiger eindeutiger Schlüssel verhindert Tie-Duplikate/-Lücken ohne Offset-Pagination und bleibt für heterogene Story-Unionen deterministisch.  
Folgen: `q` bleibt M4. Privacy/Tenant-Filter erfolgen vor Sortierung. Manipulierter oder kontextfremder Cursor liefert `400 INVALID_CURSOR` ohne fremde Metadaten. Bei konkurrierender Änderung eines Sortierfelds wird kein historischer Snapshot versprochen; Clients refreshen.  
Tests: identische effectiveDate/createdAt über alle Kinds; ASC/DESC; Cursor mit geändertem Space/Filter/order; PRIVATE HeartMoment nie in Union; keine Tie-Duplikate/-Lücken auf unverändertem Datenbestand.  
Verweise: #70, `API-DESIGN.md`, `API-CONTRACT.json`.

### M2-D09 – Routen, Nesting und DTO-Namen
Status: DECIDED  
Datum: 2026-08-25  
Entscheider: API / Projektentscheidung #70  
Entscheidung: M2 bleibt vollständig unter `/api/v1/spaces/{spaceId}`. Memories, HeartMoments, Milestones und Attachments besitzen eigene Collections. Comment Create/List werden am Parent verschachtelt; Comment Update/Delete laufen über `/comments/{commentId}` im Space. Story bleibt `/timeline`. Privacy-Wechsel für HeartMoment ist eine explizite `/visibility`-Mutation. DTO-/operationId-Namen sind in `API-DESIGN.md` und maschinenlesbar in `API-CONTRACT.json` eingefroren.  
Begründung: Parent-Nesting bei Comment Create/List eliminiert frei wählbare Target-IDs/-Typen im Body; Space-Scoping passt zum bestehenden Tenant-Guard. Ein eigener Privacy-Endpunkt macht die destruktive SHARED->PRIVATE-Semantik explizit.  
Folgen: Clients schreiben weder `privacyClass` noch Storage-Interna. Alle mutierenden bestehenden Ressourcen verwenden If-Match. `backend/openapi.json` wird erst mit implementierten Runtime-Slices durch den bestehenden Generator aktualisiert; das Manifest ist kein zweiter produktiver OpenAPI-Vertrag.  
Tests: eindeutige operationIds/Method-Path-Paare; alle Pfade Space-scoped; If-Match-Matrix; keine `privacyClass`-Write-Felder; Attachment-Descriptor ohne Storage Keys/Bucket/Provider.  
Verweise: #70, `API-DESIGN.md`, `API-CONTRACT.json`, `backend/tests/test_m2_api_contract_manifest.py`.

### M2-D14 – EXIF-/Metadaten-Entfernung beim Ingest
Status: DECIDED  
Datum: 2026-08-25  
Entscheider: Privacy + Product / Projektentscheidung #78  
Entscheidung: Eingebettete Metadaten werden beim Ingest entfernt. Der ohnehin laufende Validierungsjob extrahiert vor dem Strippen eine abschließende Allowlist technischer Felder nach ProtectedPayload: Aufnahmezeitpunkt, Orientierung, Breite, Höhe und bei Video die Dauer. Alles Übrige – GPS/Standort, Geräte- und Seriennummern, Software-, Autor- und Copyrightfelder, Kommentar-/Beschreibungsfelder, Thumbnails im Container sowie unbekannte Segmente – wird verworfen. Gespeichert wird ausschließlich die bereinigte Datei; die hochgeladenen Originalbytes werden nicht dauerhaft aufbewahrt. Die Allowlist ist fail-closed: ein nicht aufgeführtes Feld wird entfernt, nicht behalten.  
Begründung: Eine Blacklist bekannter Standortfelder ist nicht abschließend – Container transportieren Standort auch in herstellereigenen und neu hinzukommenden Segmenten. Nur eine Allowlist ist dieselbe fail-closed-Linie, die M2 bereits bei MIME- und Formatprüfung fährt. Das Strippen beim Ingest lässt genau ein Objekt entstehen; damit stellt sich bei Export, Backup und jedem künftigen Lesepfad nicht erneut die Frage, welche Kopie nach außen geht. Die Extraktion vor dem Strippen bewahrt das fachlich Wertvolle: der Aufnahmezeitpunkt bleibt als Quelle für `happenedOn` verfügbar.  
Folgen: Der Validierungsschritt aus M2-D05 schreibt das Objekt neu; `READY` wird erst nach erfolgreichem Strippen gesetzt. Ein Medium, das nicht sicher bereinigt werden kann, ist fail-closed `FAILED` und wird nicht ungestrippt gespeichert. Die extrahierte Allowlist ist ProtectedPayload und wird nicht in Events, Logs, Metriken oder Index projiziert. Eine spätere Funktion "Original mit Metadaten herunterladen" existiert nicht und benötigt eine neue Entscheidung. M2-D17 (Export) kann davon ausgehen, dass kein Standort mehr in den Medienobjekten steckt.  
Tests: Bild mit GPS-Tag ist nach `READY` frei von Standortdaten; Herstellersegment mit eingebettetem Standort wird ebenfalls entfernt; unbekanntes Metadatensegment überlebt den Ingest nicht; Aufnahmezeitpunkt ist als ProtectedPayload vorhanden und taucht in keiner Outbox-Zeile auf; nicht bereinigbares Medium endet `FAILED` statt `READY`; Video behält Dauer und verliert Standort.  
Verweise: #78, `MEDIA-PIPELINE.md`, `PRIVACY-THREAT-MODEL.md`, `SECURITY-TEST-MATRIX.md`.

### M2-D15 – Umfang abgeleiteter Medienvarianten
Status: DECIDED  
Datum: 2026-08-25  
Entscheider: Media + Product / Projektentscheidung #78  
Entscheidung: M2 erzeugt je Attachment höchstens eine abgeleitete Variante: für Bilder ein verkleinertes Thumbnail, für Video einen einzelnen Posterframe. Video-Transcoding, mehrere Auflösungsstufen, Audioextraktion und adaptives Streaming sind nicht Teil von M2. Varianten entstehen serverseitig im selben Validierungsjob, nachdem M2-D14 angewendet wurde, und tragen selbst keine eingebetteten Metadaten.  
Begründung: M2 erlaubt Bilder bis 25 MiB und 40 MP. Eine Story-Timeline, die Originale ausliefert, verfehlt jedes Client-Budget und macht aus jeder Listenansicht eine Bandbreitenverstärkung über die autorisierte Leseroute – das ist nicht nur ein Performance-, sondern ein Missbrauchsthema. Der Posterframe kostet kaum zusätzlichen Aufwand, weil die Validierung für Dauer und Auflösung ohnehin eine serverseitige Medienprobe benötigt. Transcoding dagegen zöge eine grosse Abhängigkeit samt Angriffsfläche und langen Joblaufzeiten in den ersten Media-Slice und widerspräche dem Zuschnitt, S1 als beherrschbare Sicherheitsfläche zu halten.  
Folgen: Der Storage Key erhält kontrollierte serverseitige Varianten-Suffixe gemäß bestehendem Muster; Clients wählen keine Varianten-Keys. Eine Variante hat keine eigene Autorisierung, sondern folgt exakt der ihres Attachments und damit dem Parent. Cleanup entfernt Varianten gemeinsam mit dem Attachment; ein verwaistes Variantenobjekt ist ein Cleanup-Fehler, kein zulässiger Zustand. Fehlgeschlagene Variantenerzeugung setzt das Attachment nicht `FAILED`, sondern liefert das Attachment ohne Variante aus – ein fehlendes Thumbnail ist ein Darstellungs-, kein Sicherheitsproblem. Video ohne erzeugbaren Posterframe wird im Client neutral dargestellt.  
Tests: Thumbnail und Posterframe sind nach `READY` vorhanden und metadatenfrei; Variante ist ohne Leseberechtigung am Parent nicht abrufbar; Privacy-Wechsel des Parents sperrt auch die Variante; Delete entfernt Original und Varianten; fehlgeschlagene Variantenerzeugung lässt das Attachment nutzbar; kein Client-wählbarer Varianten-Key.  
Verweise: #78, `MEDIA-PIPELINE.md`, `DELIVERY-PLAN.md`.

## Entscheidungsformat

Bei Freigabe wird die Tabellenzeile aktualisiert und darunter ein Eintrag ergänzt:

```text
### M2-Dxx – Kurztitel
Status: DECIDED
Datum: YYYY-MM-DD
Entscheider: Rolle/Name
Entscheidung: ...
Begründung: ...
Folgen: ...
Verweise: ADR / Spec / Issue / PR
```

## Definition „entscheidungsklar“

Eine Entscheidung ist erst abgeschlossen, wenn:

1. die gewählte Option und bewusst verworfene Alternative erkennbar sind,
2. Privacy-, Security- und Datenmigrationsfolgen benannt sind,
3. API-, Web-, Android- und Betriebsfolgen berücksichtigt wurden,
4. Tests und Akzeptanzkriterien daraus ableitbar sind,
5. eine verbindliche Quelle verlinkt ist.
