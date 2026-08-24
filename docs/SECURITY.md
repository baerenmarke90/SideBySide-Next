# Sicherheit

Sicherheit ist Release Gate, nicht Nacharbeit. Eine Funktion gilt nicht als
fertig, solange ihre Cross-Tenant- und Privacy-Tests fehlen.

## Zentrale Invariante: Tenant Isolation

Der Mandant heißt **Space**. Jeder gemeinsame Datensatz trägt genau eine
`space_id`.

Jeder Zugriff auf Space-Daten prüft vier Dinge:

1. authentifizierter Account
2. aktive Membership in genau diesem Space
3. die Ressource gehört tatsächlich diesem Space
4. gegebenenfalls zusätzliche Ressourcen-Berechtigung

**Es gibt keinen Datenzugriff allein anhand einer Ressourcen-ID.**

Für

```
GET /api/v1/spaces/{spaceId}/memories/{memoryId}
```

genügt es nicht, die Memory zu laden und ihre `space_id` mit dem Pfad zu
vergleichen — geprüft wird zuerst die Membership, dann wird innerhalb des
Spaces gesucht. Die Abfrage darf fremde Zeilen gar nicht erst laden.

## 404 statt 403

Bei privatsphäre-relevanten Ressourcen wird bewusst **404** geantwortet, wo
403 fachlich richtiger wäre. Ein 403 bestätigt die Existenz. Wer fremde IDs
durchprobiert, soll nicht erfahren, welche existieren.

## Privacy-Klassen

Jede Domäne ordnet ihre Daten einer Klasse zu. Eine implizite
Öffentlichkeit gibt es nicht.

| Klasse | Bedeutung |
|---|---|
| `SPACE_SHARED` | beide Partner des Space |
| `OWNER_ONLY` | nur der Eigentümer, niemals der Partner |
| `TEMPORARY_SHARED` | zeitlich begrenzt geteilt |
| `EPHEMERAL_CONTEXT` | kurzlebig, mit Ablauf |
| `SYSTEM_METADATA` | technisch, kein Nutzerinhalt |

`OWNER_ONLY` bedeutet: der Partner erhält den Inhalt über **keinen** Weg —
nicht per ID, nicht in Listen, nicht über Suche, Dashboard, Story,
Kommentare, Benachrichtigungen, Export oder eine indirekte Beziehung.

**Ausblenden im Client ist keine Durchsetzung.** Der Filter gehört in die
Abfrage. Ein Treffer, der entsteht und danach verworfen wird, ist bereits
ein Leck — er war im Speicher, im Log, in der Antwortgröße.

### Durchsetzung

Der Tenant Guard beantwortet, ob ein Account zu einem Space gehört. Die
Owner-/Privacy-Autorisierung in `sidebyside.authorization` beantwortet
danach, was er innerhalb dieses Space sehen und ändern darf. Beide
Bedingungen stehen gemeinsam in der Abfrage, nicht hinter ihr.

Owner-/autorenbezogene Domänen, die diese Grundlage verwenden, erben drei
Spalten — `space_id`, `owner_id`, `privacy_class` — und rufen `readable()`,
`require_readable()` oder `require_writable()` auf. Sie formulieren ihre
Sichtbarkeitsbedingung nicht selbst. Es gibt weder eine gemeinsame
Universal-Inhaltstabelle noch einen zweiten, handgeschriebenen Guard je
Domäne.

Space-eigene gemeinsame Ressourcen ohne fachlichen Eigentümer werden nicht
künstlich in dieses Owner-Modell gezwungen. Für sie bleibt der Tenant Guard
die gemeinsame Basis; zusätzliche Schreibregeln kommen aus der jeweiligen
Domäne.

Serverseitig erzwingbar sind derzeit `SPACE_SHARED` und `OWNER_ONLY`. Nur
diese beiden sind auch speicherbar: eine Klasse ohne Regel erzeugte Zeilen,
deren Schutz niemand einlöst. Eine Klasse ohne Regel ergibt in der Abfrage
`false` — ein Versäumnis macht Inhalte unsichtbar, nicht sichtbar. Eine
weitere Klasse aufzunehmen heißt deshalb immer dreierlei zugleich: Regel,
Freigabe des Wertebereichs und Migration.

