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

**Loeschen:** Der Client muss bei jedem Delete eine explizite
`deletePolicy` senden. Zulassig sind ausschliesslich:

- `preserve`: Die `RelatedPerson` wird geloescht, alle verknuepften
  `ImportantDate` bleiben erhalten und verlieren ihre Personenverknuepfung.
  Das gilt auch fuer `OWNER_ONLY`-Termine des Partners.
- `cascade`: Die `RelatedPerson` und alle mit ihr verknuepften
  `ImportantDate` werden geloescht. Das gilt bewusst auch fuer
  `OWNER_ONLY`-Termine des Partners.

Ohne gueltige Policy wird der Request mit 422 abgelehnt. Es gibt keinen
destruktiven Default.

Beide Varianten laufen atomar in derselben DB-Transaktion. Die Person und
bei `preserve` die verknuepften Termine werden fuer die Mutation gesperrt;
die vorhandene `If-Match`-/Versionspruefung der Person bleibt verpflichtend.
Beim Entkoppeln erhaltener Termine steigt deren Version wie bei jeder
anderen ORM-Aenderung.

Die Delete-Antwort ist fuer beide Policies ein leerer 204 und darf keinerlei
Count-, Exists- oder Metadaten ueber verknuepfte Termine enthalten. Das gilt
insbesondere unabhaengig davon, ob der Partner null, einen oder mehrere
private Termine an dieser Person besitzt.

Die Oberflaeche muss vor der Ausfuehrung aktiv zwischen **Termine erhalten**
und **Termine mit loeschen** waehlen lassen. Fuer `cascade` ist eine deutliche,
aber allgemein formulierte Warnung Pflicht, zum Beispiel sinngemaess:

> Mit dieser Person verknuepfte Termine koennen auch Eintraege deines Partners enthalten.

Die UI darf niemals anzeigen oder indirekt verraten, ob solche privaten
Partnertermine existieren, wie viele es sind oder welche Titel, Daten, Typen
oder sonstigen Metadaten sie enthalten.

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
