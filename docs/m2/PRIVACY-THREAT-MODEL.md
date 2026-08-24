# M2 Privacy Threat Model

**Scope:** Memory, HeartMoment, Milestone, Comment, Story und Attachment  
**Methode:** Datenfluss- und Abuse-Case-orientierte Bedrohungsanalyse  
**Stand:** 24.08.2026

Dieses Modell ergänzt die [Security Test Matrix](./SECURITY-TEST-MATRIX.md) um Angreifer, Vertrauensgrenzen, Datenflüsse und konkrete Kontrollen. Es macht keine Aussage, dass M2 echte Ende-zu-Ende-Verschlüsselung bietet.

![M2 Privacy Flow](./m2-privacy-flow.svg)

## 1. Schutzziele

1. **Vertraulichkeit:** Private HeartMoments sind ausschließlich für den Owner sichtbar.
2. **Tenant-Isolation:** Kein Space kann Entitäten oder Medien eines anderen Space erkennen.
3. **Integrität:** Autor, Space, Visibility, Version und Attachment-Relation können nicht clientseitig umgehängt werden.
4. **Minimierung:** Logs, Events, Analytics und Notifications enthalten keine geschützten Inhalte.
5. **Nachvollziehbarkeit:** fachliche Änderung und minimales Domain Event committen atomar.
6. **Löschwirkung:** gelöschte oder privatisierte Inhalte werden sofort aus allen autorisierten Projektionen entfernt.
7. **E2EE-Readiness:** ProtectedPayload und MediaStore bauen keine zwingende Plaintext-Annahme ein.

## 2. Schutzwürdige Assets

| Asset | Sensitivität | Beispiele | besondere Gefahr |
|---|---|---|---|
| ProtectedPayload | hoch | Titel, Body, Kommentartext | Logs, Suche, Push, Diagnose |
| PRIVATE HeartMoment | sehr hoch | Text, Emotion, Datum, Attachment | Partner-Leak über indirekten Pfad |
| Medieninhalt | hoch | Foto, Video, Audio | öffentliche URL, Cache, EXIF/GPS |
| Beziehungs-/Space-Metadaten | hoch | Membership, Autor, Visibility | soziale Rückschlüsse und IDOR |
| Such-/Story-Metadaten | mittel bis hoch | Treffer, Counts, Cursor, Monate | Existenzleak ohne Inhalt |
| Credentials und Read URLs | kritisch | Session, Signatur, Storage Key | direkte Umgehung der API |
| lokale Caches/Entwürfe | hoch | Offline Read, ungespeicherter Text | falscher Account/Space, Backup |
| Domain Events | mittel bis hoch | Typ, Actor, Target | Content-Leak durch Payload-Ausweitung |

## 3. Akteure und Fähigkeiten

| Akteur | legitimer Zugriff | angenommene Fähigkeit |
|---|---|---|
| Owner `A` | eigene und geteilte Inhalte in Space Alpha | manipuliert Requests und kennt eigene IDs |
| Partner `B` | geteilte Inhalte in Space Alpha | errät/erhält private IDs und prüft Nebenkanäle |
| Fremdmitglied `C` | Inhalte in Space Beta | versucht Cross-Tenant-IDOR und Cursor-Reuse |
| widerrufenes Mitglied `R` | kein aktueller Zugriff | besitzt alte Tokens, URLs oder Cache |
| anonymer Angreifer | kein Zugriff | scannt Routen, IDs, Medienendpunkte |
| fehlerhafte Integration | nur minimaler Event-/Push-Zugriff | loggt oder projiziert zu viel |
| interner Operator | betriebliche Diagnose | sieht Logs/Traces/Backups überprivilegiert |

Client und Netzwerk gelten nicht als Vertrauensanker. Jede Domainoperation erzwingt Auth, aktuelle Membership, Tenant und Ressourcensichtbarkeit serverseitig.

## 4. Vertrauensgrenzen

```text
Gerät/Browser
  → öffentliche API-Grenze
    → Auth + Membership + Visibility Guard
      → Domaintransaktion + Projektion
        → Postgres / MediaStore
        → Outbox → Worker → Notification Provider
```

- **TB-1 Gerät:** Cache, Clipboard, Screenshots, Backups und andere Apps.
- **TB-2 Transport/API:** manipulierte IDs, Bodies, Cursor, MIME und Concurrency.
- **TB-3 Domain/Storage:** fachliche Sichtbarkeit versus physischer Blob/Datensatz.
- **TB-4 Async:** Event, Retry, Push Preview und externe Provider.
- **TB-5 Operations:** Logs, Fehlertracking, Metriken, Support und Backups.

