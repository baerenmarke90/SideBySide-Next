"""Transportgrenzen fuer produktive HTTP-Anfragen."""

from __future__ import annotations

from starlette.datastructures import URL
from starlette.types import ASGIApp, Receive, Scope, Send

from sidebyside.api.errors import problem

_LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}


class RequireHttpsForExternalHostsMiddleware:
    """Klartext nur fuer den lokalen Loopback-Zugriff erlauben.

    Ein TLS-Reverse-Proxy setzt das Scheme ueber Forwarded Headers. Uvicorn
    uebernimmt diese Header nur von explizit vertrauten Proxy-Adressen; ein
    Client kann HTTPS daher nicht mit einem eigenen Header vortaeuschen.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope.get("scheme") != "https":
            host = (URL(scope=scope).hostname or "").lower().rstrip(".")
            if host not in _LOOPBACK_HOSTS:
                response = problem(
                    400,
                    "bad_request",
                    "Bad request",
                    "HTTPS is required for non-loopback access.",
                    "HTTPS_REQUIRED",
                )
                await response(scope, receive, send)
                return

        await self.app(scope, receive, send)
