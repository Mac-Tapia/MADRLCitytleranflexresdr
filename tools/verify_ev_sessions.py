"""Verifica las sesiones EV en el dataset por hora del dia y por edificio.

Convención de estados CityLearn (charger_X_Y.csv):
  state=1: EV CONECTADO al cargador (controlable por el agente)
  state=2: EV ENTRANTE (próximo a conectarse)
  state=3 (u otro): cargador INACTIVO / vacío
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys
sys.stdout.reconfigure(encoding="utf-8")

DATASET = Path("CityLearn/data/datasets/citylearn_iquitos_2023_2025")

chargers = sorted(DATASET.glob("charger_*.csv"))
print(f"Total cargadores: {len(chargers)}")

# Leer estado de todos los chargers
all_states = []
for cf in chargers:
    df = pd.read_csv(cf)
    all_states.append(df["electric_vehicle_charger_state"].values)

states = np.array(all_states)  # (n_chargers, 26304)
hours  = np.arange(26304) % 24

print("\n=== SESIONES EV POR HORA DEL DIA (state==1: EV conectado/controlable) ===")
for h in range(24):
    mask   = (hours == h)
    # state==1 es el único estado donde el EV está conectado y el agente lo controla
    active = int((states[:, mask] == 1).sum())
    total  = int(states[:, mask].size)
    pct    = 100.0 * active / total if total > 0 else 0
    bar    = "#" * int(pct / 2)
    tag    = " <-- PUNTA TARIFA" if h in range(18, 23) else ""
    print(f"  {h:02d}h | EVs conectados: {active:6d}/{total:6d} ({pct:5.1f}%) {bar}{tag}")

# Resumen por ventana
morning   = (hours >= 6)  & (hours < 12)
afternoon = (hours >= 12) & (hours < 18)
evening   = (hours >= 18) & (hours < 23)
night     = (hours >= 23) | (hours < 6)

print("\n=== RESUMEN POR VENTANA (state==1: EV conectado) ===")
for name, mask in [("Manana 06-12h",        morning),
                   ("Tarde  12-18h",         afternoon),
                   ("Noche-punta 18-23h",    evening),
                   ("Madrugada 23-06h",      night)]:
    a = int((states[:, mask] == 1).sum())
    t = int(states[:, mask].size)
    print(f"  {name}: {a}/{t} ({100.0*a/t:.1f}%)")

# Distribución correcta de estados
print("\n=== DISTRIBUCION REAL DE ESTADOS (todo el dataset) ===")
vals, counts = np.unique(states, return_counts=True)
labels = {
    1: "conectado (EV bajo control del agente)",
    2: "entrante (EV próximo a conectarse)",
    3: "inactivo / cargador vacío",
}
for v, c in zip(vals, counts):
    print(f"  state={v} ({labels.get(int(v), '?')}): {c:12,} ({100.0*c/states.size:.2f}%)")

# Verificar: por edificio, ¿cuántas horas conectadas vs total?
print("\n=== ACTIVIDAD EV POR EDIFICIO (horas con state==1) ===")
building_ids = sorted(set(int(cf.stem.split("_")[1]) for cf in chargers))
for bid in building_ids:
    bchargers = [cf for cf in chargers if int(cf.stem.split("_")[1]) == bid]
    b_states = [pd.read_csv(cf)["electric_vehicle_charger_state"].values for cf in bchargers]
    b_arr = np.array(b_states)
    n_connected = int((b_arr == 1).sum())
    n_total     = b_arr.size
    pct_conn    = 100.0 * n_connected / n_total if n_total > 0 else 0
    print(f"  B{bid:02d} ({len(bchargers):3d} cargadores): {n_connected:7,}/{n_total:9,} pasos conectados ({pct_conn:5.1f}%)")

# Verificar reward EV en live_progress más reciente
print("\n=== VERIFICACION LIVE PROGRESS - EV REWARD ===")
import json
lp_files = sorted(
    list(Path("outputs").glob("**/live_progress.json")),
    key=lambda p: p.stat().st_mtime,
    reverse=True,
)
if lp_files:
    p = json.loads(lp_files[0].read_text(encoding="utf-8"))
    ev_mean   = p.get("reward_component_ev_mean", "campo no encontrado")
    paso      = p.get("global_step", "?")
    ts        = p.get("time_step", 0)
    hora_dia  = int(ts) % 24 if isinstance(ts, (int, float)) else "?"
    print(f"  Archivo live_progress      : {lp_files[0]}")
    print(f"  Paso actual                : {paso}")
    print(f"  time_step => hora del dia  : {ts} => {hora_dia:02d}h")
    print(f"  reward_component_ev_mean   : {ev_mean}")
    print()
    if isinstance(hora_dia, int) and hora_dia in range(0, 7):
        print("  NOTA: hora nocturna — state=1 es raro; EV_mean=0 es CORRECTO.")
    elif isinstance(hora_dia, int):
        print("  NOTA: hora diurna — debe haber state=1 activos; EV_mean deberia ser != 0.")
    print(f"  flex_mean                  : {p.get('reward_component_flex_mean')}")
    print(f"  carbon_mean                : {p.get('reward_component_carbon_mean')}")
    print(f"  cost_mean                  : {p.get('reward_component_cost_mean')}")
    print(f"  team_reward                : {p.get('reward_team_reward')}")
else:
    print("  Sin live_progress encontrado bajo outputs/")
