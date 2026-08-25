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

Vor der serverseitigen Medienverarbeitung wird bei S3 die Objektgroesse per
`HEAD`/`Content-Length` geprueft. Der anschliessende GET wird streamend gelesen;
der Worker kopiert nur bis zur fachlichen Grenze plus einem Pruefbyte. Stimmen
Provider-Groesse und tatsaechlich gelesene Groesse nicht ueberein, scheitert die
Validierung fail-closed.

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

## Videoverarbeitung mit ffmpeg

Das offizielle Docker-/Compose-Deployment bringt `ffmpeg` und `ffprobe` bereits
im Backend-Image mit. Auf dem Docker-Host muss und soll dafuer kein separates
ffmpeg installiert werden. API, Migration und Worker verwenden dasselbe
reproduzierbare Image; fremde Videodateien werden nur im Worker interpretiert.

Die Produktionsversion des Debian-Pakets ist im Dockerfile exakt gepinnt auf:

```text
7:7.1.5-0+deb13u1
```

Die CI prueft sowohl den Pin als auch den Debian Security Tracker. Ein Upgrade
der Systembinaries erfolgt deshalb als bewusste Repository-Aenderung und nicht
ueber ein unversioniertes Paketupdate beim Containerstart.

Wer Video in einer Self-Hosted-Installation bewusst nicht anbieten will, setzt:

```dotenv
SBS_FFMPEG_ENABLED=false
```

`true` ist der Standard. Bei `false` werden neue Video-Uploads fail-closed
abgewiesen und bereits eingereihte Videojobs starten ebenfalls kein
ffmpeg/ffprobe mehr. Bilder und der restliche Dienst bleiben aktiv. Die
Binaries bleiben absichtlich im Image; der Schalter erzeugt keinen zweiten
Buildpfad.

Der Worker ist im mitgelieferten Compose-Stack als zweite Schutzschicht fuer
unvertrauenswuerdige Medien auf folgende Obergrenzen gesetzt:

- 1 CPU,
- 1 GiB RAM,
- 64 PIDs.

Die ffmpeg-/ffprobe-Kindprozesse besitzen zusaetzlich eigene CPU-, Wall-Clock-,
Adressraum-, Dateigroessen-, FD- und Core-Dump-Limits. Der validierte
Adressraum-Rahmen liegt bei 768 MiB pro Medienkindprozess. Diese Grenzen duerfen
bei einem eigenen Deployment nicht still entfernt werden.

Wer Backend/Worker ausserhalb des Docker-Images direkt aus dem Quellcode
startet und Video verarbeiten moechte, braucht kompatible Binaries unter
`/usr/bin/ffmpeg` und `/usr/bin/ffprobe`. Der reproduzierbare Produktionsnachweis
gilt fuer die oben gepinnte Debian-Version; andere lokale Versionen sind reine
Entwicklungsumgebungen und kein Ersatz fuer den Container-CI-Nachweis.

Details zu Format-, Metadaten- und Ressourcenregeln stehen in
[`m2/VIDEO-PROCESSING.md`](m2/VIDEO-PROCESSING.md).

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
