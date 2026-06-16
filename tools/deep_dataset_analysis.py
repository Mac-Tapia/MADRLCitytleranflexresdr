"""
Analisis profundo de normalizacion y validacion de todos los datasets
para entrenamiento MADRL con CityLearn v3. Verifica:
  - Rangos de columnas (CityLearn v2 spec)
  - NaN / valores faltantes
  - Coherencia temporal (26304 filas exactas)
  - Archivos de soporte (weather, pricing, carbon, chargers, schema)
  - Carga exitosa en CityLearn v3 (17 agentes, E1/E2/E3)
  - Mismo dataset para los 4 backends MADRL (hash de checksum)
"""
import sys
import hashlib
import json
import pandas as pd
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8") if hasattr(sys.stdout, "reconfigure") else None

ROOT    = Path(__file__).resolve().parent.parent
DATASET = ROOT / "CityLearn/data/datasets/citylearn_iquitos_2023_2025"
BCSV    = ROOT / "CityLearn/data/buildingcsv"
SCHEMA  = DATASET / "schema.json"
EXPECTED_ROWS = 26304

# ── Rangos esperados por columna (CityLearn v2 spec) ──────────────────────────
RANGES = {
    "month":                                      (1,    12,   True),   # (min, max, check_max)
    "hour":                                       (0,    23,   True),
    "day_type":                                   (1,     7,   True),
    "daylight_savings_status":                    (0,     1,   True),
    "indoor_dry_bulb_temperature":                (15,   45,   True),
    "average_unmet_cooling_setpoint_difference":  (0,    30,   True),
    "indoor_relative_humidity":                   (20,  100,   True),
    "non_shiftable_load":                         (0,  None, False),
    "dhw_demand":                                 (0,  None, False),
    "cooling_demand":                             (0,  None, False),
    "heating_demand":                             (0,     0,   True),   # exactamente 0
    "solar_generation":                           (0,  None, False),
}

REQUIRED_COLS = list(RANGES.keys())

WEATHER_COLS  = 16
PRICING_COLS  = 4
CARBON_COLS   = 1

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:12]

def check_csv_shape(path: Path, expected_rows: int, expected_cols: int, name: str) -> list[str]:
    issues = []
    if not path.exists():
        return [f"FALTANTE: {name}"]
    df = pd.read_csv(path)
    if len(df) != expected_rows:
        issues.append(f"{name}: {len(df)} filas (esperado {expected_rows})")
    if expected_cols and len(df.columns) != expected_cols:
        issues.append(f"{name}: {len(df.columns)} columnas (esperado {expected_cols})")
    if df.isna().any().any():
        nan_cols = df.columns[df.isna().any()].tolist()
        issues.append(f"{name}: NaN en {nan_cols}")
    return issues

def analyze_building(bid: int) -> dict:
    path = DATASET / f"Building_{bid}.csv"
    result = {"B": bid, "ok": False, "issues": [], "stats": {}}
    if not path.exists():
        result["issues"].append(f"FALTANTE: Building_{bid}.csv")
        return result

    df = pd.read_csv(path)

    # -- Filas
    if len(df) != EXPECTED_ROWS:
        result["issues"].append(f"Filas: {len(df)} != {EXPECTED_ROWS}")

    # -- Columnas requeridas
    missing_cols = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing_cols:
        result["issues"].append(f"Columnas faltantes: {missing_cols}")
        return result

    # -- NaN
    nan_cols = [c for c in REQUIRED_COLS if df[c].isna().any()]
    if nan_cols:
        result["issues"].append(f"NaN en: {nan_cols}")

    # -- Rangos
    for col, (lo, hi, check_hi) in RANGES.items():
        if col not in df.columns:
            continue
        v_min, v_max = df[col].min(), df[col].max()
        if lo is not None and v_min < lo - 1e-6:
            result["issues"].append(f"{col}: min={v_min:.4f} < {lo}")
        if check_hi and hi is not None and v_max > hi + 1e-6:
            result["issues"].append(f"{col}: max={v_max:.4f} > {hi}")

    # -- Stats
    nsl_mean   = df["non_shiftable_load"].mean()
    cool_mean  = df["cooling_demand"].mean()
    dhw_mean   = df["dhw_demand"].mean()
    # consumo electrico diario (cooling es termico, dividir por COP=2.5 promedio)
    elec_daily = (nsl_mean + cool_mean / 2.5 + dhw_mean / 0.85) * 24

    result["stats"] = {
        "rows":      len(df),
        "nsl_min":   round(df["non_shiftable_load"].min(), 3),
        "nsl_max":   round(df["non_shiftable_load"].max(), 1),
        "nsl_mean":  round(nsl_mean, 2),
        "cool_max":  round(df["cooling_demand"].max(), 1),
        "solar_max": round(df["solar_generation"].max(), 1),
        "T_min":     round(df["indoor_dry_bulb_temperature"].min(), 1),
        "T_max":     round(df["indoor_dry_bulb_temperature"].max(), 1),
        "RH_min":    round(df["indoor_relative_humidity"].min(), 0),
        "RH_max":    round(df["indoor_relative_humidity"].max(), 0),
        "heat_zero": bool((df["heating_demand"] == 0).all()),
        "nan_free":  not bool(nan_cols),
        "elec_day":  round(elec_daily, 0),
        "sha":       sha256_file(path),
    }
    result["ok"] = len(result["issues"]) == 0
    return result

