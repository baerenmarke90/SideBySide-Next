# M2 Security & Privacy Test Matrix

**Status:** verbindliche Abnahmematrix für M2  
**Stand:** 24.08.2026

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
- Autorisierung wird serverseitig vor Projektion, Suche, Zählung, Pagination und URL-Erzeugung angewandt.

## Kernmatrix

| Ressource / Operation | A | B | C / X / R | ANON | Kritische Zusatzerwartung |
|---|---:|---:|---:|---:|---|
| eigene Memory anlegen | ✅ | ✅ eigene | ❌ | `401` | `spaceId` aus Membership-Kontext prüfen |
| geteilte Memory lesen/listen/suchen | ✅ | ✅ | `404`/leer | `401` | keine Cross-Tenant-Treffer oder Counts |
| eigene Memory ändern/löschen | ✅ | nach Regel im Decision Log | `404` | `401` | Version erforderlich, Autor nicht umhängbar |
| fremde Memory per erratener ID | ✅ im selben Space | ✅ im selben Space | `404` | `401` | gleiches Verhalten für existente/nicht existente ID |
| `SHARED` HeartMoment lesen | ✅ | ✅ | `404`/leer | `401` | darf in Story und Suche erscheinen |
| eigenes `PRIVATE` HeartMoment | ✅ | ❌ | `404` | `401` | ausschließlich Owner |
| fremdes `PRIVATE` HeartMoment per ID | `404` | `404` | `404` | `401` | kein Existenzsignal, auch nicht für Partner |
| `PRIVATE` in Story/Suche/Dashboard | eigener expliziter Owner-Bereich gemäß Vertrag | ❌ | ❌ | `401` | vor Sortierung/Count/Pagination filtern |
| Milestone lesen/listen/suchen | ✅ | ✅ | `404`/leer | `401` | Space-Isolation wie Memory |
| Kommentar auf erlaubtes Shared Target | ✅ | ✅ | `404` | `401` | Target und Autor müssen selben Space haben |
| Kommentar auf privates HeartMoment | ❌ | ❌ | `404` | `401` | auch Owner darf keinen Shared-Kommentarpfad erzeugen |
| Kommentar auf ungültigen Target-Typ | `422` | `422` | `422` ohne Lookup | `401` | keine frei polymorphe Relation |
| Attachment-Metadaten lesen | gemäß sichtbarem Parent | gemäß sichtbarem Parent | `404` | `401` | Attachment allein macht Parent nicht sichtbar |
| Attachment-Inhalt abrufen | gemäß sichtbarem Parent | gemäß sichtbarem Parent | `404` | `401` | Autorisierung unmittelbar vor URL/Stream |
| Story lesen | geteilter Space-Inhalt | geteilter Space-Inhalt | `404`/leer | `401` | keine privaten HeartMoments |

`✅` bedeutet nur „fachlich grundsätzlich erlaubt“; Tenant-, Status-, Versions- und Payload-Prüfungen bleiben verpflichtend.

## Owner-only: Pflichtpfade

Für ein `PRIVATE` HeartMoment von `A` muss `B` in jedem folgenden Pfad exakt keinen Hinweis erhalten:

1. Direktabruf und Update/Delete-Versuch.
2. Listen, Volltextsuche, Filter und Autocomplete.
3. Story, Monatsgruppen, Counts und Cursor.
4. Dashboard, Activity Feed, Recap und „zuletzt geändert“.
5. Kommentar-Target-Auflösung und Comment-Listen.
6. Attachment-Metadaten, Dateiabruf, Vorschaubild und signierte URL.
7. Domain Events, Notifications, Push Preview und Badge Count.
8. Partnerexport, geteiltes Backup und Diagnoseausgabe.
9. Cache Keys, ETags, Logs, Traces, Metriken und Analytics Properties.
10. Fehlerverhalten bei bekannter ID und indirekten Relations-IDs.

Ein Testdatensatz enthält dabei eindeutig erkennbare Canary-Werte in Text, Emotion, Dateiname und Attachment-Metadaten. Kein Canary darf außerhalb des Owner-Kontexts auftauchen.

## IDOR- und Tenant-Isolation

| ID | Angriff | Erwartung |
|---|---|---|
| TEN-01 | `C` liest/ändert/löscht Alpha-Entity über UUID | `404`, keine Mutation |
| TEN-02 | `A` setzt `spaceId=Beta` in Body, Query oder Route | Request abweisen, keine implizite Umschreibung |
| TEN-03 | Comment aus Alpha referenziert Target aus Beta | atomar abweisen, kein Event |
| TEN-04 | Attachment aus Alpha an Parent in Beta binden | atomar abweisen |
| TEN-05 | Cursor aus Alpha für Beta verwenden | neutraler Fehler oder leeres Ergebnis gemäß Vertrag, keine Daten |
| TEN-06 | signierte URL/Read-Token zwischen Spaces wiederverwenden | Zugriff verweigern |
| TEN-07 | widerrufenes Mitglied nutzt alten Token | spätestens beim autorisierten Zugriff verweigern |
| TEN-08 | Groß-/Kleinschreibung, Encoding und doppelte Parameter | kanonisch und fail-closed |

## Medienmissbrauch

