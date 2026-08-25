# M2 Video Processing

**Status:** Verbindliche Betriebs- und Sicherheitsentscheidung zu M2-D23 / #88  
**Datum:** 2026-08-25  
**Scope:** MP4/QuickTime-Validierung, Metadatenbereinigung und genau ein Posterframe je Video

Diese Entscheidung wurde vor der Runtime-Implementierung von #88 festgehalten und wird hier auf den tatsächlich validierten Lieferstand synchronisiert. M2-D04, D05, D14, D15 und D23 bleiben maßgeblich.

## 1. Parser und Betriebsmodell

SideBySide Next verwendet `ffprobe` zur serverseitigen Bestimmung von Container, Streams, Dauer, Auflösung und technischen Metadaten. `ffmpeg` wird ausschließlich für einen metadatenbereinigenden **Remux mit Stream-Copy** und für genau einen Posterframe eingesetzt.

Nicht Teil von M2 sind Video-/Audio-Transcoding, mehrere Qualitätsstufen, adaptives Streaming und Audioextraktion. Es gibt dafür auch keinen Fallback.

Das Self-Hosted-Compose-Deployment installiert `ffmpeg` und `ffprobe` im gemeinsam gebauten Backend-Image. Auf dem Docker-Host ist keine separate Installation erforderlich. Fremde Videodateien werden ausschließlich im Worker verarbeitet.

## 2. Runtime-Killswitch

Videoverarbeitung kann pro Installation deaktiviert werden:

```env
SBS_FFMPEG_ENABLED=false
```

Der Schalter ist ein Runtime-Killswitch, kein alternativer Buildpfad:

- `true` ist der Standard; MP4 und QuickTime können verarbeitet werden.
- `false` weist neue Video-Uploads fail-closed mit `ATTACHMENT_TYPE_NOT_ALLOWED` ab.
- Der Worker prüft den Schalter zusätzlich unmittelbar vor der Verarbeitung. Ein bereits eingereihter Job startet nach einem späteren Abschalten kein ffmpeg/ffprobe mehr.
- Bilder und der übrige Dienst bleiben aktiv.
- Die Binaries bleiben im Image, damit ein einziges reproduzierbares Artefakt existiert.

## 3. Reproduzierbarkeit und Supply Chain

Die Produktion verwendet das bereits gepinnte Debian-basierte Python-Image. Das Debian-Paket `ffmpeg` ist exakt gepinnt auf:

```text
7:7.1.5-0+deb13u1
```

Die CI baut das Produktionsimage frisch und prüft die tatsächlich installierte Paketversion mit `dpkg-query` gegen diesen Pin. Ein unversioniertes `apt-get install ffmpeg` ist nicht zulässig.

`uv audit` bleibt unverändert für Python-Abhängigkeiten aktiv. Da es Debian-Systempakete nicht abdeckt, prüft ein separater Gate den offiziellen Debian Security Tracker für Source-Package `ffmpeg` und Release `trixie`:

1. Eine neuere trixie-/Security-Paketversion als der Repository-Pin macht den Gate rot.
2. `undetermined` macht den Gate rot.
3. Ein offener Fund macht den Gate rot, sofern Debian ihn nicht ausdrücklich als `postponed` oder `unimportant` klassifiziert.
4. `postponed` und `unimportant` werden sichtbar im CI-Log ausgegeben und als Debian-Risikoklassifikation akzeptiert, nicht still ignoriert.
5. Unbekanntes Schema, unbekannter Status, Netzwerk-/Parsefehler oder unvollständige Tracker-Daten führen fail-closed zum Fehler.

Die Imagegröße wird nach jedem frischen CI-Build protokolliert. API und Worker bleiben auf demselben Artefakt; es gibt keine kleinere, abweichende ffmpeg-Runtime.

## 4. Vertrauen und Formatbestimmung

Clientangaben dienen nur der Vorabprüfung. Der Worker bestimmt selbst:

- tatsächliche Objektgröße,
- ISO-BMFF-`ftyp`/Brand,
- das von ffprobe erkannte Containerformat,
- den primären Videostream,
- Dauer,
- Breite und Höhe,
- die M2-D14-Allowlist.

Dateiendung, Originalname, deklarierter MIME-Typ, deklarierte Dauer und deklarierte Auflösung können diese Werte nicht überschreiben.

