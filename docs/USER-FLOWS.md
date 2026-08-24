# SideBySide Critical User Flows

**Status:** Verbindliche UX-/Produktgrundlage  
**Version:** 1.0  
**Stand:** 24.08.2026

Dieses Dokument beschreibt die kritischen End-to-End-Abläufe für WebApp und Android. Es ergänzt Screen-Templates um Übergänge, Entscheidungen, Systemreaktionen und Abnahmekriterien. Fachliche Quelle bleiben die Produktspezifikation und der OpenAPI-Vertrag.

## 1. Verbindliche Flow-Regeln

- Web und Android liefern dasselbe fachliche Ergebnis; Darstellung und Plattformmechanik dürfen abweichen.
- Jeder Zugriff wird im aktuellen `spaceId` und mit aktiver Membership ausgeführt.
- `OWNER_ONLY` wird ausschließlich serverseitig durchgesetzt und erscheint niemals in Story, Partnersuche, Dashboard, Partnerbenachrichtigung oder Partnerexport.
- `SPACE_SHARED` bedeutet für die normale Paar-UI „Geteilt“.
- Android darf im MVP zuletzt geladene Daten offline anzeigen, aber **nicht offline schreiben**.
- Veränderbare Objekte tragen eine `version`; ein Konflikt wird mit HTTP 409 sichtbar, nie still überschrieben.
- Sensible Inhalte erscheinen weder in Analytics noch in Logs.
- Jeder Flow besitzt Loading-, Empty-, Error-, Offline- und Abbruchverhalten, soweit anwendbar.

## 2. Gemeinsame Zustände

```text
Entry → Loading → Ready → Action → Submitting → Success
                    │          ├──────────────→ Validation error
                    │          ├──────────────→ Authorization/not found
                    │          ├──────────────→ Conflict
                    │          └──────────────→ Network error
                    └─────────────────────────→ Read-only offline cache
```

Nach einem Fehler bleibt die letzte sichere Eingabe erhalten. Der Screen erklärt, ob die Aktion erneut versucht werden kann oder eine neue Entscheidung nötig ist.

## 3. Flow A — Account erstellen oder anmelden

**Ziel:** Eine Person erhält sicher Zugriff auf ihren Account und den zuletzt aktiven Space.

**Einstiege:** Startscreen, abgelaufene Sitzung, geschützter Deep Link, Einladung.

### Happy Path Cloud

1. Person gibt ihre E-Mail-Adresse ein oder wählt einen vorhandenen Passkey.
2. Die Oberfläche erklärt den nächsten Schritt, ohne zu verraten, ob eine fremde E-Mail registriert ist.
3. Magic Link oder Passkey wird bestätigt.
4. Der Client erhält eine sichere Sitzung; Tokens werden nicht in URL, Analytics oder Logs übernommen.
5. Existiert eine aktive Membership, öffnet der ursprünglich gewünschte Deep Link oder `Heute`.
6. Existiert noch kein Space, beginnt Flow B.

### Self-Hosted-Varianten

- Lokaler Passwortlogin und OIDC dürfen angeboten werden.
- Provider- und Serverwahl gehören vor den Credential-Schritt.
- Fehlertexte unterscheiden falsche Eingaben nicht unnötig von unbekannten Accounts.

### Fehler und Abzweigungen

- Abgelaufener/benutzter Magic Link: neuen Link anfordern, Zielkontext erhalten.
- Rate Limit: Wartezeit verständlich anzeigen; kein wiederholtes automatisches Absenden.
- Widerrufene Sitzung: lokale sensible Caches schließen und neu anmelden.
- Offline: vorhandener Read-Cache darf erst nach gültiger lokaler Zugriffssicherung angezeigt werden; keine Anmeldung vortäuschen.

**Erlaubte Analytics:** `auth_started`, `auth_method_selected`, `auth_completed`, `auth_failed` mit Methode und technischem Fehlercode; niemals E-Mail, Token oder Provider-Claims.

**Abnahme:** Cloud- und Self-Hosted-Wege, Deep-Link-Rückkehr, Token-Widerruf, Rate Limit, Tastatur, Passwortmanager/Passkey und Screenreader sind getestet.

## 4. Flow B — Space erstellen und Partner einladen

