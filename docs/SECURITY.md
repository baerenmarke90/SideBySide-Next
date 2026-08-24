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

### Was am ID Token geprüft wird

Ein ID Token ist zunächst nur die Behauptung eines fremden Servers. Sie wird
erst zu einer Identität, wenn fünf Dinge stimmen — und keine dieser
Prüfungen steht im Endpunkt, sondern in `auth.oidc`, wo jeder Anbieter sie
durchläuft:

| Prüfung | Wogegen | Warum |
|---|---|---|
| Signatur | JWKS des Issuers, nur asymmetrische Verfahren | `none` und HMAC sind ausgeschlossen: bei `HS256` wäre der Signaturschlüssel das Client Secret |
| Issuer | konfigurierter Wert **und** das Discovery-Dokument, das sich selbst benennen muss | sonst zeigte ein Dokument unter erwarteter Adresse auf fremde Endpunkte |
| Audience | `client_id`, zusätzlich `azp` wenn vorhanden | ein Token für eine andere Anwendung gilt hier nicht |
| Nonce | der beim Start erzeugte Wert | bindet das Token an genau diese Anfrage; ohne sie ließe sich ein anderswo erbeutetes Token einspielen |
| State | serverseitig gespeicherter Hash, genau einmal einlösbar | bindet den Rückweg an genau diesen Browser |

PKCE ist Pflicht (`S256`). Der Verifier bleibt beim Server und geht nie in
die Autorisierungsadresse; der Client sieht nur die Challenge.

`oidc_auth_requests` hält State-Hash, Nonce und Verifier für zehn Minuten.
Nonce und Verifier stehen dort im Klartext, und das ist richtig: der Server
muss beide selbst vorzeigen beziehungsweise vergleichen. Sie sind keine
Anmeldenachweise, sondern eine Bindung — und der Wartungsjob räumt sie weg,
sobald sie verbraucht oder abgelaufen sind.

**Eine OIDC-Anmeldung legt kein Konto an.** Ohne bestehende Identität endet
sie mit 401. Eine neue Identität entsteht ausschließlich über
`/auth/oidc/{connectionId}/link` aus einer bestehenden Anmeldung heraus.
Sonst umginge ein externer Anbieter die Bootstrap- und Einladungsgrenze.

Die Fehlermeldung des Anbieters verlässt den Adapter nicht: sie kann interne
Adressen oder das Client Secret enthalten. Nach außen bleiben es die
immergleichen Codes `OIDC_TOKEN_INVALID`, `OIDC_STATE_INVALID` und
`OIDC_PROVIDER_UNREACHABLE`.

Passkeys liegen als eigene WebAuthn-Credentials vor: global eindeutige
Credential-ID, Public Key, Signaturzähler, AAGUID, Transports sowie
Discoverable-/Backup-Metadaten. Der private Schlüssel bleibt im
Authenticator und wird vom Server weder empfangen noch gespeichert.

### Die beiden Ceremonies

Registriert wird **nur aus einer bestehenden Anmeldung heraus**: ein Passkey
ist ein zusätzlicher Zugang zu einem Konto, das es schon gibt. Angemeldet
wird **ohne Kontobezug** — die Optionen enthalten keine Kandidatenliste, der
Authenticator wählt selbst, welches auffindbare Credential er anbietet. Ein
Endpunkt, der zu einer Adresse die passenden Credentials nennt, wäre ein
Verzeichnis der Konten.

Geprüft werden Challenge, Herkunft, RP ID, Signatur und Signaturzähler.
Jeder Fehlschlag ergibt dieselbe Antwort (`PASSKEY_CEREMONY_INVALID`);
welche der Prüfungen gescheitert ist, steht nicht in der Antwort.

Die Challenge liegt in `webauthn_challenges`, fünf Minuten lang, und wird
beim Abschluss **immer** verbraucht — auch wenn die Prüfung danach
scheitert. Sonst ließe sich dieselbe Challenge beliebig oft durchprobieren.

Ein Signaturzähler, der nicht weitergelaufen ist, obwohl er einmal lief,
deutet auf eine Kopie des Authenticators und führt zur Ablehnung. Zählt ein
Gerät gar nicht — beide Werte bleiben 0 —, ist das erlaubt: viele Passkeys
tun das, und ein Verbot sperrte sie alle aus.

Credential-IDs sind global eindeutig, auch über Konten hinweg. Ob ein
Credential auffindbar ist, sagt die Registrierung nicht (`residentKey` ist
ein Wunsch, keine Zusage); es zeigt sich erst bei einer Anmeldung ohne
Kandidatenliste und wird dort vermerkt.

E-Mail-Verifikation, Magic Link und Account Recovery verwenden getrennte
Tabellen und getrennte Konsumfunktionen. Jeder Nachweis ist zufällig,
kurzlebig, widerrufbar, genau einmal verwendbar und nur als Hash
persistiert. Ein Token eines Ablaufs kann deshalb nicht in einem anderen
Ablauf eingelöst werden — nicht, weil eine Prüfung das verbietet, sondern
weil er dort gar nicht gesucht wird. Die OIDC-/WebAuthn-Adapter fehlen noch;
die lokale Argon2-Anmeldung bleibt davon unabhängig erhalten.

### Die drei Mail-Abläufe

