"""Die Invarianten, die fuer *jeden* Endpunkt gelten muessen.

Die fachlichen Sichtbarkeitsregeln stehen bei ihrer Domaene - dort gehoeren
sie hin, und dort sind sie ausfuehrlich geprueft. Was hier steht, ist der
andere Teil: dass kein einziger Endpunkt die Mandantenpruefung vergisst.

Der Unterschied ist Vollstaendigkeit. Eine Luecke entsteht nicht dadurch,
dass jemand eine Regel falsch schreibt, sondern dadurch, dass ein neuer
Endpunkt sie gar nicht erst bekommt. `test_der_vertrag_ist_vollstaendig_
abgedeckt` haelt die Tabelle unten deshalb gegen den OpenAPI-Vertrag: eine
neue Operation ohne Eintrag macht die Suite rot, bevor sie in Betrieb geht.
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
class Endpunkt:
    """Ein Endpunkt und das, was eine Anfrage an ihn braucht."""

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

SPACE_ENDPUNKTE: tuple[Endpunkt, ...] = (
    Endpunkt("GET", "/api/v1/spaces/{spaceId}"),
    Endpunkt("GET", "/api/v1/spaces/{spaceId}/profile"),
    Endpunkt("PUT", "/api/v1/spaces/{spaceId}/profile", body=PROFIL, if_match=True),
    Endpunkt("GET", "/api/v1/spaces/{spaceId}/invitations"),
    Endpunkt("POST", "/api/v1/spaces/{spaceId}/invitations", body={}),
    Endpunkt(
        "DELETE",
        "/api/v1/spaces/{spaceId}/invitations/{invitationId}",
        resource_absence="INVITATION_NOT_FOUND",
    ),
    Endpunkt(
        "GET",
        "/api/v1/spaces/{spaceId}/profiles/{accountId}",
        resource_absence="PARTNER_PROFILE_NOT_FOUND",
    ),
    Endpunkt("GET", "/api/v1/spaces/{spaceId}/profile-preferences"),
    Endpunkt(
        "POST",
        "/api/v1/spaces/{spaceId}/profile-preferences",
        body={**PRAEFERENZ, "accountId": str(uuid4()), "visibility": "SELF_PROFILE"},
    ),
    Endpunkt(
        "GET",
        "/api/v1/spaces/{spaceId}/profile-preferences/{preferenceId}",
        resource_absence="PROFILE_PREFERENCE_NOT_FOUND",
    ),
    Endpunkt(
        "PUT",
        "/api/v1/spaces/{spaceId}/profile-preferences/{preferenceId}",
        body=PRAEFERENZ,
        if_match=True,
        resource_absence="PROFILE_PREFERENCE_NOT_FOUND",
    ),
    Endpunkt(
        "DELETE",
        "/api/v1/spaces/{spaceId}/profile-preferences/{preferenceId}",
        if_match=True,
        resource_absence="PROFILE_PREFERENCE_NOT_FOUND",
    ),
    Endpunkt("GET", "/api/v1/spaces/{spaceId}/related-persons"),
    Endpunkt("POST", "/api/v1/spaces/{spaceId}/related-persons", body=PERSON),
    Endpunkt(
        "GET",
        "/api/v1/spaces/{spaceId}/related-persons/{personId}",
        resource_absence="RELATED_PERSON_NOT_FOUND",
    ),
    Endpunkt(
        "PUT",
        "/api/v1/spaces/{spaceId}/related-persons/{personId}",
        body=PERSON,
        if_match=True,
        resource_absence="RELATED_PERSON_NOT_FOUND",
    ),
    Endpunkt(
        "DELETE",
        "/api/v1/spaces/{spaceId}/related-persons/{personId}",
        if_match=True,
        resource_absence="RELATED_PERSON_NOT_FOUND",
        query={"deletePolicy": "preserve"},
    ),
    Endpunkt("GET", "/api/v1/spaces/{spaceId}/important-dates"),
    Endpunkt("POST", "/api/v1/spaces/{spaceId}/important-dates", body=TERMIN),
    Endpunkt(
        "GET",
        "/api/v1/spaces/{spaceId}/important-dates/{dateId}",
        resource_absence="IMPORTANT_DATE_NOT_FOUND",
    ),
    Endpunkt(
        "PUT",
        "/api/v1/spaces/{spaceId}/important-dates/{dateId}",
        body=TERMIN,
        if_match=True,
        resource_absence="IMPORTANT_DATE_NOT_FOUND",
    ),
    Endpunkt(
        "DELETE",
        "/api/v1/spaces/{spaceId}/important-dates/{dateId}",
        if_match=True,
        resource_absence="IMPORTANT_DATE_NOT_FOUND",
    ),
    Endpunkt("GET", "/api/v1/spaces/{spaceId}/memories"),
    Endpunkt("POST", "/api/v1/spaces/{spaceId}/memories", body=MEMORY),
    Endpunkt(
        "GET",
        "/api/v1/spaces/{spaceId}/memories/{memoryId}",
        resource_absence="RESOURCE_NOT_FOUND",
    ),
    Endpunkt(
        "PATCH",
        "/api/v1/spaces/{spaceId}/memories/{memoryId}",
        body={"title": "Matrix Memory aktualisiert"},
        if_match=True,
        resource_absence="RESOURCE_NOT_FOUND",
    ),
    Endpunkt(
        "DELETE",
        "/api/v1/spaces/{spaceId}/memories/{memoryId}",
        if_match=True,
        resource_absence="RESOURCE_NOT_FOUND",
    ),
    Endpunkt(
        "PUT",
        "/api/v1/spaces/{spaceId}/memories/{memoryId}/attachments",
        body={"attachments": []},
        if_match=True,
        resource_absence="RESOURCE_NOT_FOUND",
    ),
    Endpunkt("GET", "/api/v1/spaces/{spaceId}/heart-moments"),
    Endpunkt("POST", "/api/v1/spaces/{spaceId}/heart-moments", body=HEART_MOMENT),
    Endpunkt(
        "GET",
        "/api/v1/spaces/{spaceId}/heart-moments/{heartMomentId}",
        resource_absence="RESOURCE_NOT_FOUND",
    ),
    Endpunkt(
        "PATCH",
        "/api/v1/spaces/{spaceId}/heart-moments/{heartMomentId}",
        body={"text": "Matrix HeartMoment aktualisiert"},
        if_match=True,
        resource_absence="RESOURCE_NOT_FOUND",
    ),
    Endpunkt(
        "PATCH",
        "/api/v1/spaces/{spaceId}/heart-moments/{heartMomentId}/visibility",
        body={"visibility": "PRIVATE"},
        if_match=True,
        resource_absence="RESOURCE_NOT_FOUND",
    ),
    Endpunkt(
        "DELETE",
        "/api/v1/spaces/{spaceId}/heart-moments/{heartMomentId}",
        if_match=True,
        resource_absence="RESOURCE_NOT_FOUND",
    ),
    Endpunkt("GET", "/api/v1/spaces/{spaceId}/milestones"),
    Endpunkt("POST", "/api/v1/spaces/{spaceId}/milestones", body=MILESTONE),
    Endpunkt(
        "GET",
        "/api/v1/spaces/{spaceId}/milestones/{milestoneId}",
        resource_absence="RESOURCE_NOT_FOUND",
    ),
    Endpunkt(
        "PATCH",
        "/api/v1/spaces/{spaceId}/milestones/{milestoneId}",
        body={"title": "Matrix Milestone aktualisiert"},
        if_match=True,
        resource_absence="RESOURCE_NOT_FOUND",
    ),
    Endpunkt(
        "DELETE",
        "/api/v1/spaces/{spaceId}/milestones/{milestoneId}",
        if_match=True,
        resource_absence="RESOURCE_NOT_FOUND",
    ),
    Endpunkt("POST", "/api/v1/spaces/{spaceId}/attachments", body=ATTACHMENT),
    Endpunkt(
        "GET",
        "/api/v1/spaces/{spaceId}/attachments/{attachmentId}",
        resource_absence="RESOURCE_NOT_FOUND",
    ),
    Endpunkt(
        "PUT",
        "/api/v1/spaces/{spaceId}/attachments/{attachmentId}/content",
        resource_absence="RESOURCE_NOT_FOUND",
    ),
    Endpunkt(
        "GET",
        "/api/v1/spaces/{spaceId}/attachments/{attachmentId}/content",
        resource_absence="RESOURCE_NOT_FOUND",
    ),
    Endpunkt(
        "POST",
        "/api/v1/spaces/{spaceId}/attachments/{attachmentId}/finalize",
        body={},
        resource_absence="RESOURCE_NOT_FOUND",
    ),
    Endpunkt(
        "POST",
        "/api/v1/spaces/{spaceId}/attachments/{attachmentId}/read-access",
        body={"parentType": "NONE"},
        resource_absence="RESOURCE_NOT_FOUND",
    ),
    Endpunkt(
        "DELETE",
        "/api/v1/spaces/{spaceId}/attachments/{attachmentId}",
        if_match=True,
        resource_absence="RESOURCE_NOT_FOUND",
    ),
)

NUR_ANGEMELDET: tuple[tuple[str, str], ...] = (
    ("GET", "/api/v1/auth/me"),
    ("POST", "/api/v1/auth/sign-out"),
    ("POST", "/api/v1/auth/password"),
    ("POST", "/api/v1/auth/email/verification/request"),
    # Verknuepfen setzt voraus, dass schon jemand angemeldet ist - genau
    # das unterscheidet es vom Anmelden ueber denselben Anbieter.
    ("POST", "/api/v1/auth/oidc/{connectionId}/link"),
    # Ein Passkey ist ein zusaetzlicher Zugang zu einem bestehenden Konto;
    # registriert wird er aus der Anmeldung heraus.
    ("POST", "/api/v1/auth/passkeys/registration/start"),
    ("POST", "/api/v1/auth/passkeys/registration/finish"),
)
"""Kontobezogen, aber nicht an einen Space gebunden. Anonym: 401."""

OEFFENTLICH: tuple[tuple[str, str], ...] = (
    ("GET", "/api/v1/health"),
    ("GET", "/api/v1/health/ready"),
    ("POST", "/api/v1/auth/register"),
    ("POST", "/api/v1/auth/sign-in"),
    ("POST", "/api/v1/auth/refresh"),
    ("POST", "/api/v1/invitations/accept"),
    # Die Wege zurueck ins Konto: sie beginnen ohne Sitzung, und ihr
    # Nachweis ist der Einmal-Token aus der Mail.
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
def welt(client, session: Session):  # type: ignore[no-untyped-def]
    """Ein Paar mit je einer echten Ressource pro Domaene, plus ein Fremder."""
    anna = make_account(session, "Anna")
    ben = make_account(session, "Ben")
    fremd = make_account(session, "Fremde Person")

    space = make_space(session, anna)
    make_space(session, fremd)
    session.flush()

    token_a = sign_in(session, anna)
    kopf = auth(token_a)
    basis = f"/api/v1/spaces/{space.id}"

    # Die Einladung entsteht, solange noch Platz ist: ein voller Paar-Space
    # stellt keine mehr aus. Ben kommt gleich danach dazu.
    einladung = client.post(f"{basis}/invitations", json={}, headers=kopf).json()

    relationship_service.add_member(session, space.id, ben)
    session.flush()
    praeferenz = client.post(
        f"{basis}/profile-preferences",
        json={**PRAEFERENZ, "accountId": str(anna.id), "visibility": "SELF_PROFILE"},
        headers=kopf,
    ).json()
    person = client.post(f"{basis}/related-persons", json=PERSON, headers=kopf).json()
    termin = client.post(f"{basis}/important-dates", json=TERMIN, headers=kopf).json()
    memory = client.post(f"{basis}/memories", json=MEMORY, headers=kopf).json()
    heart_moment = client.post(f"{basis}/heart-moments", json=HEART_MOMENT, headers=kopf).json()
    milestone = client.post(f"{basis}/milestones", json=MILESTONE, headers=kopf).json()
    attachment = client.post(f"{basis}/attachments", json=ATTACHMENT, headers=kopf).json()

    return {
        "client": client,
        "space": space,
        "kopf_owner": kopf,
        "kopf_fremd": auth(sign_in(session, fremd)),
        "ids": {
            "spaceId": str(space.id),
            "accountId": str(ben.id),
            "invitationId": einladung["id"],
            "preferenceId": praeferenz["id"],
            "personId": person["id"],
            "dateId": termin["id"],
            "memoryId": memory["id"],
            "heartMomentId": heart_moment["id"],
            "milestoneId": milestone["id"],
            "attachmentId": attachment["attachment"]["id"],
        },
    }


def _pfad(endpunkt: Endpunkt, ids: dict[str, str], **ersatz: str) -> str:
    werte = {**ids, **ersatz}
    return endpunkt.template.format(**werte)


def _sende(welt, endpunkt: Endpunkt, pfad: str, kopf: dict[str, str] | None):  # type: ignore[no-untyped-def]
    kopfzeilen = dict(kopf or {})
    if endpunkt.if_match:
        # Der Konfliktschutz ist Pflicht; ohne den Kopf pruefte dieser Test
        # nur noch, dass er fehlt.
        kopfzeilen["If-Match"] = '"1"'

    zusatz: dict[str, Any] = {}
    if endpunkt.body is not None:
        zusatz["json"] = endpunkt.body
    if endpunkt.query:
        zusatz["params"] = endpunkt.query
    return welt["client"].request(endpunkt.method, pfad, headers=kopfzeilen, **zusatz)


@pytest.mark.parametrize("endpunkt", SPACE_ENDPUNKTE, ids=str)
class TestJederSpaceEndpunkt:
    """Vier Fragen an jeden Endpunkt, der an einem Space haengt."""

    def test_anonym_bleibt_401(self, welt, endpunkt: Endpunkt) -> None:  # type: ignore[no-untyped-def]
        antwort = _sende(welt, endpunkt, _pfad(endpunkt, welt["ids"]), None)
        assert antwort.status_code == 401
        assert antwort.json()["code"] == "AUTHENTICATION_REQUIRED"

    def test_fremder_bekommt_404_und_nicht_403(self, welt, endpunkt: Endpunkt) -> None:  # type: ignore[no-untyped-def]
        """Ein 403 wuerde bestaetigen, dass es den Space gibt."""
        antwort = _sende(welt, endpunkt, _pfad(endpunkt, welt["ids"]), welt["kopf_fremd"])
        assert antwort.status_code == 404
        assert antwort.json()["code"] == SPACE_ABSENCE

    def test_fremder_space_und_erfundener_sind_ununterscheidbar(  # type: ignore[no-untyped-def]
        self, welt, endpunkt: Endpunkt
    ) -> None:
        echt = _sende(welt, endpunkt, _pfad(endpunkt, welt["ids"]), welt["kopf_fremd"])
        erfunden = _sende(
            welt,
            endpunkt,
            _pfad(endpunkt, welt["ids"], spaceId=str(uuid4())),
            welt["kopf_fremd"],
        )
        assert echt.status_code == erfunden.status_code == 404
        assert echt.json() == erfunden.json()

    def test_fehlgeformte_space_id_bleibt_dieselbe_404(self, welt, endpunkt: Endpunkt) -> None:  # type: ignore[no-untyped-def]
        antwort = _sende(
            welt,
            endpunkt,
            _pfad(endpunkt, welt["ids"], spaceId="' OR 1=1 --"),
            welt["kopf_owner"],
        )
        assert antwort.status_code == 404
        assert antwort.json()["code"] == SPACE_ABSENCE


DETAIL_ENDPUNKTE = tuple(e for e in SPACE_ENDPUNKTE if e.resource_absence is not None)


@pytest.mark.parametrize("endpunkt", DETAIL_ENDPUNKTE, ids=str)
class TestJedeRessourcenId:
    """Im eigenen Space entscheidet die Ressourcen-ID - und verraet nichts."""

    def test_unbekannte_ressource_bleibt_404(self, welt, endpunkt: Endpunkt) -> None:  # type: ignore[no-untyped-def]
        pfad = endpunkt.template.format(
            **{**welt["ids"], **dict.fromkeys(_ressourcen_platzhalter(endpunkt), str(uuid4()))}
        )
        antwort = _sende(welt, endpunkt, pfad, welt["kopf_owner"])
        assert antwort.status_code == 404
        assert antwort.json()["code"] == endpunkt.resource_absence

    def test_fehlgeformte_ressourcen_id_bleibt_dieselbe_404(self, welt, endpunkt: Endpunkt) -> None:  # type: ignore[no-untyped-def]
        """Wohlgeformtheit darf keine Existenzauskunft sein."""
        unbekannt = endpunkt.template.format(
            **{**welt["ids"], **dict.fromkeys(_ressourcen_platzhalter(endpunkt), str(uuid4()))}
        )
        unfug = endpunkt.template.format(
            **{**welt["ids"], **dict.fromkeys(_ressourcen_platzhalter(endpunkt), "nicht-echt")}
        )
        erste = _sende(welt, endpunkt, unbekannt, welt["kopf_owner"])
        zweite = _sende(welt, endpunkt, unfug, welt["kopf_owner"])
        assert erste.status_code == zweite.status_code == 404
        assert erste.json() == zweite.json()


def _ressourcen_platzhalter(endpunkt: Endpunkt) -> tuple[str, ...]:
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
        )
        if "{" + name + "}" in endpunkt.template
    )


SCHREIBENDE_ENDPUNKTE = tuple(e for e in SPACE_ENDPUNKTE if e.if_match)


@pytest.mark.parametrize("endpunkt", SCHREIBENDE_ENDPUNKTE, ids=str)
def test_ohne_if_match_wird_nicht_geschrieben(welt, endpunkt: Endpunkt) -> None:  # type: ignore[no-untyped-def]
    """Ein fehlender Kopf ist der stille Weg, den Konfliktschutz abzuschalten."""
    pfad = _pfad(endpunkt, welt["ids"])
    zusatz: dict[str, Any] = {"json": endpunkt.body} if endpunkt.body is not None else {}
    if endpunkt.query:
        zusatz["params"] = endpunkt.query
    antwort = welt["client"].request(endpunkt.method, pfad, headers=welt["kopf_owner"], **zusatz)
    assert antwort.status_code == 422

    # Und die Ressource steht unveraendert da - auch die geloeschte nicht.
    if endpunkt.method == "DELETE":
        nachher = welt["client"].get(pfad, headers=welt["kopf_owner"])
        assert nachher.status_code == 200


def test_der_vertrag_ist_vollstaendig_abgedeckt() -> None:
    """Eine neue Operation ohne Eintrag in dieser Datei macht die Suite rot.

    Das ist der eigentliche Zweck der Matrix. Eine Regel, die man an jedem
    neuen Endpunkt von Hand mitschreiben muss, wird irgendwann vergessen -
    und ein vergessener Mandantenschutz faellt im Betrieb niemandem auf.
    """
    schema = create_app().openapi()
    vertrag = {
        (methode.upper(), pfad)
        for pfad, operationen in schema["paths"].items()
        for methode in operationen
    }
    abgedeckt = (
        {(e.method, e.template) for e in SPACE_ENDPUNKTE} | set(NUR_ANGEMELDET) | set(OEFFENTLICH)
    )
    assert vertrag == abgedeckt


@pytest.mark.parametrize(("methode", "pfad"), NUR_ANGEMELDET, ids=str)
def test_kontobezogene_endpunkte_bleiben_anonym_verschlossen(welt, methode: str, pfad: str) -> None:  # type: ignore[no-untyped-def]
    antwort = welt["client"].request(methode, pfad, json={})
    assert antwort.status_code == 401
    assert antwort.json()["code"] == "AUTHENTICATION_REQUIRED"


def test_oeffentliche_endpunkte_verlangen_keinen_token(welt) -> None:  # type: ignore[no-untyped-def]
    """Die Gegenprobe: sie sind der Weg zu einem Token und bleiben offen."""
    for pfad in ("/api/v1/health", "/api/v1/health/ready"):
        assert welt["client"].get(pfad).status_code == 200
