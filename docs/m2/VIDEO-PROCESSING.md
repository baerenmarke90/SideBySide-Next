# M2 Video Processing

**Status:** Verbindliche Betriebs- und Sicherheitsentscheidung zu M2-D23 / #88  
**Datum:** 2026-08-25  
**Scope:** MP4/QuickTime-Validierung, Metadatenbereinigung und ein Posterframe je Video

Diese Entscheidung wird vor der Runtime-Implementierung von #88 festgehalten. Sie konkretisiert M2-D23 fuer den Video-Slice und laesst M2-D04, M2-D05, M2-D14 und M2-D15 unveraendert massgeblich.

## 1. Parser und Betriebsmodell

SideBySide Next verwendet `ffprobe` zum serverseitigen Ermitteln von Container, Streams, Dauer, Aufloesung und der M2-D14-Allowlist. `ffmpeg` wird ausschliesslich fuer einen metadatenbereinigenden **Remux ohne Transcoding** und fuer genau einen Posterframe verwendet.

Nicht Teil von M2 sind Video-Transcoding, mehrere Qualitaetsstufen, adaptives Streaming und Audioextraktion. Der Video-Slice darf diese Funktionen weder implizit aktivieren noch als Fallback verwenden.

`ffmpeg` und `ffprobe` sind Systembinaries. Das offizielle Self-Hosted-Compose-Deployment installiert sie deshalb im gemeinsam gebauten Backend-Image; auf dem Docker-Host ist keine separate ffmpeg-Installation erforderlich. API, Migration und Worker verwenden dasselbe reproduzierbare Image, die fremden Videodateien werden jedoch ausschliesslich im Worker interpretiert.

## 2. Reproduzierbarkeit und Supply Chain

Die Runtime basiert auf dem bereits gepinnten Debian-basierten Python-Image. Das Debian-Paket `ffmpeg` wird mit der exakten Version

```text
7:7.1.5-0+deb13u1
```

installiert. Ein unversioniertes `apt-get install ffmpeg` ist nicht zulaessig. Die installierte Version wird im Supply-Chain-Job aus dem frisch gebauten Produktionscontainer gelesen und gegen den Pin geprueft.

`uv audit` bleibt unveraendert fuer Python-Abhaengigkeiten aktiv, deckt Debian-Systempakete aber nicht ab. Fuer ffmpeg kommt deshalb ein zusaetzlicher, enger Nachweisweg hinzu:

1. Die installierte Version muss exakt dem Repository-Pin entsprechen.
2. Der Debian Security Tracker fuer das Source-Package `ffmpeg` und die Distribution `trixie` wird geprueft.
3. Ist fuer trixie eine neuere Security-/Stable-Version verfuegbar als der Pin, schlaegt der Gate fehl.
4. Ein fuer trixie als offen verwundbar gefuehrter Fund schlaegt fehl, sofern Debian ihn nicht ausdruecklich als `postponed` oder `unimportant` einstuft.
5. `postponed` und `unimportant` werden im CI-Log sichtbar ausgegeben. Sie sind eine explizite Debian-Risikoeinstufung und kein stilles Ignorieren.
6. Ist die Tracker-Antwort unlesbar oder ihr erwartetes Schema nicht auswertbar, schlaegt die Pruefung fail-closed fehl.

Der Systempaket-Gate ersetzt keinen vorhandenen Gate und darf insbesondere `uv audit`, Dependabot oder den Produktionscontainer-Build nicht abschwaechen.

### Imagegroesse

ffmpeg bringt Codec-/Containerbibliotheken in das Backend-Image und vergroessert es merklich. Das wird fuer M2 akzeptiert, weil ffprobe/ffmpeg die freigegebenen Smartphone-Videoformate robust untersuchen und bereinigen koennen und ein eigener ISO-BMFF-/Codec-Parser an der groessten Angriffsflaeche des Produkts die schlechtere Sicherheitsentscheidung waere. Die Imagegroesse wird nicht durch eine zweite, abweichende Worker-Runtime optimiert; API und Worker bleiben auf demselben reproduzierbaren Artefakt.

