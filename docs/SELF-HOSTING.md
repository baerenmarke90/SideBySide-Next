# Sicherer Self-Hosted-Betrieb

## Lokaler Standard

Der mitgelieferte Compose-Stack veroeffentlicht die API ausschliesslich auf
`127.0.0.1`. Damit ist der erste Start auch dann nicht aus LAN oder Internet
erreichbar, wenn die Firewall des Hosts zu offen konfiguriert ist.

```bash
cp .env.example .env
# Mindestens POSTGRES_PASSWORD durch ein langes, zufaelliges Geheimnis ersetzen.
# SBS_BOOTSTRAP_TOKEN in .env auf ein separat erzeugtes Geheimnis mit
# mindestens 32 Zeichen setzen.
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

## Einmalige Erstregistrierung

Eine leere Instanz nimmt den ersten Account nur mit dem in der lokalen `.env`
gesetzten `SBS_BOOTSTRAP_TOKEN` an. Der Wert wird als `bootstrapToken` an
`POST /api/v1/auth/register` uebergeben. Er wird weder in der Datenbank
gespeichert noch von der Anwendung geloggt.

Fuer einen Start ohne vorhandene Benutzer gilt:

1. Ein zufaelliges Geheimnis mit mindestens 32 Zeichen erzeugen und nur in der
   nicht versionierten `.env` als `SBS_BOOTSTRAP_TOKEN` speichern.
2. Den Stack starten und die erste Registrierung lokal ueber `127.0.0.1`
   ausfuehren.
3. Nach erfolgreicher Registrierung `SBS_BOOTSTRAP_TOKEN` aus `.env` entfernen
   und den API-Container neu erstellen: `docker compose up -d --force-recreate api`.
4. Weitere Accounts ausschliesslich ueber Einladungen registrieren.

Die Datenbank speichert den erfolgreichen Abschluss dauerhaft. Derselbe oder
ein spaeter neu gesetzter Bootstrap-Wert kann danach keinen zweiten initialen
Owner erzeugen. Zwei parallele Erstregistrierungen werden in PostgreSQL
serialisiert; genau eine kann erfolgreich sein.

Das Geheimnis darf nicht in Shell-Historie, Screenshots, Support-Anfragen oder
Repository-Dateien gelangen. `.env` ist deshalb in `.gitignore` ausgeschlossen.

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

## Ausgehende E-Mail

Magic Link und Passwort-Wiederherstellung brauchen einen Mailweg. Im
Standard steht `SBS_MAIL_TRANSPORT=log`: die Nachricht landet im Log der
API, damit sich beides ohne Mailserver ausprobieren laesst.

Fuer den echten Betrieb wird ein SMTP-Server eingetragen:

```
SBS_MAIL_TRANSPORT=smtp
SBS_MAIL_FROM=no-reply@deine-domain.example
SBS_SMTP_HOST=smtp.deine-domain.example
SBS_SMTP_PORT=587
SBS_SMTP_USERNAME=...
SBS_SMTP_PASSWORD=...
SBS_PUBLIC_BASE_URL=https://deine-domain.example
```

`SBS_PUBLIC_BASE_URL` steht in jedem Link. Sie kommt bewusst aus der
Konfiguration und nicht aus dem Host-Header der Anfrage.

Mit `SBS_ENVIRONMENT=production` sind beide Einstellungen Pflicht: bleibt
der Log-Versand stehen oder ist die Basisadresse kein `https://`, startet
die API nicht. Sonst stuenden gueltige Anmeldelinks im Log.

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
