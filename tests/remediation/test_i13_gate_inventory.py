"""R008 real pytest collection/execution, in one bounded temporary Git cut."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest

from uc3m.application.training import gate_report as gr

REPO = Path(__file__).resolve().parents[2]
PLUGIN = "uc3m.application.training.gate_pytest"


def _guard():
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                    "scripts/verify_project_context.ps1"], cwd=REPO, check=True,
                   capture_output=True, text=True)


def _command(root, args, extra_env=None):
    env = dict(os.environ, PYTHONPATH=str(REPO), PYTEST_ADDOPTS="",
               PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTHONDONTWRITEBYTECODE="1")
    env.update(extra_env or {})
    result = subprocess.run([sys.executable, "-B", "-m", "pytest", *args], cwd=root, env=env,
                            capture_output=True, text=True)
    return result


def _invoke(root, folder, scope="tests/fresh_training", *, mode="execution", extra=(), inventory=None, extra_env=None,
            before=None):
    folder.mkdir(parents=True, exist_ok=True)
    context = folder / "context.json"
    before = gr.capture_context(root) if before is None else before
    context.write_text(json.dumps(before), encoding="utf-8")
    evidence = folder / (mode + ".json")
    args = [scope, "-q", "-p", "no:cacheprovider", "-p", PLUGIN, "--rootdir=" + str(root),
            "--confcutdir=" + str(root), "--gate-mode=" + mode, "--gate-scope=" + scope,
            "--gate-context=" + str(context), "--gate-evidence=" + str(evidence)]
    junit = folder / "junit.xml"
    if mode == "collection":
        args.append("--collect-only")
    else:
        args.append("--junitxml=" + str(junit))
        if inventory is not None:
            args.append("--gate-inventory=" + str(inventory))
    result = _command(root, args + list(extra), extra_env=extra_env)
    return result, evidence, junit, before


@pytest.fixture(scope="module")
def cut(tmp_path_factory):
    root = tmp_path_factory.mktemp("gate_repo").resolve()
    hooks = root / "empty_hooks"
    hooks.mkdir()
    _guard()
    subprocess.run(["git", "-c", "core.hooksPath=" + str(hooks), "init", "-q", str(root)], check=True)
    _guard()
    subprocess.run(["git", "-c", "core.hooksPath=" + str(hooks), "-c", "user.name=Gate temporary test",
                    "-c", "user.email=gate@example.invalid", "commit", "--allow-empty", "-qm", "isolated cut"],
                   cwd=root, check=True)
    fresh = root / "tests/fresh_training"
    fresh.mkdir(parents=True)
    # --rootdir does not prevent pytest from inheriting a parent's ini config.
    (root / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    (fresh / "test_values.py").write_text(
        "def test_one():\n    assert 1 + 1 == 2\n\ndef test_two():\n    assert 2 * 3 == 6\n", encoding="utf-8")
    # Legitimate run reordering must not change the exact multiset requirement.
    (root / "tests/conftest.py").write_text(
        "def pytest_collection_modifyitems(config, items):\n"
        "    if not config.option.collectonly:\n        items.reverse()\n", encoding="utf-8")
    (root / "uc3m").mkdir()
    (root / "uc3m/value.py").write_text("VALUE = 1\n", encoding="utf-8")
    return root


def _manifest(before):
    return {"campaign_id": "fresh_gate_v3", "spec_hash": "a" * 64,
            "identity": {**before, "source_git_head": before["git_head"]}}


@pytest.fixture(scope="module")
def complete(cut):
    folder = cut / "artifacts/full"
    collect, inventory, _, before = _invoke(cut, folder, mode="collection")
    assert collect.returncode == 0, collect.stdout + collect.stderr
    run, execution, junit, _ = _invoke(cut, folder, inventory=inventory)
    assert run.returncode == 0, run.stdout + run.stderr
    return cut, before, inventory, execution, junit


def _build(complete, *, collection=True, junit=None, before=None, exit_code=0):
    root, original, inventory, execution, original_junit = complete
    kwargs = {"collection": inventory} if collection else {}
    return gr.build_gate_report(root, junit or original_junit, exit_code, before or original,
                                manifest=_manifest(original), **kwargs)


def _write_gate(folder, report):
    path = folder / "gate.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    return path


def test_r008_any_single_junit_without_collection_is_never_full_fresh(cut):
    folder = cut / "artifacts/no_inventory"
    folder.mkdir(parents=True)
    junit = folder / "junit.xml"
    run = _command(cut, ["tests/fresh_training/test_values.py::test_one", "-q", "-p", "no:cacheprovider",
                          "--junitxml=" + str(junit)])
    assert run.returncode == 0
    before = gr.capture_context(cut)
    report = gr.build_gate_report(cut, junit, 0, before, manifest=_manifest(before))
    assert report["software_acceptance"] is False
    assert report["profile"] == "junit_only"
    assert not gr.verify_gate_report(_write_gate(folder, report), _manifest(before))


def test_r008_exact_independent_collection_and_reordered_run_are_valid(complete):
    root, before, inventory, execution, junit = complete
    report = _build(complete)
    assert report["schema_version"] == 3 and report["software_acceptance"] is True
    assert report["profile"] == "fresh"
    assert report["coverage"]["scope"] == "tests/fresh_training"
    assert report["coverage"]["complete"] is True
    assert len(report["coverage"]["nodeids"]) == 2
    collected = json.loads(inventory.read_text())["nodeids"]
    executed = json.loads(execution.read_text())["nodeids"]
    assert executed == list(reversed(collected))
    assert gr.verify_gate_report(_write_gate(junit.parent, report), _manifest(before))


def test_r008_collect_two_but_run_one_is_rejected(complete):
    root, before, inventory, _, _ = complete
    run, execution, junit, _ = _invoke(root, root / "artifacts/subset", extra=("-k", "one"), inventory=inventory)
    report = gr.build_gate_report(root, junit, run.returncode, before, collection=inventory,
                                  manifest=_manifest(before))
    assert report["software_acceptance"] is False
    assert report["coverage"]["complete"] is False


def test_r008_filtered_collection_is_rejected(cut):
    result, inventory, _, before = _invoke(cut, cut / "artifacts/filtered", mode="collection", extra=("-k", "one"))
    assert result.returncode != 0
    payload = json.loads(inventory.read_text())
    assert payload["complete"] is False and payload["deselected"] == 1


@pytest.mark.parametrize("mutation", ["duplicate", "missing", "unknown", "property_missing"])
def test_r008_junit_nodeid_multiset_must_be_exact(complete, tmp_path, mutation):
    root, before, inventory, execution, junit = complete
    folder = root / "artifacts" / ("multiset_" + mutation)
    folder.mkdir()
    tree = ET.parse(junit)
    suite = next(tree.getroot().iter("testsuite"))
    cases = list(suite.iter("testcase"))
    def node_property(case):
        return next(p for p in case.findall("properties/property") if p.get("name") == "gate_nodeid")
    if mutation == "duplicate":
        node_property(cases[1]).set("value", node_property(cases[0]).get("value"))
    elif mutation == "unknown":
        node_property(cases[1]).set("value", "tests/fresh_training/test_values.py::test_unknown")
    elif mutation == "property_missing":
        cases[0].find("properties").remove(node_property(cases[0]))
    else:
        suite.remove(cases[0])
        suite.set("tests", "1")
    changed = folder / "junit.xml"
    tree.write(changed, encoding="utf-8")
    # Alter the real sidecar's XML hash too: rejection must still follow from
    # IDs/binding, rather than only a stale hash masking the multiset defect.
    run_record = json.loads(execution.read_text())
    run_record["junit_sha256"] = hashlib.sha256(changed.read_bytes()).hexdigest()
    (folder / "execution.json").write_text(json.dumps(run_record), encoding="utf-8")
    report = gr.build_gate_report(root, changed, 0, before, collection=inventory, manifest=_manifest(before))
    assert report["software_acceptance"] is False
    if mutation != "property_missing":
        assert any("multiset" in reason for reason in report["reasons"])


@pytest.mark.parametrize("field", ["collection", "execution", "junit", "embedded_collection", "source_before", "schema2"])
def test_r008_offline_readback_rejects_tampering(complete, field):
    root, before, inventory, execution, junit = complete
    report = _build(complete)
    folder = root / "artifacts" / ("tamper_" + field)
    folder.mkdir()
    for path in (inventory, execution, junit):
        (folder / path.name).write_bytes(path.read_bytes())
    report["collection"]["path"] = inventory.name
    report["execution"]["path"] = execution.name
    if field in {"collection", "execution", "junit"}:
        path = folder / {"collection": inventory.name, "execution": execution.name, "junit": junit.name}[field]
        path.write_bytes(path.read_bytes() + b" ")
    elif field == "embedded_collection":
        report["collection"]["payload"]["nodeids"].pop()
    elif field == "source_before":
        report["source_before"]["source_sha256"] = "0" * 64
    else:
        report["schema_version"] = 2
    gate = _write_gate(folder, report)
    assert not gr.verify_gate_report(gate, _manifest(before))


def test_r008_repository_scope_is_explicit_and_includes_fresh(cut):
    folder = cut / "artifacts/repository"
    collect, inventory, _, before = _invoke(cut, folder, scope="tests", mode="collection")
    assert collect.returncode == 0, collect.stdout + collect.stderr
    run, execution, junit, _ = _invoke(cut, folder, scope="tests", inventory=inventory)
    assert run.returncode == 0, run.stdout + run.stderr
    report = gr.build_gate_report(cut, junit, 0, before, collection=inventory, manifest=_manifest(before))
    assert report["profile"] == "repository"
    assert report["coverage"]["scope"] == "tests" and report["coverage"]["fresh_nodeids"]
    assert gr.verify_gate_report(_write_gate(folder, report), _manifest(before))


def test_r008_source_change_after_collection_rejected(complete):
    root, before, inventory, _, junit = complete
    value = root / "uc3m/value.py"
    original = value.read_bytes()
    try:
        value.write_text("VALUE = 2\n", encoding="utf-8")
        report = _build(complete)
        assert not report["software_acceptance"] and not report["source_state_stable"]
    finally:
        value.write_bytes(original)


@pytest.mark.parametrize("outcome", ["skip", "xfail", "xpass"])
def test_r008_omissions_outside_fresh_reject_repository_gate(cut, outcome):
    test = cut / "tests/test_external_outcome.py"
    bodies = {
        "skip": "import pytest\n\ndef test_extra():\n    pytest.skip('explicit omission')\n",
        "xfail": "import pytest\n\ndef test_extra():\n    pytest.xfail('explicit omission')\n",
        "xpass": "import pytest\n\n@pytest.mark.xfail(strict=False)\ndef test_extra():\n    assert True\n",
    }
    test.write_text(bodies[outcome], encoding="utf-8")
    try:
        folder = cut / "artifacts" / ("outside_" + outcome)
        collect, inventory, _, before = _invoke(cut, folder, scope="tests", mode="collection")
        assert collect.returncode == 0, collect.stdout + collect.stderr
        run, execution, junit, _ = _invoke(cut, folder, scope="tests", inventory=inventory)
        assert run.returncode != 0
        report = gr.build_gate_report(cut, junit, run.returncode, before, collection=inventory,
                                      manifest=_manifest(before))
        assert report["software_acceptance"] is False
        assert json.loads(execution.read_text())["omissions"]["skipped" if outcome == "skip" else outcome] > 0
    finally:
        test.unlink()


def test_r008_collection_errors_are_retained_and_rejected(cut):
    test = cut / "tests/fresh_training/test_syntax_error.py"
    test.write_text("def broken(\n", encoding="utf-8")
    try:
        result, inventory, _, before = _invoke(cut, cut / "artifacts/collect_error", mode="collection")
        assert result.returncode != 0
        payload = json.loads(inventory.read_text())
        assert payload["complete"] is False and payload["collection_errors"] > 0
    finally:
        test.unlink()


def test_r008_collection_source_drift_stops_before_execution(cut):
    test = cut / "tests/fresh_training/test_import_drift.py"
    value = cut / "uc3m/value.py"
    original = value.read_bytes()
    test.write_text("from pathlib import Path\n"
                    "(Path(__file__).parents[2]/'uc3m/value.py').write_text('VALUE = 9\\n')\n"
                    "def test_drift():\n    assert True\n", encoding="utf-8")
    try:
        result, inventory, _, _ = _invoke(cut, cut / "artifacts/collect_drift", mode="collection")
        assert result.returncode != 0
        payload = json.loads(inventory.read_text())
        assert payload["complete"] is False
        assert payload["source_before"] != payload["source_after"]
    finally:
        test.unlink()
        value.write_bytes(original)


def test_r008_environment_filter_cannot_certify_collection(cut):
    result, inventory, _, _ = _invoke(cut, cut / "artifacts/env_filter", mode="collection",
                                      extra_env={"PYTEST_ADDOPTS": "-k one"})
    assert result.returncode != 0
    payload = json.loads(inventory.read_text())
    assert payload["complete"] is False and "PYTEST_ADDOPTS" in payload["filters"]


def test_r008_ini_filter_is_recorded_and_cannot_certify_collection(cut):
    ini = cut / "pytest.ini"
    ini.write_text("[pytest]\naddopts = -k one\n", encoding="utf-8")
    try:
        result, inventory, _, _ = _invoke(cut, cut / "artifacts/ini_filter", mode="collection")
        assert result.returncode != 0
        payload = json.loads(inventory.read_text())
        assert payload["complete"] is False
        assert payload["ini_addopts"] == ["-k", "one"]
    finally:
        ini.write_text("[pytest]\n", encoding="utf-8")


@pytest.mark.parametrize("extra", [
    ("-o", "python_functions=test_one"),
    ("-opython_functions=test_one",),
    ("--override-ini=python_functions=test_one",),
    ("-o", "python_files=*.py"),
    ("-o", "python_classes=*"),
    ("-o", "testpaths=tests/fresh_training"),
    ("-o", "norecursedirs=notexisting"),
    ("--noconftest",),
    ("--import-mode=importlib",),
])
def test_r008_same_discovery_override_in_both_phases_is_rejected(cut, extra):
    folder = cut / "artifacts" / ("discovery_" + hashlib.sha256(str(extra).encode()).hexdigest()[:12])
    collect, inventory, _, before = _invoke(cut, folder, mode="collection", extra=extra)
    run, execution, junit, _ = _invoke(cut, folder, inventory=inventory, extra=extra)
    report = gr.build_gate_report(cut, junit, run.returncode, before, collection=inventory,
                                  manifest=_manifest(before))
    assert not report["software_acceptance"]
    assert collect.returncode != 0 and json.loads(inventory.read_text())["filters"]


def test_r008_foreign_config_and_subtree_confcutdir_cannot_redefine_scope(cut):
    config = cut / "artifacts/alternate.ini"
    config.write_text("[pytest]\npython_functions = test_one\n", encoding="utf-8")
    for label, extra in [("alternate", ("-c", str(config))),
                         ("cutdir", ("--confcutdir=" + str(cut / "tests/fresh_training"),))]:
        folder = cut / "artifacts" / label
        collect, inventory, _, before = _invoke(cut, folder, mode="collection", extra=extra)
        run, execution, junit, _ = _invoke(cut, folder, inventory=inventory, extra=extra)
        report = gr.build_gate_report(cut, junit, run.returncode, before, collection=inventory,
                                      manifest=_manifest(before))
        assert not report["software_acceptance"]
        assert collect.returncode != 0


def test_r008_only_empty_addopts_override_remains_valid(cut):
    folder = cut / "artifacts/empty_addopts"
    collect, inventory, _, before = _invoke(cut, folder, mode="collection", extra=("-o", "addopts="))
    assert collect.returncode == 0, collect.stdout + collect.stderr
    run, execution, junit, _ = _invoke(cut, folder, inventory=inventory, extra=("-o", "addopts="))
    report = gr.build_gate_report(cut, junit, run.returncode, before, collection=inventory,
                                  manifest=_manifest(before))
    assert report["software_acceptance"]


def test_r008_config_discovery_changed_after_before_is_rejected(cut):
    before = gr.capture_context(cut)
    ini = cut / "pytest.ini"
    ini.write_text("[pytest]\npython_functions = test_one\n", encoding="utf-8")
    try:
        folder = cut / "artifacts/config_drift"
        collect, inventory, _, _ = _invoke(cut, folder, mode="collection", before=before)
        run, execution, junit, _ = _invoke(cut, folder, inventory=inventory, before=before)
        report = gr.build_gate_report(cut, junit, run.returncode, before, collection=inventory,
                                      manifest=_manifest(before))
        assert not report["software_acceptance"]
        assert not report["source_state_stable"]
        assert collect.returncode != 0
    finally:
        ini.write_text("[pytest]\n", encoding="utf-8")


@pytest.mark.parametrize("relative", ["pytest.ini", ".pytest.ini", "setup.cfg", "tox.ini", "conftest.py",
                                      "tests/pytest.ini", "tests/fresh_training/setup.cfg"])
def test_r008_discovery_configuration_is_in_cut_digest(cut, relative):
    path = cut / relative
    original = path.read_bytes() if path.exists() else None
    before = gr.capture_context(cut)
    try:
        path.write_text("# changed discovery source\n", encoding="utf-8")
        after = gr.capture_context(cut)
        assert before["test_source_sha256"] != after["test_source_sha256"]
    finally:
        if original is None:
            path.unlink()
        else:
            path.write_bytes(original)
