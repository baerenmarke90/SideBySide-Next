# G1/M1 Security Review – 24. August 2026

> Datierter Security- und Gate-Snapshot. Dieses Dokument wird nachträglich nicht umgeschrieben. Neue Prüfstände erhalten eine neue Datei.

**Geprüfter Stand:** `main` bei Commit `e2f952cb51de55062e3c6dfd51990c7254d946ce`  
**Runtime-Codebasis:** Merge `4c1e82f4bddb8c599ea43adf7884f849a48d8545` plus nachfolgende reine Governance-Dokumentation  
**Ziel:** Prüfen, ob Gate G1 „Sicherer Paar-Space“ und der sicherheitsrelevante Umfang von M1 ausreichend erfüllt sind, um M2 freizugeben.

## Ergebnis

**G1 ist noch nicht bestanden. M2 bleibt technisch gesperrt.**

Die sicherheitskritische Basis ist deutlich weiter als im ersten Soll-/Ist-Review: Bootstrap, Tenant Isolation, Einladungsrennen, atomare Refresh-Rotation, dauerhafte Security-Zustände trotz Request-Rollback, reale PostgreSQL-Integrationstests und Supply-Chain-CI sind belastbar umgesetzt. Die verbleibenden Blocker liegen jetzt überwiegend in den noch nicht implementierten M1-Funktionen: echte Auth-/Recovery-Flows, Owner-/Private-Authorization, Profile/SpaceProfile-Schreibpfade und die zugehörige Privacy-Testmatrix.

Die Clean-Room-Provenienzfrage ist auf Prozessebene separat entschieden und blockiert G1 nicht mehr: Der aktuelle Quellbaum wird nicht als strikte/formale Clean-Room-Implementierung bezeichnet, sondern als eigenständige Neuimplementierung aus schriftlicher Spezifikation mit dokumentierter Vorbefassung. Siehe ADR 0001.

## Prüfgrundlage

- `specification/CLEAN-ROOM-MASTER-SPEC.md`, insbesondere Abschnitte 4–13, 59–61 und M1.
- `docs/SECURITY.md`.
- `docs/ROADMAP.md`, Gate G1.
- `docs/IMPLEMENTATION-STATUS.md`.
- produktiver Code in `backend/src/sidebyside/`.
- Integrationstests in `backend/tests/integration/`.
- CI-Workflow `.github/workflows/ci.yml`.
- offene Issues #7, #11, #24, #25 und #26.

## G1-Matrix

| G1-Kriterium | Status | Befund |
|---|---|---|
| Auth- und Recovery-Wege für den jeweiligen Betriebsmodus | ❌ | Persistenzarchitektur für OIDC, WebAuthn, E-Mail-Verifikation, Magic Link und Recovery ist vorhanden; öffentliche Protokoll-/API-Flows fehlen noch. Tracking: #26. |
| Invitation atomar, einmalig, widerrufbar und race-sicher | ✅ | Token nur gehasht, Ablauf/Widerruf/Einmaligkeit, Zeilensperre beim Accept und Space-Sperre gegen konkurrierende letzte Plätze sind implementiert und über PostgreSQL-Wettlauftests geprüft. |
| Tenant Guard | ✅ | Membership wird vor Space-Ressourcenzugriff geprüft; Cross-Tenant-Zugriffe liefern 404 und leaken keine Partnerdaten. |
| Owner-only-/Private-Authorization | ❌ | Es gibt noch keine zentrale Owner-/Private-Autorisierungsgrundlage und keine produktive OWNER_ONLY-Domäne. Tracking: #11. |
| Profile/SpaceProfile mit Versionskonflikten | ❌ | `SpaceProfile` besitzt eine Version, aber keine Schreib-API mit Optimistic Concurrency/409. PartnerProfile/ProfilePreference/RelatedPerson/ImportantDate fehlen. Tracking: #11. |
| fachlich korrekte Beziehungsdauer | ❌ | Die GET-Ausgabe berechnet derzeit gegen `today_utc()` statt gegen die vorgesehene Benutzer-/Space-Zeitzone. Tracking: #11. |
| Cross-Tenant-, Session- und Privacy-Tests grün | 🟡 | Bestehende Auth-/Tenant-/Concurrency-Flows sind gut abgedeckt. Die Rollen-/Owner-/Privacy-Matrix für die noch fehlenden M1-Endpunkte kann naturgemäß noch nicht vollständig sein. Tracking: #7 und #11. |

