# Abhängigkeiten und Assets

Jede Abhängigkeit wird mit Name, Version, Quelle und Lizenz geführt. Jedes
Asset mit Ursprung, Lizenz und Ersteller. Was hier nicht steht, gehört
nicht ins Projekt.

Stand: 2026-08-24

## Reproduzierbarkeit und Prüfung

`backend/uv.lock` ist die verbindliche, plattformübergreifende Auflösung
aller direkten und transitiven Python-Abhängigkeiten. Die verwendete
uv-Version `0.12.5`, Python `3.13.7`, das Build-Backend und das
Python-Container-Image sind exakt gepinnt. Installationen in CI und Container
laufen ausschließlich im Frozen-/Locked-Modus; `uv lock --check` verhindert
eine veraltete Lockdatei.

Die CI führt `uv audit --preview --frozen` gegen OSV aus. Die Policy erlaubt
keinen bekannten Sicherheitsfund und keinen nachteiligen Paketstatus. Eine
Ausnahme dürfte nur mit Advisory-ID, Begründung, Ablaufdatum und verlinktem
Issue unter `[tool.uv.audit]` eingetragen werden; derzeit gibt es keine.

Der dokumentierte Stand wird nach der gesperrten Installation automatisch
mit den tatsächlich installierten Versionen und den `License-Expression`-
beziehungsweise `License`-Metadaten der Pakete verglichen. Damit sind die
Tabellen unten prüfbar und nicht nur eine manuell gepflegte Behauptung.

`.github/dependabot.yml` lässt uv-, Docker- und GitHub-Actions-Abhängigkeiten
wöchentlich aktualisieren. Bei einem neuen Fork oder Repository müssen unter
**Settings → Security and analysis** zusätzlich „Dependabot alerts“ und
„Dependabot security updates“ aktiviert werden; die normalen Versionsupdates
starten bereits durch die Konfigurationsdatei.

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

## Container-Basisimages

| Image | Version | Quelle | Lizenz |
|---|---|---|---|
| python | 3.13.7-slim@sha256:5f55cdf0c5d9dc1a415637a5ccc4a9e18663ad203673173b8cda8f8dcacef689 | Docker Hub | PSF-2.0 (Python), Debian-Pakete je eigene Lizenz |
| postgres | 17-alpine | Docker Hub | PostgreSQL License |

## Web und Android

Noch keine Abhängigkeiten. Die Clients beginnen mit Milestone M5.

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
hinzugefügt. Die CI prüft Vollständigkeit, genaue Version und Lizenz gegen
die gesperrte, installierte Umgebung. Transitive Versionen stehen vollständig
in `backend/uv.lock`.

Neue Assets werden in derselben Änderung hier dokumentiert. Bei unklarer
Herkunft, Lizenz oder Erstellerschaft wird das Asset nicht aufgenommen, bis
die Provenienz geklärt ist.
