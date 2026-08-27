"""Unit invariants for the M2 HeartMoment model."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sqlalchemy import CheckConstraint

from sidebyside.api.v1.heart_moments import (
    HeartMomentCreate,
    HeartMomentUpdate,
    HeartMomentVisibilityChange,
)
from sidebyside.authorization import ContentVisibility, PrivacyClass, privacy_for
from sidebyside.domain.events import PublicEventPayload
from sidebyside.domain.payload import ProtectedPayload
from sidebyside.heart_moments.models import HeartEmotion, HeartMoment, HeartMomentPayload


def test_text_and_emotion_live_only_in_protected_payload() -> None:
    """M2-D06: emotion is content, not metadata."""
    assert issubclass(HeartMomentPayload, ProtectedPayload)
    assert {"text", "emotion"} <= set(HeartMomentPayload.model_fields)
    assert "text" not in HeartMoment.__table__.c
    assert "emotion" not in HeartMoment.__table__.c
    assert "payload" in HeartMoment.__table__.c


def test_database_allows_only_enforceable_privacy_classes() -> None:
    checks = {
        str(constraint.sqltext)
        for constraint in HeartMoment.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    }
    assert "privacy_class IN ('SPACE_SHARED', 'OWNER_ONLY')" in checks
    assert "crypto_version >= 0" in checks


def test_heart_moment_uses_sqlalchemy_optimistic_versioning() -> None:
    assert HeartMoment.__mapper__.version_id_col is HeartMoment.__table__.c.version
    assert HeartMoment.__mapper__.version_id_generator is not False


def test_visibility_maps_to_privacy_class() -> None:
    assert privacy_for(ContentVisibility.SHARED) is PrivacyClass.SPACE_SHARED
    assert privacy_for(ContentVisibility.PRIVATE) is PrivacyClass.OWNER_ONLY


def test_update_contract_cannot_change_visibility() -> None:
    """The destructive transition therefore has its own operation."""
    assert "visibility" not in HeartMomentUpdate.model_fields
    with pytest.raises(ValidationError):
        HeartMomentUpdate.model_validate({"visibility": "PRIVATE"})


def test_write_contract_rejects_server_owned_fields() -> None:
    for field in ("id", "spaceId", "authorId", "version", "privacyClass", "createdAt"):
        with pytest.raises(ValidationError):
            HeartMomentCreate.model_validate(
                {
                    "text": "Danke fuer heute.",
                    "emotion": "LOVED",
                    "visibility": "SHARED",
                    "happenedOn": "2025-06-13",
                    field: "irgendwas",
                }
            )


def test_create_requires_the_mandatory_domain_fields() -> None:
    for missing in ("text", "emotion", "visibility", "happenedOn"):
        payload = {
            "text": "Danke fuer heute.",
            "emotion": "LOVED",
            "visibility": "SHARED",
            "happenedOn": "2025-06-13",
        }
        del payload[missing]
        with pytest.raises(ValidationError):
            HeartMomentCreate.model_validate(payload)


def test_blank_text_is_rejected() -> None:
    with pytest.raises(ValidationError):
        HeartMomentCreate.model_validate(
            {
                "text": "   ",
                "emotion": "LOVED",
                "visibility": "SHARED",
                "happenedOn": "2025-06-13",
            }
        )


def test_empty_patch_is_rejected() -> None:
    with pytest.raises(ValidationError):
        HeartMomentUpdate.model_validate({})


def test_patch_cannot_null_mandatory_fields() -> None:
    for field in ("text", "emotion", "happenedOn"):
        with pytest.raises(ValidationError):
            HeartMomentUpdate.model_validate({field: None})


def test_visibility_change_accepts_only_the_domain_values() -> None:
    assert HeartMomentVisibilityChange.model_validate({"visibility": "PRIVATE"}).visibility is (
        ContentVisibility.PRIVATE
    )
    with pytest.raises(ValidationError):
        HeartMomentVisibilityChange.model_validate({"visibility": "OWNER_ONLY"})


def test_emotion_catalogue_matches_the_domain_contract() -> None:
    assert {emotion.value for emotion in HeartEmotion} == {
        "LOVED",
        "SEEN",
        "APPRECIATED",
        "SUPPORTED",
        "GRATEFUL",
        "HAPPY",
    }


def test_event_payload_carries_visibility_but_no_content() -> None:
    """The envelope carries a category, not content (M2-D16)."""
    assert "visibility" in PublicEventPayload.model_fields
    assert "emotion" not in PublicEventPayload.model_fields
    assert "text" not in PublicEventPayload.model_fields
    with pytest.raises(ValidationError):
        PublicEventPayload(emotion="LOVED")  # type: ignore[call-arg]
