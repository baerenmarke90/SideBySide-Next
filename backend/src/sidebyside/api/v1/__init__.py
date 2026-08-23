"""API-Version 1.

Die Version steht im Pfad. Ein veröffentlichter Vertrag wird innerhalb
seiner Version nicht brechend geändert; brechende Änderungen bekommen eine
neue Version, damit ältere App-Installationen weiterlaufen.
"""

from __future__ import annotations

from fastapi import APIRouter

from sidebyside.api.v1 import health, spaces

router = APIRouter()
router.include_router(health.router)
router.include_router(spaces.router)
