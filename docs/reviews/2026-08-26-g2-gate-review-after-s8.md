# G2 Gate Review nach Abschluss von M2-S8

**Datum:** 26.08.2026  
**Gate:** G2 — Story Alpha  
**Geprüfter `main`:** `c97214687e7f559fd75afafc92cb3bd43a67fcc4`  
**Tree:** `d0e78fc5a331a84a3d2761f1d59eab2dc9fe0328`  
**Ergebnis:** **G2 NICHT BESTANDEN — Gate-Nachweis noch unvollständig**

> Dieser Review ist ein datierter Gate-Snapshot. Er wird nachträglich nicht in einen bestandenen Zustand umgeschrieben. Nach Schließung der hier dokumentierten Nachweislücken erhält G2 einen neuen datierten Review.

## 1. Anlass und Prüfgrundlage

Mit PR #130 wurde der dünne Web-Referenzflow aus #127 und mit PR #137 der dünne Android-Referenzflow aus #128 nach `main` übernommen. Damit ist der geplante M2-S8-Implementierungsumfang geliefert.

Gelieferte Referenzstände:

- Web-S8: PR #130, Head `034ab0ccf8868e0893847193b334a7a53f9dcc9e`
- Android-S8: PR #137, Head `cf184953d8b59a68b65aad661a995d9dd33b0920`
- gemeinsamer geprüfter Stand nach beiden Merges: `main` `c97214687e7f559fd75afafc92cb3bd43a67fcc4`

Die Gate-Bewertung folgt den Exit Criteria aus `docs/ROADMAP.md`, `docs/m2/PROJECT-CONTROL.md`, der verbindlichen `docs/m2/SECURITY-TEST-MATRIX.md` und der `docs/ACCESSIBILITY-QA-MATRIX.md`.

Wichtig ist die Trennung zwischen **gelieferter Referenzimplementierung** und **vollständigem Gate-Nachweis**: Ein grüner Client-Build oder ein orchestrierter Unit-Test beweist nicht automatisch einen echten Client-zu-Backend-End-to-End-Lauf und ersetzt keine vorgeschriebene manuelle Accessibility-Abnahme.

## 2. Ergebnis auf einen Blick

Die M2-Domain, der versionierte API-Vertrag und die wesentlichen Backend-Security-/Privacy-Gates sind belastbar umgesetzt und durch PostgreSQL-/HTTP-Integrationstests sowie grüne CI belegt. Beide S8-Referenzclients sind vorhanden, kompilieren und besitzen fokussierte Contract-, Orchestrierungs-, Semantics- und Privacy-nahe Tests.

Für ein bestandenes G2 fehlen jedoch zwei ausdrücklich geforderte Nachweise:

1. **Kein reproduzierbar dokumentierter echter Web- und Android-End-to-End-Lauf gegen die reale SideBySide-API, PostgreSQL und MediaStore.** Die vorhandenen S8-Flowtests verwenden auf Web gemockte API-Methoden/`fetch` und auf Android eine Fake-Implementierung von `ReferenceContract`.
2. **Keine dokumentierte manuelle Accessibility-/Privacy-Abnahme der S8-Referenzflows.** Die verbindliche QA-Matrix erklärt ausdrücklich, dass Automatisierung die Prüfung mit realer Tastatur/Assistenztechnik nicht ersetzt und dass manuelle Ergebnisse Plattform, Version, Bedienhilfe und Testdatum nennen müssen.

Da beide Punkte explizite G2-Kriterien sind, ist das Gate zum geprüften Stand **nicht bestanden**. M3 ist damit noch nicht freigegeben.

## 3. Belastbar erfüllte G2-Bereiche

### 3.1 M2-Domain und API

Für den G2-Scope sind auf `main` geliefert:

- Memory CRUD (#71 / PR #77),
- HeartMoment mit Owner-only-Privacy (#80 / PR #84),
- Attachment-Lifecycle für Bilder (#79 / PR #89),
- Memory-/HeartMoment-Attachment-Bindung (#90 / PR #93),
- Milestone (#94 / PR #95),
- Comments, Outbox und Notification Hook (#97 / PR #98),
- S3-kompatibler MediaStore-Adapter (#87 / PR #100),
- Story Read Model und `/timeline` (#113 / PR #114),
- generatorbasierte Web-/Android-API-Schichten (#102 / PR #120),
- Kotlin-StoryItem-Union-Fix (#119 / PR #126),
- Web-S8 (#127 / PR #130),
- Android-S8 (#128 / PR #137).

Video bleibt bewusst außerhalb von M2/G2 und fail-closed; #88 ist Future-Backlog.

**Bewertung:** erfüllt.

### 3.2 Story-Privacy vor Projektion und Pagination

`backend/tests/integration/test_story.py` prüft die gemeinsame Zeitleiste über die öffentliche HTTP-Schicht mit PostgreSQL. Insbesondere wird geprüft:

- ein `PRIVATE` HeartMoment fehlt dem Partner,
- derselbe private HeartMoment fehlt auch dem Owner in der gemeinsamen `/timeline`,
- der Owner findet ihn weiterhin in seiner getrennten privaten Collection,
- `SHARED -> PRIVATE` entfernt das Item aus beiden Story-Sichten,
- ein fremder Space liefert keine Daten,
- `visibility` ist kein alternativer Story-Modus,
- Filter, Sortierung und Keyset-Pagination bleiben lücken- und duplikatfrei,
- manipulierte bzw. an einen anderen Filter gebundene Cursor werden abgewiesen.

Damit wird die zentrale G2-Zusage belegt, dass `OWNER_ONLY` nicht erst nachträglich im Client oder nach der Pagination weggefiltert wird.

**Bewertung:** erfüllt.

### 3.3 Media-/Upload-Sicherheit und Parent-Autorisierung

`backend/tests/integration/test_attachments.py` und `test_attachment_binding.py` prüfen den Bild-Lifecycle über HTTP/PostgreSQL und den realen MediaStore-Vertrag. Unter anderem sind belegt:

- Upload -> Finalize -> Validierung -> `READY`,
- serverseitige MIME-/Magic-Byte-Prüfung,
- Größen- und Typgrenzen,
- fail-closed bei manipulierten/abgeschnittenen/nicht erlaubten Dateien,
- EXIF-/Hersteller-/GPS-Metadaten werden nicht unbereinigt ausgeliefert,
- Finalize ist idempotent,
- fremde und anonyme Zugriffe werden neutral abgewehrt,
- nur `READY` ist bindbar,
- abgelaufenes Bindungsfenster sperrt Bindung und Read,
- ein Attachment kann nicht konkurrierend mehreren Parents zugeordnet werden,
- nach Bindung folgt die Lesbarkeit der Parent-Autorisierung statt einer alternativen Owner-Abkürzung.

Der S3-Adapter besitzt zusätzlich einen separaten Contract-/Integrationstestpfad in `test_attachments_s3.py`.

**Bewertung:** erfüllt für den Bild-Scope von G2.

### 3.4 Races und Tenant-Isolation

Die Integrationstestfläche enthält unter anderem:

- `test_comment_races.py` mit echtem PostgreSQL-Race für Comment-Create gegen `PRIVATE`-/Delete-Entzug des Parents,
- `test_tenant_isolation.py`,
- `test_private_authorization.py`,
- die Cross-Space-/Parent-Prüfungen der Attachment-Bindung,
- transaktionale/Concurrency-Prüfungen in den jeweiligen Domain-Suites.

`test_comment_races.py` hält den Parent mit einer echten Row-Lock-Transaktion, startet den konkurrierenden Comment-Create und beweist, dass nach dem Privacy-/Delete-Commit kein unzulässiger Kommentar überlebt.

**Bewertung:** erfüllt für die im G2-Scope nachgewiesenen Race-/Tenant-Pfade.

### 3.5 OpenAPI, PostgreSQL-Integration und Repository-CI

Auf dem Android-S8-Head `cf184953d8b59a68b65aad661a995d9dd33b0920` war CI Run `32954034226` vollständig grün. Der Backend-Job bestätigte explizit:

- Lint und Formatierung,
- Typprüfung,
- OpenAPI-Vertrag,
- Migrationen und Migration-Vollständigkeit,
- Tests,
- `Integrationstests sind wirklich gelaufen`.

Zusätzlich waren Supply Chain, Self-Hosted Start, Provenance, API Clients und Secret Scan erfolgreich. Das API-Clients-Gate bestätigte, dass der erzeugte Client-Code zum Vertrag passt.

**Bewertung:** erfüllt.

## 4. S8-Client-Nachweise

### 4.1 Web-S8

Der Web-S8-Head `034ab0ccf8868e0893847193b334a7a53f9dcc9e` hatte erfolgreiche Runs für:

- Reuse Review,
- Web S8,
- Self-Hosted Deployment Guard,
- Repository-CI.

Der Web-S8-Workflow führt locked dependency install, Audit, Typecheck, Tests und Production Build aus.

`web/src/client/referenceFlow.test.ts` prüft sinnvoll:

- Bearer-Token nur auf dem authentifizierten `STREAM`-Transport,
- kein Bearer-Leak an Signed Upload URLs,
- die fachliche Reihenfolge `create-memory -> create-upload -> upload -> finalize -> READY -> bind -> timeline -> read-access -> read`,
- `If-Match` bei der Memory-Bindung,
- Parent-gebundene Read-Autorisierung.

Der Test verwendet jedoch `vi.fn`-API-Doubles und einen gemockten `fetch`. Er beweist daher die Client-Orchestrierung und den Transportvertrag, aber **nicht** den vollständigen realen Weg bis Backend/PostgreSQL/MediaStore.

**Bewertung:** Implementierung und fokussierte Tests erfüllt; G2-E2E-Nachweis offen.

### 4.2 Android-S8

Der Android-S8-Head `cf184953d8b59a68b65aad661a995d9dd33b0920` hatte erfolgreiche Runs für:

- Reuse Review,
- Android S8,
- Self-Hosted Deployment Guard,
- Repository-CI.

Der Android-S8-Workflow führt Unit-/Semantics-/Contract-Tests, Android Lint und einen reproduzierbaren Debug-Build aus.

`ReferenceFlowTest.kt` prüft dieselbe Orchestrierung und die Bindungs-/Read-Verträge. Der Test verwendet dafür jedoch eine Fake-Implementierung von `ReferenceContract`; die echte HTTP-Schicht und ein realer Backend-/PostgreSQL-/MediaStore-Stack werden in diesem Test nicht angesprochen.

Zusätzlich wurden in PR #137 zwei relevante Session-/Privacy-Races behoben und regressionsgetestet:

- spät eintreffende Session-/Timeline-Ergebnisse nach Logout,
- spät eintreffende Photo-Picker-Callbacks nach Logout oder Sessionwechsel.

**Bewertung:** Implementierung, Semantics-/Contract-Tests und Build erfüllt; G2-E2E-Nachweis offen.

## 5. Nicht erfüllte G2-Kriterien

### 5.1 Echter Client-End-to-End-Nachweis auf Web und Android

Die Roadmap verlangt mindestens einen kritischen Memory/Media/Story-Flow in **Web und Android technisch Ende-zu-Ende**.

Zum geprüften Stand existiert kein reproduzierbarer Nachweis, bei dem die produktive S8-Clientschicht den vollständigen Weg gegen eine reale SideBySide-API, PostgreSQL und MediaStore durchläuft. Die Backend-Integrationstests beweisen die Serverseite, die S8-Tests beweisen die Client-Orchestrierung; die Verbindung beider Beweisflächen fehlt.

**Blocker:** #144 — `[M2-G2][E2E] Reale Web- und Android-Referenzflows gegen SideBySide-Stack nachweisen`.

**Bewertung:** nicht erfüllt.

### 5.2 Accessibility-/Privacy-Abnahme der Referenzflows

`docs/ACCESSIBILITY-QA-MATRIX.md` schreibt für Release-Gates ausdrücklich vor:

- automatisierte Checks ersetzen die manuelle Prüfung nicht,
- kritische Pfade werden mit echter Tastatur/Assistenztechnik geprüft,
- Web umfasst u. a. Tastatur-only, Screenreader und 200 % Zoom,
- Android umfasst u. a. TalkBack und große Schrift/Displaygröße,
- manuelle Ergebnisse nennen Plattform, Version, Bedienhilfe und Testdatum,
- Blocker, kritische oder hohe Befunde müssen vor Freigabe geschlossen sein.

Die S8-PRs besitzen automatisierte DOM-/Semantics-Prüfungen, aber im Repository wurde kein datierter manueller S8-Abnahmebericht gefunden, der diese Kriterien erfüllt.

**Blocker:** #145 — `[M2-G2][QA] Accessibility- und Privacy-Abnahme der S8-Referenzflows dokumentieren`.

**Bewertung:** nicht erfüllt.

## 6. Gate-Matrix

| G2-Kriterium | Stand 26.08.2026 | Evidenz / Folge |
|---|---|---|
| Memory, Bild-Attachment, HeartMoment, Milestone, Comment vollständig | **erfüllt** | gelieferte M2-Slices und PostgreSQL-/HTTP-Tests |
| Story schließt `OWNER_ONLY` vor Projektion/Pagination aus | **erfüllt** | `backend/tests/integration/test_story.py`, PR #114 |
| Media-/Upload-Abuse und Parent-Autorisierung geprüft | **erfüllt** | `test_attachments.py`, `test_attachment_binding.py`, S3-Tests |
| relevante Cross-Tenant-/Race-Pfade geprüft | **erfüllt** | Tenant-/Private-Authorization-Suites, `test_comment_races.py` |
| OpenAPI/Migrationen/PostgreSQL-Integration grün | **erfüllt** | CI Run `32954034226`, Backend + API Clients |
| Web-S8 baut/testet reproduzierbar | **erfüllt** | Web S8 Run `32947566873` |
| Android-S8 baut/testet reproduzierbar | **erfüllt** | Android S8 Run `32954034261` |
| echter Web Memory/Media/Story-E2E gegen realen Stack | **offen / blocker** | #144 |
| echter Android Memory/Media/Story-E2E gegen realen Stack | **offen / blocker** | #144 |
| manuelle Web Accessibility-/Privacy-Abnahme ohne hohe Befunde | **offen / blocker** | #145 |
| manuelle Android Accessibility-/Privacy-Abnahme ohne hohe Befunde | **offen / blocker** | #145 |
| vollständige Client-Parität | **nicht erforderlich** | gehört zu M5/G4 |

## 7. Gate-Entscheidung

**G2: NICHT BESTANDEN.**

Die Implementierung von M2-S8 ist geliefert, aber die verbindliche Gate-Evidenz ist noch nicht vollständig. Es wäre fachlich falsch, aus grünen Unit-/Contract-/Semantics-Tests einen nicht ausgeführten realen Client-E2E-Lauf abzuleiten oder die explizit vorgeschriebene manuelle Accessibility-Abnahme stillschweigend als bestanden zu behandeln.

Bis #144 und #145 abgeschlossen und in einem **neuen datierten G2-Review** verifiziert sind:

- bleibt G2 geschlossen,
- gilt M2 noch nicht als formal abgeschlossen,
- wird M3 nicht freigegeben,
- dürfen aktive Statusquellen keinen bestandenen G2-Status behaupten.

Der spätere finale G2-Review wird über #147 vorbereitet. Der Status-Sync der laufenden Projektsteuerungsdokumente erfolgt anschließend separat über #146.

## 8. Öffentliche / Managed-Exposition

Unabhängig von G2 bleibt öffentliche bzw. Managed-Exposition weiterhin gesperrt, solange die ausdrücklich als Pre-Exposure-Härtung geführten Punkte #59 und #60 nicht geschlossen sind. Dieser Review stuft sie nicht zu M2/G2-Blockern um und schwächt ihre spätere Pflicht nicht ab.

#25 bleibt separates Repository-Hardening. #138 bleibt der separate Android-Generator-Follow-up für die beiden Passkey-Request-Modelle und ist kein Grund, den hier geprüften S8-Scope nachträglich zu erweitern.

## 9. Nächste Schritte

1. #144 schließen: reale Web- und Android-E2E-Nachweise gegen API + PostgreSQL + MediaStore.
2. #145 schließen: datierte manuelle Accessibility-/Privacy-Abnahme für beide Referenzflows.
3. Danach #147: frischen `main`, CI und beide Nachweise prüfen und einen neuen finalen G2-Gate-Review erstellen.
4. Erst bei `G2: BESTANDEN` #146 ausführen und die aktiven Statusquellen synchronisieren.
5. Erst danach M3-Planning/Decisions beginnen.
