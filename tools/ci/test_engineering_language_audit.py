#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from engineering_language_audit import check_file


class EngineeringLanguageAuditTest(unittest.TestCase):
    def test_legacy_engineering_marker_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.md"
            path.write_text("## Zusammenfassung\n", encoding="utf-8")
            findings = check_file(path)
            self.assertEqual(len(findings), 1)
            self.assertIn("Zusammenfassung", findings[0])

    def test_english_engineering_text_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.md"
            path.write_text("## Summary\n", encoding="utf-8")
            self.assertEqual(check_file(path), [])

    def test_legacy_status_marker_is_allowed_as_migration_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.py"
            path.write_text('sample = "Aktueller `main`"\n', encoding="utf-8")
            self.assertEqual(check_file(path), [])


if __name__ == "__main__":
    unittest.main()
