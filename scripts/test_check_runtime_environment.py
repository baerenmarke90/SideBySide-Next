#!/usr/bin/env python3
"""Unit tests for runtime environment drift detection."""

from __future__ import annotations

import unittest

from scripts.check_runtime_environment import (
    check_dotenv_to_rendered,
    check_production_image_identity,
    check_rendered_to_running,
    parse_container_environment,
)

INSTANCE_ID = "11111111-2222-4333-8444-555555555555"
BACKEND = "ghcr.io/baerenmarke90/eimir-backend:v0.1.0"
WEB = "ghcr.io/baerenmarke90/eimir-web:v0.1.0"
DIGEST = "a" * 64


def rendered(
    instance_id: str = INSTANCE_ID, environment: str = "production"
) -> dict[str, dict[str, str]]:
    common = {
        "SBS_ACCOUNT_DELETION_INSTANCE_ID": instance_id,
        "SBS_ENVIRONMENT": environment,
        "SBS_DEPLOYMENT": "self_hosted",
        "SBS_PUBLIC_BASE_URL": "https://example.invalid",
        "SBS_CURSOR_SIGNING_KEY": "not-printed-secret",
    }
    return {"api": dict(common), "worker": dict(common)}


def image_config(
    *,
    backend: str = BACKEND,
    web: str = WEB,
    worker: str | None = None,
    migrate: str | None = None,
    pull_policy: str = "always",
    build: bool = False,
) -> dict[str, object]:
    def service(image: str) -> dict[str, object]:
        value: dict[str, object] = {"image": image, "pull_policy": pull_policy}
        if build:
            value["build"] = {"context": "./backend"}
        return value

    return {
        "services": {
            "migrate": service(migrate or backend),
            "api": service(backend),
            "worker": service(worker or backend),
            "web": service(web),
        }
    }


class DotenvToRenderedTest(unittest.TestCase):
    def test_accepts_matching_deletion_authority(self) -> None:
        dotenv = {
            "SBS_ENVIRONMENT": "production",
            "SBS_ACCOUNT_DELETION_INSTANCE_ID": INSTANCE_ID,
        }
        self.assertEqual(check_dotenv_to_rendered(dotenv, rendered()), [])

    def test_rejects_blank_compose_override_of_nonempty_dotenv_value(self) -> None:
        dotenv = {
            "SBS_ENVIRONMENT": "production",
            "SBS_ACCOUNT_DELETION_INSTANCE_ID": INSTANCE_ID,
        }
        problems = check_dotenv_to_rendered(dotenv, rendered(instance_id=""))
        self.assertEqual(len(problems), 3)
        self.assertTrue(all("SBS_ACCOUNT_DELETION_INSTANCE_ID" in p for p in problems))
        self.assertTrue(all(INSTANCE_ID not in p for p in problems))

    def test_production_requires_deletion_authority_in_env_file_and_render(self) -> None:
        problems = check_dotenv_to_rendered(
            {"SBS_ENVIRONMENT": "production", "SBS_ACCOUNT_DELETION_INSTANCE_ID": ""},
            rendered(instance_id=""),
        )
        self.assertEqual(
            problems,
            [
                "production env file must set non-empty SBS_ACCOUNT_DELETION_INSTANCE_ID",
                "rendered Production runtime must set non-empty SBS_ACCOUNT_DELETION_INSTANCE_ID",
            ],
        )

    def test_development_may_omit_deletion_authority(self) -> None:
        problems = check_dotenv_to_rendered(
            {"SBS_ENVIRONMENT": "development", "SBS_ACCOUNT_DELETION_INSTANCE_ID": ""},
            rendered(instance_id="", environment="development"),
        )
        self.assertEqual(problems, [])

    def test_detects_process_override_of_environment_mode(self) -> None:
        dotenv = {"SBS_ENVIRONMENT": "development", "SBS_ACCOUNT_DELETION_INSTANCE_ID": ""}
        problems = check_dotenv_to_rendered(dotenv, rendered(instance_id=""))
        self.assertIn(
            "rendered Production runtime must set non-empty SBS_ACCOUNT_DELETION_INSTANCE_ID",
            problems,
        )
        self.assertEqual(
            sum("differs from env file for SBS_ENVIRONMENT" in problem for problem in problems),
            2,
        )


