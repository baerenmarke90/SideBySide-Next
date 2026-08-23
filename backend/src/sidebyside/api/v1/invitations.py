"""Einladungen in einen Space."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Path, status

from sidebyside.api.deps import CurrentAccount, DbSession, Tenant
from sidebyside.api.schema import ApiModel
from sidebyside.core.errors import NotFoundError
from sidebyside.core.ids import parse_id
from sidebyside.relationship import invitations
from sidebyside.relationship.invitations import InvitationErrorCode

router = APIRouter(tags=["invitations"])


class InvitationView(ApiModel):
    id: UUID
    expires_at: datetime
    created_at: datetime


class IssuedInvitationView(InvitationView):
    token: str
    """Wird genau einmal ausgegeben. Danach existiert nur noch der Hash."""


class AcceptRequest(ApiModel):
    token: str


class MembershipView(ApiModel):
    space_id: UUID
    role: str
    status: str


@router.post(
    "/spaces/{spaceId}/invitations",
    response_model=IssuedInvitationView,
    status_code=status.HTTP_201_CREATED,
)
def create_invitation(tenant: Tenant, session: DbSession) -> IssuedInvitationView:
    ergebnis = invitations.create(session, tenant.space_id, tenant.account)
    return IssuedInvitationView(
        id=ergebnis.invitation.id,
        expires_at=ergebnis.invitation.expires_at,
        created_at=ergebnis.invitation.created_at,
        token=ergebnis.token,
    )


@router.get("/spaces/{spaceId}/invitations", response_model=list[InvitationView])
def list_invitations(tenant: Tenant, session: DbSession) -> list[InvitationView]:
    """Die offenen Einladungen. Ohne Token - der ist einmalig gewesen."""
    return [
        InvitationView(id=e.id, expires_at=e.expires_at, created_at=e.created_at)
        for e in invitations.list_open(session, tenant.space_id)
    ]


@router.delete(
    "/spaces/{spaceId}/invitations/{invitationId}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def revoke_invitation(
    tenant: Tenant,
    session: DbSession,
    invitation_id_raw: Annotated[str, Path(alias="invitationId")],
) -> None:
    einladung_id = parse_id(invitation_id_raw)
    if einladung_id is None:
        raise NotFoundError("Invitation not found.", InvitationErrorCode.NOT_FOUND)
    invitations.revoke(session, tenant.space_id, einladung_id)


@router.post(
    "/invitations/accept",
    response_model=MembershipView,
    status_code=status.HTTP_201_CREATED,
)
def accept_invitation(
    body: AcceptRequest, account: CurrentAccount, session: DbSession
) -> MembershipView:
    """Eine Einladung annehmen.

    Ausserhalb von /spaces/..., weil der Aufrufer den Space noch nicht
    kennt - der Token bestimmt ihn.
    """
    mitgliedschaft = invitations.accept(session, body.token, account)
    return MembershipView(
        space_id=mitgliedschaft.space_id,
        role=mitgliedschaft.role,
        status=mitgliedschaft.status,
    )
