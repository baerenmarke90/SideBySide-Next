#!/usr/bin/env python3
"""Unit tests for runtime environment drift detection."""

from __future__ import annotations

import unittest

from scripts.check_runtime_environment import (
    check_dotenv_to_rendered,
    check_rendered_to_running,
    parse_container_environment,
)

INSTANCE_ID = "9e8bd148-d0f3-4568-9319-5b21a29fbdf3"


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
