# M2 Decision Log

**Stand:** 24.08.2026  
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
| M2-D01 | BLOCKING | OPEN | Product + Domain | Darf der Partner eine Memory des Autors ändern oder löschen? | Rechte getrennt für read/update/delete festlegen; Autorregel nicht aus „shared“ ableiten. |
| M2-D02 | BLOCKING | OPEN | Domain + API | Erhalten Kommentare ein `version`-Feld für Optimistic Concurrency? | Einheitlich versionieren, falls Editieren nach M2-Vertrag erlaubt bleibt. |
| M2-D03 | BLOCKING | OPEN | Domain + Data | Wie werden mehrere Attachments gebunden: exklusive Ownership, Wiederverwendung, Join-Entity und Sortierreihenfolge? | Explizite Relation mit stabiler `position`; Cross-Space und Mehrfachbindung verbieten, sofern kein Use Case dagegen spricht. |
| M2-D04 | BLOCKING | OPEN | Security + Product | Welche MIME-Typen, Dateigrößen, Pixelgrenzen und Videodauern gelten je Plattform? | Kleine Positivliste definieren; Serverwerte bleiben verbindlich. |
| M2-D05 | BLOCKING | OPEN | Backend + Ops | Erfolgt Media-Validierung synchron beim Finalize oder asynchron? Welche internen Zustände sind nötig? | Externe Spec-Zustände bewahren; interne `VALIDATING`/`DELETING` nur per ADR ergänzen. |
| M2-D06 | BLOCKING | OPEN | Security + Privacy | Wird Emotion bei HeartMoment als Metadatum oder ProtectedPayload klassifiziert? | Als sensiblen Inhalt behandeln; Such-/Analytics-Bedarf explizit begründen. |
| M2-D07 | BLOCKING | OPEN | Domain + Privacy | Was geschieht mit Kommentaren beim Wechsel eines HeartMoment von `SHARED` zu `PRIVATE`? | Wechsel atomar nur mit klarer Delete/Hide-Regel; keine Kommentare indirekt sichtbar lassen. |
| M2-D08 | BLOCKING | PROPOSED | API + Data | Welche Story-Sortierung gilt bei fehlendem `happenedOn`, und welcher Tie-Breaker stabilisiert Cursor? | `COALESCE(happenedOn, createdAt)`, danach `createdAt`, danach `id`; Cursor opak und versioniert. |
| M2-D09 | BLOCKING | OPEN | API | Exakte Routen, Nesting und DTO-Namen? | Erst nach Abschluss des OpenAPI-Gates verbindlich in den Vertrag überführen; `API-DESIGN.md` als fachliche Vorlage. |
| M2-D10 | BEFORE_CLIENTS | OPEN | Product + Privacy | Welche Notification Preview darf ein Kommentar zeigen? | Standardmäßig generisch; Content-Auszug nur nach expliziter Privacy-Freigabe. |
| M2-D11 | BLOCKING | OPEN | Data + Privacy | Delete-, Retention- und Cascade-Regeln für Entity, Relation, Blob, Event und Audit? | Fachliche Löschung sofort unsichtbar; physische Bereinigung idempotent und messbar. |
| M2-D12 | BLOCKING | OPEN | Backend + Ops | Wie lange bleiben unvollständige/fehlgeschlagene Uploads erhalten? | kurze, konfigurierbare Retention mit wiederholbarem Cleanup und Metrik. |
| M2-D13 | BLOCKING | OPEN | Security + Media | Direct Upload oder serverseitiger Stream je Local-/S3-Adapter? | Ein Domainvertrag, adapterspezifischer Transport; Autorisierung und Finalize bleiben serverkontrolliert. |
| M2-D14 | BEFORE_CLIENTS | OPEN | Privacy + Product | Werden EXIF, GPS und weitere eingebettete Metadaten entfernt? | GPS standardmäßig entfernen; Verhalten in UI und Export dokumentieren. |
| M2-D15 | BEFORE_CLIENTS | OPEN | Media + Product | Sind Thumbnailing, Transcoding und Poster Frames Teil von M2? | Nur aufnehmen, wenn Client-Performance ohne sie das Budget verfehlt; sonst separater Slice. |
| M2-D16 | BLOCKING | OPEN | Architecture + Security | Minimales Schema je M2-Domain-Event? | IDs, Typ, Actor, Space, Zeitpunkt, Version; keine Titel/Bodies/Kommentare/URLs. |
| M2-D17 | BEFORE_CLIENTS | OPEN | Product + Privacy | Welche privaten Daten enthält persönlicher Export, gemeinsamer Export oder Backup? | Owner-Export und Partnerexport strikt trennen; Private niemals in Partnerexport. |
| M2-D18 | BEFORE_CLIENTS | OPEN | Client + Security | Welche Cache-/Offline-Retention gilt für private Inhalte auf Web und Android? | Owner-/Space-gebundene Caches, vollständige Löschung bei Logout/Space-Wechsel, kein Offline Write. |
| M2-D19 | LATER | PROPOSED | Architecture | Wie bleibt E2EE nachrüstbar, ohne heute echte E2EE vorzutäuschen? | ProtectedPayload und opaque MediaStore beibehalten; Key Management ausdrücklich außerhalb M2. |
| M2-D20 | BLOCKING | OPEN | Domain | Kann ein Attachment ohne Parent `READY` sein und wie lange? | Kurzes Bindungsfenster definieren; dauerhaft ungebundene Ready-Objekte per Cleanup entfernen. |
| M2-D21 | BEFORE_CLIENTS | OPEN | Search + Privacy | Wird M2-Suche direkt in Postgres oder über separaten Index umgesetzt? | Für M2 bevorzugt tenant-gefilterte DB-Suche; separaten Index nur mit Lösch-/Privacy-SLA. |
| M2-D22 | BEFORE_CLIENTS | OPEN | Product + UX | Ist der Owner-Bereich für private HeartMoments Teil der gemeinsamen Story-Route oder eine getrennte Ansicht? | Getrennte, klar markierte Owner-Ansicht reduziert versehentliche Offenlegung. |

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
