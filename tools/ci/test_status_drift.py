#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from status_drift import LIVING_STATUS_FILES, check_repository, validate_text


class StatusDriftTest(unittest.TestCase):
    def test_static_current_main_sha_is_rejected(self) -> None:
        errors = validate_text(
            Path("docs/IMPLEMENTATION-STATUS.md"),
            "Aktueller `main`: `a07830ce3c8963a54207765e841f9c3f87b0576e`\n",
        )
        self.assertEqual(len(errors), 1)
        self.assertIn("statischen 'Aktueller main'-SHA", errors[0])

    def test_closed_issue_marked_open_is_rejected(self) -> None:
        errors = validate_text(
            Path("docs/IMPLEMENTATION-STATUS.md"),
            "- [ ] **#59 — Security:** noch offen\n",
            lambda number: "closed" if number == 59 else "open",
        )
        self.assertEqual(len(errors), 1)
        self.assertIn("Issue #59", errors[0])

    def test_open_issue_marked_open_is_valid(self) -> None:
        errors = validate_text(
            Path("docs/IMPLEMENTATION-STATUS.md"),
            "- [ ] **#88 — Future:** Video\n",
            lambda _number: "open",
        )
        self.assertEqual(errors, [])

    def test_checked_issue_is_not_live_state_assertion(self) -> None:
        called = False

        def fetch(_number: int) -> str:
            nonlocal called
            called = True
            return "closed"

        errors = validate_text(
            Path("docs/IMPLEMENTATION-STATUS.md"),
            "- [x] **#59 — Security:** geliefert\n",
            fetch,
        )
        self.assertEqual(errors, [])
        self.assertFalse(called)

    def test_historical_reviews_are_not_scanned(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative_path in LIVING_STATUS_FILES:
                path = root / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("Status ohne statischen SHA.\n", encoding="utf-8")

            review = root / "docs/reviews/2026-08-26-g2-final-gate-review.md"
            review.parent.mkdir(parents=True, exist_ok=True)
            review.write_text(
                "Aktueller `main`: `0000000000000000000000000000000000000000`\n",
                encoding="utf-8",
            )

            self.assertEqual(check_repository(root), [])

    def test_missing_living_status_file_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / LIVING_STATUS_FILES[0]
            first.parent.mkdir(parents=True, exist_ok=True)
            first.write_text("Status.\n", encoding="utf-8")

            errors = check_repository(root)
            self.assertEqual(len(errors), 1)
            self.assertIn(str(LIVING_STATUS_FILES[1]), errors[0])


if __name__ == "__main__":
    unittest.main()
