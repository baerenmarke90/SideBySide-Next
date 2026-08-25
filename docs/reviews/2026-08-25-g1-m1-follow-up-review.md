# G1/M1 Follow-up Security Review – 25. August 2026

> Datierter Security- und Gate-Snapshot. Dieses Dokument wird nachträglich nicht umgeschrieben. Neue Prüfstände erhalten eine neue Datei.

**Geprüfter Stand:** `main` bei Commit `6bc2cc955da04933e0957be2f19ce14d29e59755`  
**Geprüfter Tree:** `4931e5a5e459552b6760ea716f895b2bab6bf8ed`  
**CI-Nachweis:** PR #62, Run #138 (`32818527380`), vollständig erfolgreich gegen denselben Tree  
**Ziel:** Gate G1 „Sicherer Paar-Space“ nach Abschluss der früheren M1-Blocker erneut bewerten und die Findings #59, #60, #61 und #25 verbindlich einordnen.

## Ergebnis

**G1 ist noch nicht bestanden. M2-Runtime bleibt gesperrt.**

Die früheren Blocker aus dem Review vom 24.08.2026 sind geschlossen: produktive Auth-/Recovery-Flows, zentrale Owner-/Privacy-Autorisierung, die M1-Profile einschließlich RelatedPerson/ImportantDate, Optimistic Concurrency und die zugehörige PostgreSQL-/HTTP-Testmatrix sind vorhanden. Die OIDC-Härtung aus PR #62 ist ebenfalls enthalten und CI-grün.

Der verbliebene Runtime-Gate-Blocker ist **#61**: Das Löschen einer geteilten `RelatedPerson` kann heute über den Datenbank-Cascade auch einen `OWNER_ONLY`-Termin des Partners löschen. Der direkte Lese- und Schreibschutz des privaten Termins funktioniert, aber der Eigentümer der geteilten Person kann die private Ressource des Partners derzeit indirekt destruktiv verändern. Die Produktentscheidung erlaubt diesen Cascade nur als ausdrücklich gewählte Option neben „Termine erhalten“ und verlangt eine deutliche, privacy-sichere Warnung. Dieser Vertrag ist serverseitig noch nicht umgesetzt.

#59 und #60 sind relevante Abuse-/Availability-Härtungen, aber **keine Blocker für interne M2-Domainimplementierung**: Es ist kein Authentifizierungs- oder Tenant-Bypass bekannt. Beide müssen jedoch vor jeder öffentlichen bzw. Managed-Exposition geschlossen und mit den vorgesehenen PostgreSQL-Paralleltests nachgewiesen sein.

#25 bleibt Repository-/Prozess-Hardening und blockiert das Runtime-Gate nicht. Die PR-/CI-Pflicht bleibt bis zu technisch erzwungener Branch Protection eine verbindliche Projektregel.

## Prüfgrundlage

- `specification/CLEAN-ROOM-MASTER-SPEC.md`, insbesondere Multi-Tenancy, Privacy, Auth, Invitations, Profile und M1.
- `docs/SECURITY.md`.
- `docs/ROADMAP.md`, Gate G1.
- `docs/IMPLEMENTATION-STATUS.md`.
- produktiver Code in `backend/src/sidebyside/`.
- Integrationstests in `backend/tests/integration/`.
- CI-Workflow `.github/workflows/ci.yml`.
- historischer G1/M1-Review vom 24.08.2026.
- offene Findings #25, #59, #60 und #61.

## G1-Matrix

| G1-Kriterium | Status | Befund |
|---|---|---|
| Auth- und Recovery-Wege | ✅ | Lokales Passwort, OIDC Authorization Code + PKCE/State/Nonce, Passkeys, Magic Link, E-Mail-Verifikation und Recovery sind implementiert. OIDC-Onboarding über eine gültige Einladung ist vorhanden. |
| OIDC-Protokollgrenzen | ✅ | Discovery-Issuer, Signatur/JWKS, Nonce, State, Audience/`azp` und HTTPS für Discovery-Endpunkte werden geprüft. Zusätzliche nicht vertrauenswürdige Audiences werden abgelehnt. |
| Invitation atomar, einmalig, widerrufbar und race-sicher | ✅ | Einladungen sind gehasht, zeitlich begrenzt, widerrufbar und serialisieren konkurrierende Annahmen. OIDC-Onboarding revalidiert die Einladung beim Callback und erzeugt Account/Identität/Membership atomar. |
| Tenant Guard | ✅ | Fremde und fehlgeformte Space-/Ressourcen-Zugriffe werden vor dem Laden fremder Fachzeilen abgewehrt; Cross-Tenant-Tests sind vorhanden. |
| Owner-only-/Private-Authorization | ✅ / ⚠️ | Direkte Lese-/Schreibzugriffe werden SQL-seitig nach Space, Owner und Privacy-Klasse gefiltert. Die verbleibende indirekte destruktive Wirkung beim RelatedPerson-Cascade ist Finding #61. |
| Profile/SpaceProfile und Concurrency | ✅ | SpaceProfile, PartnerProfile/ProfilePreference, RelatedPerson und ImportantDate sind vorhanden; veränderbare Ressourcen verwenden ETag/If-Match bzw. Versionskonflikte. |
| fachlich korrekte Beziehungsdauer | ✅ | Die Berechnung berücksichtigt die Zeitzone des lesenden Accounts. |
| Session-/Refresh-Sicherheit | ✅ | Refresh-Rotation ist atomar, Replay wird über die Token-Familie erkannt, Sessions sind widerrufbar und die relevanten Paralleltests laufen gegen PostgreSQL. |
| Cross-Tenant-, Session- und Privacy-Tests | ✅ | Die Integrationstest-Suite enthält u. a. Endpoint-Matrix, Tenant Isolation, Private Authorization, PartnerProfile, RelatedPerson, SpaceProfile, OIDC, Passkey und Cloud-Auth. CI erzwingt, dass Integrationstests tatsächlich laufen. |
| Cross-owner Delete-Integrität | ❌ | Eine geteilte RelatedPerson kann derzeit ohne explizite Delete-Policy gelöscht werden; der FK-Cascade löscht dabei auch private ImportantDates des Partners. Tracking: #61. |

