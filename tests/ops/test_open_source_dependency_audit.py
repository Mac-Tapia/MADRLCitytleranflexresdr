from __future__ import annotations

from pathlib import Path

from tools.ops.audit_open_source_dependencies import audit_dependencies


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
