# SIDEBYSIDE NEXT – CLEAN-ROOM MASTER SPECIFICATION

## 0. Auftrag

Du sollst **SideBySide Next** als vollständig neue, unabhängige Anwendung implementieren.

SideBySide Next ist eine private Paar-App für zwei Partner. Sie soll langfristig sowohl als:

1. **SideBySide Cloud** – kommerziell betriebener SaaS-Dienst
2. **SideBySide Self-Hosted** – selbst betriebene Installation

angeboten werden.

Das Projekt ist eine **Clean-Room-Neuimplementierung**.

Es existiert eine ältere Anwendung namens SideBySide Classic, die historisch aus SharedMoments hervorgegangen ist. Diese ältere Codebasis darf ausschließlich als historischer Hintergrund verstanden werden.

## ABSOLUTE CLEAN-ROOM-REGEL

Während der Implementierung von SideBySide Next darfst du **keinen Sourcecode von SharedMoments oder SideBySide Classic lesen, kopieren, portieren oder als Implementierungsvorlage verwenden.**

Wenn sich ein altes Repository auf dem System befindet:

- NICHT öffnen
- NICHT durchsuchen
- NICHT mit grep/ripgrep analysieren
- NICHT importieren
- NICHT Dateien daraus kopieren
- NICHT Code daraus übernehmen
- NICHT dort schreiben
- NICHT dort committen

Insbesondere dürfen nicht übernommen werden:

- Python-Code
- Flask-Routen
- SQLAlchemy-Models
- db_queries.py
- Jinja-Templates
- CSS
- JavaScript
- Kotlin-Code der alten Android-App
- alte `/api/v2/...`-Implementierungen
- Datenbankmigrationen
- Codekommentare
- alter Fragen-Seed
- Übersetzungstabellen als Bulk-Datensatz
- Demo-Inhalte
- alte Screenshots
- Assets ungeklärter Herkunft

Du implementierst ausschließlich anhand dieser Spezifikation.

Wenn die aktuelle Working Directory das alte SideBySide-/SharedMoments-Projekt ist, ändere dort NICHTS. Wechsle bzw. erstelle stattdessen einen neuen isolierten Workspace, z. B.:

~/Projekte/SideBySide-Next

Das alte Repository muss unangetastet bleiben.

---

# 1. Produktvision

SideBySide ist ein **privater digitaler Begleiter für das gemeinsame Leben eines Paares**.

Langfristig soll die App – soweit die Nutzer Funktionen freiwillig aktivieren – wissen bzw. verwalten können:

- gemeinsame Erinnerungen
- besondere emotionale Momente
- Meilensteine
- gemeinsame Geschichte
- Wünsche
- Pläne
- gemeinsame Orte
- gemeinsame Listen
- persönliche/private Inhalte
- wichtige Termine
- Partnerpräferenzen
- Geburtstage und wichtige Personen
- Paarfragen
- gemeinsames Befinden
- Einkaufslisten
- Rezeptideen
- Freizeit- und Veranstaltungsvorschläge
- externe Fotos
- optionale Standortinformationen
- kontextbezogene Hinweise

Produktpositionierung:

> SideBySide – die Paar-App, die euch gehört.

Privacy ist ein Kernelement.

Keine Werbung.
Kein Verkauf persönlicher Daten.
Kein unnötiges Tracking.
Sensible Inhalte dürfen nicht für Analytics verwendet werden.

---

# 2. Grundarchitektur

Implementiere einen **modularen Monolithen**, keine Microservice-Landschaft.

Zielarchitektur:

                         SideBySide Next

                 ┌────────────┴────────────┐
                 │                         │
             Android App                Web App
           Kotlin / Compose          React / TypeScript
                 │                         │
                 └──────── HTTPS ──────────┘
                            │
                      REST API v1
                            │
                         FastAPI
                            │
                    Application Core
                            │
          ┌─────────────────┼──────────────────┐
          │                 │                  │
     PostgreSQL          MediaStore          Worker
                            │
                   ┌────────┴────────┐
                   │                 │
               Filesystem            S3
              Self-Hosted           Cloud

Keine Microservices, solange keine konkrete technische Notwendigkeit dafür besteht.

---

# 3. Verbindlicher Technologiestack

Backend:
- Python
- FastAPI
- SQLAlchemy 2
- Alembic
- PostgreSQL

API:
- REST
- JSON
- Versionierung unter `/api/v1/...`
- OpenAPI als verbindlicher Vertrag

Web:
- React
- TypeScript
- Vite
- React Router
- TanStack Query
- eigenes neues Designsystem

Android:
- Kotlin
- Jetpack Compose
- Material 3
- OkHttp/Retrofit oder vergleichbare saubere HTTP-Schicht
- Room für lokalen Read-Cache
- WorkManager
- Android Keystore / sichere Credential-Speicherung

Infrastructure:
- Docker
- Docker Compose für Self-Hosted
- stateless API/Web für Cloud
- PostgreSQL auch Self-Hosted
- KEIN SQLite-Support erforderlich
- KEIN Redis als Pflicht
- KEIN Celery als Pflicht

Background Jobs:
- PostgreSQL-basierte Job Queue
- Worker
- `FOR UPDATE SKIP LOCKED` oder vergleichbares robustes Verfahren

---

# 4. Technische Konventionen

## IDs

Persistente Domain-Entities verwenden UUIDv7, sofern die eingesetzten Libraries dies sauber unterstützen.

Keine hochzählbaren öffentlichen IDs.

## Zeit

Technische Zeitpunkte:
- UTC
- PostgreSQL `TIMESTAMPTZ`

Reine fachliche Tage:
- PostgreSQL `DATE`

Beispiele:

created_at  = Timestamp
updated_at  = Timestamp
happened_on = Date
birthday    = Date

## JSON

Externe API:
- camelCase

Interner Python-Code:
- snake_case

## Optimistic Concurrency

Veränderbare Domain-Objekte erhalten eine Versionsinformation.

Updates sollen später Konflikte erkennen können, z. B. über:

If-Match / Version

Konflikt:
HTTP 409

Das dient auch als Vorbereitung auf späteren Offline-Sync.

---

# 5. Einheitliches API-Fehlerformat

Verwende ein einheitliches Problem-Details-artiges Schema.

Beispiel:

{
  "type": "validation_error",
  "title": "Invalid request",
  "status": 400,
  "detail": "The title must not be empty.",
  "code": "MEMORY_TITLE_REQUIRED"
}

