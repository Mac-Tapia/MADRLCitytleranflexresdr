from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from tools.ops.capture_modernization_baseline import capture_baseline


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_capture_baseline_records_repository_identity_and_auditable_state() -> None:
    baseline = capture_baseline(PROJECT_ROOT)

    assert baseline["schema_version"] == "1.0"
    assert baseline["repository"]["root"] == "D:/MADRLCitytleranflexresdr"
    assert baseline["repository"]["origin"] == (
        "https://github.com/Mac-Tapia/MADRLCitytleranflexresdr.git"
    )
    current_branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert baseline["repository"]["branch"] == current_branch

    changes = baseline["working_tree"]
    assert set(changes) == {
        "tracked_modified",
        "tracked_deleted",
        "tracked_added",
        "untracked",
        "renamed",
        "conflicted",
        "total",
    }
    assert changes["total"] >= sum(
        changes[key]
        for key in (
            "tracked_modified",
            "tracked_deleted",
            "tracked_added",
            "untracked",
            "renamed",
            "conflicted",
        )
    )

    assert isinstance(baseline["submodules"], list)
    for submodule in baseline["submodules"]:
        assert re.fullmatch(r"[0-9a-f]{40}", submodule["commit"])
        assert not Path(submodule["path"]).is_absolute()

    hashes = baseline["canonical_files"]
    assert "README.md" in hashes
    assert "pyproject.toml" in hashes
    assert re.fullmatch(r"[0-9a-f]{64}", hashes["README.md"]["sha256"])
    assert hashes["README.md"]["size_bytes"] > 0

    serialized = repr(baseline).lower()
    assert "access_token" not in serialized
    assert "refresh_token" not in serialized
    assert "client_secret" not in serialized


def test_capture_baseline_rejects_any_other_repository_root(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unexpected project root"):
        capture_baseline(tmp_path)


def test_source_change_invalidates_acceptance_cut(tmp_path: Path) -> None:
    from tools.ops.capture_modernization_baseline import compare_cut, hash_sources

    (tmp_path / "uc3m").mkdir()
    module = tmp_path / "uc3m" / "module.py"
    module.write_text("VALUE = 1\n", encoding="utf-8")
    before = hash_sources(tmp_path, roots=("uc3m",))
    module.write_text("VALUE = 2\n", encoding="utf-8")
    after = hash_sources(tmp_path, roots=("uc3m",))

    cut = compare_cut(before, after, suite_passed=True)

    assert cut["source_state_stable"] is False
    assert cut["integral_suite_accepted"] is False
    assert cut["changed_paths"] == ["uc3m/module.py"]


def test_stable_cut_with_passing_suite_is_accepted(tmp_path: Path) -> None:
    from tools.ops.capture_modernization_baseline import compare_cut, hash_sources

    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_x.py").write_text("x = 1\r\n", encoding="utf-8")
    before = hash_sources(tmp_path, roots=("tests",))
    after = hash_sources(tmp_path, roots=("tests",))

    cut = compare_cut(before, after, suite_passed=True)

    assert cut["source_state_stable"] is True
    assert cut["integral_suite_accepted"] is True
    assert re.fullmatch(r"[0-9a-f]{64}", cut["source_digest"])
    assert compare_cut(before, after, suite_passed=False)["integral_suite_accepted"] is False
