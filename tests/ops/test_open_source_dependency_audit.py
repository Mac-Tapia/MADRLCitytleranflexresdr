from __future__ import annotations

from pathlib import Path

from tools.ops.audit_open_source_dependencies import audit_dependencies, license_file_candidates
from uc3m.governance.open_source import classify_license_text


def _fixture_with_submodule(tmp_path: Path, license_text: str) -> Path:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "fixture"\ndependencies = ["numpy>=1.23"]\n',
        encoding="utf-8",
    )
    (tmp_path / ".gitmodules").write_text(
        '[submodule "external/reference"]\n'
        "\tpath = external/reference\n"
        "\turl = https://github.com/example/reference.git\n",
        encoding="utf-8",
    )
    (tmp_path / "external/reference").mkdir(parents=True)
    (tmp_path / "external/reference/LICENSE").write_text(license_text, encoding="utf-8")
    registry = tmp_path / "registry.yaml"
    registry.write_text("repositories: []\n", encoding="utf-8")
    return registry


def _roles(tmp_path: Path, role: str) -> Path:
    roles = tmp_path / "roles.yaml"
    roles.write_text(
        'schema_version: "1.0"\n'
        "submodules:\n"
        "  external/reference:\n"
        f"    role: {role}\n"
        "    evidence: fixture\n",
        encoding="utf-8",
    )
    return roles


def test_reference_only_copyleft_submodule_is_recorded_without_blocking(
    tmp_path: Path,
) -> None:
    registry = _fixture_with_submodule(tmp_path, "GNU General Public License v3")

    manifest = audit_dependencies(tmp_path, registry, roles_path=_roles(tmp_path, "reference_only"))

    record = manifest["submodules"][0]
    assert record["role"] == "reference_only"
    assert record["status"] == "reference_only"
    assert record["policy_status"] == "review"
    assert record["license_spdx"] == "GPL-3.0-only"
    assert manifest["blockers"] == []


def test_runtime_copyleft_submodule_still_blocks(tmp_path: Path) -> None:
    registry = _fixture_with_submodule(tmp_path, "GNU General Public License v3")

    manifest = audit_dependencies(tmp_path, registry, roles_path=_roles(tmp_path, "runtime"))

    assert manifest["submodules"][0]["status"] == "review"
    assert manifest["blockers"][0]["reason"] == "copyleft_compatibility_review"


def test_submodule_without_declared_role_fails_closed_as_runtime(tmp_path: Path) -> None:
    registry = _fixture_with_submodule(tmp_path, "GNU General Public License v3")
    roles = tmp_path / "roles.yaml"
    roles.write_text('schema_version: "1.0"\nsubmodules: {}\n', encoding="utf-8")

    manifest = audit_dependencies(tmp_path, registry, roles_path=roles)

    assert manifest["submodules"][0]["role"] == "runtime"
    assert manifest["ok"] is False


def test_declared_packages_take_license_from_installed_metadata(tmp_path: Path) -> None:
    registry = _fixture_with_submodule(tmp_path, "MIT License")

    manifest = audit_dependencies(
        tmp_path,
        registry,
        roles_path=_roles(tmp_path, "runtime"),
        package_resolver=lambda name: {"version": "1.23.5", "license_spdx": "BSD-3-Clause"},
    )

    package = manifest["packages"][0]
    assert package["name"] == "numpy"
    assert package["version"] == "1.23.5"
    assert package["license_spdx"] == "BSD-3-Clause"
    assert package["status"] == "allow"


def test_uninstalled_declared_package_stays_unverified(tmp_path: Path) -> None:
    registry = _fixture_with_submodule(tmp_path, "MIT License")

    manifest = audit_dependencies(
        tmp_path,
        registry,
        roles_path=_roles(tmp_path, "runtime"),
        package_resolver=lambda name: None,
    )

    assert manifest["packages"][0]["status"] == "declared_unverified"


def test_license_text_classifier_distinguishes_bsd_variants() -> None:
    bsd = (
        "Redistribution and use in source and binary forms, with or without "
        "modification, are permitted provided that the following conditions are met:"
    )
    assert classify_license_text(bsd) == "BSD-2-Clause"
    assert classify_license_text(bsd + " Neither the name of the copyright holder") == (
        "BSD-3-Clause"
    )
    assert classify_license_text("Licensed under the Apache License, Version 2.0") == (
        "Apache-2.0"
    )
    assert classify_license_text("all rights reserved") == "NOASSERTION"