class ProductionImageIdentityTest(unittest.TestCase):
    def test_accepts_one_versioned_release_for_production(self) -> None:
        self.assertEqual(
            check_production_image_identity(
                {"SBS_ENVIRONMENT": "production"}, image_config(), rendered()
            ),
            [],
        )

    def test_accepts_digest_qualified_release_refs(self) -> None:
        self.assertEqual(
            check_production_image_identity(
                {"SBS_ENVIRONMENT": "production"},
                image_config(
                    backend=f"{BACKEND}@sha256:{DIGEST}",
                    web=f"{WEB}@sha256:{DIGEST}",
                ),
                rendered(),
            ),
            [],
        )

    def test_development_may_use_local_source_images(self) -> None:
        problems = check_production_image_identity(
            {"SBS_ENVIRONMENT": "development"},
            image_config(backend="sidebyside-backend:source-local", web="sidebyside-web:source-local", pull_policy="never"),
            rendered(environment="development"),
        )
        self.assertEqual(problems, [])

    def test_rendered_production_override_still_requires_release_images(self) -> None:
        problems = check_production_image_identity(
            {"SBS_ENVIRONMENT": "development"},
            image_config(backend="sidebyside-backend:source-local", web="sidebyside-web:source-local", pull_policy="never"),
            rendered(environment="production"),
        )
        self.assertGreater(len(problems), 0)

    def test_rejects_mutable_or_local_refs(self) -> None:
        for backend, web in (
            ("ghcr.io/baerenmarke90/eimir-backend:latest", WEB),
            ("ghcr.io/baerenmarke90/eimir-backend:main", WEB),
            ("sidebyside-backend:source-local", "sidebyside-web:source-local"),
        ):
            with self.subTest(backend=backend):
                self.assertGreater(
                    len(
                        check_production_image_identity(
                            {"SBS_ENVIRONMENT": "production"},
                            image_config(backend=backend, web=web),
                            rendered(),
                        )
                    ),
                    0,
                )

    def test_rejects_backend_role_divergence(self) -> None:
        problems = check_production_image_identity(
            {"SBS_ENVIRONMENT": "production"},
            image_config(worker="ghcr.io/baerenmarke90/eimir-backend:v0.1.1"),
            rendered(),
        )
        self.assertIn(
            "Production api/worker/migrate must use one exact backend image identity",
            problems,
        )

    def test_rejects_backend_web_version_divergence(self) -> None:
        problems = check_production_image_identity(
            {"SBS_ENVIRONMENT": "production"},
            image_config(web="ghcr.io/baerenmarke90/eimir-web:v0.1.1"),
            rendered(),
        )
        self.assertIn("Production backend and Web images must use one product release version", problems)

    def test_rejects_build_fallback_or_never_pull(self) -> None:
        problems = check_production_image_identity(
            {"SBS_ENVIRONMENT": "production"},
            image_config(build=True, pull_policy="never"),
            rendered(),
        )
        self.assertTrue(any("must not contain build configuration" in problem for problem in problems))
        self.assertTrue(any("pull_policy=always" in problem for problem in problems))


class RenderedToRunningTest(unittest.TestCase):
    def test_accepts_matching_running_containers(self) -> None:
        expected = rendered()
        running = {name: dict(environment) for name, environment in expected.items()}
        self.assertEqual(check_rendered_to_running(expected, running), [])

    def test_detects_stale_or_empty_runtime_value(self) -> None:
        expected = rendered()
        running = {name: dict(environment) for name, environment in expected.items()}
        running["api"]["SBS_ACCOUNT_DELETION_INSTANCE_ID"] = ""
        problems = check_rendered_to_running(expected, running)
        self.assertEqual(
            problems,
            ["running service api differs from rendered Compose for SBS_ACCOUNT_DELETION_INSTANCE_ID"],
        )
        self.assertNotIn(INSTANCE_ID, problems[0])

    def test_detects_missing_container(self) -> None:
        expected = rendered()
        running = {name: dict(environment) for name, environment in expected.items()}
        running["worker"] = None
        self.assertIn(
            "service worker has no inspectable Compose container",
            check_rendered_to_running(expected, running),
        )

    def test_parser_keeps_empty_environment_values(self) -> None:
        self.assertEqual(
            parse_container_environment(["A=one", "B=", "C=three=four"]),
            {"A": "one", "B": "", "C": "three=four"},
        )


if __name__ == "__main__":
    unittest.main()
