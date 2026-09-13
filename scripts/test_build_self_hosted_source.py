#!/usr/bin/env python3
"""Unit tests for the Development/CI source-image build boundary."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.build_self_hosted_source import SourceBuildError, plan, require_local_tag


class LocalImageTagTest(unittest.TestCase):
    def test_accepts_expected_local_repositories(self) -> None:
        self.assertEqual(
            require_local_tag(
                "sidebyside-backend:source-local",
                "backend",
                "sidebyside-backend",
            ),
            "sidebyside-backend:source-local",
        )
        self.assertEqual(
            require_local_tag(
                "sidebyside-web:verified-0123456789ab",
                "web",
                "sidebyside-web",
            ),
            "sidebyside-web:verified-0123456789ab",
        )

    def test_rejects_registry_digest_wrong_repository_and_option_like_values(self) -> None:
        invalid = (
            "ghcr.io/baerenmarke90/eimir-backend:v0.1.0",
            "sidebyside-backend:source@sha256:" + "a" * 64,
            "registry.example/sidebyside-backend:source-local",
            "sidebyside-web:source-local",
            "sidebyside-backend:--load",
            "sidebyside-backend:",
            "sidebyside-backend:bad/tag",
        )
        for reference in invalid:
            with self.subTest(reference=reference):
                with self.assertRaises(SourceBuildError):
                    require_local_tag(reference, "backend", "sidebyside-backend")


class SourceBuildPlanTest(unittest.TestCase):
    PRODUCTION_ERROR = "source builds are not allowed when SBS_ENVIRONMENT=production is declared"

    def write_env(self, *lines: str) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary = tempfile.TemporaryDirectory()
        env_file = Path(temporary.name) / ".env"
        env_file.write_text("\n".join((*lines, "")), encoding="utf-8")
        return temporary, env_file

    def test_env_plan_uses_explicit_local_images_and_source_contexts(self) -> None:
        temporary, env_file = self.write_env(
            "SBS_ENVIRONMENT=development",
            "SBS_BUILD_REVISION=0123456789abcdef0123456789abcdef01234567",
            "SBS_BACKEND_BUILD_CONTEXT=https://github.com/example/project.git#main:backend",
            "SBS_WEB_BUILD_CONTEXT=https://github.com/example/project.git#main:web",
            "SBS_SELF_HOSTED_BACKEND_IMAGE=sidebyside-backend:source-ci",
            "SBS_SELF_HOSTED_WEB_IMAGE=sidebyside-web:source-ci",
            "SBS_DEMO_MODE=false",
        )
        with temporary, patch.dict(os.environ, {}, clear=True):
            build_plan = plan(env_file)

        self.assertEqual(build_plan["backendImage"], "sidebyside-backend:source-ci")
        self.assertEqual(build_plan["webImage"], "sidebyside-web:source-ci")
        self.assertEqual(
            build_plan["backendContext"],
            "https://github.com/example/project.git#main:backend",
        )
        self.assertEqual(
            build_plan["webContext"],
            "https://github.com/example/project.git#main:web",
        )

    def test_registry_target_in_env_is_rejected_before_docker_execution(self) -> None:
        temporary, env_file = self.write_env(
            "SBS_ENVIRONMENT=development",
            "SBS_SELF_HOSTED_BACKEND_IMAGE=ghcr.io/baerenmarke90/eimir-backend:v0.1.0",
            "SBS_SELF_HOSTED_WEB_IMAGE=sidebyside-web:source-local",
        )
        with temporary, patch.dict(os.environ, {}, clear=True), self.assertRaises(SourceBuildError):
            plan(env_file)

    def test_production_dotenv_is_rejected_before_source_build(self) -> None:
        temporary, env_file = self.write_env(
            "SBS_ENVIRONMENT=production",
            "SBS_SELF_HOSTED_BACKEND_IMAGE=sidebyside-backend:source-local",
            "SBS_SELF_HOSTED_WEB_IMAGE=sidebyside-web:source-local",
        )
        with temporary, patch.dict(os.environ, {}, clear=True), self.assertRaisesRegex(
            SourceBuildError, self.PRODUCTION_ERROR
        ):
            plan(env_file)

    def test_export_prefixed_production_dotenv_is_rejected(self) -> None:
        temporary, env_file = self.write_env(
            "export SBS_ENVIRONMENT=production",
            "SBS_SELF_HOSTED_BACKEND_IMAGE=sidebyside-backend:source-local",
            "SBS_SELF_HOSTED_WEB_IMAGE=sidebyside-web:source-local",
        )
        with temporary, patch.dict(os.environ, {}, clear=True), self.assertRaisesRegex(
            SourceBuildError, self.PRODUCTION_ERROR
        ):
            plan(env_file)

    def test_last_duplicate_environment_assignment_wins(self) -> None:
        temporary, env_file = self.write_env(
            "SBS_ENVIRONMENT=development",
            "SBS_ENVIRONMENT=production",
            "SBS_SELF_HOSTED_BACKEND_IMAGE=sidebyside-backend:source-local",
            "SBS_SELF_HOSTED_WEB_IMAGE=sidebyside-web:source-local",
        )
        with temporary, patch.dict(os.environ, {}, clear=True), self.assertRaisesRegex(
            SourceBuildError, self.PRODUCTION_ERROR
        ):
            plan(env_file)

    def test_production_with_compose_inline_comment_is_rejected(self) -> None:
        temporary, env_file = self.write_env(
            "SBS_ENVIRONMENT=production # deployed",
            "SBS_SELF_HOSTED_BACKEND_IMAGE=sidebyside-backend:source-local",
            "SBS_SELF_HOSTED_WEB_IMAGE=sidebyside-web:source-local",
        )
        with temporary, patch.dict(os.environ, {}, clear=True), self.assertRaisesRegex(
            SourceBuildError, self.PRODUCTION_ERROR
        ):
            plan(env_file)

    def test_quoted_production_with_trailing_comment_is_rejected(self) -> None:
        temporary, env_file = self.write_env(
            'SBS_ENVIRONMENT="production" # deployed',
            "SBS_SELF_HOSTED_BACKEND_IMAGE=sidebyside-backend:source-local",
            "SBS_SELF_HOSTED_WEB_IMAGE=sidebyside-web:source-local",
        )
        with temporary, patch.dict(os.environ, {}, clear=True), self.assertRaisesRegex(
            SourceBuildError, self.PRODUCTION_ERROR
        ):
            plan(env_file)

    def test_process_environment_cannot_override_development_into_production(self) -> None:
        temporary, env_file = self.write_env(
            "SBS_ENVIRONMENT=development",
            "SBS_SELF_HOSTED_BACKEND_IMAGE=sidebyside-backend:source-local",
            "SBS_SELF_HOSTED_WEB_IMAGE=sidebyside-web:source-local",
        )
        with temporary, patch.dict(os.environ, {"SBS_ENVIRONMENT": "production"}, clear=True), self.assertRaisesRegex(
            SourceBuildError, self.PRODUCTION_ERROR
        ):
            plan(env_file)

    def test_process_development_cannot_mask_production_dotenv(self) -> None:
        temporary, env_file = self.write_env(
            "SBS_ENVIRONMENT=production # deployed",
            "SBS_SELF_HOSTED_BACKEND_IMAGE=sidebyside-backend:source-local",
            "SBS_SELF_HOSTED_WEB_IMAGE=sidebyside-web:source-local",
        )
        with temporary, patch.dict(os.environ, {"SBS_ENVIRONMENT": "development"}, clear=True), self.assertRaisesRegex(
            SourceBuildError, self.PRODUCTION_ERROR
        ):
            plan(env_file)

    def test_ambiguous_interpolated_environment_is_rejected(self) -> None:
        temporary, env_file = self.write_env(
            "SBS_ENVIRONMENT=${DEPLOYMENT_MODE:-production}",
            "SBS_SELF_HOSTED_BACKEND_IMAGE=sidebyside-backend:source-local",
            "SBS_SELF_HOSTED_WEB_IMAGE=sidebyside-web:source-local",
        )
        with temporary, patch.dict(os.environ, {}, clear=True), self.assertRaisesRegex(
            SourceBuildError, "explicit development, demo, or test"
        ):
            plan(env_file)

    def test_authenticated_git_urls_are_rejected_before_plan_output(self) -> None:
        temporary, env_file = self.write_env(
            "SBS_ENVIRONMENT=development",
            "SBS_BACKEND_BUILD_CONTEXT=https://user:token@example.invalid/project.git#main:backend",
            "SBS_WEB_BUILD_CONTEXT=https://example.invalid/project.git#main:web",
            "SBS_SELF_HOSTED_BACKEND_IMAGE=sidebyside-backend:source-local",
            "SBS_SELF_HOSTED_WEB_IMAGE=sidebyside-web:source-local",
        )
        with temporary, patch.dict(os.environ, {}, clear=True), self.assertRaisesRegex(
            SourceBuildError, "must not contain URL credentials"
        ):
            plan(env_file)

    def test_query_bearing_git_urls_are_rejected_before_plan_output(self) -> None:
        temporary, env_file = self.write_env(
            "SBS_ENVIRONMENT=development",
            "SBS_BACKEND_BUILD_CONTEXT=https://example.invalid/project.git?token=secret#main:backend",
            "SBS_WEB_BUILD_CONTEXT=https://example.invalid/project.git#main:web",
            "SBS_SELF_HOSTED_BACKEND_IMAGE=sidebyside-backend:source-local",
            "SBS_SELF_HOSTED_WEB_IMAGE=sidebyside-web:source-local",
        )
        with temporary, patch.dict(os.environ, {}, clear=True), self.assertRaisesRegex(
            SourceBuildError, "must not contain URL query values"
        ):
            plan(env_file)


if __name__ == "__main__":
    unittest.main()
