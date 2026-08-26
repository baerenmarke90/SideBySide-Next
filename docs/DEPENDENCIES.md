# Abhängigkeiten und Assets

Jede Abhängigkeit wird mit Name, Version, Quelle und Lizenz geführt. Jedes
Asset mit Ursprung, Lizenz und Ersteller. Was hier nicht steht, gehört
nicht ins Projekt.

Stand: 2026-08-26

## Reproduzierbarkeit und Prüfung

`backend/uv.lock` ist die verbindliche, plattformübergreifende Auflösung
aller direkten und transitiven Python-Abhängigkeiten. Die verwendete
uv-Version `0.12.5`, Python `3.13.7`, das Build-Backend und das
Python-Container-Image sind exakt gepinnt. Installationen in CI und Container
laufen ausschließlich im Frozen-/Locked-Modus; `uv lock --check` verhindert
eine veraltete Lockdatei.

`web/package-lock.json` ist die verbindliche npm-Auflösung für den dünnen
M2-S8-Web-Referenzflow. Direkte Versionen sind in `web/package.json` exakt
gepinnt, CI installiert ausschließlich mit `npm ci`, und `npm audit
--audit-level=high` blockiert bekannte Schwachstellen ab hoher Kritikalität.
Das Node-CI-Image ist zusätzlich per Digest gepinnt.

Der dünne M2-S8-Android-Referenzflow verwendet ausschließlich exakt
versionierte Gradle-/Maven-Koordinaten und die feste Compose-BOM
`2026.08.00`. Sein eigener CI-Nachweis pinnt JDK 17, Gradle 9.5.0,
Android Gradle Plugin 9.3.0, compileSdk 37 und Build Tools 36.0.0. Damit sind
Werkzeugkette und direkte Dependency-Auswahl nicht von lokalen Android-Studio-
Defaults abhängig.

Die Backend-CI führt `uv audit --preview --frozen` gegen OSV aus. Die Policy
erlaubt keinen bekannten Sicherheitsfund und keinen nachteiligen Paketstatus.
Eine Ausnahme dürfte nur mit Advisory-ID, Begründung, Ablaufdatum und
verlinktem Issue unter `[tool.uv.audit]` eingetragen werden; derzeit gibt es
keine.

Der dokumentierte Backend-Stand wird nach der gesperrten Installation
automatisch mit den tatsächlich installierten Versionen und den
`License-Expression`- beziehungsweise `License`-Metadaten der Pakete
verglichen. Für Web stehen die direkten Abhängigkeiten unten; der vollständige
transitive npm-Graph einschließlich Integritäts-Hashes steht in
`web/package-lock.json`. Für Android stehen direkte Laufzeit-, Test- und
Build-Abhängigkeiten unten; die CI löst sie ausschließlich aus Google Maven
und Maven Central mit den dort fest angegebenen Versionen auf.

`.github/dependabot.yml` lässt uv-, npm-, Gradle-, Docker- und GitHub-Actions-
Abhängigkeiten wöchentlich aktualisieren. Bei einem neuen Fork oder Repository
müssen unter **Settings → Security and analysis** zusätzlich „Dependabot
alerts“ und „Dependabot security updates“ aktiviert werden; die normalen
Versionsupdates starten bereits durch die Konfigurationsdatei.

### Dokumentierter Policy-Dry-Run

Der folgende Test legt nur in einem temporären Verzeichnis einen absichtlich
verwundbaren Lockstand an. Er muss mit einem Fund und einem von null
verschiedenen Exit-Code enden; die echte Projekt-Lockdatei bleibt unverändert.

```bash
probe=$(mktemp -d)
printf '[project]\nname="audit-probe"\nversion="0"\nrequires-python=">=3.12"\ndependencies=["jinja2==2.10"]\n' > "$probe/pyproject.toml"
uv lock --directory "$probe"
uv audit --preview --frozen --directory "$probe"
```

