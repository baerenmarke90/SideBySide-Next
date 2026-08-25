# G1 Gate Review nach Abschluss von #61 – 25. August 2026

> Datierter Gate-Snapshot. Dieses Dokument wird nachträglich nicht umgeschrieben. Neue Prüfstände erhalten eine neue Datei.

**Geprüfter `main`:** `095a6f14f62d174df99f86826a4f748671c053d6`  
**Geprüfter Tree:** `756b5eaa22054f5844368a6ab5f23686a3d187ff`  
**Verifizierter PR-HEAD:** `1a64d432b97e6f1ef680e682ddbd20280cb23713` mit demselben Tree  
**CI-Nachweis:** PR #64, Run #150 (`32823098333`), vollständig erfolgreich  
**Anlass:** Abschluss des letzten Runtime-G1-Blockers #61 und formale Neubewertung von G1.

## Ergebnis

**G1 ist bestanden. M2-S0 und die interne M2-Domainimplementierung sind freigegeben.**

Der im vorherigen G1/M1-Follow-up-Review vom 25.08.2026 verbliebene Runtime-Blocker #61 ist mit PR #64 geschlossen. Das Löschen einer `RelatedPerson` verlangt nun ausdrücklich eine Delete-Policy; ein stiller destruktiver Cascade ist nicht mehr möglich.

Die übrigen offenen Security-/Repository-Punkte ändern diese Entscheidung nicht:

- **#59** bleibt verpflichtende Pre-Exposure-Härtung gegen Challenge-Flooding beim anonymen Passkey-Authentication-Start.
- **#60** bleibt verpflichtende Pre-Exposure-Härtung für atomare Rate-Limit-Schwellen unter Parallelität.
- **#25** bleibt Repository-Hardening für technisch erzwungene Branch Protection.

#59 und #60 müssen vor öffentlicher bzw. Managed-Exposition geschlossen sein. #25 bleibt bis zur technischen Durchsetzbarkeit offen. Keiner dieser Punkte ist ein Runtime-Blocker für interne M2-Domainimplementierung.

## Nachweis für #61

### Explizite Delete-Policy

`DELETE /api/v1/spaces/{spaceId}/related-persons/{personId}` verlangt jetzt `deletePolicy` mit genau zwei zulässigen Varianten:

- `preserve`: Die `RelatedPerson` wird gelöscht; alle verknüpften `ImportantDate`-Einträge bleiben erhalten und werden vom Personenbezug gelöst.
- `cascade`: Die `RelatedPerson` und alle verknüpften `ImportantDate`-Einträge werden gelöscht, einschließlich privater `OWNER_ONLY`-Termine des Partners.

Fehlende oder unbekannte Policies werden abgelehnt. Es existiert kein destruktiver Default.

### Privacy

Die Delete-Antwort bleibt unabhängig von privaten Partnerterminen ein leerer `204`. Sie enthält weder Count-/Exists-Signale noch Titel, Datum, Typ, Owner oder sonstige Metadaten unsichtbarer Partnerressourcen.

Die PostgreSQL-/HTTP-Tests prüfen die gleiche Antwortform bei 0, 1 und mehreren privaten verknüpften Partnerterminen.

### Atomarität und Concurrency

Die `RelatedPerson` wird vor der Versionsprüfung gesperrt. Bei `preserve` werden auch die verknüpften `ImportantDate`-Zeilen per Row Lock behandelt, bevor die Referenzen gelöst werden. Die gesamte Operation läuft in derselben Request-Transaktion. Bestehende `If-Match`-/Versionierungsregeln bleiben wirksam; erhaltene Termine erhöhen bei der Entkopplung ihre Version.

### Verifikation

PR #64 / CI Run #150 war auf dem geprüften Tree vollständig grün. Erfolgreich waren insbesondere:

- Lint,
- Formatierung,
- Mypy,
- OpenAPI-Vertrag,
- Alembic-Migrationen und Drift-Prüfung,
- kompletter Testlauf,
- explizites PostgreSQL-Integrationstest-Gate,
- Supply Chain einschließlich Dependency-/Vulnerability-Scan und Produktionscontainer-Build,
- Secret Scan,
- Provenance.

Die neuen Tests decken `preserve` und `cascade`, eigene und partnerfremde private Termine, unverknüpfte Termine, fehlende/ungültige Policy, fremden Space, Nicht-Owner, stale `If-Match`, anonymen Zugriff sowie die Privacy-Gleichheit bei unterschiedlicher Anzahl privater Partnertermine ab.

## G1-Matrix

| G1-Kriterium | Status | Bewertung |
|---|---|---|
| Auth- und Recovery-Wege | ✅ | Bereits im vorherigen Review positiv bewertet; seitdem kein regressiver Befund. |
| OIDC-Protokollgrenzen | ✅ | HTTPS-Discovery sowie Audience-/`azp`-Härtung aus PR #62 bleiben Bestandteil von `main`. |
| Invitation atomar/race-sicher | ✅ | Unverändert positiv bewertet. |
| Tenant Guard | ✅ | Cross-Tenant-Verhalten bleibt durch HTTP-/PostgreSQL-Tests abgesichert. |
| Owner-only-/Private-Authorization | ✅ | Direkte Zugriffe bleiben SQL-seitig geschützt; die frühere indirekte Cross-owner-Destruktionswirkung ist durch #61 geschlossen. |
| Profile/SpaceProfile und Concurrency | ✅ | ETag/If-Match und Versionskonflikte bleiben wirksam. |
| Session-/Refresh-Sicherheit | ✅ | Unverändert positiv bewertet. |
| Cross-Tenant-, Session- und Privacy-Tests | ✅ | Vollständiger Testlauf und explizites PostgreSQL-Gate sind grün. |
| Cross-owner Delete-Integrität | ✅ | `preserve`/`cascade` sind explizit, atomar und privacy-sicher; kein destruktiver Default. |

## Gate-Entscheidung

### G1

**BESTANDEN.**

Es ist kein offener Runtime-Befund bekannt, der die interne Fortsetzung in M2 blockiert.

### M2

**M2-S0 FREIGEGEBEN.**

Die M2-Domainimplementierung darf auf Basis des aktuellen `main` beginnen. Die bestehenden Projektregeln bleiben unverändert: klarer Issue-Scope, eigener Branch/PR, keine direkten Änderungen an `main`, vollständige CI und Merge Commit nach frischer Prüfung.

### Öffentliche / Managed-Exposition

**Noch nicht freigegeben.**

Vor öffentlicher bzw. Managed-Exposition sind mindestens #59 und #60 sowie die späteren Productization-/G5-Anforderungen zu schließen. #25 bleibt zusätzlich als Repository-Hardening offen.
