from __future__ import annotations

from pathlib import Path

from tools.ops.audit_closed_services_and_secrets import audit_closed_services


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_audit_blocks_secrets_and_required_closed_runtime_without_leaking_values(
    tmp_path: Path,
) -> None:
    secret_value = "oauth-super-secret-value"
    _write(tmp_path / "config/token.json", '{"access_token": "' + secret_value + '"}')
    _write(tmp_path / "browser-profile/Default/Cookies", "browser-cookie-secret")
    _write(tmp_path / "app/runtime.py", "import wandb\nwandb.init()\n")
    _write(
        tmp_path / "docs/history.md",
        "Historical evidence was stored in Google Drive and reviewed in NotebookLM.",
    )

    manifest = audit_closed_services(tmp_path)

    assert manifest["ok"] is False
    categories = [finding["category"] for finding in manifest["findings"]]
    assert categories.count("critical") == 3
    assert categories.count("documentation_only") == 2
    serialized = repr(manifest)
    assert secret_value not in serialized
    assert "browser-cookie-secret" not in serialized
    for finding in manifest["findings"]:
        assert len(finding["path_sha256"]) == 64


def test_legacy_connectors_are_excluded_not_treated_as_required_runtime(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / "tools/skills/google-drive-mcp/data/credentials.json",
        '{"client_secret": "never-print-me"}',
    )
    _write(
        tmp_path / "tools/skills/notebooklm-mcp/server.py",
        "# optional legacy connector for NotebookLM\n",
    )

    manifest = audit_closed_services(tmp_path)

    assert manifest["ok"] is True
    assert {finding["category"] for finding in manifest["findings"]} == {
        "excluded_legacy"
    }
    assert "never-print-me" not in repr(manifest)


def test_project_history_external_code_and_tests_do_not_become_runtime_blockers(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / "CityLearn/scripts/training.py",
        "# legacy optional Google Drive persistence\n",
    )
    _write(tmp_path / "external/backend/runner.py", "import wandb\n")
    _write(
        tmp_path / "docs/workflow_manifest.json",
        '{"historical_store": "Google Drive"}',
    )
    _write(
        tmp_path / "tests/test_fixture.py",
        'FIXTURE = "NotebookLM"\n',
    )
    _write(
        tmp_path / ".cursor/mcp.json",
        '{"mcpServers": {"notebooklm": {"command": "closed"}}}',
    )

    manifest = audit_closed_services(tmp_path)
    by_path = {}
    for finding in manifest["findings"]:
        by_path.setdefault(finding["path"], set()).add(finding["category"])

    assert by_path["CityLearn/scripts/training.py"] == {"excluded_legacy"}
    assert by_path["external/backend/runner.py"] == {"excluded_legacy"}
    assert by_path["docs/workflow_manifest.json"] == {"documentation_only"}
    assert by_path["tests/test_fixture.py"] == {"documentation_only"}
    assert by_path[".cursor/mcp.json"] == {"critical"}


def test_inventory_that_declares_a_connector_disabled_is_not_a_runtime_blocker(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / "tools/skills/registry.yaml",
        '{"connectors": [{"name": "notebooklm-mcp", "status": "optional_legacy", '
        '"required": false}]}\n',
    )

    manifest = audit_closed_services(tmp_path)

    assert manifest["ok"] is True
    assert [finding["category"] for finding in manifest["findings"]] == ["documentation_only"]


def test_generated_audit_does_not_flag_its_own_previous_findings(tmp_path: Path) -> None:
    _write(
        tmp_path / "data/audits/closed_services_and_secrets.json",
        '{"findings": [{"kind": "notebooklm", "category": "excluded_legacy"}]}',
    )

    manifest = audit_closed_services(tmp_path)

    assert manifest["ok"] is True
    assert manifest["findings"] == []
