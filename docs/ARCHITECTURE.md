# Architektur

## Form

Ein **modularer Monolith**. Keine Microservices, solange keine konkrete
technische Notwendigkeit besteht.

```
        Android (Kotlin/Compose)     Web (React/TypeScript)
                    │                        │
                    └────────  HTTPS  ───────┘
                                 │
                           REST API v1
                                 │
                             FastAPI
                                 │
                        Application Core
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                      │
      PostgreSQL             MediaStore               Worker
                                 │
                        ┌────────┴────────┐
                    Filesystem            S3
                   (Self-Hosted)        (Cloud)
```

Cloud und Self-Hosted teilen denselben Core. Unterschiede liegen in den
Adaptern — Storage, Mail, Auth, Push —, nicht in der Fachlogik.

## Schichten

**API** (`sidebyside.api`) — HTTP, Serialisierung, Fehlerabbildung. Enthält
keine Fachregeln.

**Domain** (`sidebyside.domain`) — Fachobjekte, Regeln, Ereignisse. Kennt
weder HTTP noch einen konkreten Anbieter.

**Infrastructure** (`sidebyside.db`, `.media`, `.providers`) — Persistenz
und externe Systeme hinter Schnittstellen.

Die Abhängigkeit zeigt nach innen: API kennt Domain, Domain kennt
Infrastructure nur über Schnittstellen.

## Konventionen

### Identifikatoren

Persistente Domain-Objekte verwenden **UUIDv7**. Keine hochzählbaren
öffentlichen IDs — eine fortlaufende Nummer verrät Bestandsgrößen und lädt
zum Durchprobieren ein. UUIDv7 ist zeitlich sortierbar und damit als
Primärschlüssel indexfreundlich.

### Zeit

| Bedeutung | Typ |
|---|---|
| Technischer Zeitpunkt (`created_at`, `updated_at`) | `TIMESTAMPTZ`, immer UTC |
| Fachlicher Tag (`happened_on`, `birthday`) | `DATE` |

Ein fachlicher Tag ist kein Zeitpunkt. Ein Geburtstag hat keine Zeitzone,
und ihn als Zeitstempel zu speichern verschiebt ihn irgendwann um einen Tag.

### JSON

Nach außen **camelCase**, intern **snake_case**. Die Umsetzung geschieht an
der Serialisierungsgrenze, nicht durch Umbenennen im Domain-Code.

### Optimistic Concurrency

Veränderbare Domain-Objekte tragen eine `version`. Updates prüfen sie und
antworten bei Abweichung mit **409**. Das ist zugleich die Vorbereitung auf
späteren Offline-Sync: ohne Versionsbegriff lässt sich ein Konflikt nicht
von einem Überschreiben unterscheiden.

## Transactional Outbox

Fachliche Änderung und Ereignis werden in **einer** Transaktion
geschrieben:

```
BEGIN
  INSERT/UPDATE  Domain-Objekt
  INSERT         outbox_event
COMMIT
```

Ein Worker liest die Outbox und stellt zu. Damit kann kein Ereignis
verlorengehen, weil die Zustellung nach dem Commit fehlschlug, und keine
Benachrichtigung entstehen zu einer Änderung, die zurückgerollt wurde.

Domain und Zustellkanal bleiben entkoppelt: die Domain kennt weder Push
noch Mail noch eine Integration.

## Job Queue

PostgreSQL-basiert, ohne Redis- oder Celery-Pflicht. Nebenläufige Worker
holen Aufgaben über `FOR UPDATE SKIP LOCKED`, sodass zwei Worker nie
dieselbe Aufgabe greifen.

Jobs tragen `attempts`, `max_attempts`, `run_after` und `locked_until`.
Eine hängengebliebene Sperre läuft ab und wird erneut vergeben.

## Read Models

