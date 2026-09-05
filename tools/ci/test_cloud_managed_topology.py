#!/usr/bin/env python3
"""Fail-closed contract checks for the #521 Cloud/Managed v1 deployment recipe.

These are configuration-contract tests, not a live deployment: they read the
versioned recipe/template text (and, where Docker is available, the resolved
Compose configuration) to prove the mechanical parts of
docs/m6/CLOUD-MANAGED-TOPOLOGY.md cannot silently regress. They do not require
or simulate a real managed provider.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPOSE_CLOUD = ROOT / "deploy/compose.cloud.yml"
CLOUD_ENV_EXAMPLE = ROOT / "deploy/cloud-managed.env.example"
DEV_ENV_EXAMPLE = ROOT / "deploy/persistent-development.env.example"

sys.path.insert(0, str(ROOT / "scripts"))
import check_environment_isolation as isolation  # noqa: E402


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class CloudComposeTextContractTest(unittest.TestCase):
    """Structural checks on the raw recipe text (no Docker required)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.compose = _read(COMPOSE_CLOUD)

    def test_no_bundled_postgres_service(self) -> None:
        self.assertNotRegex(self.compose, r"(?m)^\s{2}postgres:")

    def test_no_demo_init_service(self) -> None:
        self.assertNotRegex(self.compose, r"(?m)^\s{2}demo-init:")
        self.assertNotIn("scripts.demo_space", self.compose)

    def test_no_local_media_volume(self) -> None:
        self.assertNotIn("media_data", self.compose)
        self.assertIn("SBS_MEDIA_STORE: s3", self.compose)

    def test_processes_use_immutable_images_not_source_builds(self) -> None:
        self.assertNotRegex(self.compose, r"(?m)^\s{4,}build:")
        for service in ("api", "worker", "migrate", "web"):
            self.assertIn(f"<<: *{'web-image' if service == 'web' else 'backend-image'}", self.compose)

    def test_image_references_fail_closed_without_a_floating_default(self) -> None:
        for var in ("SBS_BACKEND_IMAGE", "SBS_WEB_IMAGE"):
            self.assertIn(f"${{{var}:?", self.compose)
        self.assertNotRegex(self.compose, r"SBS_(BACKEND|WEB)_IMAGE:-")

    def test_migrate_never_restarts_automatically(self) -> None:
        match = re.search(r"(?ms)^  migrate:\n(.*?)^  \w", self.compose)
        self.assertIsNotNone(match)
        self.assertIn('restart: "no"', match.group(1))

    def test_deletion_journal_uses_a_dedicated_named_volume(self) -> None:
        self.assertIn("deletion_journal_data:/var/lib/sidebyside/deletion-journal", self.compose)
        self.assertRegex(self.compose, r"(?m)^  deletion_journal_data:\s*$")

    def test_required_secrets_fail_closed(self) -> None:
        for var in (
            "SBS_DATABASE_URL",
            "SBS_CURSOR_SIGNING_KEY",
            "SBS_S3_ENDPOINT",
            "SBS_S3_BUCKET",
            "SBS_S3_ACCESS_KEY_ID",
            "SBS_S3_SECRET_ACCESS_KEY",
            "SBS_ACCOUNT_DELETION_INSTANCE_ID",
            "SBS_ALLOWED_HOSTS",
            "SBS_PUBLIC_BASE_URL",
        ):
            self.assertIn(f"${{{var}:?", self.compose, msg=f"{var} must fail closed when unset")

    def test_production_mail_default_is_not_log(self) -> None:
        # Environment.PRODUCTION rejects SBS_MAIL_TRANSPORT=log at startup
        # (backend/src/sidebyside/config.py); the Cloud recipe must not default
        # into a configuration that always fails to start.
        self.assertIn("SBS_MAIL_TRANSPORT:-none", self.compose)
        self.assertNotIn("SBS_MAIL_TRANSPORT:-log", self.compose)