`argon2-cffi` deckt genau einen Zweck ab: die Ableitung von Passwoertern.
Eigene Tokens kommen mit `secrets` und `hashlib` aus der Standardbibliothek
aus - fuer einen Wert mit voller Entropie waere ein absichtlich langsames
Verfahren nur eine Bremse bei jeder Anfrage.

Dazu kommt mit OIDC `pyjwt[crypto]` und damit `cryptography`: die Signatur
eines fremden ID Tokens laesst sich nicht mit `hashlib` pruefen, und ein
selbst geschriebener RSA-/ECDSA-Verifizierer waere im Auth-Pfad genau der
falsche Ort fuer Eigenbau. `httpx` wird von der Entwicklungs- zur
Laufzeitabhaengigkeit, weil Discovery, JWKS-Abruf und Token-Endpunkt
ausgehendes HTTP brauchen.

`webauthn` (py_webauthn) kommt aus demselben Grund dazu: eine Passkey-
Registrierung bringt CBOR, COSE-Schluessel und Attestation mit, und diese
Formate von Hand zu lesen waere Eigenbau an der empfindlichsten Stelle.

`cbor2` steht nur in der Entwicklung: der virtuelle Authenticator in den
Tests baut `attestationObject` und COSE-Schluessel selbst, damit die Suite
echte Signaturen prueft statt aufgezeichneter Beispieldaten.

`Pillow` und `pillow-heif` kommen mit der Medienverarbeitung dazu. Bilder zu
dekodieren, ihre Masse zu bestimmen, eingebettete Metadaten zu entfernen und
ein Thumbnail zu erzeugen, ist nichts, was sich sinnvoll selbst schreiben
laesst - ein eigener JPEG-, PNG- oder WebP-Dekoder waere Eigenbau an der
groessten Angriffsflaeche des Produkts. `pillow-heif` bringt libheif und
damit HEIC/HEIF, die in der M2-D04-Allowlist stehen; es registriert sich als
Plugin in Pillow und wird nicht getrennt aufgerufen.

Beide sind bewusst der einzige Zuwachs dieses Slices. Video und der dafuer
noetige ffmpeg-Aufruf sind nach M2-D23 ein eigener spaeterer Schritt, weil
ein Systembinary Container-Image und Installationsanleitung betrifft und
sich dem `uv audit`-Gate entzieht.

Medienparser sind erklaerte Angriffsflaeche. Deshalb gilt fuer sie
besonders, was ohnehin Policy ist: kein bekannter Sicherheitsfund im Lock,
Dependabot-Updates werden nicht liegengelassen, und die Verarbeitung laeuft
ausschliesslich im Hintergrundjob unter Ressourcengrenzen - nie im
Requestpfad.

## Backend — Laufzeit

| Paket | Version | Quelle | Lizenz |
|---|---|---|---|
| fastapi | 0.141.1 | PyPI | MIT |
| uvicorn[standard] | 0.52.4 | PyPI | BSD-3-Clause |
| sqlalchemy | 2.0.52 | PyPI | MIT |
| alembic | 1.19.1 | PyPI | MIT |
| psycopg[binary] | 3.3.4 | PyPI | **LGPL-3.0-only** |
| pydantic | 2.13.4 | PyPI | MIT |
| pydantic-settings | 2.15.0 | PyPI | MIT |
| uuid6 | 2025.0.1 | PyPI | MIT |
| argon2-cffi | 25.1.0 | PyPI | MIT |
| httpx | 0.28.1 | PyPI | BSD-3-Clause |
| pyjwt[crypto] | 2.13.0 | PyPI | MIT |
| webauthn | 3.0.0 | PyPI | BSD-3-Clause |
| pillow | 12.3.0 | PyPI | MIT-CMU |
| pillow-heif | 1.5.0 | PyPI | BSD-3-Clause |

## Backend — Entwicklung

| Paket | Version | Quelle | Lizenz |
|---|---|---|---|
| pytest | 9.1.1 | PyPI | MIT |
| pytest-asyncio | 1.4.0 | PyPI | Apache-2.0 |
| httpx2 | 2.12.0 | PyPI | BSD-3-Clause |
| cbor2 | 6.1.4 | PyPI | MIT |
| ruff | 0.16.4 | PyPI | MIT |
| mypy | 2.3.1 | PyPI | MIT |