**Ziel:** Eine Person erstellt einen privaten Paar-Space und verbindet genau eine Partnerperson.

### Erstellende Person

1. Nach dem ersten Login erklärt SideBySide den privaten gemeinsamen Space.
2. Die Person bestätigt Profilname und optionale Basisdaten.
3. Der Space wird angelegt.
4. Einladung wird über einen bewusst gewählten Kanal erzeugt.
5. Die Oberfläche zeigt Status, Ablauf und „Einladung widerrufen“.
6. Bis zur Annahme bleibt die App nutzbar, soweit die jeweilige Funktion keinen Partner voraussetzt.

### Eingeladene Person

1. Einladungslink öffnet App/Web und zeigt ein neutrales, nicht sensibles Preview.
2. Vor Annahme erfolgt Anmeldung oder Account-Erstellung.
3. Name der einladenden Person und Wirkung der Verbindung werden bestätigt.
4. Das einmalige Token wird atomar eingelöst.
5. Beide Clients aktualisieren Space- und Membership-Status.
6. Die neue Person landet in einem kurzen gemeinsamen Onboarding, danach auf `Heute`.

### Verpflichtende Abzweigungen

- Token ungültig, abgelaufen, widerrufen oder bereits verwendet.
- Space hat bereits zwei aktive Partner.
- Zwei gleichzeitige Annahmen: genau eine darf erfolgreich sein.
- Person ist bereits Mitglied.
- Falscher Account: Abmelden/Account wechseln, ohne Token in Verlauf oder Telemetrie zu verlieren.

**Privacy:** Einladungsvorschau zeigt keine Erinnerungen, Präferenzen oder andere Space-Inhalte.

**Erlaubte Analytics:** `space_created`, `invitation_created`, `invitation_revoked`, `invitation_completed`, `invitation_failed`; keine Token, E-Mail oder Partnernamen.

## 5. Flow C — Erinnerung mit Medien erstellen

**Ziel:** Eine gemeinsame Erinnerung sicher anlegen und in der Story anzeigen.

**Privacy-Klasse:** `SPACE_SHARED`. Eine private Notiz ist eine eigene `OWNER_ONLY`-Domäne und kein versteckter Memory-Modus.

### Ablauf

1. Einstieg über Story oder Quick Action „Erinnerung hinzufügen“.
2. Titel, Text und fachlicher Tag `happenedOn` werden erfasst.
3. Medien können ausgewählt, geprüft, entfernt und beschrieben werden.
4. Vor dem Speichern zeigt die UI „Mit Partner geteilt“ als fachlichen Status, nicht als optionales Marketingversprechen.
5. Bei Online-Verbindung wird zuerst die Memory angelegt und anschließend/koordiniert der Medienstatus sichtbar verarbeitet.
6. Erfolg öffnet das neue Detail; Story- und Dashboard-Abfragen werden aktualisiert.

### Medienzustände

```text
selected → validating → uploading → processing → ready
                              └──────────────→ failed → retry/remove
```

- Der Client vertraut nicht allein auf Dateiendung oder gemeldeten MIME-Type.
- Ein fehlgeschlagenes Medium verwirft nicht automatisch den gesamten Entwurf.
- Nicht öffentliche Medien werden nur über autorisierte Route oder kurzlebige signierte URL geladen.

### Fehler

- Offline beim Speichern: „Noch nicht gespeichert“; Entwurf lokal im Formular erhalten, aber nicht als synchronisierten Inhalt darstellen.
- Validierung: Feldfehler direkt am Feld.
- Uploadfehler: pro Datei Retry/Entfernen.
- 409: Flow H.
- 404 nach Deep Link: neutraler Nicht-verfügbar-Zustand ohne Existenzbestätigung.

**Erlaubte Analytics:** `memory_create_started`, `memory_create_completed`, `memory_create_failed`, `attachment_upload_failed`; keine Titel, Texte, Daten, Dateinamen oder Medienmerkmale.

## 6. Flow D — Herzmoment privat oder geteilt erfassen

**Ziel:** Einen emotionalen Moment mit bewusster Sichtbarkeit speichern.

### Ablauf

