"""Die Medienregeln aus M2-D04.

Getrennt vom Lebenszyklus, damit die Grenzen an genau einer Stelle stehen.
Wer eine Zahl aendern will, aendert sie hier - und nicht an der Stelle, an
der sie gerade stoert.
"""

from __future__ import annotations

from dataclasses import dataclass

from sidebyside.attachments.models import MediaType

MEBIBYTE = 1024 * 1024


@dataclass(frozen=True)
class MediaRule:
    mime_type: str
    media_type: MediaType
    max_size: int
    max_pixels: int | None = None
    max_edge: int | None = None
    max_short_edge: int | None = None
    max_duration_seconds: int | None = None
    supported: bool = True


IMAGE_MAX_SIZE = 25 * MEBIBYTE
IMAGE_MAX_PIXELS = 40_000_000
IMAGE_MAX_EDGE = 12_000

VIDEO_MAX_SIZE = 250 * MEBIBYTE
VIDEO_MAX_DURATION_SECONDS = 180
VIDEO_MAX_LONG_EDGE = 3840
VIDEO_MAX_SHORT_EDGE = 2160


def _image(mime_type: str) -> MediaRule:
    return MediaRule(
        mime_type=mime_type,
        media_type=MediaType.IMAGE,
        max_size=IMAGE_MAX_SIZE,
        max_pixels=IMAGE_MAX_PIXELS,
        max_edge=IMAGE_MAX_EDGE,
    )


def _video(mime_type: str) -> MediaRule:
    return MediaRule(
        mime_type=mime_type,
        media_type=MediaType.VIDEO,
        max_size=VIDEO_MAX_SIZE,
        max_edge=VIDEO_MAX_LONG_EDGE,
        max_short_edge=VIDEO_MAX_SHORT_EDGE,
        max_duration_seconds=VIDEO_MAX_DURATION_SECONDS,
    )


RULES: dict[str, MediaRule] = {
    rule.mime_type: rule
    for rule in (
        _image("image/jpeg"),
        _image("image/png"),
        _image("image/webp"),
        _image("image/heic"),
        _image("image/heif"),
        _video("video/mp4"),
        _video("video/quicktime"),
    )
}


def rule_for(mime_type: str) -> MediaRule | None:
    """Die Regel zu einem MIME-Typ, oder nichts.

    Nichts heisst fail-closed abweisen. Es gibt keine Standardregel fuer
    unbekannte Typen - eine solche waere genau die Luecke, durch die ein
    nicht vorgesehenes Format hereinkaeme.
    """
    return RULES.get(mime_type.strip().lower())


def supported_mime_types() -> frozenset[str]:
    """Was der Server heute wirklich annimmt."""
    return frozenset(mime for mime, rule in RULES.items() if rule.supported)


def contracted_mime_types() -> frozenset[str]:
    """Was der M2-Vertrag erlaubt."""
    return frozenset(RULES)
