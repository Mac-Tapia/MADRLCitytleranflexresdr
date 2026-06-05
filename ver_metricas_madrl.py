"""
Ver metricas de entrenamiento MADRL — episodios, pasos, recompensas, pesos
Uso: python ver_metricas_madrl.py [--run <directorio>] [--todos]

Por defecto muestra el run oficial completo: citylearn_v3_madrl_official_full_cuda_v2
Con --todos muestra todos los runs disponibles en outputs/
"""
import csv
import json
import os
import sys

OUTPUTS_DIR = os.path.join(os.path.dirname(__file__), "outputs")
OFFICIAL_RUN = "citylearn_v3_madrl_official_full_cuda_v2"
ALGOS = ["happo", "masac", "maac", "matd3"]
SCENARIOS = ["E1", "E2", "E3"]
SCENARIO_NAMES = {
    "E1": "Flexibilidad (OE.1)",
    "E2": "CO2 (OE.2)",
    "E3": "Costos (OE.3)",
}


def sep(char="-", width=80):
    print(char * width)


def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def load_episode_summary(run_dir, algo, scenario):
    path = os.path.join(run_dir, algo, f"{scenario}_seed_0", "figures", "tables", "episode_summary.csv")
    if not os.path.isfile(path):
        return []
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def fmt(val, decimals=4):
    try:
        return f"{float(val):.{decimals}f}"
    except Exception:
        return str(val)


def print_live_progress(run_dir, run_name):
    sep("=")
    print(f"  RUN: {run_name}")
    sep("=")

    # Lee estado global si existe
    status_path = os.path.join(run_dir, "official_full_status.json")
    status = load_json(status_path)
    if status:
        print(f"  Estado     : {status.get('status', '?')}")
        print(f"  Iniciado   : {status.get('started_at', '?')}")
        print(f"  Completado : {status.get('completed_at', 'en curso...')}")
        print(f"  Episodios  : {status.get('episodes', '?')} x {status.get('episode_time_steps', '?')} pasos")
        print(f"  Dataset    : {status.get('dataset', '?')}")
        print(f"  CUDA       : {status.get('cuda', '?')}")
    sep()

    for scenario in SCENARIOS:
        print(f"\n  ESCENARIO {scenario} — {SCENARIO_NAMES.get(scenario, '')}")
        sep("-", 80)
        print(f"  {'ALGORITMO':<10} {'EP':<5} {'PASOS GLOB':<12} {'RET ACUM EP':<14} {'R_MEAN EP':<12} {'FLEX':<7} {'CO2':<7} {'COST':<7}")
        sep("-", 80)

        for algo in ALGOS:
            lp_path = os.path.join(run_dir, algo, f"{scenario}_seed_0", "live_progress.json")
            d = load_json(lp_path)
            if d is None:
                print(f"  {algo.upper():<10} {'---':>5}  (sin datos)")
                continue

            ep = d.get("episode", "?")
            steps = d.get("global_step", "?")
            ret = d.get("episode_return_cumulative", 0)
            r_mean = d.get("episode_reward_mean_cumulative", 0)
            w = d.get("reward_axis_weights", {})
            flex = w.get("flex", 0)
            co2 = w.get("carbon", 0)
            cost = w.get("cost", 0)

            print(
                f"  {algo.upper():<10} {ep:<5} {steps:<12} "
                f"{fmt(ret, 1):<14} {fmt(r_mean, 5):<12} "
                f"{fmt(flex, 2):<7} {fmt(co2, 2):<7} {fmt(cost, 2):<7}"
            )

        # Tabla de episodios para HAPPO (el mas completo generalmente)
        for algo in ALGOS:
            ep_rows = load_episode_summary(run_dir, algo, scenario)
            if ep_rows:
                sep("-", 80)
                print(f"\n  Detalle por episodio — {algo.upper()} {scenario}:")
                print(f"  {'EP':<5} {'PASOS INICIO':<14} {'PASOS FIN':<12} {'R_MEAN':<12} {'R_SUM':<14} {'PASOS':<8}")
                sep("-", 80)
                for row in ep_rows:
                    print(
                        f"  {row.get('episode','?'):<5} "
                        f"{row.get('first_global_step','?'):<14} "
                        f"{row.get('last_global_step','?'):<12} "
                        f"{fmt(row.get('reward_mean_average',0), 5):<12} "
                        f"{fmt(row.get('reward_sum_total',0), 1):<14} "
                        f"{row.get('steps','?'):<8}"
                    )
                break  # solo el primer algo que tenga datos


def find_all_runs():
    if not os.path.isdir(OUTPUTS_DIR):
        return []
    runs = []
    for name in sorted(os.listdir(OUTPUTS_DIR)):
        full = os.path.join(OUTPUTS_DIR, name)
        if not os.path.isdir(full):
            continue
        has_data = any(
            os.path.isfile(os.path.join(full, algo, f"{esc}_seed_0", "live_progress.json"))
            for algo in ALGOS for esc in SCENARIOS
        )
        if has_data:
            runs.append((name, full))
    return runs


def print_all_runs_summary():
    runs = find_all_runs()
    sep("=")
    print(f"  TODOS LOS RUNS DISPONIBLES EN outputs/ ({len(runs)} runs con datos)")
    sep("=")
    print(f"  {'RUN':<55} {'ALGOS':<20} {'ESTADO'}")
    sep("-", 80)
    for name, full in runs:
        algos_found = []
        for algo in ALGOS:
            for esc in SCENARIOS:
                lp = os.path.join(full, algo, f"{esc}_seed_0", "live_progress.json")
                if os.path.isfile(lp) and algo not in algos_found:
                    algos_found.append(algo.upper())
        status_path = os.path.join(full, "official_full_status.json")
        status = load_json(status_path)
        estado = status.get("status", "?") if status else "sin status"
        print(f"  {name[:54]:<55} {','.join(algos_found):<20} {estado}")


def main():
    args = sys.argv[1:]
    show_all = "--todos" in args

    if show_all:
        print_all_runs_summary()
        sep("=")
        print()

    # Determina el run a mostrar en detalle
    run_name = OFFICIAL_RUN
    if "--run" in args:
        idx = args.index("--run")
        if idx + 1 < len(args):
            run_name = args[idx + 1]

    run_dir = os.path.join(OUTPUTS_DIR, run_name)
    if not os.path.isdir(run_dir):
        # Intenta el run activo mas reciente
        runs = find_all_runs()
        if runs:
            run_name, run_dir = runs[-1]
            print(f"  [INFO] Run oficial no encontrado. Usando el mas reciente: {run_name}")
        else:
            print(f"  [ERROR] No se encontraron runs con datos en {OUTPUTS_DIR}")
            return 1

    print_live_progress(run_dir, run_name)

    sep("=")
    print()
    print("  INTERPRETACION DE PESOS DE RECOMPENSA:")
    print("  flex = peso del objetivo OE.1 Flexibilidad")
    print("  co2  = peso del objetivo OE.2 Emisiones CO2")
    print("  cost = peso del objetivo OE.3 Costo energetico")
    print()
    print("  Para ver todos los runs: python ver_metricas_madrl.py --todos")
    print(f"  Para un run especifico:  python ver_metricas_madrl.py --run <nombre_run>")
    sep("=")
    return 0


if __name__ == "__main__":
    sys.exit(main())
