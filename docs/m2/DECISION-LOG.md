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

| ID | Priorität | Status | Owner | Frage | Entscheidung / nächste Aktion |
|---|---|---|---|---|---|
| M2-D01 | BLOCKING | DECIDED | Product + Domain | Darf der Partner eine Memory des Autors ändern oder löschen? | Nein. Beide aktiven Partner lesen gemeinsame Memories; Update/Delete bleiben ausschließlich beim unveränderlichen Autor. Siehe #68. |
| M2-D02 | BLOCKING | DECIDED | Domain + API | Erhalten Kommentare ein `version`-Feld für Optimistic Concurrency? | Ja. Editierbare Comments erhalten `version`; Update/Delete verwenden If-Match/409. Siehe #68. |
| M2-D03 | BLOCKING | DECIDED | Domain + Data | Wie werden Attachments gebunden? | Exklusive Bindung an höchstens einen Parent; MemoryAttachment mit stabiler `position`; keine Cross-Space-/Mehrfachbindung. Siehe #69. |
| M2-D04 | BLOCKING | DECIDED | Security + Product | Welche MIME-Typen und Limits gelten? | JPEG/PNG/WebP/HEIC/HEIF ≤25 MiB/40 MP/12k px; MP4/QuickTime ≤250 MiB/180 s/4K; Memory ≤20 Attachments/500 MiB. Siehe #69. |
| M2-D05 | BLOCKING | DECIDED | Backend + Ops | Synchron oder asynchron validieren? | Asynchron; interne Zustände `PENDING`, `UPLOADING`, `VALIDATING`, `READY`, `FAILED`, `DELETING`, `DELETE_FAILED`. Siehe #69. |
| M2-D06 | BLOCKING | DECIDED | Security + Privacy | Emotion bei HeartMoment als Metadatum oder ProtectedPayload? | ProtectedPayload; keine Analytics-/Event-/Log-Metadaten. Siehe #68. |
| M2-D07 | BLOCKING | DECIDED | Domain + Privacy | Kommentare bei `SHARED -> PRIVATE`? | Atomarer Privacy-Wechsel; vorhandene Kommentare werden in derselben DB-Transaktion gelöscht. Siehe #68. |
| M2-D08 | BLOCKING | PROPOSED | API + Data | Story-Sortierung und Cursor? | `COALESCE(happenedOn, createdAt)`, danach `createdAt`, danach `id`; final in #70. |
| M2-D09 | BLOCKING | OPEN | API | Exakte Routen, Nesting und DTO-Namen? | #70. |
| M2-D10 | BEFORE_CLIENTS | OPEN | Product + Privacy | Welche Notification Preview darf ein Kommentar zeigen? | Standardmäßig generisch; Content-Auszug nur nach expliziter Privacy-Freigabe. |
| M2-D11 | BLOCKING | DECIDED | Data + Privacy | Delete-, Retention- und Cascade-Regeln für Entity, Relation, Blob, Event und Audit? | Domain + Media entschieden: fachliche Ressource sofort unsichtbar; abhängige Comments atomar löschen; letzte Mediareferenz setzt `DELETING`; Providercleanup async/idempotent; `DELETE_FAILED` retrybar/messbar. Siehe #68/#69. |
| M2-D12 | BLOCKING | DECIDED | Backend + Ops | Retention unvollständiger/fehlgeschlagener Uploads? | PENDING/UPLOADING/FAILED 24 h; Cleanup mindestens stündlich; DELETE_FAILED bis Erfolg/manuellem Eingriff. Siehe #69. |
| M2-D13 | BLOCKING | DECIDED | Security + Media | Direct Upload oder Serverstream? | Local: autorisierter Serverstream. S3: presigned Upload ≤10 min; Read URL ≤5 min. Domain-/Finalize-Autorisierung bleibt serverkontrolliert. Siehe #69. |
| M2-D14 | BEFORE_CLIENTS | OPEN | Privacy + Product | EXIF/GPS entfernen? | Vor Clients entscheiden; bis dahin keine Projektion in API/Logs/Events/Index. |
| M2-D15 | BEFORE_CLIENTS | OPEN | Media + Product | Thumbnailing/Transcoding/Poster Frames in M2? | Nur bei nachgewiesenem Performancebedarf; sonst separater Slice. |
| M2-D16 | BLOCKING | DECIDED | Architecture + Security | Minimales M2-Domain-Event-Schema? | Sicherer Envelope ohne ProtectedPayload, Dateinamen, URLs oder Emotion. Siehe #68. |
| M2-D17 | BEFORE_CLIENTS | OPEN | Product + Privacy | Welche privaten Daten enthält Export/Backup? | Owner-Export und Partnerexport strikt trennen; Private niemals in Partnerexport. |
| M2-D18 | BEFORE_CLIENTS | OPEN | Client + Security | Cache-/Offline-Retention? | Owner-/Space-gebundene Caches, vollständige Löschung bei Logout/Space-Wechsel, kein Offline Write. |
| M2-D19 | LATER | PROPOSED | Architecture | E2EE nachrüstbar halten? | ProtectedPayload und opaque MediaStore beibehalten; Key Management außerhalb M2. |
| M2-D20 | BLOCKING | DECIDED | Domain | Kann ein Attachment ohne Parent `READY` sein und wie lange? | Ja, nur Owner und maximal 60 min ab `readyAt`; danach `DELETING`; Bind-vs-Cleanup serialisiert. Siehe #69. |
| M2-D21 | BEFORE_CLIENTS | OPEN | Search + Privacy | Suchimplementierung? | Globale Volltextsuche ist grundsätzlich M4, nicht G2-pflichtig. |
| M2-D22 | BEFORE_CLIENTS | OPEN | Product + UX | Private HeartMoments in Story oder separater Bereich? | Getrennte Owner-Ansicht bevorzugt; vor Clients entscheiden. |

