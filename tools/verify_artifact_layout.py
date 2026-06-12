"""Verifica y pre-crea los directorios de artefactos para las 12 corridas MADRL."""
import sys
sys.path.insert(0, 'CityLearn/scripts')
from citylearn_v3_training_common import ensure_artifact_layout
from pathlib import Path

OUT        = Path('outputs/citylearn_v3_madrl_oficial_v3')
ALGORITHMS = ['happo', 'masac', 'matd3', 'maac']
SCENARIOS  = ['E1', 'E2', 'E3']

print("=" * 70)
print("VERIFICACION DE ESTRUCTURA DE DIRECTORIOS -- 12 CORRIDAS MADRL")
print("=" * 70)

all_ok = True
for sc in SCENARIOS:
    print(f"\n  Escenario {sc}:")
    for alg in ALGORITHMS:
        run_dir = OUT / alg / f"{sc}_seed_0"
        dirs = ensure_artifact_layout(run_dir)
        chk  = dirs["checkpoints"].exists()
        dat  = dirs["data"].exists()
        fig  = dirs["figures"].exists()
        tab  = (dirs["figures"] / "tables").exists()
        ok   = chk and dat and fig and tab
        if not ok:
            all_ok = False
        tag = "OK" if ok else "ERROR"
        print(f"    [{tag}] {alg.upper():5} | checkpoints={chk} data={dat} figures={fig} tables={tab}")
        print(f"           {run_dir}")
        # Mostrar archivos que se generaran al completar
        expected = [
            run_dir / "results.json",
            run_dir / "timeseries.csv",
            run_dir / "trace.csv",
            dirs["data"] / "results.json",
            dirs["data"] / "timeseries.csv",
            dirs["data"] / "trace.csv",
        ]
        missing = [str(p.relative_to(OUT)) for p in expected if not p.exists()]
        if missing:
            print(f"           Pendientes (se crean al completar):")
            for m in missing:
                print(f"             - {m}")

print()
if all_ok:
    print("Todos los directorios pre-creados correctamente.")
else:
    print("ERROR en algunos directorios.")
    sys.exit(1)
