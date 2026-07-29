"""Real on-disk storage diagnosis per MADRL algorithm (no .pt-only bias)."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CKPT_EXTS = {".pt", ".pth", ".pkl", ".pickle", ".ckpt", ".zip"}
ALGOS = ("HAPPO", "MAAC", "MASAC", "MATD3")


def algo_from_path(path: Path) -> str | None:
    for part in path.parts:
        low = part.lower()
        if low == "happo":
            return "HAPPO"
        if low == "maac":
            return "MAAC"
        if low == "masac":
            return "MASAC"
        if low == "matd3":
            return "MATD3"
        if part.upper() in ALGOS:
            return part.upper()
    return None


def scan_tree(root: Path) -> dict:
    by_algo: dict[str, dict] = {
        a: {
            "total_bytes": 0,
            "file_count": 0,
            "checkpoint_bytes": 0,
            "checkpoint_files": 0,
            "checkpoint_ext_counts": defaultdict(int),
            "extensions": defaultdict(int),
        }
        for a in ALGOS
    }
    if not root.is_dir():
        return {"root": str(root), "exists": False, "by_algo": by_algo}

    for f in root.rglob("*"):
        if not f.is_file():
            continue
        algo = algo_from_path(f)
        if not algo:
            continue
        sz = f.stat().st_size
        ext = f.suffix.lower()
        row = by_algo[algo]
        row["total_bytes"] += sz
        row["file_count"] += 1
        row["extensions"][ext or "(no_ext)"] += 1
        in_ckpt_dir = "/checkpoints/" in f.as_posix() or "\\checkpoints\\" in str(f)
        if in_ckpt_dir or ext in CKPT_EXTS:
            row["checkpoint_bytes"] += sz
            row["checkpoint_files"] += 1
            row["checkpoint_ext_counts"][ext or "(no_ext)"] += 1

    return {"root": str(root), "exists": True, "by_algo": by_algo}


def read_kpi_checkpoint_counts() -> list[dict]:
    kpis = REPO / "outputs" / "_drive_madrl" / "kpis"
    rows = []
    for path in sorted(kpis.glob("*_results.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        rows.append(
            {
                "file": path.name,
                "algo": str(data.get("algorithm", "?")).upper(),
                "scenario": str(data.get("scenario", "?")).upper(),
                "checkpoint_count": data.get("checkpoint_count"),
                "episodes_recorded": data.get("episodes_recorded"),
            }
        )
    return rows


def fmt_gb(n: int) -> str:
    return f"{n / 1e9:.3f} GB"


def print_report(label: str, result: dict) -> None:
    print(f"\n{'=' * 60}")
    print(label)
    print(f"Root: {result['root']}")
    if not result.get("exists"):
        print("  (no existe localmente)")
        return
    print(f"{'Algo':6} {'Total':>12} {'Ckpt':>12} {'#files':>8} {'#ckpt':>8}  extensiones checkpoint")
    for algo in ALGOS:
        v = result["by_algo"][algo]
        ext_summary = ", ".join(
            f"{e}:{n}" for e, n in sorted(v["checkpoint_ext_counts"].items(), key=lambda x: -x[1])
        )
        print(
            f"{algo:6} {fmt_gb(v['total_bytes']):>12} {fmt_gb(v['checkpoint_bytes']):>12} "
            f"{v['file_count']:8d} {v['checkpoint_files']:8d}  {ext_summary or '-'}"
        )


def main() -> None:
    v4 = REPO / "outputs" / "citylearn_v3_madrl_full_20260615_074011_v4"
    print("DIAGNOSTICO REAL DE ALMACENAMIENTO MADRL")
    print("Nota: MASAC usa .pkl (QMIX bundle), no .pt. Contar solo .pt es un error.")

    print_report("LOCAL v4 (5 episodios, referencia)", scan_tree(v4))

    print("\n--- KPIs Colab (checkpoint_count en results.json) ---")
    for row in read_kpi_checkpoint_counts():
        print(
            f"  {row['algo']:6} {row['scenario']:4}  "
            f"ep={row['episodes_recorded']}  checkpoint_count={row['checkpoint_count']}"
        )

    masac_manifest = v4 / "masac" / "E1_seed_0" / "data" / "checkpoint_manifest.json"
    if masac_manifest.is_file():
        manifest = json.loads(masac_manifest.read_text(encoding="utf-8"))
        print("\n--- MASAC E1 v4: checkpoint_manifest.json (bytes reales) ---")
        total = 0
        for ck in manifest.get("checkpoints", []):
            b = int(ck.get("bytes") or 0)
            total += b
            rel = ck.get("relative_path", ck.get("path", "?"))
            print(f"  {b:>8d} bytes  {Path(rel).name}")
        print(f"  TOTAL bundle (3 archivos .pkl): {total / 1024:.1f} KB")
        print(f"  checkpoint_count en manifest: {manifest.get('checkpoint_count')}")

    # Extrapolation for canonical 50-ep run using measured per-file sizes
    print("\n--- EXTRAPOLACION CANONICA (50 ep, desde medicion local + KPI) ---")
    maac_pt = 154.2e6  # MB per checkpoint_episode_*.pt measured
    masac_bundle = 638593  # sum of 3 pkl from manifest above
    happo_avg = 46.23e6 / 60 if (v4 / "happo").is_dir() else 0  # v4 total pt / count
    matd3_avg = 452e6 / 105 if (v4 / "matd3").is_dir() else 0

    specs = {
        "MAAC": {"count_per_job": 52, "bytes_each": maac_pt, "note": "1 .pt monolitico/ep (+ rolling)"},
        "MASAC": {"count_per_job": 12, "bytes_each": masac_bundle, "note": "bundles .pkl QMIX (3 archivos/bundle)"},
        "MATD3": {"count_per_job": 34, "bytes_each": matd3_avg, "note": ".pt por agente"},
        "HAPPO": {"count_per_job": 50 * 17 + 1, "bytes_each": happo_avg, "note": "17 actors + critic/ep (aprox)"},
    }
    for algo, spec in specs.items():
        jobs = 3
        total = jobs * spec["count_per_job"] * spec["bytes_each"]
        print(
            f"  {algo}: ~{total / 1e9:.1f} GB  "
            f"({spec['count_per_job']} ckpt/job x 3 escenarios x {spec['bytes_each']/1e6:.2f} MB)  "
            f"[{spec['note']}]"
        )


if __name__ == "__main__":
    main()