## Verbindliche Domain-/Privacy-Grundsätze für M2

- Öffentliche Domain-/API-Sprache verwendet `visibility = SHARED | PRIVATE`, wo eine Ressource beide Sichtbarkeiten unterstützt.
- `SPACE_SHARED` und `OWNER_ONLY` bleiben interne Authorization-/Persistenzklassen; Clients schreiben `privacyClass` nicht als zweite Wahrheitsquelle.
- `PRIVATE` ist keine nachträgliche UI-Filterung. Nichtberechtigte Zeilen werden bereits in der autorisierten Datenabfrage ausgeschlossen.
- ProtectedPayload ist eine Architektur- und Leckagegrenze, keine Behauptung echter E2EE.
- Memory und Milestone sind gemeinsamer Space-Inhalt; HeartMoment kann `SHARED` oder `PRIVATE` sein; Comment besitzt keine unabhängige Sichtbarkeit und erbt die Erreichbarkeit des Parents.
- Autor-/Owner-IDs sind nach Erstellung unveränderlich. Normale Updates dürfen Ownership nicht übertragen.

## Entschiedene Domain-/Privacy-Einträge

### M2-D01 – Schreibrechte für Memory
Status: DECIDED  
Datum: 2026-08-25  
Entscheider: Product + Domain / Projektentscheidung #68  
Entscheidung: Eine Memory ist gemeinsamer, für beide aktiven Space-Partner lesbarer Inhalt. Update und Delete dürfen ausschließlich durch den unveränderlichen `authorId` erfolgen. Der Partner darf die Memory weder inhaltlich noch über nicht-inhaltliche Felder verändern oder löschen.  
Begründung: Geteilte Lesbarkeit ist keine Schreibvollmacht.  
Folgen/Tests: Create setzt `authorId` aus dem Authorization Context; Partner read/list; Partner update/delete abgelehnt; fremder Space 404; stale author update/delete 409; `authorId` nicht mutierbar.  
Verweise: #68, `DOMAIN-MODEL.md`, `PROJECT-CONTROL.md`.

### M2-D02 – Optimistic Concurrency für Comments
Status: DECIDED  
Datum: 2026-08-25  
Entscheider: Domain + API / Projektentscheidung #68  
Entscheidung: Editierbare Comments erhalten ein persistiertes `version`-Feld. Update/Delete verlangen If-Match; stale Version ergibt `409 RESOURCE_VERSION_CONFLICT`. Nur der unveränderliche Comment-Autor darf Body ändern/löschen. Parent-Cascade-/Privacy-Operationen dürfen Comments serverseitig atomar entfernen.  
Verweise: #68, `DOMAIN-MODEL.md`.

### M2-D06 – HeartMoment Emotion ist ProtectedPayload
Status: DECIDED  
Datum: 2026-08-25  
Entscheider: Security + Privacy / Projektentscheidung #68  
Entscheidung: `emotion` wird mit `text` als ProtectedPayload klassifiziert. Kein Klarwert in Analytics, Logs, Notification-Previews, Domain-Events, Metriklabels oder Suchindizes außerhalb der geschützten Inhaltsgrenze.  
Verweise: #68, `DOMAIN-MODEL.md`, `SECURITY-TEST-MATRIX.md`.

### M2-D07 – SHARED zu PRIVATE bei HeartMoment
Status: DECIDED  
Datum: 2026-08-25  
Entscheider: Domain + Privacy / Projektentscheidung #68  
Entscheidung: `SHARED -> PRIVATE` ist eine atomare Domainoperation. Privacy-Klasse wird auf `OWNER_ONLY` gesetzt und sämtliche Comments werden in derselben DB-Transaktion gelöscht. Nach Commit keine Partnerprojektion; `PRIVATE -> SHARED` resurrected keine Comments.  
Verweise: #68, `DOMAIN-MODEL.md`, `SECURITY-TEST-MATRIX.md`.

