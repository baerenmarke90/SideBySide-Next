"""PostgreSQL-backed job queue integration tests.

The tests focus on concurrency and failure handling; the remaining behavior is
bookkeeping.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker

from sidebyside.core.clock import now
from sidebyside.jobs import queue
from sidebyside.jobs.errors import RetryableJobError
from sidebyside.jobs.models import Job, JobStatus
from sidebyside.jobs.worker import registry, run_once
from tests.conftest import requires_database

pytestmark = [pytest.mark.integration, requires_database]


class TestEnqueueAndClaim:
    def test_enqueued_job_has_id_before_flush(self, engine: Engine) -> None:
        factory = sessionmaker(bind=engine, expire_on_commit=False)
        session = factory()
        try:
            job = queue.enqueue(session, "referenced_job")
            assert job.id is not None
            session.rollback()
        finally:
            session.close()

    def test_enqueued_job_is_claimed(self, engine: Engine) -> None:
        factory = sessionmaker(bind=engine, expire_on_commit=False)
        session = factory()
        try:
            job = queue.enqueue(session, "send_push", {"notification_id": "x"})
            session.commit()

            claimed = queue.claim(session, "worker-1")
            assert job.id in {item.id for item in claimed}
            assert job.status == JobStatus.RUNNING.value
            assert job.attempts == 1
            session.commit()
        finally:
            session.query(Job).delete()
            session.commit()
            session.close()

    def test_delayed_job_is_not_claimed(self, engine: Engine) -> None:
        factory = sessionmaker(bind=engine, expire_on_commit=False)
        session = factory()
        try:
            job = queue.enqueue(session, "spaeter", delay=timedelta(hours=1))
            session.commit()
            assert job.id not in {item.id for item in queue.claim(session, "worker-1")}
            session.commit()
        finally:
            session.query(Job).delete()
            session.commit()
            session.close()


class TestConcurrency:
    def test_two_workers_never_claim_the_same_job(self, engine: Engine) -> None:
        """This is why the queue uses FOR UPDATE SKIP LOCKED.

        Without it, a job could be delivered twice or the second worker could
        block behind the first one.
        """
        factory = sessionmaker(bind=engine, expire_on_commit=False)

        preparation = factory()
        try:
            for i in range(6):
                queue.enqueue(preparation, "arbeit", {"i": i})
            preparation.commit()
        finally:
            preparation.close()

        first = factory()
        second = factory()
        try:
            a = {job.id for job in queue.claim(first, "worker-a", limit=3)}
            b = {job.id for job in queue.claim(second, "worker-b", limit=3)}

            assert len(a) == 3
            assert len(b) == 3
            assert a.isdisjoint(b)

            first.commit()
            second.commit()
        finally:
            first.close()
            second.close()
            cleanup = factory()
            cleanup.query(Job).delete()
            cleanup.commit()
            cleanup.close()

    def test_expired_lock_is_reassigned(self, engine: Engine) -> None:
        """A job must not remain stuck forever when its worker dies."""
        factory = sessionmaker(bind=engine, expire_on_commit=False)
        session = factory()
        try:
            job = queue.enqueue(session, "verwaist")
            session.commit()

            job.status = JobStatus.RUNNING.value
            job.locked_by = "toter-worker"
            job.locked_until = now() - timedelta(minutes=1)
            session.commit()

            claimed = queue.claim(session, "worker-neu")
            assert job.id in {item.id for item in claimed}
            assert job.locked_by == "worker-neu"
            session.commit()
        finally:
            session.query(Job).delete()
            session.commit()
            session.close()


class TestFailureHandling:
    def test_failure_returns_job_to_pending_with_delay(self, engine: Engine) -> None:
        factory = sessionmaker(bind=engine, expire_on_commit=False)
        session = factory()
        try:
            job = queue.enqueue(session, "wackelig", max_attempts=3)
            session.commit()
            queue.claim(session, "worker-1")

            queue.fail(job, "Empfaenger antwortet nicht")
            session.commit()

            assert job.status == JobStatus.PENDING.value
            assert job.run_after > now()
            assert job.locked_by is None
        finally:
            session.query(Job).delete()
            session.commit()
            session.close()

    def test_exhausted_attempts_end_as_failed(self, engine: Engine) -> None:
        """A permanently failed job must stay visible instead of disappearing."""
        factory = sessionmaker(bind=engine, expire_on_commit=False)
        session = factory()
        try:
            job = queue.enqueue(session, "hoffnungslos", max_attempts=1)
            session.commit()
            queue.claim(session, "worker-1")

            queue.fail(job, "geht nicht")
            session.commit()

            assert job.status == JobStatus.FAILED.value
            assert job.finished_at is not None
        finally:
            session.query(Job).delete()
            session.commit()
            session.close()

    def test_fail_scrubs_a_secret_pattern_even_in_an_already_safe_looking_message(
        self, engine: Engine
    ) -> None:
        """Defense in depth at the persistence boundary itself (#680).

        Call sites are expected to pass an already-safe summary; this proves
        the boundary does not simply trust that.
        """
        factory = sessionmaker(bind=engine, expire_on_commit=False)
        session = factory()
        try:
            job = queue.enqueue(session, "belegt")
            session.commit()
            queue.claim(session, "worker-1")

            queue.fail(job, "Bearer super-secret-boundary-token")
            session.commit()

            assert job.last_error is not None
            assert "super-secret-boundary-token" not in job.last_error
        finally:
            session.query(Job).delete()
            session.commit()
            session.close()


class TestUnexpectedFailureDiagnostic:
    """#680: an unexpected handler exception's own text is not
    developer-authored and must not be persisted verbatim into
    ``jobs.last_error``.
    """

    def test_unexpected_exception_persists_only_a_safe_summary(self, engine: Engine) -> None:
        canary = "SUPER_SECRET_PRIVATE_TEXT owned by another visitor"
        secret_token = "super-secret-worker-token"

        def failing_handler(session: object, payload: dict) -> None:
            raise RuntimeError(f"Bearer {secret_token} {canary}")

        job_kind = "test_worker_unexpected_failure_diagnostic"
        if registry.get(job_kind) is None:
            registry.register(job_kind, failing_handler)

        setup_session = sessionmaker(bind=engine, expire_on_commit=False)()
        try:
            job = queue.enqueue(setup_session, job_kind, {})
            setup_session.commit()
            job_id = job.id

            processed = run_once("test-worker-diag", limit=10)
            assert processed >= 1

            check_session = sessionmaker(bind=engine, expire_on_commit=False)()
            try:
                reloaded = check_session.get(Job, job_id)
                assert reloaded is not None
                assert reloaded.last_error is not None
                assert canary not in reloaded.last_error
                assert secret_token not in reloaded.last_error
                assert "RuntimeError" in reloaded.last_error
                # Attempts/retry bookkeeping is unaffected by the diagnostic
                # contract change: one failed attempt against the default
                # max_attempts leaves the job scheduled to retry, not FAILED.
                assert reloaded.status == JobStatus.PENDING.value
                assert reloaded.attempts == 1
            finally:
                check_session.close()
        finally:
            setup_session.query(Job).delete()
            setup_session.commit()
            setup_session.close()

    def test_retryable_job_error_code_is_still_retained_verbatim(self, engine: Engine) -> None:
        """A controlled, stable technical code is not affected by #680's fix."""
        stable_code = "TEST_RETRYABLE_DIAGNOSTIC_CODE"

        def retrying_handler(session: object, payload: dict) -> None:
            raise RetryableJobError(stable_code)

        job_kind = "test_worker_retryable_diagnostic"
        if registry.get(job_kind) is None:
            registry.register(job_kind, retrying_handler)

        setup_session = sessionmaker(bind=engine, expire_on_commit=False)()
        try:
            job = queue.enqueue(setup_session, job_kind, {})
            setup_session.commit()
            job_id = job.id

            processed = run_once("test-worker-retry-diag", limit=10)
            assert processed >= 1

            check_session = sessionmaker(bind=engine, expire_on_commit=False)()
            try:
                reloaded = check_session.get(Job, job_id)
                assert reloaded is not None
                assert reloaded.last_error == stable_code
            finally:
                check_session.close()
        finally:
            setup_session.query(Job).delete()
            setup_session.commit()
            setup_session.close()

    def test_successful_retry_still_clears_the_failure_diagnostic(self, engine: Engine) -> None:
        """The existing success contract (`last_error = None`) is unaffected."""
        attempt_count = {"n": 0}

        def flaky_handler(session: object, payload: dict) -> None:
            attempt_count["n"] += 1
            if attempt_count["n"] == 1:
                raise RuntimeError("temporary canary secret=abc123")

        job_kind = "test_worker_flaky_then_succeeds"
        if registry.get(job_kind) is None:
            registry.register(job_kind, flaky_handler)

        setup_session = sessionmaker(bind=engine, expire_on_commit=False)()
        try:
            job = queue.enqueue(setup_session, job_kind, {})
            setup_session.commit()
            job_id = job.id

            assert run_once("test-worker-flaky", limit=10) >= 1

            check_session = sessionmaker(bind=engine, expire_on_commit=False)()
            try:
                reloaded = check_session.get(Job, job_id)
                assert reloaded is not None
                assert reloaded.last_error is not None
                assert "abc123" not in reloaded.last_error
                reloaded.run_after = now()
            finally:
                check_session.commit()
                check_session.close()

            assert run_once("test-worker-flaky", limit=10) >= 1

            final_session = sessionmaker(bind=engine, expire_on_commit=False)()
            try:
                final = final_session.get(Job, job_id)
                assert final is not None
                assert final.status == JobStatus.SUCCEEDED.value
                assert final.last_error is None
            finally:
                final_session.close()
        finally:
            cleanup = sessionmaker(bind=engine, expire_on_commit=False)()
            cleanup.query(Job).delete()
            cleanup.commit()
            cleanup.close()
