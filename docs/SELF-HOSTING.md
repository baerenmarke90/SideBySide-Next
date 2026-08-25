# Sicherer Self-Hosted-Betrieb

## Zwei Betriebsarten

Der mitgelieferte Compose-Stack kennt zwei Betriebsarten, und der Unterschied
ist kein Detail:

| | lokaler Testbetrieb | Produktionsbetrieb |
|---|---|---|
| `SBS_ENVIRONMENT` | `development` (Standard) | `production` |
| Cursor-Signing-Key | lokaler Rueckfallwert | Pflicht, mindestens 32 Zeichen |
| Ausgehende Post | landet im Log | `smtp` oder `none`, kein `log` |
| `SBS_PUBLIC_BASE_URL` | `http://localhost:8000` | muss `https://` sein |
| HTTPS-Zwang, Host-Pruefung | aus | an |
| Schema-Auskunft `/docs` | offen | geschlossen |

Der Standard ist der Testbetrieb. Das ist eine bewusste Entscheidung
([ADR 0002](decisions/0002-self-hosted-first-start-mode.md)): Ein Erststart
soll ohne SMTP-Zugang und ohne HTTPS-Domain moeglich sein. Die API ist dabei
ausschliesslich an `127.0.0.1` gebunden und damit auch dann nicht aus LAN oder
Internet erreichbar, wenn die Firewall des Hosts zu offen konfiguriert ist.

Die Anwendung sagt bei jedem Start, in welcher Betriebsart sie laeuft. Im
Testbetrieb ist das eine Warnung in `docker compose logs api`.

## Lokaler Test

```bash
cp .env.example .env
# Mindestens POSTGRES_PASSWORD durch ein langes, zufaelliges Geheimnis ersetzen.
# SBS_BOOTSTRAP_TOKEN in .env auf ein separat erzeugtes Geheimnis mit
# mindestens 32 Zeichen setzen.
docker compose config --quiet
docker compose up -d --wait --wait-timeout 300
```

`API_PORT=8000` ist nur der Vorgabewert. Der Port muss auf dem Docker-Host frei
sein. Ist er bereits durch einen anderen Dienst belegt, vor dem Start in `.env`
einen freien Port waehlen, zum Beispiel:

```dotenv
API_PORT=8010
```

Das aendert nur den Host-Port. Die API lauscht im Container weiterhin auf
Port 8000. Ein belegter Host-Port darf nicht durch einen zweiten Dienst geteilt
werden; `docker compose up` muss in diesem Fall eindeutig fehlschlagen.

Den tatsaechlich veroeffentlichten Port zeigt Compose an:

```bash
docker compose port api 8000
```

Die Ausgabe muss an `127.0.0.1` gebunden sein. Eine Ausgabe mit `0.0.0.0`, `::`
oder einer unerwarteten externen Adresse ist fuer den Standardbetrieb nicht
zulaessig.

Nach dem Start wird die Betriebsbereitschaft geprueft, nicht nur der laufende
HTTP-Prozess:

```bash
api_port=$(docker compose port api 8000 | awk -F: '{print $NF}')
curl --fail "http://127.0.0.1:${api_port}/api/v1/health/ready"
```

Erwartet wird:

```json
{"status":"ok","database":"ok"}
```

Dieser Stand ist zum Ausprobieren gedacht und nicht zum Veroeffentlichen. Wer
die Instanz erreichbar machen will, arbeitet vorher die Checkliste unten ab.

Noch einmal getrennt davon ist der Entwicklungsablauf am Quellcode:
`deploy/docker-compose.dev.yml` startet nur PostgreSQL. Das lokal gestartete
Uvicorn ist ein Entwicklungsserver und keine Vorlage fuer einen extern
erreichbaren produktiven Dienst.

## Compose-Netzwerk und Readiness

`postgres`, `migrate`, `api` und `worker` sind in `compose.yaml` explizit an
dasselbe projektbezogene Bridge-Netzwerk `app` angeschlossen. Der konkrete
Docker-Netzwerkname enthaelt zusaetzlich den Compose-Projektnamen, damit mehrere
SideBySide-Stacks auf demselben Host nicht kollidieren.

Die Datenbank-URL verwendet absichtlich den Compose-Service-Namen
`postgres:5432`. Keine Container-ID, feste Docker-IP und kein Host-Port gehoeren
in `SBS_DATABASE_URL`.

Nach einem Deployment kann die Docker-DNS-Verbindung direkt aus der API
geprueft werden:

```bash
docker compose exec -T api python -c \
  'import socket; print(socket.gethostbyname("postgres"))'
```

