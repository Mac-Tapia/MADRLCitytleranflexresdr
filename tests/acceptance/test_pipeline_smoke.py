"""FR-011.6: dataset -> gate -> training plan smoke, without network, GPU or real training."""
from __future__ import annotations

import json
from pathlib import Path

from uc3m.application.training import cli
from uc3m.application.training.dataset_gate import require_validated_dataset
from uc3m.application.training.preflight import dataset_digest

CSV_LF = "hour,load\n0,1.0\n1,2.0\n"


def _dataset(root: Path, csv_text: str = CSV_LF, newline: str = "\n") -> Path:
    root.mkdir(parents=True)
    (root / "Building_1.csv").write_bytes(csv_text.replace("\n", newline).encode("utf-8"))
    schema = root / "schema.json"
    body = json.dumps({"buildings": {"Building_1": {"energy_simulation": "Building_1.csv"}}}, indent=2)
    schema.write_bytes((body + "\n").replace("\n", newline).encode("utf-8"))
    return schema


def _ready_manifest(path: Path, schema: Path) -> tuple:
    digest = dataset_digest(schema)
    path.write_text(json.dumps({"status": "ready", "dataset_digest": digest}), encoding="utf-8")
    return path, digest


def _cli(schema: Path, output_root: Path, *extra: str) -> int:
    return cli.main(["--algorithm", "HAPPO", "--scenario", "E1", "--schema", str(schema),
                     "--output-root", str(output_root), "--episodes", "1",
                     "--episode-time-steps", "8", *extra])


def _last_json(capsys) -> dict:
    return json.loads(capsys.readouterr().out.strip().splitlines()[-1])


def test_validated_dataset_flows_into_prepared_plan(tmp_path: Path, capsys) -> None:
    schema = _dataset(tmp_path / "dataset")
    manifest, digest = _ready_manifest(tmp_path / "ready.json", schema)
    assert require_validated_dataset(schema, manifest) == digest

    output_root = tmp_path / "runs"
    assert _cli(schema, output_root) == 0
    status = _last_json(capsys)
    assert status["status"] == "prepared_not_executed"

    plan = json.loads(Path(status["plan"]).read_text(encoding="utf-8"))
    assert plan["launch_authorized"] is False
    assert plan["experiment"]["dataset_sha256"] == digest
    # Preparing a plan never creates a run directory.
    assert sorted(p.name for p in output_root.iterdir()) == ["plans"]


def test_crlf_checkout_has_the_same_dataset_digest(tmp_path: Path) -> None:
    lf = _dataset(tmp_path / "lf")
    crlf = _dataset(tmp_path / "crlf", newline="\r\n")
    assert b"\r\n" in (crlf.parent / "Building_1.csv").read_bytes()
    assert dataset_digest(crlf) == dataset_digest(lf)

    manifest, _ = _ready_manifest(tmp_path / "ready.json", lf)
    assert require_validated_dataset(crlf, manifest) == dataset_digest(lf)


def test_one_byte_change_blocks_execution_without_creating_runs(tmp_path: Path, capsys) -> None:
    schema = _dataset(tmp_path / "dataset")
    manifest, _ = _ready_manifest(tmp_path / "ready.json", schema)
    csv = schema.parent / "Building_1.csv"
    csv.write_bytes(CSV_LF.replace("2.0", "2.1").encode("utf-8"))

    output_root = tmp_path / "runs"
    assert _cli(schema, output_root, "--execute", "--ready-manifest", str(manifest)) == 2
    status = _last_json(capsys)
    assert status["status"] == "dataset_not_validated"
    assert "revalidate" in status["reason"]
    assert not output_root.exists()
