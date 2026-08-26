# M3 Privacy Threat Model

**Status:** Readiness-Grundlage für M3  
**Stand:** 26.08.2026

M3 vergrößert die Privacy-Fläche deutlich: Neben gemeinsamem Planungsinhalt entstehen erstmals mehrere bewusst private Owner-only-Domänen und präzise Ortsdaten. Dieses Dokument definiert die Bedrohungen, die vor Runtime-Code in Modell, API und Tests berücksichtigt werden müssen.

## 1. Schutzgüter

### Gemeinsame M3-Inhalte

- Wish und Status
- Plan, Beschreibung, Termin-/Erlebnisdaten
- Place, Adresse und Koordinaten
- Chapter und Relationen
- Collection und Items

Diese Inhalte sind `SPACE_SHARED`, aber **nicht öffentlich**. Sie dürfen nur aktive Mitglieder desselben Space erhalten.

### Owner-only-Inhalte

- PrivateNote
- GiftIdea
- PrivateCollection
- PrivateCollectionItem

Für diese Inhalte gilt: Der Partner darf nicht nur den Inhalt, sondern soweit möglich auch **die Existenz** nicht erfahren.

### Besonders sensitive Metadaten

- genaue Koordinaten und Adresse,
- GiftIdea-URL, Empfänger, Anlass, Preistext,
- Titel/Freitexte privater Notizen und Listen,
- Relationen, aus denen private Interessen oder Aufenthaltsorte ableitbar wären,
- Counts/Sortierpositionen, wenn sie versteckte private Einträge verraten könnten.

## 2. Vertrauensgrenzen

```text
Web / Android
    |
    | HTTPS + Bearer/Auth
    v
FastAPI / Authorization
    |
    +--> PostgreSQL
    |
    +--> Outbox/Worker
    |
    +--> Logs/Metrics/Error Tracking
```

M3 führt **keine neue externe Provider-Grenze** ein. Insbesondere werden Maps, Geocoding, URL-Previews und Discovery nicht serverseitig aufgerufen.

## 3. Zentrale Invarianten

### T1 – Space zuerst

Kein M3-Read/Write wird allein über Resource-ID aufgelöst. Immer:

1. Authentifizierung,
2. aktive Membership in `spaceId`,
3. Query innerhalb dieses Space,
4. zusätzliche Owner-/Write-Regel.

### T2 – Owner-only in der Query

Private Area wird nicht geladen und anschließend im Service verworfen. Die Ownerbedingung ist Teil der Query/Authorization.

### T3 – Keine indirekte Private-Auskunft

`OWNER_ONLY` darf nicht sichtbar werden über:

- fremde GET-by-ID,
- Listen,
- Counts,
- Relationen,
- Fehlermeldungen,
- Sortierlücken,
- Search/Autocomplete,
- Chapter/Place,
- Dashboard/Activity/Notifications,
- Export,
- Domain Events,
- Logs/Metriken,
- Deep Links.

### T4 – Relation erweitert niemals Rechte

Eine Relation ist kein Capability-Token. Wer ein Chapter oder Place lesen kann, bekommt dadurch keinen Zugriff auf ein Target, das sonst nicht lesbar wäre.

### T5 – Keine Shared->Private-Mischdomäne

Wish/Plan/Collection werden nicht durch ein Privacy-Flag in private Ablage verwandelt. PrivateNote/GiftIdea/PrivateCollection bleiben eigene Domainmodelle. Dadurch kann ein falsch interpretierter Shared-Filter keine privaten Daten freigeben.

## 4. Threats und Controls

### M3-T01 – ID Enumeration in Private Area

**Angriff:** Partner errät `noteId`/`giftIdeaId`/private Collection-ID und vergleicht Antworten.

**Controls:**

- owner-scoped Query,
- identisches privacy-sicheres 404 für unbekannt/fremd/anderer Space/gelöscht,
- keine unterschiedliche Fehlermeldung,
- keine vorherige Exists-Query ohne Ownerfilter.

