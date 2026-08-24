# SideBySide Content and Privacy Guidelines

**Status:** Verbindliche UX-Writing- und Privacy-Grundlage  
**Version:** 1.0  
**Stand:** 24.08.2026

SideBySide spricht ruhig, warm und eindeutig. Die Sprache unterstützt Nähe, ohne Druck, Bewertung oder therapeutische Versprechen. Privacy-Aussagen beschreiben nur technisch belegte Eigenschaften.

## 1. Stimme

SideBySide ist:

- **zugewandt:** menschlich, respektvoll und nicht bürokratisch,
- **ruhig:** kurze Sätze, wenige Ausrufezeichen, keine künstliche Dringlichkeit,
- **klar:** konkrete Folgen und nächste Schritte,
- **gleichwertig:** beide Partner werden sprachlich und visuell gleich behandelt,
- **privacy-first:** Sichtbarkeit und Datenwirkung werden vor einer Aktion verständlich,
- **nicht wertend:** keine Beziehung wird anhand von Nutzung, Häufigkeit oder Stimmung bewertet.

SideBySide ist nicht:

- kitschig oder verniedlichend,
- belehrend oder moralisierend,
- ein Therapie-, Diagnose- oder Sicherheitsversprechen,
- auf Engagement um jeden Preis optimiert,
- künstlich personalisiert durch sensible Inhalte.

## 2. Anrede und Begriffe

- Deutsch verwendet standardmäßig „ihr/euch“ für den gemeinsamen Raum und „du/dein“ für persönliche Aktionen.
- „Partner“ ist der neutrale Produktbegriff; Namen können ihn im konkreten Kontext ersetzen.
- „Space“ darf im Produkt als etablierter Eigenname erscheinen, wird bei Erstnutzung aber als „euer privater gemeinsamer Raum“ erklärt.
- `OWNER_ONLY` heißt „Nur für mich“.
- `SPACE_SHARED` heißt je nach Kontext „Geteilt“ oder „Mit Partner teilen“.
- „Öffentlich“ wird nicht verwendet, weil es keine Public-Privacy-Klasse gibt.
- Technische Begriffe wie Tenant, Payload, Entity, 409 oder UUID bleiben aus regulären Endnutzertexten fern.

## 3. Grundregeln für UI-Text

- Buttontexte beginnen mit einem Verb und benennen das Ergebnis: „Erinnerung speichern“.
- Titel beschreiben Ort oder Aufgabe: „Neue Erinnerung“.
- Hilfetext erklärt nur, was nicht aus Label und Kontext hervorgeht.
- Ein Satz enthält möglichst eine Aussage.
- Kritische Folge steht vor der Bestätigung, nicht erst danach.
- „OK“, „Ja“ und „Weiter“ werden vermieden, wenn ein konkreteres Verb möglich ist.
- Auslassungspunkte werden nur verwendet, wenn eine Aktion einen weiteren Dialog öffnet.

## 4. Privacy-Sprache

### Zulässige Aussagen

- „Nur für mich“ – wenn die Ressource serverseitig `OWNER_ONLY` ist.
- „Mit Partner geteilt“ – wenn beide aktiven Space-Mitglieder zugreifen dürfen.
- „Private Inhalte werden nicht für Produkt-Analytics verwendet.“ – wenn Telemetrie und Betrieb dies nachweislich einhalten.
- „Medien sind nicht öffentlich zugänglich.“ – wenn Abruf autorisiert oder kurzlebig signiert erfolgt.
- „SideBySide ist privacy-first gestaltet.“ – als Designprinzip, nicht als absolute Sicherheitsgarantie.

### Nicht zulässige Aussagen im MVP

- „Ende-zu-Ende verschlüsselt“ oder „Nur ihr könnt das lesen“.
- „Vollständig anonym“.
- „Kann niemals verloren gehen“.
- „100 % sicher“.
- „Niemand außer dir erfährt davon“, wenn Metadaten betrieblich verarbeitet werden.
- „Offline gespeichert und wird später synchronisiert“.

Im MVP ist echte E2EE nicht implementiert. `cryptoVersion = 0` oder technische E2EE-Bereitschaft wird nicht als vorhandene Verschlüsselungsfunktion vermarktet.

## 5. Sichtbarkeitstexte

### Anzeigezustand

