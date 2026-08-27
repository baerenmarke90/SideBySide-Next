#!/usr/bin/env python3
"""Remove residual hybrid engineering language identified by the strict PR #219 audit."""

from __future__ import annotations

import io
import tokenize
from pathlib import Path

FILES = (
    Path("backend/tests/integration/test_attachments.py"),
    Path("backend/tests/integration/test_cloud_auth_flows.py"),
    Path("backend/tests/integration/test_places.py"),
    Path("backend/tests/integration/test_private_authorization.py"),
    Path("backend/tests/integration/test_wishes.py"),
)

IDENTIFIERS = {
    # Attachments
    "upload_hoch": "upload_and_finalize",
    "angelegt": "created",
    "verarbeite": "process_attachment",
    "test_upload_is_validiert_stripped_and_ready": "test_upload_is_validated_stripped_and_ready",
    "test_allowlist_aus_exif_remains_protected_payload": "test_exif_allowlist_remains_protected_payload",
    "test_status_is_public_projiziert": "test_status_is_publicly_projected",
    "test_video_is_until_zum_video_slice_rejected": "test_video_is_rejected_until_video_slice",
    "test_png_als_jpeg_angekuendigt_scheitert": "test_png_declared_as_jpeg_fails",
    "test_truncated_file_scheitert": "test_truncated_file_fails",
    "test_owner_reads_own_ungebundenen_upload": "test_owner_reads_own_unbound_upload",
    "test_parent_reference_verleiht_no_access": "test_parent_reference_grants_no_access",
    "test_expired_binding_window_sperrt_the_access": "test_expired_binding_window_blocks_access",
    "test_delete_macht_sofort_unsichtbar": "test_delete_makes_immediately_invisible",
    "test_delete_verlangt_aktuelle_version": "test_delete_requires_current_version",
    "test_cleanup_entfernt_original_and_thumbnail": "test_cleanup_removes_original_and_thumbnail",
    # Cloud auth
    "ADRESSE": "ADDRESS",
    # Places
    "GEHEIME_ADRESSE": "SECRET_ADDRESS",
    "erstelle": "create_place",
    "test_coordinates_koennen_wieder_entfernt_werden": "test_coordinates_can_be_removed_again",
    "test_a_place_aus_a_foreign_space_remains_unsichtbar": "test_place_from_foreign_space_remains_invisible",
    "test_a_id_aus_dem_other_space_remains_unsichtbar": "test_id_from_other_space_remains_invisible",
    "entfernt": "removed",
    # Privacy probe
    "CANARY_FREMD": "CANARY_FOREIGN",
}

# Wishes uses the same legacy helper names as Places, but its helper should
# remain domain-specific rather than becoming create_place.
WISH_IDENTIFIERS = {
    "erstelle": "create_wish",
    "angelegt": "created",
    "entfernt": "removed",
    "test_a_id_aus_dem_other_space_remains_unsichtbar": "test_id_from_other_space_remains_invisible",
}

TEXT_REPLACEMENTS: dict[Path, tuple[tuple[str, str], ...]] = {
    Path("backend/tests/integration/test_attachments.py"): (
        (
            '"""PostgreSQL/HTTP acceptance tests for the first media slice.\n\nSchwerpunkte: the Statusautomat, the Strippen after M2-D14, the\nOwner boundary and fail-closed behavior for everything that is not on the\nAllowlist is stored.\n"""',
            '"""PostgreSQL/HTTP acceptance tests for the first media slice.\n\nFocus: the attachment status machine, metadata stripping after M2-D14, and\nthe owner boundary with fail-closed handling for data outside the allowlist.\n"""',
        ),
        (
            '"Sign in, uebertragen, finalisieren; the volle Clientpfad."',
            '"Sign in, upload, and finalize through the full client path."',
        ),
        (
            "# No Plaintext field in the Table; the Capture timestamp is no\n        # sortierbares Metadatum geworden.",
            "# No plaintext field exists in the table; the capture timestamp did not\n        # become sortable metadata.",
        ),
        ("# No Storage-Interna after outside.", "# No storage internals are exposed."),
        (
            '"M2-D23: the Contract erlaubt it, this Lieferstand not."',
            '"M2-D23: the contract allows video, but this delivery slice does not."',
        ),
        (
            '"The declared Typ counts not; the magic bytes decide."',
            '"The declared type is not trusted; the magic bytes decide."',
        ),
    ),
}


def rewrite_identifiers(path: Path, mapping: dict[str, str]) -> None:
    text = path.read_text(encoding="utf-8")
    tokens: list[tokenize.TokenInfo] = []
    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        if token.type == tokenize.NAME and token.string in mapping:
            token = token._replace(string=mapping[token.string])
        tokens.append(token)
    path.write_text(tokenize.untokenize(tokens), encoding="utf-8")


def replace_text(path: Path, replacements: tuple[tuple[str, str], ...]) -> None:
    text = path.read_text(encoding="utf-8")
    for source, target in replacements:
        if source not in text:
            raise RuntimeError(f"Expected fragment not found in {path}: {source!r}")
        text = text.replace(source, target)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    for path in FILES:
        mapping = WISH_IDENTIFIERS if path.name == "test_wishes.py" else IDENTIFIERS
        rewrite_identifiers(path, mapping)
        replacements = TEXT_REPLACEMENTS.get(path)
        if replacements:
            replace_text(path, replacements)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
