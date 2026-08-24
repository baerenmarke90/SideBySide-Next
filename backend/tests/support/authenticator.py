"""Ein virtueller Authenticator fuer die WebAuthn-Tests.

Er baut `attestationObject`, `clientDataJSON` und Assertions selbst und
signiert mit einem echten P-256-Schluessel. Damit prueft die Suite die
Signatur-, Flag- und Zaehlerpruefung tatsaechlich - aufgezeichnete
Beispieldaten koennten das nicht, weil sie an eine feste Challenge und
eine feste Herkunft gebunden waeren.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import struct
from dataclasses import dataclass, field
from typing import Any

import cbor2
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec

FLAG_USER_PRESENT = 0x01
FLAG_USER_VERIFIED = 0x04
FLAG_BACKUP_ELIGIBLE = 0x08
FLAG_BACKUP_STATE = 0x10
FLAG_ATTESTED_DATA = 0x40


def b64url(rohdaten: bytes) -> str:
    return base64.urlsafe_b64encode(rohdaten).decode("ascii").rstrip("=")


def from_b64url(wert: str) -> bytes:
    return base64.urlsafe_b64decode(wert + "=" * (-len(wert) % 4))


@dataclass
class VirtualAuthenticator:
    """Ein Geraet mit genau einem Schluesselpaar."""

    rp_id: str = "localhost"
    origin: str = "http://localhost:8000"
    aaguid: bytes = b"\x00" * 16
    sign_count: int = 0
    schluessel: ec.EllipticCurvePrivateKey = field(
        default_factory=lambda: ec.generate_private_key(ec.SECP256R1())
    )
    credential_id: bytes = field(default_factory=lambda: os.urandom(32))
    backup_eligible: bool = False
    backup_state: bool = False

    def _cose_key(self) -> bytes:
        zahlen = self.schluessel.public_key().public_numbers()
        return cbor2.dumps(
            {
                1: 2,  # kty: EC2
                3: -7,  # alg: ES256
                -1: 1,  # crv: P-256
                -2: zahlen.x.to_bytes(32, "big"),
                -3: zahlen.y.to_bytes(32, "big"),
            }
        )

    def _flags(self, *, attested: bool, user_verified: bool) -> int:
        flags = FLAG_USER_PRESENT
        if user_verified:
            flags |= FLAG_USER_VERIFIED
        if self.backup_eligible:
            flags |= FLAG_BACKUP_ELIGIBLE
        if self.backup_state:
            flags |= FLAG_BACKUP_STATE
        if attested:
            flags |= FLAG_ATTESTED_DATA
        return flags

    def _auth_data(self, *, attested: bool, rp_id: str | None = None) -> bytes:
        rp_hash = hashlib.sha256((rp_id or self.rp_id).encode("utf-8")).digest()
        daten = rp_hash + bytes([self._flags(attested=attested, user_verified=True)])
        daten += struct.pack(">I", self.sign_count)
        if attested:
            schluessel = self._cose_key()
            daten += (
                self.aaguid
                + struct.pack(">H", len(self.credential_id))
                + self.credential_id
                + schluessel
            )
        return daten

    def _client_data(self, *, typ: str, challenge: str, origin: str | None = None) -> bytes:
        return json.dumps(
            {
                "type": typ,
                "challenge": challenge,
                "origin": origin or self.origin,
                "crossOrigin": False,
            },
            separators=(",", ":"),
        ).encode("utf-8")

    def register(
        self, optionen: dict[str, Any], *, origin: str | None = None, rp_id: str | None = None
    ) -> dict[str, Any]:
        client_data = self._client_data(
            typ="webauthn.create",
            challenge=optionen["challenge"],
            origin=origin,
        )
        auth_data = self._auth_data(attested=True, rp_id=rp_id)
        attestation = cbor2.dumps({"fmt": "none", "attStmt": {}, "authData": auth_data})
        return {
            "id": b64url(self.credential_id),
            "rawId": b64url(self.credential_id),
            "type": "public-key",
            "response": {
                "clientDataJSON": b64url(client_data),
                "attestationObject": b64url(attestation),
            },
            "clientExtensionResults": {},
            "transports": ["internal"],
        }

    def authenticate(
        self,
        optionen: dict[str, Any],
        *,
        origin: str | None = None,
        rp_id: str | None = None,
        zaehler_erhoehen: bool = True,
        signieren_mit: ec.EllipticCurvePrivateKey | None = None,
    ) -> dict[str, Any]:
        if zaehler_erhoehen:
            self.sign_count += 1
        client_data = self._client_data(
            typ="webauthn.get", challenge=optionen["challenge"], origin=origin
        )
        auth_data = self._auth_data(attested=False, rp_id=rp_id)
        signatur = (signieren_mit or self.schluessel).sign(
            auth_data + hashlib.sha256(client_data).digest(),
            ec.ECDSA(hashes.SHA256()),
        )
        return {
            "id": b64url(self.credential_id),
            "rawId": b64url(self.credential_id),
            "type": "public-key",
            "response": {
                "clientDataJSON": b64url(client_data),
                "authenticatorData": b64url(auth_data),
                "signature": b64url(signatur),
                "userHandle": None,
            },
            "clientExtensionResults": {},
        }
