"""FR-011.6: dataset -> gate -> training plan smoke, without network, GPU or real training."""
from __future__ import annotations

import json
from pathlib import Path

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


def _last_json(capsys) -> dict:
    return json.loads(capsys.readouterr().out.strip().splitlines()[-1])


def test_crlf_checkout_has_the_same_dataset_digest(tmp_path: Path) -> None:
    lf = _dataset(tmp_path / "lf")
    crlf = _dataset(tmp_path / "crlf", newline="\r\n")
    assert b"\r\n" in (crlf.parent / "Building_1.csv").read_bytes()
    assert dataset_digest(crlf) == dataset_digest(lf)

    manifest, _ = _ready_manifest(tmp_path / "ready.json", lf)
    assert require_validated_dataset(crlf, manifest) == dataset_digest(lf)


