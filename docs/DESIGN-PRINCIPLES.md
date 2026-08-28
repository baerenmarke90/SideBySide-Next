# Design-Prinzipien für SideBySide Next

**Status:** Verbindliche Grundlage für Web und App  
**Version:** 1.0  
**Gültig ab:** 24. August 2026  
**Markenversprechen:** *Gemeinsam leben. Privat verbunden.*

Dieses Dokument übersetzt die Produktidee von SideBySide Next in verbindliche
Gestaltungsregeln. Es gilt für Produktoberflächen, Website, Store-Auftritt,
Marketingseiten und neue Funktionen.

Die Begriffe **MUSS**, **SOLLTE** und **KANN** beschreiben die Verbindlichkeit.
Bei Konflikten gilt diese Reihenfolge:

1. Datenschutz und Sicherheit
2. Barrierefreiheit
3. Verständlichkeit und Nutzbarkeit
4. Konsistenz
5. Markenwirkung
6. visuelle Neuheit

## Design Tokens und semantische Werte

Wiederverwendbare visuelle Werte MÜSSEN über semantische Design-Tokens ausgedrückt werden.
Komponenten beschreiben die Bedeutung eines Wertes und nicht dessen aktuelle technische Ausprägung.

- Farbrollen, Abstände, Radien, Typografie, Schatten und ähnliche wiederverwendbare Werte gehören an die Token-Definition-Grenze.
- Komponenten verwenden vorhandene Tokens über `var(...)` statt wiederholte Literale einzuführen.
- Token-Namen beschreiben die Rolle im Interface, zum Beispiel `--color-text-inverse-muted` statt `--white-90`.
- Theme-, Branding- und Accessibility-sensitive Werte sind bevorzugte Token-Kandidaten.
- Echte Einzelfälle dürfen lokal bleiben, wenn kein sinnvoller Wiederverwendungs- oder Bedeutungswert entsteht.
- Bestehende Token-Strukturen werden erweitert, bevor neue parallele Abstraktionen entstehen.

Die vollständige Naming- und Ausnahme-Regel steht in `docs/DESIGN-TOKEN-POLICY.md`.

## 1. Gestaltungsziel

SideBySide soll sich wie ein ruhiger, privater Raum für zwei Menschen anfühlen:
warm, persönlich und hochwertig, aber niemals kitschig oder überladen.

Jede Oberfläche beantwortet innerhalb weniger Sekunden:

- Wo bin ich?
- Was ist hier gemeinsam und was ist privat?
- Was ist der nächste sinnvolle Schritt?
- Welche Daten oder Berechtigungen sind betroffen?

