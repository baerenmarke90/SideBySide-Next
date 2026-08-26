# Arcane Deployment

Diese Hinweise ergaenzen `SELF-HOSTING.md` fuer Installationen, bei denen Arcane
den SideBySide-Stack verwaltet und ein separater TLS-Reverse-Proxy davorsteht.

## Welche Compose-Datei?

SideBySide hat zwei bewusst getrennte Self-Hosting-Einstiege:

| Umgebung | Compose-Datei | Build-Kontext |
|---|---|---|
| kompletter Repository-Checkout | `compose.yaml` | lokal: `./backend`, `./web` |
| Arcane / Remote-Workspace | `compose.arcane.yaml` | Git-Repository + Ref |

`compose.yaml` ist der kanonische Einstieg fuer normale Docker-Compose-Nutzer.
Arcane soll dagegen **`compose.arcane.yaml`** verwenden. Diese Datei benoetigt
weder `./backend` noch `./web` im Arcane-Projektverzeichnis und vermeidet damit
den Fehler `build context not found` fuer `/app/data/projects/<projekt>/backend`.

Beide Varianten enthalten dieselben Dienste, Volumes, Netzwerke,
Runtime-Einstellungen und Startabhaengigkeiten. CI vergleicht ihre gerenderte
Konfiguration und erlaubt als beabsichtigten Unterschied nur die Build-Kontexte.

## Arcane einrichten

1. In Arcane das SideBySide-Projekt mit GitOps bzw. der gewuenschten
   Repository-Quelle anlegen.
2. Als Compose-Datei `compose.arcane.yaml` auswaehlen.
3. Die Werte aus `.env.example` als Projekt-Environment uebernehmen und
   mindestens `POSTGRES_PASSWORD` sowie fuer die Erstregistrierung
   `SBS_BOOTSTRAP_TOKEN` sicher setzen.
4. Fuer Tests kann `SBS_SOURCE_REF=main` verwendet werden. Fuer Produktion
   einen unveraenderlichen Release-Tag verwenden.
5. Deployment starten. `migrate` muss erfolgreich abschliessen, bevor API und
   Worker starten; Web wartet zusaetzlich auf die API-Readiness.

Die Arcane-Datei verwendet standardmaessig:

```dotenv
SBS_SOURCE_REPOSITORY=https://github.com/baerenmarke90/SideBySide-Next.git
SBS_SOURCE_REF=main
```

Daraus entstehen fuer die Builds beispielsweise:

```text
https://github.com/baerenmarke90/SideBySide-Next.git#main:backend
https://github.com/baerenmarke90/SideBySide-Next.git#main:web
```

`api`, `worker` und `migrate` verwenden immer denselben Backend-Kontext und
entstehen damit aus demselben Quellstand.

## Oeffentliches und privates Repository

Bei einem oeffentlichen Repository kann Docker/BuildKit den Git-Build-Kontext
ohne Repository-Credentials laden.

Bei einem privaten Repository benoetigt der Docker-/BuildKit-Prozess dagegen
eine vom Betreiber bzw. von Arcane bereitgestellte Git-Authentifizierung. Diese
Authentifizierung ist eine Eigenschaft der Build-Umgebung und wird **nicht** in
`compose.arcane.yaml`, `.env.example` oder einer Git-URL mit eingebettetem Token
abgelegt.

Wenn die eingesetzte Arcane-/BuildKit-Konfiguration keinen authentifizierten
Remote-Git-Build unterstuetzt, ist `compose.arcane.yaml` mit einem privaten Repo
nicht ausreichend. Dann muss zuerst die Build-Authentifizierung der Plattform
sauber eingerichtet oder spaeter auf versionierte Registry-Images umgestellt
werden. Die Repository-Sichtbarkeit selbst ist keine SideBySide-Anforderung.

## Warum Git-Build-Kontexte?

Docker Compose und BuildKit unterstuetzen Git-Repositorys mit Ref und
Unterverzeichnis nativ. Deshalb ist fuer Arcane kein eigener Deployment-
Orchestrator und keine SideBySide-spezifische Synchronisationslogik notwendig.

Der fruehere Weg, in der Standard-Compose-Datei `SBS_BACKEND_BUILD_CONTEXT` und
`SBS_WEB_BUILD_CONTEXT` manuell zu setzen, wurde bewusst entfernt: Die normale
Compose-Datei bleibt dadurch auf vollstaendige Repository-Checkouts fokussiert,
waehrend Arcane einen eindeutigen eigenen Einstieg besitzt.

