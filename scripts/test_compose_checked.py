#!/usr/bin/env python3
"""Unit tests for the verified-checkout Compose wrapper's own safety checks.

These do not invoke Docker; they cover the pure precondition checks that run
before ``compose_checked.py`` ever shells out.
"""

from __future__ import annotations

import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from scripts.compose_checked import CheckoutError, require_self_hosted_secrets


class RequireSelfHostedSecretsTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.env_file = Path(self._tmp.name) / ".env"

    def _write_env(self, contents: str) -> None:
        self.env_file.write_text(contents, encoding="utf-8")

    def test_refuses_when_env_file_is_missing(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True), self.assertRaises(CheckoutError):
            require_self_hosted_secrets(self.env_file)

    def test_refuses_a_blank_password(self) -> None:
        self._write_env("POSTGRES_USER=sidebyside\nPOSTGRES_PASSWORD=\n")
        with (
            mock.patch.dict(os.environ, {}, clear=True),
            self.assertRaises(CheckoutError) as ctx,
        ):
            require_self_hosted_secrets(self.env_file)
        self.assertIn("POSTGRES_PASSWORD", str(ctx.exception))

    def test_refuses_a_missing_password_line(self) -> None:
        self._write_env("POSTGRES_USER=sidebyside\n")
        with mock.patch.dict(os.environ, {}, clear=True), self.assertRaises(CheckoutError):
            require_self_hosted_secrets(self.env_file)

    def test_accepts_credentials_from_the_env_file(self) -> None:
        self._write_env("POSTGRES_USER=sidebyside\nPOSTGRES_PASSWORD=a-real-secret\n")
        with mock.patch.dict(os.environ, {}, clear=True):
            require_self_hosted_secrets(self.env_file)  # must not raise

    def test_process_environment_can_supply_the_password_instead(self) -> None:
        self._write_env("POSTGRES_USER=sidebyside\n")
        with mock.patch.dict(
            os.environ, {"POSTGRES_PASSWORD": "a-real-secret"}, clear=True
        ):
            require_self_hosted_secrets(self.env_file)  # must not raise

    def test_process_environment_blank_value_does_not_fall_back_to_the_file(self) -> None:
        # Matches Compose's own precedence: an explicitly-set (even blank)
        # process environment variable wins over `.env` and must still fail
        # closed rather than silently reading the file's value instead.
        self._write_env("POSTGRES_USER=sidebyside\nPOSTGRES_PASSWORD=a-real-secret\n")
        with (
            mock.patch.dict(os.environ, {"POSTGRES_PASSWORD": ""}, clear=True),
            self.assertRaises(CheckoutError),
        ):
            require_self_hosted_secrets(self.env_file)


if __name__ == "__main__":
    unittest.main()
