"""HTTP contract for editable Account identity and profile avatars (#368)."""

from __future__ import annotations

import io

import pytest
from sqlalchemy.orm import Session

from sidebyside.attachments import service as attachment_service
from sidebyside.attachments.models import (
    Attachment,
    AttachmentPayload,
    AttachmentStatus,
    MediaType,
)
from sidebyside.authorization import PrivacyClass
from sidebyside.core.clock import now
from sidebyside.media import get_media_store
from sidebyside.relationship import service as relationship_service
from tests.conftest import auth, make_account, make_space, requires_database, sign_in

pytestmark = [pytest.mark.integration, requires_database]


@pytest.fixture
def identity_couple(session: Session):  # type: ignore[no-untyped-def]
    anna = make_account(session, "Anna")
    ben = make_account(session, "Ben")
    outsider = make_account(session, "Fremd")
    space = make_space(session, anna)
    relationship_service.add_member(session, space.id, ben)
    outsider_space = make_space(session, outsider)
    session.flush()
    return {
        "anna": anna,
        "ben": ben,
        "outsider": outsider,
        "space": space,
        "outsider_space": outsider_space,
        "token_a": sign_in(session, anna),
        "token_b": sign_in(session, ben),
        "token_outsider": sign_in(session, outsider),
    }


def profile_path(space_id: object, account_id: object) -> str:
    return f"/api/v1/spaces/{space_id}/profiles/{account_id}"


def ready_avatar(session: Session, *, account_id, space_id) -> Attachment:  # type: ignore[no-untyped-def]
    attachment = Attachment(
        space_id=space_id,
        owner_id=account_id,
        privacy_class=PrivacyClass.OWNER_ONLY.value,
        status=AttachmentStatus.READY.value,
        media_type=MediaType.IMAGE.value,
        declared_mime_type="image/jpeg",
        declared_size=12,
        mime_type="image/jpeg",
        size=12,
        ready_at=now(),
        payload=AttachmentPayload(original_name="avatar.jpg"),
    )
    session.add(attachment)
    session.flush()
    get_media_store().put(
        attachment_service.storage_key_for(attachment),
        io.BytesIO(b"avatar-bytes"),
        "image/jpeg",
    )
    return attachment


def test_profile_defaults_to_no_avatar(client, identity_couple) -> None:  # type: ignore[no-untyped-def]
    response = client.get(
        profile_path(identity_couple["space"].id, identity_couple["anna"].id),
        headers=auth(identity_couple["token_b"]),
    )

    assert response.status_code == 200
    assert response.json()["profileAttachmentId"] is None


def test_self_updates_display_name_and_partner_sees_current_identity(
    client,
    identity_couple,
) -> None:  # type: ignore[no-untyped-def]
    response = client.put(
        f"{profile_path(identity_couple['space'].id, identity_couple['anna'].id)}/identity",
        json={"displayName": "  Änne 李  "},
        headers=auth(identity_couple["token_a"]),
    )
    assert response.status_code == 200
    assert response.json()["displayName"] == "Änne 李"

    partner_view = client.get(
        profile_path(identity_couple["space"].id, identity_couple["anna"].id),
        headers=auth(identity_couple["token_b"]),
    )
    assert partner_view.status_code == 200
    assert partner_view.json()["displayName"] == "Änne 李"


def test_partner_cannot_change_foreign_identity(client, identity_couple) -> None:  # type: ignore[no-untyped-def]
    response = client.put(
        f"{profile_path(identity_couple['space'].id, identity_couple['anna'].id)}/identity",
        json={"displayName": "Nicht erlaubt"},
        headers=auth(identity_couple["token_b"]),
    )

    assert response.status_code == 403
    assert response.json()["code"] == "PROFILE_SELF_WRITE_ONLY"


def test_profile_avatar_is_shared_with_active_partner_and_streamed_by_profile(
    client,
    session: Session,
    identity_couple,
) -> None:  # type: ignore[no-untyped-def]
    avatar = ready_avatar(
        session,
        account_id=identity_couple["anna"].id,
        space_id=identity_couple["space"].id,
    )

    updated = client.put(
        f"{profile_path(identity_couple['space'].id, identity_couple['anna'].id)}/avatar",
        json={"profileAttachmentId": str(avatar.id)},
        headers=auth(identity_couple["token_a"]),
    )
    assert updated.status_code == 200
    assert updated.json()["profileAttachmentId"] == str(avatar.id)

    partner_view = client.get(
        profile_path(identity_couple["space"].id, identity_couple["anna"].id),
        headers=auth(identity_couple["token_b"]),
    )
    assert partner_view.status_code == 200
    assert partner_view.json()["profileAttachmentId"] == str(avatar.id)

    content = client.get(
        f"{profile_path(identity_couple['space'].id, identity_couple['anna'].id)}/avatar/content",
        headers=auth(identity_couple["token_b"]),
    )
    assert content.status_code == 200
    assert content.content == b"avatar-bytes"
    assert content.headers["cache-control"] == "private, no-store"
    assert content.headers["content-type"].startswith("image/jpeg")


def test_partner_cannot_replace_foreign_avatar(
    client,
    session: Session,
    identity_couple,
) -> None:  # type: ignore[no-untyped-def]
    avatar = ready_avatar(
        session,
        account_id=identity_couple["ben"].id,
        space_id=identity_couple["space"].id,
    )
    response = client.put(
        f"{profile_path(identity_couple['space'].id, identity_couple['anna'].id)}/avatar",
        json={"profileAttachmentId": str(avatar.id)},
        headers=auth(identity_couple["token_b"]),
    )

    assert response.status_code == 403
    assert response.json()["code"] == "PROFILE_SELF_WRITE_ONLY"


def test_cross_tenant_avatar_stream_is_not_discoverable(
    client,
    session: Session,
    identity_couple,
) -> None:  # type: ignore[no-untyped-def]
    avatar = ready_avatar(
        session,
        account_id=identity_couple["anna"].id,
        space_id=identity_couple["space"].id,
    )
    bound = client.put(
        f"{profile_path(identity_couple['space'].id, identity_couple['anna'].id)}/avatar",
        json={"profileAttachmentId": str(avatar.id)},
        headers=auth(identity_couple["token_a"]),
    )
    assert bound.status_code == 200

    response = client.get(
        f"{profile_path(identity_couple['outsider_space'].id, identity_couple['anna'].id)}/avatar/content",
        headers=auth(identity_couple["token_outsider"]),
    )
    assert response.status_code == 404
    assert response.json()["code"] == "PARTNER_PROFILE_NOT_FOUND"
