"""Der ASGI-Einstiegspunkt."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from starlette.middleware.trustedhost import TrustedHostMiddleware

from sidebyside.api.errors import register_error_handlers
from sidebyside.api.openapi import SideBySideFastAPI
from sidebyside.api.transport import RequireHttpsForExternalHostsMiddleware
from sidebyside.api.v1 import router as v1_router
from sidebyside.config import Environment, Settings, get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


_log = logging.getLogger(__name__)


def _betriebsart_melden(settings: Settings) -> None:
    """Sagen, in welchem Betrieb diese Instanz laeuft.

    Der mitgelieferte Compose-Stack startet nach ADR 0002 absichtlich als
    lokaler Testbetrieb. Damit daraus kein unbemerkter Dauerzustand wird,
    steht der Unterschied in der ersten Zeile der Logs statt nur in einer
    Datei, die beim Aufsetzen einmal gelesen wird.
    """
    if settings.is_production:
        _log.info(
            "Produktionsbetrieb: HTTPS-Zwang, Host-Pruefung und geschlossene Schema-Auskunft aktiv."
        )
        return
    if settings.environment is Environment.TEST:
        # Die Testsuite baut die App je Test neu; eine Warnung pro Aufbau
        # waere Rauschen und keine Information.
        return
    _log.warning(
        "Lokaler Testbetrieb (SBS_ENVIRONMENT=%s). HTTPS-Zwang und Host-Pruefung "
        "sind aus, /docs ist offen und der Cursor-Signing-Key ist ein lokaler "
        "Rueckfallwert. Fuer echten Betrieb SBS_ENVIRONMENT=production setzen; "
        "die Checkliste steht in docs/SELF-HOSTING.md.",
        settings.environment.value,
    )


def create_app() -> FastAPI:
    settings = get_settings()
    _betriebsart_melden(settings)

    app = SideBySideFastAPI(
        title="SideBySide Next",
        version="0.1.0",
        description="Application Core. OpenAPI ist der verbindliche Vertrag.",
        # In Produktion keine offene Schema-Auskunft: sie ist eine
        # Landkarte der Angriffsfläche.
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None,
        openapi_url=None if settings.is_production else "/openapi.json",
    )

    if settings.is_production:
        # Die HTTPS-Pruefung verlaesst sich nur auf das von Uvicorn bereits
        # bereinigte Scheme. Uvicorn vertraut Forwarded Headers ausschliesslich
        # von den im Deployment explizit gesetzten Proxy-Adressen.
        app.add_middleware(RequireHttpsForExternalHostsMiddleware)
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)

    register_error_handlers(app)
    app.include_router(v1_router, prefix="/api/v1")

    return app


app = create_app()
