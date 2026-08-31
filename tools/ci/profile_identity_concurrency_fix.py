from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one replacement anchor, found {count}")
    file.write_text(text.replace(old, new), encoding="utf-8")


# Account is the aggregate that owns presentation identity across Spaces.
replace_once(
    "backend/src/sidebyside/identity/models.py",
    "from sidebyside.db.mixins import IdMixin, TimestampMixin\n",
    "from sidebyside.db.mixins import IdMixin, TimestampMixin, VersionMixin\n",
)
replace_once(
    "backend/src/sidebyside/identity/models.py",
    "class Account(IdMixin, TimestampMixin, Base):\n",
    "class Account(IdMixin, TimestampMixin, VersionMixin, Base):\n",
)

service_path = Path("backend/src/sidebyside/profiles/service.py")
service = service_path.read_text(encoding="utf-8")
service = service.replace(
    "from sidebyside.core.errors import ConflictError, ErrorCode, ForbiddenError, ValidationError\n",
    "from sidebyside.core.clock import now\n"
    "from sidebyside.core.errors import ConflictError, ErrorCode, ForbiddenError, ValidationError\n",
    1,
)
service = service.replace(
    "from sidebyside.identity.models import Account\n",
    "from sidebyside.identity import service as identity_service\n"
    "from sidebyside.identity.models import Account\n",
    1,
)
start = service.index("def set_profile_attachment(\n")
end = service.index("\n\ndef profile_preferences(\n", start)
replacement = '''def _set_profile_attachment_for_account(
    session: Session,
    context: AuthorizationContext,
    account: Account,
    attachment_id: UUID | None,
) -> tuple[Attachment | None, bool]:
    """Apply an avatar binding for an already locked Account.

    The boolean reports whether presentation identity actually changed.
    Keeping the Account clean during the attachment flushes lets the
    caller advance the Account-global version exactly once afterwards.
    """
    current = session.execute(
        select(attachment_binding.AccountProfileAttachment).where(
            attachment_binding.AccountProfileAttachment.account_id == account.id
        )
    ).scalar_one_or_none()

    if attachment_id is None:
        if current is None:
            return None, False
        previous = session.get(Attachment, current.attachment_id)
        session.delete(current)
        session.flush()
        if previous is not None:
            attachment_service.mark_for_deletion(session, previous)
            session.flush()
        return None, True

    candidates = attachment_binding.lock_for_binding(session, [attachment_id])
    candidate = attachment_binding.ensure_bindable(
        candidates.get(attachment_id),
        space_id=context.space_id,
        account_id=account.id,
    )
    if candidate.media_type != MediaType.IMAGE.value:
        raise ValidationError(
            "A profile avatar must be an image.",
            ProfileErrorCode.AVATAR_IMAGE_REQUIRED,
        )

    if current is not None and current.attachment_id == candidate.id:
        return candidate, False

    attachment_binding.ensure_unlinked(
        session,
        candidate.id,
        allow=("ACCOUNT_PROFILE", account.id),
    )

    previous = session.get(Attachment, current.attachment_id) if current is not None else None
    if current is not None:
        session.delete(current)
        session.flush()

    session.add(
        attachment_binding.AccountProfileAttachment(
            account_id=account.id,
            attachment_id=candidate.id,
        )
    )
    session.flush()

    if previous is not None:
        attachment_service.mark_for_deletion(session, previous)
        session.flush()
    return candidate, True


def set_profile_attachment(
    session: Session,
    context: AuthorizationContext,
    attachment_id: UUID | None,
) -> Attachment | None:
    """Replace or remove the authenticated Account's avatar atomically."""
    account = _locked_self_account(session, context)
    attachment, _changed = _set_profile_attachment_for_account(
        session,
        context,
        account,
        attachment_id,
    )
    return attachment


def update_profile_identity(
    session: Session,
    context: AuthorizationContext,
    account_id: UUID | str,
    *,
    expected_version: int,
    changed_fields: frozenset[str],
    display_name: str | None,
    profile_attachment_id: UUID | None,
) -> Account:
    """Update Account-global presentation identity under one version boundary.

    The Account row is the concurrency authority because display name and
    avatar follow the person across Spaces. Avatar binding may flush its own
    rows while the Account remains clean; the Account is dirtied only after
    those operations, so a combined name+avatar request increments one ETag.
    """
    subject = active_subject(session, context, account_id)
    if subject.id != context.account_id:
        raise ForbiddenError(
            "Only your own self profile can be changed.",
            ProfileErrorCode.SELF_WRITE_ONLY,
        )

    account = _locked_self_account(session, context)
    if account.version != expected_version:
        raise ConflictError(
            "The profile identity was changed by another request.",
            ErrorCode.VERSION_CONFLICT,
        )

    avatar_changed = False
    if "profile_attachment_id" in changed_fields:
        _attachment, avatar_changed = _set_profile_attachment_for_account(
            session,
            context,
            account,
            profile_attachment_id,
        )

    if "display_name" in changed_fields:
        account.display_name = identity_service.normalize_display_name(display_name or "")

    # The avatar relation is a separate table. Mark the Account aggregate
    # dirty so an avatar-only mutation advances the same global version.
    if avatar_changed:
        account.updated_at = now()

    try:
        session.flush()
    except StaleDataError as stale:
        raise ConflictError(
            "The profile identity was changed by another request.",
            ErrorCode.VERSION_CONFLICT,
        ) from stale
    return account
'''
service_path.write_text(service[:start] + replacement + service[end:], encoding="utf-8")