Zulässig sind nur MP4 und QuickTime/MOV innerhalb M2-D04. Unbekannte ISO-BMFF-Brands, weitere Container, Audio-only-Dateien, fehlende oder mehrdeutige Videostreams und Widersprüche zwischen angekündigtem und tatsächlichem Container scheitern fail-closed.

## 5. D04-Limits und Storage-Grenzen

Der Worker erzwingt am gespeicherten Objekt:

- maximal **250 MiB**,
- maximal **180 Sekunden**,
- maximal **3840 × 2160**, rotationsunabhängig als lange Kante `<= 3840` und kurze Kante `<= 2160`.

Die Dauer muss positiv und endlich sein. Das persistierte `durationSeconds` wird auf volle Sekunden aufgerundet.

Für S3 wird die Objektgröße per `HEAD`/`Content-Length` geprüft, bevor der Body verarbeitet wird. Der anschließende GET ist streamend; der Worker kopiert höchstens `max_size + 1` Byte in eine private Temp-Datei. Weicht die tatsächlich gelesene Größe von der zuvor gemeldeten Providergröße ab, scheitert die Validierung. Damit kann auch ein inkonsistenter Provider-Response keinen unbeschränkten RAM- oder Plattenverbrauch verursachen.

LocalMediaStore liefert die Größe über `stat()`. Unabhängig vom Adapter bleibt die begrenzte Kopie die zweite Schutzschicht.

## 6. M2-D14: Metadatenbereinigung

Vor dem Strippen werden nur diese Werte extrahiert:

- Aufnahmezeitpunkt,
- Orientierung,
- Breite,
- Höhe,
- Dauer.

Aufnahmezeitpunkt und Orientierung werden wie bei Bildern als ProtectedPayload behandelt. Breite, Höhe und Dauer sind technische Attachmentfelder.

Das gespeicherte Video ist nicht der Upload mit einzelnen gelöschten Tags. ffmpeg baut einen neuen Container aus genau:

- dem ersten primären Videostream,
- optional dem ersten Audiostream,
- `-c copy`, also ohne Video-/Audio-Neukodierung.

Globales Metadata-Mapping und Chapters sind deaktiviert. Untertitel-, Data-, Attachment-, Cover- und weitere Streams werden nicht übernommen.

Danach wird die bereinigte Datei erneut geprobt. Zulässig sind nur server-/muxerbedingte technische Containerfelder wie Brand, Encoder, Sprache, Handler und `vendor_id` sowie eine sichere Display-Matrix für Orientierung. Unbekannte verbleibende Metadaten machen das Ergebnis unsicher und das Attachment `FAILED`.

GPS-/Location-Metadaten dürfen nach `READY` weder im bereinigten Video noch im Posterframe verbleiben. Der Produktionscontainer-Smoke erzeugt dafür reale MP4- und MOV-Fixtures mit Location-Daten und prüft deren Entfernung.

## 7. Prozessausführung und Isolation

ffmpeg/ffprobe werden nur als Argumentlisten ohne Shell gestartet:

- `shell=False`,
- stdin geschlossen / `-nostdin`,
- lokale `file`-Protokoll-Allowlist,
- servergenerierte Temp-Dateinamen,
- minimale Prozessumgebung,
- eigene Prozessgruppe,
- keine ffmpeg-/ffprobe-Stderr-Ausgabe in fachlichen Fehlern, DB-Feldern oder Logs.

### Harte Subprozessgrenzen

| Schritt | Wall time | CPU | Adressraum | Ausgabegroesse |
|---|---:|---:|---:|---:|
| ffprobe | 10 s | 8 s | 768 MiB | Probe-JSON max. 1 MiB |
| sicherer Remux | 45 s | 30 s | 768 MiB | max. 250 MiB |
| Posterframe | 20 s | 12 s | 768 MiB | max. 4 MiB |

Die ursprünglich geplanten 512 MiB erwiesen sich im Test mit dem exakt gepinnten Debian-ffmpeg für Poster/4K als zu knapp; **768 MiB** ist deshalb der validierte Kindprozess-Rahmen.

Zusätzlich gelten Limits für offene File Descriptors, Prozesszahl, Core-Dumps und Dateigröße. Poster- und Filterthreads werden begrenzt. Bei Timeout wird die gesamte Prozessgruppe beendet.

Der Compose-Worker bildet die zweite Schutzschicht:

- maximal **1 CPU**,
- **1 GiB RAM**,
- **64 PIDs**.

