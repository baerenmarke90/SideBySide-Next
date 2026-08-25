# M2 Security & Privacy Test Matrix

**Status:** verbindliche Abnahmematrix für M2  
**Stand:** 25.08.2026

Diese Matrix ergänzt die allgemeinen Security- und HTTP-Tests um die fachlichen Risiken von Memories, HeartMoments, Milestones, Kommentaren, Story und Attachments. Tests sind grundsätzlich über die öffentliche API auszuführen; reine Repository-Tests reichen für Autorisierung nicht aus.

## Testidentitäten

| Kürzel | Rolle |
|---|---|
| `A` | Autor und aktives Mitglied von Space Alpha |
| `B` | Partner und aktives Mitglied von Space Alpha |
| `C` | aktives Mitglied eines anderen Space Beta |
| `R` | ehemaliges/widerrufenes Mitglied von Space Alpha |
| `X` | authentifiziert, aber ohne Mitgliedschaft |
| `ANON` | nicht authentifiziert |

Alle IDs werden zusätzlich mit zufälligen, existierenden fremden und formal ungültigen Werten getestet. Eine bekannte UUID darf keine Berechtigung ersetzen.

## Erwartete Offenlegung

- `401` nur bei fehlender oder ungültiger Authentifizierung.
- `404` für nicht sichtbare oder fremde Ressourcen, wenn `403` deren Existenz offenlegen würde.
- `403` nur dort, wo die Existenz der Ressource für den Aufrufer bereits legitim bekannt ist.
- Fehlertexte, Timing, Header und Response-Größe dürfen private oder fremde Inhalte nicht verraten.
- Autorisierung wird serverseitig vor Projektion, Zählung, Pagination und URL-Erzeugung angewandt.

## Medienmissbrauch – verbindliche M2-Werte

| ID | Fall | Erwartung |
|---|---|---|
| MED-01 | erlaubte Dateiendung, Magic Bytes/MIME nicht in Allowlist | `FAILED`, kein regulär lesbarer Blob |
| MED-02 | deklarierter MIME weicht vom serverseitig erkannten Typ ab | `FAILED`, sicherer Fehlercode, kein Client-MIME als Wahrheit |
| MED-03A | Bild >25 MiB | vor `READY` `FAILED` |
| MED-03B | Bild >40 MP oder >12.000 px Kante | vor `READY` `FAILED` |
| MED-03C | Video >250 MiB, >180 s oder >3840×2160 | vor `READY` `FAILED` |
| MED-03D | Memory >20 Attachments oder >500 MiB validierte Gesamtgröße | Bindung atomar abweisen, bestehende Relationen unverändert |
| MED-04 | Dekompressionsbombe/extreme Dimension | Ressourcenlimit greift, Worker bleibt stabil, `FAILED` |
| MED-05 | manipulierter/kaputter Container | Parserfehler isoliert, `FAILED` |
| MED-06 | Originalname mit Pfad-/Unicode-Steuerzeichen | niemals Storage Key/Autorisierung; nicht in Standardlogs |
| MED-07 | doppeltes/paralleles Finalize | genau ein wirksamer Validierungsjob; idempotentes Ergebnis |
| MED-08 | S3 Upload URL älter als 10 min / manipuliert | Providerzugriff verweigert; kein frei wählbarer Key |
| MED-09 | S3 Read URL älter als 5 min / manipuliert | Zugriff verweigert |
| MED-10 | Read URL nach Membership-/Privacy-Entzug | keine neue URL; bereits ausgestellte URL höchstens bis 5-min-TTL |
| MED-11 | fremder `storageKey` im Request | Feld nicht clientseitig setzbar bzw. abweisen |
| MED-12 | PENDING/UPLOADING/FAILED >24 h | stündlicher Cleanup markiert/löscht idempotent |
| MED-13 | READY ungebunden >60 min | `DELETING`; Owner kann nicht mehr nachträglich binden |
| MED-14 | Bindung Attachment Alpha → Parent Beta | atomar 404/abweisen, kein Leak/keine Relation |
| MED-15 | zweiter Parent für bereits gebundenes Attachment | abweisen; exklusive Bindung bleibt unverändert |
| MED-16 | Bind vs. Orphan-Cleanup parallel | genau eine Operation gewinnt; nie gebundener gelöschter Blob |
| MED-17 | Parent-Delete vs. Finalize/Bind parallel | keine Relation zu gelöschtem Parent; kein sichtbarer Orphan |
| MED-18 | Providerdelete Timeout | Domaininhalt bleibt unsichtbar; `DELETE_FAILED`, Retry/Metrik |
| MED-19 | Local-/S3-Adapter | identischer Lifecycle-/Autorisierungscontract |
| MED-20 | EXIF/GPS vorhanden | bis D14 keine Projektion in API/Logs/Events/Index; Original privat |
| MED-21 | unbekannter Typ/GIF/RAW/WebM/MKV/Dokument | fail-closed `FAILED` |
| MED-22 | HEIC/HEIF/JPEG/PNG/WebP innerhalb Limits | Validierung kann READY erreichen |
| MED-23 | MP4/QuickTime innerhalb Limits | Validierung kann READY erreichen |
| MED-24 | S3 Bucket/Public ACL | Deployment-/Contract-Test bestätigt nicht öffentlich |

