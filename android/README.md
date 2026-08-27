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

Für den S8-Build wird daraus unverändert eine temporäre Compile-Source-Root
unter `app/build/generated/` vorbereitet. Die zwei generator-owned Passkey-
Request-Modelle mit `Map<String, Any>` werden in diesem fachfremden Slice aus
der Compile-Kopie ausgelassen, weil kotlinx.serialization dafür keinen
konkreten `Any`-Serializer erzeugen kann. Der Generatorbefund ist separat in
#138 dokumentiert; die Quelldateien selbst bleiben unverändert. Alle für S8
benötigten DTOs und insbesondere die mit #119 reparierte `StoryItem`-Union
kommen weiterhin direkt aus dem generierten Vertrag. Es gibt keine zweite
handgeschriebene DTO-Schicht.

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
weitergereicht. Das App-Manifest erlaubt keine Cleartext-Verbindungen; ein
realer Remote-Betrieb verwendet daher HTTPS.

## Betreiberkonfiguration

Normale Nutzer geben keine technischen URLs oder IDs ein. Für den Referenzflow
werden die Werte beim Build als Gradle Properties gesetzt:

```bash
./gradlew -PsbsApiBaseUrl=https://sidebyside.example \
  -PsbsSpaceId=00000000-0000-0000-0000-000000000000 \
  :app:assembleDebug
```

Ohne gültige Konfiguration zeigt die Oberfläche nur einen verständlichen
Betreiberhinweis und startet keine API-Anfrage.

## Reproduzierbarer Gradle-Build

Der eingecheckte Gradle Wrapper ist die einzige unterstützte Gradle-
Einstiegsstelle für Android. Aktuell sind **Gradle 9.5.0**, AGP 9.3.0 und
JDK 17 festgelegt. `gradle/wrapper/gradle-wrapper.properties` bindet die
Gradle-9.5.0-Binärdistribution an deren offiziellen SHA-256; CI validiert
zusätzlich den eingecheckten Wrapper-JAR gegen den offiziellen Wrapper-
SHA-256. `gradle/actions/setup-gradle` wird in CI nur noch für Cache und
Wrapper-Validierung verwendet und installiert keine separate Gradle-Version.

Mit installiertem JDK 17 und Android SDK 37.1:

```bash
./gradlew --version
./gradlew --no-daemon --dependency-verification strict :app:testDebugUnitTest
./gradlew --no-daemon --dependency-verification strict :app:lintDebug
./gradlew --no-daemon --dependency-verification strict :app:assembleDebug
```

Gradle Dependency Verification läuft mit `gradle/verification-metadata.xml`.
Der Default-Modus von Gradle ist bereits `strict`; CI gibt den Modus zusätzlich
explizit an. Die Datei enthält konkrete SHA-256-Werte für die tatsächlich
aufgelösten Build-, Plugin-, Test- und Runtime-Artefakte. Es gibt keine
Wildcards oder pauschalen Trust-Ausnahmen. Signaturprüfung ist derzeit nicht
aktiviert: die verwendeten Google-Maven-/Maven-Central-Artefakte bieten keine
für den gesamten Graphen konsistente PGP-Abdeckung; vollständige SHA-256-
Prüfung vermeidet deshalb Ausnahmen für unsignierte Artefakte. CI führt einen
Negativtest aus, der Checksums nur in der Arbeitskopie manipuliert und belegt,
dass Gradle den Build anschließend wegen Dependency Verification ablehnt.

### Wrapper aktualisieren

Wrapper-Upgrades sind security-sensitiv und werden nur zusammen mit einer
bewussten Gradle-/AGP-Kompatibilitätsprüfung durchgeführt. Die neue
Distribution- und Wrapper-JAR-Checksum zuerst unabhängig auf Gradles offizieller
Release-Checksum-Seite prüfen. Anschließend aus `android/`:

```bash
./gradlew wrapper \
  --gradle-version <VERSION> \
  --distribution-type bin \
  --gradle-distribution-sha256-sum <OFFICIAL_BIN_SHA256>
sha256sum gradle/wrapper/gradle-wrapper.jar
```

Danach den erwarteten Wrapper-JAR-SHA in den Android-CI-Workflows aktualisieren,
den vollständigen Wrapper-Diff prüfen und alle Android-/G2-Gates ausführen.
Ein Wrapper-JAR wird nie aus einer inoffiziellen Quelle übernommen.

### Dependency Verification pflegen

Eine legitime Dependency-Änderung scheitert zunächst erwartungsgemäß an einem
noch nicht freigegebenen Artefakt. Nachdem Koordinate, Version und Quelle der
Änderung geprüft wurden, kann die Metadata-Datei mit Gradles nativer Funktion
ergänzt werden:

```bash
./gradlew --write-verification-metadata sha256 \
  :app:testDebugUnitTest :app:lintDebug :app:assembleDebug
```

`gradle/verification-metadata.xml` danach **nicht blind übernehmen**: Diff auf
unerwartete Komponenten/Versionen, zusätzliche Artefakte, Wildcards oder
Trust-Ausnahmen prüfen und anschließend wieder einen normalen Strict-Build
sowie den CI-Negativtest laufen lassen. Nicht mehr benötigte alte Einträge
sollen bei Dependency-Wechseln entfernt werden, damit die Datei eine enge
Allowlist bleibt.

### Dependency Locking

Dependency Locking wurde für #185 geprüft und bewusst nicht zusätzlich
aktiviert. Der aktuelle Android-Build verwendet keine dynamischen Versionen,
Versionsbereiche oder `SNAPSHOT`-Dependencies; direkte Versionen und die
Compose-BOM sind fest versioniert. Die strikte Verification-Metadata lässt
außerdem neu aufgelöste, noch nicht freigegebene transitive Artefakte nicht
stillschweigend zu. Lockfiles würden für den aktuellen Scope einen zweiten,
konfigurationsreichen Versionszustand pflegen, ohne das konkrete #185-Risiko
weiter zu schließen. Sobald dynamische Versionen eingeführt oder andere
Reproduzierbarkeitsanforderungen entstehen, ist Locking separat neu zu
bewerten.

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