HTTP-Konvention:

Create       201
Get          200
Update       200
Delete       204
Validation   400/422
Unauthenticated 401
Forbidden    403
Not Found    404
Conflict     409
Rate Limit   429

Bei privacy-relevanten Ressourcen soll häufig bewusst `404` statt `403` verwendet werden, damit die Existenz fremder/private Ressourcen nicht geleakt wird.

---

# 6. Multi-Tenancy – zentrale Sicherheitsinvariante

Das zentrale Mandantenobjekt heißt:

Space

Ein Space repräsentiert den privaten gemeinsamen Raum eines Paares.

Jeder gemeinsame Datensatz muss genau einem `space_id` zugeordnet sein.

Grundmodell:

Account A ──┐
            ├── Membership ── Space
Account B ──┘

Ein normaler Paar-Space hat maximal zwei aktive Partner.

Ein Account darf technisch mehreren Spaces angehören, auch wenn die normale UI zunächst nur einen aktiven Paar-Space in den Vordergrund stellt.

Jeder Zugriff auf Space-Daten benötigt:

1. authentifizierten Account
2. aktive Membership
3. Prüfung, dass die Ressource tatsächlich diesem Space gehört
4. ggf. zusätzliche Resource-/Owner-Berechtigung

Es darf KEINEN Datenzugriff nur anhand einer Resource-ID ohne Tenant-Prüfung geben.

Beispiel:

GET /api/v1/spaces/{spaceId}/memories/{memoryId}

muss prüfen:

- current account
- membership in spaceId
- memory.spaceId == spaceId
- resource permission

Cross-Tenant-Schutz ist Release-kritisch.

---

# 7. Privacy-Klassen

Jede Domain muss ihre Daten einer dieser Klassen zuordnen:

SPACE_SHARED
OWNER_ONLY
TEMPORARY_SHARED
EPHEMERAL_CONTEXT
SYSTEM_METADATA

Es gibt keine implizite PUBLIC-Klasse.

Private Informationen müssen serverseitig geschützt werden.

Ein Ausblenden ausschließlich im Client reicht niemals.

---

# 8. Kern-Domainmodell

Plane mindestens folgende fachliche Domains:

Identity:
- Account
- AccountEmail
- AuthIdentity
- DeviceSession

Relationship:
- Space
- Membership
- Invitation
- SpaceProfile

Profiles:
- PartnerProfile
- ProfilePreference
- RelatedPerson
- ImportantDate

Memories:
- Memory
- Attachment
- HeartMoment
- Milestone
- Comment

Planning:
- Wish
- Plan
- Place
- Chapter

Collections:
- Collection
- CollectionItem

Private:
- PrivateNote
- GiftIdea
- PrivateCollection
- PrivateCollectionItem

Engagement:
- Reminder
- ReminderSchedule
- ReminderOffset
- ReminderPreference
- Activity
- Notification
- PushDelivery
- Suggestion
- RulePreference

Platform:
- FeatureConfiguration
- Entitlement
- Job
- OutboxEvent
- AuditEvent
- IntegrationConnection

Later:
- Question
- QuestionAssignment
- QuestionAnswer
- QuestionFavorite
- DailyCheckIn
- ShoppingList
- ShoppingItem

Keine generische Universal-Tabelle wie:

items(type, content, misc, ...)

für sämtliche Domains.

Wichtige Fachbereiche bekommen eigene Modelle.

---

# 9. Accounts und Authentifizierung

Account enthält Profilidentität, aber keine vermischten Auth-Geheimnisse.

Konzeptionell:

Account
- id
- displayName
- birthday?
- profileAttachmentId?
- locale
- timezone
- createdAt
- updatedAt

Auth-Identitäten separat.

## Cloud

Vorgesehen:
- E-Mail-Verifikation
- Magic Link
- Passkey
- Recovery

Keine Passwortpflicht für Cloud.

## Self-Hosted

Zusätzlich:
- lokaler Passwortlogin
- Passkey
- OIDC

Pocket ID muss dadurch später als normaler OIDC-Provider möglich sein.

## Native Auth

Android nutzt Bearer Tokens.

Authorization: Bearer <access-token>

Kein Web-Session-Cookie als primäre Native-Authentifizierung.

DeviceSession:

- accountId
- refreshTokenHash
- deviceName
- platform
- createdAt
- lastUsedAt
- expiresAt
- revokedAt

Refresh Tokens:
- nur gehasht persistieren
- Rotation
- Replay möglichst erkennen

Access Token:
- kurzlebig, z. B. ungefähr 15 Minuten

---

# 10. Invitations

Workflow:

Account A erstellt Space
→ Invitation erzeugen
→ einmaliger Token
→ Partner öffnet Link
→ Login/Registrierung
→ Accept
→ Membership

Invitation Token:
- zufällig
- ausreichend Entropie
- nur gehasht speichern
- Ablaufdatum
- widerrufbar
- nur einmal verwendbar

Tests:
- expired
- revoked
- reused
- full space
- race condition
- invalid token

---

# 11. Partnerprofile und Preferences

Partnerprofile sind Foundation.

Zwei Dinge strikt trennen:

## SELF_PROFILE

Informationen, die ein Nutzer über sich selbst für den Partner freigibt.

Mögliche Angaben:

- Geburtstag
- Lieblingsblumen
- Lieblingsessen
- Lieblingsgetränke
- Lieblingsfarben
- Filmgenres
- Seriengenres
- Musik
- Hobbys
- Aktivitäten
- Reisevorlieben
- Restaurants
- Abneigungen
- optional weitere Eigenschaften

## PRIVATE_PARTNER_NOTE

Private Informationen, die ein Nutzer sich über seinen Partner merkt.

Beispiel:
- Geschenkidee
- private Notiz
- Überraschungsplanung

Diese dürfen niemals im sichtbaren Partnerprofil auftauchen.

## ProfilePreference

Konzeptionell:

- accountId
- spaceId
- category
- topic
- sentiment
- value
- visibility
- updatedAt

Categories mindestens:

FOOD
DRINK
FLOWERS
MOVIES
SERIES
MUSIC
HOBBIES
ACTIVITIES
TRAVEL
RESTAURANTS
COLORS
OTHER

Sentiment:

LOVE
LIKE
NEUTRAL
DISLIKE
AVOID

Beispiel:

category = DRINK
topic = favorite_drink
sentiment = LOVE
value = "Coca Cola Zero"

