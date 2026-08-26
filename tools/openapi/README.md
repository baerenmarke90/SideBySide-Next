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
  deckt Kotlin aber nicht ab. Zwei Werkzeuge hießen zwei Pins, zwei
  Konfigurationsstile, zwei Lizenzprüfungen und zwei CI-Pfade.
- **Kiota** (Microsoft) unterstützt TypeScript, aber kein Kotlin.
- **orval**, **hey-api**, **oazapfts** sind TypeScript-only.
- **swagger-codegen** ist der Vorgänger von openapi-generator; die aktive
  Weiterentwicklung liegt bei letzterem.

## Story-Union auf Kotlin

Der frühere Generator-Stand erzeugte `StoryItem` als unbrauchbare
`sealed class`: die Varianten erbten nicht von ihr und der Basistyp verlangte
die Felder aller drei Varianten gleichzeitig. Das ist mit #119 behoben.

OpenAPI Generator v7.24.0 erzeugt mit `generateOneOfAnyOfWrappers` und
`kotlinx.serialization` jetzt eine discriminator-basierte `sealed interface`.
Der generierte Serializer wertet `kind` aus und deserialisiert `MEMORY`,
`HEART_MOMENT` und `MILESTONE` jeweils in den passenden Wrapper. Damit bleibt
`StoryPage.items` eine `List<StoryItem>`, ohne dass eine Variante die Felder der
anderen Varianten benötigt.

Die Ursache lag nicht im OpenAPI-Vertrag. Der Vertrag mit
`discriminator.propertyName = kind` bleibt unverändert die einzige Quelle.

## Warum der generierte Code eingecheckt ist

Der Vertrag `backend/openapi.json` ist bereits eingecheckt und wird gegen die
echte ASGI-App geprüft. Der Client-Code folgt derselben Linie:

- Ein Vertragsbruch ist im Pull Request als Diff **lesbar**, statt nur als
  roter CI-Schritt zu erscheinen.
- Web- und Android-Builds brauchen weder Docker noch Netzzugang, um zu
  starten.
- Der Drift-Check ist ein Vergleich und kein zweiter Erzeugungspfad, der
  selbst abweichen könnte.

Der Preis ist ein größerer Diff bei Vertragsänderungen. Das ist beabsichtigt:
eine Änderung an der Client-Schnittstelle *soll* im Review sichtbar sein.

## Runtime-Abhängigkeiten

**TypeScript:** keine. Der Generator `typescript-fetch` erzeugt Code gegen die
Fetch-API des Browsers. Es entsteht keine `package.json`, und die erzeugten
Dateien importieren nichts außerhalb ihres eigenen Ordners — nachgeprüft, nicht
angenommen.

**Kotlin:** `kotlinx.serialization`. Die Modelle tragen `@Serializable` und
`@SerialName`; ohne eine JSON-Bibliothek geht das nicht, und
`kotlinx.serialization` ist die einzige der Optionen, die den Android-Client
**nicht** zusätzlich auf einen HTTP-Stack festlegt — sie funktioniert sowohl
mit Retrofit als auch mit Ktor. Moshi, Gson und Jackson wären hier stärkere
Vorfestlegungen.

Kein Service-Layer auf der Kotlin-Seite: Retrofit oder Ktor wären eine
Entscheidung über den Android-Client, den es noch nicht gibt. Sie kommt
additiv dazu, sobald das Projekt existiert.

## Lizenzen

`openapi-generator` steht unter **Apache-2.0**. Das Werkzeug wird nur zur
Bauzeit ausgeführt und nicht ausgeliefert; Apache-2.0 stellt an den erzeugten
Code keine Bedingungen. Der erzeugte Code ist damit Projektcode unter der
Projektlizenz.

Der Container wird über Version **und** Digest festgenagelt
(`tools/openapi/generator.env`). Ein neu gesetzter Tag kann so nicht
unbemerkt anderen Client-Code erzeugen.

## Aktualisieren

1. Neuen Tag in `generator.env` eintragen.
2. `docker pull openapitools/openapi-generator-cli:<tag>` ausführen und den
   gemeldeten Digest eintragen.
3. `tools/openapi/generate.sh` laufen lassen.
4. Den entstehenden Diff im Pull Request begründen — ein Generatorwechsel
   ändert Client-Code, und das ist eine Review-Frage, keine Formalie.