Story, Dashboard, Jahresrückblick und "Weißt du noch?" sind **abgeleitet**,
nicht gespeichert. Es gibt keine Story-Tabelle. Doppelte Datenhaltung
driftet auseinander, und ein zweiter Ort für denselben Inhalt ist ein
zweiter Ort, an dem eine Sichtbarkeitsregel vergessen werden kann.

## E2EE-Bereitschaft

Im ersten Release gibt es **keine** echte Ende-zu-Ende-Verschlüsselung.
Der Aufbau muss sie später aufnehmen können, ohne neu gebaut zu werden.

Deshalb trennt jedes sensible Fachobjekt zwei Bereiche:

| Metadata | ProtectedPayload |
|---|---|
| `id`, `space_id`, `author_id` | `title`, `body` |
| `happened_on`, `created_at` | weitere sensible Felder |
| `crypto_version` | |

In Version 1 ist der Payload Klartext (`crypto_version = 0`). Die Grenze
existiert aber schon in API und Persistenz, sodass ein späterer Wechsel auf
clientseitig erzeugten Ciphertext eine Formatänderung ist und kein Umbau.

Die Persistenz verwendet dafür `ProtectedPayloadJSON` mit einer konkreten
`ProtectedPayload`-Klasse. Ein rohes Dictionary oder die Payload einer
anderen Domäne wird bereits vor dem SQL-Bind abgewiesen. Das ist eine
Typ- und Architekturgrenze, **keine Verschlüsselung**: Bei
`crypto_version = 0` kann der Server den Inhalt weiterhin lesen.

Outbox-Ereignisse bilden die Gegenrichtung ab. Ihre Nutzlast ist kein
beliebiges JSON-Dictionary, sondern `PublicEventPayload` mit einer zentralen
Allowlist unkritischer Metadaten. Der JSONB-Persistenztyp weist auch bei
direkter ORM-Nutzung rohe Dictionaries ab. Sensibler Text bleibt damit im
ProtectedPayload und wird nicht dauerhaft in Outbox, Worker oder Logs kopiert.

Ableitende Funktionen — Dashboard, Rückblicke, Regeln, Benachrichtigungen —
sollen möglichst mit Metadaten auskommen. Was den Klartext braucht, wird
später nicht mehr funktionieren.

Siehe [SECURITY.md](SECURITY.md).

## Provider-Rahmen

Externe Anbieter ausschließlich über Adapter: Karten, Geocoding, Orte,
Discovery, Rezepte, Unterhaltung, externe Medien, Standortverlauf.

Der Domain-Code kennt keinen konkreten Anbieter. Externe Daten werden vor
dem Eintritt in die Domain in eigene, normalisierte Formen überführt.

Die Verträge heißen `MapProvider`, `GeocodingProvider`, `PlacesProvider`,
`DiscoveryProvider`, `RecipeProvider`, `EntertainmentProvider`,
`ExternalMediaProvider` und `LocationHistoryProvider`. Sie geben nur eigene,
immutable Modelle wie `GeoPoint`, `MapRoute`, `PlaceCandidate`, `RecipeItem`
oder `EntertainmentItem` zurück; DTOs einzelner Anbieter enden im Adapter.

Eine `ProviderRegistry` verbindet Interface und frei konfigurierbaren Namen
erst an der Composition Root. Damit kann Cloud oder Self-Hosted einen Adapter
wechseln, ohne Domain-Code zu ändern. M0 implementiert ausdrücklich keinen
kommerziellen Anbieter und keine darauf aufbauende M6-/M7-Funktion.

## Was bewusst fehlt

- **Keine generische Universaltabelle** (`items(type, content, ...)`) für
  alle Domänen. Fachbereiche bekommen eigene Modelle.
- **Kein SQLite.** Ein zweiter Dialekt im Test prüft nicht, was in
  Produktion läuft.
- **Keine unkontrollierte Universalrelation** ohne referenzielle
  Integrität. Beziehungen sind echte Fremdschlüsseltabellen.
