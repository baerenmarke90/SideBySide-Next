# Arcane Deployment

Diese Hinweise ergaenzen `SELF-HOSTING.md` fuer Installationen, bei denen Arcane die `compose.yaml` verwaltet und ein separater TLS-Reverse-Proxy davorsteht.

## Zielbild

Der Reverse-Proxy ist der einzige oeffentliche TLS-Endpunkt. Er routet auf derselben oeffentlichen Origin zwei interne Ziele:

| Pfad | internes Ziel |
|---|---|
| `/api/` | SideBySide API auf `API_PORT` |
| alle anderen Pfade | SideBySide Web auf `WEB_PORT` |

Die `/api/`-Route muss **direkt** zur API gehen. In Produktion darf sie nicht zuerst durch den Web-Nginx laufen, weil sonst der vertrauenswuerdige TLS-Proxy-Hop fuer `X-Forwarded-Proto` verloren geht und die API externe HTTP-Anfragen mit `HTTPS_REQUIRED` ablehnt.

## Reverse-Proxy auf demselben Host

Der sichere Standard reicht aus:

```dotenv
SBS_BIND_IP=127.0.0.1
API_PORT=8000
WEB_PORT=8080
```

Der Proxy verwendet dann `127.0.0.1:<API_PORT>` und `127.0.0.1:<WEB_PORT>`.

## Reverse-Proxy auf einem anderen Host

Ist der Proxy ein eigener Host im privaten Netz, muss SideBySide gezielt an die private Adresse des Docker-/Arcane-Hosts gebunden werden:

```dotenv
SBS_BIND_IP=192.168.10.20
API_PORT=8000
WEB_PORT=8099
```

`SBS_BIND_IP` ist absichtlich **eine konkrete Hostadresse**. `0.0.0.0` ist fuer diesen Aufbau nicht erforderlich und vergroessert die Exposition unnoetig.

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

`TRUSTED_PROXY_IPS` enthaelt nur Adressen bzw. den kleinsten CIDR-Bereich, aus dem der Reverse-Proxy die API tatsaechlich erreicht. Niemals `*` verwenden.

## Git-Build-Kontexte in Arcane

Arcane-Installationen, die nur die `compose.yaml` in ein Projektverzeichnis kopieren, haben die lokalen Verzeichnisse `./backend` und `./web` dort nicht automatisch zur Verfuegung. Dann muessen beide Build-Kontexte auf Git zeigen:

```dotenv
SBS_BACKEND_BUILD_CONTEXT=https://github.com/baerenmarke90/SideBySide-Next.git#main:backend
SBS_WEB_BUILD_CONTEXT=https://github.com/baerenmarke90/SideBySide-Next.git#main:web
```

Der Arcane-GitOps-Clone interpretiert einen nackten Commit-SHA in diesem Ref-Feld derzeit als Branch-Ref (`refs/heads/<sha>`). Ein SHA kann deshalb mit `couldn't find remote ref` scheitern. Fuer Tests ist `main` verwendbar; fuer reproduzierbare Produktion ist ein unveraenderlicher Release-Tag vorzuziehen.

## M2-Referenzflow

Der aktuelle Web-Referenzflow benoetigt noch eine vorhandene Space-UUID als Build-Konfiguration:

```dotenv
SBS_WEB_SPACE_ID=<space-uuid>
```

Die UUID ist kein Secret. Sie wird beim Vite-Build in das Web-Bundle eingebettet. Nach einer Aenderung reicht deshalb ein Container-Restart nicht; das Web-Image muss neu gebaut werden.

Zum Nachschlagen einer vorhandenen Space-ID:

```bash
psql -U sidebyside -d sidebyside -c "SELECT id, created_at FROM spaces;"
```

## Pruefung nach dem Deploy

Vom Reverse-Proxy-Host bzw. aus demselben privaten Netz kann zuerst die Erreichbarkeit des Webdienstes geprueft werden:

```bash
curl --fail http://<docker-host>:<WEB_PORT>/healthz
```

Die produktive API sollte dagegen ueber den echten TLS-Pfad geprueft werden:

```bash
curl --fail https://sidebyside.example/api/v1/health/ready
```

Das ist absichtlich nicht dasselbe wie `curl http://<docker-host>:<API_PORT>/...`: ein direkter HTTP-Aufruf mit einer Nicht-Loopback-Adresse besitzt keinen vertrauenswuerdigen `X-Forwarded-Proto: https`-Hop und muss in Produktion mit `HTTPS_REQUIRED` scheitern.

Soll der interne Proxy-Hop selbst diagnostiziert werden, kann die Anfrage **vom tatsaechlich als `TRUSTED_PROXY_IPS` eingetragenen Proxy-Host** mit denselben Forwarded-Informationen simuliert werden:

```bash
curl --fail \
  -H 'Host: sidebyside.example' \
  -H 'X-Forwarded-Proto: https' \
  http://<docker-host>:<API_PORT>/api/v1/health/ready
```

Ueber die oeffentliche Origin sollten damit beide Ziele funktionieren:

```bash
curl --fail https://sidebyside.example/
curl --fail https://sidebyside.example/api/v1/health/ready
```

Die Readiness-Antwort der API lautet im Normalfall:

```json
{"status":"ok","database":"ok"}
```

Bei einem Login darf die API in Produktion nicht `HTTPS_REQUIRED` melden. Tritt dieser Fehler auf, zuerst pruefen, ob `/api/` im Reverse-Proxy wirklich direkt zur API zeigt und ob der Proxy `X-Forwarded-Proto: https` neu setzt.

## Reuse-Pruefung

Diese Arcane-Anpassung baut keinen eigenen Deployment-Orchestrator. Sie nutzt weiterhin Docker-Compose-Port-Bindings, Git-Build-Kontexte und die vorhandene Reverse-Proxy-/Forwarded-Header-Unterstuetzung. Es kommt keine neue Runtime-Abhaengigkeit und kein externer Provider hinzu.