## Web — M2-S8 Laufzeit

| Paket | Version | Quelle | Lizenz |
|---|---|---|---|
| @tanstack/react-query | 5.85.5 | npm | MIT |
| react | 19.1.1 | npm | MIT |
| react-dom | 19.1.1 | npm | MIT |
| react-router-dom | 7.18.2 | npm | MIT |

## Web — M2-S8 Entwicklung

| Paket | Version | Quelle | Lizenz |
|---|---|---|---|
| @types/react | 19.1.12 | npm | MIT |
| @types/react-dom | 19.1.9 | npm | MIT |
| typescript | 5.9.2 | npm | Apache-2.0 |
| vite | 7.3.6 | npm | MIT |
| vitest | 3.2.7 | npm | MIT |

Diese Web-Abhängigkeiten dienen ausschließlich dem dünnen S8-Referenzflow.
Sie ziehen keine M5-Funktionen wie persistente Offline-Caches, vollständige
Navigation oder Client-Parität vor. Der generierte `typescript-fetch`-Code
bleibt ohne zusätzliche Runtime-Abhängigkeit und nutzt die Browser-Fetch-API.

## Android — M2-S8 Laufzeit

| Paket / Plattformbaustein | Version | Quelle | Lizenz |
|---|---|---|---|
| Jetpack Compose BOM | 2026.08.00 | Google Maven | Apache-2.0 |
| Compose UI / Material 3 | über BOM (Compose 1.12 / Material 3 1.4) | Google Maven | Apache-2.0 |
| androidx.activity:activity-compose | 1.13.0 | Google Maven | Apache-2.0 |
| androidx.lifecycle:lifecycle-viewmodel-compose | 2.11.0 | Google Maven | Apache-2.0 |
| com.squareup.okhttp3:okhttp | 5.4.0 | Maven Central | Apache-2.0 |
| org.jetbrains.kotlinx:kotlinx-coroutines-android | 1.11.0 | Maven Central | Apache-2.0 |
| org.jetbrains.kotlinx:kotlinx-serialization-json | 1.11.0 | Maven Central | Apache-2.0 |
| Android Photo Picker | Plattform / Activity Result Contract | Android | Plattform-API; kein zusätzliches Paket |

`android/api/generated` bleibt generator-owned. Seine `@Serializable`-
Modelle werden direkt als Source-Root eingebunden; insbesondere gibt es keine
zweite DTO-/Union-Schicht. OkHttp ist ausschließlich die kleine Transportstufe
für die veröffentlichten Endpunkte und die serverseitig ausgestellten
Upload-/Read-Deskriptoren. `STREAM` erhält Bearer-Auth; Signed URLs erhalten
sie absichtlich nicht.

Der S8-Client führt bewusst **kein** Room, Paging, WorkManager, DataStore oder
Bildcache-Framework ein. Tokens, Ergebnis und Bild leben nur im flüchtigen
Prozess-/ViewModel-State. Damit wird die offene M2-D18-Cacheentscheidung nicht
vorweggenommen.

## Android — M2-S8 Test und Build

| Paket / Werkzeug | Version | Quelle | Lizenz |
|---|---|---|---|
| Android Gradle Plugin | 9.3.0 | Google Maven | Apache-2.0 |
| Gradle | 9.5.0 | gradle.org / CI setup-gradle | Apache-2.0 |
| Compose Compiler Gradle Plugin | 2.3.21 | Gradle Plugin Portal / Maven Central | Apache-2.0 |
| Kotlin Serialization Gradle Plugin | 2.3.21 | Gradle Plugin Portal / Maven Central | Apache-2.0 |
| JUnit 4 | 4.13.2 | Maven Central | EPL-1.0 |
| androidx.test:core | 1.7.0 | Google Maven | Apache-2.0 |
| Compose UI Test JUnit4 | über BOM | Google Maven | Apache-2.0 |
| kotlinx-coroutines-test | 1.11.0 | Maven Central | Apache-2.0 |
| Robolectric | 4.16.1 | Maven Central | MIT |