Zusatzkontrolle des tatsaechlichen Netzwerkzustands:

```bash
api_id=$(docker compose ps -q api)
docker inspect "$api_id" --format '{{json .NetworkSettings.Networks}}'
```

Ein laufender API-Container mit leerem Ergebnis `{}` ist **nicht**
betriebsbereit. In diesem Zustand kann Docker-DNS `postgres` nicht aufloesen.

SideBySide trennt zwei Gesundheitsfragen:

- `/api/v1/health` ist reine **Liveness**: der API-Prozess antwortet.
- `/api/v1/health/ready` ist **Readiness**: die API kann auch PostgreSQL
  erreichen und einen echten `SELECT 1` ausfuehren.

Der Docker-Healthcheck verwendet bewusst die Readiness-Route. Dadurch meldet
`docker compose up -d --wait` einen fehlenden Datenbank-/Netzwerkpfad als
Deploymentfehler, auch wenn Uvicorn selbst noch laeuft. Docker Compose startet
einen Prozess nicht allein wegen des Status `unhealthy` neu; ein kurzfristiger
Datenbankausfall bleibt damit von einem Prozessabsturz getrennt.

## Checkliste fuer den Produktionsbetrieb

Vor dem ersten oeffentlichen Start in `.env` setzen:

```dotenv
SBS_ENVIRONMENT=production
SBS_CURSOR_SIGNING_KEY=...        # openssl rand -base64 48
SBS_PUBLIC_BASE_URL=https://deine-domain.example
SBS_ALLOWED_HOSTS=["deine-domain.example"]
TRUSTED_PROXY_IPS=...             # kleinster IP-Bereich des Reverse-Proxys

# Mit Mailserver:
SBS_MAIL_TRANSPORT=smtp
SBS_MAIL_FROM=no-reply@deine-domain.example
SBS_SMTP_HOST=smtp.deine-domain.example

# Oder ohne Mailserver - siehe unten:
# SBS_MAIL_TRANSPORT=none
```

Fehlt der Cursor-Signing-Key oder ist die Basisadresse kein `https://`, startet
die Anwendung nicht. Das ist Absicht und wird nicht umgangen: Der
Cursor-Signing-Key schuetzt die Integritaet opaker Pagination-Cursor, und ein
Anmeldelink ueber Klartext-HTTP ist ein uebernehmbarer Zugang.

### Betrieb ohne Mailserver

Ein SMTP-Zugang ist **keine** Startvoraussetzung. Mit
`SBS_MAIL_TRANSPORT=none` laeuft die Instanz ohne Mailweg:

- Magic Link, Passwort-Recovery und Adressbestaetigung antworten mit
  `503 MAIL_TRANSPORT_UNAVAILABLE` statt eine Nachricht zu versprechen, die
  nie ankommt.
- Anmeldung laeuft ueber Passwort, Passkey/WebAuthn und OIDC weiter.
- Wer sein Passwort vergisst und keinen Passkey hat, kommt ohne Mailweg nicht
  mehr selbst in sein Konto. Das ist der Preis dieser Betriebsart.

Was Produktion **nicht** akzeptiert, ist `SBS_MAIL_TRANSPORT=log`. Dabei
stuenden gueltige Einmal-Token im Log der API und damit in jeder
Log-Aggregation und jedem Backup davon. Der Unterschied zu `none` ist nicht
formal: dort verlaesst kein Token das System.

Danach `docker compose up -d --force-recreate --wait --wait-timeout 300` und
pruefen, dass `docker compose logs api` den Produktionsbetrieb meldet.

## Medienablage

`SBS_MEDIA_STORE=local` ist der Standard. API und Worker benutzen dabei das
private Compose-Volume `media_data`; Dateisystempfade werden nicht an Clients
ausgegeben.

Fuer einen S3-kompatiblen Objektspeicher wird in `.env` stattdessen gesetzt:

```dotenv
SBS_MEDIA_STORE=s3
SBS_S3_ENDPOINT=https://s3.example.com
SBS_S3_REGION=eu-central-1
SBS_S3_BUCKET=sidebyside-private
SBS_S3_ACCESS_KEY_ID=...
SBS_S3_SECRET_ACCESS_KEY=...
# Nur bei temporaeren Provider-Credentials:
# SBS_S3_SESSION_TOKEN=...
```

