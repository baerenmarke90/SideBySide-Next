# Partnerprofile und Praeferenzen

## Scope

Die M1-Profiles-Domain trennt zwei fachlich unterschiedliche Arten von
Informationen strikt:

- `SELF_PROFILE`: Ein Account beschreibt sich selbst fuer den aktiven
  Partner im selben Space. Diese Zeilen sind `SPACE_SHARED`.
- `PRIVATE_PARTNER_NOTE`: Ein Account merkt sich privat etwas ueber den
  anderen aktiven Partner. Diese Zeilen sind `OWNER_ONLY`.

Es gibt keine `PUBLIC`-Sichtbarkeit und der Request kann `privacyClass`
nicht frei setzen. Die API leitet die Privacy-Klasse serverseitig aus der
fachlichen `visibility` ab.

## Persistenz

`partner_profiles` ist der sichtbare Profil-Aggregatkopf eines Accounts in
einem Space. Pro `(space_id, owner_id)` existiert hoechstens eine Zeile und
die Datenbank erzwingt `SPACE_SHARED`.

`profile_preferences` speichert strukturierte Praeferenzen. Metadaten wie
Kategorie, Topic, Sentiment, Ownership und Sichtbarkeit bleiben separat vom
schuetzenswerten `value`. Der Wert liegt in einer `ProtectedPayloadJSON`-
Spalte mit `crypto_version = 0`; das ist Klartext und **keine E2EE**. Die
Trennung haelt den spaeteren Wechsel auf clientseitig versiegelte Payloads
offen.

Die Datenbank erzwingt zusaetzlich:

- `SELF_PROFILE` => `account_id == owner_id`, `SPACE_SHARED`, sichtbares
  `partner_profile` vorhanden.
- `PRIVATE_PARTNER_NOTE` => `account_id != owner_id`, `OWNER_ONLY`, keine
  Verbindung zum sichtbaren `partner_profile`.

Damit kann eine private Partnernotiz nicht durch eine fehlerhafte
Serialisierung Teil des sichtbaren Partnerprofils werden.

## Autorisierung

Jeder Endpunkt beginnt mit dem bestehenden Tenant Context. Listen und
Detailzugriffe verwenden anschliessend den zentralen Owner-/Privacy-Guard.
Die Filterbedingung ist Bestandteil der SQL-Abfrage; unsichtbare Zeilen
werden nicht zuerst geladen und danach verworfen.

Fuer `SPACE_SHARED` gilt:

- beide aktiven Partner duerfen lesen,
- nur der Owner darf schreiben oder loeschen.

Fuer `OWNER_ONLY` gilt:

- nur der Owner darf lesen, schreiben oder loeschen,
- fuer den betroffenen Partner und Cross-Tenant-Aufrufer ist die Ressource
  ununterscheidbar von einer nicht vorhandenen Ressource (`404`).

Der sichtbare Endpunkt
`GET /api/v1/spaces/{spaceId}/profiles/{accountId}` filtert zusaetzlich
immer auf `SELF_PROFILE`. Eigene private Notizen ueber diese Person werden
also auch dem Notiz-Owner nicht versehentlich in dieser Profilansicht
beigemischt.

## API

- `GET /api/v1/spaces/{spaceId}/profiles/{accountId}`
- `GET /api/v1/spaces/{spaceId}/profile-preferences`
- `POST /api/v1/spaces/{spaceId}/profile-preferences`
- `GET /api/v1/spaces/{spaceId}/profile-preferences/{preferenceId}`
- `PUT /api/v1/spaces/{spaceId}/profile-preferences/{preferenceId}`
- `DELETE /api/v1/spaces/{spaceId}/profile-preferences/{preferenceId}`

Aendern und Loeschen verwenden ETag/`If-Match`. Veraltete Versionen liefern
`409 VERSION_CONFLICT` statt eines stillen Lost Updates.

## Stabile Enums

Kategorien:

`FOOD`, `DRINK`, `FLOWERS`, `MOVIES`, `SERIES`, `MUSIC`, `HOBBIES`,
`ACTIVITIES`, `TRAVEL`, `RESTAURANTS`, `COLORS`, `OTHER`.

Sentiments:

`LOVE`, `LIKE`, `NEUTRAL`, `DISLIKE`, `AVOID`.

Visibility:

`SELF_PROFILE`, `PRIVATE_PARTNER_NOTE`.

Unbekannte Werte werden an der API abgewiesen und sind zusaetzlich durch
Datenbank-Constraints ausgeschlossen.
