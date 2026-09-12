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
    def test_env_plan_uses_explicit_local_images_and_source_contexts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / ".env"
            env_file.write_text(
                "\n".join(
                    (
                        "SBS_BUILD_REVISION=0123456789abcdef0123456789abcdef01234567",
                        "SBS_BACKEND_BUILD_CONTEXT=https://github.com/example/project.git#main:backend",
                        "SBS_WEB_BUILD_CONTEXT=https://github.com/example/project.git#main:web",
                        "SBS_SELF_HOSTED_BACKEND_IMAGE=sidebyside-backend:source-ci",
                        "SBS_SELF_HOSTED_WEB_IMAGE=sidebyside-web:source-ci",
                        "SBS_DEMO_MODE=false",
                        "",
                    )
                ),
                encoding="utf-8",
            )
            with patch.dict(os.environ, {}, clear=True):
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
        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / ".env"
            env_file.write_text(
                "SBS_SELF_HOSTED_BACKEND_IMAGE=ghcr.io/baerenmarke90/eimir-backend:v0.1.0\n"
                "SBS_SELF_HOSTED_WEB_IMAGE=sidebyside-web:source-local\n",
                encoding="utf-8",
            )
            with patch.dict(os.environ, {}, clear=True):
                with self.assertRaises(SourceBuildError):
                    plan(env_file)


if __name__ == "__main__":
    unittest.main()