Diese Containerlimits ersetzen die Kindprozesslimits nicht.

## 8. Temporärer Speicher

Videoverarbeitung nutzt ein privates servergeneriertes Temp-Verzeichnis:

- Eingabe: maximal 250 MiB plus höchstens ein Prüfbyte,
- bereinigtes Video: maximal 250 MiB,
- Poster: maximal 4 MiB.

Temp-Dateien werden im Erfolgs- und Fehlerfall entfernt. Erst das vollständig validierte und erneut geprüfte Sanitized-Objekt ersetzt das hochgeladene Original im MediaStore.

## 9. Posterframe und Variantenmodell

M2-D15 erlaubt je Attachment höchstens eine abgeleitete Still-Variante. Der bestehende serverkontrollierte Slot `thumbnail` wird deshalb weiterverwendet:

- `mediaType=IMAGE`: `thumbnail` enthält das Bild-Thumbnail,
- `mediaType=VIDEO`: `thumbnail` enthält den Posterframe.

Es gibt kein neues `hasPoster`, keinen zweiten Storage-Key-Typ und keine zweite ACL. `hasThumbnail`, Parent-Autorisierung, S3-Signing und Cleanup gelten unverändert.

Der Posterframe entsteht erst aus dem bereinigten Video. ffmpeg erzeugt ein Bild mit maximal 512 Pixeln an der langen Kante. Pillow dekodiert dieses Bild anschließend und schreibt aus reinen Pixeln ein neues JPEG. Dadurch übernimmt der finale Posterframe keine EXIF-/GPS-Metadaten.

Ein Fehler nur bei Poster-Erzeugung oder Variantenspeicherung ist nicht fatal. Das sicher bereinigte Video darf `READY` werden und `hasThumbnail=false` behalten.

## 10. Autorisierung und Fehlersemantik

Die vorhandene Attachment-Autorisierung bleibt unverändert. Original und Poster folgen nach Bindung ausschließlich der Lesbarkeit des Parents; ungebundene READY-Attachments bleiben auf Owner + Bindungsfenster beschränkt.

Stabile Fehlersemantik:

- falscher/unbekannter Container oder MIME-Spoofing → `FAILED`,
- tatsächliche Größe über D04 → `ATTACHMENT_TOO_LARGE`,
- Dauer/Auflösung außerhalb D04 → `FAILED`,
- abgeschnittene/manipulierte Datei → `FAILED`,
- ffprobe/ffmpeg Timeout oder Prozessfehler → `FAILED`,
- nicht sicher bereinigbare Metadaten → `FAILED`,
- reiner Posterfehler → Video bleibt nutzbar, keine Variante,
- deaktiviertes `SBS_FFMPEG_ENABLED` → Video wird fail-closed nicht verarbeitet.

Providerupload, Magic-Bytes oder ein einzelner erfolgreicher ffprobe-Lauf sind niemals allein ausreichend für `READY`.

## 11. Verifikation für #88

CI und Tests weisen mindestens nach:

- MP4 und QuickTime/MOV,
- serverseitig ermittelte Dauer und Auflösung,
- 250-MiB-, 180-Sekunden- und 3840×2160-Grenzen,
- MIME-/Container-Spoofing fail-closed,
- abgeschnittene Dateien fail-closed,
- Location-Daten nach Sanitizing entfernt,
- Posterframe metadatenfrei,
- Posterfehler nicht fatal,
- Killswitch am API-Eingang und erneut im Worker,
- S3-HEAD vor Body-Verarbeitung und bounded Streaming,
- Local-/S3-Lifecycle,
- Debian-Security-Tracker-Gate,
- exakte ffmpeg-Version im Produktionsimage,
- Non-Root-Container und Worker-Ressourcenrahmen,
- realer MP4/MOV-Smoke im frisch gebauten Produktionscontainer,
- vollständige bestehende CI und Integrationstests ohne Skip.

Keine Datenmigration ist für #88 erforderlich: Dauer/Breite/Höhe existieren bereits, und der vorhandene `thumbnail`-Variantenslot wird für den Posterframe wiederverwendet.

## 12. Verweise

- #88 – Video und Posterframes im Attachment-Lifecycle
- #85 – M2-D23 / Reihenfolge und Parser
- #79 – erster Bild-Media-Slice
- `DECISION-LOG.md`
- `MEDIA-PIPELINE.md`
- `../DEPENDENCIES.md`
- `../SELF-HOSTING.md`
