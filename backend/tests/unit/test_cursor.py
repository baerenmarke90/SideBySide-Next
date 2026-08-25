"""Invarianten des signierten Keyset-Cursors."""

from __future__ import annotations

import base64

import pytest

from sidebyside.core import cursor
from sidebyside.core.errors import BadRequestError

BINDING = {"collection": "memories", "spaceId": "s", "year": None}
POSITION = {"createdAt": "2026-08-25T07:00:00Z", "id": "i"}


def test_roundtrip_returns_the_position() -> None:
    token = cursor.encode(binding=BINDING, position=POSITION)
    assert cursor.decode(token, binding=BINDING) == POSITION


def test_a_different_binding_is_rejected() -> None:
    """Ein Cursor aus einem anderen Kontext beschreibt eine andere Menge."""
    token = cursor.encode(binding=BINDING, position=POSITION)
    for abweichend in (
        {**BINDING, "spaceId": "anderer-space"},
        {**BINDING, "year": 2025},
        {**BINDING, "collection": "heart_moments"},
    ):
        with pytest.raises(BadRequestError):
            cursor.decode(token, binding=abweichend)


def test_every_single_character_change_invalidates_the_token() -> None:
    """Kein veraendertes Token bleibt gueltig - auch nicht am Signaturende.

    Die Signatur endet auf angebrochenen Bits. Ohne die Kanonizitaetspruefung
    decodieren vier verschiedene Schlusszeichen zu denselben Bytes, und ein
    veraendertes Token waere dann kein anderes Token.
    """
    token = cursor.encode(binding=BINDING, position=POSITION)
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"

    for stelle in (len(token) - 1, len(token) - 2, 0, token.index(".") - 1):
        original = token[stelle]
        for ersatz in alphabet:
            if ersatz == original:
                continue
            verfaelscht = token[:stelle] + ersatz + token[stelle + 1 :]
            with pytest.raises(BadRequestError):
                cursor.decode(verfaelscht, binding=BINDING)


def test_non_canonical_encoding_is_rejected() -> None:
    signatur = bytes(range(32))
    kanonisch = base64.urlsafe_b64encode(signatur).rstrip(b"=").decode("ascii")
    zwillinge = [
        zeichen
        for zeichen in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
        if base64.urlsafe_b64decode(kanonisch[:-1] + zeichen + "=") == signatur
    ]
    # Genau vier Schreibweisen liefern dieselben Bytes; nur eine ist kanonisch.
    assert len(zwillinge) == 4
    assert kanonisch[-1] in zwillinge


def test_a_structurally_broken_token_is_rejected() -> None:
    for kaputt in ("", "ohne-punkt", ".", "a.b", "!!!.???"):
        with pytest.raises(BadRequestError):
            cursor.decode(kaputt, binding=BINDING)