## Bereits bestandene Sicherheitsgrundlagen

### Tenant Isolation

Der `TenantContext` entsteht erst nach erfolgreicher Bearer-Authentifizierung und aktiver Membership. Fehlgeformte oder fremde Space-IDs führen zu 404. Die HTTP-Tests prüfen Mitglied A, Mitglied B, Fremd-Space, anonyme Zugriffe, malformed IDs, beendete Memberships und Whitelist-Serialisierung der Partnerdaten.

**Bewertung:** bestanden für die aktuell existierenden Space-Endpunkte.

### Zwei-Mitglieder-Grenze und Invitations

`add_member()` sperrt die Space-Zeile mit `FOR UPDATE`, bevor aktive Memberships gezählt und verändert werden. `Invitation.accept()` sperrt zusätzlich die konkrete Invitation. Der Wettlauftest lässt zwei verschiedene Einladungen um den letzten freien Platz konkurrieren und erwartet exakt einen Erfolg.

**Bewertung:** bestanden.

### Self-Hosted-Bootstrap

Die Erstregistrierung verwendet einen transaktionsweiten PostgreSQL-Advisory-Lock und einen dauerhaften Singleton-Zustand. Paralleltests erwarten exakt einen initialen Owner; Wiederverwendung des Bootstrap-Nachweises wird abgewiesen.

**Bewertung:** bestanden.

### Session- und Refresh-Sicherheit

Access- und Refresh-Tokens werden nur gehasht persistiert. Refresh-Rotation sperrt die DeviceSession-Zeile. Der produktive HTTP-Wettlauftest prüft zwei parallele Rotationen desselben Refresh Tokens mit genau einem Erfolg und dauerhaftem Widerruf nach Replay.

**Bewertung:** Kernanforderung bestanden; zusätzliche Härtung siehe Finding S-05 / Issue #24.

### Security-Zustand trotz Rollback

Rate-Limit-Ereignisse und Replay-Widerrufe werden bei fachlich abgelehnten Requests über getrennte After-Rollback-Aktionen in einer frischen Transaktion dauerhaft gespeichert. Tests laufen über den produktiven Unit-of-Work-Lifecycle.

**Bewertung:** früherer P0-Befund behoben.

### CI / Supply Chain

Die CI erzwingt echtes PostgreSQL, Lint, Formatierung, mypy strict, OpenAPI-Vertrag, Migrationen und Drift-Prüfung, vollständige Tests ohne still übersprungene Integrationstests, Dependency-/Vulnerability-Scan, Dependency-Inventar, Wheel-/Container-Build, Secret Scan und Provenance-Prüfung.

**Bewertung:** G0/Security-Foundation bestanden.

## Offene Findings

### S-01 – P1 / G1-Blocker: Owner-/Private-Authorization fehlt

Der bestehende Tenant Guard beantwortet die Frage „gehört der Account zu diesem Space?“. Für M2 reicht das nicht. Private Inhalte benötigen zusätzlich die Frage „ist dieser Account der Owner genau dieser Ressource bzw. darf er diese Privacy-Klasse sehen?“.

Vor HeartMoments mit `PRIVATE`/`OWNER_ONLY` muss eine zentrale, wiederverwendbare Authorisierungsgrundlage existieren. Die Filterung muss in der Datenbankabfrage erfolgen und darf nicht erst nach dem Laden oder im Client passieren.

**Tracking:** #11.

### S-02 – P1 / G1-Blocker: Auth-/Recovery-Persistenz ist noch kein nutzbarer Auth-Flow

OIDC `(issuer, subject, connection_id)`, WebAuthn-Credentials und getrennte Einmal-Tokenmodelle sind vorhanden. Es fehlen aber Discovery-/Signatur-/Claim-Prüfung, OIDC State/Nonce, WebAuthn Ceremonies sowie öffentliche Magic-Link-/Verification-/Recovery-Endpunkte.

Damit sind die vorgesehenen Cloud- und Self-Hosted-Authwege noch nicht vollständig nutzbar.

**Tracking:** #26.

### S-03 – P1 / G1-Blocker: M1-Beziehungsprofile unvollständig

Offen sind:

- SpaceProfile-Schreib-API mit Version/409,
- korrekte Zeitzonenbehandlung der sichtbaren Beziehungsdauer,
- PartnerProfile,
- ProfilePreference,
- RelatedPerson,
- ImportantDate,
- Privacy-/Visibility-Durchsetzung für diese Modelle.

