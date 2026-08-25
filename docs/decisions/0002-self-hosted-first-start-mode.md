# ADR 0002 – Betriebsmodus des Self-Hosted-Erststarts

**Status:** Angenommen  
**Datum:** 25. August 2026  
**Verweis:** #110

## Kontext

Der mitgelieferte Compose-Stack setzte `SBS_ENVIRONMENT=production` fest, während `.env.example` als ausfüllbarer Startpunkt geschrieben war. Beides zusammen ergab keinen funktionierenden Startpfad: `cp .env.example .env && docker compose up -d` scheiterte an drei aufeinanderfolgenden Production-Invarianten — fehlender Cursor-Signing-Key, `SBS_MAIL_TRANSPORT=log` und eine `http://`-Basisadresse.

Die Validierungen sind fachlich richtig. Der Widerspruch lag nicht in ihnen, sondern in der ungeklärten Frage, was der erste Start einer Self-Hosted-Instanz überhaupt sein soll. Solange sie offen war, hätte jede Reparatur an `compose.yaml` sie stillschweigend mitentschieden.

Drei Optionen standen zur Wahl:

1. **Production bleibt Default**, ergänzt um eine lesbare Preflight-Meldung und einen dokumentierten Entwicklungs-Override.
2. **Der Erststart ist ein lokaler Testbetrieb**, echter Betrieb verlangt eine bewusste Umstellung.
3. **Der Quickstart ist echt Production**, und die Dokumentation verlangt SMTP-Zugang und HTTPS-Domain ab der ersten Zeile.

## Entscheidung

Es gilt Option 2. Der mitgelieferte Stack startet als **klar markierter lokaler Testbetrieb**.

- `compose.yaml` setzt `SBS_ENVIRONMENT` auf `${SBS_ENVIRONMENT:-development}`.
- `.env.example` ist für diesen Testbetrieb vorbereitet und setzt `SBS_ENVIRONMENT=development` ausdrücklich.
- Echter Betrieb verlangt `SBS_ENVIRONMENT=production` in `.env` und damit einen Cursor-Signing-Key, eine `https://`-Basisadresse und einen entschiedenen Mailweg.
- Die Production-Validierungen bleiben in Kraft. Sie werden weder entfernt noch umgangen.
- **Ein SMTP-Zugang ist keine Startvoraussetzung.** Production akzeptiert `SBS_MAIL_TRANSPORT=none`: die Instanz versendet dann keine E-Mail, die mailabhängigen Anmeldewege — Magic Link, Recovery, Adressbestätigung — antworten mit `503 MAIL_TRANSPORT_UNAVAILABLE`, und Anmeldung läuft über Passwort, Passkey und OIDC. Verboten bleibt in Production allein `log`, weil dabei gültige Einmal-Token in jede Logablage geschrieben werden. Der Unterschied ist nicht formal: bei `none` verlässt kein Token das System.
- Die API meldet den Betriebsmodus beim Start im Log. Im Testbetrieb ist das eine Warnung, die benennt, was fehlt.

## Begründung

Option 3 wäre die ehrlichste Variante, macht SideBySide aber unausprobierbar: Wer die Software ansehen will, müsste vorher eine Domain mieten und einen Mailserver einrichten. Für ein Produkt, dessen Zielgruppe Paare sind, die selbst hosten, ist das die falsche Eintrittshürde.

Option 1 hält den sicheren Default formal, verschiebt das Problem aber nur: Der Quickstart bliebe für jeden Erstnutzer eine Fehlermeldung, und der Entwicklungs-Override wäre der Pfad, den faktisch alle nehmen — nur ohne dass die Dokumentation ihn als den normalen Weg beschreibt.

Der Preis von Option 2 ist real und wird hier ausdrücklich benannt: Der Default des mitgelieferten Stacks ist nicht mehr `production`. Wer die Umstellung vergisst, betreibt seine Instanz ohne HTTPS-Zwang, ohne Host-Prüfung und mit offener Schema-Auskunft.

Getragen wird das durch zwei bestehende Schutzlagen und eine neue:

- Die API ist im Compose-Stack ausschließlich an `127.0.0.1` gebunden. Eine vergessene Umstellung ist damit nicht aus dem LAN oder dem Internet erreichbar.
- Wer die Instanz veröffentlicht, braucht dafür ohnehin einen Reverse Proxy und trifft dabei auf die Checkliste in `docs/SELF-HOSTING.md`.
- Neu: Der Betriebsmodus steht bei jedem Start im Log, im Testbetrieb als Warnung. Der Unterschied ist damit nicht nur in einer Datei dokumentiert, die beim Aufsetzen einmal gelesen wird.

## Folgen

- `docs/SELF-HOSTING.md` beschreibt zwei getrennte Abläufe: lokaler Test und Produktionsbetrieb. Der Produktionsabschnitt ist eine Checkliste, keine Fußnote.
- CI prüft den realen Compose-Startpfad — Migration, API, Worker, Healthcheck — statt nur `docker compose config` zu parsen. Genau diese Lücke hat den Fehler aus #110 an allen Gates vorbeigelassen.
- Die Production-Invarianten bleiben durch Negativtests abgesichert. Eine CI, die grün wird, indem sie eine Validierung lockert, ist ausdrücklich nicht zulässig.
- Diese Entscheidung betrifft ausschließlich den Self-Hosted-Stack. Für SideBySide Managed gilt sie nicht; dort ist `production` gesetzt und es gibt keinen Testbetriebsmodus.

Eine spätere Rückkehr zu Option 1 bleibt möglich und wäre additiv: Sie verlangt einen Preflight-Check und einen benannten Override, aber keine Änderung an den Validierungen.
