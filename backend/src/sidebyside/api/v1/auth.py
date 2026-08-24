"""Anmeldung.

Alle Antworten sind bewusst wortkarg. Ein Anmelde-Endpunkt, der freundlich
erklaert, welcher Teil nicht gestimmt hat, erklaert das auch dem, der
Konten aufzaehlen will.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, status

from sidebyside.api.deps import CurrentAccount, CurrentSession, DbSession
from sidebyside.api.errors import problem_responses
from sidebyside.api.schema import ApiModel
from sidebyside.auth import local, sessions
from sidebyside.auth.local import SignedIn
from sidebyside.config import get_settings

router = APIRouter(tags=["auth"])

MAX_DEVICE_NAME = 120


class RegisterRequest(ApiModel):
    display_name: str
    email: str
    password: str
    invitation_token: str | None = None
    bootstrap_token: str | None = None
    device_name: str = ""
    platform: str = ""


class SignInRequest(ApiModel):
    email: str
    password: str
    device_name: str = ""
    platform: str = ""


class RefreshRequest(ApiModel):
    refresh_token: str


class ChangePasswordRequest(ApiModel):
    current_password: str
    new_password: str


class AccountView(ApiModel):
    id: UUID
    display_name: str


class TokenView(ApiModel):
    access_token: str
    refresh_token: str
    access_expires_at: datetime
    refresh_expires_at: datetime


class SessionView(ApiModel):
    account: AccountView
    tokens: TokenView


def _view(result: SignedIn) -> SessionView:
    return SessionView(
        account=AccountView(id=result.account.id, display_name=result.account.display_name),
        tokens=TokenView(
            access_token=result.tokens.access_token,
            refresh_token=result.tokens.refresh_token,
            access_expires_at=result.tokens.access_expires_at,
            refresh_expires_at=result.tokens.refresh_expires_at,
        ),
    )


@router.post(
    "/auth/register",
    response_model=SessionView,
    status_code=status.HTTP_201_CREATED,
    responses=problem_responses(403, 409, 422, 429),
)
def register(body: RegisterRequest, session: DbSession) -> SessionView:
    """Einen Account anlegen.

    Der erste Account braucht den einmaligen Bootstrap-Nachweis. Danach
    braucht jede Registrierung eine gueltige Einladung.
    """
    configured = get_settings().bootstrap_token
    return _view(
        local.register(
            session,
            display_name=body.display_name,
            email=body.email,
            password=body.password,
            invitation_token=body.invitation_token,
            bootstrap_token=body.bootstrap_token,
            configured_bootstrap_token=(
                configured.get_secret_value() if configured is not None else None
            ),
            device_name=body.device_name[:MAX_DEVICE_NAME],
            platform=body.platform,
        )
    )


@router.post(
    "/auth/sign-in",
    response_model=SessionView,
    responses=problem_responses(401, 422, 429),
)
def sign_in(body: SignInRequest, session: DbSession) -> SessionView:
    return _view(
        local.sign_in(
            session,
            email=body.email,
            password=body.password,
            device_name=body.device_name[:MAX_DEVICE_NAME],
            platform=body.platform,
        )
    )


@router.post(
    "/auth/refresh",
    response_model=TokenView,
    responses=problem_responses(401, 422, 429),
)
def refresh(body: RefreshRequest, session: DbSession) -> TokenView:
    tokens = sessions.refresh_session(session, body.refresh_token)
    return TokenView(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        access_expires_at=tokens.access_expires_at,
        refresh_expires_at=tokens.refresh_expires_at,
    )


@router.post(
    "/auth/sign-out",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=problem_responses(401),
)
def sign_out(device_session: CurrentSession) -> None:
    """Diese Sitzung beenden. Andere Geraete bleiben angemeldet."""
    sessions.revoke(device_session)


@router.post(
    "/auth/password",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=problem_responses(401, 422),
)
def change_password(
    body: ChangePasswordRequest, account: CurrentAccount, session: DbSession
) -> None:
    """Passwort aendern und alle Sitzungen beenden.

    Auch die eigene: wer sein Passwort aendert, vermutet oft einen fremden
    Zugriff - dann darf kein Geraet angemeldet bleiben.
    """
    local.change_password(session, account, current=body.current_password, new=body.new_password)


@router.get(
    "/auth/me",
    response_model=AccountView,
    responses=problem_responses(401),
)
def me(account: CurrentAccount) -> AccountView:
    return AccountView(id=account.id, display_name=account.display_name)