Die Architektur muss später Empfehlungen und Regeln auf diesen Daten ermöglichen.

---

# 12. Related Persons und Important Dates

Kinder/Familienmitglieder sind keine SideBySide-Accounts.

RelatedPerson:

- id
- spaceId
- createdBy
- displayName
- relationship
- birthday?
- birthdayYearKnown
- visibility

Relationship z. B.:

CHILD
PARENT
SIBLING
FRIEND
OTHER

Datensparsamkeit:

Standardmäßig keine Adressen, Schulen, Telefonnummern etc. für Dritte speichern.

ImportantDate:

- id
- spaceId
- relatedPersonId?
- type
- date
- repeats
- label
- visibility

Typen:

BIRTHDAY
ANNIVERSARY
CUSTOM

Damit soll später regelbasiert möglich sein:

"Lisa hat in 7 Tagen Geburtstag."

---

# 13. SpaceProfile

Enthält beziehungsbezogene Informationen.

Mindestens:

- relationshipStartedOn?
- showRelationshipDuration
- durationDisplayMode
- optional gemeinsamer Song später

Die Anzeige gemeinsamer Tage/Beziehungsdauer gehört zum MVP, ist aber optional abschaltbar.

Mögliche Darstellung:

4 Jahre, 3 Monate

oder:

1.568 gemeinsame Tage

Wenn deaktiviert, erscheint sie nicht.

---

# 14. Memories

Memory:

- id
- spaceId
- authorId
- title
- body
- happenedOn?
- createdAt
- updatedAt
- version

Funktionen:

- erstellen
- lesen
- bearbeiten
- löschen
- mehrere Bilder/Medien
- Galerie
- Autor anzeigen
- Story
- Suche
- Kommentare
- Kapitel-/Ortsverknüpfung später

Das fachliche Ereignisdatum ist getrennt vom Erstellungszeitpunkt zu speichern.

Autorschaft ist relevant.

Grundregel:
Der Autor darf persönlichen Text bearbeiten/löschen.
Partner darf gemeinsame Erinnerung lesen.

---

# 15. Heart Moments

HeartMoment:

- id
- spaceId
- authorId
- text
- emotion
- visibility
- happenedOn
- attachmentId?
- createdAt
- updatedAt
- version

Emotionen initial:

LOVED
SEEN
APPRECIATED
SUPPORTED
GRATEFUL
HAPPY

Visibility:

SHARED
PRIVATE

PRIVATE bedeutet:

Der Partner darf den Inhalt NICHT erhalten über:

- GET by ID
- Listen
- Suche
- Dashboard
- Story
- Kommentare
- Notifications
- Export des Partners
- indirekte Relation

Nur Owner.

SHARED darf in Story erscheinen und kommentiert werden.

---

# 16. Milestones

Eigenständiges Domainmodell.

Milestone:

- id
- spaceId
- authorId
- title
- body?
- happenedOn
- timestamps
- version

Nutzung:
- Story
- Kapitel
- Suche
- Jahresrückblick

Keine Modellierung als spezieller Listentyp.

---

# 17. Attachments / MediaStore

Storage muss abstrahiert sein.

Interface sinngemäß:

createUpload()
finalizeUpload()
open()
delete()
createReadUrl()

Implementierungen:

LocalMediaStore
S3MediaStore

Attachment:

- id
- spaceId
- ownerId
- mediaType
- mimeType
- size
- width?
- height?
- duration?
- originalName
- storageKey
- cryptoVersion
- encrypted
- createdAt

Storage Keys niemals direkt aus User-Dateinamen ableiten.

Beispiel:

spaces/{spaceUuid}/attachments/{attachmentUuid}/original

Upload Lifecycle:

PENDING
→ upload
→ validation
→ READY

Fehler:
FAILED

Prüfen:
- tatsächlicher MIME-Type
- Größe
- erlaubter Medientyp
- Bilddimensionen
- Space-Zuordnung

Cloud-Medien sind nicht öffentlich.

Lesen:
Authorization
→ kurzlebige signed URL oder autorisierte Streaming-Route

---

# 18. E2EE-READINESS – STUFE 1 IST PFLICHT

Es wird im ersten Release noch KEINE echte Ende-zu-Ende-Verschlüsselung implementiert.

Die Architektur muss jedoch von Tag 1 E2EE-ready sein.

Wichtig:

Stufe 1 darf NICHT als echte E2EE vermarktet werden.

Die tatsächliche E2EE wird später ein eigener Security-Milestone.

## Architekturregel

Sensible Inhalte und Metadaten logisch trennen.

Beispiel:

Memory

Metadata:
- id
- spaceId
- authorId
- happenedOn
- createdAt
- updatedAt
- cryptoVersion

ProtectedPayload:
- title
- body
- weitere sensible Felder

In Version 1 darf ProtectedPayload noch Klartext sein.

Die API und Persistenz dürfen jedoch nicht so konstruiert sein, dass ein späterer Wechsel zu:

ProtectedPayload
→ clientseitige Verschlüsselung
→ Ciphertext

eine komplette Neuarchitektur erfordert.

Attachments ebenfalls:

- cryptoVersion
- encrypted

Storage darf keinen Klartext voraussetzen.

Dashboard, Rückblicke, Notification-System und Rule Engine sollen möglichst nicht zwingend auf sensible Klartexte angewiesen sein.

Späterer E2EE-Milestone reservieren für:

- Device Keys
- Account Keys
- Space Keys
- Key Distribution
- Device Verification
- Recovery
- Key Rotation
- verschlüsselte Payloads
- verschlüsselte Attachments
- lokale Suche
- Web Crypto
- Android Crypto
- Migration bestehender Daten
- externer Security Audit

Noch NICHT implementieren.

---

# 19. Kommentare

Comment:

- id
- spaceId
- authorId
- targetType
- targetId
- body
- createdAt
- updatedAt

Zulässige Targets in Version 1 kontrolliert enumerieren.

Mindestens:
- shared Memory
- Milestone
- shared HeartMoment

Keine Kommentare auf private Inhalte.

Kommentar auf fremdem gemeinsamen Content:

→ Domain Event
→ Notification für Content-Autor
→ optional Push

---

# 20. Transactional Outbox / Domain Events

Domain Events sind Foundation.

Bei relevanten Änderungen:

DB Transaction
├── Domain Entity
└── OutboxEvent

Worker verarbeitet OutboxEvent.

Beispiele:

