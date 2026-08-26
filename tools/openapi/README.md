# OpenAPI-Client-Generierung

Web und Android sprechen denselben versionierten Vertrag. Diese Schicht
erzeugt die mechanischen Teile davon — DTOs und, auf der Webseite, die
Endpunktaufrufe — aus `backend/openapi.json`, statt sie zweimal von Hand zu
pflegen.

Generiert wird ausdrücklich **keine** Domain-, UI- oder State-Logik.

```text
FastAPI  ->  backend/openapi.json  ->  openapi-generator
                                        |-- web/src/api/generated      (TypeScript)
                                        '-- android/api/generated      (Kotlin-Modelle)
```

## Benutzung

```bash
tools/openapi/generate.sh           # neu erzeugen
tools/openapi/generate.sh --check   # nur auf Drift prüfen (CI)
```

Voraussetzung ist Docker — dasselbe, was der Self-Hosted-Stack ohnehin
verlangt. Ein JDK oder Node wird lokal nicht gebraucht.

## Warum dieser Generator

`openapi-generator` bedient TypeScript und Kotlin aus einer Konfiguration.
Geprüfte Alternativen und warum sie hier nicht passen:

- **openapi-typescript + openapi-fetch** erzeugt sehr schlanken TypeScript-Code,
  deckt Kotlin aber nicht ab.
- **Kiota** unterstützt TypeScript, aber kein Kotlin.
- **orval**, **hey-api**, **oazapfts** sind TypeScript-only.
- **swagger-codegen** ist der Vorgänger von openapi-generator; die aktive
  Weiterentwicklung liegt bei letzterem.

## Bekannte Einschränkung: die Story-Union auf Kotlin

Der ursprüngliche Kotlin-Generator-Stand erzeugte `StoryItem` als unbrauchbare
abstrakte Sammelklasse. Der Fix ist in #119 umgesetzt:

- OpenAPI Generator wurde aktualisiert.
- `generateOneOfAnyOfWrappers` ist für Kotlin aktiviert.
- Die erzeugten Varianten werden wieder als discriminator-basierte Union
  erzeugt und können über `kotlinx.serialization` deserialisiert werden.

Die Ursache lag nicht im OpenAPI-Vertrag. Der Vertrag mit
`discriminator.propertyName = kind` bleibt die einzige Quelle.

## Warum der generierte Code eingecheckt ist

Der Vertrag `backend/openapi.json` ist bereits eingecheckt und wird gegen die
echte ASGI-App geprüft. Der Client-Code folgt derselben Linie.

- Ein Vertragsbruch ist im Pull Request als Diff sichtbar.
- Web- und Android-Builds brauchen weder Docker noch Netzzugang, um zu starten.
- Der Drift-Check vergleicht nur die erzeugten Dateien.

## Runtime-Abhängigkeiten

**TypeScript:** keine. Der Generator `typescript-fetch` erzeugt Code gegen die
Fetch-API des Browsers.

**Kotlin:** `kotlinx.serialization`. Die Modelle tragen `@Serializable` und
`@SerialName`; Retrofit oder Ktor bleiben eine spätere Android-Entscheidung.

## Lizenzen

`openapi-generator` steht unter Apache-2.0. Der Generator wird nur zur Bauzeit
ausgeführt.

Der Container wird über Version und Digest festgenagelt.

## Aktualisieren

1. Neuen Tag in `generator.env` eintragen.
2. Digest aktualisieren.
3. `tools/openapi/generate.sh` laufen lassen.
4. Den Diff im Pull Request begründen.
