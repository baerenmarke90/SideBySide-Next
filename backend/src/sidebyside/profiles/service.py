"""Domain logic for PartnerProfile and ProfilePreference.

All read-side lists start at the central privacy guard. OWNER_ONLY rows are
therefore excluded in SQL rather than only after loading.
"""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from sidebyside.attachments import binding as attachment_binding
from sidebyside.attachments import service as attachment_service
from sidebyside.attachments.models import Attachment, MediaType
from sidebyside.authorization import (
    AuthorizationContext,
    PrivacyClass,
    readable,
    require_readable,
    require_writable,
)
from sidebyside.core.errors import ConflictError, ErrorCode, ForbiddenError, ValidationError
from sidebyside.core.ids import parse_id
from sidebyside.identity.models import Account
from sidebyside.profiles.models import (
    PartnerProfile,
    PreferenceCategory,
    PreferenceSentiment,
    ProfilePreference,
    ProfilePreferencePayload,
    ProfileVisibility,
    privacy_for,
)
from sidebyside.relationship.models import Membership, MembershipStatus


class ProfileErrorCode:
    SELF_WRITE_ONLY = "PROFILE_SELF_WRITE_ONLY"
    PARTNER_NOTE_TARGET_REQUIRED = "PROFILE_PARTNER_NOTE_TARGET_REQUIRED"
    TOPIC_REQUIRED = "PROFILE_PREFERENCE_TOPIC_REQUIRED"
    VALUE_REQUIRED = "PROFILE_PREFERENCE_VALUE_REQUIRED"
    AVATAR_IMAGE_REQUIRED = "PROFILE_AVATAR_IMAGE_REQUIRED"


def _subject_id(value: UUID | str) -> UUID | None:
    return value if isinstance(value, UUID) else parse_id(value)


def active_subject(
    session: Session,
    context: AuthorizationContext,
    account_id: UUID | str,
) -> Account:
    """Return a writable person in the current space, or the profile's same 404."""
    identifier = _subject_id(account_id)
    if identifier is None:
        raise PartnerProfile.privacy_absence.error()

    account = session.execute(
        select(Account)
        .join(Membership, Membership.account_id == Account.id)
        .where(
            Account.id == identifier,
            Membership.space_id == context.space_id,
            Membership.status == MembershipStatus.ACTIVE.value,
        )
    ).scalar_one_or_none()
    if account is None:
        raise PartnerProfile.privacy_absence.error()
    return account


def ensure_profile(session: Session, space_id: UUID, owner_id: UUID) -> PartnerProfile:
    """Ensure the SELF_PROFILE for an account proven to belong to this space."""
    profile = session.execute(
        select(PartnerProfile).where(
            PartnerProfile.space_id == space_id,
            PartnerProfile.owner_id == owner_id,
        )
    ).scalar_one_or_none()
    if profile is not None:
        return profile

    profile = PartnerProfile(
        space_id=space_id,
        owner_id=owner_id,
        privacy_class=PrivacyClass.SPACE_SHARED.value,
    )
    session.add(profile)
    session.flush()
    return profile


def profile_for_subject(
    session: Session,
    context: AuthorizationContext,
    account_id: UUID | str,
) -> tuple[PartnerProfile, Account]:
    """Load the visible profile of an active partner."""
    subject = active_subject(session, context, account_id)
    profile = session.execute(
        readable(PartnerProfile, context).where(PartnerProfile.owner_id == subject.id)
    ).scalar_one_or_none()
    if profile is None:
        raise PartnerProfile.privacy_absence.error()
    return profile, subject


def profile_attachment(session: Session, account_id: UUID) -> Attachment | None:
    """Return the stable Attachment currently bound as this Account's avatar."""
    return session.execute(
        select(Attachment)
        .join(
            attachment_binding.AccountProfileAttachment,
            attachment_binding.AccountProfileAttachment.attachment_id == Attachment.id,
        )
        .where(attachment_binding.AccountProfileAttachment.account_id == account_id)
    ).scalar_one_or_none()


def _locked_self_account(session: Session, context: AuthorizationContext) -> Account:
    """Serialize Account-global avatar replacement after tenant authorization."""
    active_subject(session, context, context.account_id)
    return session.execute(
        select(Account).where(Account.id == context.account_id).with_for_update()
    ).scalar_one()


def set_profile_attachment(
    session: Session,
    context: AuthorizationContext,
    attachment_id: UUID | None,
) -> Attachment | None:
    """Replace or remove the authenticated Account's avatar atomically.

    Candidate media must be a READY image uploaded by the same Account in the
    currently authorized Space. The Account row serializes changes across
    multiple active Spaces because the resulting avatar is Account-global.

    Replacement first detaches the old parent relation, then binds the new
    Attachment, and finally marks the obsolete media for the existing cleanup
    job. Provider deletion therefore remains in the normal Attachment lifecycle
    and never becomes a second profile-specific cleanup path.
    """
    account = _locked_self_account(session, context)
    current = session.execute(
        select(attachment_binding.AccountProfileAttachment).where(
            attachment_binding.AccountProfileAttachment.account_id == account.id
        )
    ).scalar_one_or_none()

    if attachment_id is None:
        if current is None:
            return None
        previous = session.get(Attachment, current.attachment_id)
        session.delete(current)
        session.flush()
        if previous is not None:
            attachment_service.mark_for_deletion(session, previous)
            session.flush()
        return None

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
        return candidate

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
    return candidate


