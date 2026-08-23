"""Job-Warteschlange in PostgreSQL.

Geprueft wird vor allem das Verhalten unter Nebenlaeufigkeit und im
Fehlerfall - der Rest ist Buchhaltung.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker

from sidebyside.core.clock import now
from sidebyside.jobs import queue
from sidebyside.jobs.models import Job, JobStatus
from tests.conftest import requires_database

pytestmark = [pytest.mark.integration, requires_database]


class TestEinstellenUndAbholen:
    def test_eingestellte_aufgabe_wird_abgeholt(self, engine: Engine) -> None:
        macher = sessionmaker(bind=engine, expire_on_commit=False)
        sitzung = macher()
        try:
            job = queue.enqueue(sitzung, "send_push", {"notification_id": "x"})
            sitzung.commit()

            geholt = queue.claim(sitzung, "worker-1")
            assert job.id in {j.id for j in geholt}
            assert job.status == JobStatus.RUNNING.value
            assert job.attempts == 1
            sitzung.commit()
        finally:
            sitzung.query(Job).delete()
            sitzung.commit()
            sitzung.close()

    def test_verzoegerte_aufgabe_wird_noch_nicht_abgeholt(self, engine: Engine) -> None:
        macher = sessionmaker(bind=engine, expire_on_commit=False)
        sitzung = macher()
        try:
            job = queue.enqueue(sitzung, "spaeter", delay=timedelta(hours=1))
            sitzung.commit()
            assert job.id not in {j.id for j in queue.claim(sitzung, "worker-1")}
            sitzung.commit()
        finally:
            sitzung.query(Job).delete()
            sitzung.commit()
            sitzung.close()


class TestNebenlaeufigkeit:
    def test_zwei_worker_greifen_nie_dieselbe_aufgabe(self, engine: Engine) -> None:
        """Das ist der Grund fuer FOR UPDATE SKIP LOCKED. Ohne das wuerde
        entweder doppelt zugestellt oder der zweite Worker blockiert."""
        macher = sessionmaker(bind=engine, expire_on_commit=False)

        vorbereitung = macher()
        try:
            for i in range(6):
                queue.enqueue(vorbereitung, "arbeit", {"i": i})
            vorbereitung.commit()
        finally:
            vorbereitung.close()

        erste = macher()
        zweite = macher()
        try:
            a = {job.id for job in queue.claim(erste, "worker-a", limit=3)}
            b = {job.id for job in queue.claim(zweite, "worker-b", limit=3)}

            assert len(a) == 3
            assert len(b) == 3
            assert a.isdisjoint(b)

            erste.commit()
            zweite.commit()
        finally:
            erste.close()
            zweite.close()
            aufraeumen = macher()
            aufraeumen.query(Job).delete()
            aufraeumen.commit()
            aufraeumen.close()

    def test_abgelaufene_sperre_wird_neu_vergeben(self, engine: Engine) -> None:
        """Eine Aufgabe, deren Worker gestorben ist, darf nicht fuer immer
        liegenbleiben."""
        macher = sessionmaker(bind=engine, expire_on_commit=False)
        sitzung = macher()
        try:
            job = queue.enqueue(sitzung, "verwaist")
            sitzung.commit()

            job.status = JobStatus.RUNNING.value
            job.locked_by = "toter-worker"
            job.locked_until = now() - timedelta(minutes=1)
            sitzung.commit()

            geholt = queue.claim(sitzung, "worker-neu")
            assert job.id in {j.id for j in geholt}
            assert job.locked_by == "worker-neu"
            sitzung.commit()
        finally:
            sitzung.query(Job).delete()
            sitzung.commit()
            sitzung.close()


class TestFehlerbehandlung:
    def test_fehlschlag_geht_mit_verzoegerung_zurueck(self, engine: Engine) -> None:
        macher = sessionmaker(bind=engine, expire_on_commit=False)
        sitzung = macher()
        try:
            job = queue.enqueue(sitzung, "wackelig", max_attempts=3)
            sitzung.commit()
            queue.claim(sitzung, "worker-1")

            queue.fail(job, "Empfaenger antwortet nicht")
            sitzung.commit()

            assert job.status == JobStatus.PENDING.value
            assert job.run_after > now()
            assert job.locked_by is None
        finally:
            sitzung.query(Job).delete()
            sitzung.commit()
            sitzung.close()

    def test_aufgebrauchte_versuche_enden_als_failed(self, engine: Engine) -> None:
        """Nicht still verwerfen - eine dauerhaft gescheiterte Aufgabe muss
        sichtbar bleiben."""
        macher = sessionmaker(bind=engine, expire_on_commit=False)
        sitzung = macher()
        try:
            job = queue.enqueue(sitzung, "hoffnungslos", max_attempts=1)
            sitzung.commit()
            queue.claim(sitzung, "worker-1")

            queue.fail(job, "geht nicht")
            sitzung.commit()

            assert job.status == JobStatus.FAILED.value
            assert job.finished_at is not None
        finally:
            sitzung.query(Job).delete()
            sitzung.commit()
            sitzung.close()
