# ADR 0001 – Clean-Room-Provenienzklassifikation

**Status:** Angenommen  
**Datum:** 24. August 2026

## Kontext

SideBySide Next wird in einem eigenen Repository und aus einer schriftlichen Produktspezifikation neu implementiert. Die bestehende `PROVENANCE.md` dokumentiert jedoch, dass die Assistentensitzung, die die erste Implementierung begonnen hat, unmittelbar zuvor im Rahmen eines getrennten Projekts erhebliche Teile des Vorgänger-Quellcodes gesehen hatte.

Damit ist die in formalen Clean-Room-Verfahren übliche personelle bzw. kontextuelle Trennung zwischen der Sichtung des Originals und der Implementierung des Ersatzes nicht erfüllt. Der datierte Soll-/Ist-Review vom 24. August 2026 hat diese Prozessabweichung bereits ausdrücklich festgehalten.

## Entscheidung

Das Projekt wird **nicht** als strikte oder formale Clean-Room-Implementierung bezeichnet.

Die verbindliche Projektklassifikation lautet stattdessen:

> **Eigenständige Neuimplementierung auf Basis einer schriftlichen Spezifikation mit dokumentierter Vorbefassung der initialen Implementierungssitzung.**

Der bestehende Quellbaum wird fortgeführt. Es erfolgt kein Neustart allein mit dem Ziel, nachträglich eine strengere Clean-Room-Prozessklassifikation zu erreichen.

Für die weitere Entwicklung gelten weiterhin diese Grenzen:

- Vorgänger-Repositories werden nicht als Implementierungsvorlage geöffnet, durchsucht oder konsultiert.
- Quellcode, Kommentare, Migrationen, Templates, Assets oder sonstige konkrete Implementierungsdetails des Vorgängers werden nicht übernommen.
- Die vollständige schriftliche Master-Spezifikation ist die normative fachliche und technische Quelle.
- Die dokumentierte Vorbefassung bleibt dauerhaft in der Provenienz sichtbar und wird nicht sprachlich abgeschwächt.
- Aussagen wie „formal clean room“, „strict clean room“ oder gleichwertige uneingeschränkte Herkunftsbehauptungen werden für den aktuellen Quellbaum nicht verwendet.

## Folgen

Diese Entscheidung schließt den offenen Governance-Punkt vor M2 auf Prozessebene. Sie ändert keine technische Security-Anforderung und ersetzt insbesondere nicht das G1/M1-Sicherheitsgate.

Sollte eine strikte formale Clean-Room-Trennung später aus geschäftlichen, vertraglichen oder rechtlichen Gründen zwingend werden, wäre dafür eine neue, nachweisbar nicht vorbefasste Implementierung auf Basis der Spezifikation erforderlich. Der aktuelle Quellbaum würde durch eine bloße Textänderung nicht nachträglich zu einer formalen Clean-Room-Implementierung.

Diese ADR ist eine Projekt- und Provenienzentscheidung. Sie ist **keine Rechtsberatung und keine Aussage darüber, welche urheber-, lizenz- oder sonstigen rechtlichen Folgen sich aus dem Entwicklungsprozess ergeben**.

## Verweise

- [`PROVENANCE.md`](../../PROVENANCE.md)
- [`specification/CLEAN-ROOM-MASTER-SPEC.md`](../../specification/CLEAN-ROOM-MASTER-SPEC.md)
- [`docs/reviews/2026-08-24-spec-gap-review.md`](../reviews/2026-08-24-spec-gap-review.md)
- [`docs/IMPLEMENTATION-STATUS.md`](../IMPLEMENTATION-STATUS.md)