def profile_preferences(
    session: Session,
    context: AuthorizationContext,
    account_id: UUID | str,
) -> tuple[PartnerProfile, Account, Sequence[ProfilePreference]]:
    """Return SELF_PROFILE rows only, never private notes about the same person."""
    profile, subject = profile_for_subject(session, context, account_id)
    preferences = (
        session.execute(
            readable(ProfilePreference, context)
            .where(
                ProfilePreference.account_id == subject.id,
                ProfilePreference.visibility == ProfileVisibility.SELF_PROFILE.value,
            )
            .order_by(ProfilePreference.category, ProfilePreference.topic, ProfilePreference.id)
        )
        .scalars()
        .all()
    )
    return profile, subject, preferences


def list_preferences(
    session: Session,
    context: AuthorizationContext,
) -> Sequence[ProfilePreference]:
    """Return all preferences visible to the caller without loading hidden rows."""
    return (
        session.execute(
            readable(ProfilePreference, context).order_by(
                ProfilePreference.updated_at.desc(), ProfilePreference.id
            )
        )
        .scalars()
        .all()
    )


def get_preference(
    session: Session,
    context: AuthorizationContext,
    preference_id: UUID | str,
) -> ProfilePreference:
    return require_readable(session, ProfilePreference, context, preference_id)


def _clean_topic(topic: str) -> str:
    value = topic.strip()
    if not value:
        raise ValidationError(
            "The preference topic must not be empty.",
            ProfileErrorCode.TOPIC_REQUIRED,
        )
    return value


def _clean_value(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValidationError(
            "The preference value must not be empty.",
            ProfileErrorCode.VALUE_REQUIRED,
        )
    return cleaned


def create_preference(
    session: Session,
    context: AuthorizationContext,
    *,
    account_id: UUID,
    visibility: ProfileVisibility,
    category: PreferenceCategory,
    topic: str,
    sentiment: PreferenceSentiment,
    value: str,
) -> ProfilePreference:
    subject = active_subject(session, context, account_id)

    profile_id: UUID | None = None
    if visibility is ProfileVisibility.SELF_PROFILE:
        if subject.id != context.account_id:
            raise ForbiddenError(
                "Only your own self profile can be changed.",
                ProfileErrorCode.SELF_WRITE_ONLY,
            )
        profile_id = ensure_profile(session, context.space_id, context.account_id).id
    elif subject.id == context.account_id:
        raise ValidationError(
            "A private partner note must describe the other active partner.",
            ProfileErrorCode.PARTNER_NOTE_TARGET_REQUIRED,
        )

    preference = ProfilePreference(
        space_id=context.space_id,
        owner_id=context.account_id,
        privacy_class=privacy_for(visibility).value,
        profile_id=profile_id,
        account_id=subject.id,
        category=category.value,
        topic=_clean_topic(topic),
        sentiment=sentiment.value,
        visibility=visibility.value,
        payload=ProfilePreferencePayload(value=_clean_value(value)),
    )
    session.add(preference)
    session.flush()
    return preference


def update_preference(
    session: Session,
    context: AuthorizationContext,
    preference_id: UUID | str,
    *,
    expected_version: int,
    category: PreferenceCategory,
    topic: str,
    sentiment: PreferenceSentiment,
    value: str,
) -> ProfilePreference:
    preference = require_writable(session, ProfilePreference, context, preference_id)
    if preference.version != expected_version:
        raise ConflictError(
            "The profile preference was changed by someone else.",
            ErrorCode.VERSION_CONFLICT,
        )

    preference.category = category.value
    preference.topic = _clean_topic(topic)
    preference.sentiment = sentiment.value
    preference.payload = ProfilePreferencePayload(value=_clean_value(value))

    try:
        session.flush()
    except StaleDataError as stale:
        raise ConflictError(
            "The profile preference was changed by someone else.",
            ErrorCode.VERSION_CONFLICT,
        ) from stale
    return preference


def delete_preference(
    session: Session,
    context: AuthorizationContext,
    preference_id: UUID | str,
    *,
    expected_version: int,
) -> None:
    preference = require_writable(session, ProfilePreference, context, preference_id)
    if preference.version != expected_version:
        raise ConflictError(
            "The profile preference was changed by someone else.",
            ErrorCode.VERSION_CONFLICT,
        )

    session.delete(preference)
    try:
        session.flush()
    except StaleDataError as stale:
        raise ConflictError(
            "The profile preference was changed by someone else.",
            ErrorCode.VERSION_CONFLICT,
        ) from stale
