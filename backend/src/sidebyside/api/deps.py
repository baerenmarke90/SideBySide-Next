"""Abhaengigkeiten der API-Schicht.

Hier entsteht der Tenant Context: aus einem Bearer Token wird ein Account,
aus Account und Pfad-ID wird eine geprüfte Mitgliedschaft. Routen bekommen
nur das fertige Ergebnis - sie sollen die Pruefung nicht wiederholen und
schon gar nicht vergessen koennen.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Path, Request
from sqlalchemy.orm import Session

from sidebyside.auth.sessions import resolve
from sidebyside.authorization import AuthorizationContext
from sidebyside.core.errors import ErrorCode, NotFoundError, UnauthenticatedError
from sidebyside.core.ids import parse_id
from sidebyside.db.session import get_session
from sidebyside.identity.models import Account, DeviceSession
from sidebyside.relationship.models import Membership
from sidebyside.relationship.service import SpaceErrorCode, require_membership

DbSession = Annotated[Session, Depends(get_session)]


def _bearer_token(request: Request) -> str:
    """Den Token aus dem Authorization-Kopf ziehen.

    Native Clients weisen sich ausschliesslich so aus - kein
    Sitzungs-Cookie. Ein Cookie waere im Browser automatisch mitgesendet
    worden und haette CSRF-Schutz noetig gemacht.
    """
    kopf = request.headers.get("Authorization", "")
    schema, _, wert = kopf.partition(" ")
    if schema.lower() != "bearer" or not wert.strip():
        raise UnauthenticatedError("Authentication required.", ErrorCode.AUTHENTICATION_REQUIRED)
    return wert.strip()


def current_session(request: Request, session: DbSession) -> DeviceSession:
    """Die Geraetesitzung hinter dem Token.

    Fuer Abmelden und Sitzungsverwaltung - alles andere braucht nur den
    Account.
    """
    return resolve(session, _bearer_token(request))[0]


def current_account(request: Request, session: DbSession) -> Account:
    return resolve(session, _bearer_token(request))[1]


CurrentAccount = Annotated[Account, Depends(current_account)]
CurrentSession = Annotated[DeviceSession, Depends(current_session)]


@dataclass(frozen=True)
class TenantContext:
    """Ein geprueftes Paar aus Account und Space.

    Wer diesen Kontext in der Hand hat, hat die Mitgliedschaftspruefung
    hinter sich. Alles, was eine Route danach laedt, muss zusaetzlich gegen
    `space_id` eingeschraenkt werden - der Kontext beweist die
    Zugehoerigkeit zum Space, nicht die einer einzelnen Ressource.
    """

    account: Account
    space_id: UUID
    membership: Membership


def tenant_context(
    session: DbSession,
    account: CurrentAccount,
    space_id: Annotated[str, Path(alias="spaceId")],
) -> TenantContext:
    """Zugriff auf einen Space pruefen.

    Eine fehlgeformte ID ergibt 404 und nicht 422. Sonst liesse sich an der
    Antwort ablesen, ob eine wohlgeformte ID existiert - und aus dem
    Unterschied eine Existenzauskunft bauen.
    """
    gepruefte_id = parse_id(space_id)
    if gepruefte_id is None:
        raise NotFoundError("Space not found.", SpaceErrorCode.NOT_FOUND)

    mitgliedschaft = require_membership(session, account, gepruefte_id)
    return TenantContext(account=account, space_id=gepruefte_id, membership=mitgliedschaft)


Tenant = Annotated[TenantContext, Depends(tenant_context)]


def authorization_context(tenant: Tenant) -> AuthorizationContext:
    """Der Kontext fuer Owner- und Privacy-Fragen.

    Entsteht ausschliesslich aus dem bereits geprueften Tenant Context. Es
    gibt keinen zweiten Weg, ihn zu bauen - damit kann keine Route eine
    Sichtbarkeitsentscheidung auf einen Account oder Space stuetzen, der
    nicht durch die Mitgliedschaftspruefung gegangen ist.
    """
    return AuthorizationContext(account_id=tenant.account.id, space_id=tenant.space_id)


Authorization = Annotated[AuthorizationContext, Depends(authorization_context)]
