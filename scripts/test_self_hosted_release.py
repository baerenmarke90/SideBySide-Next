#!/usr/bin/env python3
"""Unit tests for the released Self-Hosted launcher boundary."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.self_hosted_release import (
    ReleaseOperationError,
    read_dotenv,
    require_release_environment,
)


class ReleaseEnvironmentTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.env_file = Path(self._tmp.name) / ".env"

    def _write(self, environment: str) -> None:
        self.env_file.write_text(
            f"SBS_ENVIRONMENT={environment}\nSBS_RELEASE_VERSION=0.1.0\n",
            encoding="utf-8",
        )

    def _require_release_environment(self) -> None:
        require_release_environment(read_dotenv(self.env_file))

    def test_accepts_production_with_no_process_override(self) -> None:
        self._write("production")
        with mock.patch.dict(os.environ, {}, clear=True):
            self._require_release_environment()

    def test_rejects_development_dotenv(self) -> None:
        self._write("development")
        with mock.patch.dict(os.environ, {}, clear=True), self.assertRaisesRegex(
            ReleaseOperationError, "requires exact SBS_ENVIRONMENT=production"
        ):
            self._require_release_environment()

    def test_rejects_process_override_away_from_production(self) -> None:
        self._write("production")
        with mock.patch.dict(
            os.environ, {"SBS_ENVIRONMENT": "development"}, clear=True
        ), self.assertRaisesRegex(
            ReleaseOperationError, "must be unset or exactly production"
        ):
            self._require_release_environment()

    def test_accepts_explicit_production_process_environment(self) -> None:
        self._write("production")
        with mock.patch.dict(
            os.environ, {"SBS_ENVIRONMENT": "production"}, clear=True
        ):
            self._require_release_environment()

    def test_rejects_missing_env_file(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True), self.assertRaisesRegex(
            ReleaseOperationError, "does not exist"
        ):
            self._require_release_environment()


if __name__ == "__main__":
    unittest.main()
