"""Was beim Ingest mit einem Bild geschieht - und was nicht."""

from __future__ import annotations

import io

import pytest
from PIL import Image

from sidebyside.attachments import images
from sidebyside.attachments.limits import MediaRule, rule_for

HERSTELLER = "GeheimKamera GmbH"
KOMMENTAR = "privater Kommentar"
SOFTWARE = "SpionageApp 1.0"


def _rule(mime: str = "image/jpeg"):  # type: ignore[no-untyped-def]
    regel = rule_for(mime)
    assert regel is not None
    return regel


def _mit_metadaten(format: str = "JPEG", groesse: tuple[int, int] = (32, 24)) -> bytes:
    bild = Image.new("RGB", groesse, (10, 20, 30))
    exif = Image.Exif()
    exif[0x9003] = "2025:06:13 21:15:00"
    exif[0x0112] = 3
    exif[0x010F] = HERSTELLER
    exif[0x0131] = SOFTWARE
    exif[0x9286] = KOMMENTAR
    exif[0x8825] = {1: "N", 2: (52.0, 31.0, 0.0), 3: "E", 4: (13.0, 24.0, 0.0)}
    puffer = io.BytesIO()
    bild.save(puffer, format, exif=exif.tobytes())
    return puffer.getvalue()


def test_location_and_device_metadata_do_not_survive() -> None:
    roh = _mit_metadaten()
    assert HERSTELLER.encode() in roh

    ergebnis = images.process(roh, _rule())

    assert HERSTELLER.encode() not in ergebnis.content
    assert SOFTWARE.encode() not in ergebnis.content
    assert KOMMENTAR.encode() not in ergebnis.content
    assert Image.open(io.BytesIO(ergebnis.content)).getexif() == {}


def test_the_allowlist_is_extracted_before_stripping() -> None:
    ergebnis = images.process(_mit_metadaten(), _rule())
    assert ergebnis.captured_at is not None
    assert ergebnis.captured_at.year == 2025
    assert ergebnis.orientation == 3


def test_unknown_segments_do_not_survive_either() -> None:
    """Allowlist, nicht Blacklist: auch ein unbekanntes Feld faellt weg."""
    bild = Image.new("RGB", (16, 16))
    exif = Image.Exif()
    exif[0x9C9E] = "unbekanntes Feld"  # XPAuthor - nicht auf der Allowlist
    puffer = io.BytesIO()
    bild.save(puffer, "JPEG", exif=exif.tobytes())

    ergebnis = images.process(puffer.getvalue(), _rule())
    assert "unbekanntes Feld".encode("utf-16-le") not in ergebnis.content
    assert Image.open(io.BytesIO(ergebnis.content)).getexif() == {}


def test_dimensions_come_from_the_decoder() -> None:
    ergebnis = images.process(_mit_metadaten(groesse=(40, 25)), _rule())
    assert (ergebnis.width, ergebnis.height) == (40, 25)


def test_declared_type_must_match_the_decoded_one() -> None:
    puffer = io.BytesIO()
    Image.new("RGB", (8, 8)).save(puffer, "PNG")
    with pytest.raises(images.ImageRejectedError) as fehler:
        images.process(puffer.getvalue(), _rule("image/jpeg"))
    assert fehler.value.code == "IMAGE_TYPE_MISMATCH"


def test_garbage_is_rejected() -> None:
    with pytest.raises(images.ImageRejectedError) as fehler:
        images.process(b"das ist kein bild", _rule())
    assert fehler.value.code == "IMAGE_UNREADABLE"


def test_truncated_data_is_rejected_instead_of_half_decoded() -> None:
    ganz = _mit_metadaten(groesse=(64, 64))
    with pytest.raises(images.ImageRejectedError):
        images.process(ganz[: len(ganz) // 3], _rule())


def test_oversized_dimensions_are_rejected() -> None:
    regel = _rule()
    puffer = io.BytesIO()
    Image.new("RGB", (64, 64)).save(puffer, "JPEG")
    eng = MediaRule(
        mime_type=regel.mime_type,
        media_type=regel.media_type,
        max_size=regel.max_size,
        max_pixels=100,
        max_edge=10,
    )
    with pytest.raises(images.ImageRejectedError) as fehler:
        images.process(puffer.getvalue(), eng)
    assert fehler.value.code == "IMAGE_TOO_LARGE"


def test_heif_goes_through_the_same_path() -> None:
    puffer = io.BytesIO()
    Image.new("RGB", (24, 18)).save(puffer, "HEIF")
    ergebnis = images.process(puffer.getvalue(), _rule("image/heic"))
    assert ergebnis.width == 24
    assert ergebnis.height == 18


def test_a_thumbnail_is_produced_and_bounded() -> None:
    puffer = io.BytesIO()
    Image.new("RGB", (2000, 1000)).save(puffer, "JPEG")
    ergebnis = images.process(puffer.getvalue(), _rule())
    assert ergebnis.thumbnail is not None
    klein = Image.open(io.BytesIO(ergebnis.thumbnail))
    assert max(klein.size) <= images.THUMBNAIL_EDGE


def test_the_thumbnail_carries_no_metadata_either() -> None:
    ergebnis = images.process(_mit_metadaten(groesse=(200, 200)), _rule())
    assert ergebnis.thumbnail is not None
    assert HERSTELLER.encode() not in ergebnis.thumbnail
    assert Image.open(io.BytesIO(ergebnis.thumbnail)).getexif() == {}