Der Android-S8-CI-Job nutzt JDK 17, installiert SDK Platform 37 sowie Build
Tools 36.0.0 und führt JVM-/Robolectric-/Compose-Semantics-Tests, Android Lint
und `assembleDebug` aus. Die GitHub Actions selbst sind auf Commit-SHAs
gepinnt.

## Container-Basisimages

| Image | Version | Quelle | Lizenz |
|---|---|---|---|
| python | 3.13.7-slim@sha256:5f55cdf0c5d9dc1a415637a5ccc4a9e18663ad203673173b8cda8f8dcacef689 | Docker Hub | PSF-2.0 (Python), Debian-Pakete je eigene Lizenz |
| postgres | 17-alpine | Docker Hub | PostgreSQL License |
| node | 22.19.0-bookworm-slim@sha256:4a4884e8a44826194dff92ba316264f392056cbe243dcc9fd3551e71cea02b90 | Docker Hub | MIT (Node.js), Debian-Pakete je eigene Lizenz |

## Werkzeuge zur Bauzeit

| Werkzeug | Version | Quelle | Lizenz |
|---|---|---|---|
| openapi-generator-cli | v7.16.0@sha256:e56372add5e038753fb91aa1bbb470724ef58382fdfc35082bf1b3e079ce353c | Docker Hub | Apache-2.0 |

Der Generator erzeugt die Client-API-Schichten aus `backend/openapi.json`. Er
läuft ausschließlich zur Bauzeit und wird nicht ausgeliefert; Apache-2.0
stellt an den erzeugten Code keine Bedingungen. Version und Digest stehen in
`tools/openapi/generator.env`, Details in
[`tools/openapi/README.md`](../tools/openapi/README.md).

## Zu prüfen: psycopg unter LGPL

`psycopg` steht unter **LGPL-3.0-only** und ist damit die einzige
Abhängigkeit, deren Lizenz nicht permissiv ist.

Die praktische Lage:

- Der Treiber wird als eigenständiges Paket dynamisch geladen, nicht in
  eigenen Code hineinkompiliert.
- Für den betriebenen Cloud-Dienst liegt keine Weitergabe vor; die LGPL
  greift dort typischerweise nicht.
- Für die Self-Hosted-Auslieferung als Container-Image liegt eine
  Weitergabe vor. Die LGPL verlangt dann unter anderem, dass Empfänger den
  Treiber durch eine eigene Fassung ersetzen können und dass Lizenztext
  und Quellenhinweis beiliegen.

Das ist bei einem separat installierten Python-Paket erfüllbar, aber es
ist eine bewusste Auflage und keine Formalie. Vor dem kommerziellen Start
gehört sie geprüft — gegebenenfalls durch Wechsel auf einen permissiv
lizenzierten Treiber.

Diese Einschätzung ist keine Rechtsberatung.

## Assets

Das Repository enthält inzwischen projektspezifische Bild- und SVG-Assets.
Sie wurden für SideBySide Next bzw. dessen Roadmap und M2-Handoff erstellt;
Assets ungeklärter Drittanbieter- oder Vorgängerherkunft werden weiterhin
nicht aufgenommen. Die Produktbilder sind ausdrücklich Mockups und keine
Screenshots einer bereits fertigen App.

Für die unten als **Projektasset** gekennzeichneten Dateien wird derzeit keine
separate öffentliche Lizenz eingeräumt. Diese Einordnung ändert nichts an
der noch offenen Lizenzentscheidung für den eigenen Quellcode.

