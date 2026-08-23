# Datenschutzmodell

## Haltung

SideBySide verwaltet, was ein Paar freiwillig hineingibt: Erinnerungen,
emotionale Momente, Wünsche, private Notizen, Vorlieben. Das ist kein
beliebiger Anwendungsinhalt. Der Umgang damit ist Produktmerkmal.

Keine Werbung. Kein Verkauf persönlicher Daten. Kein unnötiges Tracking.
Sensible Inhalte fließen nicht in Analytics.

## Klassen

| Klasse | Sichtbar für | Beispiele |
|---|---|---|
| `SPACE_SHARED` | beide Partner | geteilte Erinnerung, Meilenstein, Plan |
| `OWNER_ONLY` | nur Eigentümer | private Notiz, Geschenkidee, privater Herzmoment |
| `TEMPORARY_SHARED` | begrenzt geteilt | zeitlich befristete Freigabe |
| `EPHEMERAL_CONTEXT` | kurzlebig, mit TTL | abgeleitete Situation, Presence |
| `SYSTEM_METADATA` | System | Job, Audit, Outbox |

Eine implizite öffentliche Klasse gibt es nicht. Öffentliche Freigabelinks
sind nicht Teil von 1.0.

## Die harte Grenze

Der Partner ist **kein** privilegierter Leser. Bei `OWNER_ONLY` steht er
Fremden gleich.

Das gilt besonders für die private Ablage — private Notizen, Geschenkideen,
private Listen — und für Herzmomente mit `visibility = PRIVATE`. Eine
Überraschung, die der Beschenkte sehen kann, ist keine.

Durchgesetzt wird das serverseitig in der Abfrage, nicht in der Anzeige.

## Zwei Arten von Profilinformation

Strikt getrennt, weil ihre Verwechslung direkt schadet:

**`SELF_PROFILE`** — was jemand über sich selbst für den Partner freigibt.
Lieblingsessen, Lieblingsblumen, Genres, Abneigungen. Sichtbar für den
Partner, das ist der Zweck.

**`PRIVATE_PARTNER_NOTE`** — was jemand sich über den Partner merkt.
Geschenkidee, Beobachtung, Überraschungsplanung. Niemals im sichtbaren
Partnerprofil.

Beide beschreiben dieselbe Person. Nur eine davon darf diese Person sehen.

## Dritte Personen

Kinder, Familie und Freunde sind keine Accounts. `RelatedPerson` speichert
bewusst wenig: Anzeigename, Beziehung, optional Geburtstag.

Standardmäßig **keine** Adressen, Schulen oder Telefonnummern Dritter. Über
diese Personen wurde nie eine Einwilligung eingeholt.

`birthday_year_known` erlaubt einen Geburtstag ohne Jahr — für ein Kind ist
das Alter oft die heiklere Angabe als der Tag.

## Standort

Standortfunktionen sind standardmäßig **aus**. Es braucht ein
ausdrückliches Opt-in.

Vier Begriffe, strikt getrennt:

| Begriff | Bedeutung |
|---|---|
| `Place` | bewusst gespeicherter gemeinsamer Ort |
| `LocationHistory` | externer Verlauf aus einer Integration |
| `Presence` | aktueller, kurzlebiger Standort |
| `Context` | abgeleitete Situation, etwa "vermutlich im Supermarkt" |

Wo möglich wird auf dem Gerät ausgewertet statt in der Cloud. Serverseitige
Standortdaten: minimale nötige Genauigkeit, kurze Aufbewahrung, kein
Standort in normalen Logs, jederzeit widerrufbar.

Die optionale Partnerentfernung bleibt aus, bis sie bewusst aktiviert wird,
und erzeugt keinen dauerhaften Verlauf.

## Benachrichtigungen

Push-Nachrichten enthalten standardmäßig **keine** sensiblen Texte.

> Neue Aktivität in SideBySide

statt des privaten Originaltexts. Eine Benachrichtigung erscheint auf einem
gesperrten Bildschirm, den auch andere sehen — womöglich der Partner, für
den die Überraschung gedacht war.

## Analytics

Erlaubt sind technische und produktbezogene Ereignisse: App-Version,
geöffneter Bildschirm, genutzte Funktion, Absturz, Account angelegt,
Partner eingeladen, Partner beigetreten, erste Erinnerung angelegt,
Aktivität nach 7 und 30 Tagen, Abo-Status.

Nicht erfasst: Inhalte von Erinnerungen, Herzmomenten, Antworten, privaten
Notizen und Geschenkideen sowie persönliche Standortbeschreibungen.

Kein verpflichtendes Werbenetzwerk-SDK im Produkt.

## Portabilität und Löschung

Ein versioniertes eigenes Transferformat erlaubt den vollständigen Export
der Nutzerdaten. Nicht exportiert werden Passwörter, Passkeys, Refresh
Tokens, Sitzungen, Push Tokens und Sicherheitsprotokolle — das sind
Zugangsmittel, keine Erinnerungen.

Beim Löschen eines Kapitels, Orts oder einer Liste werden Verknüpfungen
entfernt, aber **keine** fremden Originalinhalte gelöscht. Wer ein Kapitel
auflöst, wollte nicht die Erinnerungen des Partners löschen.

Account- und Space-Löschung sind eigene, ausdrückliche Vorgänge. Konkrete
Aufbewahrungsfristen werden vor dem Cloud-Start festgelegt.

## Deaktivierte Funktionen

Eine deaktivierte Funktion löscht ihre Daten **niemals** automatisch. Wer
eine Funktion abschaltet, hat nicht ihre Löschung beauftragt.