MEMORY_CREATED
HEART_MOMENT_CREATED
PLAN_COMPLETED
IMPORTANT_DATE_APPROACHING
PARTNER_THINKING_OF_YOU
REMINDER_DUE
PROFILE_PREFERENCE_CHANGED

Später:

SHOPPING_CONTEXT_ENTERED
NEW_RELEVANT_MOVIE
NEARBY_EVENT_FOUND
IMMICH_MEMORY_FOUND

Keine enge Kopplung zwischen Domain und Push/Integration.

---

# 21. Story

Die Story ist KEINE persistierte Story-Tabelle.

Sie ist ein Read Model aus:

- Memory
- shared HeartMoment
- Milestone

angereichert um:

- Author
- Attachment
- Chapter
- Place

API z. B.:

GET /api/v1/spaces/{spaceId}/timeline

Filter:
- type
- year
- q
- order
- cursor
- limit

Cursor-basierte Pagination.

Story:
- nach Typ filtern
- nach Jahr filtern
- suchen
- chronologisch auf/absteigend
- monatsweise Gruppierung

Private Inhalte niemals einbeziehen.

Zeitliche Sortierung primär nach happenedOn, sonst geeigneter Fallback.

---

# 22. "Weißt du noch?"

Automatischer Rückblick aus historischen gemeinsamen Inhalten.

Kein duplizierter Inhalt.

Beispiel:
- heute vor 1 Jahr
- heute vor 2 Jahren
- ähnliche historische Daten

Der Rückblick referenziert Originalcontent.

Das Feature soll E2EE-kompatibel bleiben, indem der Server möglichst nur Metadaten für die Auswahl benötigt.

---

# 23. Wishes

Wish:

- id
- spaceId
- title
- createdBy
- createdAt
- updatedAt
- version

Fachzustände:

OPEN
PLANNED
COMPLETED

Benutzerworkflow:

Wunsch
→ als Plan angehen
→ Plan
→ erlebt

Ein nicht abgeschlossener Plan kann ggf. wieder in den Wunschzustand zurückgeführt werden.

Funktionen:
- Suche
- Filter
- Sortierung
- Fortschritt
- Autor

---

# 24. Plans

Plan:

- id
- spaceId
- sourceWishId?
- title
- description?
- status
- plannedStart?
- plannedEnd?
- experiencedOn?
- placeId?
- createdBy
- createdAt
- updatedAt
- version

Status:

IDEA
PLANNED
COMPLETED

Workflow:

Wish
→ Plan
→ Completed
→ optional Chapter

Transitions explizit modellieren und testen.

---

# 25. Places

Place:

- id
- spaceId
- name
- description?
- address?
- latitude?
- longitude?
- createdBy
- timestamps
- version

Position optional.

Nutzer soll später:
- Adresse/Ort suchen
- aktuelle Position verwenden
- Kartenposition wählen
- Ort ohne Koordinaten speichern

Places können verbunden werden mit:
- Memories
- HeartMoments
- Milestones
- Plans
- Chapters

---

# 26. Content Relations

Nach außen gemeinsamer Relation Service.

In PostgreSQL nach Möglichkeit echte Foreign Keys verwenden.

Keine unkontrollierte Universalrelation mit:

targetType
targetId

ohne Referential Integrity.

Intern dürfen klare Relationstabellen existieren:

chapter_memories
chapter_heart_moments
chapter_milestones

place_memories
place_heart_moments
place_milestones
place_plans
place_chapters

---

# 27. Chapters

Chapter:

- id
- spaceId
- title
- description?
- startOn?
- endOn?
- placeId?
- createdBy
- timestamps
- version

Kapitel bündelt:
- Erinnerungen
- Herzmomente
- Meilensteine

Löschregel:

Chapter löschen
→ Beziehungen entfernen
→ Originalinhalte NICHT löschen

---

# 28. Collections

Normale frei definierbare gemeinsame Listen:

Collection:
- id
- spaceId
- title
- icon
- timestamps

CollectionItem:
- id
- collectionId
- title
- completed
- position
- createdBy
- timestamps

Anwendungsfälle:
- TrashTV
- Filme
- Restaurants
- Reiseideen
- sonstige Checklisten

Funktionen:
- create
- edit
- complete/reopen
- delete
- bulk select
- bulk delete
- reorder

Einkaufsliste ist später eine eigene Domain und NICHT einfach eine Collection.

---

# 29. Private Area

Harte Privacy-Domain.

## PrivateNote

- id
- spaceId
- ownerId
- title
- body
- pinned
- timestamps
- version

## GiftIdea

- id
- spaceId
- ownerId
- title
- description?
- recipient?
- occasion?
- targetOn?
- priceText?
- url?
- status
- pinned
- timestamps
- version

## PrivateCollection

- id
- spaceId
- ownerId
- title
- icon

PrivateCollectionItem:
- title
- completed
- position

OWNER_ONLY.

Partner darf sie niemals sehen, auch nicht:
- über ID
- Suche
- Story
- Dashboard
- direkten Link
- API-Manipulation

---

# 30. Reminders

Reminder:
- id
- spaceId
- title
- description?
- source
- createdBy

ReminderSchedule:
- reminderId
- type
- entsprechende Parameter

Schedule Types:

ONCE
ANNUAL
RELATIONSHIP_DAY_COUNT

ReminderOffset:
- reminderId
- daysBefore

Keine CSV-Strings wie `"0,1,3,7"`.

ReminderPreference:
- accountId
- reminderId
- muted

Automatisch erzeugte Reminder müssen ihre Quelle kennen und sollen nicht wie frei editierbare manuelle Reminder behandelt werden.

---

# 31. Rule & Suggestion Engine

Die Architektur muss deterministische Regeln unterstützen.

Grundmodell:

Trigger
+
Conditions
+
Action

Keine frei ausführbaren User-Skripte.

Kontrollierter Rule-Katalog.

RulePreference:

- accountId
- spaceId
- ruleKey
- enabled
- parameters

Beispiel:

birthday_reminder
enabled = true
daysBefore = [14, 7, 1]

Beispielregeln später:

IMPORTANT_DATE_APPROACHING
+ BIRTHDAY
+ 7 days
→ notification

SHOPPING_CONTEXT_ENTERED
+ partner favorite drink exists
+ locationSuggestions enabled
→ local suggestion

Keine KI notwendig.

---

# 32. Notifications

Trennen:

Activity
→ Notification
→ optional PushDelivery

