# Android

Der native Kotlin-/Jetpack-Compose-Client wird langfristig in M5 vollständig
produktisiert. Für **M2-S8 / G2** existiert hier bewusst vorher nur ein dünner
vertikaler Referenzflow. Er beweist denselben Memory-/Bild-/Story-Vertrag wie
der Web-Slice, ohne Navigation, Offline-Sync oder Client-Parität vorzuziehen.

Android spricht ausschließlich über die versionierte REST-/OpenAPI-
Schnittstelle mit dem gemeinsamen Application Core und erhält keine eigene
Fach- oder Privacy-Logik.

## Generierte API-Modelle

`api/generated/` enthält die Kotlin-Datenklassen aus `backend/openapi.json`
und wird **nicht von Hand bearbeitet**. Erzeugen mit
`tools/openapi/generate.sh`; CI prüft den eingecheckten Stand gegen den
Vertrag.

Der S8-Client bindet diese Modelle direkt als zusätzliche Kotlin-Source-Root
ein. Insbesondere wird die mit #119 reparierte, generatorbasierte
`StoryItem`-Union real deserialisiert. Es gibt keine zweite handgeschriebene
DTO-Schicht.

## M2-S8 Referenzflow

Der Slice führt genau einen kritischen Flow aus:

1. Passwort-Anmeldung gegen `/api/v1/auth/sign-in`,
2. Bearer-Token ausschließlich im flüchtigen ViewModel-State,
3. Memory gegen den veröffentlichten Vertrag anlegen,
4. Bild über Android Photo Picker auswählen,
5. `UploadDescriptor` für `STREAM` oder `SIGNED_UPLOAD` ausführen,
6. Upload finalisieren und bis `READY` prüfen,
7. Attachment mit `If-Match` an die Memory binden,
8. gemeinsame `/timeline` laden und den generierten `StoryItem` behandeln,
9. autorisierten `ReadDescriptor` ausführen und das Bild minimal anzeigen.

Bei `STREAM` geht der Bearer-Token an die SideBySide-API. Bei
`SIGNED_UPLOAD`/`SIGNED_URL` wird er bewusst **nicht** an den Storage-Endpunkt
weitergereicht.

## Betreiberkonfiguration

Normale Nutzer geben keine technischen URLs oder IDs ein. Für den Referenzflow
werden die Werte beim Build als Gradle Properties gesetzt:

```bash
gradle -PsbsApiBaseUrl=https://sidebyside.example \
  -PsbsSpaceId=00000000-0000-0000-0000-000000000000 \
  :app:assembleDebug
```

Ohne gültige Konfiguration zeigt die Oberfläche nur einen verständlichen
Betreiberhinweis und startet keine API-Anfrage.

## Lokal prüfen

Der CI-Stand verwendet JDK 17, Gradle 9.5.0, AGP 9.3.0 und compileSdk 37.
Mit entsprechend installiertem Android SDK:

```bash
gradle --no-daemon :app:testDebugUnitTest
gradle --no-daemon :app:lintDebug
gradle --no-daemon :app:assembleDebug
```

Die fokussierten Tests decken Flow-Orchestrierung, Bearer-Trennung bei
Stream-/Signed-Deskriptoren, echte `StoryItem`-Deserialisierung und Compose-
Semantics bei großer Systemschrift ab.

## Bewusste S8-Grenzen

- kein persistenter Token-, Read- oder Offline-Cache,
- kein Room/Paging und kein WorkManager,
- keine vollständige Navigation oder Deep Links,
- kein Offline Write Sync,
- kein Export/Import und keine globale Suche,
- keine Wishes/Plans/Places/Private Area oder M3+-Funktionen,
- kein Video; #88 bleibt Future-Backlog.

Diese Punkte gehören in spätere, ausdrücklich freigegebene Milestones und
werden durch den technischen G2-Nachweis nicht stillschweigend entschieden.