| Ablauf | Endpunkte | Frist |
|---|---|---|
| Magic Link | `/auth/magic-link/request`, `/auth/magic-link/consume` | 15 Minuten |
| E-Mail-Verifikation | `/auth/email/verification/request` (angemeldet), `/auth/email/verification/confirm` | 24 Stunden |
| Account Recovery | `/auth/recovery/request`, `/auth/recovery/consume` | 30 Minuten |

**Keine Existenzauskunft.** Die beiden `request`-Endpunkte antworten immer
mit `202` und leerem Rumpf — für eine bekannte Adresse ebenso wie für eine
unbekannte. Auch das Rate Limit greift für beide gleich, sonst wäre der
Unterschied im Verhalten selbst die Auskunft. Ein Zustellfehler des
Mailservers wird protokolliert, ändert die Antwort aber nicht.

Es bleibt eine Restdifferenz in der Antwortzeit: für eine bekannte Adresse
wird eine Mail übergeben, für eine unbekannte nicht. Sie wird in Kauf
genommen — die Endpunkte sind rate-limitiert, und ein Ausgleich hieße,
den Versand künstlich zu verzögern.

**Nur der zuletzt angeforderte Link gilt.** Eine neue Anforderung entwertet
die noch offenen Vorgänger desselben Ablaufs. Sonst sammelten sich gültige
Anmeldenachweise in einem Postfach an.

**Ein eingelöster Magic Link bestätigt die Adresse.** Wer den Link im
Postfach öffnet, hat den Besitz nachgewiesen; ein zweiter Weg dafür wäre
eine zweite Gelegenheit, ihn zu vergessen.

**Recovery richtet keinen neuen Anmeldeweg ein.** Ein Konto ohne lokales
Passwort — etwa ein reines OIDC-Konto — bekommt keinen Link; nach außen ist
das von einer unbekannten Adresse nicht zu unterscheiden. Ein erfolgreiches
Zurücksetzen beendet **alle** bestehenden Sitzungen und eröffnet genau eine
neue: die auf diesem Gerät.

**Jeder erfolgreiche Weg endet in der zentralen `DeviceSession`-Ausgabe.**
Es gibt keinen zweiten Ort, an dem Tokens entstehen.

### Ausgehende Post

Der Klartext-Token existiert genau zweimal: im Rückgabewert der
Ausgabefunktion und in der Mail. Er wird nicht persistiert und nicht
geloggt.

Deshalb ist der Entwicklungsadapter, der Nachrichten ins Log schreibt, in
Produktion nicht zulässig: `SBS_MAIL_TRANSPORT` muss dort `smtp` sein und
`SBS_PUBLIC_BASE_URL` mit `https://` beginnen, sonst verweigert die
Anwendung den Start. Ein Fehlstart ist hier die freundlichere Antwort — der
stille Gegenentwurf wäre eine Instanz, die Anmeldenachweise ins Log
schreibt, und das fällt niemandem auf.

Die Basisadresse der Links kommt aus der Konfiguration und niemals aus
einem Request-Header. Ein gefälschter `Host` würde den Link sonst auf einen
fremden Server umbiegen, und der Empfänger übergäbe seinen Token dorthin.

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

### Wo sie stehen

Die Liste oben ist die Anforderung; diese Tabelle sagt, wo sie eingelöst
ist. Sie wird beim Schließen einer Lücke fortgeschrieben, nicht beim
Anlegen eines Tests.

| Invariante | Nachweis |
|---|---|
| Jeder Space-Endpunkt weist anonym, Fremde und fehlgeformte IDs gleich ab | `test_endpoint_matrix.py` |
| Der veröffentlichte Vertrag ist vollständig durch diese Matrix abgedeckt | `test_endpoint_matrix.py::test_der_vertrag_ist_vollstaendig_abgedeckt` |
| Kein Schreibzugriff ohne `If-Match` | `test_endpoint_matrix.py::test_ohne_if_match_wird_nicht_geschrieben` |
| Private Ressourcen bleiben für den Partner unsichtbar — Detail, Liste, Filter, Fehlerantwort | `test_private_authorization.py`, `test_related_persons.py`, `test_partner_profiles.py` |
| Fehlversuche bleiben trotz abgelehnter Anfrage dauerhaft gezählt | `test_auth_flows.py::TestProduktiveTransaktionsgrenze` |
| Refresh-Replay widerruft die Familie dauerhaft, auch über Generationen | `test_auth_flows.py`, `test_sessions.py::TestReplay` |
| Paralleler Refresh hat genau einen Sieger | `test_auth_flows.py::test_parallele_refresh_rotation_hat_genau_einen_sieger` |
| Erfolgreiche Rotationen sind selbst begrenzt | `test_sessions.py::TestRotationsflut` |
| Zwei gleichzeitige Einladungsannahmen füllen den Space nicht über zwei Partner | `test_invitations.py::TestWettlauf` |
| Paralleler Bootstrap erzeugt genau einen initialen Owner | `test_auth_flows.py::test_paralleler_bootstrap_hat_genau_einen_owner` |
| Sicherheitsrelevante Tests laufen in CI wirklich und werden nicht still übersprungen | CI-Schritt „Integrationstests sind wirklich gelaufen" |

Die Zeilen zu Uploads, signierten URLs, Backups und Suche bleiben offen —
die zugehörigen Funktionen gibt es noch nicht. Sie werden mit ihrer Domäne
eingelöst, nicht vorher.

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
