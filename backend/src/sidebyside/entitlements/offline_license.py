"""Self-Hosted Ed25519 offline license token verification."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import ed25519

from sidebyside.core import clock


class LicenseValidationError(Exception):
    """Raised when an offline license token is invalid or expired."""


@dataclass(frozen=True)
class OfflineLicensePayload:
    """Validated contents of an offline license token."""

    licensee: str
    tier: str
    capabilities: list[str]
    issued_at: datetime
    expires_at: datetime | None
    instance_id: str | None = None


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * ((4 - len(data) % 4) % 4)
    return base64.b64decode((data + padding).encode("ascii"), altchars=b"-_", validate=True)


def sign_offline_license(
    payload: dict[str, Any],
    private_key: ed25519.Ed25519PrivateKey,
) -> str:
    """Create a signed offline license token from a dictionary payload."""
    payload_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    signature = private_key.sign(payload_bytes)
    return f"{_b64url_encode(payload_bytes)}.{_b64url_encode(signature)}"


def verify_offline_license(
    license_token: str,
    public_key: ed25519.Ed25519PublicKey,
    *,
    at: datetime | None = None,
) -> OfflineLicensePayload:
    """Verify an Ed25519-signed offline license token without outbound requests."""
    current_time = clock.ensure_utc(at) if at is not None else clock.now()

    parts = license_token.strip().split(".")
    if len(parts) != 2:
        raise LicenseValidationError("Malformed license token format.")

    try:
        payload_bytes = _b64url_decode(parts[0])
        signature = _b64url_decode(parts[1])
    except Exception as error:
        raise LicenseValidationError("Invalid base64 encoding in license token.") from error

    try:
        public_key.verify(signature, payload_bytes)
    except InvalidSignature as error:
        raise LicenseValidationError("Invalid license signature.") from error

    try:
        raw_payload = json.loads(payload_bytes.decode("utf-8"))
    except Exception as error:
        raise LicenseValidationError("Invalid JSON in license payload.") from error

    licensee = raw_payload.get("licensee")
    if not isinstance(licensee, str) or not licensee:
        raise LicenseValidationError("Missing or invalid licensee in license payload.")

    tier = raw_payload.get("tier", "PREMIUM")
    if not isinstance(tier, str):
        raise LicenseValidationError("Invalid tier in license payload.")

    raw_capabilities = raw_payload.get("capabilities", [])
    if not isinstance(raw_capabilities, list) or not all(
        isinstance(c, str) for c in raw_capabilities
    ):
        raise LicenseValidationError("Invalid capabilities in license payload.")

    raw_issued_at = raw_payload.get("issued_at")
    if not isinstance(raw_issued_at, str):
        raise LicenseValidationError("Missing issued_at timestamp in license payload.")
    try:
        issued_at = clock.ensure_utc(datetime.fromisoformat(raw_issued_at))
    except Exception as error:
        raise LicenseValidationError("Invalid issued_at timestamp format.") from error

    expires_at: datetime | None = None
    raw_expires_at = raw_payload.get("expires_at")
    if raw_expires_at is not None:
        if not isinstance(raw_expires_at, str):
            raise LicenseValidationError("Invalid expires_at timestamp format.")
        try:
            expires_at = clock.ensure_utc(datetime.fromisoformat(raw_expires_at))
        except Exception as error:
            raise LicenseValidationError("Invalid expires_at timestamp format.") from error

    if expires_at is not None and current_time > expires_at:
        raise LicenseValidationError("License token has expired.")

    if current_time < issued_at:
        raise LicenseValidationError("License token is not yet valid (issued in future).")

    return OfflineLicensePayload(
        licensee=licensee,
        tier=tier,
        capabilities=raw_capabilities,
        issued_at=issued_at,
        expires_at=expires_at,
        instance_id=raw_payload.get("instance_id"),
    )