## Geschlossene Findings des Reviews vom 24.08.2026

### Owner-/Private-Authorization

Der zentrale Guard formuliert die Sichtbarkeits- und Schreibbedingungen als Teil des SQL-Statements. Für nicht lesbare private Zeilen bleiben malformed, unbekannt, fremder Space und fremdes `OWNER_ONLY` nach außen nicht unterscheidbar; sichtbare geteilte Zeilen eines anderen Owners ergeben beim Schreibversuch 403.

**Bewertung:** früherer G1-Blocker geschlossen.

### Auth-/Recovery-Flows

OIDC, WebAuthn/Passkey, Magic Link, E-Mail-Verifikation und Recovery sind als reale API-/Protokollflows vorhanden. Die Passkey-Integrationstests verwenden einen virtuellen Authenticator mit echtem P-256-Schlüssel; OIDC wird mit echten signierten Testtokens geprüft.

**Bewertung:** früherer G1-Blocker geschlossen.

### M1-Profile und Concurrency

SpaceProfile besitzt Schreibpfad und Optimistic Concurrency. PartnerProfile/ProfilePreference sowie RelatedPerson/ImportantDate sind implementiert und besitzen Owner-/Privacy-/Tenant-Regeln.

**Bewertung:** früherer G1-Blocker geschlossen.

### Privacy-/Tenant-Testmatrix

Die neuen M1-Endpunkte sind in der HTTP-/PostgreSQL-Testmatrix enthalten. Private Ressourcen werden über Detail-, Listen-, Filter- und Schreibzugriffe negativ geprüft.

**Bewertung:** früherer G1-Blocker geschlossen.

### Refresh-Replay über die Token-Familie

Die frühere Härtung #24 ist umgesetzt; alte Generationen bleiben der Familie zuordenbar und ein erkannter Replay widerruft die Sitzung dauerhaft.

**Bewertung:** frühere P1-Härtung geschlossen.

## Neue bzw. verbleibende Findings

### F-01 – P1 / G1-Blocker: RelatedPerson-Cascade kann private Partnerressourcen indirekt löschen (#61)

`ImportantDate` verwendet für den Personenbezug `ON DELETE CASCADE`. Der heutige Delete-Endpunkt für `RelatedPerson` besitzt keine Delete-Policy. Der vorhandene Integrationstest belegt bewusst, dass beim Löschen einer geteilten Person auch ein daran gebundener privater Termin des Partners verschwindet.

Das ist kein Lesedaten-Leak und kein Cross-Tenant-Bypass. Es ist jedoch eine **Cross-owner-Destruktionswirkung**: Der Account darf den privaten Termin nicht lesen, ändern oder direkt löschen, kann ihn aber durch Löschen der geteilten Bezugsressource entfernen.

Die beschlossene Produktregel lautet:

- `preserve`: betroffene Termine bleiben erhalten und werden in eine fachlich geeignete neutrale Form überführt bzw. vom Personenbezug gelöst;
- `cascade`: die heutigen abhängigen Löschungen bleiben erlaubt, einschließlich privater Termine des Partners;
- kein destruktiver Default;
- die Warnung muss allgemein bleiben und darf Existenz, Anzahl, Label, Datum oder Owner unsichtbarer Partnertermine nicht offenlegen;
- die Auswahl wird serverseitig autorisiert und atomar umgesetzt.

**Gate-Entscheidung:** G1 bleibt bis zur Umsetzung und grünen Verifikation von #61 geschlossen.

### F-02 – P1 / Pre-Exposure: Passkey-Authentication-Start kann Challenges fluten (#59)

Der anonyme Authentication-Start legt pro Aufruf eine `WebAuthnChallenge` an. Eine serverseitige, multi-instance-fähige Abuse-Grenze fehlt derzeit.