| Privacy-Klasse | Label | Erklärung bei Bedarf |
|---|---|---|
| `OWNER_ONLY` | Nur für mich | Dein Partner sieht diesen Inhalt nicht. |
| `SPACE_SHARED` | Geteilt | Für euch beide im gemeinsamen Space sichtbar. |
| `TEMPORARY_SHARED` | Zeitlich geteilt | Erst verwenden, wenn Ablauf und Empfänger fachlich implementiert sind. |

### Auswahlzustand HeartMoment

```text
Wer kann diesen Moment sehen?

( ) Nur für mich
    Dein Partner sieht diesen Moment nicht.

( ) Mit Partner teilen
    Der Moment erscheint in eurem gemeinsamen Bereich.
```

- Eine Auswahl ist verpflichtend.
- Der Client erfindet keine Privacy-Auswahl für Domains, die nur `SPACE_SHARED` unterstützen.
- Wechsel zu geteilt wird bewusst bestätigt; Wechsel zu privat erklärt Grenzen des nachträglichen Zurücknehmens.

## 6. Status- und Systemtexte

| Zustand | Bevorzugter Text |
|---|---|
| Speichern läuft | Wird gespeichert … |
| Erfolg | Gespeichert |
| Upload läuft | Foto wird hochgeladen … |
| Cache offline | Offline · Stand von {Zeit} |
| Offline-Schreibversuch | Noch nicht gespeichert. Verbinde dich mit dem Internet und versuche es erneut. |
| Konflikt | Dieser Inhalt wurde inzwischen geändert. |
| nicht verfügbar | Dieser Inhalt ist nicht verfügbar. |
| Sitzung abgelaufen | Deine Sitzung ist abgelaufen. Melde dich erneut an. |
| Rate Limit | Das waren viele Versuche. Probiere es in {Dauer} erneut. |

- „Etwas ist schiefgelaufen“ darf nur ein letzter Fallback sein und benötigt einen nächsten Schritt.
- Erfolgstext nennt Ergebnis, nicht technische Verarbeitung.
- Ein Fehler macht Nutzende nicht verantwortlich.

## 7. Fehlermuster

Ein guter Fehlertext beantwortet:

1. Was ist nicht gelungen?
2. Was ist mit der Eingabe passiert?
3. Was kann die Person jetzt tun?

### Beispiele

**Validierung**

```text
Titel fehlt
Gib der Erinnerung einen kurzen Titel.
```

**Netzwerk**

```text
Noch nicht gespeichert
Dein Entwurf bleibt hier erhalten. Verbinde dich mit dem Internet und versuche es erneut.
```

**Konflikt**

```text
Inzwischen geändert
Dein Partner hat diesen Inhalt bearbeitet. Sieh dir die aktuelle Version an, bevor du erneut speicherst.
```

**Privacy-sicheres 404**

```text
Inhalt nicht verfügbar
Er wurde möglicherweise entfernt oder du kannst ihn nicht öffnen.
```

## 8. Empty States

Empty States unterscheiden:

- **Erstnutzung:** Nutzen erklären und ersten Inhalt anlegen.
- **Alles erledigt:** positiven Abschluss zeigen, keine künstliche Aufgabe erzeugen.
- **Suche/Filter:** Suchbegriff nicht wiederholen, wenn er sensibel sein könnte; Filter zurücksetzen anbieten.
- **fehlende Berechtigung:** Nutzen und Alternative erklären.
- **nicht aktiviertes Feature:** Aktivierung oder Grund nennen.

Beispiel Story:

```text
Eure Story beginnt hier
Haltet einen gemeinsamen Moment fest, wenn es für euch passt.
[Erinnerung hinzufügen]
```

## 9. Berechtigungsanfragen

Vor der Systemabfrage enthält der Text Nutzen, Umfang und Alternative.

### Fotos

```text
Foto hinzufügen
Wähle ein Foto für diese Erinnerung aus. Ohne Zugriff kannst du die Erinnerung weiterhin ohne Bild speichern.
```

### Benachrichtigungen

```text
Gemeinsame Momente nicht verpassen
SideBySide kann dich an ausgewählte Termine erinnern. Sensible Inhalte bleiben in der Vorschau standardmäßig verborgen.
```

- Keine Berechtigung wird beim App-Start ohne Kontext angefragt.
- Ablehnung wird respektiert; erneute Abfrage erfolgt erst nach neuer bewusster Aktion.
- Bei dauerhaft blockierter Berechtigung führt eine Aktion gezielt zu Systemeinstellungen.

