# M2 Video Processing

**Status:** Verbindliche Betriebs- und Sicherheitsentscheidung zu M2-D23 / #88  
**Datum:** 2026-08-25  

## ffmpeg Runtime-Killswitch

Das Self-Hosted-Image enthaelt ffmpeg/ffprobe reproduzierbar. Die Videoverarbeitung kann jedoch pro Installation deaktiviert werden:

```env
SBS_FFMPEG_ENABLED=false
```

Der Schalter ist ein Runtime-Killswitch, kein alternativer Buildpfad:

- `true` (Standard): MP4/QuickTime koennen nach der M2-D23-Verarbeitung validiert werden.
- `false`: Video-Uploads werden fail-closed mit einem stabilen Nicht-verfuegbar-Fehler abgelehnt.
- Bilder und der restliche Anwendungsbetrieb bleiben unveraendert.
- Bereits installierte ffmpeg-Binaries werden nicht entfernt; dadurch bleibt das Container-Artefakt reproduzierbar.
- Der Worker prueft den Schalter erneut vor jedem Video-Processing-Job, damit auch nach einer Konfigurationsaenderung kein alter Job unerwartet ffmpeg startet.

Der Schalter ist insbesondere fuer Self-Hosted-Installationen gedacht, die bewusst keine Videoverarbeitung anbieten wollen.

## Betriebsmodell

SideBySide Next verwendet `ffprobe` zum serverseitigen Ermitteln von Container, Streams, Dauer und Aufloesung. `ffmpeg` wird ausschliesslich fuer sicheren Remux ohne Transcoding und Posterframe-Erzeugung verwendet.

