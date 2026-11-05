"""Independent HEAD reproductions in temp dirs only: promotion gate, Drive sync, pipeline exit code."""
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path
from unittest import mock

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root))
sys.dont_write_bytecode = True

from uc3m.application import pipeline  # noqa: E402
from uc3m.application.training import drive_sync  # noqa: E402
from uc3m.application.training.fresh_acceptance import attempt_evidence_reasons, verify_fresh_acceptance  # noqa: E402
from uc3m.domain.campaigns import canonical_hash  # noqa: E402
from uc3m.domain.evidence import checkpoint_bundle_hash  # noqa: E402

CID = "fresh_probe_20261101_v1"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def build(base, *, updates, steps, planned):
    rootd = base / "campaign"
    (rootd / "stages").mkdir(parents=True)
    stage = rootd / "stages/confirm.json"
    stage.write_text(json.dumps({"stage": "confirm", "treatments": [{"treatment_id": f"t{i}"} for i in range(planned)]}))
    identity = {"config_sha256": "1" * 64, "dataset_hash": "2" * 64}
    manifest = {"schema_version": 1, "campaign_id": CID, "spec_hash": canonical_hash(identity), "identity": identity,
                "stages": {"confirm": {"path": "stages/confirm.json", "sha256": sha(stage), "treatments": planned}}}
    (rootd / "campaign_manifest.json").write_text(json.dumps(manifest))
    (rootd / "campaign.json").write_text(json.dumps({"campaign_id": CID, "spec_hash": manifest["spec_hash"]}))
    attempt = rootd / "attempts/t0/try_01"
    ckpt = attempt / "ckpt.pt"
    ckpt.parent.mkdir(parents=True)
    ckpt.write_bytes(b"not a model")
    evidence = {"campaign_id": CID, "attempt_id": "otro", "verified": True, "exit_code": 0, "salvage": None,
                "checkpoint_bundle_hash": checkpoint_bundle_hash([ckpt]), "checkpoint_files": ["ckpt.pt"],
                "successful_optimizer_updates_by_owner": {"actor": updates}, "env_steps": steps, "completed_episodes": 0}
    (attempt / "learning_evidence.json").write_text(json.dumps(evidence))
    (attempt / "completion.json").write_text(json.dumps({"training_complete": True}))
    result = {"campaign_id": CID, "stage": "confirm", "status": "training_complete", "planned_treatments": planned,
              "treatments": [{"treatment_id": "t0", "attempts": [{"attempt_id": "try_01", "training_complete": True,
                                                                  "path": attempt.relative_to(rootd).as_posix()}]}]}
    (rootd / "stages/confirm_result.json").write_text(json.dumps(result))
    (rootd / "reports").mkdir()
    (rootd / "reports/scientific_report.json").write_text(json.dumps({"campaign_id": CID, "status": "scientifically_complete"}))
    gate = base / "gate.json"
    gate.write_text(json.dumps({"exit_code": 0, "software_acceptance": True,
                                "counters": {"tests": 1, "failures": 0, "errors": 0, "skipped": 0}}))
    return rootd / "campaign_manifest.json", gate, attempt, evidence


def attempt_dir(base, name):
    d = base / "attempts" / name
    d.mkdir(parents=True)
    (d / "attempt.json").write_text("{}")
    (d / "completion.json").write_text(json.dumps({"training_complete": False}))
    (d / "data.bin").write_bytes(b"x" * 16)
    return d


out = {}
with tempfile.TemporaryDirectory() as tmp:
    m, g, attempt, evidence = build(Path(tmp), updates=0, steps=0, planned=2)
    report = verify_fresh_acceptance(m, gate_report=g)
    out["P1_promocion"] = {
        "entrada": "0 updates, 0 pasos, intento ajeno, 1 de 2 tratamientos, checkpoint basura, informe de 2 campos",
        "status": report.status, "scientific_acceptance": report.scientific_acceptance,
        "contrato_estricto_rechazaria_por": attempt_evidence_reasons(
            evidence, attempt, campaign_id=CID, attempt_id="try_01", treatment_id="t0", seed=1001,
            expected_owners=["actor"]),
    }