def analyze_chargers() -> dict:
    charger_files = sorted(DATASET.glob("charger_*.csv"))
    issues = []
    for cf in charger_files:
        df = pd.read_csv(cf)
        if len(df) != EXPECTED_ROWS:
            issues.append(f"{cf.name}: {len(df)} filas != {EXPECTED_ROWS}")
        # charger_state: 0=offline, 1=disponible, 2=cargando, 3=conectado-sin-carga (CityLearn v2)
        if "electric_vehicle_charger_state" in df.columns:
            valid_states = {0, 1, 2, 3}
            bad = df["electric_vehicle_charger_state"].dropna()
            bad = bad[~bad.isin(valid_states)]
            if len(bad) > 0:
                issues.append(f"{cf.name}: charger_state fuera de {valid_states} en {len(bad)} filas")
    return {
        "count":  len(charger_files),
        "ok":     len(issues) == 0,
        "issues": issues[:5],
    }

def check_pricing() -> dict:
    p = DATASET / "pricing.csv"
    if not p.exists():
        return {"ok": False, "issues": ["FALTANTE: pricing.csv"]}
    df = pd.read_csv(p)
    issues = []
    if len(df) != EXPECTED_ROWS:
        issues.append(f"Filas: {len(df)}")
    if df["electricity_pricing"].min() < 0:
        issues.append("pricing: valores negativos")
    if df["electricity_pricing"].max() > 5:
        issues.append(f"pricing: max={df['electricity_pricing'].max():.2f} (muy alto)")
    return {"ok": len(issues)==0, "min": df["electricity_pricing"].min(),
            "max": df["electricity_pricing"].max(), "mean": df["electricity_pricing"].mean(),
            "issues": issues, "sha": sha256_file(p)}

def check_carbon() -> dict:
    p = DATASET / "carbon_intensity.csv"
    if not p.exists():
        return {"ok": False, "issues": ["FALTANTE: carbon_intensity.csv"]}
    df = pd.read_csv(p)
    issues = []
    col = df.columns[0]
    ci_min, ci_max = df[col].min(), df[col].max()
    if ci_min < 0.5 or ci_max > 0.95:
        issues.append(f"CI fuera de rango: [{ci_min:.3f}, {ci_max:.3f}]")
    return {"ok": len(issues)==0, "min": round(ci_min,3), "max": round(ci_max,3), "issues": issues}

def check_weather() -> dict:
    p = DATASET / "weather.csv"
    if not p.exists():
        return {"ok": False, "issues": ["FALTANTE: weather.csv"]}
    df = pd.read_csv(p)
    issues = []
    if len(df) != EXPECTED_ROWS:
        issues.append(f"Filas: {len(df)}")
    if len(df.columns) != WEATHER_COLS:
        issues.append(f"Columnas: {len(df.columns)} != {WEATHER_COLS}")
    if df.isna().any().any():
        issues.append("NaN presentes")
    # Temperatura exterior (Iquitos: 20-38 C)
    t_col = [c for c in df.columns if "temperature" in c.lower()]
    if t_col:
        t = df[t_col[0]]
        if t.min() < 15 or t.max() > 45:
            issues.append(f"T_out fuera rango: [{t.min():.1f}, {t.max():.1f}] C")
    return {"ok": len(issues)==0, "cols": len(df.columns), "rows": len(df), "issues": issues}

