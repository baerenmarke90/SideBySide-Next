# Sicherer Self-Hosted-Betrieb

## Lokaler Standard

Der mitgelieferte Compose-Stack veroeffentlicht die API ausschliesslich auf
`127.0.0.1`. Damit ist der erste Start auch dann nicht aus LAN oder Internet
erreichbar, wenn die Firewall des Hosts zu offen konfiguriert ist.

```bash
cp .env.example .env
# Mindestens POSTGRES_PASSWORD durch ein langes, zufaelliges Geheimnis ersetzen.
docker compose config --quiet
docker compose up -d
curl --fail http://127.0.0.1:8000/api/v1/health
```

`docker compose port api 8000` muss eine Bindung an `127.0.0.1` melden. Eine
Ausgabe mit `0.0.0.0`, `::` oder nur `:8000` ist fuer den produktiven Betrieb
nicht zulaessig.

Der Entwicklungsablauf ist davon getrennt: `deploy/docker-compose.dev.yml`
startet nur PostgreSQL. Das lokal gestartete Uvicorn ist ein Entwicklungsserver
und keine Vorlage fuer einen extern erreichbaren produktiven Dienst.

## Zugriff aus LAN oder Internet

Externer Zugriff erfolgt ausschliesslich ueber einen TLS-Reverse-Proxy auf
demselben Host oder in einem kontrollierten privaten Netz. Der Proxy terminiert
HTTPS und leitet intern an `http://127.0.0.1:8000` weiter. Die API-Portbindung in
`compose.yaml` bleibt dabei unveraendert auf Loopback.

In `.env` werden zusaetzlich gesetzt:

```dotenv
SBS_ALLOWED_HOSTS=["sidebyside.example.com","localhost","127.0.0.1"]
TRUSTED_PROXY_IPS=192.0.2.10
```

- `SBS_ALLOWED_HOSTS` ist eine JSON-Liste der oeffentlichen API-Hostnamen.
  Ein globales `"*"` wird in Produktion abgelehnt.
- `TRUSTED_PROXY_IPS` ist die genaue Adresse oder der kleinste CIDR-Bereich,
  aus dem der Proxy den API-Container erreicht. Niemals `*` verwenden.
- Der Proxy setzt `Host`, `X-Forwarded-For` und `X-Forwarded-Proto: https` neu;
  vom Client angelieferte Forwarded Header werden nicht ungeprueft übernommen.
- TLS-Zertifikate muessen gueltig sein und automatisch erneuert werden.

Die Anwendung lehnt einen erlaubten externen Host trotzdem ab, solange das von
Uvicorn bereinigte Request-Scheme nicht `https` ist. Ein normaler Client kann
diese Pruefung nicht allein durch einen gefaelschten Forwarded Header umgehen.

## Smoke-Test nach Aenderungen

```bash
# Lokal bleibt der Healthcheck erreichbar.
curl --fail http://127.0.0.1:8000/api/v1/health

# Die oeffentliche Adresse muss HTTPS verwenden.
curl --fail https://sidebyside.example.com/api/v1/health

# Klartext darf extern keine erfolgreiche API-Antwort liefern.
curl --fail http://sidebyside.example.com/api/v1/health && exit 1 || true
```

Der Container-Healthcheck greift intern auf `127.0.0.1` zu und funktioniert
daher unabhaengig von TLS-Terminierung und oeffentlichem Hostnamen.
