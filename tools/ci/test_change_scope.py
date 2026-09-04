#!/usr/bin/env python3
from __future__ import annotations

import unittest

from change_scope import SCOPES, classify_paths


class ChangeScopeTest(unittest.TestCase):
    def assert_scope(self, paths: list[str], *, enabled: set[str]) -> None:
        expected = {scope: scope in enabled for scope in SCOPES}
        self.assertEqual(classify_paths(paths), expected)

    def test_normal_docs_do_not_enable_expensive_gates(self) -> None:
        self.assert_scope(
            [
                "README.md",
                "docs/ROADMAP.md",
                "docs/IMPLEMENTATION-STATUS.md",
                "specification/PRODUCT-SPEC.md",
            ],
            enabled=set(),
        )

    def test_web_ui_change_does_not_enable_backend_or_container_gates(self) -> None:
        self.assert_scope(["web/src/App.tsx"], enabled=set())

    def test_android_change_does_not_enable_backend_gates(self) -> None:
        self.assert_scope(
            ["android/app/src/main/java/example/App.kt"],
            enabled=set(),
        )

    def test_backend_unit_test_only_enables_fast_backend_gate(self) -> None:
        self.assert_scope(
            ["backend/tests/test_config.py"],
            enabled={"backend"},
        )

    def test_backend_runtime_change_enables_postgres_integration(self) -> None:
        self.assert_scope(
            ["backend/src/sidebyside/memories/service.py"],
            enabled={"backend", "backend_integration"},
        )

    def test_backend_runtime_entrypoint_also_enables_deployment_gates(self) -> None:
        self.assert_scope(
            ["backend/src/sidebyside/main.py"],
            enabled={
                "backend",
                "backend_integration",
                "self_hosted",
                "deployment_guard",
            },
        )

    def test_compose_changes_only_enable_stack_and_recovery_gates(self) -> None:
        for path in ("compose.yaml", "compose.arcane.yaml"):
            with self.subTest(path=path):
                self.assert_scope(
                    [path],
                    enabled={"self_hosted", "deployment_guard", "recovery"},
                )

    def test_web_dockerfile_enables_build_and_deployment_gates(self) -> None:
        self.assert_scope(
            ["web/Dockerfile"],
            enabled={"self_hosted", "supply_chain", "deployment_guard"},
        )

    def test_backend_dependency_change_runs_backend_integration_and_supply_chain(self) -> None:
        self.assert_scope(
            ["backend/uv.lock"],
            enabled={"backend", "backend_integration", "supply_chain"},
        )

    def test_openapi_contract_enables_generated_client_check(self) -> None:
        self.assert_scope(
            ["backend/openapi.json"],
            enabled={"backend", "api_clients"},
        )

    def test_openapi_generator_only_enables_client_check(self) -> None:
        self.assert_scope(
            ["tools/openapi/generate.sh"],
            enabled={"api_clients"},
        )

    def test_dependency_inventory_only_enables_supply_chain(self) -> None:
        self.assert_scope(
            ["docs/DEPENDENCIES.md"],
            enabled={"supply_chain"},
        )

    def test_self_hosting_contract_enables_stack_deployment_and_recovery(self) -> None:
        for path in ("docs/SELF-HOSTING.md", "docs/ARCANE.md"):
            with self.subTest(path=path):
                self.assert_scope(
                    [path],
                    enabled={"self_hosted", "deployment_guard", "recovery"},
                )

    def test_migration_runs_backend_integration_and_recovery(self) -> None:
        self.assert_scope(
            ["backend/alembic/versions/0042_example.py"],
            enabled={"backend", "backend_integration", "recovery"},
        )

    def test_recovery_tooling_only_enables_recovery_gate(self) -> None:
        for path in (
            "scripts/self_hosted_recovery.py",
            "scripts/self_hosted_deletion_reconcile.py",
            "scripts/self_hosted_recovery_acceptance.py",
            "scripts/account_deletion_recovery_acceptance.py",
            "scripts/test_self_hosted_recovery.py",
            "scripts/test_self_hosted_deletion_reconcile.py",
            "docs/SELF-HOSTED-RECOVERY.md",
        ):
            with self.subTest(path=path):
                self.assert_scope([path], enabled={"recovery"})

    def test_deletion_runtime_surfaces_also_enable_recovery(self) -> None:
        for path in (
            "backend/src/sidebyside/identity/deletion.py",
            "backend/src/sidebyside/identity/deletion_journal.py",
            "backend/src/sidebyside/identity/deletion_reconcile.py",
        ):
            with self.subTest(path=path):
                self.assert_scope(
                    [path],
                    enabled={"backend", "backend_integration", "recovery"},
                )

    def test_filter_changes_fail_closed(self) -> None:
        self.assertTrue(all(classify_paths(["tools/ci/change_scope.py"]).values()))

    def test_ci_workflow_changes_fail_closed(self) -> None:
        self.assertTrue(all(classify_paths([".github/workflows/ci.yml"]).values()))

    def test_unknown_path_fails_closed(self) -> None:
        self.assertTrue(all(classify_paths(["future-build-system/config.toml"]).values()))

    def test_mixed_pr_combines_relevant_scopes(self) -> None:
        self.assert_scope(
            ["docs/ROADMAP.md", "web/src/App.tsx", "backend/tests/test_config.py"],
            enabled={"backend"},
        )

    def test_mixed_pr_cannot_hide_unknown_change_with_docs(self) -> None:
        result = classify_paths(["docs/ROADMAP.md", "future-build-system/config.toml"])
        self.assertTrue(all(result.values()))


if __name__ == "__main__":
    unittest.main()
