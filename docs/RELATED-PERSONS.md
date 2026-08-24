# Nahestehende Personen und wichtige Termine

## Scope

Die M1-Domain `people` traegt zwei Objekte aus Abschnitt 12 der
Master-Spezifikation:

- `RelatedPerson`: eine Person im Umfeld des Paares - Kind, Elternteil,
  Geschwister, Freundin. Sie hat **keinen SideBySide-Account**, keine
  Anmeldung und keine Einladung.
- `ImportantDate`: ein Datum, das dem Paar wichtig ist. Es kann zu einer
  `RelatedPerson` gehoeren, muss es aber nicht - der eigene Jahrestag
  gehoert zu niemandem sonst.

Nicht enthalten: Erinnerungen, Benachrichtigungen und Regeln. Die Termine
sind so modelliert, dass eine spaetere Regel wie "Lisa hat in 7 Tagen
Geburtstag" mit Metadaten auskommt.

## Datensparsamkeit

Ueber Dritte wird gespeichert, was fuer die Beziehungspflege noetig ist:
Anzeigename, Art der Beziehung, ein Geburtstag. Keine Adressen, keine
Schulen, keine Telefonnummern. Diese Personen koennen ihre Daten nicht
selbst einsehen oder loeschen; das Modell bleibt deshalb bewusst schmal.

Anzeigename und Termin-Etikett sind der schuetzenswerte Teil und liegen in
einer `ProtectedPayloadJSON`-Spalte mit `crypto_version = 0` - Klartext und
**keine E2EE**. Alles, was zum Sortieren, Verknuepfen und spaeteren
Erinnern gebraucht wird - Beziehung, Datum, Wiederholung, Sichtbarkeit -
bleibt als Spalte abfragbar.

## Sichtbarkeit

Der Request nennt `visibility` (`SHARED` oder `PRIVATE`), nie die
Privacy-Klasse. Der Server leitet ab: `SHARED` => `SPACE_SHARED`,
`PRIVATE` => `OWNER_ONLY`. Lesen und Schreiben laufen anschliessend ueber
den zentralen Owner-/Privacy-Guard; die Bedingung ist Teil der SQL-Abfrage
und kein nachtraegliches Filtern.

Schreiben darf nur der Eigentuemer. Ein geteilter Eintrag des Partners ist
lesbar und ergibt beim Schreibversuch 403; ein privater Eintrag des
Partners ergibt 404, weil ein 403 seine Existenz bestaetigen wuerde.

## Ein Termin ist nie offener als seine Person

Ein `SPACE_SHARED` Termin an einer `OWNER_ONLY` Person waere die Auskunft,
dass es diese Person gibt - genau das soll der private Eintrag verhindern.

Die Regel steht deshalb im Schema und nicht nur im Service.
`important_dates` fuehrt `space_id` und die Privacy-Klasse seiner Person
als Kopie mit; beide zusammen bilden mit `related_person_id` einen
zusammengesetzten Fremdschluessel auf `related_persons (id, space_id,
privacy_class)`. Damit gilt zweierlei ohne Zutun der Fachlogik:

- Ein Termin kann nicht auf eine Person aus einem fremden Space zeigen.
- Ein Termin kann nicht offener sein als seine Person; ein CHECK haelt
  fest, dass eine `OWNER_ONLY` Person nur `OWNER_ONLY` Termine traegt.

`ON UPDATE CASCADE` haelt die Kopie aktuell. Der Service prueft dieselbe
Bedingung vorher, damit ein Client eine erklaerende 422 bekommt
(`IMPORTANT_DATE_MORE_OPEN_THAN_PERSON`) und keinen Datenbankfehler.

## Aendern und Loeschen einer Person

**Privater stellen:** Existieren noch geteilte Termine an dieser Person,
wird die Umstellung mit 409 (`RELATED_PERSON_HAS_SHARED_DATES`) abgelehnt.
Sie werden nicht still umklassifiziert - auch nicht die des Partners.
Private Termine des Partners halten die Umstellung dagegen nicht auf: sie
bleiben erlaubt, und eine Ablehnung ihretwegen waere die Auskunft, dass es
sie gibt.

**Loeschen:** Die abhaengigen Termine werden mitgeloescht, einschliesslich
privater Termine des Partners an dieser Person. Ein `SET NULL` ist nicht
moeglich, weil `space_id` Teil desselben Fremdschluessels ist und nicht
leer werden darf; ein Termin ohne seine Person waere ausserdem ein Datum
ohne Bezug.

## Geburtstag ohne bekanntes Jahr

`DATE` kennt kein Datum ohne Jahr. Ist das Geburtsjahr unbekannt
(`birthdayYearKnown = false`), speichert der Server Monat und Tag mit dem
Platzhalterjahr **1904** - einem Schaltjahr, damit der 29. Februar
speicherbar bleibt. Die Datenbank erzwingt den Platzhalter, damit keine
zweite Stelle im Code ein anderes Jahr waehlt.

Clients zeigen bei `birthdayYearKnown = false` ausschliesslich Tag und
Monat an. Ein bekanntes Jahr ohne Datum ist ein Widerspruch und wird mit
422 (`RELATED_PERSON_BIRTHDAY_REQUIRED`) abgelehnt statt still korrigiert.

## Concurrency

Beide Objekte tragen eine Version. Schreibzugriffe brauchen `If-Match` mit
der zuletzt gelesenen Version; ein veralteter Stand ergibt 409
(`VERSION_CONFLICT`). Antworten tragen die Version als `ETag`.

## Ereignisse

Diese Domain erzeugt keine Outbox-Ereignisse. Es gibt in M1 keinen
Empfaenger dafuer, und ein Ereignis ueber eine dritte Person waere eine
zweite Kopie ihrer Daten an einer Stelle mit eigener Aufbewahrung. Wenn
die Erinnerungslogik kommt, entsteht das Ereignis dort - mit Metadaten und
ohne Klartext.
