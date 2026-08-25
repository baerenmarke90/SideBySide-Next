"""Bilder pruefen, bereinigen und verkleinern.

Das ist die Stelle, an der fremde Bytes zum ersten Mal interpretiert
werden. Sie laeuft ausschliesslich im Hintergrundjob, nie im Requestpfad,
und sie geht davon aus, dass jede Datei boesartig sein kann.

Drei Regeln:

- Es wird nichts geglaubt, was in der Datei steht. Format, Masse und Typ
  stammen aus dem Dekoder, nicht aus Header- oder Clientangaben.
- Es wird nur weitergereicht, was auf der Allowlist steht. Metadaten werden
  nicht gefiltert, sondern verworfen und einzeln wieder aufgebaut.
- Was sich nicht sicher verarbeiten laesst, scheitert - es wird nicht
  "so gut wie moeglich" gespeichert.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from datetime import datetime

import pillow_heif
from PIL import Image, ImageFile, UnidentifiedImageError

from sidebyside.attachments.limits import MediaRule

pillow_heif.register_heif_opener()

ImageFile.LOAD_TRUNCATED_IMAGES = False
"""Eine abgeschnittene Datei ist ein Fehler, kein halbes Bild.

Pillow wuerde sonst stillschweigend liefern, was es lesen konnte - und der
gespeicherte Rest saehe wie ein gueltiges Bild aus."""

THUMBNAIL_EDGE = 512
"""Laengste Kante des Thumbnails. Gross genug fuer eine Listendarstellung
auf einem dichten Display, klein genug, dass eine Timeline nicht die
Originalgroesse ueber die autorisierte Leseroute zieht."""

_PILLOW_FORMAT_BY_MIME = {
    "image/jpeg": "JPEG",
    "image/png": "PNG",
    "image/webp": "WEBP",
    "image/heic": "HEIF",
    "image/heif": "HEIF",
}

_MIME_BY_PILLOW_FORMAT = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
    "HEIF": "image/heic",
}

_EXIF_DATETIME_ORIGINAL = 0x9003
_EXIF_ORIENTATION = 0x0112


class ImageRejectedError(Exception):
    """Das Bild ist nicht verarbeitbar.

    Traegt einen stabilen Code und nie den Text des Parsers: der koennte
    Dateiinhalt enthalten und landete damit in Logs und Fehlerfeldern.
    """

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class ProcessedImage:
    mime_type: str
    width: int
    height: int
    captured_at: datetime | None
    orientation: int | None
    content: bytes
    thumbnail: bytes | None


def _guard_decompression_bomb(rule: MediaRule) -> None:
    """Pillows eigene Bombengrenze auf unsere Pixelgrenze setzen.

    Ohne das entscheidet ein Bibliotheksstandard darueber, wie viel
    Speicher eine fremde Datei belegen darf.
    """
    Image.MAX_IMAGE_PIXELS = rule.max_pixels


def _extract_allowlist(image: Image.Image) -> tuple[datetime | None, int | None]:
    """Genau die Felder aus M2-D14 - und sonst nichts.

    Es wird einzeln gelesen, nicht gefiltert: eine Filterliste muesste alle
    unerwuenschten Felder kennen, diese Schleife kennt nur die erwuenschten.
    """
    captured_at: datetime | None = None
    orientation: int | None = None
    try:
        exif = image.getexif()
    except Exception:  # ein kaputter EXIF-Block ist kein Grund, das Bild zu verwerfen
        return None, None

    raw_datetime = exif.get(_EXIF_DATETIME_ORIGINAL)
    if isinstance(raw_datetime, str):
        try:
            captured_at = datetime.strptime(raw_datetime.strip(), "%Y:%m:%d %H:%M:%S")
        except ValueError:
            captured_at = None

    raw_orientation = exif.get(_EXIF_ORIENTATION)
    if isinstance(raw_orientation, int) and 1 <= raw_orientation <= 8:
        orientation = raw_orientation

    return captured_at, orientation


def _rebuild_without_metadata(image: Image.Image, pillow_format: str) -> bytes:
    """Neu schreiben statt Felder loeschen.

    Ein frisches Image-Objekt aus den reinen Pixeldaten traegt keinen
    Herstellerblock, kein eingebettetes Vorschaubild und kein unbekanntes
    Segment mehr - auch keines, das wir nicht kennen.
    """
    sauber = Image.new(image.mode, image.size)
    # paste und nicht putdata(list(...)): letzteres baute fuer ein 40-MP-Bild
    # eine Python-Liste mit vierzig Millionen Tupeln auf, bevor irgendetwas
    # geschrieben waere. paste kopiert die Pixel in C.
    sauber.paste(image)

    ziel = io.BytesIO()
    optionen: dict[str, object] = {}
    if pillow_format == "JPEG":
        optionen["quality"] = 92
    sauber.save(ziel, format=pillow_format, **optionen)
    return ziel.getvalue()


def _thumbnail(image: Image.Image) -> bytes | None:
    """Ein Thumbnail, oder nichts.

    Ein Fehlschlag ist ein Darstellungs- und kein Sicherheitsproblem
    (M2-D15) und darf das Attachment nicht scheitern lassen.
    """
    try:
        klein = image.copy()
        klein.thumbnail((THUMBNAIL_EDGE, THUMBNAIL_EDGE))
        if klein.mode not in ("RGB", "L"):
            klein = klein.convert("RGB")
        ziel = io.BytesIO()
        klein.save(ziel, format="JPEG", quality=82)
        return ziel.getvalue()
    except Exception:  # siehe Docstring
        return None


def process(data: bytes, rule: MediaRule) -> ProcessedImage:
    """Ein hochgeladenes Bild pruefen, bereinigen und verkleinern.

    Die Bytes liegen vollstaendig vor: dekodieren heisst ohnehin, das Bild
    im Speicher aufzubauen, und die Groesse ist durch das Limit aus M2-D04
    gedeckelt. Ein Streamingdekoder waere hier nur scheinbar sparsamer.
    """
    _guard_decompression_bomb(rule)

    try:
        image = Image.open(io.BytesIO(data))
        image.load()
    except Image.DecompressionBombError as error:
        raise ImageRejectedError("IMAGE_TOO_LARGE") from error
    except (UnidentifiedImageError, OSError, ValueError) as error:
        raise ImageRejectedError("IMAGE_UNREADABLE") from error

    erkanntes_format = (image.format or "").upper()
    erkannter_mime = _MIME_BY_PILLOW_FORMAT.get(erkanntes_format)
    if erkannter_mime is None:
        raise ImageRejectedError("IMAGE_TYPE_NOT_ALLOWED")

    # Der angekuendigte Typ muss zum erkannten passen. HEIC und HEIF sind
    # dasselbe Containerformat und duerfen einander vertreten.
    erwartetes_format = _PILLOW_FORMAT_BY_MIME.get(rule.mime_type)
    if erwartetes_format != erkanntes_format:
        raise ImageRejectedError("IMAGE_TYPE_MISMATCH")

    breite, hoehe = image.size
    if rule.max_edge is not None and max(breite, hoehe) > rule.max_edge:
        raise ImageRejectedError("IMAGE_TOO_LARGE")
    if rule.max_pixels is not None and breite * hoehe > rule.max_pixels:
        raise ImageRejectedError("IMAGE_TOO_LARGE")

    captured_at, orientation = _extract_allowlist(image)

    try:
        inhalt = _rebuild_without_metadata(image, erkanntes_format)
    except (OSError, ValueError) as error:
        # Nicht sicher bereinigbar heisst FAILED - niemals ungestrippt
        # speichern (M2-D14).
        raise ImageRejectedError("IMAGE_NOT_SANITIZABLE") from error

    return ProcessedImage(
        mime_type=erkannter_mime,
        width=breite,
        height=hoehe,
        captured_at=captured_at,
        orientation=orientation,
        content=inhalt,
        thumbnail=_thumbnail(image),
    )