`SPACE_SHARED` beschreibt Sichtbarkeit, nicht pauschal das Schreibrecht.
Bei owner-/autorenbezogenen Ressourcen gilt derzeit auch für
`SPACE_SHARED`: der Eigentümer bzw. Autor bearbeitet, der Partner liest.
`SpaceProfile` ist die Gegenklasse: Es gehört dem Space, besitzt keine
`owner_id` und darf von beiden aktiven Partnern geändert werden. Dafür wird
bewusst kein `PrivateResourceMixin` erfunden.

Die Ablehnung ist zweigeteilt, und der Unterschied ist Absicht:

| Lage | Antwort |
|---|---|
| nicht lesbar — fremder Space, fremdes `OWNER_ONLY`, unbekannte oder fehlgeformte ID | 404, in allen Fällen wortgleich |
| lesbar, aber nicht änderbar — ownerbezogene geteilte Zeile eines anderen Eigentümers | 403 |

Ein 404 auf etwas, das der Aufrufer sich gerade hat anzeigen lassen, wäre
kein Schutz, sondern eine Unwahrheit. Ein 403 auf etwas, das er nicht sehen
darf, wäre die Existenzauskunft, die `OWNER_ONLY` gerade verhindern soll.

## Authentifizierung

Android und andere native Clients nutzen Bearer Tokens, kein
Web-Session-Cookie.

```
Authorization: Bearer <access-token>
```

Access Token kurzlebig (Größenordnung 15 Minuten). Refresh Tokens werden
**nur gehasht** persistiert, rotieren bei Gebrauch, und ein
Wiederverwendungsversuch soll erkennbar sein — er deutet auf einen
gestohlenen Token.

`DeviceSession` hält `refresh_token_hash`, Gerätename, Plattform,
`last_used_at`, `expires_at`, `revoked_at`. Sitzungen sind einzeln
widerrufbar.

Cloud setzt auf E-Mail-Verifikation, Magic Link, Passkey und Recovery —
ohne Passwortpflicht. Self-Hosted zusätzlich lokaler Passwortlogin und
OIDC, womit ein externer Provider später ohne Sonderweg möglich ist.

Bei OIDC ist das externe Konto ausschließlich durch `(issuer, subject)`
bestimmt. Ein frei konfigurierbarer `connection_id` wählt den Adapter; Pocket
ID ist damit eine normale OIDC-Verbindung und kein Sonderfall. Ein neuer
Eintrag darf erst nach vollständiger Prüfung von Discovery, Signatur und
Claims gespeichert werden.

Passkeys liegen als eigene WebAuthn-Credentials vor: global eindeutige
Credential-ID, Public Key, Signaturzähler, AAGUID, Transports sowie
Discoverable-/Backup-Metadaten. Der private Schlüssel bleibt im
Authenticator und wird vom Server weder empfangen noch gespeichert.

E-Mail-Verifikation, Magic Link und Account Recovery verwenden getrennte
Tabellen und getrennte Konsumfunktionen. Jeder Nachweis ist zufällig,
kurzlebig, widerrufbar, genau einmal verwendbar und nur als Hash
persistiert. Ein Token eines Ablaufs kann deshalb nicht in einem anderen
Ablauf eingelöst werden. Die eigentlichen OIDC-/WebAuthn-Adapter und
öffentlichen Cloud-Auth-Endpunkte sind noch nicht implementiert; die lokale
Argon2-Anmeldung bleibt davon unabhängig erhalten.

Der erste Self-Hosted-Account braucht einen einmaligen geheimen Bootstrap-
Nachweis. PostgreSQL serialisiert konkurrierende Erstregistrierungen; nach
dem ersten Erfolg bleibt der Bootstrap dauerhaft geschlossen und alle
weiteren Registrierungen brauchen eine Einladung. Der geheime Wert wird
nicht persistiert oder geloggt.

### Refresh-Token-Familie

Die `DeviceSession` ist zugleich die Token-Familie: jeder Refresh Token, der
aus einer Anmeldung hervorgeht, gehört zu genau dieser Sitzung. Jede
verbrauchte Generation bleibt als `ConsumedRefreshToken` mit ihrem Hash der
Familie zugeordnet, solange die Sitzung lebt.

Damit ist die Erkennung nicht auf die unmittelbar vorherige Generation
beschränkt. Taucht nach `T0 → T1 → T2` erneut `T0` auf, ist es kein bloß
ungültiger Token, sondern eine Kopie: der rechtmäßige Client hätte `T2`.
Die Sitzung wird deshalb dauerhaft widerrufen — auch dann, wenn die Anfrage
selbst mit 401 endet und zurückgerollt wird.

