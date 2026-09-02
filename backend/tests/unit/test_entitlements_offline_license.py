"""Unit tests for Self-Hosted Ed25519 offline license verification."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from cryptography.hazmat.primitives.asymmetric import ed25519

from sidebyside.entitlements.offline_license import (
    LicenseValidationError,
    sign_offline_license,
    verify_offline_license,
)


@pytest.fixture
def keypair() -> tuple[ed25519.Ed25519PrivateKey, ed25519.Ed25519PublicKey]:
    priv = ed25519.Ed25519PrivateKey.generate()
    return priv, priv.public_key()


def test_valid_offline_license_verification(
    keypair: tuple[ed25519.Ed25519PrivateKey, ed25519.Ed25519PublicKey],
) -> None:
    priv, pub = keypair
    now = datetime(2026, 9, 1, 12, 0, 0, tzinfo=UTC)

    payload = {
        "licensee": "Acme Family",
        "tier": "PREMIUM",
        "capabilities": ["storage.cloud_quota_50gb", "recap.pdf_yearbook"],
        "issued_at": (now - timedelta(days=1)).isoformat(),
        "expires_at": (now + timedelta(days=365)).isoformat(),
        "instance_id": "inst-12345",
    }

    token = sign_offline_license(payload, priv)
    verified = verify_offline_license(token, pub, at=now)

    assert verified.licensee == "Acme Family"
    assert verified.tier == "PREMIUM"
    assert verified.capabilities == ["storage.cloud_quota_50gb", "recap.pdf_yearbook"]
    assert verified.instance_id == "inst-12345"
    assert verified.expires_at == now + timedelta(days=365)


def test_expired_offline_license_rejected(
    keypair: tuple[ed25519.Ed25519PrivateKey, ed25519.Ed25519PublicKey],
) -> None:
    priv, pub = keypair
    now = datetime(2026, 9, 1, 12, 0, 0, tzinfo=UTC)

    payload = {
        "licensee": "Expired Licensee",
        "tier": "PREMIUM",
        "capabilities": [],
        "issued_at": (now - timedelta(days=400)).isoformat(),
        "expires_at": (now - timedelta(days=35)).isoformat(),
    }

    token = sign_offline_license(payload, priv)
    with pytest.raises(LicenseValidationError, match="License token has expired"):
        verify_offline_license(token, pub, at=now)


def test_tampered_signature_rejected(
    keypair: tuple[ed25519.Ed25519PrivateKey, ed25519.Ed25519PublicKey],
) -> None:
    _, pub = keypair
    other_priv = ed25519.Ed25519PrivateKey.generate()
    now = datetime(2026, 9, 1, 12, 0, 0, tzinfo=UTC)

    payload = {
        "licensee": "Tampered",
        "tier": "PREMIUM",
        "capabilities": [],
        "issued_at": now.isoformat(),
        "expires_at": (now + timedelta(days=30)).isoformat(),
    }

    # Signed with a different private key than the public key being used
    token = sign_offline_license(payload, other_priv)
    with pytest.raises(LicenseValidationError, match="Invalid license signature"):
        verify_offline_license(token, pub, at=now)


def test_malformed_token_rejected(
    keypair: tuple[ed25519.Ed25519PrivateKey, ed25519.Ed25519PublicKey],
) -> None:
    _, pub = keypair
    with pytest.raises(LicenseValidationError, match="Malformed license token"):
        verify_offline_license("not-a-valid-token", pub)

    with pytest.raises(LicenseValidationError, match="Invalid base64 encoding"):
        verify_offline_license("invalid!part1.invalid!part2", pub)
