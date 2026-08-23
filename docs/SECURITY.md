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

Nicht geloggt: Inhalte von Memories, Herzmomenten, Antworten, privaten
Notizen und Geschenkideen, sensible Präferenzwerte, präzise Standorte.
Error Tracking wird ebenso bereinigt.

## Ende-zu-Ende-Verschlüsselung

**Noch nicht implementiert.** Der Aufbau ist vorbereitet (siehe
[ARCHITECTURE.md](ARCHITECTURE.md)).

Der Claim, dass selbst der Betreiber Inhalte nicht lesen kann, darf **erst**
nach tatsächlicher Umsetzung und externem Audit verwendet werden. Stufe 1
ist keine E2EE und wird nicht so genannt.