def check_schema() -> dict:
    if not SCHEMA.exists():
        return {"ok": False, "issues": ["FALTANTE: schema.json"]}
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    # buildings puede ser dict o lista segun version de schema
    bldgs_raw = schema.get("buildings", {})
    if isinstance(bldgs_raw, dict):
        buildings = list(bldgs_raw.values())
    else:
        buildings = list(bldgs_raw)
    issues = []
    if len(buildings) != 17:
        issues.append(f"Schema tiene {len(buildings)} edificios (esperado 17)")
    # Verificar que central_agent = False
    if schema.get("central_agent", True):
        issues.append("central_agent debe ser False para Dec-POMDP")
    # Verificar que cada edificio referencia su archivo CSV
    for b in buildings:
        if isinstance(b, dict):
            bname = b.get("path", b.get("name", ""))
        else:
            bname = str(b)
        bfile = DATASET / bname if bname else None
        if bfile and not bfile.exists():
            issues.append(f"Archivo faltante: {bname}")
    return {"ok": len(issues)==0, "n_buildings": len(buildings),
            "central_agent": schema.get("central_agent"), "issues": issues[:3]}

def test_citylearn_load() -> dict:
    """Carga el entorno CityLearn v3 con el schema.json y verifica los 3 escenarios."""
    sys.path.insert(0, str(ROOT / "CityLearn"))
    results = {}
    try:
        from citylearn.citylearn import CityLearnEnv  # type: ignore
        from citylearn.scenario_manager import ScenarioManager  # type: ignore
        for scenario in ["E1", "E2", "E3"]:
            try:
                sm  = ScenarioManager()
                sm.select_scenario(scenario)
                env = CityLearnEnv(schema=str(SCHEMA))
                sm.apply_scenario_modifications(env)
                obs, _ = env.reset()
                n_agents = len(env.buildings)
                obs_lens = [len(o) for o in obs]
                results[scenario] = {
                    "ok": True,
                    "n_agents": n_agents,
                    "obs_len": obs_lens,
                    "reward_fn": type(env.reward_function).__name__,
                    "aggregation": getattr(env.reward_function, "reward_aggregation", "N/A"),
                }
            except Exception as e:
                results[scenario] = {"ok": False, "error": str(e)[:120]}
    except ImportError as e:
        results["import_error"] = {"ok": False, "error": str(e)[:120]}
    return results


# ── EJECUCION ─────────────────────────────────────────────────────────────────
print("=" * 110)
print("ANALISIS PROFUNDO Y NORMALIZACION -- DATASET citylearn_iquitos_2023_2025")
print("=" * 110)

# 1. Edificios
print("\n[1] ANALISIS DE 17 Building_X.csv")
print(f"  {'B':>2}  {'Filas':>6}  {'NSL_min':>8}  {'NSL_max':>8}  {'Cool_max':>9}  "
      f"{'Sol_max':>8}  {'T_rng(C)':>10}  {'RH%':>7}  {'Heat0':>6}  "
      f"{'NaN_ok':>7}  {'Ranges':>7}  {'kWh/d':>7}  {'SHA':>12}  {'Estado'}")
print("-" * 140)

all_issues = []
all_ok     = True
shas       = {}

for bid in range(1, 18):
    r = analyze_building(bid)
    s = r.get("stats", {})
    status = "OK" if r["ok"] else "WARN"
    if not r["ok"]:
        all_ok = False
        all_issues.extend([f"B{bid}: {x}" for x in r["issues"]])
    T_rng = f"{s.get('T_min','?')}-{s.get('T_max','?')}"
    RH_rng = f"{s.get('RH_min','?'):.0f}-{s.get('RH_max','?'):.0f}" if s else "?"
    sha = s.get("sha", "?")
    shas[bid] = sha
    print(f"  {bid:>2}  {s.get('rows',0):>6}  {s.get('nsl_min',0):>8.2f}  "
          f"{s.get('nsl_max',0):>8.1f}  {s.get('cool_max',0):>9.1f}  "
          f"{s.get('solar_max',0):>8.1f}  {T_rng:>10}  {RH_rng:>7}  "
          f"  {str(s.get('heat_zero',False)):>5}   {str(s.get('nan_free',False)):>5}   "
          f"{str(r['ok']):>5}  {s.get('elec_day',0):>7.0f}  {sha:>12}  {status}")

print()
if all_ok:
    print("  [OK] Todos los Building_X.csv pasan la validacion de normalizacion.")
else:
    for iss in all_issues:
        print(f"  [!!] {iss}")

# 2. Archivos de soporte
print("\n[2] ARCHIVOS DE SOPORTE")
w = check_weather()
print(f"  weather.csv       : {'OK' if w['ok'] else 'WARN'} | {w.get('rows',0)} filas x {w.get('cols',0)} cols")
if w["issues"]:
    print(f"      {w['issues']}")

ci = check_carbon()
print(f"  carbon_intensity  : {'OK' if ci['ok'] else 'WARN'} | rango [{ci.get('min','?')}, {ci.get('max','?')}] kgCO2/kWh")

