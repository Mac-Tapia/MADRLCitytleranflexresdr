"""
distill_building_loads.py
=========================
Ingeniería de destilación: calibra cooling_demand y non_shiftable_load con
mediciones reales de medidores ELECTRO ORIENTE para los 9 edificios con datos.

Algoritmo (proporcional) por edificio, por mes:
  E_total_sintetico[mes] = E_gest[mes] + E_ns[mes]
                         = sum(cooling/COP + dhw/COP_ACS) + sum(nsl)

  scale[mes] = E_medido[mes] / E_total_sintetico[mes]

  cooling_demand_nuevo[t] = cooling_demand[t] * scale[mes_de_t]
  nsl_nuevo[t]            = nsl[t]            * scale[mes_de_t]

Mantiene la proporción relativa cooling/NSL mientras ajusta el total al
valor medido. Correcto incluso cuando E_gest > E_medido (datos sintéticos
sobreestiman), evitando el scale=0 del enfoque anterior.

Uso:
    python tools/distill_building_loads.py
    python tools/distill_building_loads.py --buildings 11 12
    python tools/distill_building_loads.py --dry-run
    python tools/distill_building_loads.py --report-only
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ── Rutas ──────────────────────────────────────────────────────────────────────
ROOT        = Path(__file__).resolve().parent.parent
DATASET_DIR = ROOT / "CityLearn" / "data" / "datasets" / "citylearn_iquitos_2023_2025"
SCHEMA_PATH = DATASET_DIR / "schema.json"
WEATHER_CSV = DATASET_DIR / "weather.csv"

sys.stdout.reconfigure(encoding="utf-8")

# ── Parámetros físicos ─────────────────────────────────────────────────────────
T_TARGET      = 8.5        # °C temperatura target del chiller (CityLearn default)
COP_ACS_DEF   = 0.85       # calefón eléctrico resistivo (sin bomba de calor ACS)
COP_CLIP_LOW  = 1.5
COP_CLIP_HIGH = 5.0

# ── Factor Carnot η por edificio (fallback cuando schema tiene attributes vacíos)
# Fuente: plan dataset — COP_diseno/cop_factor_avg donde cop_factor_avg=14.44
ETA_BY_BLDG: dict[int, float] = {
    1:  0.193858,   # industrial       (Electro Oriente S.A.)
    7:  0.193858,   # universitario    (UNAP Zungarococha)
    8:  0.173087,   # educacion        (Escuela Técnica PNP)
    10: 0.193858,   # administrativo   (Gobierno Regional Loreto)
    11: 0.173087,   # salud_24h        (Hospital Regional Loreto)
    12: 0.173087,   # salud_24h        (EsSalud Hospital III)
    13: 0.193858,   # universitario    (Facultad Economía UNAP)
    14: 0.173087,   # portuario_24h    (Terminal Portuario ENAPU)
    15: 0.173087,   # educacion        (Colegio Nacional CNI)
}

# ── Medidas reales ELECTRO ORIENTE (kWh/mes por año) ──────────────────────────
# Formato: {bldg_id: {año: {mes: kWh_medido}}}
# Valores actuales: promedios mensuales del estudio GD-Iquitos V3.
# Para mayor precisión: reemplazar con valores reales por mes/año del xlsx.
#
# FUENTE: Resultados_Preliminares-GD-Iquitos_V3 (2).xlsx
#   - Consumo mensual ELECTRO ORIENTE 2023–2025 por medidor
#   - B11 suma dos medidores (0104005T + 0104007T)
# ─────────────────────────────────────────────────────────────────────────────
def _flat(kwh_mes: float) -> dict[int, dict[int, float]]:
    """Genera dict {año: {mes: valor}} con el mismo valor para todos los meses."""
    return {y: {m: kwh_mes for m in range(1, 13)} for y in (2023, 2024, 2025)}


MEDIDAS_REALES: dict[int, dict[int, dict[int, float]]] = {
    1:  _flat(482_735),
    7:  _flat(13_089),
    8:  _flat(8_925),
    10: _flat(100_751),
    11: _flat(299_141),
    12: _flat(192_207),
    13: _flat(12_367),
    14: _flat(29_203),
    15: _flat(14_171),
}

BUILDINGS_WITH_DATA = sorted(MEDIDAS_REALES.keys())


# ── Utilidades ─────────────────────────────────────────────────────────────────

def load_schema() -> dict:
    if not SCHEMA_PATH.exists():
        print(f"ERROR: schema.json no encontrado en {SCHEMA_PATH}")
        sys.exit(1)
    return json.load(open(SCHEMA_PATH, encoding="utf-8"))


def load_weather() -> np.ndarray:
    """Carga temperatura exterior del weather.csv → array shape (26304,)."""
    if not WEATHER_CSV.exists():
        print(f"ERROR: weather.csv no encontrado en {WEATHER_CSV}")
        sys.exit(1)
    df = pd.read_csv(WEATHER_CSV, usecols=["outdoor_dry_bulb_temperature"])
    return df["outdoor_dry_bulb_temperature"].values


def get_cop_params(schema: dict, bldg_id: int) -> tuple[float, float]:
    """
    Extrae (eta_carnot, cop_acs) para el edificio dado.

    Prioridad eta_carnot:
      1. schema.json → cooling_device.attributes.efficiency
      2. ETA_BY_BLDG[bldg_id]  (tabla por tipo de edificio)
      3. 0.193858               (administrativo, fallback global)

    cop_acs: schema dhw_device.attributes.efficiency o COP_ACS_DEF.
    """
    bkey  = f"Building_{bldg_id}"
    bldgs = schema.get("buildings", {})
    bdata = bldgs.get(bkey, {}) if isinstance(bldgs, dict) else {}

    # ── eta Carnot ─────────────────────────────────────────────────────────
    cd   = bdata.get("cooling_device", {})
    attr = cd.get("attributes", {})
    if isinstance(attr, dict) and "efficiency" in attr and attr["efficiency"]:
        eta = float(attr["efficiency"])
    else:
        # Fallback 1: tabla por tipo de edificio
        eta = ETA_BY_BLDG.get(bldg_id, 0.193858)

    # ── COP ACS ────────────────────────────────────────────────────────────
    dhw = bdata.get("dhw_device", {})
    if dhw:
        dattr   = dhw.get("attributes", {}) if isinstance(dhw, dict) else {}
        cop_acs = float(dattr.get("efficiency", COP_ACS_DEF)) if dattr else COP_ACS_DEF
    else:
        cop_acs = COP_ACS_DEF

    return eta, cop_acs


def compute_cop_array(t_out: np.ndarray, eta: float) -> np.ndarray:
    """COP variable hora a hora (Carnot).
    COP_act[t] = (T_target + 273.15) * eta / max(T_out[t] - T_target, 0.5)
    Clipped a [COP_CLIP_LOW, COP_CLIP_HIGH].
    """
    denom = np.maximum(t_out - T_TARGET, 0.5)
    cop   = (T_TARGET + 273.15) * eta / denom
    return np.clip(cop, COP_CLIP_LOW, COP_CLIP_HIGH)


def compute_managed_energy(df: pd.DataFrame,
                           cop_act: np.ndarray,
                           cop_acs: float) -> np.ndarray:
    """
    E_gest[t] = cooling_demand[t] / COP_act[t]
              + dhw_demand[t]     / cop_acs
    Retorna kWh eléctrico por hora.
    """
    cd = df["cooling_demand"].values if "cooling_demand" in df.columns else np.zeros(len(df))
    dw = df["dhw_demand"].values     if "dhw_demand"     in df.columns else np.zeros(len(df))
    return cd / cop_act + dw / cop_acs


def build_month_year_index(df: pd.DataFrame) -> pd.DataFrame:
    """
    Añade columnas auxiliares '_year' y '_month' al df a partir del orden de
    filas (2023→2024→2025) y la columna 'month'.
    """
    n = len(df)
    years_arr = np.empty(n, dtype=int)
    years_arr[:8760]               = 2023
    years_arr[8760:8760 + 8784]    = 2024
    years_arr[8760 + 8784:]        = 2025

    df = df.copy()
    df["_year"]  = years_arr
    df["_month"] = df["month"].values.astype(int)
    return df


# ── Calibración principal ──────────────────────────────────────────────────────

def calibrate_building(bldg_id: int,
                       schema: dict,
                       t_out: np.ndarray,
                       dry_run: bool = False,
                       report_only: bool = False) -> pd.DataFrame:
    """
    Calibra cooling_demand y non_shiftable_load del edificio bldg_id con
    mediciones reales usando escala proporcional.

    Algoritmo por mes:
      E_total_syn = E_gest + E_ns_orig
      scale       = E_medido / E_total_syn
      cd_nuevo    = cd_orig  * scale
      nsl_nuevo   = nsl_orig * scale

    Retorna DataFrame de reporte con:
        year, mes, E_medido, E_total_syn, E_gest, E_ns_orig,
        scale_factor, E_calibrado, delta_%
    """
    csv_path = DATASET_DIR / f"Building_{bldg_id}.csv"
    if not csv_path.exists():
        print(f"  SKIP B{bldg_id}: {csv_path.name} no encontrado")
        return pd.DataFrame()

    df = pd.read_csv(csv_path)
    if len(df) != len(t_out):
        print(f"  ERROR B{bldg_id}: filas={len(df)} ≠ weather={len(t_out)}")
        return pd.DataFrame()

    eta, cop_acs = get_cop_params(schema, bldg_id)
    cop_act      = compute_cop_array(t_out, eta)
    e_gest       = compute_managed_energy(df, cop_act, cop_acs)

    cd_orig  = df["cooling_demand"].values.copy()
    dw_orig  = df["dhw_demand"].values.copy()  if "dhw_demand" in df.columns else np.zeros(len(df))
    nsl_orig = df["non_shiftable_load"].values.copy()

    df = build_month_year_index(df)
    medidas = MEDIDAS_REALES[bldg_id]

    cd_nuevo  = cd_orig.copy()
    dw_nuevo  = dw_orig.copy()
    nsl_nuevo = nsl_orig.copy()
    report_rows = []

    for year in (2023, 2024, 2025):
        if year not in medidas:
            continue
        for month in range(1, 13):
            mask = (df["_year"] == year) & (df["_month"] == month)
            idx  = np.where(mask.values)[0]
            if len(idx) == 0:
                continue

            e_med = medidas[year].get(month, None)
            if e_med is None:
                continue

            e_gest_mes  = float(e_gest[idx].sum())   # cd/cop + dw/cop_acs
            e_ns_orig   = float(nsl_orig[idx].sum())
            e_total_syn = e_gest_mes + e_ns_orig      # total eléctrico sintético

            if e_total_syn > 0:
                scale = e_med / e_total_syn
            else:
                scale = 1.0

            # Escala proporcional: mantiene ratio cooling/DHW/NSL
            cd_nuevo[idx]  = cd_orig[idx]  * scale
            dw_nuevo[idx]  = dw_orig[idx]  * scale
            nsl_nuevo[idx] = nsl_orig[idx] * scale

            # Verificación: energía calibrada total (incluye DHW)
            e_cd_cal   = float((cd_nuevo[idx] / cop_act[idx]).sum())
            e_dw_cal   = float((dw_nuevo[idx] / cop_acs).sum())
            e_ns_cal   = float(nsl_nuevo[idx].sum())
            e_cal_tot  = e_cd_cal + e_dw_cal + e_ns_cal

            delta_pct  = (e_cal_tot - e_med) / max(e_med, 1.0) * 100.0

            report_rows.append({
                "year":         year,
                "mes":          month,
                "E_medido_kWh": round(e_med, 1),
                "E_total_syn":  round(e_total_syn, 1),
                "E_gest_kWh":   round(e_gest_mes, 1),
                "E_ns_orig":    round(e_ns_orig, 1),
                "scale_factor": round(scale, 6),
                "E_cal_tot":    round(e_cal_tot, 1),
                "delta_%":      round(delta_pct, 4),
            })

    report = pd.DataFrame(report_rows)

    has_dhw = "dhw_demand" in pd.read_csv(csv_path, nrows=0).columns

    if not report_only and not dry_run:
        df_out = pd.read_csv(csv_path)
        df_out["cooling_demand"]    = cd_nuevo
        df_out["non_shiftable_load"] = nsl_nuevo
        if has_dhw:
            df_out["dhw_demand"] = dw_nuevo
        df_out.to_csv(csv_path, index=False, float_format="%.6f")

    return report


# ── Reporte por consola ────────────────────────────────────────────────────────

BLDG_NAMES = {
    1:  "Electro Oriente S.A.",
    7:  "UNAP Zungarococha",
    8:  "Escuela Técnica PNP",
    10: "Gobierno Regional Loreto",
    11: "Hospital Regional Loreto",
    12: "EsSalud Hospital III",
    13: "Facultad Economía UNAP",
    14: "Terminal Portuario ENAPU",
    15: "Colegio Nacional CNI",
}


def print_report(bldg_id: int, report: pd.DataFrame, dry_run: bool, report_only: bool):
    if report.empty:
        return
    name = BLDG_NAMES.get(bldg_id, f"B{bldg_id}")
    mode = "(DRY-RUN)" if dry_run else ("(SOLO REPORTE)" if report_only else "")
    print(f"\n{'='*100}")
    print(f"  B{bldg_id} — {name}  {mode}")
    print(f"  eta_Carnot={ETA_BY_BLDG.get(bldg_id, 0.193858):.6f}")
    print(f"{'='*100}")
    print(f"  {'Año':>4}  {'Mes':>3}  {'E_medido':>10}  {'E_sintét':>9}  "
          f"{'E_gest':>8}  {'E_ns':>8}  {'Scale':>8}  {'E_cal':>9}  {'Δ%':>7}")
    print("  " + "-" * 84)
    for _, row in report.iterrows():
        print(f"  {int(row['year']):>4}  {int(row['mes']):>3}  "
              f"{row['E_medido_kWh']:>10.0f}  {row['E_total_syn']:>9.0f}  "
              f"{row['E_gest_kWh']:>8.0f}  {row['E_ns_orig']:>8.0f}  "
              f"{row['scale_factor']:>8.5f}  {row['E_cal_tot']:>9.0f}  "
              f"{row['delta_%']:>7.4f}")

    avg_scale = report["scale_factor"].mean()
    avg_delta = report["delta_%"].abs().mean()
    print("  " + "-" * 84)
    print(f"  Promedio: scale={avg_scale:.5f}  |Δ%|_medio={avg_delta:.4f}%")

    if not dry_run and not report_only:
        print(f"  → Building_{bldg_id}.csv actualizado (cooling_demand + non_shiftable_load)")


def print_summary(reports: dict[int, pd.DataFrame], dry_run: bool, report_only: bool):
    print(f"\n{'='*100}")
    print("  RESUMEN GLOBAL")
    print(f"{'='*100}")
    print(f"  {'B':>3}  {'Edificio':<35}  {'Scale prom':>10}  {'|Δ%| med':>9}  {'Status':>8}")
    print("  " + "-" * 74)
    for bid, rep in sorted(reports.items()):
        if rep.empty:
            print(f"  {bid:>3}  {BLDG_NAMES.get(bid,''):<35}  {'NO DATA':>10}")
            continue
        name   = BLDG_NAMES.get(bid, f"B{bid}")[:34]
        scale  = rep["scale_factor"].mean()
        delta  = rep["delta_%"].abs().mean()
        status = "✓ OK" if delta < 0.1 else "✗ ERR"
        print(f"  {bid:>3}  {name:<35}  {scale:>10.5f}  {delta:>9.4f}  {status:>8}")

    action = "NO se modificaron archivos (dry-run/report-only)" if (dry_run or report_only) \
             else f"{len([r for r in reports.values() if not r.empty])} Building_X.csv actualizados"
    print(f"\n  → {action}")
    print("  → Columnas modificadas: cooling_demand  +  non_shiftable_load")
    print("="*100)


# ── main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Destilación de cargas: calibra cooling_demand+NSL con mediciones ELOR"
    )
    parser.add_argument(
        "--buildings", nargs="+", type=int, default=BUILDINGS_WITH_DATA,
        help=f"IDs de edificios a procesar (default: {BUILDINGS_WITH_DATA})"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Calcular scale_factors pero NO sobreescribir Building_X.csv"
    )
    parser.add_argument(
        "--report-only", action="store_true",
        help="Solo mostrar tabla de reporte; no modificar ningún archivo"
    )
    args = parser.parse_args()

    dry_run     = args.dry_run
    report_only = args.report_only

    invalid = [b for b in args.buildings if b not in MEDIDAS_REALES]
    if invalid:
        print(f"ADVERTENCIA: edificios {invalid} no tienen medición real — se omiten")
        args.buildings = [b for b in args.buildings if b in MEDIDAS_REALES]

    if not args.buildings:
        print("No hay edificios con medición real para procesar.")
        sys.exit(0)

    print("="*100)
    print("DESTILACIÓN DE CARGAS — Calibración proporcional cooling_demand + NSL")
    print(f"  Dataset:   {DATASET_DIR}")
    mode_str = "DRY-RUN (sin escritura)" if dry_run else \
               "REPORT-ONLY (sin escritura)" if report_only else \
               "ESCRITURA: Building_X.csv serán actualizados (2 columnas)"
    print(f"  Modo:      {mode_str}")
    print(f"  Edificios: {args.buildings}")
    print("="*100)

    schema = load_schema()
    t_out  = load_weather()

    print(f"  weather.csv cargado: {len(t_out)} filas, "
          f"T_out ∈ [{t_out.min():.1f}, {t_out.max():.1f}]°C")

    reports: dict[int, pd.DataFrame] = {}
    for bid in args.buildings:
        reports[bid] = calibrate_building(
            bldg_id=bid,
            schema=schema,
            t_out=t_out,
            dry_run=dry_run,
            report_only=report_only,
        )
        print_report(bid, reports[bid], dry_run, report_only)

    print_summary(reports, dry_run, report_only)


if __name__ == "__main__":
    main()
