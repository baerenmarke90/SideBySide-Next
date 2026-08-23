"""Der ASGI-Einstiegspunkt."""

from __future__ import annotations

import logging

from fastapi import FastAPI

from sidebyside.api.errors import register_error_handlers
from sidebyside.api.v1 import router as v1_router
from sidebyside.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="SideBySide Next",
        version="0.1.0",
        description="Application Core. OpenAPI ist der verbindliche Vertrag.",
        # In Produktion keine offene Schema-Auskunft: sie ist eine
        # Landkarte der Angriffsfläche.
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None,
        openapi_url=None if settings.is_production else "/openapi.json",
    )

    register_error_handlers(app)
    app.include_router(v1_router, prefix="/api/v1")

    return app


app = create_app()
