"""Der Wartungsjob fuer Security-Retention.

Geprueft wird beides: dass er die richtigen Zeilen raeumt und dass er
ueberhaupt zuverlaessig wieder ansteht.
"""

from __future__ import annotations

from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import pytest
from sqlalchemy import Engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from sidebyside.auth import rate_limit, sessions
from sidebyside.core.clock import now
from sidebyside.identity.models import ConsumedRefreshToken, RateLimitEvent
from sidebyside.jobs import maintenance
from sidebyside.jobs.models import Job, JobStatus
from sidebyside.jobs.worker import JobRegistry
from tests.conftest import make_account, requires_database

pytestmark = [pytest.mark.integration, requires_database]


@pytest.fixture
def aufgaben(engine: Engine) -> Iterator[sessionmaker[Session]]:
    """Committete Aufgaben - Advisory Locks brauchen echte Transaktionen."""
    macher = sessionmaker(bind=engine, expire_on_commit=False)

    def leeren() -> None:
        with macher() as sitzung:
            sitzung.query(Job).delete()
            sitzung.commit()

    leeren()
    yield macher
    leeren()


def offene_aufgaben(session: Session) -> list[Job]:
    return list(
        session.execute(
            select(Job).where(
                Job.kind == maintenance.SECURITY_RETENTION,
                Job.status == JobStatus.PENDING.value,
            )
        )
        .scalars()
        .all()
    )


class TestRaeumen:
    def test_beendete_familie_wird_nach_der_frist_geraeumt(self, session: Session) -> None:
        konto = make_account(session)
        geraet, tokens = sessions.start_session(session, konto)
        session.flush()
        sessions.refresh_session(session, tokens.refresh_token)
        session.flush()

        sessions.revoke(geraet)
        geraet.revoked_at = now() - sessions.REPLAY_HISTORY_RETENTION - timedelta(days=1)
        session.flush()

        maintenance.run_security_retention(session, {})
        session.flush()

        assert session.execute(select(ConsumedRefreshToken)).scalars().all() == []

    def test_laufende_familie_behaelt_ihre_historie(self, session: Session) -> None:
        """Die Historie einer lebenden Sitzung ist die Replay-Erkennung selbst."""
        konto = make_account(session)
        _, tokens = sessions.start_session(session, konto)
        session.flush()
        sessions.refresh_session(session, tokens.refresh_token)
        session.flush()

        maintenance.run_security_retention(session, {})
        session.flush()

        assert session.execute(select(ConsumedRefreshToken)).scalars().all()

    def test_alte_rate_limit_ereignisse_gehen_aktuelle_bleiben(self, session: Session) -> None:
        rate_limit.record_attempt(session, "sign_in", "alt@example.org")
        rate_limit.record_attempt(session, "sign_in", "neu@example.org")
        session.flush()

        alt = (
            session.execute(select(RateLimitEvent).where(RateLimitEvent.key_hash != ""))
            .scalars()
            .all()[0]
        )
        alt.occurred_at = now() - timedelta(days=2)
        session.flush()

        maintenance.run_security_retention(session, {})
        session.flush()

        uebrig = session.execute(select(func.count()).select_from(RateLimitEvent)).scalar_one()
        assert uebrig == 1

    def test_wiederholter_lauf_ist_harmlos(self, session: Session) -> None:
        maintenance.run_security_retention(session, {})
        maintenance.run_security_retention(session, {})
        session.flush()


class TestEinplanung:
    def test_ein_lauf_plant_seinen_nachfolger(self, aufgaben) -> None:  # type: ignore[no-untyped-def]
        with aufgaben() as sitzung:
            maintenance.run_security_retention(sitzung, {})
            sitzung.commit()

            offen = offene_aufgaben(sitzung)
            assert len(offen) == 1
            assert offen[0].run_after > now() + maintenance.RETENTION_INTERVAL - timedelta(
                minutes=1
            )

    def test_ensure_scheduled_ist_idempotent(self, aufgaben) -> None:  # type: ignore[no-untyped-def]
        with aufgaben() as sitzung:
            maintenance.ensure_scheduled(sitzung)
            sitzung.commit()
            maintenance.ensure_scheduled(sitzung)
            sitzung.commit()

            assert len(offene_aufgaben(sitzung)) == 1

    def test_zwei_startende_worker_planen_nur_einen_lauf(self, aufgaben) -> None:  # type: ignore[no-untyped-def]
        """Ohne die Advisory Lock saehen beide nichts und stellten beide ein."""
        schranke = Barrier(2)

        def einplanen() -> None:
            with aufgaben() as sitzung:
                schranke.wait(timeout=5)
                maintenance.ensure_scheduled(sitzung)
                sitzung.commit()

        with ThreadPoolExecutor(max_workers=2) as pool:
            for aufgabe in [pool.submit(einplanen), pool.submit(einplanen)]:
                aufgabe.result(timeout=10)

        with aufgaben() as sitzung:
            assert len(offene_aufgaben(sitzung)) == 1

    def test_eine_aufgegebene_kette_wird_wieder_aufgenommen(self, aufgaben) -> None:  # type: ignore[no-untyped-def]
        """Sonst bliebe der Cleanup nach einem endgueltigen Fehlschlag still aus."""
        with aufgaben() as sitzung:
            job = maintenance.ensure_scheduled(sitzung)
            assert job is not None
            sitzung.commit()

            job.status = JobStatus.FAILED.value
            job.finished_at = now()
            sitzung.commit()

            assert maintenance.ensure_scheduled(sitzung) is not None
            sitzung.commit()
            assert len(offene_aufgaben(sitzung)) == 1

    def test_laufende_aufgabe_wird_nicht_verdoppelt(self, aufgaben) -> None:  # type: ignore[no-untyped-def]
        with aufgaben() as sitzung:
            job = maintenance.ensure_scheduled(sitzung)
            assert job is not None
            job.status = JobStatus.RUNNING.value
            sitzung.commit()

            assert maintenance.ensure_scheduled(sitzung) is None
            sitzung.commit()


class TestUeberDenWorker:
    def test_der_worker_fuehrt_die_wartung_aus_und_plant_neu(self, aufgaben, monkeypatch) -> None:  # type: ignore[no-untyped-def]
        """Der ganze Weg: eingeplant, abgeholt, ausgefuehrt, neu eingeplant."""
        from sidebyside.db import session as db_session
        from sidebyside.jobs import worker

        monkeypatch.setattr(db_session, "get_sessionmaker", lambda: aufgaben)

        eigene_registry = JobRegistry()
        maintenance.register_handlers(eigene_registry)
        monkeypatch.setattr(worker, "registry", eigene_registry)

        with aufgaben() as sitzung:
            maintenance.ensure_scheduled(sitzung)
            sitzung.commit()

        assert worker.run_once("test-worker") == 1

        with aufgaben() as sitzung:
            erledigt = (
                sitzung.execute(select(Job).where(Job.status == JobStatus.SUCCEEDED.value))
                .scalars()
                .all()
            )
            assert len(erledigt) == 1
            assert erledigt[0].kind == maintenance.SECURITY_RETENTION
            assert len(offene_aufgaben(sitzung)) == 1

    def test_doppelte_anmeldung_bleibt_folgenlos(self) -> None:
        eigene_registry = JobRegistry()
        maintenance.register_handlers(eigene_registry)
        maintenance.register_handlers(eigene_registry)
        assert eigene_registry.get(maintenance.SECURITY_RETENTION) is not None
