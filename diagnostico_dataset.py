"""
Diagnóstico del dataset CityLearn v2 — Iquitos 2023-2025 (17 edificios)
Uso: python diagnostico_dataset.py
"""
import csv
import json
import os
import sys

DATASET_DIR = os.path.join(
    os.path.dirname(__file__),
    "CityLearn", "data", "datasets", "citylearn_iquitos_2023_2025"
)
LOG_PATH = os.path.join(os.path.dirname(__file__), "tools", "dataset_docs", "dataset_generation_log.json")
EXPECTED_ROWS = 26305
EXPECTED_BUILDINGS = 17

BUILDING_COLS = {
    "month", "hour", "day_type", "daylight_savings_status",
    "non_shiftable_load", "solar_generation", "cooling_demand",
}
WEATHER_COLS = {
    "outdoor_dry_bulb_temperature", "outdoor_relative_humidity",
    "diffuse_solar_irradiance", "direct_solar_irradiance",
}
CARBON_COLS = {"carbon_intensity"}
PRICING_COLS = {"electricity_pricing"}


def sep(char="-", width=72):
    print(char * width)


def count_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return sum(1 for _ in f)


def get_columns(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        return set(next(reader, []))


def check_file(label, path, expected_rows, required_cols=None):
    ok = True
    errors = []
    if not os.path.isfile(path):
        return False, ["ARCHIVO NO EXISTE"]
    rows = count_rows(path)
    if rows != expected_rows:
        ok = False
        errors.append(f"filas={rows} (esperado {expected_rows})")
    if required_cols:
        cols = get_columns(path)
        missing = required_cols - cols
        if missing:
            ok = False
            errors.append(f"columnas faltantes: {missing}")
    return ok, errors


def print_row(label, status, detail=""):
    icon = "[OK]" if status else "[FAIL]"
    print(f"  {icon:<6} {label:<40} {detail}")


def main():
    sep("=")
    print("  DIAGNOSTICO DEL DATASET — CityLearn v2 Iquitos 2023-2025")
    sep("=")
    print(f"  Directorio: {DATASET_DIR}")

    # 1. Log de generacion
    sep()
    print("1. LOG DE GENERACION")
    sep()
    if os.path.isfile(LOG_PATH):
        with open(LOG_PATH, encoding="utf-8") as f:
            log = json.load(f)
        print(f"  Fecha generacion  : {log.get('fecha_generacion', '?')}")
        print(f"  Anos cubiertos    : {log.get('anios', '?')}")
        print(f"  Total horas       : {log.get('total_horas', '?')}")
        print(f"  Edificios         : {log.get('edificios_generados', '?')}")
        fuentes = log.get("fuentes_meteorologicas", {})
        for anio, fuente in fuentes.items():
            print(f"  Fuente meteo {anio}  : {fuente}")
    else:
        print(f"  [WARN] No se encontro {LOG_PATH}")

    # 2. Schema.json
    sep()
    print("2. SCHEMA.JSON")
    sep()
    schema_path = os.path.join(DATASET_DIR, "schema.json")
    if os.path.isfile(schema_path):
        with open(schema_path, encoding="utf-8") as f:
            schema = json.load(f)
        buildings_schema = schema.get("buildings", {})
        included = [k for k, v in buildings_schema.items() if v.get("include", False)]
        excluded = [k for k, v in buildings_schema.items() if not v.get("include", False)]
        print(f"  Edificios incluidos ({len(included)}): {sorted(included)}")
        if excluded:
            print(f"  Edificios excluidos ({len(excluded)}): {sorted(excluded)}")
        sim_steps = schema.get("simulation_end_time_step", "?")
        central = schema.get("central_agent", "?")
        seed = schema.get("random_seed", "?")
        print(f"  Simulation steps  : {sim_steps}")
        print(f"  Central agent     : {central}")
        print(f"  Random seed       : {seed}")
        schema_ok = len(included) == EXPECTED_BUILDINGS
        print_row("17 edificios incluidos en schema", schema_ok, f"({len(included)}/17)")
    else:
        print(f"  [FAIL] No se encontro schema.json")
        schema_ok = False

    # 3. Building_X.csv
    sep()
    print("3. BUILDING_X.CSV (17 edificios)")
    sep()
    building_results = []
    for i in range(1, EXPECTED_BUILDINGS + 1):
        path = os.path.join(DATASET_DIR, f"Building_{i}.csv")
        ok, errors = check_file(f"Building_{i}.csv", path, EXPECTED_ROWS, BUILDING_COLS)
        size_kb = os.path.getsize(path) // 1024 if os.path.isfile(path) else 0
        detail = f"{size_kb} KB" if ok else " | ".join(errors)
        print_row(f"Building_{i}.csv", ok, detail)
        building_results.append(ok)

    n_ok = sum(building_results)
    sep()
    print(f"  RESULTADO: {n_ok}/{EXPECTED_BUILDINGS} edificios OK")

    # 4. Archivos de contexto global
    sep()
    print("4. ARCHIVOS DE CONTEXTO (weather, carbon, pricing)")
    sep()
    context_files = [
        ("weather.csv", WEATHER_COLS),
        ("carbon_intensity.csv", CARBON_COLS),
        ("pricing.csv", PRICING_COLS),
        ("Washing_Machine_1.csv", None),
    ]
    context_ok = True
    for fname, cols in context_files:
        path = os.path.join(DATASET_DIR, fname)
        ok, errors = check_file(fname, path, EXPECTED_ROWS, cols)
        size_kb = os.path.getsize(path) // 1024 if os.path.isfile(path) else 0
        detail = f"{size_kb} KB  {EXPECTED_ROWS} filas" if ok else " | ".join(errors)
        print_row(fname, ok, detail)
        if not ok:
            context_ok = False

    # 5. Charger CSVs
    sep()
    print("5. CHARGER CSVs (EV por edificio)")
    sep()
    charger_files = [f for f in os.listdir(DATASET_DIR) if f.startswith("charger_") and f.endswith(".csv")]
    charger_files.sort()

    charger_by_building = {}
    for fname in charger_files:
        parts = fname.replace(".csv", "").split("_")
        if len(parts) >= 3:
            bid = int(parts[1])
            charger_by_building.setdefault(bid, []).append(fname)

    charger_total = 0
    charger_ok_count = 0
    for bid in range(1, EXPECTED_BUILDINGS + 1):
        files = charger_by_building.get(bid, [])
        charger_total += len(files)
        n_ok_c = 0
        for fname in files:
            path = os.path.join(DATASET_DIR, fname)
            ok, _ = check_file(fname, path, EXPECTED_ROWS)
            if ok:
                n_ok_c += 1
                charger_ok_count += 1
        all_ok = (n_ok_c == len(files)) and len(files) > 0
        print_row(f"Edificio_{bid} chargers", all_ok, f"{len(files)} archivos  ({n_ok_c} OK)")

    sep()
    print(f"  RESULTADO: {charger_ok_count}/{charger_total} charger CSVs OK  |  {len(charger_files)} archivos totales")

    # 6. Resumen final
    sep("=")
    print("RESUMEN FINAL")
    sep("=")
    all_ok = (
        n_ok == EXPECTED_BUILDINGS
        and context_ok
        and schema_ok
        and charger_ok_count == charger_total
    )
    estado = "DATASET INTEGRO - APTO PARA ENTRENAMIENTO MADRL" if all_ok else "DATASET CON PROBLEMAS - REVISAR ERRORES ARRIBA"
    print(f"  Building CSVs     : {n_ok}/{EXPECTED_BUILDINGS}")
    print(f"  Archivos contexto : {'OK' if context_ok else 'FALLO'}")
    print(f"  Schema.json       : {'OK' if schema_ok else 'FALLO'}")
    print(f"  Charger CSVs      : {charger_ok_count}/{charger_total}")
    sep()
    print(f"  >>> {estado} <<<")
    sep("=")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