## 3. Vertrauen und Formatbestimmung

Clientangaben sind nur Vorab-UX und niemals Sicherheitsquelle. Der Worker bestimmt selbst:

- die tatsaechliche Objektgroesse,
- ISO-BMFF/Magic-Bytes und Brand,
- das von ffprobe erkannte Containerformat,
- den primaeren Videostream,
- Dauer,
- Breite und Hoehe,
- die erlaubten technischen Metadaten.

Dateiendung, Originalname, deklarierter MIME-Typ, deklarierte Dauer und deklarierte Aufloesung koennen diese Werte nicht ueberschreiben.

Zulaessig sind ausschliesslich MP4 und QuickTime/MOV innerhalb M2-D04. Unbekannte ISO-BMFF-Brands, weitere Video-Container, Audio-only-Dateien, fehlende/mehrdeutige primaere Videostreams sowie Widersprueche zwischen angekuendigtem und tatsaechlichem Container scheitern fail-closed.

## 4. M2-D04-Limits

Der Worker erzwingt am gespeicherten Objekt:

- maximal **250 MiB**,
- maximal **180 Sekunden**,
- maximal **3840 x 2160** Pixel, rotationsunabhaengig als lange Kante `<= 3840` und kurze Kante `<= 2160`.

Die Dauer muss positiv, endlich und parsebar sein. Fuer das persistierte ganzzahlige `durationSeconds` wird auf volle Sekunden **aufgerundet**, damit keine Datei durch Abrunden unter die 180-Sekunden-Grenze faellt.

Bei S3 wird die Provider-Objektgroesse per HEAD geprueft, bevor der Worker den Body abruft. Zusaetzlich ist jeder lokale Kopiervorgang auf das M2-D04-Limit begrenzt. Ein manipulierter oder inkonsistenter Provider-Response kann so keinen unbeschraenkten RAM-/Plattenverbrauch erzwingen.

## 5. M2-D14: Metadatenbereinigung

Vor dem Strippen wird nur die bereits entschiedene Allowlist extrahiert:

- Aufnahmezeitpunkt,
- Orientierung,
- Breite,
- Hoehe,
- Dauer.

Aufnahmezeitpunkt und Orientierung werden wie bei Bildern als ProtectedPayload behandelt. Breite, Hoehe und Dauer sind die bereits fuer die Limitpruefung benoetigten serverseitigen technischen Felder.

Das gespeicherte Video ist **nicht** der Upload mit geloeschten Einzel-Tags. ffmpeg baut einen neuen Container aus genau einem primaeren Videostream und hoechstens einem primaeren Audiostream mit Stream-Copy (`-c copy`) auf. Globales Metadata-Mapping und Chapters sind deaktiviert; Untertitel-, Data-, Attachment-, Cover- und weitere Streams werden nicht uebernommen. Es findet keine Video-/Audio-Neukodierung statt.

Anschliessend wird das bereinigte Ergebnis erneut geprobt. Unbekannte oder nicht erlaubte verbleibende Metadaten, eine ungueltige Struktur oder ein erneut verletztes D04-Limit machen die Bereinigung ungueltig. Dann endet das Attachment `FAILED`; die hochgeladenen Originalbytes werden nie als `READY` ausgeliefert.

GPS-/Location-Metadaten, insbesondere ISO-6709-/QuickTime-Location-Felder, duerfen nach `READY` weder im bereinigten Container noch im Posterframe vorhanden sein.

## 6. Prozessausfuehrung und Isolation

ffmpeg/ffprobe werden ausschliesslich als Argumentlisten ohne Shell gestartet. Es gilt:

- `shell=False`, keine zusammengesetzten Kommando-Strings,
- keine Benutzerdateinamen oder Storage Keys als vom Client kontrollierte Argumentbestandteile,
- Temporaerdateien mit servergenerierten Namen in einem privaten Temp-Verzeichnis,
- `stdin` geschlossen / `-nostdin`,
- lokale `file`-Protokoll-Allowlist; keine Netzwerkprotokolle fuer fremde Eingaben,
- minimale Prozessumgebung,
- neuer Prozess-Session/Prozessgruppe fuer sicheres Beenden bei Timeout,
- keine Parserausgabe in fachlichen Fehlern, Datenbankfeldern oder Logs.

### Harte Subprozessgrenzen

Jeder Aufruf erhaelt eine Wall-Clock-Grenze. Der Runtime-Slice verwendet als Obergrenzen:

| Schritt | Wall time | CPU | Adressraum | Ausgabegroesse |
|---|---:|---:|---:|---:|
| ffprobe | 10 s | 8 s | 512 MiB | keine Mediendatei |
| sicherer Remux | 45 s | 30 s | 512 MiB | 250 MiB |
| Posterframe | 20 s | 12 s | 512 MiB | 4 MiB |

Zusaetzlich werden offene File Descriptors, Child-Prozesse und Core-Dumps per OS-Ressourcenlimit begrenzt. ffmpeg-Threads werden begrenzt; Posterfilter laufen nicht mit unbeschraenkter Parallelitaet.

Der Compose-Worker erhaelt als zweite Schutzschicht einen Container-Rahmen von maximal 1 CPU, 1 GiB RAM und 64 PIDs. Diese Containergrenze ersetzt die pro Kind gesetzten Subprozesslimits nicht.

Bei Timeout wird die gesamte Prozessgruppe hart beendet. Ein Timeout, Crash, Signal, nicht-null Exit oder unlesbare Parserantwort erzeugt nur einen stabilen nicht sensitiven Fehlercode. Der bestehende Job-Worker verarbeitet danach weitere Jobs; ein einzelnes fremdes Video darf den Worker nicht dauerhaft blockieren.

## 7. Maximale Ausgabe und temporärer Speicher

Der Upload wird nicht unter seinem Originalnamen auf dem Dateisystem verarbeitet. Der Worker schreibt in ein privates Temp-Verzeichnis und uebernimmt nur Dateien, die alle nachgelagerten Pruefungen bestanden haben.

- Eingabe: maximal 250 MiB, bereits vor bzw. waehrend des Kopierens begrenzt.
- Bereinigtes Video: maximal 250 MiB; OS-Dateigroessenlimit plus explizite `stat()`-Pruefung.
- Posterframe: maximal 4 MiB.
- Temporaere Dateien werden im Erfolgs- wie Fehlerfall entfernt.

Ein Remux, dessen Ausgabe die Grenze ueberschreitet, scheitert fail-closed. Die Originalbytes bleiben dadurch niemals als vermeintlich bereinigtes `READY`-Objekt bestehen.

## 8. Posterframe und Variantenmodell

M2-D15 erlaubt pro Attachment hoechstens **eine** abgeleitete Still-Variante. Der bestehende kontrollierte Varianten-Slot `thumbnail` wird deshalb bewusst nicht um einen zweiten `poster`-Key oder eine eigene Berechtigungsentitaet erweitert:

- bei `mediaType=IMAGE` enthaelt `thumbnail` das Bild-Thumbnail,
- bei `mediaType=VIDEO` enthaelt `thumbnail` den Posterframe.

Damit bleiben bestehende `hasThumbnail`-/Variantensemantik, Parent-Autorisierung, S3-Signing und Cleanup identisch. Der Media-Type sagt dem Client eindeutig, ob die Still-Variante ein Thumbnail oder Poster ist. Ein neues Schemafeld `hasPoster`, eine eigene URL oder eigene ACL waeren eine zweite Berechtigungs-/Lifecycle-Wahrheit ohne fachlichen Nutzen.

Der Posterframe entsteht **erst nach** erfolgreicher Videobereinigung. Er wird aus dem bereinigten Video erzeugt, auf maximal 512 Pixel an der langen Kante verkleinert und abschliessend mit Pillow aus reinen Pixeln als frisches JPEG geschrieben. Dadurch traegt die Variante keine EXIF-, GPS- oder sonstigen eingebetteten Metadaten.

