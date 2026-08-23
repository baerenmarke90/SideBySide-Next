# SideBySide Next — Produktspezifikation

Verbindliche fachliche Vorgabe. Diese Datei ist die Implementierungsquelle;
eine Vorgängeranwendung wird dafür nicht herangezogen.

| | |
|---|---|
| Version | 1.0 |
| Stand | 2026-08-23 |

## 1. Produkt

Ein privater digitaler Begleiter für das gemeinsame Leben eines Paares, in
zwei Betriebsformen: betriebener Cloud-Dienst und Self-Hosted-Installation.

Positionierung: *Die Paar-App, die euch gehört.*

Verwaltet werden — soweit die Nutzer die Funktionen aktivieren —
Erinnerungen, emotionale Momente, Meilensteine, gemeinsame Geschichte,
Wünsche, Pläne, Orte, Listen, private Inhalte, Termine,
Partnerpräferenzen, Geburtstage und wichtige Personen, Paarfragen,
gemeinsames Befinden, Einkaufslisten, Rezeptideen, Freizeitvorschläge,
externe Fotos und optionale Standortinformationen.

## 2. Mandantenmodell

```
Account A ──┐
            ├── Membership ── Space
Account B ──┘
```

Ein **Space** ist der private gemeinsame Raum eines Paares; ein normaler
Paar-Space hat höchstens zwei aktive Partner. Ein Account darf technisch
mehreren Spaces angehören.

Jeder gemeinsame Datensatz gehört genau einem Space. Zugriffsregeln siehe
[docs/SECURITY.md](../docs/SECURITY.md).

## 3. Domänen

### Identity
`Account`, `AccountEmail`, `AuthIdentity`, `DeviceSession`

Account trägt Profilidentität, keine vermischten Auth-Geheimnisse.
Auth-Identitäten liegen getrennt.

### Relationship
`Space`, `Membership`, `Invitation`, `SpaceProfile`

`SpaceProfile` hält `relationship_started_on`,
`show_relationship_duration`, `duration_display_mode`. Die Anzeige der
Beziehungsdauer gehört zum MVP und ist abschaltbar.

### Profiles
`PartnerProfile`, `ProfilePreference`, `RelatedPerson`, `ImportantDate`

`ProfilePreference`: `account_id`, `space_id`, `category`, `topic`,
`sentiment`, `value`, `visibility`.

Kategorien: FOOD, DRINK, FLOWERS, MOVIES, SERIES, MUSIC, HOBBIES,
ACTIVITIES, TRAVEL, RESTAURANTS, COLORS, OTHER.
Sentiment: LOVE, LIKE, NEUTRAL, DISLIKE, AVOID.

`RelatedPerson`: Anzeigename, Beziehung (CHILD, PARENT, SIBLING, FRIEND,
OTHER), optional Geburtstag mit `birthday_year_known`.
`ImportantDate`: Typ BIRTHDAY, ANNIVERSARY, CUSTOM, mit Wiederholung.

### Memories
`Memory`, `Attachment`, `HeartMoment`, `Milestone`, `Comment`

`Memory`: Titel, Text, `happened_on` getrennt von `created_at`, Autor,
mehrere Medien, Kommentare.

`HeartMoment`: Text, Emotion (LOVED, SEEN, APPRECIATED, SUPPORTED,
GRATEFUL, HAPPY), Sichtbarkeit SHARED oder PRIVATE. PRIVATE ist
`OWNER_ONLY` ohne Ausnahme.

`Milestone` ist ein eigenes Modell, kein Listentyp.

`Comment`: Ziele in Version 1 kontrolliert aufgezählt — geteilte Memory,
Milestone, geteilter HeartMoment. Keine Kommentare auf privaten Inhalten.

### Planning
`Wish` (OPEN, PLANNED, COMPLETED), `Plan` (IDEA, PLANNED, COMPLETED),
`Place`, `Chapter`

Ablauf: Wunsch → Plan → erlebt → optional Kapitel. Ein nicht
abgeschlossener Plan kann in den Wunschzustand zurück.

`Place` mit optionalen Koordinaten; ein Ort ohne Koordinaten ist gültig.

`Chapter` bündelt Erinnerungen, Herzmomente, Meilensteine. Löschen entfernt
Verknüpfungen, nicht die Originale.

### Collections
`Collection`, `CollectionItem` — frei definierbare gemeinsame Listen mit
Abhaken, Sortierung, Mehrfachauswahl. Die Einkaufsliste ist später eine
eigene Domäne, keine Collection.

### Private
`PrivateNote`, `GiftIdea`, `PrivateCollection`, `PrivateCollectionItem` —
sämtlich `OWNER_ONLY`.

### Engagement
`Reminder`, `ReminderSchedule` (ONCE, ANNUAL, RELATIONSHIP_DAY_COUNT),
`ReminderOffset` (eigene Zeilen, keine CSV-Strings),
`ReminderPreference`, `Activity`, `Notification`, `PushDelivery`,
`Suggestion`, `RulePreference`

Automatisch erzeugte Reminder kennen ihre Quelle und sind nicht wie
manuelle frei editierbar.

### Platform
`FeatureConfiguration` (technische Aktivierung) und `Entitlement`
(tarifliche Berechtigung) sind strikt getrennt. `Job`, `OutboxEvent`,
`AuditEvent`, `IntegrationConnection`.

