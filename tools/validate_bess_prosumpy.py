"""
validate_bess_prosumpy.py
=========================
Valida el dimensionamiento BESS de cada edificio usando prosumpy (dispatch_max_sc)
y reporta Self-Sufficiency Rate (SSR) y Self-Consumption Rate (SCR) reales.

Integración con repositorios externos:
  - external/prosumpy  → dispatch_max_sc, print_analysis
  - external/MicroGrids → referencia de metodología LP (ver size_bess_microgrid_lp.py)

Uso:
    python tools/validate_bess_prosumpy.py
    python tools/validate_bess_prosumpy.py --buildings 1 6 11 12
    python tools/validate_bess_prosumpy.py --year 2023
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
PROSUMPY    = ROOT / "external" / "prosumpy"
DATASET_DIR = ROOT / "CityLearn" / "data" / "datasets" / "citylearn_iquitos_2023_2025"
SCHEMA_PATH = DATASET_DIR / "schema.json"

sys.path.insert(0, str(PROSUMPY))
sys.stdout.reconfigure(encoding="utf-8")

# ── Importar prosumpy ──────────────────────────────────────────────────────────
try:
    from prosumpy.dispatch import dispatch_max_sc
    PROSUMPY_OK = True
except ImportError:
    PROSUMPY_OK = False
    print("ADVERTENCIA: prosumpy no disponible — se usa simulación interna equivalente")


# ── Parámetros LFP ────────────────────────────────────────────────────────────
ETA_C  = 0.95
ETA_D  = 0.95
ETA_RT = ETA_C * ETA_D   # 0.9025

COP_BY_TYPE = {
    "industrial": 2.8, "mall": 3.0, "salud_24h": 2.5, "hotelero_24h": 3.0,
    "deportivo": 2.5, "institucional": 2.5, "universitario": 2.8,
    "educacion": 2.5, "educacion_motolineal": 2.5, "educacion_tec": 2.5,
    "portuario_24h": 2.5, "transporte_24h": 3.0, "administrativo": 2.8,
}

# Factor Carnot η → COP_act(T_out) = (8.5+273.15)×η / (T_out−8.5)
ETA_CARNOT = {
    "industrial": 0.193858, "mall": 0.207705, "salud_24h": 0.173087,
    "hotelero_24h": 0.207705, "deportivo": 0.173087, "institucional": 0.173087,
    "universitario": 0.193858, "educacion": 0.173087, "educacion_motolineal": 0.173087,
    "educacion_tec": 0.173087, "portuario_24h": 0.173087, "transporte_24h": 0.207705,
    "administrativo": 0.193858,
}


def cop_actual(eta: float, t_out_arr: np.ndarray) -> np.ndarray:
    """COP variable Carnot hora a hora."""
    t_target = 8.5
    cop = (t_target + 273.15) * eta / np.maximum(t_out_arr - t_target, 0.5)
    return np.clip(cop, 1.5, 5.0)


def load_building(bkey: str, bdata: dict, t_out: np.ndarray) -> tuple[pd.Series, pd.Series]:
    """Carga carga total eléctrica y generación solar de un edificio."""
    df = pd.read_csv(DATASET_DIR / f"{bkey}.csv")
    idx = pd.RangeIndex(len(df))

    nsl   = df["non_shiftable_load"].values
    cd    = df["cooling_demand"].values
    dhw   = df["dhw_demand"].values
    solar = df["solar_generation"].values

    # COP Carnot horario
    cd_dev = bdata.get("cooling_device", {})
    eta    = cd_dev.get("attributes", {}).get("efficiency", 0.193858)
    cop    = cop_actual(eta, t_out[:len(df)])

    dhw_dev = bdata.get("dhw_device", {})
    cop_acs = dhw_dev.get("attributes", {}).get("efficiency", 0.85) if dhw_dev else 0.85

    load_elec = nsl + cd / cop + dhw / cop_acs
    return (
        pd.Series(np.maximum(load_elec, 0), index=idx, name="load"),
        pd.Series(np.maximum(solar, 0),     index=idx, name="solar"),
    )


def simulate_dispatch(
    pv: pd.Series, demand: pd.Series, capacity_kwh: float, max_power_kw: float
) -> dict[str, np.ndarray]:
    """Simula despacho BESS usando prosumpy o implementación interna equivalente."""
    if PROSUMPY_OK:
        param = {
            "BatteryCapacity":   capacity_kwh * 0.80,   # DOD=0.80
            "MaxPower":          max_power_kw,
            "BatteryEfficiency": ETA_RT,
            "InverterEfficiency":0.97,
            "timestep":          1.0,
        }
        return dispatch_max_sc(pv, demand, param, return_series=False)
    else:
        # Implementación interna simplificada (misma lógica que prosumpy)
        n   = len(pv)
        cap = capacity_kwh * 0.80
        soc = np.zeros(n)
        pv2store  = np.zeros(n)
        store2inv = np.zeros(n)
        n_inv = 0.97

        pv_v    = pv.values if hasattr(pv, "values") else np.asarray(pv)
        dem_v   = demand.values if hasattr(demand, "values") else np.asarray(demand)
        pv2inv  = np.minimum(pv_v, dem_v / n_inv)
        res_load = np.maximum(dem_v - pv2inv * n_inv, 0)
        res_pv   = np.maximum(pv_v - dem_v / n_inv, 0)

        for i in range(1, n):
            if soc[i-1] < cap:
                pv2store[i] = min(res_pv[i], max_power_kw,
                                  (cap - soc[i-1]))
            store2inv[i] = min(max_power_kw, res_load[i] / n_inv,
                               soc[i-1])
            soc[i] = min(soc[i-1] - (store2inv[i] - pv2store[i] * ETA_RT), cap)

        inv2load  = pv2inv * n_inv + store2inv * n_inv
        grid2load = np.maximum(dem_v - inv2load, 0)
        inv2grid  = res_pv - pv2store
        return {
            "pv2store":      pv2store,
            "store2inv":     store2inv,
            "LevelOfCharge": soc,
            "inv2load":      inv2load,
            "grid2load":     grid2load,
            "inv2grid":      np.maximum(inv2grid, 0),
        }


def compute_kpis(E: dict, demand: pd.Series, pv: pd.Series, timestep: float = 1.0) -> dict:
    """Calcula KPIs desde resultado de dispatch."""
    dem_v = demand.values if hasattr(demand, "values") else np.asarray(demand)
    pv_v  = pv.values    if hasattr(pv,     "values") else np.asarray(pv)

    total_load   = dem_v.sum() * timestep
    total_pv     = pv_v.sum()  * timestep
    self_cons    = E["inv2load"].sum() * timestep if "inv2load" in E else (dem_v - E["grid2load"]).sum() * timestep
    from_grid    = E["grid2load"].sum() * timestep
    to_grid      = E["inv2grid"].sum() * timestep if "inv2grid" in E else 0.0
    bat_gen      = E["store2inv"].sum() * timestep
    bat_cha      = E["pv2store"].sum()  * timestep

    scr = self_cons / total_pv  * 100 if total_pv > 0 else 0.0
    ssr = self_cons / total_load * 100 if total_load > 0 else 0.0

    return {
        "total_load_kwh":   total_load,
        "total_pv_kwh":     total_pv,
        "self_cons_kwh":    self_cons,
        "from_grid_kwh":    from_grid,
        "to_grid_kwh":      to_grid,
        "bat_charge_kwh":   bat_cha,
        "bat_discharge_kwh":bat_gen,
        "SCR_%":            scr,
        "SSR_%":            ssr,
        "PV_load_ratio_%":  total_pv / total_load * 100 if total_load > 0 else 0.0,
    }


def main(buildings: list[int] | None = None, year_filter: int | None = None):
    if not SCHEMA_PATH.exists():
        print(f"ERROR: Schema no encontrado en {SCHEMA_PATH}")
        sys.exit(1)

    schema = json.load(open(SCHEMA_PATH, encoding="utf-8"))
    weather = pd.read_csv(DATASET_DIR / "weather.csv")
    t_out = weather["outdoor_dry_bulb_temperature"].values

    # Filtrar por año si se especifica
    if year_filter:
        # 26304 horas: 2023=0..8759, 2024=8760..17543, 2025=17544..26303
        year_offsets = {2023: (0, 8760), 2024: (8760, 17544), 2025: (17544, 26304)}
        if year_filter not in year_offsets:
            print(f"ERROR: año {year_filter} no válido (usar 2023, 2024 o 2025)")
            sys.exit(1)
        s, e = year_offsets[year_filter]
    else:
        s, e = 0, None

    target_ssr = 70.0  # target MADRL

    print("=" * 100)
    print("VALIDACIÓN BESS — prosumpy dispatch_max_sc (Maximización Autoconsumo)")
    print(f"  Fuente: external/prosumpy/prosumpy/dispatch.py | DOD=0.80 | η_RT={ETA_RT:.4f}")
    print(f"  Target SSR ≥ {target_ssr:.0f}%  (OE.1 Flexibilidad)")
    if year_filter:
        print(f"  Período: {year_filter} (horas {s}–{e})")
    print("=" * 100)
    print(f"\n  {'B':>3}  {'Edificio':<35}  {'Cap kWh':>8}  {'Pot kW':>7}  "
          f"{'PV kWh':>10}  {'Carga kWh':>10}  {'PV/Load%':>8}  "
          f"{'SCR%':>6}  {'SSR%':>6}  {'Status':>8}")
    print("  " + "-" * 98)

    results = {}
    for bkey in sorted(schema["buildings"].keys(), key=lambda k: int(k.split("_")[1])):
        bid = int(bkey.split("_")[1])
        if buildings and bid not in buildings:
            continue

        bdata = schema["buildings"][bkey]
        load_full, solar_full = load_building(bkey, bdata, t_out)

        # Aplicar filtro de año
        load_s  = load_full.iloc[s:e]  if e else load_full
        solar_s = solar_full.iloc[s:e] if e else solar_full

        # Capacidad BESS del schema (atributos bajo "attributes" o nivel raíz)
        es   = bdata.get("electrical_storage", {})
        attr = es.get("attributes", es)   # compatibilidad con ambas estructuras
        cap  = attr.get("capacity", 0)
        pwr  = attr.get("nominal_power", 0)

        if cap == 0 or pwr == 0:
            print(f"  {bid:>3}  {'(sin BESS)':>35}")
            continue

        # Simular con prosumpy
        E   = simulate_dispatch(solar_s, load_s, cap, pwr)
        kpi = compute_kpis(E, load_s, solar_s)

        ssr    = kpi["SSR_%"]
        scr    = kpi["SCR_%"]
        status = "✓ OK" if ssr >= target_ssr else "✗ BAJO"

        name = bdata.get("name", bkey)[:34]
        print(f"  {bid:>3}  {name:<35}  {cap:>8.0f}  {pwr:>7.0f}  "
              f"{kpi['total_pv_kwh']:>10.0f}  {kpi['total_load_kwh']:>10.0f}  "
              f"{kpi['PV_load_ratio_%']:>8.1f}  "
              f"{scr:>6.1f}  {ssr:>6.1f}  {status:>8}")
        results[bid] = kpi

    # Resumen
    if results:
        avg_ssr = np.mean([v["SSR_%"] for v in results.values()])
        avg_scr = np.mean([v["SCR_%"] for v in results.values()])
        below   = [bid for bid, v in results.items() if v["SSR_%"] < target_ssr]
        print("\n" + "=" * 100)
        print(f"  RESUMEN:  SSR promedio = {avg_ssr:.1f}%  |  SCR promedio = {avg_scr:.1f}%")
        print(f"  {len(results) - len(below)}/{len(results)} edificios cumplen SSR ≥ {target_ssr:.0f}%")
        if below:
            print(f"  Edificios bajo target: B{', B'.join(str(b) for b in below)}")
            print("  → Considerar aumentar capacidad BESS con size_bess_optimal.py")
        print("=" * 100)

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Valida BESS de Iquitos con prosumpy dispatch_max_sc"
    )
    parser.add_argument("--buildings", nargs="+", type=int,
                        help="IDs de edificios a validar (default: todos)")
    parser.add_argument("--year", type=int, choices=[2023, 2024, 2025],
                        help="Filtrar por año (default: 2023+2024+2025)")
    args = parser.parse_args()
    main(buildings=args.buildings, year_filter=args.year)
