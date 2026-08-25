"""Signierte, opake Keyset-Cursor.

Ein Cursor benennt eine Position in einer sortierten, bereits autorisierten
Menge. Er ist kein Geheimnis, aber er ist auch kein Clientfeld: wer ihn frei
waehlen koennte, koennte eine Abfrage an einer Filterbedingung vorbei
fortsetzen. Deshalb traegt jeder Cursor eine HMAC-Signatur ueber seinen
gesamten Inhalt und den Kontext, in dem er ausgestellt wurde.

Die Bindung ist der eigentliche Punkt. Ein Cursor aus einem anderen Space
oder mit anderen Filtern ist kein gueltiger Fortsetzungspunkt, auch wenn
seine Signatur stimmt - er beschriebe eine Position in einer anderen Menge.
Deshalb wandert der Kontext in die signierten Daten und wird beim Einloesen
gegen den aktuellen Request geprueft, statt nur mitgeliefert zu werden.

Die Domaene legt fest, was ihre Position ausmacht (`position`) und woran der
Cursor gebunden ist (`binding`); dieser Modul kennt weder Sortierschluessel
noch Filter. So teilen sich Memories, HeartMoments und spaeter Story
dieselbe Signatur- und Bindungsmechanik, ohne dass eine Collection ihre
eigene Variante schreibt - die Stelle, an der sich sonst genau eine
Bindungspruefung schleichend unterscheidet.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from typing import Any

from sidebyside.config import get_settings
from sidebyside.core.errors import BadRequestError, ErrorCode

CURSOR_VERSION = 1
"""Wird mitsigniert. Ein Cursor aus einer aelteren Version ist ungueltig,
nicht 'so gut wie moeglich' interpretierbar."""


def _signing_key() -> bytes:
    return get_settings().cursor_signing_secret


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    """Base64url ohne Padding - und nur in der kanonischen Schreibweise.

    Ein Token endet auf angebrochenen Bits, die der Decoder verwirft. Ohne
    diese Pruefung haetten dieselben Bytes mehrere gueltige Schreibweisen:
    fuer eine 32-Byte-Signatur decodieren vier verschiedene Schlusszeichen
    identisch. Ein veraendertes Token waere dann nicht zwangslaeufig ein
    anderes Token - genau die Eigenschaft, die eine Signatur zusichern soll.
    """
    padding = "=" * (-len(value) % 4)
    raw = base64.urlsafe_b64decode(value + padding)
    if base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii") != value:
        raise ValueError("non-canonical base64")
    return raw


def invalid_cursor() -> BadRequestError:
    """Eine Antwort fuer alle Fehlerarten.

    Manipulation, fremder Space, geaenderter Filter und kaputtes Base64
    enden gleich. Ein Unterschied waere die Auskunft, welche der vier
    Annahmen zutraf.
    """
    return BadRequestError("The cursor is invalid for this request.", ErrorCode.INVALID_CURSOR)


def encode(*, binding: dict[str, Any], position: dict[str, Any]) -> str:
    """Position und Bindung zu einem opaken Token signieren."""
    payload = {"v": CURSOR_VERSION, "b": binding, "p": position}
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    signature = hmac.new(_signing_key(), raw, hashlib.sha256).digest()
    return f"{_b64encode(raw)}.{_b64encode(signature)}"


def decode(token: str, *, binding: dict[str, Any]) -> dict[str, Any]:
    """Token pruefen und die Position zurueckgeben.

    Die Signatur wird vor dem Parsen des Inhalts geprueft, damit kein
    manipulierter Payload den Parser erreicht. Danach muss die eingebettete
    Bindung exakt der erwarteten entsprechen.
    """
    try:
        raw_part, signature_part = token.split(".", 1)
        raw = _b64decode(raw_part)
        supplied = _b64decode(signature_part)
    except (ValueError, TypeError) as error:
        raise invalid_cursor() from error

    expected = hmac.new(_signing_key(), raw, hashlib.sha256).digest()
    if not hmac.compare_digest(supplied, expected):
        raise invalid_cursor()

    try:
        payload: dict[str, Any] = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as error:
        raise invalid_cursor() from error

    if payload.get("v") != CURSOR_VERSION or payload.get("b") != binding:
        raise invalid_cursor()

    position = payload.get("p")
    if not isinstance(position, dict):
        raise invalid_cursor()
    return position