Der Widerruf setzt einen echten Token dieser Familie voraus. Ein beliebiger
unbekannter Wert widerruft nichts, sonst könnte jeder eine fremde Sitzung
beenden. Nach außen sind unbekannt, abgelaufen, widerrufen und als Replay
erkannt nicht unterscheidbar.

Die Historie hält ausschließlich Hashes und ist damit keine zweite Quelle
für Anmeldenachweise. Sie verschwindet mit der Sitzung und wird für
beendete Sitzungen nach einer Aufbewahrungsfrist geräumt; laufende
Sitzungen behalten ihre Historie, denn sie *ist* die Erkennung.

### Die Aufbewahrung wird tatsächlich ausgeführt

Eine Frist, die nur als Funktion im Code steht, ist keine Frist. Der Job
`security_retention` führt `sessions.prune_replay_history()` und
`rate_limit.prune()` regelmäßig aus — als gewöhnliche Aufgabe in der
PostgreSQL-Warteschlange, die sich nach getaner Arbeit selbst neu einstellt
(Standardtakt: alle sechs Stunden, deutlich kürzer als die kürzeste Frist).

Kein zweiter Scheduler und kein Cron im Container: die Warteschlange liegt
ohnehin in der Datenbank und übersteht einen Neustart. Eingeplant wird unter
einer Advisory Lock, damit zwei gleichzeitig startende Worker nicht beide
eine Aufgabe einstellen; ein doppelter Lauf wäre allerdings ohnehin harmlos,
weil beide Prune-Funktionen idempotent sind.

Gibt eine Aufgabe endgültig auf, hängt keine Kette mehr an ihr. Der Worker
sieht deshalb zusätzlich regelmäßig nach, ob überhaupt ein Lauf ansteht, und
plant ihn sonst neu — ein dauerhaft ausbleibender Cleanup soll nicht still
passieren.

**Betriebliche Folge:** Die Retention hängt am laufenden Worker-Prozess
(`python -m sidebyside.jobs.runner`, im Compose-Setup der Dienst `worker`).
Wer nur die API betreibt, hält seine Daten länger als dokumentiert.

### Zwei Ablaufzeitpunkte je Sitzung

Damit die Familie und mit ihr die Historie tatsächlich endlich ist, trägt
`DeviceSession` zwei verschiedene Grenzen:

| Feld | Bedeutung | Wird verlängert? |
|---|---|---|
| `expires_at` | gleitendes Fenster gegen Untätigkeit | ja, bei jeder Rotation |
| `absolute_expires_at` | harte Obergrenze ab Anmeldung | **nein** |

Das gleitende Fenster allein wäre keine Begrenzung: Wer regelmäßig
erneuert, schiebt es beliebig weit vor sich her. Eine dauerhaft genutzte
Sitzung liefe dann unbegrenzt weiter und sammelte pro Rotation eine weitere
Zeile Historie, die nie geräumt würde.

Die absolute Grenze steht ab der Anmeldung fest. Keine Rotation verschiebt
sie. Ist sie erreicht, hilft kein Refresh mehr — es braucht eine neue
Anmeldung und damit eine neue Familie. Auch ein kurz zuvor ausgestellter
Access Token endet an dieser Grenze, sonst wäre sie keine.

`expires_at` wird nie über `absolute_expires_at` hinaus gesetzt. Der Client
erfährt über `refreshExpiresAt` also den Zeitpunkt, der tatsächlich gilt.

### Begrenzte Rotationsrate

Die absolute Grenze macht das Wachstum der Historie endlich, aber nicht
langsam: ein Client mit gültigem Token könnte in einer engen Schleife
innerhalb kurzer Zeit sehr viele Generationen erzeugen. `/api/v1/auth/refresh`
hat deshalb ein eigenes Budget (`rate_limit.REFRESH`, derzeit 20 Rotationen
je 15 Minuten). Das ist ein Vielfaches der regulären Rate — ein Access Token
lebt 15 Minuten, ein normaler Client erneuert also etwa einmal pro Fenster.

Gezählt wird gegen die **`DeviceSession`**, nicht gegen den Tokenwert. Der
wechselt bei jeder Rotation; eine Begrenzung darauf wäre nach genau einem
Versuch wieder bei null. Andere Sitzungen desselben Accounts bleiben
unberührt.