Ein Fehler ausschliesslich bei der Posterframe-Erzeugung oder beim Speichern der Variante setzt das sicher bereinigte Video nicht auf `FAILED`. Das Attachment darf `READY` werden und `hasThumbnail=false` behalten; Clients stellen das Video dann neutral ohne Poster dar.

## 9. Autorisierung, S3 und Logging

Die vorhandene Attachment-Autorisierung wird nicht veraendert. Ein Posterframe kann nur ueber denselben bereits autorisierten Attachment-Lesepfad wie das Original angefordert werden. Nach Bindung entscheidet ausschliesslich der Parent; Privacy-Wechsel und Cross-Tenant-Grenzen gelten fuer die Variante automatisch mit.

LocalMediaStore und S3MediaStore verwenden denselben Validierungsdienst und dieselben serverkontrollierten Varianten-Keys. Bei S3 bedeutet ein erfolgreicher Providerupload weiterhin nie `READY`; erst die vollstaendige serverseitige Pruefung und Bereinigung darf den Status setzen.

Nicht geloggt werden:

- Originaldateiname,
- temporaere Dateipfade,
- Storage Keys,
- Signed URLs,
- Provider-Credentials,
- ffmpeg-/ffprobe-Stderr,
- ProtectedPayload-Werte.

Zulaessig sind stabile technische Fehlercodes sowie bestehende nicht sensitive Attachment-/Job-IDs fuer die Korrelation.

## 10. Fehlersemantik

- unbekannter/falscher Container oder MIME-Spoofing -> `FAILED`, stabiler Video-Validierungscode,
- D04-Groessenverletzung -> `ATTACHMENT_TOO_LARGE`,
- Dauer/Aufloesung ausserhalb D04 -> `FAILED`, stabiler Video-Limitcode,
- unlesbare/abgeschnittene/manipulierte Datei -> `FAILED`,
- ffprobe/ffmpeg Timeout oder Prozessfehler -> `FAILED`,
- nicht sicher bereinigbare Metadaten -> `FAILED`,
- reiner Posterframe-Fehler -> Video bleibt nutzbar, keine Variante.

Providerupload allein, erfolgreiche Magic-Bytes oder erfolgreiche ffprobe-Erkennung sind niemals ausreichend fuer `READY`.

## 11. Verifikation fuer #88

Die Implementierung muss mindestens nachweisen:

- gueltiges MP4 und QuickTime/MOV,
- serverseitig ermittelte Dauer und Aufloesung,
- GPS-/Location-Metadaten nach `READY` entfernt,
- 250-MiB-, 180-Sekunden- und 3840x2160-Grenze,
- MIME-/Extension-Spoofing fail-closed,
- manipulierte/abgeschnittene Datei fail-closed,
- Timeout und Prozessfehler ohne dauerhaft blockierten Worker,
- Posterframe erzeugt und metadatenfrei,
- Posterfehler laesst das Video nutzbar,
- Variante folgt Parent-/Privacy-/Tenant-Autorisierung,
- LocalMediaStore und gemeinsamer S3-Lifecycle,
- unveraenderte Cross-Tenant-/Privacy-Grenzen,
- Supply-Chain-Gate fuer den gepinnten ffmpeg-Stand,
- vollstaendige bestehende CI.

Keine Datenmigration ist fuer #88 erforderlich, weil Dauer/Breite/Hoehe bereits serverseitige Attachmentfelder sind und der vorhandene einzige Still-Variantenslot fuer den Posterframe wiederverwendet wird.

## 12. Verweise

- #88 – Video und Posterframes im Attachment-Lifecycle
- #85 – M2-D23 / Reihenfolge und Parser
- #79 – erster Bild-Media-Slice
- `DECISION-LOG.md` – M2-D04, D05, D14, D15, D23
- `MEDIA-PIPELINE.md`
- `../DEPENDENCIES.md`
- `../SELF-HOSTING.md`
