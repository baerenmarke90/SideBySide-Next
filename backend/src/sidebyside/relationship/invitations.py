"""Einladungen.

    Account A legt einen Space an
    → Einladung erzeugen
    → einmaliger Token
    → Partner oeffnet den Link
    → Anmeldung oder Registrierung
    → Annehmen
    → Mitgliedschaft

Der Token wird nur einmal ausgegeben und nur gehasht abgelegt.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from sidebyside.auth.tokens import generate_token, hash_token
from sidebyside.core.clock import now
from sidebyside.core.errors import ConflictError, NotFoundError, ValidationError
from sidebyside.identity.models import Account
from sidebyside.relationship import service
from sidebyside.relationship.models import (
    MAX_ACTIVE_PARTNERS,
    Invitation,
    Membership,
)

INVITATION_LIFETIME = timedelta(days=14)
INVITATION_TOKEN_BYTES = 32


class InvitationErrorCode:
    NOT_FOUND = "INVITATION_NOT_FOUND"
    INVALID = "INVITATION_INVALID"
    SPACE_FULL = "SPACE_FULL"
    ALREADY_MEMBER = "ACCOUNT_ALREADY_MEMBER"
    SELF_INVITE = "CANNOT_ACCEPT_OWN_INVITATION"


@dataclass(frozen=True)
class IssuedInvitation:
    invitation: Invitation
    token: str
    """Der Klartext. Existiert nur hier und in der Antwort an den Ersteller."""


def create(session: Session, space_id: UUID, created_by: Account) -> IssuedInvitation:
    """Eine Einladung erzeugen.

    Ist der Space schon voll, entsteht gar keine Einladung. Andernfalls
    verschickte jemand einen Link, der beim Oeffnen nur enttaeuscht.
    """
    if len(service.active_memberships(session, space_id)) >= MAX_ACTIVE_PARTNERS:
        raise ConflictError("This space already has two partners.", InvitationErrorCode.SPACE_FULL)

    token = generate_token(INVITATION_TOKEN_BYTES)
    einladung = Invitation(
        space_id=space_id,
        created_by=created_by.id,
        token_hash=hash_token(token),
        expires_at=now() + INVITATION_LIFETIME,
    )
    session.add(einladung)
    session.flush()
    return IssuedInvitation(invitation=einladung, token=token)


def list_open(session: Session, space_id: UUID) -> Sequence[Invitation]:
    jetzt = now()
    alle = (
        session.execute(
            select(Invitation)
            .where(Invitation.space_id == space_id)
            .order_by(Invitation.created_at.desc())
        )
        .scalars()
        .all()
    )
    return [e for e in alle if e.is_open(jetzt)]


def revoke(session: Session, space_id: UUID, invitation_id: UUID) -> Invitation:
    """Eine Einladung zurueckziehen.

    Die Suche ist auf den Space eingeschraenkt: eine Einladungs-ID allein
    darf keinen Zugriff geben, auch nicht zum Widerrufen.
    """
    einladung = session.execute(
        select(Invitation).where(
            Invitation.id == invitation_id,
            Invitation.space_id == space_id,
        )
    ).scalar_one_or_none()

    if einladung is None:
        raise NotFoundError("Invitation not found.", InvitationErrorCode.NOT_FOUND)

    if einladung.revoked_at is None and einladung.accepted_at is None:
        einladung.revoked_at = now()
        session.flush()
    return einladung


def _invalid() -> ValidationError:
    return ValidationError("This invitation is no longer valid.", InvitationErrorCode.INVALID)


def _open_for_update(session: Session, token_hash: str) -> Invitation:
    """Eine noch offene Einladung unter Zeilensperre laden.

    Auch interne Aufrufer arbeiten nur mit dem Hash. Damit muss ein
    Klartext-Token nicht durch weitere Schichten gereicht oder gespeichert
    werden.
    """
    if not token_hash:
        raise _invalid()

    einladung = session.execute(
        select(Invitation).where(Invitation.token_hash == token_hash).with_for_update()
    ).scalar_one_or_none()

    if einladung is None or not einladung.is_open(now()):
        raise _invalid()
    return einladung


def _accept_open(session: Session, einladung: Invitation, account: Account) -> Membership:
    """Eine bereits gesperrte, offene Einladung fachlich annehmen."""
    if not einladung.is_open(now()):
        raise _invalid()

    # Der Ersteller kann seine eigene Einladung nicht annehmen. Sonst
    # verbraucht ein Fehlgriff die Einladung, und der Partner steht vor
    # einem toten Link.
    if einladung.created_by == account.id:
        raise ValidationError(
            "You cannot accept your own invitation.", InvitationErrorCode.SELF_INVITE
        )

    # add_member prueft Obergrenze und bestehende Mitgliedschaft. Schlaegt es
    # fehl, bleibt die Einladung offen - der Fehler liegt nicht an ihr.
    mitgliedschaft = service.add_member(session, einladung.space_id, account)

    einladung.accepted_at = now()
    einladung.accepted_by = account.id
    session.flush()
    return mitgliedschaft


def accept(session: Session, token: str, account: Account) -> Membership:
    """Eine Einladung annehmen.

    Jeder Fehlschlag - unbekannt, abgelaufen, widerrufen, bereits benutzt -
    ergibt dieselbe Meldung. Ein Unterschied waere eine Auskunft darueber,
    welche Token existieren.

    Die Zeile wird gesperrt geladen. Nehmen zwei Versuche gleichzeitig
    dieselbe Einladung an, wartet der zweite auf den ersten und sieht dann
    `accepted_at` gesetzt - statt dass beide durchgehen.
    """
    if not token:
        raise _invalid()
    einladung = _open_for_update(session, hash_token(token))
    return _accept_open(session, einladung, account)


def accept_with_new_account(
    session: Session,
    token_hash: str,
    account_factory: Callable[[], Account],
) -> tuple[Account, Membership]:
    """Eine Einladung annehmen und das neue Konto erst unter der Sperre anlegen.

    Dieser Weg ist fuer Onboarding-Verfahren gedacht, bei denen das Konto
    noch nicht existiert. Entscheidend ist die Reihenfolge: zuerst wird die
    Einladung gesperrt und erneut auf Gueltigkeit geprueft, erst danach darf
    der Aufrufer das Konto erzeugen. Zwei parallele Rueckwege mit derselben
    Einladung koennen so niemals zwei Konten anlegen.
    """
    einladung = _open_for_update(session, token_hash)
    account = account_factory()
    return account, _accept_open(session, einladung, account)