@unittest.skipUnless(shutil.which("docker"), "docker is required to resolve compose config")
class CloudComposeResolvedConfigTest(unittest.TestCase):
    """Validates the recipe actually resolves the way the text implies."""

    def _resolve(self, env_overrides: dict[str, str]) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / "cloud.env"
            merged: dict[str, str] = dict(_pairs(_read(CLOUD_ENV_EXAMPLE).splitlines()))
            merged.update(env_overrides)
            env_path.write_text(
                "\n".join(f"{key}={value}" for key, value in merged.items()) + "\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    "docker",
                    "compose",
                    "-f",
                    str(COMPOSE_CLOUD),
                    "--env-file",
                    str(env_path),
                    "config",
                    "--format",
                    "json",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise AssertionError(result.stderr)
            return json.loads(result.stdout)

    def _valid_overrides(self) -> dict[str, str]:
        return {
            "SBS_BACKEND_IMAGE": "registry.example/sidebyside-backend:v1.0.0",
            "SBS_WEB_IMAGE": "registry.example/sidebyside-web:v1.0.0",
            "SBS_DATABASE_URL": "postgresql+psycopg://user:pass@db.private:5432/sidebyside",
            "SBS_S3_ACCESS_KEY_ID": "test-access-key",
            "SBS_S3_SECRET_ACCESS_KEY": "test-secret-key",
            "SBS_ACCOUNT_DELETION_INSTANCE_ID": "00000000-0000-0000-0000-000000000000",
        }

    def test_resolved_recipe_has_no_postgres_or_demo_init_service(self) -> None:
        config = self._resolve(self._valid_overrides())
        self.assertEqual(sorted(config["services"]), ["api", "migrate", "web", "worker"])

    def test_resolved_services_reference_images_not_builds(self) -> None:
        config = self._resolve(self._valid_overrides())
        for name in ("api", "migrate", "worker"):
            self.assertEqual(
                config["services"][name]["image"],
                "registry.example/sidebyside-backend:v1.0.0",
            )
            self.assertNotIn("build", config["services"][name])
        self.assertEqual(
            config["services"]["web"]["image"], "registry.example/sidebyside-web:v1.0.0"
        )

    def test_resolved_media_store_is_s3(self) -> None:
        config = self._resolve(self._valid_overrides())
        self.assertEqual(config["services"]["api"]["environment"]["SBS_MEDIA_STORE"], "s3")

    def test_missing_backend_image_fails_closed(self) -> None:
        overrides = self._valid_overrides()
        del overrides["SBS_BACKEND_IMAGE"]
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / "cloud.env"
            merged: dict[str, str] = dict(_pairs(_read(CLOUD_ENV_EXAMPLE).splitlines()))
            merged.update(overrides)
            del merged["SBS_BACKEND_IMAGE"]
            env_path.write_text(
                "\n".join(f"{key}={value}" for key, value in merged.items()) + "\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    "docker",
                    "compose",
                    "-f",
                    str(COMPOSE_CLOUD),
                    "--env-file",
                    str(env_path),
                    "config",
                    "--quiet",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("SBS_BACKEND_IMAGE", result.stderr)


def _pairs(lines: list[str]):
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        yield key.strip(), value.strip()


class CloudEnvironmentTemplateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.values = dict(_pairs(_read(CLOUD_ENV_EXAMPLE).splitlines()))

    def test_declares_production_cloud_deployment(self) -> None:
        self.assertEqual(self.values["SBS_ENVIRONMENT"], "production")
        self.assertEqual(self.values["SBS_DEPLOYMENT"], "cloud")

    def test_rejects_local_media_store_by_omission(self) -> None:
        self.assertNotIn("SBS_MEDIA_STORE", self.values)
        text = _read(CLOUD_ENV_EXAMPLE)
        self.assertNotIn("SBS_MEDIA_STORE=local", text)

    def test_image_placeholders_are_not_floating_tags(self) -> None:
        for var in ("SBS_BACKEND_IMAGE", "SBS_WEB_IMAGE"):
            value = self.values[var]
            self.assertNotIn(":latest", value)
            self.assertNotRegex(value, r":main$")

    def test_isolated_from_persistent_development_template(self) -> None:
        development = isolation.parse_dotenv(DEV_ENV_EXAMPLE)
        production = isolation.parse_dotenv(CLOUD_ENV_EXAMPLE)
        problems = isolation.check_isolation(development, production)
        self.assertEqual(problems, [])

    def test_reused_development_signing_key_is_rejected(self) -> None:
        development = isolation.parse_dotenv(DEV_ENV_EXAMPLE)
        production = dict(isolation.parse_dotenv(CLOUD_ENV_EXAMPLE))
        production["SBS_CURSOR_SIGNING_KEY"] = development["SBS_CURSOR_SIGNING_KEY"]
        problems = isolation.check_isolation(development, production)
        self.assertIn(
            "Development and Production must not reuse SBS_CURSOR_SIGNING_KEY", problems
        )


if __name__ == "__main__":
    unittest.main()