## 5. Datenflüsse

| Flow | Quelle → Ziel | Daten | erforderliche Kontrolle |
|---|---|---|---|
| DF-01 | Client → API | Create/Update DTO | Schema, Auth, Membership, Version |
| DF-02 | API → Domain | Actor + Space + Operation | serverabgeleiteter Actor/Space |
| DF-03 | Domain → Postgres | Metadaten + ProtectedPayload | Tenant, Transaktion, minimale Logs |
| DF-04 | Client → MediaStore | Blob über Uploadpfad | nicht erratbarer Key, Limits, Finalize |
| DF-05 | Domain → Read Projection | Story/Detail/Search | Visibility vor Count/Sort/Cursor |
| DF-06 | API → Client | DTO + Read URL/Stream | Autorisierung unmittelbar vorher, kurze TTL |
| DF-07 | Domain → Outbox | minimales Ereignis | atomar, kein Content |
| DF-08 | Worker → Notification | generische Preview | Zielberechtigung und Datenminimierung |
| DF-09 | Client ↔ lokaler Cache | autorisierte Read-Daten/Entwurf | Owner-/Space-Bindung, Löschung/Sperre |

## 6. Bedrohungen und Kontrollen

| ID | Bedrohung | Angriffspfad | Auswirkung | Pflichtkontrollen | Nachweis |
|---|---|---|---|---|---|
| TM-01 | Cross-Tenant IDOR | fremde UUID in Read/Write/Delete | Datenleck/Mutation | Tenant aus Membership, Parent/Child gleicher Space, privacy-safe 404 | HTTP-Isolationstests |
| TM-02 | Partner liest PRIVATE direkt | bekannte HeartMoment-ID | schwerer Privacy-Verstoß | zentrale Owner-only Policy vor Repositoryprojektion | A/B-Canary per ID |
| TM-03 | PRIVATE leak über Story/Suche | Filter erst nach Count/Pagination | Existenz-, Datum- oder Timing-Leak | vor Query/Count/Sort/Cursor ausschließen | Count-, Cursor-, Timing-Tests |
| TM-04 | PRIVATE leak über Relation | Comment/Attachment/Notification löst Parent indirekt auf | Inhalt oder Existenz sichtbar | Parent-Sichtbarkeit bestimmt jede Relation | indirekte Canary-Suite |
| TM-05 | öffentliche/zu lange Media URL | Bucket ACL oder langlebige Signatur | unkontrollierter Abruf | private Storage Defaults, kurze TTL, autorisierter Stream/URL | URL-Ablauf- und ACL-Test |
| TM-06 | Upload-Spoofing | Endung/MIME/Container manipuliert | Schadinhalt, Parser-/Ressourcenangriff | Positivliste, tatsächlicher MIME, Größen-/Pixel-/Dauerlimit, isolierte Verarbeitung | Media-Abuse-Suite |
| TM-07 | Storage-Key-Injektion | Dateiname/Pfad als Key | Überschreiben/fremder Zugriff | servergenerierte UUID-Keys; Name nur Metadatum | Key-Contract-Test |
| TM-08 | Cache nach Logout/Space-Wechsel | Browser-/Android-Cache bleibt erhalten | nachträglicher Zugriff | Cache nach Owner/Space partitionieren und löschen/sperren | Logout-/Switch-E2E |
| TM-09 | Notification Preview | Kommentar-/Titeltext im Push | Lockscreen-/Provider-Leak | generische Preview, minimaler Event, Preferences | Push-Payload-Snapshot |
| TM-10 | Logging/Analytics Leak | Request Body, URL oder Suchtext geloggt | interner/Third-Party-Leak | Allowlist-Logging, Redaction, keine Content-Properties | Canary in Logscan |
| TM-11 | Visibility Race | Share/Private parallel zu Comment/Read | unzulässige Relation/kurzes Leak | Version, Transaktion, Guard beim finalen Read/Event | Race-Test |
| TM-12 | Revoked Membership | alter Token/Read URL/Cache | Zugriff nach Entzug | Membership bei API-Read, kurze URL-TTL, Cache-Sperre | Revocation-E2E |
| TM-13 | Cursor-/Fehler-Orakel | Cursor aus anderem Space, verschiedene 403/404 | Ressourcenerkennung | opaker Space-gebundener Cursor, neutrales Fehlerbild | Manipulationsmatrix |
| TM-14 | Export/Backup Leak | PRIVATE im Partnerexport oder Systembackup | dauerhafte Offenlegung | Owner- und Partnerexport trennen; Cache-/Backup-Regel | Export-Canary |
| TM-15 | Screenshot/Recents | private Ansicht im App Switcher | Schulterblick/OS-Artefakt | bewusste Plattformentscheidung, optional Screen-Schutz | Android-UX-/Security-Test |
| TM-16 | Outbox Replay | Worker liefert mehrfach | doppelte Pushs/Seiteneffekte | Idempotenz/Dedupe, minimale Eventversion | Retry-Test |
| TM-17 | Delete-Orphan | Parent gelöscht, Blob/Index/Cache bleibt | spätere Wiederentdeckung | sofort unsichtbar, idempotenter Cleanup, Suchindex-SLA | Delete-/Cleanup-Test |
| TM-18 | Diagnose-/Support-Übergriff | Operator sieht Content | interner Privacy-Verstoß | Rollen, Break-glass, Audit, Redaction, Retention | Ops-Review |

