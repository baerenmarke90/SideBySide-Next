# M2 Decision Log

**Stand:** 25.08.2026  
**Regel:** Eine offene Frage wird nicht stillschweigend im Code entschieden.

Dieses Log trennt Spezifikationsaussagen von Umsetzungsvorschlägen. `PROPOSED` ist nicht bindend. `DECIDED` benötigt Datum, Entscheider und Verweis auf ADR, Spec oder Issue.

> Hinweis zu parallelem M2-S0: Dieser Branch entscheidet ausschließlich die Media-Punkte aus #69. Domain-/Privacy-Punkte D01/D02/D06/D07/D16 und der Domain-Anteil von D11 werden parallel in #68/PR #73 entschieden und nach Merge über `main` zusammengeführt.

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
| M2-D01 | BLOCKING | OPEN | Product + Domain | Darf der Partner eine Memory des Autors ändern oder löschen? | Parallel #68 / PR #73. |
| M2-D02 | BLOCKING | OPEN | Domain + API | Erhalten Kommentare ein `version`-Feld für Optimistic Concurrency? | Parallel #68 / PR #73. |
| M2-D03 | BLOCKING | DECIDED | Domain + Data | Wie werden mehrere Attachments gebunden: exklusive Ownership, Wiederverwendung, Join-Entity und Sortierreihenfolge? | Exklusive Bindung an höchstens einen Parent; MemoryAttachment mit stabiler `position`; keine Cross-Space-/Mehrfachbindung. Siehe #69. |
| M2-D04 | BLOCKING | DECIDED | Security + Product | Welche MIME-Typen, Dateigrößen, Pixelgrenzen und Videodauern gelten je Plattform? | JPEG/PNG/WebP/HEIC/HEIF ≤25 MiB/40 MP/12k px; MP4/QuickTime ≤250 MiB/180 s/4K; Memory ≤20/500 MiB. Siehe #69. |
| M2-D05 | BLOCKING | DECIDED | Backend + Ops | Erfolgt Media-Validierung synchron beim Finalize oder asynchron? Welche internen Zustände sind nötig? | Asynchron; `PENDING/UPLOADING/VALIDATING/READY/FAILED/DELETING/DELETE_FAILED`. Siehe #69. |
| M2-D06 | BLOCKING | OPEN | Security + Privacy | Wird Emotion bei HeartMoment als Metadatum oder ProtectedPayload klassifiziert? | Parallel #68 / PR #73. |
| M2-D07 | BLOCKING | OPEN | Domain + Privacy | Was geschieht mit Kommentaren beim Wechsel eines HeartMoment von `SHARED` zu `PRIVATE`? | Parallel #68 / PR #73. |
| M2-D08 | BLOCKING | PROPOSED | API + Data | Welche Story-Sortierung gilt bei fehlendem `happenedOn`, und welcher Tie-Breaker stabilisiert Cursor? | `COALESCE(happenedOn, createdAt)`, danach `createdAt`, danach `id`; Cursor opak und versioniert. |
| M2-D09 | BLOCKING | OPEN | API | Exakte Routen, Nesting und DTO-Namen? | #70. |
| M2-D10 | BEFORE_CLIENTS | OPEN | Product + Privacy | Welche Notification Preview darf ein Kommentar zeigen? | Standardmäßig generisch; Content-Auszug nur nach expliziter Privacy-Freigabe. |
| M2-D11 | BLOCKING | DECIDED (MEDIA) | Data + Privacy | Delete-, Retention- und Cascade-Regeln für Entity, Relation, Blob, Event und Audit? | Media-Anteil: letzte Referenz markiert Attachment atomar `DELETING`; Providercleanup asynchron/idempotent; `DELETE_FAILED` wird retryt/gemessen. Domain-Anteil parallel #68. |
| M2-D12 | BLOCKING | DECIDED | Backend + Ops | Wie lange bleiben unvollständige/fehlgeschlagene Uploads erhalten? | PENDING/UPLOADING/FAILED 24 h; Cleanup mindestens stündlich; DELETE_FAILED bis Erfolg/manuellem Eingriff. Siehe #69. |
| M2-D13 | BLOCKING | DECIDED | Security + Media | Direct Upload oder serverseitiger Stream je Local-/S3-Adapter? | Local: autorisierter Serverstream. S3: presigned Upload ≤10 min; Read URL ≤5 min. Domain-/Finalize-Autorisierung serverkontrolliert. |
| M2-D14 | BEFORE_CLIENTS | OPEN | Privacy + Product | Werden EXIF, GPS und weitere eingebettete Metadaten entfernt? | Vor Clients entscheiden; bis dahin keine Projektion in API/Logs/Events/Index. |
| M2-D15 | BEFORE_CLIENTS | OPEN | Media + Product | Sind Thumbnailing, Transcoding und Poster Frames Teil von M2? | Nur aufnehmen, wenn Client-Performance ohne sie das Budget verfehlt; sonst separater Slice. |
| M2-D16 | BLOCKING | OPEN | Architecture + Security | Minimales Schema je M2-Domain-Event? | Parallel #68 / PR #73. |
| M2-D17 | BEFORE_CLIENTS | OPEN | Product + Privacy | Welche privaten Daten enthält persönlicher Export, gemeinsamer Export oder Backup? | Owner-Export und Partnerexport strikt trennen; Private niemals in Partnerexport. |
| M2-D18 | BEFORE_CLIENTS | OPEN | Client + Security | Welche Cache-/Offline-Retention gilt für private Inhalte auf Web und Android? | Owner-/Space-gebundene Caches, vollständige Löschung bei Logout/Space-Wechsel, kein Offline Write. |
| M2-D19 | LATER | PROPOSED | Architecture | Wie bleibt E2EE nachrüstbar, ohne heute echte E2EE vorzutäuschen? | ProtectedPayload und opaque MediaStore beibehalten; Key Management ausdrücklich außerhalb M2. |
| M2-D20 | BLOCKING | DECIDED | Domain | Kann ein Attachment ohne Parent `READY` sein und wie lange? | Ja, nur Owner und maximal 60 min ab `readyAt`; danach `DELETING`; Bind-vs-Cleanup wird serialisiert. |
| M2-D21 | BEFORE_CLIENTS | OPEN | Search + Privacy | Wird M2-Suche direkt in Postgres oder über separaten Index umgesetzt? | Globale Volltextsuche ist nach #67 grundsätzlich M4, nicht G2-pflichtig. |
| M2-D22 | BEFORE_CLIENTS | OPEN | Product + UX | Ist der Owner-Bereich für private HeartMoments Teil der gemeinsamen Story-Route oder eine getrennte Ansicht? | Getrennte, klar markierte Owner-Ansicht reduziert versehentliche Offenlegung. |

## Entschiedene Media-Einträge

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

### M2-D11 – Media Delete/Cleanup
Status: DECIDED (MEDIA); Domain-Anteil parallel #68  
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
