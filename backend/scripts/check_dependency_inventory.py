"""Gleicht direkte Abhaengigkeiten mit Lock-Installation und Dokumentation ab."""

from __future__ import annotations

import argparse
import re
import tomllib
from importlib.metadata import PackageNotFoundError, metadata, version
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

MARKDOWN_ROW = re.compile(
    r"^\|\s*(?P<name>[^|]+?)\s*\|\s*(?P<version>[^|]+?)\s*\|\s*PyPI\s*\|"
    r"\s*(?P<license>[^|]+?)\s*\|$"
)


def _dependency_names(pyproject_path: Path) -> set[str]:
    with pyproject_path.open("rb") as handle:
        project = tomllib.load(handle)

    requirements = list(project["project"]["dependencies"])
    for group in project.get("dependency-groups", {}).values():
        requirements.extend(group)
    return {canonicalize_name(Requirement(value).name) for value in requirements}


def _documented_dependencies(documentation_path: Path) -> dict[str, tuple[str, str]]:
    result: dict[str, tuple[str, str]] = {}
    for raw_line in documentation_path.read_text(encoding="utf-8").splitlines():
        match = MARKDOWN_ROW.match(raw_line)
        if match is None:
            continue
        name = canonicalize_name(Requirement(match.group("name").strip(" `")).name)
        documented_version = match.group("version").strip(" `")
        documented_license = match.group("license").strip(" `*")
        result[name] = (documented_version, documented_license)
    return result


def _installed_license(package_name: str) -> str:
    package_metadata = metadata(package_name)
    license_expression = package_metadata.get("License-Expression")
    if license_expression:
        return license_expression.strip()
    legacy_license = package_metadata.get("License")
    if legacy_license:
        return legacy_license.strip()
    return ""


def check_inventory(pyproject_path: Path, documentation_path: Path) -> list[str]:
    required = _dependency_names(pyproject_path)
    documented = _documented_dependencies(documentation_path)
    errors: list[str] = []

    for package_name in sorted(required):
        entry = documented.get(package_name)
        if entry is None:
            errors.append(f"{package_name}: fehlt in {documentation_path}")
            continue
        documented_version, documented_license = entry
        try:
            installed_version = version(package_name)
            installed_license = _installed_license(package_name)
        except PackageNotFoundError:
            errors.append(f"{package_name}: ist in der gesperrten Umgebung nicht installiert")
            continue
        if documented_version != installed_version:
            errors.append(
                f"{package_name}: dokumentiert {documented_version}, "
                f"installiert {installed_version}"
            )
        if documented_license != installed_license:
            errors.append(
                f"{package_name}: Lizenz dokumentiert {documented_license!r}, "
                f"Paketmetadaten {installed_license!r}"
            )

    unexpected = sorted(set(documented) - required)
    for package_name in unexpected:
        errors.append(
            f"{package_name}: als PyPI-Abhaengigkeit dokumentiert, aber nicht direkt deklariert"
        )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("documentation", type=Path)
    parser.add_argument("--pyproject", type=Path, default=Path("pyproject.toml"))
    arguments = parser.parse_args()
    errors = check_inventory(arguments.pyproject, arguments.documentation)
    if errors:
        print("Abhaengigkeitsinventar ist inkonsistent:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Abhaengigkeitsinventar stimmt mit Installation und Paketmetadaten ueberein.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