1. Person erfasst Text und Emotion.
2. Sichtbarkeit ist eine verpflichtende Auswahl: „Nur für mich“ (`OWNER_ONLY`) oder „Mit Partner teilen“ (`SPACE_SHARED`).
3. Vor dem ersten Wechsel zu geteilt erklärt die UI knapp, dass der Inhalt im gemeinsamen Space sichtbar wird.
4. Nach dem Speichern zeigt der Detailzustand Privacy-Label und Sync-Ergebnis.

### Invarianten

- `OWNER_ONLY` erscheint nur für den Eigentümer: Liste, Suche, Story, Dashboard, Benachrichtigungen, Export, Attachments und Relationen eingeschlossen.
- Kommentare sind nur auf geteilten HeartMoments möglich.
- Ein Wechsel der Privacy-Klasse erfordert Online-Verbindung und aktuelle `version`.
- Beim Wechsel von geteilt zu privat erklärt die UI, dass bereits gelesene Inhalte nicht „ungesehen“ gemacht werden können.

**Erlaubte Analytics:** `heart_moment_create_started/completed/failed`, optional Privacy-Kategorie als grobe Klasse; niemals Text oder Emotion, wenn diese als sensibel eingestuft wird.

## 7. Flow E — Wunsch zu Plan entwickeln

**Ziel:** Eine Idee nachvollziehbar in einen konkreten Plan überführen und abschließen.

### Ablauf

1. Wunsch wird als `OPEN` erstellt.
2. Optional werden Ort oder ergänzende Informationen verknüpft.
3. „Als Plan weiterführen“ öffnet eine Vorschau der übernommenen Daten.
4. Bestätigung erzeugt/verknüpft den Plan im Zustand `IDEA` oder `PLANNED` gemäß Eingabe.
5. Der Wunschstatus und die Relation werden in einer fachlichen Transaktion aktualisiert.
6. Nach dem Erlebnis wird der Plan `COMPLETED`.
7. Optional kann er einem Chapter zugeordnet werden; Originalinhalte bleiben eigenständig.

### Regeln

- Wünsche und Pläne sind im Core `SPACE_SHARED`, solange die Produktspezifikation keine private Variante definiert.
- Ein nicht abgeschlossener Plan kann kontrolliert in den Wunschzustand zurück.
- Eine Empfehlung aus „Entdecken“ erzeugt erst nach ausdrücklicher Bestätigung einen Wunsch oder Plan.
- Löschen eines Chapters entfernt Verknüpfungen, nicht Erinnerungen oder Pläne.

### Fehler

- Doppelte Bestätigung darf keine Duplikate erzeugen.
- 409 zeigt aktuelle und eigene Version; Flow H.
- Feature nicht aktiviert/entitled: klare Erklärung, keine ausgegraute Sackgasse.

## 8. Flow F — Story durchsuchen und Inhalt öffnen

**Ziel:** Gemeinsame Geschichte sicher filtern, durchsuchen und per Deep Link öffnen.

### Ablauf

1. Story lädt cursor-basiert, gruppiert nach Monat.
2. Filter nach Typ/Jahr und Suche werden serverseitig mit Space- und Privacy-Filter ausgeführt.
3. Auswahl öffnet auf Compact eine Seite, auf Expanded das Detail-Pane.
4. Zurück stellt Suchbegriff, Filter, Auswahl und Scrollposition wieder her.
5. „Weißt du noch?“ verlinkt auf Originale und erzeugt keine Kopie.

### Privacy

- Story enthält Memories, Milestones und geteilte HeartMoments – niemals `OWNER_ONLY`.
- 404 wird für nicht vorhandene und nicht berechtigte privacy-relevante Ressourcen gleich behandelt.
- Trefferanzahl, Ladezeit und Antwortgröße dürfen keine privaten Partnerinhalte verraten.

**Erlaubte Analytics:** Suchstart und Trefferklasse nur aggregiert; kein Suchtext, kein Inhaltstitel, keine Resource-ID.

## 9. Flow G — Offline lesen, Schreibversuch sicher behandeln

**Ziel:** Android bleibt bei Verbindungsverlust verständlich, ohne einen nicht vorhandenen Offline-Sync vorzutäuschen.

### Lesen

