"""Transport boundaries for production HTTP requests."""

from __future__ import annotations

from ipaddress import ip_address

from starlette.types import ASGIApp, Receive, Scope, Send

from sidebyside.api.errors import problem


def _peer_is_loopback(scope: Scope) -> bool:
    """Return whether the ASGI client address is an actual loopback IP.

    Request authority/Host is caller-controlled and therefore cannot establish
    network locality. Uvicorn supplies ``scope['client']`` from the connection
    peer and only normalizes it from forwarded headers for explicitly trusted
    proxy addresses. This middleware deliberately parses neither Host nor
    forwarded headers itself.
    """
    client = scope.get("client")
    if not client:
        return False

    try:
        return ip_address(client[0]).is_loopback
    except ValueError:
        # A non-IP or otherwise malformed peer value is never evidence that the
        # connection is local. Fail closed to the HTTPS requirement.
        return False


class RequireHttpsForExternalHostsMiddleware:
    """Allow cleartext HTTP only for connections that are actually loopback.

    A TLS reverse proxy sets the scheme through forwarded headers. Uvicorn
    accepts those headers only from explicitly trusted proxy addresses, so a
    client cannot spoof HTTPS by supplying its own forwarded header.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if (
            scope["type"] == "http"
            and scope.get("scheme") != "https"
            and not _peer_is_loopback(scope)
        ):
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