with tempfile.TemporaryDirectory() as tmp:
    art, drive = Path(tmp) / "art", Path(tmp) / "drive"
    attempt_dir(art, "a1")
    real_write = drive_sync._write_manifest
    with mock.patch.object(drive_sync, "_write_manifest", side_effect=KeyboardInterrupt):
        try:
            drive_sync.sync_finished_attempts(art, drive)
        except KeyboardInterrupt:
            pass
    second = drive_sync.sync_finished_attempts(art, drive)
    code = drive_sync.main(["--artifacts", str(art), "--drive", str(drive), "--sync"])
    manifest = json.loads((drive / drive_sync.MANIFEST).read_text())
    local2 = Path(tmp) / "fresh_session"
    restored = drive_sync.restore_finished_attempts(drive, local2, CID, trust=lambda *a: [])
    out["P2_drive_corte_antes_del_manifiesto"] = {
        "segunda_sync_conflicts": second["conflicts"], "exit_code_cli_con_conflicto": code,
        "intentos_en_manifiesto": list(manifest["attempts"]), "copia_en_drive_existe": (drive / "attempts/a1").is_dir(),
        "restaurados_en_sesion_nueva": restored["restored_failed"] + restored["restored_complete"],
    }

with tempfile.TemporaryDirectory() as tmp:
    base = Path(tmp)
    art, drive = base / "sandbox/art", base / "sandbox/drive"
    art.mkdir(parents=True)
    drive.mkdir(parents=True)
    (base / "sandbox/payload.txt").write_text("fuera")
    escape = "../escaped.txt"
    (drive / escape).parent.mkdir(exist_ok=True)
    source = drive / "../payload.txt"
    manifest = {"attempts": {}, "files": {"../payload.txt": sha(source)}}
    (drive / drive_sync.MANIFEST).write_text(json.dumps(manifest))
    report = drive_sync.restore_finished_attempts(drive, art, CID, trust=lambda *a: [])
    written = base / "sandbox/payload.txt"
    # source and target both resolve above their roots; target exists, so use a distinct depth
    manifest = {"attempts": {}, "files": {"sub/../../outside.txt": None}}
    (base / "sandbox/outside.txt").write_text("fuera")
    (drive / "sub").mkdir()
    manifest["files"]["sub/../../outside.txt"] = sha(base / "sandbox/outside.txt")
    (drive / drive_sync.MANIFEST).write_text(json.dumps(manifest))
    art2 = base / "sandbox/deep/art"
    (art2 / "sub").mkdir(parents=True)
    report2 = drive_sync.restore_finished_attempts(drive, art2, CID, trust=lambda *a: [])
    out["P3_drive_ruta_con_punto_punto"] = {
        "rutas_aceptadas": report2["files"], "escrito_fuera_de_artifacts": (base / "sandbox/deep/outside.txt").is_file(),
    }

with tempfile.TemporaryDirectory() as tmp:
    fake = Path(tmp) / "m.json"
    fake.write_text("{}")
    with mock.patch.object(pipeline, "evaluate_stage", return_value={
            "stage": "confirm", "split": "s", "evaluated": [], "existing": [],
            "failed": [{"attempt": "a", "treatment_id": "t", "reason": "RuntimeError: boom"}]}):
        code = pipeline.main(["evaluate", "--manifest", str(fake)])
    out["P4_pipeline_evaluate_con_fallos"] = {"exit_code": code}

with tempfile.TemporaryDirectory() as tmp:
    fake = Path(tmp) / "m.json"
    fake.write_text(json.dumps({"campaign_id": CID}))
    partial = Path(tmp) / "analysis" / "confirm_s.partial"
    partial.mkdir(parents=True)
    with mock.patch("uc3m.application.evaluation.results_catalog.build_seed_table", return_value=mock.Mock(rows=[])), \
            mock.patch("uc3m.application.evaluation.fresh_analysis.analyze_campaign",
                       return_value=mock.Mock(as_dict=lambda: {})), \
            mock.patch("uc3m.application.evaluation.fresh_analysis.FrozenProtocol"):
        try:
            pipeline.analyze_stage(fake, stage="confirm", split="s")
            out["P5_analyze_tras_parcial"] = "reintento correcto"
        except FileExistsError as exc:
            out["P5_analyze_tras_parcial"] = f"bloqueado: FileExistsError ({Path(exc.filename).name})"

print(json.dumps(out, indent=1, ensure_ascii=False))