## Attachment-Autorisierung

Für jedes Attachment werden mindestens folgende Pfade getestet:

1. Owner kann eigenen ungebundenen Upload nur in PENDING/UPLOADING/VALIDATING/FAILED bzw. READY innerhalb 60 Minuten verwalten.
2. Partner kann ungebundenes Attachment niemals lesen, zählen oder über Fehler unterscheiden.
3. Nach Bindung folgt Read ausschließlich dem Parent.
4. Owner-ID allein umgeht eine spätere Parent-Privacy-Sperre nicht.
5. Owner-only HeartMoment leakt weder Metadaten noch Stream/Read URL an Partner.
6. Cross-Space Attachment/Parent-Kombination wird vor Relation/URL-Erzeugung abgewiesen.
7. Nach letzter Referenz/Parent-Delete wird keine neue Read URL ausgestellt.
8. Storage Key, Bucket und Providerdetails erscheinen nicht in nutzerexponierten Responses.

## IDOR- und Tenant-Isolation

| ID | Angriff | Erwartung |
|---|---|---|
| TEN-01 | `C` liest/ändert/löscht Alpha-Entity über UUID | `404`, keine Mutation |
| TEN-02 | `A` setzt `spaceId=Beta` in Body, Query oder Route | Request abweisen, keine implizite Umschreibung |
| TEN-03 | Comment aus Alpha referenziert Target aus Beta | atomar abweisen, kein Event |
| TEN-04 | Attachment aus Alpha an Parent in Beta binden | atomar abweisen |
| TEN-05 | Cursor aus Alpha für Beta verwenden | neutraler Fehler oder leeres Ergebnis gemäß Vertrag, keine Daten |
| TEN-06 | signierte URL/Read-Token zwischen Spaces wiederverwenden | Zugriff verweigern bzw. ausschließlich exakt gebundener Key innerhalb TTL |
| TEN-07 | widerrufenes Mitglied fordert neuen Media-Read an | verweigern; keine neue signierte URL |
| TEN-08 | Groß-/Kleinschreibung, Encoding und doppelte Parameter | kanonisch und fail-closed |

## Concurrency und Transaktionen

- Zwei Updates mit derselben Version: genau eines gewinnt, das andere erhält `409`.
- Update parallel zu Delete: kein Wiederauftauchen, konsistentes Fehlerbild.
- Parent-Delete parallel zu Attachment-Finalize/Bind: kein sichtbarer Orphan und keine Relation zu gelöschtem Parent.
- Comment-Create parallel zu Target-Privatisierung oder Delete: Transaktion verhindert unzulässigen Kommentar.
- Doppelter Create mit Idempotency-Key: eine fachliche Entity und höchstens ein Outbox-Event.
- Domainänderung plus Outbox: entweder beides committed oder beides verworfen.
- Zwei Finalize-Requests: genau ein Validierungsjob/terminal konsistenter Status.
- Bindung parallel zu READY-Orphan-Cleanup: Status-/Row-Lock verhindert Bindung an gelöschten Blob.
- Letzte Referenz entfernen parallel zu Read-Descriptor: keine neue Autorisierung nach fachlichem Delete.

## Owner-only: Pflichtpfade

Für ein `PRIVATE` HeartMoment von `A` muss `B` in jedem folgenden Pfad exakt keinen Hinweis erhalten:

1. Direktabruf und Update/Delete-Versuch.
2. Listen, spätere Suche/Filter und Autocomplete.
3. Story, Monatsgruppen, Counts und Cursor.
4. Dashboard, Activity Feed, Recap und „zuletzt geändert“.
5. Kommentar-Target-Auflösung und Comment-Listen.
6. Attachment-Metadaten, Dateiabruf, Vorschaubild und signierte URL.
7. Domain Events, Notifications, Push Preview und Badge Count.
8. Partnerexport, geteiltes Backup und Diagnoseausgabe.
9. Cache Keys, ETags, Logs, Traces, Metriken und Analytics Properties.
10. Fehlerverhalten bei bekannter ID und indirekten Relations-IDs.