## 7. Owner-only Kontrollpunkt

Für `PRIVATE` gilt eine einzige fachliche Aussage:

```text
visible(resource, actor) = resource.ownerId == actor.id
```

Membership im selben Space reicht nicht. Diese Regel muss vor allen folgenden Operationen greifen:

- Detail, Update, Delete,
- Liste, Suche, Count, Filter, Cursor,
- Story, Dashboard, Recap, zuletzt geöffnet,
- Comment-Target und Comment Count,
- Attachment-Metadaten, Thumbnail, Download, Read URL,
- Event, Notification, Badge Count,
- Analytics, Diagnose, Export und Cache-Projektion.

## 8. Privacy-Canaries

Testdaten enthalten künstliche Marker:

- `CANARY-PRIVATE-LEA-7421` im privaten Text,
- `private-lea-7421.jpg` als Originalname,
- eindeutiges fachliches Datum,
- Attachment mit eindeutigem Testhash.

Partner-, Fremd- und Operator-Standardpfade werden automatisiert nach diesen Markern durchsucht. Kein Marker darf in Response, DOM, Cache, Log, Trace, Event, Notification, Export oder Screenshot-Testfixture auftauchen.

## 9. Client-Kontrollen

### Web

- Query-/Service-Worker-/Bildcache nach Owner und Space partitionieren.
- Logout/Space-Wechsel löscht/sperrt Daten vor Navigation.
- Read URLs nicht in Local Storage, Analytics, History oder dauerhaften Cache schreiben.
- Private Deep Links nie in öffentlichen Metatags oder Server-rendered Cache aufnehmen.

### Android

- sensible lokale Daten verschlüsselt und account-/space-gebunden speichern.
- keine privaten Inhalte im allgemeinen Backup, Clipboard oder Share Sheet.
- Notifications standardmäßig ohne Content Preview.
- Recents-/Screenshot-Verhalten explizit entscheiden und testen.
- kein autonomer Offline-Write-Worker im MVP.

## 10. Async- und Observability-Vertrag

Ein M2-Event enthält höchstens:

```text
eventId · eventType · occurredAt · actorId · spaceId · targetType · targetId · version
```

Keine Titel, Bodies, Kommentare, Emotionen, Dateinamen, Storage Keys oder Read URLs. Jeder zusätzliche Wert benötigt Privacy-Review und dokumentierten Consumer.

## 11. Restrisiken und offene Entscheidungen

| Thema | Restrisiko | benötigte Entscheidung |
|---|---|---|
| signierte URL nach Membership-Entzug | bis TTL-Ende eventuell nutzbar | TTL/Stream je Adapter `M2-D13` |
| EXIF/GPS | eingebettete Standortdaten | Strip-Regel `M2-D14` |
| Shared → Private | bereits gelesene Inhalte/Kommentare | Kommentarregel `M2-D07` |
| Emotion | Metadatum versus ProtectedPayload | Klassifikation `M2-D06` |
| Android Recents | Screenshot des privaten Screens | Plattformregel |
| Export/Backup | unterschiedliche Empfänger und Retention | `M2-D17`/`M2-D18` |

## 12. Release Gate

M2 wird nicht freigegeben, wenn:

- Owner-only nur im Controller oder nur per UI-Filter umgesetzt ist,
- ein Partner-Canary indirekt sichtbar ist,
- Medien ohne Parent-Autorisierung abrufbar sind,
- Push, Logs oder Analytics geschützten Inhalt tragen,
- Logout/Space-Wechsel private Caches zurücklässt,
- Cross-Tenant- und Race-Tests nicht über die öffentliche API laufen,
- das Produkt E2EE behauptet, obwohl nur E2EE-Readiness besteht.
