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

    def test_common_english_article_is_not_a_german_marker(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.md"
            path.write_text(
                "An existing component is not selected merely because it exists.\n",
                encoding="utf-8",
            )
            self.assertEqual(check_file(path), [])

    def test_english_address_identifier_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.py"
            path.write_text(
                "def normalize_address(address: str) -> str:\n"
                "    return address.strip()\n",
                encoding="utf-8",
            )
            self.assertEqual(check_file(path), [])

    def test_english_domain_moment_identifier_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.py"
            path.write_text(
                "def load_heart_moment(heart_moment_id: str):\n"
                "    moment = heart_moment_id\n"
                "    return moment\n",
                encoding="utf-8",
            )
            self.assertEqual(check_file(path), [])

    def test_english_status_drift_term_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.md"
            path.write_text("Status-drift migration guard.\n", encoding="utf-8")
            self.assertEqual(check_file(path), [])

    def test_legacy_status_marker_is_allowed_as_migration_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.py"
            path.write_text('sample = "Aktueller `main`"\n', encoding="utf-8")
            self.assertEqual(check_file(path), [])

    def test_python_comment_and_identifier_are_audited(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.py"
            path.write_text(
                "# Die Pruefung bleibt technisch.\n"
                "def test_fehler_wird_abgewiesen():\n"
                "    pass\n",
                encoding="utf-8",
            )
            findings = check_file(path)
            self.assertGreaterEqual(len(findings), 2)

    def test_hybrid_identifiers_from_backend_migration_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.py"
            path.write_text(
                "def upload_hoch():\n"
                "    pass\n\n"
                "def test_png_als_jpeg_angekuendigt_scheitert():\n"
                "    pass\n\n"
                "CANARY_FREMD = b'fixture'\n",
                encoding="utf-8",
            )
            findings = check_file(path)
            self.assertEqual(len(findings), 3)
            self.assertTrue(any("upload_hoch" in finding for finding in findings))
            self.assertTrue(any("angekuendigt" in finding for finding in findings))
            self.assertTrue(any("CANARY_FREMD" in finding for finding in findings))

    def test_hybrid_engineering_prose_from_backend_migration_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.py"
            path.write_text(
                '"""Schwerpunkte: attachment status and metadata stripping."""\n'
                "# No Storage-Interna are exposed.\n",
                encoding="utf-8",
            )
            findings = check_file(path)
            self.assertEqual(len(findings), 2)

    def test_ordinary_product_literal_is_not_classified(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.py"
            path.write_text(
                'subject = "Dein Anmeldelink fuer SideBySide"\n'
                'body = "Nur fuer mich"\n',
                encoding="utf-8",
            )
            self.assertEqual(check_file(path), [])

    def test_exception_diagnostic_is_audited(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.py"
            path.write_text('raise ValueError("Der Wert ist ungueltig")\n', encoding="utf-8")
            findings = check_file(path)
            self.assertEqual(len(findings), 1)


if __name__ == "__main__":
    unittest.main()