Ein Testdatensatz enthält eindeutig erkennbare Canary-Werte in Text, Emotion, Dateiname und Attachment-Metadaten. Kein Canary darf außerhalb des Owner-Kontexts auftauchen.

## Logging, Telemetrie und Events

- Keine Titel, Bodies, Kommentare, Originaldateien, Originaldateinamen, Read-/Upload-URLs oder privaten Emotionen in Standardlogs.
- IDs werden nur soweit für Betrieb nötig geloggt; keine Tokens, Signaturen oder Storage Credentials.
- Fehlertracking erhält bereinigte Payloads und keine kompletten Request Bodies/Providerantworten.
- Domain Events enthalten minimale Referenzen statt geschützter Inhalte.
- Metriken haben begrenzte Kardinalität und keine Nutzertexte/Dateinamen als Labels.
- Media-Metriken erfassen mindestens Statusalter/-anzahl für PENDING, FAILED, READY-ungebunden, DELETE_FAILED sowie Cleanup-Erfolg/-Fehler.

## Adapter-Contract-Tests

Jede `MediaStore`-Implementierung muss denselben fachlichen Testkatalog bestehen:

- `createUpload` erzeugt nicht erratbare, Space-gebundene serverseitige Keys.
- Local Upload streamt autorisiert über Server; S3 Upload Descriptor läuft nach ≤10 min ab.
- `finalizeUpload` ist idempotent und führt nicht direkt ohne Validierung zu READY.
- `open`/`createReadUrl` ist ohne unmittelbar vorherige Domainautorisierung nicht erreichbar.
- S3 Read URL läuft nach ≤5 min ab; Bucket bleibt privat.
- `delete` ist idempotent und löscht nur den exakt adressierten Blob.
- Teilfehler verändern den fachlichen Status nicht irreführend.
- Ein zukünftiger verschlüsselter Blob kann gespeichert/übertragen werden; M2 behauptet nicht, dass serverseitige Validation mit echter E2EE bereits gelöst ist.

## Retention-/Job-Tests

- Cleanup-Clock wird mit serverseitigen Zeitpunkten getestet, nicht Clientzeit.
- 23:59 h alte PENDING/FAILED bleiben, >24 h werden fällig.
- 59 min altes READY-ungebunden bleibt bindbar, >60 min wird fällig.
- wiederholter Cleanup ist idempotent.
- Providerfehler erzeugt keinen Domain-Rollback und kein Wiederauftauchen.
- `DELETE_FAILED` bleibt sichtbar für Ops/Metrik und wird retryt.
- Cleanup-Logs enthalten Attachment-ID/Status/Adapter/Versuch, aber keine URL/Dateinamen/Inhalte.

## Story/Pagination

Globale Volltextsuche `q` ist nach M2-S0-Projektsteuerung nicht G2-pflichtig und grundsätzlich M4. Story-Privacy wird trotzdem vor Sortierung, Count und Cursorbildung durchgesetzt. Sortierung/Cursor werden in #70/D08 verbindlich entschieden.

## Client- und Cache-Prüfungen

| Bereich | Web | Android |
|---|---|---|
| Logout / Space-Wechsel | Query- und Mediencache vollständig leeren | lokale Projektionen und Bildcache leeren |
| PRIVATE-Daten | nie in gemeinsamem Browser-/Service-Worker-Cache | owner-gebunden, nicht in Backup/Share Sheet |
| Offline | letzte autorisierte Ansicht gemäß späterem Cache-Vertrag | letzte autorisierte Ansicht gemäß späterem Cache-Vertrag |
| Offline Write | deaktiviert oder klar blockiert | deaktiviert oder klar blockiert |
| Read URL | nicht dauerhaft persistieren | nicht dauerhaft persistieren |

## Abnahmekriterium

M2 ist sicherheitsseitig nicht fertig, solange ein Pflichtpfad fehlt, ein Cross-Tenant-Test nur auf Repository-Ebene existiert oder ein privater HeartMoment indirekt sichtbar werden kann. Media-Runtime ist zusätzlich blockiert, bis die #69-Werte in API, Adapter-Contract-Tests und PostgreSQL-Integrationstests reproduzierbar umgesetzt sind.
