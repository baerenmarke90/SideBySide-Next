"""PartnerProfile and ProfilePreference endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Path, Response, status
from pydantic import Field, field_validator

from sidebyside.api.concurrency import IfMatchVersion, etag_for
from sidebyside.api.deps import Authorization, DbSession
from sidebyside.api.errors import problem_responses
from sidebyside.api.schema import ApiModel
from sidebyside.profiles import service
from sidebyside.profiles.models import (
    PartnerProfile,
    PreferenceCategory,
    PreferenceSentiment,
    ProfilePreference,
    ProfileVisibility,
)

router = APIRouter(tags=["profiles"])

ETAG_HEADERS = {
    "ETag": {
        "description": "ProfilePreference version to use for the next If-Match write request.",
        "schema": {"type": "string"},
    }
}


class PreferenceFields(ApiModel):
    category: PreferenceCategory
    topic: str = Field(min_length=1, max_length=120)
    sentiment: PreferenceSentiment
    value: str = Field(min_length=1, max_length=2000)

    @field_validator("topic", "value")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned


class ProfilePreferenceCreate(PreferenceFields):
    account_id: UUID
    visibility: ProfileVisibility


class ProfilePreferenceUpdate(PreferenceFields):
    pass


class ProfilePreferenceView(ApiModel):
    id: UUID
    account_id: UUID
    category: PreferenceCategory
    topic: str
    sentiment: PreferenceSentiment
    value: str
    visibility: ProfileVisibility
    version: int
    created_at: datetime
    updated_at: datetime


class PartnerProfileView(ApiModel):
    id: UUID
    account_id: UUID
    display_name: str
    created_at: datetime
    updated_at: datetime
    preferences: list[ProfilePreferenceView]


def _preference_view(preference: ProfilePreference) -> ProfilePreferenceView:
    return ProfilePreferenceView(
        id=preference.id,
        account_id=preference.account_id,
        category=PreferenceCategory(preference.category),
        topic=preference.topic,
        sentiment=PreferenceSentiment(preference.sentiment),
        value=preference.payload.value,
        visibility=ProfileVisibility(preference.visibility),
        version=preference.version,
        created_at=preference.created_at,
        updated_at=preference.updated_at,
    )


def _profile_view(
    profile: PartnerProfile,
    *,
    display_name: str,
    preferences: list[ProfilePreferenceView],
) -> PartnerProfileView:
    return PartnerProfileView(
        id=profile.id,
        account_id=profile.owner_id,
        display_name=display_name,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
        preferences=preferences,
    )


@router.get(
    "/spaces/{spaceId}/profiles/{accountId}",
    response_model=PartnerProfileView,
    responses=problem_responses(401, 404),
)
def get_partner_profile(
    authorization: Authorization,
    session: DbSession,
    account_id: Annotated[str, Path(alias="accountId")],
) -> PartnerProfileView:
    profile, subject, preferences = service.profile_preferences(session, authorization, account_id)
    return _profile_view(
        profile,
        display_name=subject.display_name,
        preferences=[_preference_view(preference) for preference in preferences],
    )


@router.get(
    "/spaces/{spaceId}/profile-preferences",
    response_model=list[ProfilePreferenceView],
    responses=problem_responses(401, 404),
)
def list_profile_preferences(
    authorization: Authorization,
    session: DbSession,
) -> list[ProfilePreferenceView]:
    return [
        _preference_view(preference)
        for preference in service.list_preferences(session, authorization)
    ]


@router.post(
    "/spaces/{spaceId}/profile-preferences",
    response_model=ProfilePreferenceView,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"headers": ETAG_HEADERS},
        **problem_responses(401, 403, 404, 422),
    },
)
def create_profile_preference(
    authorization: Authorization,
    session: DbSession,
    response: Response,
    body: ProfilePreferenceCreate,
) -> ProfilePreferenceView:
    preference = service.create_preference(
        session,
        authorization,
        account_id=body.account_id,
        visibility=body.visibility,
        category=body.category,
        topic=body.topic,
        sentiment=body.sentiment,
        value=body.value,
    )
    response.headers["ETag"] = etag_for(preference.version)
    return _preference_view(preference)


@router.get(
    "/spaces/{spaceId}/profile-preferences/{preferenceId}",
    response_model=ProfilePreferenceView,
    responses={
        200: {"headers": ETAG_HEADERS},
        **problem_responses(401, 404),
    },
)
def get_profile_preference(
    authorization: Authorization,
    session: DbSession,
    response: Response,
    preference_id: Annotated[str, Path(alias="preferenceId")],
) -> ProfilePreferenceView:
    preference = service.get_preference(session, authorization, preference_id)
    response.headers["ETag"] = etag_for(preference.version)
    return _preference_view(preference)


@router.put(
    "/spaces/{spaceId}/profile-preferences/{preferenceId}",
    response_model=ProfilePreferenceView,
    responses={
        200: {"headers": ETAG_HEADERS},
        **problem_responses(401, 403, 404, 409, 422),
    },
)
def update_profile_preference(
    authorization: Authorization,
    session: DbSession,
    response: Response,
    body: ProfilePreferenceUpdate,
    expected_version: IfMatchVersion,
    preference_id: Annotated[str, Path(alias="preferenceId")],
) -> ProfilePreferenceView:
    preference = service.update_preference(
        session,
        authorization,
        preference_id,
        expected_version=expected_version,
        category=body.category,
        topic=body.topic,
        sentiment=body.sentiment,
        value=body.value,
    )
    response.headers["ETag"] = etag_for(preference.version)
    return _preference_view(preference)


@router.delete(
    "/spaces/{spaceId}/profile-preferences/{preferenceId}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses=problem_responses(401, 403, 404, 409, 422),
)
def delete_profile_preference(
    authorization: Authorization,
    session: DbSession,
    expected_version: IfMatchVersion,
    preference_id: Annotated[str, Path(alias="preferenceId")],
) -> Response:
    service.delete_preference(
        session,
        authorization,
        preference_id,
        expected_version=expected_version,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
