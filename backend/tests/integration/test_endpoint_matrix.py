"""Cross-cutting endpoint invariants.

Domain-specific visibility rules live with their domain. This matrix covers
the complementary guarantee that every endpoint enforces tenant isolation.

The distinction is completeness: a gap can exist because an endpoint is
missing from the matrix entirely. `test_contract_is_completely_covered`
therefore compares the table below with the OpenAPI contract. A new operation
without an entry makes the suite fail before it reaches production.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from sidebyside.main import create_app
from sidebyside.relationship import service as relationship_service
from tests.conftest import auth, make_account, make_space, requires_database, sign_in

pytestmark = [pytest.mark.integration, requires_database]

SPACE_ABSENCE = "SPACE_NOT_FOUND"


@dataclass(frozen=True)
class Endpoint:
    "An endpoint and the requirements for a request to it."

    method: str
    template: str
    body: dict[str, Any] | None = None
    if_match: bool = False
    resource_absence: str | None = None
    """The code this endpoint uses to deny an unknown resource.

    Only set for endpoints with their own resource ID in the path.
    """

    placeholders: tuple[str, ...] = field(default=())
    query: dict[str, str] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"{self.method} {self.template}"


PERSON = {
    "displayName": "Lisa",
    "relationship": "CHILD",
    "birthday": None,
    "birthdayYearKnown": False,
    "visibility": "SHARED",
}
IMPORTANT_DATE = {
    "label": "Jahrestag",
    "type": "ANNIVERSARY",
    "date": "2020-06-13",
    "repeats": "ANNUALLY",
    "visibility": "SHARED",
}
PREFERENCE = {
    "category": "DRINK",
    "topic": "lieblingsgetraenk",
    "sentiment": "LOVE",
    "value": "Wasser",
}
PROFILE = {
    "relationshipStartedOn": "2020-06-13",
    "showRelationshipDuration": True,
    "durationDisplayMode": "YEARS_MONTHS",
}
MEMORY = {
    "title": "Matrix Memory",
    "body": "Gemeinsame Erinnerung fuer die Endpoint-Matrix.",
    "happenedOn": "2025-06-13",
}
HEART_MOMENT = {
    "text": "Matrix HeartMoment",
    "emotion": "LOVED",
    "visibility": "SHARED",
    "happenedOn": "2025-06-13",
}
ATTACHMENT = {
    "mediaType": "IMAGE",
    "originalName": "matrix.jpg",
    "expectedMimeType": "image/jpeg",
    "expectedSize": 2048,
}
MILESTONE = {
    "title": "Matrix Milestone",
    "body": "Text",
    "happenedOn": "2025-06-13",
}
COMMENT = {"body": "Matrix Comment"}
WISH = {"title": "Matrix Wish"}
PLAN = {"title": "Matrix Plan", "description": "Text"}
PLACE = {"name": "Matrix Place", "latitude": 52.520008, "longitude": 13.404954}

SPACE_ENDPOINTS: tuple[Endpoint, ...] = (
    Endpoint("GET", "/api/v1/spaces/{spaceId}"),
    Endpoint("GET", "/api/v1/spaces/{spaceId}/profile"),
    Endpoint("PUT", "/api/v1/spaces/{spaceId}/profile", body=PROFILE, if_match=True),
    Endpoint("GET", "/api/v1/spaces/{spaceId}/invitations"),
    Endpoint("POST", "/api/v1/spaces/{spaceId}/invitations", body={}),
    Endpoint(
        "DELETE",
        "/api/v1/spaces/{spaceId}/invitations/{invitationId}",
        resource_absence="INVITATION_NOT_FOUND",
    ),
    Endpoint(
        "GET",
        "/api/v1/spaces/{spaceId}/profiles/{accountId}",
        resource_absence="PARTNER_PROFILE_NOT_FOUND",
    ),
    Endpoint("GET", "/api/v1/spaces/{spaceId}/profile-preferences"),
    Endpoint(
        "POST",
        "/api/v1/spaces/{spaceId}/profile-preferences",
        body={**PREFERENCE, "accountId": str(uuid4()), "visibility": "SELF_PROFILE"},
    ),
    Endpoint(
        "GET",
        "/api/v1/spaces/{spaceId}/profile-preferences/{preferenceId}",
        resource_absence="PROFILE_PREFERENCE_NOT_FOUND",
    ),
    Endpoint(
        "PUT",
        "/api/v1/spaces/{spaceId}/profile-preferences/{preferenceId}",
        body=PREFERENCE,
        if_match=True,
        resource_absence="PROFILE_PREFERENCE_NOT_FOUND",
    ),
    Endpoint(
        "DELETE",
        "/api/v1/spaces/{spaceId}/profile-preferences/{preferenceId}",
        if_match=True,
        resource_absence="PROFILE_PREFERENCE_NOT_FOUND",
    ),
    Endpoint("GET", "/api/v1/spaces/{spaceId}/related-persons"),
    Endpoint("POST", "/api/v1/spaces/{spaceId}/related-persons", body=PERSON),
    Endpoint(
        "GET",
        "/api/v1/spaces/{spaceId}/related-persons/{personId}",
        resource_absence="RELATED_PERSON_NOT_FOUND",
    ),
    Endpoint(
        "PUT",
        "/api/v1/spaces/{spaceId}/related-persons/{personId}",
        body=PERSON,
        if_match=True,
        resource_absence="RELATED_PERSON_NOT_FOUND",
    ),
    Endpoint(
        "DELETE",
        "/api/v1/spaces/{spaceId}/related-persons/{personId}",
        if_match=True,
        resource_absence="RELATED_PERSON_NOT_FOUND",
        query={"deletePolicy": "preserve"},
    ),
    Endpoint("GET", "/api/v1/spaces/{spaceId}/important-dates"),
    Endpoint("POST", "/api/v1/spaces/{spaceId}/important-dates", body=IMPORTANT_DATE),
    Endpoint(
        "GET",
        "/api/v1/spaces/{spaceId}/important-dates/{dateId}",
        resource_absence="IMPORTANT_DATE_NOT_FOUND",
    ),
    Endpoint(
        "PUT",
        "/api/v1/spaces/{spaceId}/important-dates/{dateId}",
        body=IMPORTANT_DATE,
        if_match=True,
        resource_absence="IMPORTANT_DATE_NOT_FOUND",
    ),
    Endpoint(
        "DELETE",
        "/api/v1/spaces/{spaceId}/important-dates/{dateId}",
        if_match=True,
        resource_absence="IMPORTANT_DATE_NOT_FOUND",
    ),
    Endpoint("GET", "/api/v1/spaces/{spaceId}/memories"),
    Endpoint("POST", "/api/v1/spaces/{spaceId}/memories", body=MEMORY),
    Endpoint(
        "GET",
        "/api/v1/spaces/{spaceId}/memories/{memoryId}",
        resource_absence="RESOURCE_NOT_FOUND",
    ),
    Endpoint(
        "PATCH",
        "/api/v1/spaces/{spaceId}/memories/{memoryId}",
        body={"title": "Matrix Memory aktualisiert"},
        if_match=True,
        resource_absence="RESOURCE_NOT_FOUND",
    ),
    Endpoint(
        "DELETE",
        "/api/v1/spaces/{spaceId}/memories/{memoryId}",
        if_match=True,
        resource_absence="RESOURCE_NOT_FOUND",
    ),
    Endpoint(
        "PUT",
        "/api/v1/spaces/{spaceId}/memories/{memoryId}/attachments",
        body={"attachments": []},
        if_match=True,
        resource_absence="RESOURCE_NOT_FOUND",
    ),
    Endpoint("GET", "/api/v1/spaces/{spaceId}/heart-moments"),
    Endpoint("POST", "/api/v1/spaces/{spaceId}/heart-moments", body=HEART_MOMENT),
    Endpoint(
        "GET",
        "/api/v1/spaces/{spaceId}/heart-moments/{heartMomentId}",
        resource_absence="RESOURCE_NOT_FOUND",
    ),
    Endpoint(
        "PATCH",
        "/api/v1/spaces/{spaceId}/heart-moments/{heartMomentId}",
        body={"text": "Matrix HeartMoment aktualisiert"},
        if_match=True,
        resource_absence="RESOURCE_NOT_FOUND",
    ),
    Endpoint(
        "PATCH",
        "/api/v1/spaces/{spaceId}/heart-moments/{heartMomentId}/visibility",
        body={"visibility": "PRIVATE"},
        if_match=True,
        resource_absence="RESOURCE_NOT_FOUND",
    ),
    Endpoint(
        "DELETE",
        "/api/v1/spaces/{spaceId}/heart-moments/{heartMomentId}",
        if_match=True,
        resource_absence="RESOURCE_NOT_FOUND",
    ),
    Endpoint("GET", "/api/v1/spaces/{spaceId}/timeline"),
    Endpoint("GET", "/api/v1/spaces/{spaceId}/milestones"),
    Endpoint("POST", "/api/v1/spaces/{spaceId}/milestones", body=MILESTONE),
    Endpoint(
        "GET",
        "/api/v1/spaces/{spaceId}/milestones/{milestoneId}",
        resource_absence="RESOURCE_NOT_FOUND",
    ),
    Endpoint(
        "PATCH",
        "/api/v1/spaces/{spaceId}/milestones/{milestoneId}",
        body={"title": "Matrix Milestone aktualisiert"},
        if_match=True,
        resource_absence="RESOURCE_NOT_FOUND",
    ),
    Endpoint(
        "DELETE",
        "/api/v1/spaces/{spaceId}/milestones/{milestoneId}",
        if_match=True,
        resource_absence="RESOURCE_NOT_FOUND",
    ),
    Endpoint(
        "POST",
        "/api/v1/spaces/{spaceId}/memories/{memoryId}/comments",
        body=COMMENT,
        resource_absence="COMMENT_TARGET_NOT_AVAILABLE",
    ),
    Endpoint(
        "GET",
        "/api/v1/spaces/{spaceId}/memories/{memoryId}/comments",
        resource_absence="COMMENT_TARGET_NOT_AVAILABLE",
    ),
    Endpoint(
        "POST",
        "/api/v1/spaces/{spaceId}/heart-moments/{heartMomentId}/comments",
        body=COMMENT,
        resource_absence="COMMENT_TARGET_NOT_AVAILABLE",
    ),
    Endpoint(
        "GET",
        "/api/v1/spaces/{spaceId}/heart-moments/{heartMomentId}/comments",
        resource_absence="COMMENT_TARGET_NOT_AVAILABLE",
    ),
    Endpoint(
        "POST",
        "/api/v1/spaces/{spaceId}/milestones/{milestoneId}/comments",
        body=COMMENT,
        resource_absence="COMMENT_TARGET_NOT_AVAILABLE",
    ),
    Endpoint(
        "GET",
        "/api/v1/spaces/{spaceId}/milestones/{milestoneId}/comments",
        resource_absence="COMMENT_TARGET_NOT_AVAILABLE",
    ),
    Endpoint(
        "PATCH",
        "/api/v1/spaces/{spaceId}/comments/{commentId}",
        body=COMMENT,
        if_match=True,
        resource_absence="COMMENT_TARGET_NOT_AVAILABLE",
    ),
    Endpoint(
        "DELETE",
        "/api/v1/spaces/{spaceId}/comments/{commentId}",
        if_match=True,
        resource_absence="COMMENT_TARGET_NOT_AVAILABLE",
    ),
    Endpoint("GET", "/api/v1/spaces/{spaceId}/wishes"),
    Endpoint("POST", "/api/v1/spaces/{spaceId}/wishes", body=WISH),
    Endpoint(
        "GET",
        "/api/v1/spaces/{spaceId}/wishes/{wishId}",
        resource_absence="WISH_NOT_FOUND",
    ),
    Endpoint(
        "PATCH",
        "/api/v1/spaces/{spaceId}/wishes/{wishId}",
        body={"title": "Matrix Wish aktualisiert"},
        if_match=True,
        resource_absence="WISH_NOT_FOUND",
    ),
    Endpoint(
        "DELETE",
        "/api/v1/spaces/{spaceId}/wishes/{wishId}",
        if_match=True,
        resource_absence="WISH_NOT_FOUND",
    ),
    Endpoint(
        "POST",
        "/api/v1/spaces/{spaceId}/wishes/{wishId}/plan",
        body={},
        if_match=True,
        resource_absence="WISH_NOT_FOUND",
    ),
    Endpoint("GET", "/api/v1/spaces/{spaceId}/places"),
    Endpoint("POST", "/api/v1/spaces/{spaceId}/places", body=PLACE),
    Endpoint(
        "GET",
        "/api/v1/spaces/{spaceId}/places/{placeId}",
        resource_absence="PLACE_NOT_FOUND",
    ),
    Endpoint(
        "PATCH",
        "/api/v1/spaces/{spaceId}/places/{placeId}",
        body={"name": "Matrix Place aktualisiert"},
        if_match=True,
        resource_absence="PLACE_NOT_FOUND",
    ),
    Endpoint(
        "DELETE",
        "/api/v1/spaces/{spaceId}/places/{placeId}",
        if_match=True,
        resource_absence="PLACE_NOT_FOUND",
    ),
    Endpoint(
        "GET",
        "/api/v1/spaces/{spaceId}/places/{placeId}/memories",
        resource_absence="PLACE_NOT_FOUND",
    ),
    Endpoint(
        "PUT",
        "/api/v1/spaces/{spaceId}/places/{placeId}/memories/{targetId}",
        resource_absence="PLACE_NOT_FOUND",
    ),
    Endpoint(
        "DELETE",
        "/api/v1/spaces/{spaceId}/places/{placeId}/memories/{targetId}",
        resource_absence="PLACE_NOT_FOUND",
    ),
    Endpoint(
        "GET",
        "/api/v1/spaces/{spaceId}/places/{placeId}/heart-moments",
        resource_absence="PLACE_NOT_FOUND",
    ),
    Endpoint(
        "PUT",
        "/api/v1/spaces/{spaceId}/places/{placeId}/heart-moments/{targetId}",
        resource_absence="PLACE_NOT_FOUND",
    ),
    Endpoint(
        "DELETE",
        "/api/v1/spaces/{spaceId}/places/{placeId}/heart-moments/{targetId}",
        resource_absence="PLACE_NOT_FOUND",
    ),
    Endpoint(
        "GET",
        "/api/v1/spaces/{spaceId}/places/{placeId}/milestones",
        resource_absence="PLACE_NOT_FOUND",
    ),
    Endpoint(
        "PUT",
        "/api/v1/spaces/{spaceId}/places/{placeId}/milestones/{targetId}",
        resource_absence="PLACE_NOT_FOUND",
    ),
    Endpoint(
        "DELETE",
        "/api/v1/spaces/{spaceId}/places/{placeId}/milestones/{targetId}",
        resource_absence="PLACE_NOT_FOUND",
    ),
    Endpoint("GET", "/api/v1/spaces/{spaceId}/plans"),
    Endpoint("POST", "/api/v1/spaces/{spaceId}/plans", body=PLAN),
    Endpoint(
        "GET",
        "/api/v1/spaces/{spaceId}/plans/{planId}",
        resource_absence="PLAN_NOT_FOUND",
    ),
    Endpoint(
        "PATCH",
        "/api/v1/spaces/{spaceId}/plans/{planId}",
        body={"title": "Matrix Plan aktualisiert"},
        if_match=True,
        resource_absence="PLAN_NOT_FOUND",
    ),
    Endpoint(
        "DELETE",
        "/api/v1/spaces/{spaceId}/plans/{planId}",
        if_match=True,
        resource_absence="PLAN_NOT_FOUND",
    ),
    Endpoint(
        "POST",
        "/api/v1/spaces/{spaceId}/plans/{planId}/schedule",
        body={"plannedStart": "2026-09-01T18:00:00Z"},
        if_match=True,
        resource_absence="PLAN_NOT_FOUND",
    ),
    Endpoint(
        "POST",
        "/api/v1/spaces/{spaceId}/plans/{planId}/unschedule",
        body={},
        if_match=True,
        resource_absence="PLAN_NOT_FOUND",
    ),
    Endpoint(
        "POST",
        "/api/v1/spaces/{spaceId}/plans/{planId}/complete",
        body={"experiencedOn": "2026-08-20"},
        if_match=True,
        resource_absence="PLAN_NOT_FOUND",
    ),
    Endpoint(
        "POST",
        "/api/v1/spaces/{spaceId}/plans/{planId}/return-to-wish",
        body={},
        if_match=True,
        resource_absence="PLAN_NOT_FOUND",
    ),
    Endpoint("POST", "/api/v1/spaces/{spaceId}/attachments", body=ATTACHMENT),
    Endpoint(
        "GET",
        "/api/v1/spaces/{spaceId}/attachments/{attachmentId}",
        resource_absence="RESOURCE_NOT_FOUND",
    ),
    Endpoint(
        "PUT",
        "/api/v1/spaces/{spaceId}/attachments/{attachmentId}/content",
        resource_absence="RESOURCE_NOT_FOUND",
    ),
    Endpoint(
        "GET",
        "/api/v1/spaces/{spaceId}/attachments/{attachmentId}/content",
        resource_absence="RESOURCE_NOT_FOUND",
    ),
    Endpoint(
        "POST",
        "/api/v1/spaces/{spaceId}/attachments/{attachmentId}/finalize",
        body={},
        resource_absence="RESOURCE_NOT_FOUND",
    ),
    Endpoint(
        "POST",
        "/api/v1/spaces/{spaceId}/attachments/{attachmentId}/read-access",
        body={"parentType": "NONE"},
        resource_absence="RESOURCE_NOT_FOUND",
    ),
    Endpoint(
        "DELETE",
        "/api/v1/spaces/{spaceId}/attachments/{attachmentId}",
        if_match=True,
        resource_absence="RESOURCE_NOT_FOUND",
    ),
)

AUTHENTICATED_ONLY: tuple[tuple[str, str], ...] = (
    ("GET", "/api/v1/auth/me"),
    ("POST", "/api/v1/auth/sign-out"),
    ("POST", "/api/v1/auth/password"),
    ("POST", "/api/v1/auth/email/verification/request"),
    # Linking requires an existing signed-in account, which distinguishes it
    # from sign-in through the same provider.
    ("POST", "/api/v1/auth/oidc/{connectionId}/link"),
    # A passkey is an additional access method for an existing account and is
    # registered from an authenticated session.
    ("POST", "/api/v1/auth/passkeys/registration/start"),
    ("POST", "/api/v1/auth/passkeys/registration/finish"),
)
"""Account-scoped but not space-scoped. Anonymous requests receive 401."""

PUBLIC_ENDPOINTS: tuple[tuple[str, str], ...] = (
    ("GET", "/api/v1/health"),
    ("GET", "/api/v1/health/ready"),
    ("POST", "/api/v1/auth/register"),
    ("POST", "/api/v1/auth/sign-in"),
    ("POST", "/api/v1/auth/refresh"),
    ("POST", "/api/v1/invitations/accept"),
    # These paths lead back into an account. They start without a session and
    # use the single-use token delivered by mail as their proof.
    ("POST", "/api/v1/auth/magic-link/request"),
    ("POST", "/api/v1/auth/magic-link/consume"),
    ("POST", "/api/v1/auth/email/verification/confirm"),
    ("POST", "/api/v1/auth/recovery/request"),
    ("POST", "/api/v1/auth/recovery/consume"),
    ("POST", "/api/v1/auth/oidc/{connectionId}/start"),
    ("POST", "/api/v1/auth/oidc/{connectionId}/callback"),
    ("POST", "/api/v1/auth/passkeys/authentication/start"),
    ("POST", "/api/v1/auth/passkeys/authentication/finish"),
)
"""Intentionally reachable without a bearer token because they lead to a token.