| Asset | Ursprung | Ersteller | Lizenz |
|---|---|---|---|
| `docs/assets/playstore/app-icon.png` | SideBySide Next Produktvorschau | SideBySide Next Projektworkflow, AI-assistiert und menschlich geprüft | Projektasset; keine separate öffentliche Lizenzfreigabe |
| `docs/assets/playstore/feature-graphic.png` | SideBySide Next Produktvorschau | SideBySide Next Projektworkflow, AI-assistiert und menschlich geprüft | Projektasset; keine separate öffentliche Lizenzfreigabe |
| `docs/assets/playstore/screen-01-onboarding.png` | SideBySide Next Produkt-Mockup | SideBySide Next Projektworkflow, AI-assistiert und menschlich geprüft | Projektasset; keine separate öffentliche Lizenzfreigabe |
| `docs/assets/playstore/screen-02-heute.png` | SideBySide Next Produkt-Mockup | SideBySide Next Projektworkflow, AI-assistiert und menschlich geprüft | Projektasset; keine separate öffentliche Lizenzfreigabe |
| `docs/assets/playstore/screen-03-story.png` | SideBySide Next Produkt-Mockup | SideBySide Next Projektworkflow, AI-assistiert und menschlich geprüft | Projektasset; keine separate öffentliche Lizenzfreigabe |
| `docs/assets/playstore/screen-04-wuensche.png` | SideBySide Next Produkt-Mockup | SideBySide Next Projektworkflow, AI-assistiert und menschlich geprüft | Projektasset; keine separate öffentliche Lizenzfreigabe |
| `docs/assets/playstore/screen-05-plan.png` | SideBySide Next Produkt-Mockup | SideBySide Next Projektworkflow, AI-assistiert und menschlich geprüft | Projektasset; keine separate öffentliche Lizenzfreigabe |
| `docs/assets/playstore/screen-06-discovery.png` | SideBySide Next Produkt-Mockup | SideBySide Next Projektworkflow, AI-assistiert und menschlich geprüft | Projektasset; keine separate öffentliche Lizenzfreigabe |
| `docs/assets/playstore/screen-07-einkauf.png` | SideBySide Next Produkt-Mockup | SideBySide Next Projektworkflow, AI-assistiert und menschlich geprüft | Projektasset; keine separate öffentliche Lizenzfreigabe |
| `docs/assets/playstore/screen-08-privacy.png` | SideBySide Next Produkt-Mockup | SideBySide Next Projektworkflow, AI-assistiert und menschlich geprüft | Projektasset; keine separate öffentliche Lizenzfreigabe |
| `docs/assets/roadmap/roadmap-overview.svg` | SideBySide Next Roadmap | SideBySide Next Projektworkflow, AI-assistiert und menschlich geprüft | Projektasset; keine separate öffentliche Lizenzfreigabe |
| `docs/assets/roadmap/roadmap-tracks.svg` | SideBySide Next Roadmap | SideBySide Next Projektworkflow, AI-assistiert und menschlich geprüft | Projektasset; keine separate öffentliche Lizenzfreigabe |
| `design/m2/m2-screenflow.svg` | M2 Client-Handoff | SideBySide Next Projektworkflow, AI-assistiert und menschlich geprüft | Projektasset; keine separate öffentliche Lizenzfreigabe |
| `docs/m2/m2-privacy-flow.svg` | M2 Privacy-/Acceptance-Handoff | SideBySide Next Projektworkflow, AI-assistiert und menschlich geprüft | Projektasset; keine separate öffentliche Lizenzfreigabe |

Derzeit sind keine Schrift- oder Audio-Assets im Repository dokumentiert.

## Pflege

Eine neue direkte Abhängigkeit wird zusammen mit ihrem Eintrag hier
hinzugefügt. Die CI prüft die Backend-Dokumentation gegen die gesperrte,
installierte Umgebung. Transitive Python-Versionen stehen vollständig in
`backend/uv.lock`; transitive Web-Versionen und Integritäts-Hashes vollständig
in `web/package-lock.json`. Android hält alle direkten Koordinaten und die
Compose-BOM im Gradle-Build exakt fest; Dependabot beobachtet den
`/android`-Build separat.

Neue Assets werden in derselben Änderung hier dokumentiert. Bei unklarer
Herkunft, Lizenz oder Erstellerschaft wird das Asset nicht aufgenommen, bis
die Provenienz geklärt ist.