Activity = Space-Ereignis

Notification = Empfängerzustand

PushDelivery = technischer Versandkanal

Funktionen:
- unread count
- als gelesen markieren
- alle gelesen
- Zielinhalt öffnen

Push-Nachrichten sollen standardmäßig keine sensiblen Texte enthalten.

Bevorzugt z. B.:

"Neue Aktivität in SideBySide"

statt eines privaten Originaltexts.

---

# 33. "Ich denke an dich"

Kleines Partner-Signal.

A sendet
→ Activity
→ Notification B
→ optional Push

Kein Freitext erforderlich.

Cooldown und Rate Limit.

Soll auch als Testfall für Event-/Notification-Pipeline dienen.

---

# 34. Dashboard

Dashboard ist ein Read Model, keine redundante Datenhaltung.

API z. B.:

GET /api/v1/spaces/{spaceId}/dashboard

Kann enthalten:

- Space Summary
- Partner
- Beziehungsdauer optional
- "Ich denke an dich"
- "Weißt du noch?"
- Demnächst
- Zuletzt bei uns
- Daily Question später
- Year Summary später

Alle Daten aus echten Domains ableiten.

---

# 35. Global Search

Version 1:
PostgreSQL Full Text Search.

Kein Elasticsearch/OpenSearch erforderlich.

Search Service abstrahieren, damit später austauschbar.

API z. B.:

GET /api/v1/spaces/{spaceId}/search?q=...

Mindestens:
- Memories
- HeartMoments
- Milestones
- Chapters
- Plans
- Places
- Collections
- später Questions
- eigene private Inhalte

Security Filter muss serverseitig stattfinden.

Private Treffer des Partners dürfen nie erzeugt und anschließend nur im Client ausgeblendet werden.

---

# 36. Export / Portability

Versioniertes eigenes SideBySide Transfer Bundle.

Beispiel:

sidebyside-export.zip
├── manifest.json
├── accounts.json
├── space.json
├── memories.json
├── heart-moments.json
├── milestones.json
├── wishes.json
├── plans.json
├── places.json
├── chapters.json
├── collections.json
├── private/
└── media/

Manifest:
- formatVersion
- exportedAt
- applicationVersion
- checksums

NICHT exportieren:
- Passwörter
- Passkeys
- Refresh Tokens
- Sessions
- Push Tokens
- Security Logs

Notifications müssen nicht Teil des portablen Nutzerdatensatzes sein.

---

# 37. Migration aus SideBySide Classic

Späterer Ablauf:

SideBySide Classic
→ neutrales Transferformat
→ normaler SideBySide-Next-Importer

KEIN direkter Import der alten Datenbank in das neue ORM.

Der neue Importer kennt nur das neutrale Datenaustauschformat.

Der Classic-Exporter wird separat und erst später behandelt.

Während der Clean-Room-Implementierung NICHT den alten Sourcecode dafür lesen.

---

# 38. Feature Flags vs Entitlements

Strikt trennen:

FeatureConfiguration
= technische/administrative Aktivierung

Entitlement
= tarifliche Berechtigung

Ein deaktiviertes Feature löscht seine Daten niemals automatisch.

Billing darf nicht tief in den Application Core eingebaut werden.

Core fragt z. B.:

entitlements.has(space, "feature_name")

aber kennt Google Play/Stripe/etc. nicht.

---

# 39. Cloud und Self-Hosted

Gleicher Application Core.

## Self-Hosted

Ziel:

docker compose up -d

Komponenten:

- sidebyside-api
- sidebyside-web
- sidebyside-worker
- postgres

Persistenz:
- PostgreSQL volume
- Media volume oder S3

Optional:
- SMTP
- OIDC
- S3

## Cloud

- stateless API
- stateless Web
- Worker
- Managed PostgreSQL
- S3-compatible Object Storage
- Secret Management
- Mail
- Push
- Billing

Provider-neutral entwickeln.

Nicht direkt Scaleway/Google/AWS in Domain-Code einbauen.

---

# 40. Provider Framework

Externe Anbieter nur über Adapter.

Definiere Interfaces für:

MapProvider
GeocodingProvider
PlacesProvider
DiscoveryProvider
RecipeProvider
EntertainmentProvider
ExternalMediaProvider
LocationHistoryProvider

IntegrationConnection:

- id
- spaceId
- accountId
- provider
- status
- sharingMode
- capabilities
- credentialReference
- lastSyncAt?
- syncCursor?
- timestamps

Credentials nicht als Klartext in normaler DB-Konfiguration speichern.

SharingMode:

PRIVATE
SPACE_SHARED

Externe Verbindungen sind nicht automatisch mit dem Partner geteilt.

---

# 41. Normalisierte externe Daten

Beispiel DiscoveryItem:

- externalId
- title
- category
- description?
- startsAt?
- endsAt?
- latitude?
- longitude?
- locationName?
- source
- sourceUrl?
- imageUrl?

SideBySide-Domains dürfen nicht überall die proprietären Datenmodelle externer APIs kennen.

---

# 42. Location & Context Framework

Vier Konzepte strikt trennen:

Place
= gemeinsam gespeicherter Ort

LocationHistory
= externer Verlauf, z. B. Dawarich

Presence
= aktueller/kurzfristiger Standort

Context
= abgeleitete Situation, z. B. "wahrscheinlich Supermarkt"

Standortfunktionen standardmäßig:

OFF

Explizites Opt-in erforderlich.

Wo möglich:
- lokale Android-Geofencing-/Context-Auswertung
- keine permanente Cloud-Standortverfolgung

Serverseitige Location:
- minimal notwendige Genauigkeit
- kurze Retention
- kein Standort in normalen Logs
- jederzeit widerrufbar

---

# 43. Partnerentfernung – später

Optionales Future Feature.

Default:
OFF

Nur bei bewusster Aktivierung.

Mögliche Anzeige:
- 18 km voneinander entfernt
- in der Nähe

Keine permanente historische Speicherung daraus.

Falls PresenceSnapshot nötig:

- accountId
- spaceId
- approximateLocation
- accuracy
- capturedAt
- expiresAt

Kurze TTL.

Dawarich bleibt getrennte Location-History-Integration.

---

# 44. Shopping Domain – für später vorbereiten

Einkaufsliste NICHT als normale Collection modellieren.

Spätere eigene Domain:

ShoppingList
ShoppingItem

ShoppingItem soll perspektivisch unterstützen:

- name
- quantity?
- unit?
- category?
- note?
- completed
- addedBy
- recipeReference?

Damit später:

Rezept
→ Zutaten auswählen
→ Einkaufsliste

möglich ist.

Noch NICHT Bestandteil des ersten Kern-MVP.

---

# 45. "Was kochen wir heute?" – später

Späteres System:

Partner Preferences
+
RecipeProvider
+
Recipe Favorites
+
ShoppingList
→ Empfehlungen

Keine harte Bindung an Chefkoch.

Vor Integration eines konkreten Anbieters kommerzielle API-/Lizenzbedingungen prüfen.

---

# 46. Veranstaltungen/Freizeit – später

Discovery:

Location
+
Radius
+
DiscoveryProvider(s)
+
Space Preferences
→ Vorschläge

Radius z. B.:
10 km
25 km
50 km
100 km

Später mögliche Faktoren:
- Datum
- Wochenende
- Preis
- Interessen
- Wetter
- Entfernung

Provider-neutral.

---

# 47. Filme/Serien – später

EntertainmentProvider.

ProfilePreference kann z. B. Filmgenres enthalten.

Später möglich:

Partner A mag Thriller
Partner B mag Thriller
+
neuer Thriller
→ relevante Suggestion

Keine KI erforderlich.

---

# 48. Immich – später

Immich wird über:

ExternalMediaProvider

angebunden.

Mögliche Funktionen:

- Fotos eines Datums finden
- Fotos eines Ortes finden
- Album durchsuchen
- Foto für Erinnerung auswählen
- Rückblick mit externen Fotos

Externe Bilder nicht automatisch kopieren.

Später bewusste Wahl zwischen:

REFERENCE
IMPORT

---

# 49. Dawarich – später

Dawarich wird:

LocationHistoryProvider

Mögliche Funktionen:
- Wo waren wir an Datum X?
- Welche gemeinsamen Orte wurden besucht?
- Orte für Erinnerungen vorschlagen

SideBySide muss vollständig ohne Dawarich funktionieren.

---

# 50. Daily Check-in – später

Optional.

Kein medizinisches Diagnosesystem.

DailyCheckIn:

- accountId
- spaceId
- localDate
- mood
- energy?
- note?
- visibility
- createdAt

Mögliche einfache Stufen:

sehr schlecht
schlecht
neutral
gut
sehr gut

Partnerdarstellung nur nach freiwilliger Freigabe.

Feature vollständig deaktivierbar.

---

# 51. Unsere Fragen – nach dem Core

Eigenständige spätere Domain:

Question
QuestionAssignment
QuestionAnswer
QuestionFavorite

Zentrale Reveal-Regel:

Beide beantworten unabhängig.

Bevor beide geantwortet haben, darf kein Partner die Antwort des anderen sehen.

Es soll vor Reveal möglichst auch nicht verraten werden, ob der Partner bereits geantwortet hat.

Funktionen später:
- tägliche Frage
- Kategorien
- Archiv
- Suche
- offen/beantwortet
- persönliche Favoriten
- Jahres-/Monatsfilter
- heutige Frage wechseln
- eigene Frage erstellen
- Frage terminieren
- Frage in Pool
- beantwortete Frage → HeartMoment

Bestehenden Fragenkatalog NICHT übernehmen.

Es wird später ein komplett neuer redaktioneller Fragenpool erstellt.

---

# 52. Unser Jahr – nach dem Core

Kein persistierter Jahresrückblick erforderlich.

YearRecapQueryService berechnet:

- Memories count
- HeartMoments
- Questions
- Milestones
- Chapters
- Places
- completed Wishes
- completed Plans
- Monatsgruppen
- Highlights
- Cover Media

Später:
- Monatsrückblicke
- PDF/Print
- Teilen

Leere Statistiken müssen nicht angezeigt werden.

---

# 53. Offline

MVP:

Offline Read Cache = JA
Offline Write = NEIN

Android darf zuletzt geladene Daten lokal anzeigen.

Ohne Verbindung beim Schreiben:
klare Meldung, dass noch nichts gespeichert wurde.

Full Offline Sync / Outbox erst später.

Die Optimistic-Concurrency-Architektur soll dies vorbereiten.

---

# 54. Öffentliche Share Links

Nicht Teil von SideBySide Next 1.0.

Keine öffentlichen Freigabelinks im MVP.

Später neu bewerten.

---

# 55. AI

Keine AI-Funktionen im MVP.

Keine:
- AI Text Enhancement
- AI Coach
- AI Image Analysis
- AI Question Generation

Später optional möglich.

Core darf nicht davon abhängen.

---

# 56. Product Analytics

Keine privaten Inhalte erfassen.

Erlaubte technische/produktbezogene Beispiele:

- appVersion
- screenOpened
- featureUsed
- crash
- accountCreated
- partnerInvited
- partnerJoined
- firstMemoryCreated
- D7 active
- D30 active
- subscriptionState

NICHT erfassen:

- Memory body
- HeartMoment text
- QuestionAnswer
- PrivateNote
- GiftIdea
- persönliche Standortbeschreibung

Keine Meta-/TikTok-SDK-Pflicht im Produkt.

---

# 57. Logging und Observability

Logs dürfen enthalten:

- requestId
- accountId
- spaceId
- route
- duration
- status
- errorCode

Nicht loggen:

- Memory.body
- HeartMoment.text
- QuestionAnswer
- PrivateNote.body
- GiftIdea-Inhalt
- sensible ProfilePreference-Werte
- präzise Location

Error Tracking ebenfalls scrubben.

---

# 58. Delete / Data Retention

Grundregel:

Beim Löschen von:
- Chapter
- Place
- Collection

werden Verknüpfungen entfernt, aber nicht automatisch fremde Originalinhalte gelöscht.

Account- und Space-Löschung müssen explizite Prozesse erhalten.

Vor Cloud-Launch müssen konkrete Retention-Fristen separat festgelegt werden.

Portabilität und vollständige Löschung müssen technisch möglich sein.

---

# 59. Security

Security ist Release Gate.

Zwingende Tests:

- Cross-Tenant / IDOR
- private resource leakage
- malformed IDs
- invitation abuse
- token replay
- refresh rotation
- revoked sessions
- rate limiting
- upload abuse
- malicious media
- XSS
- CSRF bei Browser-Flows
- SQL injection
- signed URL expiration
- backup authorization
- search privacy leaks