| ID | Fall | Erwartung |
|---|---|---|
| MED-01 | Dateiendung erlaubt, tatsächlicher MIME verboten | `FAILED`, kein lesbarer Blob |
| MED-02 | deklarierter MIME weicht vom erkannten Typ ab | abweisen und sicher protokollieren |
| MED-03 | Datei/Pixel/Dauer über Limit | vor `READY` abweisen |
| MED-04 | Dekompressionsbombe oder extreme Dimension | Ressourcenlimit greift, Worker bleibt stabil |
| MED-05 | manipuliertes Bild/Video/Container | Parserfehler isoliert, Status `FAILED` |
| MED-06 | Originalname mit Pfad-/Unicode-Steuerzeichen | nur Anzeige-Metadatum; niemals Teil des Storage Keys |
| MED-07 | doppeltes Finalize oder parallele Finalize-Requests | idempotentes Ergebnis, genau ein finaler Zustand |
| MED-08 | Read URL abgelaufen oder verändert | verweigert; kurze TTL |
| MED-09 | Read URL nach Membership-Entzug | Risiko je Adapter dokumentiert; TTL minimiert Restfenster |
| MED-10 | fremder `storageKey` im Request | Feld nicht clientseitig setzbar bzw. ignoriert/abgewiesen |
| MED-11 | Upload ohne Finalize / verwaister Blob | nach Retention sicher bereinigt |
| MED-12 | Storage antwortet teilweise oder mit Timeout | Retry ohne doppelte Relation oder falsches `READY` |
| MED-13 | Metadaten/EXIF enthalten Standort | Verhalten explizit entschieden und getestet |
| MED-14 | Local- und S3-Adapter | identischer Contract und Autorisierungssemantik |

## Concurrency und Transaktionen

- Zwei Updates mit derselben Version: genau eines gewinnt, das andere erhält `409`.
- Update parallel zu Delete: kein Wiederauftauchen, konsistentes Fehlerbild.
- Parent-Delete parallel zu Attachment-Finalize: kein sichtbarer Orphan und keine Relation zu gelöschtem Parent.
- Comment-Create parallel zu Target-Privatisierung oder Delete: Transaktion verhindert unzulässigen Kommentar.
- Doppelter Create mit Idempotency-Key: eine fachliche Entity und höchstens ein Outbox-Event.
- Domainänderung plus Outbox: entweder beides committed oder beides verworfen.
- Wiederholte Worker-Zustellung: Notification ist dedupliziert oder semantisch idempotent.
- Cursor-Abfrage bei parallelen Inserts: keine Duplikate innerhalb stabiler Tie-Breaker-Semantik.

## Story, Suche und Pagination

1. Private Inhalte werden **vor** Count, Gruppierung, Suche, Sortierung und Cursorbildung entfernt.
2. Primärsortierung nutzt `happenedOn`; Fallback und Tie-Breaker entsprechen dem Decision Log.
3. `type`, `year`, `q`, `order`, `cursor` und `limit` sind kombinierbar und validiert.
4. Ungültige oder manipulierte Cursor führen zu einem neutralen Clientfehler, nicht zu Datenbankdetails.
5. Page 1 + Page 2 enthalten bei unverändertem Datenbestand weder Lücken noch Duplikate.
6. Suchindex, falls separat, übernimmt Berechtigungsänderungen und Löschungen nachweisbar.
7. Gruppenüberschriften oder leere Monate verraten keine privaten Treffer.
8. Attachment-Vorschaudaten werden nur für bereits autorisierte Story Items projiziert.

## Logging, Telemetrie und Events

- Keine Titel, Bodies, Kommentare, Originaldateien, Read URLs oder privaten Emotionen in Standardlogs.
- IDs werden nur soweit für Betrieb nötig geloggt; keine Tokens, Signaturen oder Storage Credentials.
- Fehlertracking erhält bereinigte Payloads und keine kompletten Request Bodies.
- Domain Events enthalten minimale Referenzen statt geschützter Inhalte.
- Notification Preview verwendet nur die explizit freigegebene Darstellung.
- Metriken haben begrenzte Kardinalität und keine Nutzertexte als Labels.
- Auditdaten respektieren Tenant und Retention; operative Einsicht ist rollenbasiert.

## Client- und Cache-Prüfungen

| Bereich | Web | Android |
|---|---|---|
| Logout / Space-Wechsel | Query- und Mediencache vollständig leeren | lokale Projektionen und Bildcache leeren |
| PRIVATE-Daten | nie in gemeinsamem Browser-/Service-Worker-Cache | owner-gebunden, nicht in Backup/Share Sheet |
| Offline | letzte autorisierte Ansicht lesbar | letzte autorisierte Ansicht lesbar |
| Offline Write | deaktiviert oder klar blockiert | deaktiviert oder klar blockiert |
| Read URL | nicht dauerhaft persistieren | nicht dauerhaft persistieren |
| Screenshots/Recents | Produktentscheidung dokumentieren | sensible Screens ggf. schützen |

## Adapter-Contract-Tests

Jede `MediaStore`-Implementierung muss denselben Testkatalog bestehen:

- `createUpload` erzeugt nicht erratbare, Space-gebundene Keys.
- `finalizeUpload` ist idempotent und prüft Besitz/Status.
- `open`/`createReadUrl` ist ohne vorherige Domainautorisierung nicht erreichbar.
- `delete` ist idempotent und löscht nur den exakt adressierten Blob.
- Teilfehler verändern den fachlichen Status nicht irreführend.
- Kein Adapter macht Cloud-Medien öffentlich.
- Ein zukünftiger verschlüsselter Blob kann ohne Plaintext-Annahme gespeichert und übertragen werden.

## Abnahmekriterium

M2 ist sicherheitsseitig nicht fertig, solange ein Pflichtpfad fehlt, ein Cross-Tenant-Test nur auf Repository-Ebene existiert oder ein privater HeartMoment indirekt sichtbar werden kann. Alle kritischen Fälle müssen im CI reproduzierbar und für LocalMediaStore sowie S3-kompatiblen MediaStore grün sein.
