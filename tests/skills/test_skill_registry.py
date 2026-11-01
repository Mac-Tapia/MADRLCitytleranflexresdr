"""Contract tests for the repository's auditable skill installation."""
import importlib.util
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_validator():
    path = ROOT / "tools/skills/validate_skills.py"
    assert path.is_file(), "Missing repository-local skill validator"
    spec = importlib.util.spec_from_file_location("skill_validator", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_repository_registry_is_valid():
    assert load_validator().validate_registry(ROOT) == []


def test_rejects_missing_license_and_wrong_name(tmp_path):
    skill = tmp_path / "example"
    skill.mkdir()
    (skill / "SKILL.md").write_text(
        "---\nname: other\ndescription: Test skill\n---\nRead only.\n", encoding="utf-8"
    )
    errors = load_validator().validate_skill(skill)
    assert any("name" in error for error in errors)
    assert any("license" in error.lower() for error in errors)


def test_rejects_outside_repository_and_duplicate_names(tmp_path):
    registry = {"skills": [
        {"name": "duplicate", "path": "../outside", "license": "MIT"},
        {"name": "duplicate", "path": "tools/skills/missing", "license": "MIT"},
    ]}
    errors = load_validator().validate_registry(tmp_path, registry)
    assert any("outside" in error for error in errors)
    assert any("duplicate" in error for error in errors)


def test_modified_vendor_file_is_detected(tmp_path):
    folder = tmp_path / "tools/skills/example"
    folder.mkdir(parents=True)
    (folder / "SKILL.md").write_text(
        "---\nname: example\ndescription: Test\n---\nChanged\n", encoding="utf-8"
    )
    (folder / "LICENSE.txt").write_text("MIT License", encoding="utf-8")
    registry = {"skills": [{
        "name": "example", "path": "tools/skills/example", "license": "MIT",
        "sha256": {"SKILL.md": "0" * 64},
    }]}
    assert any("hash" in error for error in load_validator().validate_registry(tmp_path, registry))


def test_rejects_empty_inventory(tmp_path):
    assert load_validator().validate_registry(tmp_path, {"skills": []})


def test_rejects_unregistered_canonical_skill(tmp_path):
    folder = tmp_path / "tools/skills/unreviewed"
    folder.mkdir(parents=True)
    (folder / "SKILL.md").write_text("unreviewed", encoding="utf-8")
    errors = load_validator().validate_registry(tmp_path, {"skills": []})
    assert any("unregistered" in error for error in errors)


def test_requires_exact_hash_coverage(tmp_path):
    folder = tmp_path / "tools/skills/example"
    folder.mkdir(parents=True)
    (folder / "SKILL.md").write_text(
        "---\nname: example\ndescription: Test\n---\nRead only.\n", encoding="utf-8"
    )
    (folder / "LICENSE.txt").write_text("MIT License", encoding="utf-8")
    record = {"name": "example", "path": "tools/skills/example", "license": "MIT"}
    assert any("hash" in error for error in load_validator().validate_registry(
        tmp_path, {"skills": [record]}
    ))
    record["sha256"] = {"SKILL.md": hashlib.sha256((folder / "SKILL.md").read_bytes()).hexdigest()}
    assert any("coverage" in error for error in load_validator().validate_registry(
        tmp_path, {"skills": [record]}
    ))


def test_discovery_rejects_stale_entry_without_removing_it(tmp_path):
    surface = tmp_path / "discovery"
    surface.mkdir()
    (surface / "unexpected").mkdir()
    errors = load_validator().validate_discovery(surface, {"expected": tmp_path / "canonical"})
    assert any("unexpected" in error for error in errors)
    assert (surface / "unexpected").is_dir()


def test_discovery_rejects_copy_instead_of_link(tmp_path):
    surface = tmp_path / "discovery"
    surface.mkdir()
    (surface / "example").mkdir()
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    errors = load_validator().validate_discovery(surface, {"example": canonical})
    assert any("wrong discovery target" in error for error in errors)