**Risiko:** Availability/DB-Wachstum, kein bekannter Auth-Bypass.  
**Pflicht:** PostgreSQL-Schwellen- und Parallel-/Burst-Test sowie Nachweis, dass oberhalb der Grenze keine weiteren Challenge-Zeilen entstehen.

**Gate-Entscheidung:** kein Blocker für interne M2-Domainimplementierung; **Blocker vor öffentlicher/Managed-Exposition**.

### F-03 – P1 / Pre-Exposure: Rate-Limit-Schwellen sind unter Parallelität weich (#60)

Die aktuelle Logik arbeitet als `count -> check -> record`. Parallele Requests können denselben alten Zählerstand lesen und dadurch die nominelle Grenze in einem Burst überschreiten.

**Risiko:** Abuse-Grenze unter Last weicher als konfiguriert, kein bekannter Auth-Bypass.  
**Pflicht:** atomare bzw. serialisierte Slot-Vergabe pro `(action, key)` über PostgreSQL oder gleichwertige zentrale Primitive und realer Paralleltest.

**Gate-Entscheidung:** kein Blocker für interne M2-Domainimplementierung; **Blocker vor öffentlicher/Managed-Exposition**.

### F-04 – Repository-Härtung: `main` ist technisch nicht geschützt (#25)

Das Ruleset wird für das private Repository im aktuellen Tarif nicht erzwungen; `main` ist API-seitig weiterhin nicht protected. Der CI-Umfang ist stark, kann aber durch einen direkten Push organisatorisch umgangen werden.

**Gate-Entscheidung:** kein Runtime-G1-Blocker. PR + frische CI + Merge-Commit bleiben verbindliche Projektregel, bis GitHub das Ruleset technisch erzwingt.

### F-05 – Productization: Auth-Routen-/Provider-Policy je Betriebsform

`SBS_DEPLOYMENT` unterscheidet Cloud und Self-Hosted, erzwingt aber noch nicht vollständig, welche Auth-Routen und Provider je Betriebsform verfügbar sind. Ein im Client versteckter Button ist keine Sicherheitsgrenze.

Die Roadmap ordnet diese Durchsetzung dem Productization-/G5-Umfang zu. Für G1 sind die Auth-Protokolle und ihre Sicherheitsinvarianten maßgeblich; eine öffentliche Managed-Instanz darf jedoch erst exponiert werden, wenn die Betriebsform-Policy und F-02/F-03 umgesetzt sind.

**Gate-Entscheidung:** kein Blocker für interne M2-Domainimplementierung; vor Launch/Managed-Exposition verpflichtend.

## CI- und Build-Bewertung

Der geprüfte Tree `4931e5a5e459552b6760ea716f895b2bab6bf8ed` lief in PR #62 vollständig durch CI #138. Erfolgreich waren insbesondere:

- Lint und Formatierung,
- Mypy,
- OpenAPI-Vertrag,
- Alembic-Migrationen und Drift-Prüfung,
- vollständiger Testlauf,
- explizites Gate, dass PostgreSQL-Integrationstests tatsächlich gelaufen sind,
- Dependency-/Vulnerability-Scan,
- Dependency-Inventar,
- Wheel- und Produktionscontainer-Build,
- Secret Scan,
- Provenance-/Lizenzprüfung.

Der Merge-Commit `6bc2cc955da04933e0957be2f19ce14d29e59755` zeigt auf exakt diesen geprüften Tree.

## Freigabeentscheidung

### G1

**NICHT FREIGEGEBEN.**

Vor G1-Freigabe ist mindestens erforderlich:

1. #61 serverseitig mit expliziter `preserve`-/`cascade`-Policy umsetzen,
2. destruktiven Default ausschließen,
3. privacy-sichere Semantik ohne Existenzauskunft über private Partnertermine nachweisen,
4. PostgreSQL-/HTTP-Tests für beide Policies sowie Cross-owner-/Tenant-Fälle grün bekommen,
5. danach einen kurzen neuen datierten Gate-Review gegen den dann aktuellen `main` und dessen CI durchführen.

### M2

**Produktive M2-Runtime bleibt bis dahin gesperrt.**

Nach erfolgreicher #61-Umsetzung und positiver G1-Neubewertung kann M2-S0 bzw. die M2-Domainimplementierung freigegeben werden. #59 und #60 dürfen parallel oder danach bearbeitet werden, müssen aber vor jeder öffentlichen/Managed-Exposition geschlossen sein.

## Nächster Review

Nach Merge von #61 einen neuen datierten G1-Gate-Review erstellen. Dieser nächste Review muss:

- den exakten `main`-Commit und den getesteten Tree nennen,
- die erfolgreiche CI referenzieren,
- die beiden Delete-Policies einschließlich Privacy-Test nachweisen,
- G1 anschließend ausdrücklich auf bestanden oder weiterhin blockiert setzen.