## Zielbild mit Reverse-Proxy

Der Reverse-Proxy ist der einzige oeffentliche TLS-Endpunkt. Er routet auf
derselben oeffentlichen Origin zwei interne Ziele:

| Pfad | internes Ziel |
|---|---|
| `/api/` | SideBySide API auf `API_PORT` |
| alle anderen Pfade | SideBySide Web auf `WEB_PORT` |

Die `/api/`-Route muss **direkt** zur API gehen. In Produktion darf sie nicht
zuerst durch den Web-Nginx laufen, weil sonst der vertrauenswuerdige TLS-Proxy-
Hop fuer `X-Forwarded-Proto` verloren geht.

## Reverse-Proxy auf demselben Host

Der sichere Standard reicht aus:

```dotenv
SBS_BIND_IP=127.0.0.1
API_PORT=8000
WEB_PORT=8080
```

Der Proxy verwendet dann `127.0.0.1:<API_PORT>` und
`127.0.0.1:<WEB_PORT>`.

## Reverse-Proxy auf einem anderen Host

Ist der Proxy ein eigener Host im privaten Netz, muss SideBySide gezielt an die
private Adresse des Docker-/Arcane-Hosts gebunden werden:

```dotenv
SBS_BIND_IP=192.168.10.20
API_PORT=8000
WEB_PORT=8099
```

`SBS_BIND_IP` ist absichtlich **eine konkrete Hostadresse**. `0.0.0.0` ist fuer
diesen Aufbau nicht erforderlich und vergroessert die Exposition unnoetig.

Der Reverse-Proxy routet dann beispielsweise:

```text
https://sidebyside.example/
    -> http://192.168.10.20:8099

https://sidebyside.example/api/
    -> http://192.168.10.20:8000
```

In SideBySide werden dazu die oeffentliche Origin und die Proxy-Adressen gesetzt:

```dotenv
SBS_ENVIRONMENT=production
SBS_PUBLIC_BASE_URL=https://sidebyside.example
SBS_ALLOWED_HOSTS=["sidebyside.example","localhost","127.0.0.1"]
TRUSTED_PROXY_IPS=192.168.10.30,192.168.10.31
```

`TRUSTED_PROXY_IPS` enthaelt nur Adressen bzw. den kleinsten CIDR-Bereich, aus
dem der Reverse-Proxy die API tatsaechlich erreicht. Niemals `*` verwenden.

## Web-Referenzflow

Der aktuelle Web-Referenzflow benoetigt noch eine vorhandene Space-UUID als
Build-Konfiguration:

```dotenv
SBS_WEB_SPACE_ID=<space-uuid>
```

Die UUID ist kein Secret. Sie wird beim Vite-Build in das Web-Bundle
eingebettet. Nach einer Aenderung reicht deshalb ein Container-Restart nicht;
das Web-Image muss neu gebaut werden.

## Pruefung nach dem Deploy

Vom Reverse-Proxy-Host bzw. aus demselben privaten Netz kann zuerst der
Webdienst geprueft werden:

```bash
curl --fail http://<docker-host>:<WEB_PORT>/healthz
```

Die produktive API wird ueber den echten TLS-Pfad geprueft:

```bash
curl --fail https://sidebyside.example/api/v1/health/ready
```

Ueber die oeffentliche Origin sollten beide Ziele funktionieren:

```bash
curl --fail https://sidebyside.example/
curl --fail https://sidebyside.example/api/v1/health/ready
```

Die Readiness-Antwort der API lautet im Normalfall:

```json
{"status":"ok","database":"ok"}
```

## Reuse-Pruefung

Geprueft wurden ein eigener Arcane-Synchronisationsmechanismus, publizierte
Registry-Images und die vorhandenen Docker-/Compose-Bordmittel. Gewaehlt wurden
native Git-Build-Kontexte, weil sie das konkrete Workspace-Problem ohne neue
Runtime-Komponente oder Provider-Abstraktion loesen.

- Standard/Plattform: Docker Compose + BuildKit Git-Kontexte
- neue Runtime-Abhaengigkeiten: keine
- externer Provider: keiner; Git-Hosting ist nur Quelltransport beim Build
- Privacy/Nutzdaten: keine SideBySide-Nutzdaten verlassen durch diesen Schritt
  den Host
- Kosten: keine zusaetzlichen SideBySide-Laufzeitkosten
- Fallback: vollstaendiger Checkout mit `compose.yaml`; spaeter optional
  versionierte Registry-Images, falls Remote-Git-Builds betrieblich ungeeignet
  werden