Their abuse protection is provided by rate limits and single-use tokens, as
covered in `test_auth_flows` and `test_invitations`.
"""


@pytest.fixture
def scenario(client, session: Session):  # type: ignore[no-untyped-def]
    "A couple with one real resource per domain, plus a foreign one."
    anna = make_account(session, "Anna")
    ben = make_account(session, "Ben")
    foreign = make_account(session, "Fremde Person")

    space = make_space(session, anna)
    make_space(session, foreign)
    session.flush()

    token_a = sign_in(session, anna)
    headers = auth(token_a)
    base_path = f"/api/v1/spaces/{space.id}"

    # Create the invitation while the couple still has a free member slot. A
    # full couple space issues no new invitation, so Ben joins afterwards.
    invitation = client.post(f"{base_path}/invitations", json={}, headers=headers).json()

    relationship_service.add_member(session, space.id, ben)
    session.flush()
    preference = client.post(
        f"{base_path}/profile-preferences",
        json={**PREFERENCE, "accountId": str(anna.id), "visibility": "SELF_PROFILE"},
        headers=headers,
    ).json()
    person = client.post(f"{base_path}/related-persons", json=PERSON, headers=headers).json()
    important_date = client.post(
        f"{base_path}/important-dates", json=IMPORTANT_DATE, headers=headers
    ).json()
    memory = client.post(f"{base_path}/memories", json=MEMORY, headers=headers).json()
    heart_moment = client.post(
        f"{base_path}/heart-moments", json=HEART_MOMENT, headers=headers
    ).json()
    milestone = client.post(f"{base_path}/milestones", json=MILESTONE, headers=headers).json()
    comment = client.post(
        f"{base_path}/memories/{memory['id']}/comments", json=COMMENT, headers=headers
    ).json()
    wish = client.post(f"{base_path}/wishes", json=WISH, headers=headers).json()
    place = client.post(f"{base_path}/places", json=PLACE, headers=headers).json()
    plan = client.post(f"{base_path}/plans", json=PLAN, headers=headers).json()
    attachment = client.post(
        f"{base_path}/attachments", json=ATTACHMENT, headers=headers
    ).json()

    return {
        "client": client,
        "space": space,
        "owner_headers": headers,
        "foreign_headers": auth(sign_in(session, foreign)),
        "ids": {
            "spaceId": str(space.id),
            "accountId": str(ben.id),
            "invitationId": invitation["id"],
            "preferenceId": preference["id"],
            "personId": person["id"],
            "dateId": important_date["id"],
            "memoryId": memory["id"],
            "heartMomentId": heart_moment["id"],
            "milestoneId": milestone["id"],
            "commentId": comment["id"],
            "wishId": wish["id"],
            "planId": plan["id"],
            "placeId": place["id"],
            # The target is a typed relation. A memory is enough for all three
            # relation types because this matrix checks occur before target resolution.
            "targetId": memory["id"],
            "attachmentId": attachment["attachment"]["id"],
        },
    }


def _path(endpoint: Endpoint, ids: dict[str, str], **replacements: str) -> str:
    values = {**ids, **replacements}
    return endpoint.template.format(**values)


def _send(scenario, endpoint: Endpoint, path: str, headers: dict[str, str] | None):  # type: ignore[no-untyped-def]
    headers = dict(headers or {})
    if endpoint.if_match:
        # Conflict protection is mandatory. Supplying the header ensures these
        # tests exercise tenant/resource isolation rather than header absence.
        headers["If-Match"] = '"1"'

    request_kwargs: dict[str, Any] = {}
    if endpoint.body is not None:
        request_kwargs["json"] = endpoint.body
    if endpoint.query:
        request_kwargs["params"] = endpoint.query
    return scenario["client"].request(endpoint.method, path, headers=headers, **request_kwargs)


@pytest.mark.parametrize("endpoint", SPACE_ENDPOINTS, ids=str)
class TestEverySpaceEndpoint:
    "Four tenant-isolation questions for every endpoint scoped to a space."

    def test_anonymous_remains_401(self, scenario, endpoint: Endpoint) -> None:  # type: ignore[no-untyped-def]
        response = _send(scenario, endpoint, _path(endpoint, scenario["ids"]), None)
        assert response.status_code == 401
        assert response.json()["code"] == "AUTHENTICATION_REQUIRED"

    def test_foreign_actor_gets_404_not_403(self, scenario, endpoint: Endpoint) -> None:  # type: ignore[no-untyped-def]
        "A 403 would confirm that the space exists."
        response = _send(
            scenario,
            endpoint,
            _path(endpoint, scenario["ids"]),
            scenario["foreign_headers"],
        )
        assert response.status_code == 404
        assert response.json()["code"] == SPACE_ABSENCE

    def test_foreign_space_and_invented_space_are_indistinguishable(
        self, scenario, endpoint: Endpoint
    ) -> None:  # type: ignore[no-untyped-def]
        real = _send(
            scenario, endpoint, _path(endpoint, scenario["ids"]), scenario["foreign_headers"]
        )
        invented = _send(
            scenario,
            endpoint,
            _path(endpoint, scenario["ids"], spaceId=str(uuid4())),
            scenario["foreign_headers"],
        )
        assert real.status_code == invented.status_code == 404
        assert real.json() == invented.json()

    def test_malformed_space_id_remains_same_404(self, scenario, endpoint: Endpoint) -> None:  # type: ignore[no-untyped-def]
        response = _send(
            scenario,
            endpoint,
            _path(endpoint, scenario["ids"], spaceId="' OR 1=1 --"),
            scenario["owner_headers"],
        )
        assert response.status_code == 404
        assert response.json()["code"] == SPACE_ABSENCE


DETAIL_ENDPOINTS = tuple(
    endpoint for endpoint in SPACE_ENDPOINTS if endpoint.resource_absence is not None
)


@pytest.mark.parametrize("endpoint", DETAIL_ENDPOINTS, ids=str)
class TestEveryResourceId:
    "Within the actor's own space, the resource ID decides and reveals nothing."

    def test_unknown_resource_remains_404(self, scenario, endpoint: Endpoint) -> None:  # type: ignore[no-untyped-def]
        path = endpoint.template.format(
            **{**scenario["ids"], **dict.fromkeys(_resource_placeholders(endpoint), str(uuid4()))}
        )
        response = _send(scenario, endpoint, path, scenario["owner_headers"])
        assert response.status_code == 404
        assert response.json()["code"] == endpoint.resource_absence

    def test_malformed_resource_id_remains_same_404(self, scenario, endpoint: Endpoint) -> None:  # type: ignore[no-untyped-def]
        "Well-formedness must not disclose existence."
        unknown = endpoint.template.format(
            **{**scenario["ids"], **dict.fromkeys(_resource_placeholders(endpoint), str(uuid4()))}
        )
        malformed = endpoint.template.format(
            **{**scenario["ids"], **dict.fromkeys(_resource_placeholders(endpoint), "nicht-echt")}
        )
        first = _send(scenario, endpoint, unknown, scenario["owner_headers"])
        second = _send(scenario, endpoint, malformed, scenario["owner_headers"])
        assert first.status_code == second.status_code == 404
        assert first.json() == second.json()


def _resource_placeholders(endpoint: Endpoint) -> tuple[str, ...]:
    return tuple(
        name
        for name in (
            "invitationId",
            "preferenceId",
            "personId",
            "dateId",
            "accountId",
            "memoryId",
            "heartMomentId",
            "attachmentId",
            "milestoneId",
            "commentId",
            "wishId",
            "planId",
            "placeId",
            "targetId",
        )
        if "{" + name + "}" in endpoint.template
    )


WRITING_ENDPOINTS = tuple(endpoint for endpoint in SPACE_ENDPOINTS if endpoint.if_match)


@pytest.mark.parametrize("endpoint", WRITING_ENDPOINTS, ids=str)
def test_without_if_match_does_not_write(scenario, endpoint: Endpoint) -> None:  # type: ignore[no-untyped-def]
    "A missing header is the silent path to disabling conflict protection."
    path = _path(endpoint, scenario["ids"])
    request_kwargs: dict[str, Any] = {"json": endpoint.body} if endpoint.body is not None else {}
    if endpoint.query:
        request_kwargs["params"] = endpoint.query
    response = scenario["client"].request(
        endpoint.method, path, headers=scenario["owner_headers"], **request_kwargs
    )
    assert response.status_code == 422

    # Verify that a DELETE without the required header did not remove the resource.
    if endpoint.method == "DELETE":
        if "{commentId}" in endpoint.template:
            afterwards = scenario["client"].patch(
                path,
                json=COMMENT,
                headers={**scenario["owner_headers"], "If-Match": '"1"'},
            )
            assert afterwards.status_code == 200
        else:
            afterwards = scenario["client"].get(path, headers=scenario["owner_headers"])
            assert afterwards.status_code == 200


def test_contract_is_completely_covered() -> None:
    """A new operation without an entry in this file makes the suite fail.

    This is the matrix's primary purpose. A rule that developers must remember
    to copy to every new endpoint will eventually be forgotten; a missing tenant
    guard can otherwise remain invisible until production.
    """
    schema = create_app().openapi()
    contract = {
        (method.upper(), path)
        for path, operations in schema["paths"].items()
        for method in operations
    }
    covered = (
        {(endpoint.method, endpoint.template) for endpoint in SPACE_ENDPOINTS}
        | set(AUTHENTICATED_ONLY)
        | set(PUBLIC_ENDPOINTS)
    )
    assert contract == covered


@pytest.mark.parametrize(("method", "path"), AUTHENTICATED_ONLY, ids=str)
def test_account_scoped_endpoints_remain_closed_to_anonymous(
    scenario, method: str, path: str
) -> None:  # type: ignore[no-untyped-def]
    response = scenario["client"].request(method, path, json={})
    assert response.status_code == 401
    assert response.json()["code"] == "AUTHENTICATION_REQUIRED"


def test_public_endpoints_require_no_token(scenario) -> None:  # type: ignore[no-untyped-def]
    "The countercheck: these endpoints lead to a token and remain public."
    for path in ("/api/v1/health", "/api/v1/health/ready"):
        assert scenario["client"].get(path).status_code == 200
