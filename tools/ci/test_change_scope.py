#!/usr/bin/env python3
from __future__ import annotations

import unittest

from change_scope import classify_paths


class ChangeScopeTest(unittest.TestCase):
    def test_normal_docs_do_not_enable_expensive_gates(self) -> None:
        self.assertEqual(
            classify_paths(
                [
                    "README.md",
                    "docs/ROADMAP.md",
                    "docs/IMPLEMENTATION-STATUS.md",
                    "specification/PRODUCT-SPEC.md",
                ]
            ),
            {
                "backend": False,
                "self_hosted": False,
                "supply_chain": False,
                "deployment_guard": False,
            },
        )

    def test_backend_change_enables_all_runtime_related_gates(self) -> None:
        self.assertEqual(
            classify_paths(["backend/src/sidebyside/main.py"]),
            {
                "backend": True,
                "self_hosted": True,
                "supply_chain": True,
                "deployment_guard": True,
            },
        )

    def test_compose_change_enables_runtime_but_not_supply_chain(self) -> None:
        result = classify_paths(["compose.yaml"])
        self.assertTrue(result["backend"])
        self.assertTrue(result["self_hosted"])
        self.assertTrue(result["deployment_guard"])
        self.assertFalse(result["supply_chain"])

    def test_web_source_change_enables_runtime_gates(self) -> None:
        self.assertEqual(
            classify_paths(["web/src/App.tsx"]),
            {
                "backend": True,
                "self_hosted": True,
                "supply_chain": False,
                "deployment_guard": True,
            },
        )

    def test_web_dockerfile_also_enables_supply_chain(self) -> None:
        self.assertTrue(all(classify_paths(["web/Dockerfile"]).values()))

    def test_dependency_inventory_only_enables_supply_chain(self) -> None:
        result = classify_paths(["docs/DEPENDENCIES.md"])
        self.assertFalse(result["backend"])
        self.assertFalse(result["self_hosted"])
        self.assertTrue(result["supply_chain"])
        self.assertFalse(result["deployment_guard"])

    def test_self_hosting_contract_enables_both_self_hosted_gates(self) -> None:
        result = classify_paths(["docs/SELF-HOSTING.md"])
        self.assertFalse(result["backend"])
        self.assertTrue(result["self_hosted"])
        self.assertFalse(result["supply_chain"])
        self.assertTrue(result["deployment_guard"])

    def test_filter_changes_fail_closed(self) -> None:
        self.assertTrue(all(classify_paths(["tools/ci/change_scope.py"]).values()))

    def test_unknown_path_fails_closed(self) -> None:
        self.assertTrue(all(classify_paths(["future-build-system/config.toml"]).values()))

    def test_mixed_pr_cannot_hide_backend_change_with_docs(self) -> None:
        result = classify_paths(["docs/ROADMAP.md", "backend/src/sidebyside/main.py"])
        self.assertTrue(all(result.values()))

    def test_mixed_pr_cannot_hide_unknown_change_with_docs(self) -> None:
        result = classify_paths(["docs/ROADMAP.md", "future-build-system/config.toml"])
        self.assertTrue(all(result.values()))


if __name__ == "__main__":
    unittest.main()