**Tests:** Partner-ID-Sweep gegen existierende und nicht existierende IDs liefert semantisch gleiche Antwortklasse.

### M3-T02 – Cross-Space ID Substitution

**Angriff:** gültige ID aus Space A wird in Route von Space B eingesetzt.

**Controls:**

- Membership in Route-Space zuerst,
- Ressourcenquery enthält `space_id`,
- Relationstabellen sichern Space-Konsistenz service-/constraintseitig.

**Tests:** alle M3-Domänen und alle Relationstypen.

### M3-T03 – Cross-Space Relation

**Angriff:** Place/Chapter aus Space A wird mit Memory/Plan aus Space B verbunden.

**Controls:**

- beide Targets space-scoped laden,
- DB-Constraints soweit möglich,
- Transaktion re-checkt vor Insert,
- nach außen 404, keine Fremdspace-Auskunft.

### M3-T04 – Private HeartMoment über Shared Chapter/Place

**Angriff:** Nutzer kennt private HeartMoment-ID und versucht, sie mit gemeinsamem Chapter/Place zu verbinden; Partner erkennt Existenz aus Relation oder Count.

**Controls:**

- Target muss für Actor im Shared-Kontext lesbar und relationierbar sein,
- `OWNER_ONLY` HeartMoment wird für gemeinsame Relation wie nicht vorhanden behandelt,
- bestehende Relation muss bei `SHARED -> PRIVATE` atomar/serialisiert entfernt bzw. vor Commit verhindert werden – endgültige Semantik M3-D09/M3-D26.

### M3-T05 – Relation Race gegen Privacy-Wechsel

**Angriff:** gleichzeitig `link shared HeartMoment -> Chapter` und `SHARED -> PRIVATE`.

**Risiko:** Relation bleibt nach Privacy-Commit bestehen und verrät private Existenz.

**Controls:**

- Row Lock/serialisierte Reihenfolge auf Target/Relation,
- Re-Check der Privacy vor Commit,
- Privacy-Wechsel muss M3-Relationen in seiner Cascade-/Listener-Grenze berücksichtigen, sobald diese Domain existiert.

### M3-T06 – Wish->Plan Double Submit

**Angriff/Fehler:** zwei Geräte oder Retry erzeugen zwei Plans aus einem Wish.

**Controls:**

- definierte Kardinalität,
- DB Unique Constraint,
- Row Lock/atomare Transaktion,
- stabile Conflict/Idempotenzantwort.

### M3-T07 – Delete-vs-Relation Race

**Angriff/Fehler:** Target wird gelöscht, während Relation erstellt wird.

**Controls:**

- FK verhindert dangling relation,
- fachlicher Service übersetzt Integrity-/Lock-Ergebnis in stabilen Fehler,
- keine Catch-and-ignore-Logik, die Phantomrelation bestätigt.

### M3-T08 – Partner bearbeitet creator-owned Shared Content

**Angriff:** Client zeigt Aktion nicht, Partner sendet Request manuell.

**Controls:**

- M3-D01 bestimmt Write Policy serverseitig,
- Capabilities nur Darstellung,
- Query/Service erzwingt die Regel.

### M3-T09 – Private Count Leakage

**Angriff:** gemeinsame Antwort enthält z. B. `privateItemCount`, Gesamtcount oder Paginationverhalten, aus dem Partner private Inhalte ableitet.

**Controls:**

- Shared Endpoints zählen nur shared Domain,
- Private Collections besitzen getrennte owner-only Listen,
- keine kombinierte Shared+Private Collection-Liste mit clientseitigem Filter.

### M3-T10 – Sortier-/Positionsleck

**Angriff:** sichtbare gemeinsame Items haben Positionen `1,4,7`, weil private Items in derselben Tabelle mitsortiert wurden.