### Später
`Question`, `QuestionAssignment`, `QuestionAnswer`, `QuestionFavorite`,
`DailyCheckIn`, `ShoppingList`, `ShoppingItem`

Reveal-Regel der Fragen: beide antworten unabhängig; vor dem Reveal sieht
niemand die Antwort des anderen, und möglichst auch nicht, ob schon
geantwortet wurde. Der Fragenkatalog wird redaktionell neu erstellt.

## 4. Abgeleitete Sichten

Nicht persistiert, sondern berechnet:

- **Story** aus Memory, geteiltem HeartMoment und Milestone, angereichert
  um Autor, Medien, Kapitel, Ort. Cursor-Pagination, Filter nach Typ und
  Jahr, Suche, Sortierung, Monatsgruppen. Private Inhalte niemals.
- **"Weißt du noch?"** referenziert Originalinhalte, dupliziert nichts.
- **Dashboard** — Space-Übersicht, Partner, optionale Beziehungsdauer,
  "Ich denke an dich", Rückblick, Demnächst, Zuletzt.
- **Jahresrückblick** — Zahlen, Monatsgruppen, Highlights. Leere
  Statistiken müssen nicht erscheinen.

## 5. Suche

PostgreSQL Full Text Search in Version 1, hinter einer Abstraktion.
Sicherheitsfilter serverseitig in der Abfrage.

Umfasst Memories, HeartMoments, Milestones, Chapters, Plans, Places,
Collections, eigene private Inhalte, später Questions.

## 6. Export

Versioniertes eigenes Transfer Bundle mit `manifest.json`
(`formatVersion`, `exportedAt`, `applicationVersion`, `checksums`),
Domänen-Dateien und Medien.

Nicht enthalten: Passwörter, Passkeys, Refresh Tokens, Sitzungen, Push
Tokens, Sicherheitsprotokolle.

Migration aus der Vorgängeranwendung läuft später über dasselbe neutrale
Format — kein Direktimport einer Fremddatenbank in dieses ORM.

## 7. Regeln und Vorschläge

Deterministisch: Trigger + Bedingungen + Aktion. Kontrollierter Katalog,
keine frei ausführbaren Nutzerskripte, keine KI erforderlich.

`RulePreference` je Account und Space mit `rule_key`, `enabled`,
`parameters`.

## 8. Clients

Web (React/TypeScript) und Android (Kotlin/Compose). Eine Kernfunktion ist
produktreif, wenn beide dasselbe fachliche Verhalten zeigen — bei Create,
Read, Update, Delete, Autorisierung, Sichtbarkeit, Validierung und
Fehlern. Die Oberfläche darf sich unterscheiden.

Android: Offline-Lesecache ja, Offline-Schreiben nein. Ohne Verbindung
folgt eine klare Meldung, dass nichts gespeichert wurde.

## 9. Meilensteine

| | Inhalt |
|---|---|
| M0 | Technische Plattform, Outbox, Jobs, Fehlerformat, CI, Provenance |
| M1 | Identity, Spaces, Memberships, Invitations, Profile, Präferenzen |
| M2 | MediaStore, Attachments, Memories, HeartMoments, Milestones, Kommentare, Story |
| M3 | Wishes, Plans, Places, Relations, Chapters, Collections, private Ablage |
| M4 | Reminders, Activity, Notifications, "Ich denke an dich", Dashboard, Suche, Regeln |
| M5 | Export, Import, Web-Client, Android-Client, Read Cache, Parität |
| M6 | Unsere Fragen, neuer Fragenpool, Jahres- und Monatsrückblick, Check-in |
| M7 | Integrationen: Discovery, Shopping, Rezepte, Unterhaltung, externe Medien, Standortverlauf, Karten |
| M8 | Opt-in-Standortkontext, Geofencing, kontextbezogene Vorschläge, Presence |
| M9 | Self-Hosted-Compose, Backup, Cloud-Deployment, Entitlements, Billing-Adapter, Härtung, Release |
| MX | Echte Ende-zu-Ende-Verschlüsselung |

## 10. Nicht im ersten MVP

Echte E2EE, Offline-Schreib-Sync, KI, öffentliche Freigabelinks,
Filmempfehlungen, Event Discovery, Rezeptintegration, Shopping-Automation,
externe Medien- und Standortintegrationen, Karten-Integration, Geofencing,
Partnerentfernung, Daily Check-in, Unsere Fragen, Jahresrückblick.

Der Aufbau muss die Erweiterung tragen; der Core wird zuerst sauber und
sicher.

## 11. Definition of Done je Domänen-Feature

Datenmodell, Migration, Domain Service, Autorisierung, API, OpenAPI,
Validierung, Fehlercodes, Unit-Tests, Integrationstests,
Cross-Tenant-Tests, Privacy-Tests sofern einschlägig,
Export-Unterstützung bei persistenten Nutzerdaten, Web-UI, Android-UI,
Fehlerbehandlung, Dokumentation.

Ein funktionierender Knopf allein ist nicht fertig.

## 12. Priorität bei Zielkonflikten

1. Clean-Room-Trennung
2. Sicherheit und Tenant Isolation
3. sauberes Domainmodell
4. stabile API
5. Tests
6. Portabilität
7. Web- und Android-UX
8. Erweiterungen
9. Monetarisierung

Keine Abkürzung darf Tenant Isolation oder Privatsphäre schwächen.
