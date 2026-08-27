"""Cross-cutting endpoint invariants.

Domain-specific visibility rules live with their domain. This matrix covers
the complementary guarantee that every endpoint enforces tenant isolation.

The distinction is completeness: a gap can exist because an endpoint is
missing from the matrix entirely. `test_the_contract_is_complete_covered`
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
    "To endpoint and what a request to it requires."

    method: str
    template: str
    body: dict[str, Any] | None = None
    if_match: bool = False
    resource_absence: str | None = None
    """Der Code, mit dem dieser Endpunkt eine unbekannte Ressource verneint.

    Nur fuer Endpunkte mit eigener Ressourcen-ID im Pfad.
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
TERMIN = {
    "label": "Jahrestag",
    "type": "ANNIVERSARY",
    "date": "2020-06-13",
    "repeats": "ANNUALLY",
    "visibility": "SHARED",
}
PRAEFERENZ = {
    "category": "DRINK",
    "topic": "lieblingsgetraenk",
    "sentiment": "LOVE",
    "value": "Wasser",
}
PROFIL = {
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

SPACE_ENDPUNKTE: tuple[Endpoint, ...] = (
    Endpoint("GET", "/api/v1/spaces/{spaceId}"),
    Endpoint("GET", "/api/v1/spaces/{spaceId}/profile"),
    Endpoint("PUT", "/api/v1/spaces/{spaceId}/profile", body=PROFIL, if_match=True),
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
        body={**PRAEFERENZ, "accountId": str(uuid4()), "visibility": "SELF_PROFILE"},
    ),
    Endpoint(
        "GET",
        "/api/v1/spaces/{spaceId}/profile-preferences/{preferenceId}",
        resource_absence="PROFILE_PREFERENCE_NOT_FOUND",
    ),
    Endpoint(
        "PUT",
        "/api/v1/spaces/{spaceId}/profile-preferences/{preferenceId}",
        body=PRAEFERENZ,
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
    Endpoint("POST", "/api/v1/spaces/{spaceId}/important-dates", body=TERMIN),
    Endpoint(
        "GET",
        "/api/v1/spaces/{spaceId}/important-dates/{dateId}",
        resource_absence="IMPORTANT_DATE_NOT_FOUND",
    ),
    Endpoint(
        "PUT",
        "/api/v1/spaces/{spaceId}/important-dates/{dateId}",
        body=TERMIN,
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
    # Verknuepfen setzt voraus, that schon jemand signed in is; exactly
    # This distinguishes it from sign-in through the same provider.
    ("POST", "/api/v1/auth/oidc/{connectionId}/link"),
    # A Passkey is a zusaetzlicher Zugang to a bestehenden Account;
    # registriert is it from the Sign-in heraus.
    ("POST", "/api/v1/auth/passkeys/registration/start"),
    ("POST", "/api/v1/auth/passkeys/registration/finish"),
)
"""Kontobezogen, aber nicht an einen Space gebunden. Anonym: 401."""

PUBLIC_ENDPOINTS: tuple[tuple[str, str], ...] = (
    ("GET", "/api/v1/health"),
    ("GET", "/api/v1/health/ready"),
    ("POST", "/api/v1/auth/register"),
    ("POST", "/api/v1/auth/sign-in"),
    ("POST", "/api/v1/auth/refresh"),
    ("POST", "/api/v1/invitations/accept"),
    # The Paths back into the Account: it start without Session, and their
    # Proof is the Once-Token from the Mail.
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
"""Absichtlich ohne Token erreichbar - sie sind der Weg *zu* einem Token.

Ihr Missbrauchsschutz sind Rate Limits und Einmal-Tokens, nachgewiesen in
`test_auth_flows` und `test_invitations`, nicht der Bearer-Kopf.
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
    basis = f"/api/v1/spaces/{space.id}"

    # The Einladung is created, while still Platz is: a voller Couple-Space
    # stellt no more from. Ben kommt same danach dazu.
    invitation = client.post(f"{basis}/invitations", json={}, headers=headers).json()

    relationship_service.add_member(session, space.id, ben)
    session.flush()
    praeferenz = client.post(
        f"{basis}/profile-preferences",
        json={**PRAEFERENZ, "accountId": str(anna.id), "visibility": "SELF_PROFILE"},
        headers=headers,
    ).json()
    person = client.post(f"{basis}/related-persons", json=PERSON, headers=headers).json()
    termin = client.post(f"{basis}/important-dates", json=TERMIN, headers=headers).json()
    memory = client.post(f"{basis}/memories", json=MEMORY, headers=headers).json()
    heart_moment = client.post(f"{basis}/heart-moments", json=HEART_MOMENT, headers=headers).json()
    milestone = client.post(f"{basis}/milestones", json=MILESTONE, headers=headers).json()
    comment = client.post(
        f"{basis}/memories/{memory['id']}/comments", json=COMMENT, headers=headers
    ).json()
    wish = client.post(f"{basis}/wishes", json=WISH, headers=headers).json()
    place = client.post(f"{basis}/places", json=PLACE, headers=headers).json()
    plan = client.post(f"{basis}/plans", json=PLAN, headers=headers).json()
    attachment = client.post(f"{basis}/attachments", json=ATTACHMENT, headers=headers).json()

    return {
        "client": client,
        "space": space,
        "kopf_owner": headers,
        "kopf_fremd": auth(sign_in(session, foreign)),
        "ids": {
            "spaceId": str(space.id),
            "accountId": str(ben.id),
            "invitationId": invitation["id"],
            "preferenceId": praeferenz["id"],
            "personId": person["id"],
            "dateId": termin["id"],
            "memoryId": memory["id"],
            "heartMomentId": heart_moment["id"],
            "milestoneId": milestone["id"],
            "commentId": comment["id"],
            "wishId": wish["id"],
            "planId": plan["id"],
            "placeId": place["id"],
            # The Target a typed Relation. A Erinnerung is sufficient
            # for alle drei Relationsarten: the Checks this Matrix
            # apply before the Zielaufloesung.
            "targetId": memory["id"],
            "attachmentId": attachment["attachment"]["id"],
        },
    }


def _path(endpoint: Endpoint, ids: dict[str, str], **ersatz: str) -> str:
    values = {**ids, **ersatz}
    return endpoint.template.format(**values)


def _send(scenario, endpoint: Endpoint, path: str, headers: dict[str, str] | None):  # type: ignore[no-untyped-def]
    headers = dict(headers or {})
    if endpoint.if_match:
        # The Konfliktschutz is Pflicht; without the Kopf would check this Test
        # only still, that it is missing.
        headers["If-Match"] = '"1"'

    request_kwargs: dict[str, Any] = {}
    if endpoint.body is not None:
        request_kwargs["json"] = endpoint.body
    if endpoint.query:
        request_kwargs["params"] = endpoint.query
    return scenario["client"].request(endpoint.method, path, headers=headers, **request_kwargs)


@pytest.mark.parametrize("endpunkt", SPACE_ENDPUNKTE, ids=str)
class TestJederSpaceEndpunkt:
    "Vier Fragen to every Endpoint, the to a Space haengt."

    def test_anonymous_remains_401(self, scenario, endpoint: Endpoint) -> None:  # type: ignore[no-untyped-def]
        response = _send(scenario, endpoint, _path(endpoint, scenario["ids"]), None)
        assert response.status_code == 401
        assert response.json()["code"] == "AUTHENTICATION_REQUIRED"

    def test_foreign_gets_404_and_not_403(self, scenario, endpoint: Endpoint) -> None:  # type: ignore[no-untyped-def]
        "a 403 would confirm that the space exists."
        response = _send(
            scenario, endpoint, _path(endpoint, scenario["ids"]), scenario["kopf_fremd"]
        )
        assert response.status_code == 404
        assert response.json()["code"] == SPACE_ABSENCE

    def test_foreign_space_and_invented_are_indistinguishable(  # type: ignore[no-untyped-def]
        self, scenario, endpoint: Endpoint
    ) -> None:
        real = _send(scenario, endpoint, _path(endpoint, scenario["ids"]), scenario["kopf_fremd"])
        erfunden = _send(
            scenario,
            endpoint,
            _path(endpoint, scenario["ids"], spaceId=str(uuid4())),
            scenario["kopf_fremd"],
        )
        assert real.status_code == erfunden.status_code == 404
        assert real.json() == erfunden.json()

    def test_malformed_space_id_remains_same_404(self, scenario, endpoint: Endpoint) -> None:  # type: ignore[no-untyped-def]
        response = _send(
            scenario,
            endpoint,
            _path(endpoint, scenario["ids"], spaceId="' OR 1=1 --"),
            scenario["kopf_owner"],
        )
        assert response.status_code == 404
        assert response.json()["code"] == SPACE_ABSENCE


DETAIL_ENDPUNKTE = tuple(e for e in SPACE_ENDPUNKTE if e.resource_absence is not None)


@pytest.mark.parametrize("endpunkt", DETAIL_ENDPUNKTE, ids=str)
class TestJedeRessourcenId:
    "Within the actor's own space, the resource ID decides and reveals nothing."

    def test_unknown_resource_remains_404(self, scenario, endpoint: Endpoint) -> None:  # type: ignore[no-untyped-def]
        path = endpoint.template.format(
            **{**scenario["ids"], **dict.fromkeys(_resources_platzhalter(endpoint), str(uuid4()))}
        )
        response = _send(scenario, endpoint, path, scenario["kopf_owner"])
        assert response.status_code == 404
        assert response.json()["code"] == endpoint.resource_absence

    def test_malformed_resources_id_remains_same_404(self, scenario, endpoint: Endpoint) -> None:  # type: ignore[no-untyped-def]
        "well-formedness must not disclose existence."
        unknown = endpoint.template.format(
            **{**scenario["ids"], **dict.fromkeys(_resources_platzhalter(endpoint), str(uuid4()))}
        )
        malformed = endpoint.template.format(
            **{**scenario["ids"], **dict.fromkeys(_resources_platzhalter(endpoint), "nicht-echt")}
        )
        first = _send(scenario, endpoint, unknown, scenario["kopf_owner"])
        second = _send(scenario, endpoint, malformed, scenario["kopf_owner"])
        assert first.status_code == second.status_code == 404
        assert first.json() == second.json()


def _resources_platzhalter(endpoint: Endpoint) -> tuple[str, ...]:
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


SCHREIBENDE_ENDPUNKTE = tuple(e for e in SPACE_ENDPUNKTE if e.if_match)


@pytest.mark.parametrize("endpunkt", SCHREIBENDE_ENDPUNKTE, ids=str)
def test_without_if_match_is_not_geschrieben(scenario, endpoint: Endpoint) -> None:  # type: ignore[no-untyped-def]
    "a missing header is the silent path to disabling conflict protection."
    path = _path(endpoint, scenario["ids"])
    request_kwargs: dict[str, Any] = {"json": endpoint.body} if endpoint.body is not None else {}
    if endpoint.query:
        request_kwargs["params"] = endpoint.query
    response = scenario["client"].request(
        endpoint.method, path, headers=scenario["kopf_owner"], **request_kwargs
    )
    assert response.status_code == 422

    # And the Resource is stored unchanged there; therefore the deleted not.
    if endpoint.method == "DELETE":
        if "{commentId}" in endpoint.template:
            afterwards = scenario["client"].patch(
                path,
                json=COMMENT,
                headers={**scenario["kopf_owner"], "If-Match": '"1"'},
            )
            assert afterwards.status_code == 200
        else:
            afterwards = scenario["client"].get(path, headers=scenario["kopf_owner"])
            assert afterwards.status_code == 200


def test_the_contract_is_complete_covered() -> None:
    """a new operation without to entry in this file makes the suite fail.

    The is the eigentliche Zweck the Matrix. A Regel, the man to jedem
    new Endpoint from Hand mitschreiben must, is irgendwann vergessen -
    and a vergessener Mandantenschutz fails in the Betrieb niemandem on.
    """
    schema = create_app().openapi()
    contract = {
        (methode.upper(), path)
        for path, operationen in schema["paths"].items()
        for methode in operationen
    }
    covered = (
        {(e.method, e.template) for e in SPACE_ENDPUNKTE}
        | set(AUTHENTICATED_ONLY)
        | set(PUBLIC_ENDPOINTS)
    )
    assert contract == covered


@pytest.mark.parametrize(("methode", "pfad"), AUTHENTICATED_ONLY, ids=str)
def test_account_scoped_endpoints_bleiben_anonymous_closed(
    scenario, methode: str, path: str
) -> None:  # type: ignore[no-untyped-def]
    response = scenario["client"].request(methode, path, json={})
    assert response.status_code == 401
    assert response.json()["code"] == "AUTHENTICATION_REQUIRED"


def test_public_endpoints_verlangen_no_token(scenario) -> None:  # type: ignore[no-untyped-def]
    "the countercheck: these endpoints lead to a token and remain public."
    for path in ("/api/v1/health", "/api/v1/health/ready"):
        assert scenario["client"].get(path).status_code == 200