Tenant Isolation Test:

User A / Space A = erlaubt
User B / Space A = erlaubt
User C / Space B = niemals Zugriff
anonymous = niemals Zugriff

Private Isolation zusätzlich testen über:

- list
- search
- dashboard
- timeline
- notifications
- export
- relations
- attachments
- update/delete

---

# 60. Tests

Vier Ebenen:

1. Unit Tests
2. Integration Tests
3. API Contract Tests
4. End-to-End Tests

Zusätzlich eigene:

SECURITY & PRIVACY TEST SUITE

Ein Feature gilt nicht als fertig, solange Cross-Tenant- und ggf. Privacy-Tests fehlen.

---

# 61. Definition of Done pro Domain Feature

Ein Feature gilt erst als fertig, wenn vorhanden:

- Datenmodell
- Migration
- Domain Service
- Authorization
- API
- OpenAPI
- Validation
- Error Codes
- Unit Tests
- Integration Tests
- Cross-Tenant Tests
- Privacy Tests falls relevant
- Export-Unterstützung falls persistente Nutzerdaten
- Web UI
- Android UI
- Error Handling
- Dokumentation

Ein funktionierender Button allein bedeutet NICHT "fertig".

---

# 62. Client-Parität

Eine Kernfunktion gilt erst als produktreif, wenn Web und Android dasselbe fachliche Verhalten besitzen.

Nicht zwingend identische UI.

Aber identisch bei:

- Create
- Read
- Update
- Delete
- Authorization
- Visibility
- Validation
- Errors

---

# 63. CI/CD

Bei jedem Commit mindestens:

- formatting
- lint
- type check
- unit tests
- integration tests
- security/privacy tests
- dependency scan
- secret scan
- backend build
- web build
- Android build sobald vorhanden

Später zusätzlich:
- container scan
- SBOM
- license scan

Keine roten Tests ignorieren.

---

# 64. Dependency- und Asset-Provenienz

Alle neuen Abhängigkeiten dokumentieren:

- Name
- Version
- Quelle
- Lizenz

Alle Assets dokumentieren:

- Ursprung
- Lizenz
- Ersteller

Keine Assets ungeklärter Herkunft aufnehmen.

Branding-Assets nur verwenden, wenn sie ausdrücklich als für SideBySide Next freigegeben bereitgestellt werden.

Noch KEINE endgültige Lizenz für den eigenen neuen Sourcecode festlegen.

Keine automatische MIT-/Apache-/AGPL-LICENSE-Datei hinzufügen, solange ich das nicht ausdrücklich entscheide.

Third-Party-Lizenzpflichten selbstverständlich erfüllen.

---

# 65. PROVENANCE

Von Anfang an `PROVENANCE.md` pflegen.

Sinngemäß dokumentieren:

SideBySide Next is an independently implemented software project based on a functional product specification. No source code from SharedMoments or SideBySide Classic is to be copied into the implementation.

Dokumentieren:
- Startdatum
- Spezifikationsversion
- Dependencies
- Assets
- Contributors
- relevante Herkunft
- ggf. AI-assisted development intern

Nicht behaupten, dass diese technische Dokumentation allein eine bestimmte juristische Lizenzfolge garantiert.

---

# 66. Freemium-Architektur

Noch keine harten Produktpreise in Domain-Code einbauen.

Entitlement-System flexibel halten.

Arbeitshypothese Cloud:

Free:
- 1 Space
- Textfeatures weitgehend unbegrenzt
- begrenzter Media Storage
- begrenzte Zahl bestimmter Komfortfeatures

Premium:
- mehr Storage
- erweiterte Komfort-/Rückblickfunktionen
- Premium-Services

Persönliche Erinnerungen NICHT künstlich nach Stückzahl limitieren.

Self-Hosted:
- grundsätzlich sinnvoll nutzbar
- nicht künstlich funktionskastrieren

Spätere Supporter-Dienste können sein:
- Push Relay
- Offsite Backup
- Health Monitoring
- Restore Service
- Support
- Update Services

---

# 67. Spätere echte E2EE

Echte E2EE ist NICHT MVP.

Aber die Architektur muss sie vorbereiten.

Später möglicher Marketing-Claim erst nach tatsächlicher Umsetzung und Audit:

"Eure Erinnerungen sind Ende-zu-Ende verschlüsselt – selbst SideBySide kann sie nicht lesen."

Diesen Claim VORHER niemals verwenden.

---

# 68. Entwicklungs-Milestones

## M0 – Clean Foundation

- isoliertes neues Projekt
- Repository-Struktur
- Backend-Grundgerüst
- PostgreSQL
- Alembic
- API-Konventionen
- UUIDv7
- Error Model
- Domain Event Foundation
- Transactional Outbox
- Job Foundation
- Provider Interfaces
- E2EE-ready Payload Boundary
- CI
- Provenance
- Dependency Documentation

Ergebnis:
neue unabhängige technische Plattform läuft.

## M1 – Identity & Relationship

- Accounts
- E-Mail/Auth Identities
- Sessions
- Passkey-fähige Auth-Architektur
- Self-Hosted OIDC-ready
- Spaces
- Memberships
- Invitations
- Tenant Authorization
- Private Authorization
- SpaceProfile
- PartnerProfile
- ProfilePreferences
- RelatedPersons
- ImportantDates

Ergebnis:
zwei Partner können sicher einen Space benutzen.

## M2 – Memory Core

- MediaStore
- Attachments
- Memories
- HeartMoments
- Milestones
- Comments
- Story
- "Weißt du noch?"
- Security Tests

Ergebnis:
SideBySide ist bereits als echte Paar-/Erinnerungs-App nutzbar.

## M3 – Shared Life

- Wishes
- Plans
- Places
- Content Relations
- Chapters
- Collections
- PrivateNotes
- GiftIdeas
- PrivateCollections

## M4 – Engagement

- Reminders
- Reminder Scheduling
- Important Date Notifications
- Activity
- Notifications
- Push abstraction
- "Ich denke an dich"
- Dashboard
- Search
- Rule/Suggestion Engine

Nach M4 ist der funktionale Core weitgehend komplett.

## M5 – Clients & Portability

- versionierter Export
- normaler Import
- vorbereiteter Classic-Migrationspfad
- React Web Client vollständig
- Android Native Client vollständig
- Read Cache
- Client-Parität
- responsive UX
- Accessibility Basics

## M6 – Rich Relationship Features

