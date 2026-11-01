from __future__ import annotations

import re
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
    assert baseline["repository"]["branch"].startswith("codex/")

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