1. Der letzte autorisierte Read-Cache darf mit „Offline · Stand …“ angezeigt werden.
2. Cache-Inhalte behalten Privacy- und Space-Grenzen.
3. Abmeldung, Sitzungswiderruf oder Space-Wechsel sperrt/entfernt den zugehörigen Cache gemäß Sicherheitskonzept.

### Schreiben

1. Vor oder beim Absenden wird fehlende Verbindung erkannt.
2. Die Aktion endet nicht in `success` oder `synced`.
3. Meldung: „Noch nicht gespeichert. Verbinde dich mit dem Internet und versuche es erneut.“
4. Formulareingaben dürfen als lokaler Entwurf im aktuellen sicheren Kontext erhalten bleiben.
5. Nach Wiederverbindung startet der Retry nur durch bewusste Aktion; keine unkontrollierte Hintergrund-Übertragung im MVP.

### Abnahme

- Flugmodus vor und während des Requests.
- Verbindungsabbruch nach Uploadbeginn.
- Prozessneustart mit und ohne lokalem Entwurf.
- Account-/Space-Wechsel mit vorhandenem Cache.
- UI zeigt nie „Offline gespeichert“ oder „wird später synchronisiert“.

## 10. Flow H — Versionskonflikt lösen

**Ziel:** Gleichzeitige Änderungen werden nicht still überschrieben.

### Ablauf

1. Client sendet die geladene `version` beim Update.
2. API antwortet bei Abweichung mit 409 und stabilem Fehlercode.
3. Client lädt die aktuelle Serverversion.
4. UI zeigt: „Dieser Inhalt wurde inzwischen geändert.“
5. Person kann aktuelle Version übernehmen oder die eigene Eingabe kopieren/erneut anwenden.
6. Ein erneutes Speichern verwendet die neue `version`.

### Regeln

- Automatisches Zusammenführen nur für nachweislich sichere, feldweise unabhängige Änderungen.
- Privacy-Klasse, Löschung und Membership werden nie automatisch zusammengeführt.
- Bei gelöschtem Ziel wird kein „Überschreiben“ angeboten.
- Konfliktdetails enthalten keine nicht berechtigten Inhalte.

## 11. Flow I — Datenexport und Kontoschutz

**Ziel:** Eigene Daten portabel erhalten und sensible Kontoaktionen bewusst durchführen.

### Export

1. Exportumfang und nicht enthaltene Sicherheitsdaten werden erklärt.
2. Re-Authentifizierung kann verlangt werden.
3. Exportjob wird gestartet; Status ist später wieder auffindbar.
4. Download ist zeitlich begrenzt und erneut autorisiert.
5. Transfer Bundle enthält Manifest, Checksums, Domänendateien und Medien – keine Passwörter, Passkeys, Tokens, Sitzungen oder Push Tokens.

### Konto-/Space-Aktionen

- Abmelden, Sitzung widerrufen, Account löschen und Space löschen sind getrennte Flows.
- Partnerentfernung ist im MVP nicht verfügbar.
- Vor destruktiven Aktionen werden Umfang, Frist und Wiederherstellbarkeit erklärt.
- Konkrete Retention-Fristen müssen vor Cloud-Launch verbindlich beschlossen werden.

## 12. Flow-Abnahme je Plattform

Jeder Flow wird mindestens geprüft für:

- Web: Tastatur, Screenreader, 200 % Textzoom, Browser-Zurück, direkte URL.
- Android: TalkBack, große Schrift, System-Zurück, Prozessneustart, Read-Cache.
- Compact, Medium und Expanded.
- Cloud und Self-Hosted, wenn Auth- oder Providerunterschiede betroffen sind.
- normale Membership, fremder Space, `OWNER_ONLY`, abgelaufene Sitzung.
- Loading, Empty, Validation, 401, privacy-sicheres 404, 409, 429, Offline und Serverfehler.

## Verwandte Dokumente

- [Produktspezifikation](../specification/PRODUCT-SPEC.md)
- [Informationsarchitektur](./INFORMATION-ARCHITECTURE.md)
- [UX Patterns](./UX-PATTERNS.md)
- [API-/UI-Verträge](./API-UI-CONTRACTS.md)
- [Accessibility- und QA-Matrix](./ACCESSIBILITY-QA-MATRIX.md)
- [Content- und Privacy-Guidelines](./CONTENT-PRIVACY-GUIDELINES.md)