**Control:** Shared und Private Collections sind getrennte Tabellen/Aggregate; Positionsräume werden nicht gemischt.

### M3-T11 – Location Leakage über Telemetrie

**Angriff/Fehler:** Koordinaten/Adresse erscheinen in Logs, Metrics, Analytics, Error Context oder Outbox.

**Controls:**

- strukturierte Redaction,
- Events ohne Location-Payload,
- Request-Logging darf Bodies nicht ungescrubbt erfassen,
- Tests auf Event-/Logrepräsentationen.

### M3-T12 – Location Leakage über Relation/Read Model

**Angriff:** Place wird später in Dashboard/Search projiziert und verrät mehr als der autorisierte Parent.

**Control in M3:** keine neuen Dashboard/Search-Projektionen. Spätere Read Models müssen Space-/Privacy-Regel erneut anwenden; M3 speichert keine „öffentliche“ Place-Variante.

### M3-T13 – GiftIdea URL SSRF/Tracking

**Angriff:** Nutzer speichert interne URL; Backend lädt Preview oder Metadaten und wird SSRF-Proxy.

**Control:** M3 speichert URL nur als Inhalt und führt keinen serverseitigen Fetch aus.

Späteres Preview benötigt eigenes Security-/Reuse-Design (URL-Allow/Block, DNS-Rebinding, Redirects, Content-Limits, Privacy).

### M3-T14 – GiftIdea URL im Partnerclient

**Angriff/Fehler:** Shared Client prefetch/instrumentiert URLs aus owner-only GiftIdea.

**Control:** Partner erhält GiftIdea überhaupt nicht. Ownerclient darf URL erst bei bewusster Interaktion öffnen; automatische externe Requests sind nicht Teil M3.

### M3-T15 – Private Inhalt in Domain Events

**Fehler:** Event enthält Titel/Body für bequemeren Consumer.

**Controls:** Event-Envelope IDs + sichere Zustände; keine ProtectedPayloads. Consumer laden autorisierte Daten nur in ihrem eigenen Kontext oder arbeiten ohne Inhalt.

### M3-T16 – Private Inhalt in Audit

Audit darf notwendige Sicherheitsmetadaten halten, aber keinen privaten Klartext duplizieren. Zulässig sind beispielsweise Actor, Aktion, Resource-ID, Zeitpunkt, Ergebnis. Titel/Body/GiftIdea-Details/Koordinaten gehören nicht hinein.

### M3-T17 – Private Export des Partners

M3 implementiert Export nicht, muss aber die Datenarchitektur so halten, dass M5 klar trennen kann:

- Owner-Export darf eigene private Ressourcen enthalten,
- gemeinsamer/Partnerexport niemals owner-only Ressourcen des anderen,
- Relationstabellen dürfen private Targets nicht in gemeinsamen Bundle-Metadaten verraten.

### M3-T18 – Cache nach Logout/Space-Wechsel

M3 implementiert keinen M5-Read-Cache. Trotzdem gilt als Architekturvoraussetzung:

- private DTOs nicht in unkontrolliertem Browserstorage persistieren,
- zukünftige Android-Caches account+space+owner scopen,
- Logout/Session-Revoke/Space-Wechsel muss sichere Cache-Clear-Regeln bekommen (M3-D22/M2-D18).

### M3-T19 – Chapter-Delete als Datenverlust

**Fehler:** DB Cascade löscht Memory/HeartMoment/Milestone statt Joinzeile.

**Control:** FK-Richtung und `ON DELETE` nur auf Join-Parent; Integrationstest prüft Originalbestand.

### M3-T20 – Doppelte Wahrheitsquelle Chapter/Place

**Fehler:** `chapter.place_id` zeigt Place A, `place_chapters` enthält Place B.

**Control:** M3-D31 entscheidet genau ein kanonisches Modell vor Migration.

## 5. Privacy-Klassifizierung