api_path = Path("backend/src/sidebyside/api/v1/profiles.py")
api = api_path.read_text(encoding="utf-8")
api = api.replace("from sidebyside.core.errors import ForbiddenError\n", "", 1)
api = api.replace("from sidebyside.identity import service as identity_service\n", "", 1)
api = api.replace(
    '"description": "ProfilePreference version to use for the next If-Match write request.",',
    '"description": "Resource version to use for the next If-Match write request.",',
    1,
)
api = api.replace(
    "    profile_attachment_id: UUID | None\n    created_at: datetime\n",
    "    profile_attachment_id: UUID | None\n    version: int\n    created_at: datetime\n",
    1,
)
view_start = api.index("def _profile_view(\n")
view_end = api.index("\n\n@router.get(\n    \"/spaces/{spaceId}/profiles/{accountId}\"", view_start)
view = '''def _profile_view(
    profile: PartnerProfile,
    *,
    display_name: str,
    profile_attachment_id: UUID | None,
    version: int,
    preferences: list[ProfilePreferenceView],
) -> PartnerProfileView:
    return PartnerProfileView(
        id=profile.id,
        account_id=profile.owner_id,
        display_name=display_name,
        profile_attachment_id=profile_attachment_id,
        version=version,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
        preferences=preferences,
    )
'''
api = api[:view_start] + view + api[view_end:]
routes_start = api.index('@router.get(\n    "/spaces/{spaceId}/profiles/{accountId}",')
routes_end = api.index('\n\n@router.get(\n    "/spaces/{spaceId}/profiles/{accountId}/avatar/content",', routes_start)
routes = '''@router.get(
    "/spaces/{spaceId}/profiles/{accountId}",
    response_model=PartnerProfileView,
    responses={
        200: {"headers": ETAG_HEADERS},
        **problem_responses(401, 404),
    },
)
def get_partner_profile(
    authorization: Authorization,
    session: DbSession,
    response: Response,
    account_id: Annotated[str, Path(alias="accountId")],
) -> PartnerProfileView:
    profile, subject, preferences = service.profile_preferences(session, authorization, account_id)
    attachment = service.profile_attachment(session, subject.id)
    response.headers["ETag"] = etag_for(subject.version)
    return _profile_view(
        profile,
        display_name=subject.display_name,
        profile_attachment_id=attachment.id if attachment is not None else None,
        version=subject.version,
        preferences=[_preference_view(preference) for preference in preferences],
    )


@router.patch(
    "/spaces/{spaceId}/profiles/{accountId}",
    response_model=PartnerProfileView,
    operation_id="updateProfileIdentity",
    responses={
        200: {"headers": ETAG_HEADERS},
        **problem_responses(401, 403, 404, 409, 422),
    },
)
def update_profile_identity(
    authorization: Authorization,
    session: DbSession,
    response: Response,
    body: ProfileIdentityUpdate,
    expected_version: IfMatchVersion,
    account_id: Annotated[str, Path(alias="accountId")],
) -> PartnerProfileView:
    """Change only the authenticated account's current presentation identity."""
    subject = service.update_profile_identity(
        session,
        authorization,
        account_id,
        expected_version=expected_version,
        changed_fields=frozenset(body.model_fields_set),
        display_name=body.display_name,
        profile_attachment_id=body.profile_attachment_id,
    )
    profile, subject, preferences = service.profile_preferences(session, authorization, subject.id)
    attachment = service.profile_attachment(session, subject.id)
    response.headers["ETag"] = etag_for(subject.version)
    return _profile_view(
        profile,
        display_name=subject.display_name,
        profile_attachment_id=attachment.id if attachment is not None else None,
        version=subject.version,
        preferences=[_preference_view(preference) for preference in preferences],
    )
'''
api_path.write_text(api[:routes_start] + routes + api[routes_end:], encoding="utf-8")

