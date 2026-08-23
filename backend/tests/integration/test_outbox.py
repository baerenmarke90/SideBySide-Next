"""Transactional Outbox.

Der Punkt der Outbox ist eine Garantie: fachliche Aenderung und Ereignis
werden gemeinsam wirksam oder gar nicht. Genau das wird hier geprueft -
nicht nur, dass sich eine Zeile schreiben laesst.
"""

from __future__ import annotations

import pytest
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session, sessionmaker

from sidebyside.core.ids import new_id
from sidebyside.domain.events import DomainEvent, EventType
from sidebyside.outbox import service
from sidebyside.outbox.models import OutboxEvent
from tests.conftest import requires_database

pytestmark = [pytest.mark.integration, requires_database]


def _event() -> DomainEvent:
    return DomainEvent(
        type=EventType.MEMORY_CREATED,
        space_id=new_id(),
        actor_id=new_id(),
        subject_type="memory",
        subject_id=new_id(),
        payload={"has_attachment": True},
    )


class TestSchreiben:
    def test_ereignis_wird_vorgemerkt(self, session: Session) -> None:
        zeile = service.record(session, _event())
        session.flush()

        assert zeile.id is not None
        assert zeile.processed_at is None
        assert zeile.attempts == 0

    def test_ohne_commit_der_fachlichen_transaktion_bleibt_nichts(self, engine: Engine) -> None:
        """Die Garantie in ihrer wichtigsten Richtung: wird die Transaktion
        zurueckgerollt, entsteht auch kein Ereignis. Sonst benachrichtigte
        die Anwendung ueber etwas, das nie geschehen ist."""
        macher = sessionmaker(bind=engine, expire_on_commit=False)
        ereignis = _event()

        sitzung = macher()
        service.record(sitzung, ereignis)
        sitzung.flush()
        sitzung.rollback()
        sitzung.close()

        pruefer = macher()
        try:
            treffer = (
                pruefer.execute(
                    select(OutboxEvent).where(OutboxEvent.subject_id == ereignis.subject_id)
                )
                .scalars()
                .all()
            )
            assert treffer == []
        finally:
            pruefer.close()


class TestAbholen:
    def test_liefert_nur_unverarbeitete(self, session: Session) -> None:
        offen = service.record(session, _event())
        erledigt = service.record(session, _event())
        service.mark_processed(erledigt)
        session.flush()

        ids = {zeile.id for zeile in service.claim_unprocessed(session)}
        assert offen.id in ids
        assert erledigt.id not in ids

    def test_reihenfolge_ist_die_entstehung(self, session: Session) -> None:
        erst = service.record(session, _event())
        dann = service.record(session, _event())
        session.flush()

        geholt = list(service.claim_unprocessed(session))
        positionen = {zeile.id: i for i, zeile in enumerate(geholt)}
        assert positionen[erst.id] < positionen[dann.id]


class TestFehlschlag:
    def test_fehlschlag_schliesst_die_zeile_nicht_ab(self, session: Session) -> None:
        """Ein fehlgeschlagenes Ereignis muss erneut versucht werden."""
        zeile = service.record(session, _event())
        session.flush()

        service.mark_failed(zeile, "Empfaenger nicht erreichbar")
        session.flush()

        assert zeile.processed_at is None
        assert zeile.attempts == 1
        assert zeile.id in {z.id for z in service.claim_unprocessed(session)}

    def test_lange_fehlermeldung_wird_gekuerzt(self, session: Session) -> None:
        zeile = service.record(session, _event())
        session.flush()
        service.mark_failed(zeile, "x" * 5000)
        assert zeile.last_error is not None
        assert len(zeile.last_error) == 2000


class TestNutzlast:
    def test_traegt_keine_inhalte(self, session: Session) -> None:
        """Die Nutzlast ueberlebt in der Outbox und in Logs, und nach der
        Umstellung auf Ende-zu-Ende-Verschluesselung stuende ein Text
        ohnehin nicht mehr zur Verfuegung."""
        zeile = service.record(session, _event())
        session.flush()
        assert set(zeile.payload) <= {"has_attachment"}