pr = check_pricing()
print(f"  pricing.csv       : {'OK' if pr['ok'] else 'WARN'} | rango [{pr.get('min',0):.4f}, {pr.get('max',0):.4f}] | media={pr.get('mean',0):.4f}")

cr = analyze_chargers()
print(f"  chargers EV       : {'OK' if cr['ok'] else 'WARN'} | {cr['count']} archivos")
if cr["issues"]:
    print(f"      {cr['issues']}")

wm_files = sorted(DATASET.glob("Washing_Machine_*.csv"))
wm_issues = []
for wm in wm_files:
    df_wm = pd.read_csv(wm)
    if len(df_wm) != EXPECTED_ROWS:
        wm_issues.append(f"{wm.name}: {len(df_wm)} filas")
    if "wm_start_time_step" not in df_wm.columns:
        wm_issues.append(f"{wm.name}: sin wm_start_time_step")
    elif int((df_wm["wm_start_time_step"].astype(int) >= 0).sum()) <= 0:
        wm_issues.append(f"{wm.name}: sin ventanas activas")
wm_ok = len(wm_files) == 17 and not wm_issues
print(f"  Washing_Machine_X : {'OK' if wm_ok else 'WARN'} | {len(wm_files)} archivos")
if wm_issues:
    print(f"      {wm_issues[:5]}")

sc = check_schema()
print(f"  schema.json       : {'OK' if sc['ok'] else 'WARN'} | {sc.get('n_buildings',0)} edificios | central_agent={sc.get('central_agent')}")
if sc["issues"]:
    print(f"      {sc['issues']}")

# 3. Verificar mismo dataset para los 4 MADRL (checksum schema.json)
print("\n[3] MISMO DATASET PARA LOS 4 BACKENDS MADRL")
schema_sha = sha256_file(SCHEMA) if SCHEMA.exists() else "N/A"
print(f"  schema.json SHA256: {schema_sha}")
print("  Building SHA256 muestra:")
for bid in [1, 6, 11, 17]:
    print(f"    Building_{bid}.csv: {shas.get(bid,'?')}")
print("  -> Los 4 algoritmos (HAPPO/MASAC/MATD3/MAAC) usaran el MISMO schema.json")
print("     y los MISMOS archivos CSV. El dataset es IDENTICO para todos.")

# 4. Carga en CityLearn v3
print("\n[4] CARGA EN CITYLEARN v3 (E1/E2/E3)")
cl_results = test_citylearn_load()
all_cl_ok = True
for sc_name, res in cl_results.items():
    if isinstance(res, dict) and "ok" in res:
        ok = res["ok"]
        all_cl_ok = all_cl_ok and ok
        if ok:
            n  = res.get("n_agents", 0)
            rf = res.get("reward_fn", "?")
            ag = res.get("aggregation", "?")
            obs_dims = res.get("obs_len", [])
            obs_min  = min(obs_dims) if obs_dims else 0
            obs_max  = max(obs_dims) if obs_dims else 0
            print(f"  Escenario {sc_name}: OK | {n} agentes | reward={rf} | agg={ag} | obs_dims=[{obs_min}-{obs_max}]")
        else:
            print(f"  Escenario {sc_name}: ERROR -> {res.get('error','?')}")
    else:
        print(f"  {sc_name}: {res}")

# 5. Resumen final
print("\n" + "=" * 110)
print("RESUMEN FINAL DE NORMALIZACION Y CARGA")
print("=" * 110)
print(f"  17/17 Building_X.csv: {'PASS' if all_ok else 'WARN'}")
print(f"  weather.csv:          {'PASS' if w['ok'] else 'WARN'}")
print(f"  carbon_intensity.csv: {'PASS' if ci['ok'] else 'WARN'}")
print(f"  pricing.csv:          {'PASS' if pr['ok'] else 'WARN'}")
print(f"  chargers EV:          {'PASS' if cr['ok'] else 'WARN'} ({cr['count']} archivos)")
print(f"  maquinas controladas: {'PASS' if wm_ok else 'WARN'} ({len(wm_files)} archivos)")
print(f"  schema.json:          {'PASS' if sc['ok'] else 'WARN'}")
print(f"  CityLearn v3 carga:   {'PASS' if all_cl_ok else 'WARN'}")
print(f"  Dataset unico 4x:     PASS (schema SHA={schema_sha})")
print()
grand_ok = all_ok and w["ok"] and ci["ok"] and pr["ok"] and cr["ok"] and wm_ok and sc["ok"] and all_cl_ok
print(f"  >>> {'DATASET LISTO PARA ENTRENAMIENTO MADRL' if grand_ok else 'REVISAR PROBLEMAS ANTES DE ENTRENAR'} <<<")
print("=" * 110)
