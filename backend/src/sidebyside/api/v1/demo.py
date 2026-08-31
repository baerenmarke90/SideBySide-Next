"""Public entry boundary for an explicitly configured demo deployment.

The route is intentionally excluded from the product OpenAPI contract. It is a
deployment facility for the isolated public demo instance, not a supported
client authentication method for normal SideBySide installations.
"""

from __future__ import annotations

from datetime import timedelta
from enum import StrEnum

from fastapi import APIRouter, Request, Response
from sqlalchemy import select

from sidebyside.api.deps import DbSession
from sidebyside.api.errors import problem_responses
from sidebyside.api.schema import ApiModel
from sidebyside.auth import action_tokens, rate_limit
from sidebyside.config import get_settings
from sidebyside.core.errors import NotFoundError
from sidebyside.demo.service import ALEX_EMAIL, ALEX_NAME, LEA_EMAIL, LEA_NAME
from sidebyside.identity import service as identity_service
from sidebyside.identity.models import AccountEmail

router = APIRouter(tags=["demo"])

DEMO_ENTRY_ACTION = "demo_entry"
DEMO_ENTRY_LIMIT = rate_limit.Limit(attempts=30, window=timedelta(minutes=15))


class DemoPersona(StrEnum):
    LEA = "LEA"
    ALEX = "ALEX"


class DemoEntryRequest(ApiModel):
    persona: DemoPersona


class DemoEntryView(ApiModel):
    token: str


def _demo_identity(persona: DemoPersona) -> tuple[str, str]:
    if persona is DemoPersona.LEA:
        return LEA_EMAIL, LEA_NAME
    return ALEX_EMAIL, ALEX_NAME


@router.post(
    "/demo/entry",
    response_model=DemoEntryView,
    responses=problem_responses(404, 429),
    include_in_schema=False,
)
def create_demo_entry(
    body: DemoEntryRequest,
    request: Request,
    response: Response,
    session: DbSession,
) -> DemoEntryView:
    """Issue a one-time sign-in proof for Lea or Alex on the demo instance only."""
    settings = get_settings()
    if not settings.demo_mode:
        raise NotFoundError("Demo entry is not available.", "DEMO_MODE_DISABLED")

    client = request.client.host if request.client is not None else "unknown"
    rate_limit.check(
        session,
        DEMO_ENTRY_ACTION,
        f"{client}:{body.persona.value}",
        DEMO_ENTRY_LIMIT,
    )

    email, expected_name = _demo_identity(body.persona)
    account = identity_service.find_by_email(session, email)
    if account is None or not account.is_active or account.display_name != expected_name:
        raise NotFoundError("Canonical demo identity is not available.", "DEMO_IDENTITY_MISSING")

    email_record = session.execute(
        select(AccountEmail).where(
            AccountEmail.account_id == account.id,
            AccountEmail.email == email,
            AccountEmail.is_primary.is_(True),
        )
    ).scalar_one_or_none()
    if email_record is None:
        raise NotFoundError("Canonical demo identity is not available.", "DEMO_IDENTITY_MISSING")

    _, issued = action_tokens.issue_magic_link(session, email_record.id)
    response.headers["Cache-Control"] = "no-store"
    return DemoEntryView(token=issued.token)
