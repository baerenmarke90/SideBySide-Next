"""Server-authoritative authentication capability policy.

Enforces deployment-mode authentication restrictions on the server side so that
deployment boundaries (Cloud/Managed vs Self-Hosted) are cryptographic/authoritative
boundaries rather than merely UI conventions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from fastapi import Depends

from sidebyside import config
from sidebyside.api.schema import ApiModel
from sidebyside.config import Deployment, MailTransport
from sidebyside.core.errors import AuthMethodDisabledError

if TYPE_CHECKING:
    from sidebyside.config import Settings


class AuthCapabilities(ApiModel):
    """Authoritative authentication capabilities for this instance.

    Reused across the backend auth router, service layers, and capability
    projections to clients.
    """

    local_password: bool
    passkey: bool
    magic_link: bool
    oidc: bool

    def ensure_local_password_allowed(self) -> None:
        """Reject local password operations if disabled by deployment policy."""
        if not self.local_password:
            raise AuthMethodDisabledError(
                "Local password authentication is not supported on this deployment."
            )

    def ensure_passkey_allowed(self) -> None:
        """Reject passkey ceremonies if disabled by deployment policy."""
        if not self.passkey:
            raise AuthMethodDisabledError(
                "Passkey authentication is not supported on this deployment."
            )

    def ensure_magic_link_allowed(self) -> None:
        """Reject magic link operations if disabled by deployment policy."""
        if not self.magic_link:
            raise AuthMethodDisabledError(
                "Magic link authentication is not supported on this deployment."
            )

    def ensure_oidc_allowed(self) -> None:
        """Reject OIDC authentication if disabled by deployment policy."""
        if not self.oidc:
            raise AuthMethodDisabledError(
                "OIDC authentication is not supported on this deployment."
            )


def resolve_auth_capabilities(settings: Settings | None = None) -> AuthCapabilities:
    """Derive authentication capabilities from deployment mode and configuration.

    Rules:
    - Local password: supported on Self-Hosted; disabled on Cloud.
    - Passkeys: supported in both deployment modes.
    - Magic Link: supported when mail transport is configured (not NONE).
    - OIDC: supported when one or more OIDC connections are configured.
    """
    if settings is None:
        settings = config.get_settings()

    local_password = settings.deployment is Deployment.SELF_HOSTED
    passkey = True
    magic_link = settings.mail_transport is not MailTransport.NONE
    oidc = len(settings.oidc_connections) > 0

    return AuthCapabilities(
        local_password=local_password,
        passkey=passkey,
        magic_link=magic_link,
        oidc=oidc,
    )


def get_auth_capabilities() -> AuthCapabilities:
    """FastAPI dependency returning current instance auth capabilities."""
    return resolve_auth_capabilities(config.get_settings())


AuthPolicy = Annotated[AuthCapabilities, Depends(get_auth_capabilities)]