| Daten | Shared/Private | Sensitivität | Telemetrie |
|---|---|---|---|
| Wish title | shared | Beziehung/Interessen | kein Klartext |
| Plan title/description | shared | Pläne/Termine | kein Klartext |
| plannedStart/End | shared | Zeitplanung | keine hochkardinale Raw-Telemetrie |
| Place name/address | shared | potenziell Standort | kein Klartext |
| lat/lon | shared, aber hochsensitiv | präziser Standort | strikt verboten |
| Chapter title/description | shared | Beziehungsinhalt | kein Klartext |
| Collection/Item title | shared | Interessen/Checklisten | kein Klartext |
| PrivateNote | owner-only | hochsensitiv | strikt verboten |
| GiftIdea | owner-only | hochsensitiv | strikt verboten |
| PrivateCollection | owner-only | hochsensitiv | strikt verboten |

## 6. Fehlersemantik

### Nicht lesbar

Fremder Space, private Ressource des Partners, unbekannte ID und gelöschte private Ressource werden nach außen nicht unterschieden.

### Lesbar, aber nicht schreibbar

Falls M3-D01 creator-only Writes beschließt, kann bei einer gemeinsamen sichtbaren Ressource ein 403 fachlich korrekt sein – analog zur bestehenden Security-Konvention. Es bestätigt nichts, was der Partner nicht ohnehin lesen darf.

### Relationen

Nicht lesbares Target -> 404. Kein `RELATION_TARGET_PRIVATE` oder ähnlicher Code.

## 7. Logging / Analytics / Error Tracking

M3 darf technische Ereignisse wie folgende zählen:

```text
wish_created
plan_transition_completed
relation_create_failed
private_note_create_failed
```

Zulässige Dimensionen sind ausschließlich grobe technische Klassen, z. B. `result`, stabiler Error Code, Plattform/App-Version.

Nicht zulässig:

- Resource-ID als Analytics-Dimension,
- Titel/Text,
- genaue Daten/Termine bei sensiblen Flows,
- Adresse/Koordinaten,
- URL,
- Recipient/Occasion/PriceText,
- private Item Counts.

## 8. Provider- und Netzwerkgrenze

M3 hat keine fachliche Notwendigkeit für ausgehende Requests aufgrund von Place/GiftIdea-Inhalten.

Daher:

- keine Geocoding-API,
- keine Karten-Tile-Anbindung,
- keine Link Preview,
- keine URL-Validierung durch Fetch,
- keine automatische Location-Auflösung.

Ein späterer Provider-Slice benötigt `REUSE-BEFORE-BUILD`, Privacy-/Kosten-/ToS-/Self-Hosted-Bewertung und eigene Threats.

## 9. Security Gate für einen M3-Slice

Ein Slice ist nicht merge-ready, wenn:

- Cross-Tenant-Negativtest fehlt,
- Owner-only-Negativtest fehlt, sofern private Domain,
- Relation einen Target-Auth-Bypass ermöglicht,
- Race nur durch „wahrscheinlich nacheinander“ statt DB-/Transaction-Primitive abgesichert ist,
- Event/Log sensible Inhalte kopiert,
- Delete-Cascade nicht gegen Originaldatenverlust getestet ist,
- neue externe Datenübertragung ohne expliziten Scope eingeführt wird.

## 10. G3-Privacy-Mindestnachweis

Vor G3 müssen mindestens belastbar sein:

- alle Shared-M3-Domänen cross-tenant isoliert,
- jede Private-Area-Domain owner-only inklusive List/GET/Mutation,
- keine private Ressource über Shared Relation beweisbar,
- Wish->Plan und relevante Relation/Delete-Races PostgreSQL-basiert getestet,
- Chapter-Delete erhält Originalinhalte,
- Events/Logs enthalten keine geschützten M3-Payloads,
- Place-Koordinaten erscheinen nicht in Telemetrie,
- G3-spezifische Client-/E2E-Evidenz gemäß M3-D24 dokumentiert.