Anders als bei der Anmeldung zählen hier die **erfolgreichen** Versuche, und
der Zähler wird nach einem Erfolg nicht geräumt — der Erfolg ist ja gerade
das, was begrenzt wird.

Die Prüfung sitzt hinter der Token-Prüfung. Eine 429 bekommt nur, wer den
aktuellen Token der Familie besitzt; unbekannte, alte und widerrufene Tokens
enden unverändert bei 401 und werden nicht gezählt. Damit wird die Bremse
nicht zur Auskunft darüber, ob es eine Sitzung gibt.

Bis dahin bleibt **jede** Generation der Familie zuordenbar. Die Grenze
verkürzt die Historie nicht und ist ausdrücklich kein Zeitfenster, durch
das alte Tokens wieder aus der Erkennung fallen.

## Invitations

Einladungstoken: zufällig, ausreichend Entropie, **nur gehasht**
gespeichert, mit Ablaufdatum, widerrufbar, genau einmal verwendbar.

Zu testen: abgelaufen, widerrufen, wiederverwendet, Space bereits voll,
Wettlauf zweier gleichzeitiger Annahmen, ungültiger Token.

## Medien

Cloud-Medien sind nicht öffentlich. Lesen erfolgt über eine autorisierte
Route oder eine kurzlebige signierte URL.

Storage Keys werden **niemals** aus Benutzer-Dateinamen abgeleitet:

```
spaces/{spaceUuid}/attachments/{attachmentUuid}/original
```

Beim Upload werden tatsächlicher MIME-Type, Größe, erlaubter Medientyp,
Bilddimensionen und Space-Zuordnung geprüft — der vom Client behauptete
Content-Type genügt nicht.

## Verpflichtende Testfälle

- Cross-Tenant / IDOR
- Leck privater Ressourcen
- fehlgeformte IDs
- Missbrauch von Einladungen
- Token Replay
- Refresh Rotation
- widerrufene Sitzungen
- Rate Limiting
- paralleler und wiederverwendeter Self-Hosted-Bootstrap
- Upload-Missbrauch, bösartige Medien
- XSS, CSRF bei Browser-Flows, SQL Injection
- Ablauf signierter URLs
- Autorisierung von Backups
- Privacy-Lecks in der Suche

### Tenant-Matrix

| Zugriff | Erwartung |
|---|---|
| Account A auf Space A (Mitglied) | erlaubt |
| Account B auf Space A (Mitglied) | erlaubt |
| Account C auf Space B, greift auf Space A | niemals |
| anonym | niemals |

### Private Isolation

Für jede `OWNER_ONLY`-Domäne separat geprüft über: Liste, Suche, Dashboard,
Timeline, Benachrichtigungen, Export, Beziehungen, Attachments sowie
Update und Delete.

## Logging

Erlaubt: `request_id`, `account_id`, `space_id`, Route, Dauer, Status,
Fehlercode.

Nicht geloggt: Passwörter, Bearer-/Refresh-/Magic-Link-/Verifikations- oder
Recovery-Tokens, OIDC-Tokens und WebAuthn-Challenges; außerdem Inhalte von
Memories, Herzmomenten, Antworten, privaten Notizen und Geschenkideen,
sensible Präferenzwerte und präzise Standorte. Error Tracking wird ebenso
bereinigt.

## Ende-zu-Ende-Verschlüsselung

**Noch nicht implementiert.** Der Aufbau ist vorbereitet (siehe
[ARCHITECTURE.md](ARCHITECTURE.md)).

Der Claim, dass selbst der Betreiber Inhalte nicht lesen kann, darf **erst**
nach tatsächlicher Umsetzung und externem Audit verwendet werden. Stufe 1
ist keine E2EE und wird nicht so genannt.

Stufe 1 erzwingt nur die technische Trennung: sensible Fachinhalte werden
als konkrete `ProtectedPayload`-Klasse an eine dafür vorgesehene JSONB-Spalte
gebunden; rohe Dictionaries werden abgewiesen. Bei `crypto_version = 0`
liegt dieser Inhalt weiterhin als serverlesbarer Klartext vor. Es gibt noch
keine Schlüssel, keine clientseitige Versiegelung und keinen Schutz vor dem
Serverbetreiber.

Outbox-Nutzlasten sind separat auf explizit freigegebene, nicht sensible
Metadaten beschränkt. Freitextfelder und `ProtectedPayload`-Objekte scheitern
sowohl an der Domain-Validierung als auch beim direkten ORM-Bind.