**Tracking:** #11.

### S-04 – P1 / G1-Blocker: Privacy-Testmatrix für neue M1-Endpunkte fehlt

Die bestehende Tenant-Testmatrix ist stark. Sie kann jedoch Owner-/Private-Isolation für noch nicht implementierte Profile und private Ressourcen nicht beweisen. Jeder neue M1-Endpunkt benötigt positive und negative Rollen-/Owner-/Tenant-Fälle über HTTP.

**Tracking:** #7 und #11.

### S-05 – P1-Härtung: Refresh-Replay wird nur für die unmittelbar vorherige Generation zugeordnet

Die DeviceSession merkt aktuell den aktuellen und den unmittelbar vorherigen Refresh-Hash. Nach `T0 -> T1 -> T2` ist ein späteres `T0` zwar ungültig, kann aber nicht mehr als Replay derselben Token-Familie erkannt werden und löst daher keinen kompromittierungsbedingten Widerruf aus.

Das ist kein Login-Bypass, aber eine Lücke in der Kompromittierungserkennung.

**Tracking:** #24.  
**Empfehlung:** vor M2 schließen, spätestens vor jeder extern erreichbaren produktiven Auth-Nutzung.

### S-06 – P2-Härtung: Rate-Limit-Schwelle ist bei einem parallelen Burst nicht serialisiert

`check()` zählt bestehende Ereignisse und `record_attempt()` schreibt anschließend separat. Die Tests beweisen, dass parallele Fehlversuche keine Zähler verlieren, verwenden aber eine Anzahl unterhalb der eigentlichen Sperrschwelle. Mehrere exakt parallele Requests können daher gleichzeitig noch unterhalb des Limits prüfen und den nominellen Grenzwert in einem Burst überschreiten.

**Auswirkung:** kein Auth-Bypass; das konfigurierte Abuse-Limit ist unter starker Parallelität weicher als sein Zahlenwert suggeriert.

**Empfehlung:** vor öffentlicher Cloud-Exposition mit Advisory Lock, atomarem Counter oder gleichwertiger DB-Serialisierung härten. Für den Beginn der internen M2-Domainimplementierung kein eigenständiger Blocker, solange G1 vor Produktfreigabe erneut geprüft wird.

### S-07 – Repository-Härtung: `main` ist nicht geschützt

Der CI-Umfang ist stark, wird aber auf Repository-Ebene noch nicht als Merge-Gate erzwungen. Direct Pushes können die Prüfungen organisatorisch umgehen.

**Tracking:** #25.  
**Bewertung:** Prozess-/Repository-Risiko; vor regelmäßigem Multi-Agent-/PR-Betrieb schließen.

## Governance

ADR 0001 schließt die bislang offene Provenienzklassifikation. Der aktuelle Quellbaum darf nicht als strikte/formale Clean-Room-Implementierung bezeichnet werden. Die bestehende Offenlegung bleibt erhalten; die weitere Implementierung verwendet ausschließlich die versionierte Spezifikation und konsultiert keine Vorgänger-Repositories als Vorlage.

**Bewertung:** Governance-Punkt entschieden; kein G1-Blocker mehr.

## Freigabeentscheidung

### G1

**NICHT FREIGEGEBEN.**

Für G1 müssen mindestens folgende Punkte geschlossen und anschließend erneut geprüft werden:

1. #26 – tatsächliche OIDC-/WebAuthn-/Cloud-Auth-Flows,
2. #11 – Owner-/Private-Authorization und vollständige M1-Profile inklusive SpaceProfile-409/Timezone,
3. #7 – Rollen-/Privacy-/Tenant-Matrix für die neuen M1-Endpunkte.

Zusätzlich soll #24 vor M2 geschlossen werden. #25 ist als Repository-Härtung zeitnah zu erledigen.

### M2

**Noch nicht mit produktiver Domainimplementierung freigeben.**

Die M2-Handoff-Dokumente können weiter als Design-/Planungsgrundlage verwendet werden. Runtime-Code für private HeartMoments, Memories, Comments, Story oder Attachments sollte erst auf die zentrale Owner-/Private-Autorisierung aufsetzen.

## Nächster Review

Neuen datierten G1-Review erstellen, sobald #11, #26 und der relevante Rest von #7 geschlossen sind sowie #24 entschieden/umgesetzt ist. Der nächste Review muss den dann aktuellen `main`-Commit und die erfolgreiche CI eindeutig referenzieren.