migration = Path("backend/alembic/versions/0035_profile_identity_version.py")
migration.write_text(
    '''"""Account-global profile identity version.

Revision ID: 0035
Revises: 0034
Create Date: 2026-08-31
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0035"
down_revision = "0034"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "accounts",
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
    )
    op.alter_column("accounts", "version", server_default=None)


def downgrade() -> None:
    op.drop_column("accounts", "version")
''',
    encoding="utf-8",
)

matrix_path = Path("backend/tests/integration/test_endpoint_matrix.py")
matrix = matrix_path.read_text(encoding="utf-8")
old = '''    Endpoint(
        "PATCH",
        "/api/v1/spaces/{spaceId}/profiles/{accountId}",
        body={"displayName": "Matrix Name"},
        resource_absence="PARTNER_PROFILE_NOT_FOUND",
    ),
'''
new = '''    Endpoint(
        "PATCH",
        "/api/v1/spaces/{spaceId}/profiles/{accountId}",
        body={"displayName": "Matrix Name"},
        if_match=True,
        resource_absence="PARTNER_PROFILE_NOT_FOUND",
    ),
'''
if matrix.count(old) != 1:
    raise SystemExit("endpoint matrix profile PATCH anchor changed")
matrix_path.write_text(matrix.replace(old, new), encoding="utf-8")

test_path = Path("backend/tests/integration/test_profile_identity_api.py")
tests = test_path.read_text(encoding="utf-8")
first_start = tests.index("def test_profile_projection_and_display_name_update(")
first_end = tests.index("\n\ndef test_avatar_set_remove_and_attachment_owner_boundary", first_start)
first = '''def test_profile_projection_and_display_name_update(client, couple) -> None:  # type: ignore[no-untyped-def]
    initial = client.get(
        profile_path(couple["space"].id, couple["anna"].id),
        headers=auth(couple["token_b"]),
    )
    assert initial.status_code == 200
    assert initial.json()["profileAttachmentId"] is None
    assert initial.json()["version"] == 1
    assert initial.headers["etag"] == '"1"'

    updated = client.patch(
        profile_path(couple["space"].id, couple["anna"].id),
        json={"displayName": "  Änne 李  "},
        headers={**auth(couple["token_a"]), "If-Match": initial.headers["etag"]},
    )
    assert updated.status_code == 200
    assert updated.json()["displayName"] == "Änne 李"
    assert updated.json()["profileAttachmentId"] is None
    assert updated.json()["version"] == 2
    assert updated.headers["etag"] == '"2"'

    partner_view = client.get(
        profile_path(couple["space"].id, couple["anna"].id),
        headers=auth(couple["token_b"]),
    )
    assert partner_view.status_code == 200
    assert partner_view.json()["displayName"] == "Änne 李"
    assert partner_view.json()["version"] == 2
    assert partner_view.headers["etag"] == '"2"'

    stale = client.patch(
        profile_path(couple["space"].id, couple["anna"].id),
        json={"displayName": "Veraltet"},
        headers={**auth(couple["token_a"]), "If-Match": initial.headers["etag"]},
    )
    assert stale.status_code == 409
    assert stale.json()["code"] == "VERSION_CONFLICT"

    foreign_write = client.patch(
        profile_path(couple["space"].id, couple["anna"].id),
        json={"displayName": "Nicht erlaubt"},
        headers={**auth(couple["token_b"]), "If-Match": partner_view.headers["etag"]},
    )
    assert foreign_write.status_code == 403
    assert foreign_write.json()["code"] == "PROFILE_SELF_WRITE_ONLY"

    invalid = client.patch(
        profile_path(couple["space"].id, couple["anna"].id),
        json={"displayName": None},
        headers={**auth(couple["token_a"]), "If-Match": partner_view.headers["etag"]},
    )
    assert invalid.status_code == 422
    assert invalid.json()["code"] == "DISPLAY_NAME_REQUIRED"
'''
tests = tests[:first_start] + first + tests[first_end:]

