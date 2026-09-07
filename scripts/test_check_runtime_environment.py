#!/usr/bin/env python3
"""Unit tests for runtime environment drift detection."""

from __future__ import annotations

import unittest

from scripts.check_runtime_environment import (
    check_dotenv_to_rendered,
    check_production_source_identity,
    check_rendered_to_running,
    parse_container_environment,
)

INSTANCE_ID = "11111111-2222-4333-8444-555555555555"
REVISION = "1234567890abcdef1234567890abcdef12345678"
OTHER_REVISION = "abcdef1234567890abcdef1234567890abcdef12"
REPOSITORY = "https://github.com/baerenmarke90/SideBySide-Next.git"


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
    return {
        "api": dict(common),
        "worker": dict(common),
        "demo-init": dict(common),
    }


def source_config(
    revision: str = REVISION,
    *,
    backend_ref: str | None = None,
    web_ref: str | None = None,
    build_revision: str | None = None,
) -> dict[str, object]:
    backend_ref = revision if backend_ref is None else backend_ref
    web_ref = revision if web_ref is None else web_ref
    build_revision = revision if build_revision is None else build_revision

    def build(subdir: str, ref: str) -> dict[str, object]:
        context = f"{REPOSITORY}#{ref}:{subdir}" if ref else f"./{subdir}"
        return {"context": context, "args": {"SBS_BUILD_REVISION": build_revision}}

    backend_build = build("backend", backend_ref)
    return {
        "services": {
            "migrate": {"build": dict(backend_build)},
            "demo-init": {"build": dict(backend_build)},
            "api": {"build": dict(backend_build)},
            "worker": {"build": dict(backend_build)},
            "web": {"build": build("web", web_ref)},
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
        self.assertEqual(len(problems), 4)
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
            3,
        )


class ProductionSourceIdentityTest(unittest.TestCase):
    def test_accepts_one_full_sha_for_all_production_builds(self) -> None:
        problems = check_production_source_identity(
            {"SBS_ENVIRONMENT": "production"}, source_config(), rendered()
        )
        self.assertEqual(problems, [])

    def test_development_may_use_main(self) -> None:
        problems = check_production_source_identity(
            {"SBS_ENVIRONMENT": "development"},
            source_config(backend_ref="main", web_ref="main", build_revision="main"),
            rendered(environment="development"),
        )
        self.assertEqual(problems, [])

    def test_rendered_production_override_still_requires_immutable_source(self) -> None:
        problems = check_production_source_identity(
            {"SBS_ENVIRONMENT": "development"},
            source_config(backend_ref="main", web_ref="main", build_revision="main"),
            rendered(environment="production"),
        )
        self.assertGreater(len(problems), 0)

    def test_rejects_mutable_or_incomplete_source_refs(self) -> None:
        for ref in ("main", "release/1.0", "v1.0.0", REVISION[:12], ""):
            with self.subTest(ref=ref or "blank/default"):
                problems = check_production_source_identity(
                    {"SBS_ENVIRONMENT": "production"},
                    source_config(backend_ref=ref, web_ref=ref, build_revision=ref),
                    rendered(),
                )
                self.assertGreater(len(problems), 0)

    def test_rejects_mismatched_backend_and_web_refs(self) -> None:
        problems = check_production_source_identity(
            {"SBS_ENVIRONMENT": "production"},
            source_config(web_ref=OTHER_REVISION),
            rendered(),
        )
        self.assertIn(
            "Production Backend/Web build contexts and SBS_BUILD_REVISION must use the same commit SHA",
            problems,
        )

    def test_rejects_mismatched_declared_revision(self) -> None:
        problems = check_production_source_identity(
            {"SBS_ENVIRONMENT": "production"},
            source_config(build_revision=OTHER_REVISION),
            rendered(),
        )
        self.assertIn(
            "Production Backend/Web build contexts and SBS_BUILD_REVISION must use the same commit SHA",
            problems,
        )

    def test_rejects_uppercase_sha(self) -> None:
        uppercase = REVISION.upper()
        problems = check_production_source_identity(
            {"SBS_ENVIRONMENT": "production"},
            source_config(backend_ref=uppercase, web_ref=uppercase, build_revision=uppercase),
            rendered(),
        )
        self.assertGreater(len(problems), 0)


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
            [
                "running service api differs from rendered Compose for "
                "SBS_ACCOUNT_DELETION_INSTANCE_ID"
            ],
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
