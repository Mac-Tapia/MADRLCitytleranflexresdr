#!/usr/bin/env python3
"""Validate Colab resume plan against real Drive exports (folder 1ihH6RqL2KpevfCQEUXj7PP1aS2QYssAX).

Uses outputs/_drive_madrl/kpis/ (real results.json downloaded from Drive) as ground truth.
Optional: OAuth via tools/skills/google-drive-mcp for live API checks.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "CityLearn" / "scripts"
KPI_DIR = REPO / "outputs" / "_drive_madrl" / "kpis"
CANONICAL_RUN = "madrl_v3_20260627_164047"
SHARED_FOLDER_ID = "1ihH6RqL2KpevfCQEUXj7PP1aS2QYssAX"
SHARED_FOLDER_URL = f"https://drive.google.com/drive/folders/{SHARED_FOLDER_ID}"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from citylearn_v3_training_common import (  # noqa: E402
    assert_canonical_colab_skip_plan,
    build_jobs_resume_report,
    preview_job_launcher_decision,
    validate_canonical_colab_skip_plan,
)

EXPECTED = {
    ("happo", "E1"): "resume",
    ("happo", "E2"): "resume",
    ("happo", "E3"): "resume",
    ("masac", "E1"): "skip",
    ("masac", "E2"): "skip",
    ("masac", "E3"): "skip",
    ("matd3", "E1"): "skip",
    ("matd3", "E2"): "skip",
    ("matd3", "E3"): "skip",
    ("maac", "E1"): "skip",
    ("maac", "E2"): "skip",
    ("maac", "E3"): "skip",
}


def _drive_oauth_status() -> dict:
    cred = REPO / "tools/skills/google-drive-mcp/data/credentials.json"
    token = REPO / "tools/skills/google-drive-mcp/data/token.json"
    out = {"credentials": cred.is_file(), "token": token.is_file(), "live_api": False}
    if out["token"]:
        try:
            skill_scripts = REPO / "tools/skills/google-drive-mcp/scripts"
            sys.path.insert(0, str(skill_scripts))
            from auth_manager import AuthManager  # type: ignore

            out["live_api"] = bool(AuthManager().validate_auth())
        except Exception as exc:
            out["error"] = str(exc)
    return out


def _build_run_from_real_kpis(kpi_dir: Path, run_root: Path) -> int:
    import shutil

    copied = 0
    for algo in ("happo", "masac", "matd3", "maac"):
        for scen in ("E1", "E2", "E3"):
            src = kpi_dir / f"{algo}_{scen}_results.json"
            if not src.is_file():
                continue
            dest = run_root / algo.upper() / scen / "data"
            dest.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest / "results.json")
            copied += 1
            if algo == "happo":
                ckpt = run_root / algo.upper() / scen / "checkpoints" / "gym" / "run" / "models"
                ckpt.mkdir(parents=True, exist_ok=True)
                (ckpt / "actor_agent0.pt").write_bytes(b"drive-kpi-stub")
                (ckpt / "critic_agent.pt").write_bytes(b"drive-kpi-stub")
    return copied


def _audit_kpi_exports(kpi_dir: Path) -> list[dict]:
    rows: list[dict] = []
    for path in sorted(kpi_dir.glob("*_results.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        jr = (data.get("hyperparameters") or {}).get("job_resume") or {}
        rows.append(
            {
                "file": path.name,
                "algorithm": data.get("algorithm"),
                "scenario": data.get("scenario"),
                "output_dir": data.get("output_dir"),
                "status": data.get("status"),
                "resume_ep": f"{jr.get('completed_episodes', '?')}/{jr.get('target_episodes', 50)}",
                "episodes_recorded": data.get("episodes_recorded"),
            }
        )
    return rows


def main() -> int:
    print("=" * 72)
    print("VALIDACION COLAB: reanudar desde Drive real (sin inventar datos)")
    print(f"  Carpeta compartida: {SHARED_FOLDER_URL}")
    print(f"  Run canonico:     {CANONICAL_RUN}")
    print("=" * 72)

    oauth = _drive_oauth_status()
    print("\n1. Conector Drive OAuth (google-drive-mcp)")
    print(f"   credentials.json: {'OK' if oauth['credentials'] else 'FALTA'}")
    print(f"   token.json:       {'OK' if oauth['token'] else 'FALTA'}")
    print(f"   API en vivo:      {'OK' if oauth.get('live_api') else 'no (usa KPIs locales)'}")
    if not oauth.get("live_api"):
        print(
            "   -> Para API directa: coloca credentials.json y ejecuta setup_auth "
            "(tools/skills/google-drive-mcp/README.md)"
        )

    if not KPI_DIR.is_dir():
        print(f"\nERROR: sin exports Drive locales: {KPI_DIR}", file=sys.stderr)
        return 2

    print(f"\n2. KPIs reales en disco ({KPI_DIR})")
    exports = _audit_kpi_exports(KPI_DIR)
    if len(exports) < 12:
        print(f"   ERROR: solo {len(exports)}/12 results.json", file=sys.stderr)
        return 2
    print(f"   OK: {len(exports)}/12 exports con output_dir de Drive")
    for row in exports:
        print(
            f"   {row['algorithm']:5} {row['scenario']}  "
            f"resume={row['resume_ep']}  status={row['status']}"
        )

    print("\n3. Plan skip/resume (misma logica que celdas 2.1b y 7.2)")
    run_root = REPO / "outputs" / "_validate_drive_run" / CANONICAL_RUN
    if run_root.exists():
        import shutil

        shutil.rmtree(run_root.parent)
    n = _build_run_from_real_kpis(KPI_DIR, run_root)
    if n < 12:
        print(f"   ERROR: layout incompleto ({n}/12)", file=sys.stderr)
        return 2

    report = build_jobs_resume_report(
        run_root,
        target_episodes=50,
        episode_time_steps=8760,
        happo_rollout_threads=2,
    )
    mismatches = []
    for job in report["jobs"]:
        algo = str(job["algorithm"]).lower()
        scen = str(job["scenario"]).upper()
        action = str(job["action"])
        exp = EXPECTED.get((algo, scen))
        ok = action == exp
        mark = "OK" if ok else "FAIL"
        print(f"   [{mark}] {algo.upper()}/{scen}: {action} (esperado {exp})")
        if not ok:
            mismatches.append((algo, scen, exp, action))

    validation = validate_canonical_colab_skip_plan(report)
    print(
        f"\n   Resumen: SKIP={report['completed']}  REANUDA={report['resumable']}  "
        f"PENDIENTE={report['pending']}"
    )
    if not validation.get("ok") or mismatches:
        print("   FAIL: plan no coincide con Drive", file=sys.stderr)
        return 1
    assert_canonical_colab_skip_plan(report, output_root=run_root)
    print("   PASS: 9 SKIP + 3 REANUDA (solo HAPPO E1-E3 ep 49/50)")

    print("\n4. Contrato notebook madrl_citylearn_v3_tutorial.ipynb")
    for script, label in (
        ("verify_notebook.py", "verify_notebook"),
        ("validate_colab_two_phase.py", "two_phase Colab"),
    ):
        proc = subprocess.run(
            [sys.executable, str(REPO / "tools" / script)],
            cwd=str(REPO),
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            print(f"   FAIL {label}:\n{proc.stdout}\n{proc.stderr}", file=sys.stderr)
            return proc.returncode
        print(f"   OK: {label}")

    print("\n" + "=" * 72)
    print("RESULTADO: NOTEBOOK LISTO PARA COLAB — reanudar madrl_v3_20260627_164047")
    print("  Colab: 1.5 -> 2.1 -> 2.1b (debe PASS 9+3) -> 6.1 -> 7.1 -> 7.2")
    print("  HAPPO: reanuda ep 50/50; MASAC/MATD3/MAAC: omitidos (--skip-completed)")
    print("  Post-HAPPO: celda 2.3 si salvage sin KPIs completos")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
