"""Ein Testendpunkt auf der Autorisierungsgrundlage.

Die Isolation muss ueber HTTP geprueft werden. Ein Direktaufruf des Guards
ueberspringt genau den Weg, auf dem eine Pruefung vergessen werden kann -
Pfadparameter, Abhaengigkeiten, Fehlerbehandlung, Serialisierung.

Der Router wird nicht in die produktive Anwendung eingehaengt, sondern in
eine eigene App-Instanz. Der versionierte OpenAPI-Vertrag bleibt dadurch
unveraendert; die Sonde ist eine Testvorrichtung und kein Angebot an
Clients.

Die Routen sind absichtlich so knapp geschrieben, wie eine spaetere
Domaene es auch sein soll. Steht hier mehr als ein Guard-Aufruf, muesste
eine echte Domaene ihn ebenfalls nachbauen.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, FastAPI, Path, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from sidebyside.api.deps import Authorization, DbSession
from sidebyside.api.schema import ApiModel
from sidebyside.authorization import readable, require_readable, require_writable
from sidebyside.db.session import get_session
from sidebyside.main import create_app
from tests.support.privacy_probe import PrivacyProbe

router = APIRouter(tags=["privacy-probes"])

ProbeId = Annotated[str, Path(alias="probeId")]


class ProbeView(ApiModel):
    id: UUID
    owner_id: UUID
    privacy_class: str
    label: str


class ProbeUpdate(ApiModel):
    label: str


class ProbeCount(ApiModel):
    total: int


@router.get("/spaces/{spaceId}/privacy-probes", response_model=list[ProbeView])
def list_probes(authorization: Authorization, session: DbSession) -> list[ProbeView]:
    sichtbare = (
        session.execute(readable(PrivacyProbe, authorization).order_by(PrivacyProbe.created_at))
        .scalars()
        .all()
    )
    return [ProbeView.model_validate(sonde) for sonde in sichtbare]


@router.get("/spaces/{spaceId}/privacy-probes/count", response_model=ProbeCount)
def count_probes(authorization: Authorization, session: DbSession) -> ProbeCount:
    """Zaehlen auf demselben Statement wie Lesen.

    Eine Trefferzahl ist selbst schon eine Auskunft: wer mitzaehlt, was er
    nicht sehen darf, erfaehrt, dass es existiert.
    """
    gezaehlt = session.execute(
        select(func.count()).select_from(readable(PrivacyProbe, authorization).subquery())
    ).scalar_one()
    return ProbeCount(total=gezaehlt)


@router.get("/spaces/{spaceId}/privacy-probes/{probeId}", response_model=ProbeView)
def get_probe(authorization: Authorization, session: DbSession, probe_id: ProbeId) -> ProbeView:
    return ProbeView.model_validate(
        require_readable(session, PrivacyProbe, authorization, probe_id)
    )


@router.patch("/spaces/{spaceId}/privacy-probes/{probeId}", response_model=ProbeView)
def update_probe(
    authorization: Authorization,
    session: DbSession,
    probe_id: ProbeId,
    eingabe: ProbeUpdate,
) -> ProbeView:
    sonde = require_writable(session, PrivacyProbe, authorization, probe_id)
    sonde.label = eingabe.label
    session.flush()
    return ProbeView.model_validate(sonde)


@router.delete(
    "/spaces/{spaceId}/privacy-probes/{probeId}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_probe(authorization: Authorization, session: DbSession, probe_id: ProbeId) -> None:
    session.delete(require_writable(session, PrivacyProbe, authorization, probe_id))
    session.flush()


def create_probe_app(session: Session) -> FastAPI:
    """Die produktive App plus Sondenrouter, auf der Transaktion des Tests."""
    app = create_app()
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_session] = lambda: session
    return app