Der Endpoint ist eine S3-API-Origin ohne eingebettete Zugangsdaten oder
Unterpfad. Fuer produktiven Verkehr ueber nicht vollstaendig vertrauenswuerdige
Netze muss HTTPS verwendet werden. Der Bucket selbst bleibt privat: keine
Public ACLs, keine anonyme Read-Policy und keine statische Website-Freigabe.
Die Server-Credentials benoetigen fuer den verwendeten Bucket/Key-Prefix nur
die Objektoperationen GET/PUT/HEAD/DELETE; ein oeffentliches Bucket ist dafuer
nicht notwendig.

Bei S3 lädt der Client mit einer serverseitig signierten PUT-Capability direkt
auf genau den erzeugten Storage Key. Die Upload-URL gilt exakt 10 Minuten und
ist mit `If-None-Match: *` gegen ein spaeteres Ueberschreiben desselben Objekts
gebunden. Ein Provider-Upload setzt das Attachment nicht auf `READY`:
`finalizeUpload` bestaetigt das Objekt serverseitig und die vorhandene
Validierung entscheidet weiterhin allein ueber `READY`.

Lesen wird erst nach der normalen Membership-/Parent-Autorisierung freigegeben.
Die signierte GET-URL gilt exakt 5 Minuten und nur fuer dieses Objekt. Bereits
ausgestellte URLs koennen nach einem Membership- oder Privacy-Entzug technisch
bis zum Ende dieser 5 Minuten weiter funktionieren. Das ist der dokumentierte
Privacy-Trade-off des S3-Adapters; neue URLs werden nach dem Entzug nicht mehr
ausgestellt.

Descriptor-Antworten und gespeicherte Objekte tragen `Cache-Control: private,
no-store`; die API setzt fuer Descriptoren zusaetzlich `Referrer-Policy:
no-referrer`. Presigned URLs, Signaturen und Storage-Credentials duerfen nicht
in Access-Logs, Analytics, Supportdaten oder dauerhafte Clientcaches uebernommen
werden.

Bei einem Browser-Client braucht der Bucket eine enge CORS-Regel fuer die
konkrete SideBySide-Origin. Fuer den Upload sind `PUT` und die Header
`Content-Type`, `Cache-Control` und `If-None-Match` erforderlich; fuer direkte
Reads `GET`/`HEAD`. Keine CORS-Regel ersetzt die private Bucket-Policy oder die
serverseitige Autorisierung.

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
demselben Host oder in einem kontrollierten privaten Netz. Der sichere
Standard bindet die API in `compose.yaml` nur an Loopback. Ein Reverse-Proxy auf
demselben Host kann daher an `http://127.0.0.1:<API_PORT>` weiterleiten.

Steht der Reverse-Proxy auf einem **anderen** Host, ist Loopback dort nicht
erreichbar. Dann braucht das Deployment eine bewusst konfigurierte, auf das
private Netz begrenzte Weiterleitung statt einer pauschalen Freigabe auf
`0.0.0.0`. Diese Freigabe gehoert zur Hoster-Konfiguration und darf nicht
versehentlich durch den Standard-Compose-Stack entstehen.

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

Mit `SBS_ENVIRONMENT=production` startet die API nicht, wenn der Log-Versand
stehen bleibt oder die Basisadresse kein `https://` ist. Sonst stuenden
gueltige Anmeldelinks im Log.

Wer keinen Mailserver hat, setzt `SBS_MAIL_TRANSPORT=none` statt `log` - siehe
[Betrieb ohne Mailserver](#betrieb-ohne-mailserver).

## Smoke-Test nach Aenderungen

```bash
# Tatsaechlichen Host-Port ermitteln.
api_port=$(docker compose port api 8000 | awk -F: '{print $NF}')

# Liveness: der API-Prozess antwortet.
curl --fail "http://127.0.0.1:${api_port}/api/v1/health"

# Readiness: Docker-DNS und PostgreSQL funktionieren ebenfalls.
curl --fail "http://127.0.0.1:${api_port}/api/v1/health/ready"

# Der API-Container kann den Compose-Service postgres aufloesen.
docker compose exec -T api python -c \
  'import socket; print(socket.gethostbyname("postgres"))'

# Die oeffentliche Adresse muss HTTPS verwenden.
curl --fail https://sidebyside.example.com/api/v1/health

# Klartext darf extern keine erfolgreiche API-Antwort liefern.
curl --fail http://sidebyside.example.com/api/v1/health && exit 1 || true
```

Der Container-Healthcheck greift intern auf `127.0.0.1` zu und bewertet
`/health/ready`. Damit wird ein API-Prozess ohne funktionsfaehigen
Datenbankpfad als `unhealthy` sichtbar, ohne die separate Liveness-Route zu
veraendern.