second_start = tests.index("def test_avatar_set_remove_and_attachment_owner_boundary(")
second_end = tests.index("\n\ndef test_avatar_content_is_profile_authorized_and_account_global", second_start)
second = '''def test_avatar_set_remove_and_attachment_owner_boundary(
    client,
    couple,
    session: Session,
) -> None:  # type: ignore[no-untyped-def]
    initial = client.get(
        profile_path(couple["space"].id, couple["anna"].id),
        headers=auth(couple["token_a"]),
    )
    assert initial.status_code == 200
    assert initial.headers["etag"] == '"1"'

    avatar = ready_avatar(
        session,
        account_id=couple["anna"].id,
        space_id=couple["space"].id,
    )
    set_response = client.patch(
        profile_path(couple["space"].id, couple["anna"].id),
        json={"profileAttachmentId": str(avatar.id)},
        headers={**auth(couple["token_a"]), "If-Match": initial.headers["etag"]},
    )
    assert set_response.status_code == 200
    assert set_response.json()["profileAttachmentId"] == str(avatar.id)
    assert set_response.json()["version"] == 2
    assert set_response.headers["etag"] == '"2"'

    partner_view = client.get(
        profile_path(couple["space"].id, couple["anna"].id),
        headers=auth(couple["token_b"]),
    )
    assert partner_view.status_code == 200
    assert partner_view.json()["profileAttachmentId"] == str(avatar.id)
    assert partner_view.json()["version"] == 2

    foreign_avatar = ready_avatar(
        session,
        account_id=couple["ben"].id,
        space_id=couple["space"].id,
    )
    foreign_candidate = client.patch(
        profile_path(couple["space"].id, couple["anna"].id),
        json={"profileAttachmentId": str(foreign_avatar.id)},
        headers={**auth(couple["token_a"]), "If-Match": partner_view.headers["etag"]},
    )
    assert foreign_candidate.status_code == 404

    removed = client.patch(
        profile_path(couple["space"].id, couple["anna"].id),
        json={"profileAttachmentId": None},
        headers={**auth(couple["token_a"]), "If-Match": partner_view.headers["etag"]},
    )
    assert removed.status_code == 200
    assert removed.json()["profileAttachmentId"] is None
    assert removed.json()["version"] == 3
    assert removed.headers["etag"] == '"3"'
    assert avatar.status == AttachmentStatus.DELETING.value
'''
test_path.write_text(tests[:second_start] + second + tests[second_end:], encoding="utf-8")

docs_path = Path("docs/PROFILES.md")
docs = docs_path.read_text(encoding="utf-8")
docs = docs.replace(
    "`PATCH /api/v1/spaces/{spaceId}/profiles/{accountId}` is self-write only. Omitted identity fields remain unchanged. `displayName` is normalized and validated only by the authoritative identity-domain rule; changing it does not change authentication identity or sessions. An explicit `profileAttachmentId: null` removes the avatar, while a non-null ID must pass the existing READY/owner/current-Space/image validation.\n",
    "`PATCH /api/v1/spaces/{spaceId}/profiles/{accountId}` is self-write only and requires the last-read Account presentation `ETag` in `If-Match`. Omitted identity fields remain unchanged. `displayName` is normalized and validated only by the authoritative identity-domain rule; changing it does not change authentication identity or sessions. An explicit `profileAttachmentId: null` removes the avatar, while a non-null ID must pass the existing READY/owner/current-Space/image validation. Display name and avatar share one Account-global `version`, because both follow the Account across Spaces; avatar-only changes advance that version too. A stale write returns `409 VERSION_CONFLICT` rather than silently overwriting a newer edit.\n",
    1,
)
docs = docs.replace(
    "ProfilePreference changes and deletes use ETag/`If-Match`. Stale versions return `409 VERSION_CONFLICT` instead of a silent Lost Update.\n",
    "Profile identity changes as well as ProfilePreference changes/deletes use ETag/`If-Match`. Stale versions return `409 VERSION_CONFLICT` instead of a silent Lost Update. The identity ETag is Account-global; preference ETags remain resource-local.\n",
    1,
)
docs_path.write_text(docs, encoding="utf-8")