- Unsere Fragen
- komplett neuer Fragenpool
- Year Recap
- Month Recap
- Daily Check-in
- PDF/Print Year Recap

## M7 – Integrations

- Discovery Provider / Veranstaltungen
- Shopping Domain
- Recipe Provider
- "Was kochen wir heute?"
- Entertainment Provider
- Film-/Serien-Releases
- Immich Provider
- Dawarich Provider
- Maps / Places / Geocoding Provider

## M8 – Contextual Features

- opt-in Location Context
- Geofencing
- Shopping Context
- kontextbezogene Suggestions
- optionale Partnerentfernung
- Ephemeral Presence

## M9 – Productization

- Self-Hosted Compose
- Backup/Restore
- Cloud Deployment
- Managed Storage
- Managed DB
- Entitlements
- Billing Adapter
- Datenschutzfunktionen
- Security Hardening
- Penetration Tests
- Observability
- Release Pipeline
- Store Preparation

## MX – Future E2EE

Erst später:
echte Ende-zu-Ende-Verschlüsselung.

---

# 69. Was NICHT zum ersten MVP gehört

Nicht in den ersten Kern ziehen:

- echte E2EE
- Full Offline Write Sync
- AI
- öffentliche Share Links
- komplexe Filmempfehlungen
- Event Discovery
- Rezeptintegration
- Shopping Automation
- Immich
- Dawarich
- Google Maps Integration
- Geofencing
- Partner Distance
- Daily Check-in
- Our Questions
- Year Recap

Die Architektur muss Erweiterungen ermöglichen, aber der Core soll zuerst sauber und sicher werden.

---

# 70. Sofortiger Start – PHASE D

Du darfst jetzt mit der **Clean-Room-Implementierung** beginnen.

Arbeite NICHT am alten SideBySide-/SharedMoments-Repository.

## D0 – Isolation prüfen

Als allererstes:

1. `pwd`
2. prüfen, ob aktueller Ordner SideBySide Classic / SharedMoments ist
3. falls ja: KEINE Änderung dort
4. neuen isolierten Workspace verwenden, bevorzugt:

   `~/Projekte/SideBySide-Next`

5. sicherstellen, dass keine Dateien aus Classic kopiert werden

## D1 – neues Projekt initialisieren

Neue Struktur:

sidebyside-next/
├── backend/
├── web/
├── android/
├── deploy/
├── docs/
├── specification/
└── tools/

Git initialisieren, falls dort noch kein neues Repo existiert.

Keinen Remote anlegen und nicht pushen, solange ich es nicht ausdrücklich sage.

Lokale, logisch kleine Commits sind nach grünen Tests erlaubt.

## D2 – Dokumentation zuerst

Erstelle mindestens:

- README.md
- PROVENANCE.md
- docs/ARCHITECTURE.md
- docs/SECURITY.md
- docs/PRIVACY-MODEL.md
- docs/DEPENDENCIES.md
- specification/PRODUCT-SPEC.md

Diese Dateien basieren ausschließlich auf diesem Master Prompt.

Nicht den alten Code konsultieren.

## D3 – M0 implementieren

Danach M0 beginnen:

- FastAPI skeleton
- SQLAlchemy 2
- PostgreSQL connection
- Alembic
- `/health`
- Problem Details error handling
- UUIDv7 support
- UTC conventions
- base entity conventions
- transaction handling
- OutboxEvent
- Job foundation
- domain-event contracts
- MediaStore interfaces
- provider interfaces
- E2EE-ready protected-payload abstraction
- initial CI
- tests

## D4 – PostgreSQL lokal

Erstelle für Development eine Docker-Compose-Konfiguration mit PostgreSQL.

Kein SQLite-Fallback.

## D5 – erste Security Foundation

Implementiere vor echten Content-Domains:

- Account skeleton
- Space
- Membership
- Tenant Context
- Membership Guard
- Security tests

Noch bevor Memory etc. implementiert werden.

## D6 – Arbeitsweise

Arbeite inkrementell.

Nach jedem Block:

1. Tests ausführen
2. Lint/Typecheck ausführen
3. `git diff --check`
4. `git status`
5. kurz zusammenfassen:
   - was geändert wurde
   - warum
   - welche Tests liefen
   - Ergebnis
   - nächster Schritt

Bei Fehlern:
- Ursache untersuchen
- nicht einfach Tests deaktivieren
- nicht Sicherheitsprüfungen umgehen

## D7 – keine unnötigen Rückfragen

Wenn eine Entscheidung durch diese Spezifikation eindeutig festgelegt ist, entscheide nicht erneut und frage nicht nach.

Frage mich nur, wenn:
- eine echte Produktentscheidung fehlt
- eine sicherheitsrelevante Entscheidung nicht aus der Spezifikation hervorgeht
- eine Handlung externe Credentials benötigt
- ein Remote/GitHub-Repo erstellt werden soll
- Kosten verursacht werden könnten
- eine endgültige Sourcecode-Lizenz gewählt werden müsste
- ein alter Classic-Sourcezugriff vermeintlich nötig wäre

Falls du glaubst, Classic-Sourcecode zu benötigen:
STOP.
Nicht öffnen.
Erkläre stattdessen, welche funktionale Information in der Spezifikation fehlt.

---

# 71. Priorität

Die Priorität lautet:

1. Clean-Room-Trennung
2. Sicherheit / Tenant Isolation
3. sauberes Domainmodell
4. stabile API
5. Tests
6. Portabilität
7. Web/Android UX
8. Erweiterungen
9. Cloud-Monetarisierung

Keine schnelle Abkürzung darf Tenant Isolation oder Privacy schwächen.

---

# 72. Erfolgsdefinition

SideBySide Next soll am Ende:

- vollständig unabhängig implementiert sein
- keine SharedMoments-/Classic-Codebasis benötigen
- Cloud-fähig sein
- Self-Hosted-fähig sein
- Multi-Tenant sicher sein
- Android nativ unterstützen
- Web unterstützen
- providerneutral sein
- später E2EE nachrüstbar sein
- Erweiterungen ohne grundlegenden Umbau erlauben
- saubere Provenienz besitzen

Beginne jetzt mit D0 und D1.

Zeige mir zunächst:
1. welche isolierte Working Directory du verwendest,
2. die geplante initiale Verzeichnisstruktur,
3. dass das Classic-Repository nicht verändert wird,

und fahre anschließend direkt mit M0 fort, solange kein echter Blocker auftritt.

