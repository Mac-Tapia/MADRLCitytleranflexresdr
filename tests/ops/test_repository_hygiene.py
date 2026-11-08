from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MANIFEST = PROJECT_ROOT / "data/audits/repository_hygiene_manifest.json"

AGENT_NAME = re.compile(r"codex|cursor|copilot|claude", re.IGNORECASE)
# Configuration locations whose names the tools require (SPEC-012/FR-012.1).
AGENT_NAME_EXEMPT = (".claude/", ".cursor/", ".github/", "CLAUDE.md")
TEMPORARY = re.compile(r"(^|/)(_tmp_[^/]*|~\$[^/]*|\.git_commit_msg\.tmp)$")
ROOT_ALLOWED = {
    ".dockerignore",
    ".gitattributes",
    ".gitignore",
    ".gitmodules",
    ".markdownlint.json",
    ".markdownlintignore",
    "AGENTS.md",
    "CLAUDE.md",
    "CityLearn",
    "Dockerfile",
    "README.md",
    "PT_TAPIA_ZAMBRANO_v6_Iquitos_2.docx",  # owner-supplied canonical research plan; preserve bytes
    "cspell.json",
    "pyproject.toml",
    "pyrightconfig.json",
    "requirements.txt",
    "uv.lock",
}


def _tracked_paths() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        check=True,
    )
    return [path for path in result.stdout.decode("utf-8").split("\0") if path]


def test_tracked_paths_carry_no_agent_tool_names() -> None:
    offending = [
        path
        for path in _tracked_paths()
        if AGENT_NAME.search(path) and not path.startswith(AGENT_NAME_EXEMPT)
    ]
    assert offending == []


def test_no_temporary_files_are_tracked() -> None:
    assert [path for path in _tracked_paths() if TEMPORARY.search(path)] == []


def test_root_contains_only_project_files() -> None:
    root_entries = {path.split("/", 1)[0] for path in _tracked_paths() if "/" not in path}
    assert root_entries - ROOT_ALLOWED == set()


def test_package_sources_are_not_ignored() -> None:
    # A clone (Colab, CI) only gets tracked files; an ignored module breaks `import uc3m`.
    result = subprocess.run(
        ["git", "ls-files", "-z", "--others", "--ignored", "--exclude-standard", "--", "uc3m"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        check=True,
    )
    ignored = [p for p in result.stdout.decode("utf-8").split("\0") if p.endswith(".py")]
    assert ignored == []


def test_hygiene_manifest_records_recoverable_removals() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "1.0"
    assert manifest["spec"] == "SPEC-012"

    tracked = set(_tracked_paths())
    for entry in manifest["entries"]:
        assert entry["reason"]
        # Untracked local data was never in Git: there is nothing to recover from a commit.
        if entry["action"] != "removed" or entry.get("kind") == "untracked_data":
            continue
        assert re.fullmatch(r"[0-9a-f]{40}", entry["recover_from_commit"])
        removed = list(entry.get("git_blobs", {})) or entry.get("paths") or [entry["path"]]
        for path in removed:
            prefix = path.rstrip("/")
            assert not any(t == prefix or t.startswith(prefix + "/") for t in tracked)