### M2-D16 – Minimales M2-Domain-Event-Schema
Status: DECIDED  
Datum: 2026-08-25  
Entscheider: Architecture + Security / Projektentscheidung #68  
Entscheidung: Envelope `eventId`, `eventType`, `occurredAt`, `spaceId`, `actorId`, `resourceType`, `resourceId`, `resourceVersion`. Event-spezifisch nur weitere IDs, technische Zeitpunkte und sicher klassifizierte Zustände/Kategorien. Keine ProtectedPayload, Originaldateinamen, Storage Keys oder URLs.  
Verweise: #68, `DOMAIN-MODEL.md`, `SECURITY-TEST-MATRIX.md`.

## Entschiedene Media-Einträge

### M2-D03 – Attachment-Bindung
Status: DECIDED  
Datum: 2026-08-25  
Entscheider: Domain + Data / Projektentscheidung #69  
Entscheidung: Ein Attachment gehört genau einem Space und Owner und darf in M2 höchstens an eine Domainressource gebunden werden. Memory verwendet `MemoryAttachment(memoryId, attachmentId, position)`; HeartMoment maximal ein Attachment. Wiederverwendung desselben Attachment-Datensatzes an mehreren Parents sowie Cross-Space-Bindung sind verboten.  
Begründung: Exklusive Bindung hält Parent-Autorisierung und Cleanup eindeutig.  
Verweise: #69, `MEDIA-PIPELINE.md`.

### M2-D04 – Media-Allowlist und Limits
Status: DECIDED  
Datum: 2026-08-25  
Entscheider: Security + Product / Projektentscheidung #69  
Entscheidung: Bilder JPEG/PNG/WebP/HEIC/HEIF bis 25 MiB, 40 MP und 12.000 px/Kante. Videos MP4/QuickTime bis 250 MiB, 180 s und 3840×2160. Memory maximal 20 Attachments und 500 MiB; HeartMoment maximal eins. Andere Typen fail-closed.  
Folgen: Server prüft tatsächliche Bytes/MIME/Größe/Dimension/Dauer; Clientwerte sind nur UX.  
Verweise: #69, `MEDIA-PIPELINE.md`, `SECURITY-TEST-MATRIX.md`.

### M2-D05 – Asynchrone Validierung und Zustände
Status: DECIDED  
Datum: 2026-08-25  
Entscheider: Backend + Ops / Projektentscheidung #69  
Entscheidung: `finalizeUpload` setzt atomar `VALIDATING` und reiht einen idempotenten Job ein. Zustände: `PENDING`, `UPLOADING`, `VALIDATING`, `READY`, `FAILED`, `DELETING`, `DELETE_FAILED`.  
Verweise: #69, `MEDIA-PIPELINE.md`.

### M2-D11 – Delete/Cleanup vollständig
Status: DECIDED  
Datum: 2026-08-25  
Entscheider: Data + Privacy / Projektentscheidungen #68/#69  
Entscheidung: Fachliches Delete macht den Parent sofort unsichtbar und löscht abhängige Comments atomar. Wird die letzte Mediareferenz entfernt, markiert die DB das Attachment atomar `DELETING`; Providercleanup läuft idempotent außerhalb der Domaintransaktion. Fehler führen zu `DELETE_FAILED` und Retry/Alarm, ohne Domaininhalt wieder sichtbar zu machen.  
Verweise: #68, #69, `DOMAIN-MODEL.md`, `MEDIA-PIPELINE.md`.

### M2-D12 – Upload-Retention
Status: DECIDED  
Datum: 2026-08-25  
Entscheider: Backend + Ops / Projektentscheidung #69  
Entscheidung: PENDING ohne Abschluss, UPLOADING ohne Finalize und FAILED werden nach 24 h cleanup-fällig. Cleanup mindestens stündlich. `DELETE_FAILED` bleibt bis Erfolg oder manuellem Eingriff sichtbar/metriciert.  
Verweise: #69, `MEDIA-PIPELINE.md`.

### M2-D13 – Upload-/Read-Transport
Status: DECIDED  
Datum: 2026-08-25  
Entscheider: Security + Media / Projektentscheidung #69  
Entscheidung: LocalMediaStore nimmt Uploads/Reads über autorisierte Serverstreams entgegen. S3MediaStore darf presigned Upload-URLs ≤10 min und nach Parent-Autorisierung Read-URLs ≤5 min ausstellen. Bucket/Storage bleiben privat.  
Verweise: #69, `MEDIA-PIPELINE.md`.

### M2-D20 – READY ohne Parent
Status: DECIDED  
Datum: 2026-08-25  
Entscheider: Domain / Projektentscheidung #69  
Entscheidung: Ein READY Attachment darf maximal 60 min ab `readyAt` ungebunden bleiben und ist nur für seinen Owner verwaltbar. Danach cleanup-fällig; Bindung und Cleanup werden über Statusprüfung/Row Lock serialisiert.  
Verweise: #69, `MEDIA-PIPELINE.md`.

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
