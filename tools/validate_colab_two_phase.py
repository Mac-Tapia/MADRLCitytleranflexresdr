#!/usr/bin/env python3
"""Final Colab two_phase_happo_masac validation (local pre-flight)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CL = ROOT / "CityLearn"
LAUNCHER = CL / "scripts" / "colab_a100_official_launcher.py"
MONITOR = CL / "scripts" / "colab_a100_live_monitor.py"
GUARD = CL / "scripts" / "colab_protocol_guard.py"
NOTEBOOK = CL / "examples" / "madrl_citylearn_v3_tutorial.ipynb"
SCHEMA = CL / "data" / "datasets" / "citylearn_iquitos_2023_2025" / "schema.json"

REQUIRED_LAUNCHER = (
    "LAUNCHER_PROTOCOL_ID",
    "two_phase_happo_masac_v3",
    "run_two_phase_happo_masac_jobs",
    "TWO_PHASE_P1_HM",
    "TWO_PHASE_P2_HM",
)
FORBIDDEN_LAUNCHER = (
    "algo_sequential",
    "run_two_phase_jobs",
    "TWO_PHASE_LIGHT",
    "FASE 1: HAPPO + MATD3",
    "delay=600",
)
REQUIRED_MONITOR = ("MONITOR_PROTOCOL_ID", "two_phase_happo_masac_v3", "TWO_PHASE_P1", "TWO_PHASE_P2")


def ok(msg: str) -> None:
    print(f"  [OK] {msg}")


def fail(msg: str) -> None:
    print(f"  [FAIL] {msg}")
    sys.exit(1)


def main() -> int:
    print("=" * 72)
    print("VALIDACION FINAL: two_phase_happo_masac (Colab A100)")
    print("=" * 72)

    # 1. Git sync
    print("\n1. Git / submodulo")
    parent_head = subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True
    ).strip()
    cl_head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=CL, text=True
    ).strip()
    sub_line = subprocess.check_output(
        ["git", "submodule", "status", "CityLearn"], cwd=ROOT, text=True
    ).strip()
    if cl_head not in sub_line:
        fail(f"CityLearn HEAD {cl_head[:12]} no coincide con submodule: {sub_line}")
    ok(f"Padre @ {parent_head}")
    ok(f"CityLearn @ {cl_head[:12]} (submodulo alineado)")

    # 2. Launcher / monitor source
    print("\n2. Launcher y monitor")
    la = LAUNCHER.read_text(encoding="utf-8")
    mo = MONITOR.read_text(encoding="utf-8")
    for s in REQUIRED_LAUNCHER:
        if s not in la:
            fail(f"Launcher falta: {s}")
    for s in FORBIDDEN_LAUNCHER:
        if s in la:
            fail(f"Launcher contiene legacy: {s}")
    ok("Launcher: protocolo two_phase_happo_masac_v3, sin legacy")
    for s in REQUIRED_MONITOR:
        if s not in mo:
            fail(f"Monitor falta: {s}")
    ok("Monitor: protocolo y fases P1/P2")
    if not GUARD.is_file():
        fail("Falta colab_protocol_guard.py")
    ok("protocol-guard presente")

    # 3. Notebook bindings
    print("\n3. Notebook Colab")
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    src = "\n".join("".join(c.get("source", [])) for c in nb["cells"])
    for needle in (
        "REPO_BRANCH      = 'codex/fix-madrl-traceability-docs'",
        "CITYLEARN_BRANCH = 'codex/iquitos-distillation-madrl-docs'",
        "EXECUTION_MODE = 'two_phase_happo_masac'",
        "verify_two_phase_protocol()",
        "'--execution-mode', 'two_phase_happo_masac'",
    ):
        if needle not in src:
            fail(f"Notebook falta: {needle!r}")
    ok("Ramas Colab + EXECUTION_MODE + verify_two_phase_protocol")
    sys.path.insert(0, str(CL / "scripts"))
    from colab_notebook_urls import badge_must_contain, open_in_colab_url

    badge_needle = badge_must_contain()
    if badge_needle not in src:
        fail(f"Badge Open in Colab desactualizado; falta: {badge_needle!r}")
    if "citylearn-v3-madrl/examples/madrl_citylearn_v3_tutorial.ipynb" in src:
        fail("Notebook aun referencia rama legacy citylearn-v3-madrl en badge")
    ok(f"Open in Colab -> {open_in_colab_url()}")

    # 4. Argparse: solo two_phase
    print("\n4. CLI launcher")
    proc = subprocess.run(
        [sys.executable, str(LAUNCHER), "--help"],
        capture_output=True,
        text=True,
        cwd=CL,
    )
    help_text = proc.stdout + proc.stderr
    if "algo_sequential" in help_text:
        fail("--help aun menciona algo_sequential")
    if "two_phase_happo_masac" not in help_text:
        fail("--help sin two_phase_happo_masac")
    ok("CLI: solo two_phase_happo_masac")

    # 5. Dry-run (si schema existe)
    print("\n5. Dry-run launcher")
    if not SCHEMA.exists():
        print("  [SKIP] schema no encontrado localmente")
    else:
        out = ROOT / "outputs" / "_validate_two_phase_dryrun"
        proc = subprocess.run(
            [
                sys.executable,
                "-B",
                str(LAUNCHER),
                "--dry-run",
                "--execution-mode",
                "two_phase_happo_masac",
                "--scenario",
                "ALL",
                "--seed",
                "0",
                "--episode-time-steps",
                "8760",
                "--episodes",
                "50",
                "--schema-path",
                "CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json",
                "--output-root",
                "outputs/_validate_two_phase_dryrun",
                "--skip-completed",
                "--no-require-a100",
                "--no-smoke-imports",
                "--skip-gpu-preflight",
                "--no-cuda",
            ],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        if proc.returncode != 0:
            print(proc.stdout)
            print(proc.stderr, file=sys.stderr)
            fail(f"dry-run exit={proc.returncode}")
        if "protocol=two_phase_happo_masac_v3" not in proc.stdout:
            fail("dry-run sin linea protocol=two_phase_happo_masac_v3")
        status_path = out / "official_full_status.json"
        if not status_path.exists():
            fail(f"no existe {status_path}")
        status = json.loads(status_path.read_text(encoding="utf-8"))
        assert status["status"] == "dry_run"
        assert status.get("execution") == "two_phase_happo_masac"
        assert len(status.get("jobs", [])) == 12
        strat = status.get("parallelization", {}).get("strategy", "")
        assert "Phase1=HAPPO+MASAC" in strat and "Phase2=MATD3+MAAC" in strat
        assert "no stagger" in strat.lower()
        algos = {j["name"] for j in status["jobs"]}
        assert algos == {"happo", "masac", "matd3", "maac"}
        ok(f"12 jobs, execution=two_phase_happo_masac, strategy OK")
        ok(f"protocol line en stdout")

    print("\n" + "=" * 72)
    print("RESULTADO: LISTO PARA COLAB (two_phase_happo_masac)")
    print("  Fase 1: HAPPO+MASAC x3 (6 paralelo, sin stagger)")
    print("  Fase 2: MATD3+MAAC x3 (6 paralelo, sin stagger)")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