def test_license_text_classifier_is_not_fooled_by_secondary_gpl_mentions() -> None:
    mpl = (
        "Mozilla Public License Version 2.0 ... Secondary License means either the "
        "GNU General Public License, Version 2.0"
    )
    psf = (
        "PYTHON SOFTWARE FOUNDATION LICENSE VERSION 2 ... see the "
        "GNU General Public License for comparison"
    )
    assert classify_license_text(mpl) == "MPL-2.0"
    assert classify_license_text(psf) == "PSF-2.0"
    lgpl = (
        "GNU LESSER GENERAL PUBLIC LICENSE Version 2.1 ... the GNU General Public License"
    )
    assert classify_license_text(lgpl) == "LGPL-2.1-only"


def test_package_license_prefers_the_distribution_own_license_file() -> None:
    files = [
        "adodbapi/license.txt",
        "pywin32-311.dist-info/LICENSE.txt",
        "win32/license.txt",
    ]
    assert license_file_candidates(files)[0] == "pywin32-311.dist-info/LICENSE.txt"
    assert license_file_candidates(["pkg/README.md"]) == []


def test_audit_classifies_research_repositories_and_rejects_duplicates(
    tmp_path: Path,
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "fixture"\ndependencies = ["numpy>=1.23"]\n',
        encoding="utf-8",
    )
    (tmp_path / ".gitmodules").write_text(
        '[submodule "existing"]\n'
        "\tpath = external/existing\n"
        "\turl = https://github.com/example/existing.git\n",
        encoding="utf-8",
    )
    (tmp_path / "external/existing").mkdir(parents=True)
    (tmp_path / "external/existing/LICENSE").write_text("MIT License", encoding="utf-8")

    registry = tmp_path / "registry.yaml"
    registry.write_text(
        "repositories:\n"
        "  - name: C-MORL\n"
        "    url: https://github.com/example/c-morl.git\n"
        "    license_spdx: null\n"
        "    decision: reference_only\n"
        "  - name: MO-Gymnasium\n"
        "    url: https://github.com/Farama-Foundation/MO-Gymnasium.git\n"
        "    license_spdx: MIT\n"
        "    decision: candidate\n"
        "  - name: MORL-Baselines\n"
        "    url: https://github.com/LucasAlegre/morl-baselines.git\n"
        "    license_spdx: MIT\n"
        "    decision: candidate\n"
        "  - name: duplicate\n"
        "    url: https://github.com/example/existing.git\n"
        "    license_spdx: MIT\n"
        "    decision: candidate\n",
        encoding="utf-8",
    )

    manifest = audit_dependencies(tmp_path, registry)

    by_name = {entry["name"]: entry for entry in manifest["research_repositories"]}
    assert by_name["C-MORL"]["status"] == "reference_only"
    assert by_name["C-MORL"]["blocks"] is False
    assert by_name["MO-Gymnasium"]["status"] == "candidate"
    assert by_name["MORL-Baselines"]["status"] == "candidate"
    assert by_name["duplicate"]["status"] == "rejected"
    assert by_name["duplicate"]["reason"] == "duplicate_existing_submodule"


def test_required_submodule_without_local_license_blocks_acceptance(
    tmp_path: Path,
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "fixture"\ndependencies = []\n', encoding="utf-8"
    )
    (tmp_path / ".gitmodules").write_text(
        '[submodule "unlicensed"]\n'
        "\tpath = external/unlicensed\n"
        "\turl = https://github.com/example/unlicensed.git\n",
        encoding="utf-8",
    )
    (tmp_path / "external/unlicensed").mkdir(parents=True)
    registry = tmp_path / "registry.yaml"
    registry.write_text("repositories: []\n", encoding="utf-8")

    manifest = audit_dependencies(tmp_path, registry)

    assert manifest["ok"] is False
    assert manifest["submodules"][0]["status"] == "blocked"
    assert manifest["submodules"][0]["reason"] == "missing_local_license"