## 10. Benachrichtigungen

### Standardvorschau

- Keine Memory-Titel, HeartMoment-Texte, privaten Notizen, Präferenzen oder genauen Orte.
- Neutrale Formulierungen wie „In SideBySide gibt es etwas Neues“.
- Name der Partnerperson nur, wenn die Person dies bewusst erlaubt und der System-Lockscreen-Kontext berücksichtigt ist.

### In-App

- Darf nach erfolgreicher Authentifizierung konkreter sein.
- Führt immer zu einem berechtigten Ziel.
- `OWNER_ONLY` erzeugt keine Partnerbenachrichtigung.

## 11. Destruktive Aktionen

- Titel nennt das konkrete Objekt: „Erinnerung löschen?“
- Text erklärt Wirkung und Wiederherstellbarkeit.
- Bestätigungsbutton wiederholt die Aktion: „Erinnerung löschen“.
- „Abbrechen“ ist die sichere Alternative.
- Account löschen, Space löschen, Sitzung widerrufen und Abmelden verwenden getrennte Texte.
- Partnerentfernung wird nicht beschrieben, solange sie nicht Teil des MVP ist.

## 12. Analytics-Allowlist

Erlaubte Kategorien:

- App-/Schema-Version und Plattform,
- Screen geöffnet,
- Feature gestartet/abgeschlossen/fehlgeschlagen,
- technische Fehlercodes,
- Account erstellt,
- Partner eingeladen/beigetreten,
- erste Memory erstellt,
- grobe Aktivitätskohorten wie D7/D30,
- Subscription-/Entitlement-Status ohne Zahlungsdetails.

Verboten:

- Freitext jeder Domain,
- Suchbegriffe,
- E-Mail, Name oder Einladungstoken,
- Memory-/HeartMoment-/Question-/PrivateNote-/GiftIdea-Inhalt,
- sensible Präferenzwerte,
- exakte Daten aus privaten Inhalten,
- Dateinamen, Medieninhalt oder Bildanalyse,
- präzise Standorte,
- direkte Resource-IDs oder Space-Inhalte als Eventparameter.

Jedes neue Event benötigt Owner, Zweck, Aufbewahrung, Properties und Privacy-Review. Nicht dokumentierte Properties werden nicht versendet.

## 13. Logs und Support

Logs dürfen technische Werte wie `requestId`, pseudonymisierte Account-/Space-Referenz, Route, Dauer, Status und Fehlercode enthalten, soweit Sicherheitsdokumentation und Betrieb dies erlauben.

- Support bittet nie um Passwörter, Tokens oder vollständige private Inhalte.
- Kopierbarer Diagnosecode ist `requestId`, keine Ressourcen-URL mit Token.
- Crashreporting wird vor Versand bereinigt.
- Screenshots mit privaten Inhalten werden nicht automatisch angehängt.

## 14. Lokalisierung

- UI-Struktur funktioniert mit mindestens 30 % längeren Texten.
- Keine Satzfragmente aus getrennten Variablen zusammensetzen.
- Plural, Datum und relative Zeit verwenden Locale-Funktionen.
- Fachlicher Tag bleibt ein Datum und wird nicht durch Zeitzonen verschoben.
- Namen werden nicht gekürzt, wenn dadurch Personen verwechselt werden können.
- Gender und Beziehungsform werden nicht aus Namen oder Profilbildern abgeleitet.

## 15. Content Review

Vor Freigabe eines Flows wird geprüft:

- gleiche Begriffe auf Web und Android,
- klare Hauptaktion und klare Folgen,
- korrekte Privacy-Klasse und kein überzogenes Versprechen,
- Offline-Text ohne falsche Sync-Aussage,
- Fehler mit nächstem Schritt,
- neutrale Notification Preview,
- keine sensiblen Analytics-Properties,
- verständlich bei großer Schrift und mit Screenreader/TalkBack,
- Cloud- und Self-Hosted-Unterschiede korrekt.

## Verwandte Dokumente

- [Security](./SECURITY.md)
- [User Flows](./USER-FLOWS.md)
- [API-/UI-Verträge](./API-UI-CONTRACTS.md)
- [Accessibility- und QA-Matrix](./ACCESSIBILITY-QA-MATRIX.md)
