"""
dimension_ev_chargers.py  v3.0
================================
Dimensionamiento realista de cargadores EV para dataset CityLearn Iquitos 2023-2025.

METODOLOGÍA: Peak Demand Factor (PDF) + Ley de Little (M/G/c queuing)
  N_stalls = ceil(N_daily × (dwell_h / facility_h) × charging_pct / utilization)

  Donde:
    N_daily        = vehículos EV que arriban por día al edificio
    dwell_h        = tiempo medio de permanencia en el lugar [h]
    facility_h     = horas de operación del edificio [h]
    charging_pct   = fracción que carga en ese período
    utilization    = utilización objetivo del cargador (0.70-0.75)

  Referencia: EPRI (2020). EV Infrastructure Deployment Guidelines for Commercial Sites.
              IEC 61851-1 (2019). Electric vehicle conductive charging system — Part 1.
              OSINERGMIN (2022). Guía Técnica Infraestructura de Carga VE Perú.

TIPOS DE EV VERIFICADOS (auditoria vigente):
  moto_lineal: Honda PCX Electric / Kymco Ionex / Sunra / Yadea → 3.0 kW AC, 4.0 kWh
  mototaxi:   trimotos eléctricas amazónicas 60V 75Ah LiFePO4   → 4.0 kW AC, 6.0 kWh
  camioneta:  BYD T3=6.6kW, Maxus eDeliver=7.4kW → usado 7.4 kW (estándar LatAm L2)

NOTA CAMIONETA: búsqueda web verificó BYD T3 Perú=6.6kW, Maxus eDeliver LatAm=7.4kW.
No existe estándar >10kW para furgonetas comerciales en Perú 2023-2025.
Se usa 7.4 kW como máximo comercialmente disponible (Level 2 AC, Type 2, 32A).

HERRAMIENTAS REFERENCIADAS:
  - evnrg (PyPI): fleet EV demand simulation, queuing logic
  - datafev (PyPI): EVSE management algorithms
  - EVI-EnSitePy (NREL): vehicle arrival modeling, peak power estimation
  - ACN-Data (Caltech): session profiles workplace/university (proxy)

DATOS DE AFLUENCIA (observación directa B6 + estimaciones por tipo):
B6 Mall Aventura en hora punta: 930 motos lineales + 150 mototaxis + ≥20 camionetas
  → Dimensionamiento: 22 × 3.0kW + 6 × 4.0kW + 4 × 7.4kW = 32 cargadores B6
"""

import math
import json
import logging
import sys
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from buildingcsv_inputs import load_building_inventory  # noqa: E402
from size_bess_optimal import BUILDING_OPERATION_WINDOWS  # noqa: E402

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "CityLearn" / "data" / "datasets" / "citylearn_iquitos_2023_2025"
OUT_DIR = ROOT / "outputs" / "dataset_audit"
EV_AUDIT_CSV = OUT_DIR / "ev_charger_sizing_audit.csv"
EV_AUDIT_JSON = OUT_DIR / "ev_charger_sizing_audit.json"
EV_DATASET_LOG = BASE / "ev_charger_sizing_log.json"
EV_AUDIT_MD = ROOT / "docs" / "INFORME_AUDITORIA_DIMENSIONAMIENTO_EV_IQUITOS.md"
TOTAL_H = 26304    # 2023 (8760) + 2024 bisiesto (8784) + 2025 (8760)
YEARS   = [2023, 2024, 2025]

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 1 — Especificaciones EV reales Iquitos 2023-2025
# ══════════════════════════════════════════════════════════════════════════════

EV_SPEC = {
    'moto_lineal': {
        # Motos lineales eléctricas Iquitos: Sunra, Yadea, Kymco Ionex (mercado local 2023-25)
        # Batería: 60V 30Ah≈1.8 kWh típico, pero modelos con 4 kWh (Sunra Hawk, Yadea G5S)
        # Cargador Mode 3 AC 3.0 kW (IEC 61851 Modo 3, 13A monofásico 230V)
        # Tiempo carga real: 3.2 kWh / (3.0 kW × 0.92 η) × 1.15 taper = ~80 min
        'charger_kw':    3.0,      # alineado con EV_CONFIG/schema real Iquitos
        'bat_kwh':       4.0,      # alineado con EV_CONFIG/schema real Iquitos
        'ev_label':      'Moto_Lineal_Electrica',
        'dwell_h':       1.5,      # permanencia media en el lugar [h]
        'session_h_mu':  1.33,     # 80 min Mode 3 — validado con batería 4 kWh @ 3 kW
        'session_h_sig': 0.2,
        'soc_arr_mu':    30,       # SOC al llegar [%] — uso intensivo diario en Iquitos
        'soc_arr_sig':   12,
        'soc_req_mu':    85,       # SOC requerido al partir [%]
        'soc_req_sig':   6,
        'min_kw_frac':   0.10,     # mínimo 10% de potencia nominal (IEC 61851 6A)
    },
    'mototaxi': {
        # Mototaxis (trimotos) eléctricas Iquitos: 60V 75Ah LiFePO4 ≈ 6 kWh (dato real)
        # Cargador Mode 3 AC 4.0 kW (60V 67A) — estándar mototaxis eléctricas Loreto 2023-25
        # Tiempo carga real: 2.7 kWh (35→80% SOC) / (4.0 kW × 0.92) × 1.10 = ~48 min parcial
        #   carga completa 80% DOD: 4.8 kWh / 3.68 kW × 1.10 ≈ 1.43h → usuario declara 1.2h
        'charger_kw':    4.0,      # alineado con EV_CONFIG/schema real Iquitos
        'bat_kwh':       6.0,      # alineado con EV_CONFIG/schema real Iquitos
        'ev_label':      'Mototaxi_Electrica',
        'dwell_h':       1.5,      # mototaxi hace parada breve para cargar entre turnos
        'session_h_mu':  1.20,     # 1.2 h Mode 3 — declarado usuario, consistente con spec
        'session_h_sig': 0.2,
        'soc_arr_mu':    35,       # SOC al llegar [%] — mototaxi comercial, llega bajo
        'soc_arr_sig':   12,
        'soc_req_mu':    82,       # SOC requerido al partir [%]
        'soc_req_sig':   6,
        'min_kw_frac':   0.10,
    },
    'camioneta': {
        # Camionetas/vans eléctricas institucionales: BYD T3 (40 kWh), Maxus eDeliver 3 (40 kWh)
        # Cargador Mode 3 AC 7.4 kW (Type 2 Mennekes, 32A monofásico 230V)
        # Tiempo carga real: 14 kWh (50→85% SOC) / (7.4 kW × 0.95) = ~2.0 h
        'charger_kw':    7.4,      # sin cambio — estándar L2 AC LatAm
        'bat_kwh':       40.0,     # alineado con EV_CONFIG/schema (era 47.0)
        'ev_label':      'Camioneta_Electrica',
        'dwell_h':       4.0,      # camioneta carga en ~2h pero permanece más tiempo
        'session_h_mu':  2.00,     # 2.0 h Mode 3 (50→85% SOC) — validado con 40 kWh @ 7.4 kW
        'session_h_sig': 0.4,
        'soc_arr_mu':    35,
        'soc_arr_sig':   12,
        'soc_req_mu':    85,
        'soc_req_sig':   5,
        'min_kw_frac':   0.13,     # mínimo 13% = ~1 kW (no cortar sesión)
    },
}

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 2 — Afluencia diaria EV por edificio (observaciones + estimaciones)
# ══════════════════════════════════════════════════════════════════════════════

BUILDING_NAMES = {
    1:  'Electro Oriente S.A.',
    2:  'Municipalidad Distrital San Juan Bautista',
    3:  'Aeropuerto Internacional de Iquitos',
    4:  'Hipermercados Tottus Oriente',
    5:  'Hotel Plaza S.A.',
    6:  'Mall Aventura Iquitos',
    7:  'UNAP Facultad de Biologia',
    8:  'PNP Escuela Tecnica Superior Iquitos',
    9:  'Gobierno Regional Loreto COER',
    10: 'Gobierno Regional de Loreto',
    11: 'Hospital Regional de Loreto',
    12: 'Seguro Social de Salud EsSalud',
    13: 'UNAP Facultad de Ciencias Economicas',
    14: 'Autoridad Portuaria Nacional Iquitos',
    15: 'DREL Colegio Nacional de Iquitos',
    16: 'SIMA Iquitos S.R.Ltda',
    17: 'Asociacion Civil Selva Amazonica',
}

# Contexto flota Iquitos 2023-2025 (dato usuario + MININTER/MTC):
#   75 000 motos lineales  |  65 000 mototaxis (trimotos)  |  ~500 000 hab.
#   Adopción EV estimada: 20-35 % motos, 15-25 % mototaxis (transición 2023-2025)
#   → Alta densidad EV urbana: 1 moto/6.7 hab, 1 mototaxi/7.7 hab
#
# flag 'remote': edificios alejados del centro (>5 km) donde el usuario DEBE cargar
#   para el viaje de retorno — aplica parámetros PDF_REMOTE (mayor dwell + charging_pct)
#   B7 UNAP Zungarococha: 18 km del centro | B8 Escuela PNP: campus cerrado ~6 km
#
# B6 datos directos del usuario: 930 motos + 150 mototaxis + ≥20 camionetas hora punta

BUILDING_DATA = {
    1:  {'motos':  20,  'mototaxis':   5, 'camionetas':  5, 'facility_h':  8, 'bldg_type': 'institucional',  'remote': False},
    2:  {'motos':  80,  'mototaxis':  30, 'camionetas':  2, 'facility_h': 10, 'bldg_type': 'deportivo',      'remote': False},
    3:  {'motos':  40,  'mototaxis': 180, 'camionetas':  8, 'facility_h': 16, 'bldg_type': 'transporte_24h', 'remote': False},
    4:  {'motos': 150,  'mototaxis':  60, 'camionetas':  3, 'facility_h': 14, 'bldg_type': 'retail',         'remote': False},
    5:  {'motos':   8,  'mototaxis':  15, 'camionetas':  4, 'facility_h': 24, 'bldg_type': 'hotelero',       'remote': False},
    6:  {'motos': 930,  'mototaxis': 150, 'camionetas': 20, 'facility_h': 11, 'bldg_type': 'mall',           'remote': False},  # DATO USUARIO
    # B7 UNAP Zungarococha: 18 km centro, ~2 000 estudiantes + 300 docentes/staff
    # Commuter: motos estacionan TODO EL DÍA → dwell_remote = 3.0 h (captive audience)
    # 30% estudiantes usan moto propia + mototaxis rutas exclusivas → alta afluencia
    7:  {'motos': 500,  'mototaxis': 200, 'camionetas': 10, 'facility_h': 10, 'bldg_type': 'universitario',  'remote': True},
    # B8 Escuela PNP: campus cerrado 97 000 m², 750 cadetes + 200 staff
    # Semi-remoto: personal y proveedores llegan en moto/mototaxi desde ciudad
    8:  {'motos': 150,  'mototaxis':  60, 'camionetas': 15, 'facility_h': 10, 'bldg_type': 'militar',        'remote': True},
    9:  {'motos': 120,  'mototaxis':  40, 'camionetas':  2, 'facility_h':  6, 'bldg_type': 'deportivo',      'remote': False},
    10: {'motos':  25,  'mototaxis':   8, 'camionetas': 15, 'facility_h':  8, 'bldg_type': 'administrativo', 'remote': False},
    11: {'motos':  80,  'mototaxis':  40, 'camionetas': 10, 'facility_h': 24, 'bldg_type': 'salud',          'remote': False},
    12: {'motos':  60,  'mototaxis':  30, 'camionetas':  8, 'facility_h': 24, 'bldg_type': 'salud',          'remote': False},
    # B13 UNAP FACEN: campus principal Iquitos, 1 500 estudiantes 5 escuelas — alta densidad motos
    13: {'motos': 200,  'mototaxis':  80, 'camionetas':  3, 'facility_h': 10, 'bldg_type': 'universitario',  'remote': False},
    14: {'motos':  20,  'mototaxis':  15, 'camionetas': 10, 'facility_h': 16, 'bldg_type': 'portuario',      'remote': False},
    # B15-B17 Colegio Nacional/SIMA/Selva Amazonica con alta densidad en moto (75k flota ciudad)
    15: {'motos': 100,  'mototaxis':  50, 'camionetas':  2, 'facility_h':  8, 'bldg_type': 'educacion',      'remote': False},
    16: {'motos': 180,  'mototaxis':  70, 'camionetas':  2, 'facility_h':  8, 'bldg_type': 'educacion',      'remote': False},
    17: {'motos': 220,  'mototaxis':  90, 'camionetas':  3, 'facility_h': 10, 'bldg_type': 'educacion',      'remote': False},
}

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 3 — Parámetros PDF por tipo EV
# EPRI (2020): charging_pct = fracción simultánea que carga
# utilization = objetivo de utilización del cargador
# ══════════════════════════════════════════════════════════════════════════════

PDF_PARAMS = {
    # charging_pct: fracción simultánea que carga.
    # Iquitos: alta densidad EV (75k motos + 65k mototaxis), baterías pequeñas se agotan
    # en uso diario → mototaxi recorre 80-120 km/día ≈ 1.6 kWh (40% de 4 kWh), DEBE cargar.
    # Se duplican los pct respecto a proxy genérico EPRI (0.06/0.10) para reflejar esto.
    'moto_lineal': {'charging_pct': 0.12, 'utilization': 0.70},  # era 0.06
    'mototaxi':    {'charging_pct': 0.20, 'utilization': 0.70},  # era 0.10
    'camioneta':   {'charging_pct': 0.38, 'utilization': 0.75},  # sin cambio
}

# Huella bruta por plaza con maniobra/circulacion local.
# No es area de bateria; es area de estacionamiento reservada por cargador.
PARKING_STALL_AREA_M2 = {
    'moto_lineal': 2.5,
    'mototaxi': 7.5,
    'camioneta': 25.0,
}

# Porcentaje del estacionamiento que puede reservarse como EV-ready sin
# bloquear la operacion normal. Edificios remotos/criticos elevan este valor.
EV_READY_SHARE_BY_TYPE = {
    'institucional': 0.18,
    'deportivo': 0.18,
    'transporte_24h': 0.22,
    'retail': 0.20,
    'hotelero': 0.18,
    'mall': 0.22,
    'universitario': 0.26,
    'militar': 0.24,
    'administrativo': 0.18,
    'salud': 0.24,
    'portuario': 0.18,
    'educacion': 0.22,
}
REMOTE_EV_READY_BONUS = 0.08
MAX_EV_READY_SHARE = 0.35

# EVCC modela loadpoints AC con corriente minima/maxima y fases.
# Para el dataset se adopta IEC 61851 modo 3, toma AC controlada por piloto.
MODE3_VOLTAGE_V = 230
MODE3_MIN_CURRENT_A = 6
MODE3_MIN_POWER_KW = round(MODE3_VOLTAGE_V * MODE3_MIN_CURRENT_A / 1000.0, 3)
MODE3_SOCKET_COUNT = 2
MODE3_CONNECTOR_STANDARD = "IEC_62196_Type_2_socket"
MODE3_EQUIPMENT_LABEL = "Mode_3_AC_dual_socket"

LAST_SUMMARY_ROWS = []

# Parámetros para edificios REMOTOS (>5 km del centro, sin cargadores alternativos)
# Diferencias vs. urbano:
#   dwell_h mayor: commuter estaciona TODO EL DÍA (no solo 1.5h de paso)
#   charging_pct mayor: captive audience + necesidad real de cargar para retorno ≥15 km
REMOTE_PDF = {
    'moto_lineal': {
        'dwell_h':      3.0,    # 2× base (1.5h): estudiante llega 8am, sale 5pm
        'charging_pct': 0.12,   # 2× base (0.06): retorno ≥15 km obliga a cargar
        'utilization':  0.72,
    },
    'mototaxi': {
        'dwell_h':      2.5,    # 1.25× base (2.0h): rutas largas, más paradas por turno
        'charging_pct': 0.20,   # 2× base (0.10): conductor DEBE cargar para retorno
        'utilization':  0.72,
    },
    'camioneta': {
        'dwell_h':      6.0,    # sin cambio: camioneta institucional, patrón similar
        'charging_pct': 0.38,
        'utilization':  0.75,
    },
}

def calc_stalls(n_daily, ev_type, facility_h, remote=False):
    """
    Peak Demand Factor + Ley de Little:
      N_simultaneous = N_daily × min(dwell_h, facility_h) / facility_h
      N_charging     = N_simultaneous × charging_pct
      N_stalls       = ceil(N_charging / utilization)

    Para edificios remotos (remote=True): usa REMOTE_PDF con mayor dwell y charging_pct
    para reflejar la necesidad real de carga en commuters de larga distancia.
    """
    spec = EV_SPEC[ev_type]
    if remote and ev_type in ('moto_lineal', 'mototaxi'):
        params = REMOTE_PDF[ev_type]
        dwell  = REMOTE_PDF[ev_type]['dwell_h']
    else:
        params = PDF_PARAMS[ev_type]
        dwell  = spec['dwell_h']
    n_sim  = n_daily * min(dwell, facility_h) / facility_h
    n_chrg = n_sim * params['charging_pct']
    return max(1, math.ceil(n_chrg / params['utilization']))


def _ev_ready_share(bldg_type, remote=False):
    share = EV_READY_SHARE_BY_TYPE.get(bldg_type, 0.18)
    if remote:
        share += REMOTE_EV_READY_BONUS
    return min(share, MAX_EV_READY_SHARE)


def _parking_area_required(counts):
    return sum(counts.get(ev_type, 0) * area for ev_type, area in PARKING_STALL_AREA_M2.items())


def _cap_counts_to_parking_area(raw_counts, area_budget_m2, priority_order):
    """
    Reduce charger counts only if the EV-ready parking area is exceeded.

    The removal order protects the building-specific priority EV types. For
    example hospitals and logistics keep camioneta chargers before motos.

    Guarantee: any EV type with raw_count >= 1 is preserved at minimum 1 stall
    even after capping, because in Iquitos motos and mototaxis are present at
    every building in greater or lesser quantity.
    """
    counts = dict(raw_counts)
    if area_budget_m2 <= 0.0:
        return {key: 0 for key in counts}, True

    capped = False
    removable_order = [ev for ev in ('camioneta', 'mototaxi', 'moto_lineal') if ev not in priority_order]
    removable_order += [ev for ev in reversed(priority_order) if ev not in removable_order]

    while _parking_area_required(counts) > area_budget_m2 and sum(counts.values()) > 0:
        reduced = False
        for ev_type in removable_order:
            if counts.get(ev_type, 0) > 1:
                counts[ev_type] -= 1
                capped = True
                reduced = True
                break
        if not reduced:
            # All types are at 1 — stop reducing; minimum guarantee kicks in
            break
        if not reduced:
            break

    # Minimum guarantee: restore to 1 any type that had daily arrivals but was zeroed out
    for ev_type, raw_n in raw_counts.items():
        if raw_n >= 1 and counts.get(ev_type, 0) < 1:
            counts[ev_type] = 1
            capped = True  # still flag as capped (area limit was binding)

    return counts, capped


def _priority_order_for_building(bldg_type, vehicle_predominant):
    text = f"{bldg_type} {vehicle_predominant}".lower()
    if any(token in text for token in ('salud', 'hospital', 'ambulance', 'medical', 'critical', 'industrial', 'portuario', 'cargo', 'truck', 'pickup')):
        return ['camioneta', 'mototaxi', 'moto_lineal']
    if any(token in text for token in ('transporte', 'mall', 'retail', 'motokar', 'mototaxi', 'taxis')):
        return ['mototaxi', 'moto_lineal', 'camioneta']
    return ['moto_lineal', 'mototaxi', 'camioneta']


def _counts_to_ev_list(counts):
    ev_list = []
    for ev_type in ('moto_lineal', 'mototaxi', 'camioneta'):
        ev_list.extend([ev_type] * int(counts.get(ev_type, 0)))
    return ev_list


def _phase_assignments(ev_list):
    phase_totals = {'L1': 0.0, 'L2': 0.0, 'L3': 0.0}
    phases = []
    for ev_type in ev_list:
        phase = min(phase_totals, key=lambda key: (phase_totals[key], key))
        phases.append(phase)
        phase_totals[phase] += EV_SPEC[ev_type]['charger_kw']
    return phases, phase_totals

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 4 — Perfiles de llegada por (tipo EV, tipo edificio)
# Basados en ACN-Data (Caltech) para workplace/university +
# adaptación contextual Iquitos (mototaxi 24h, moto comercio)
# ══════════════════════════════════════════════════════════════════════════════

# Formato: (arr_mu, arr_sig, ses_h_mu, ses_h_sig, prob_wd, prob_we)
# arr_mu/sig = hora media y desv. estándar de llegada
# ses_h = duración de sesión de carga [h]
# prob_wd/we = probabilidad sesión en día laboral / fin de semana

ARRIVAL_PROFILE = {
    # ── Mall (B6 y similares) ────────────────────────────────────────────
    ('moto_lineal', 'mall'):        (13.5, 2.0, 1.2, 0.3, 0.60, 0.82),
    ('mototaxi',    'mall'):        (12.0, 2.5, 1.8, 0.4, 0.65, 0.78),
    ('camioneta',   'mall'):        (10.0, 1.5, 5.0, 1.0, 0.72, 0.85),
    # ── Deportivo (B2, B9) ───────────────────────────────────────────────
    ('moto_lineal', 'deportivo'):   (16.0, 2.0, 1.5, 0.4, 0.40, 0.78),
    ('mototaxi',    'deportivo'):   (17.0, 2.0, 2.0, 0.5, 0.35, 0.75),
    ('camioneta',   'deportivo'):   (15.0, 1.5, 3.0, 0.6, 0.38, 0.70),
    # ── Transporte 24h (B3 aeropuerto) ───────────────────────────────────
    ('moto_lineal', 'transporte_24h'): (10.0, 3.5, 1.2, 0.3, 0.72, 0.72),
    ('mototaxi',    'transporte_24h'): ( 9.0, 3.0, 2.0, 0.5, 0.88, 0.88),
    ('camioneta',   'transporte_24h'): ( 7.0, 1.5, 6.0, 1.0, 0.90, 0.88),
    # ── Retail hiperbodega (B4) ───────────────────────────────────────────
    ('moto_lineal', 'retail'):      (12.5, 2.0, 1.2, 0.3, 0.62, 0.80),
    ('mototaxi',    'retail'):      (13.0, 2.5, 1.8, 0.4, 0.58, 0.78),
    ('camioneta',   'retail'):      (10.0, 1.5, 3.0, 0.6, 0.62, 0.70),
    # ── Hotelero 24h (B5) ────────────────────────────────────────────────
    ('moto_lineal', 'hotelero'):    ( 8.0, 1.5, 8.0, 1.0, 0.65, 0.62),
    ('mototaxi',    'hotelero'):    (20.5, 1.2, 2.0, 0.4, 0.68, 0.75),
    ('camioneta',   'hotelero'):    (20.0, 1.5,10.0, 1.5, 0.65, 0.78),
    # ── Universitario (B7, B13) ACN-Data Caltech proxy ───────────────────
    ('moto_lineal', 'universitario'): (8.0, 1.0, 7.5, 0.8, 0.72, 0.08),
    ('mototaxi',    'universitario'): (8.5, 1.2, 6.5, 0.9, 0.68, 0.05),
    ('camioneta',   'universitario'): (8.0, 0.5, 7.8, 0.6, 0.82, 0.05),
    # ── Militar (B8) ─────────────────────────────────────────────────────
    ('moto_lineal', 'militar'):     ( 7.0, 0.5, 8.0, 0.5, 0.85, 0.28),
    ('mototaxi',    'militar'):     ( 7.2, 0.6, 7.5, 0.6, 0.80, 0.25),
    ('camioneta',   'militar'):     ( 7.0, 0.3, 8.5, 0.4, 0.88, 0.30),
    # ── Administrativo (B10) ─────────────────────────────────────────────
    ('moto_lineal', 'administrativo'): (8.0, 0.6, 7.0, 0.5, 0.82, 0.00),
    ('mototaxi',    'administrativo'): (8.5, 0.8, 6.5, 0.6, 0.78, 0.00),
    ('camioneta',   'administrativo'): (7.8, 0.4, 7.2, 0.4, 0.85, 0.00),
    # ── Salud 24h (B11, B12) Saarinen et al. 2022 proxy ─────────────────
    ('moto_lineal', 'salud'):       ( 7.5, 1.0, 8.0, 0.8, 0.88, 0.85),
    ('mototaxi',    'salud'):       ( 8.0, 1.2, 7.5, 0.8, 0.85, 0.82),
    ('camioneta',   'salud'):       ( 7.0, 0.5, 8.0, 0.5, 0.92, 0.90),  # 3 turnos 24h
    # ── Portuario 24h (B14) ──────────────────────────────────────────────
    ('moto_lineal', 'portuario'):   ( 6.5, 1.5, 1.5, 0.3, 0.78, 0.65),
    ('mototaxi',    'portuario'):   ( 7.0, 2.0, 2.0, 0.5, 0.80, 0.68),
    ('camioneta',   'portuario'):   ( 6.5, 1.5, 7.5, 0.8, 0.88, 0.72),  # 3 turnos
    # ── Educación (B15-B17) ──────────────────────────────────────────────
    ('moto_lineal', 'educacion'):   ( 7.0, 0.8, 7.0, 0.6, 0.75, 0.00),
    ('mototaxi',    'educacion'):   ( 7.5, 0.9, 6.5, 0.7, 0.72, 0.00),
    ('camioneta',   'educacion'):   ( 7.5, 0.5, 6.0, 0.5, 0.78, 0.00),
    # ── Institucional (B1) ────────────────────────────────────────────────
    ('moto_lineal', 'institucional'): (8.0, 0.6, 8.0, 0.5, 0.88, 0.00),
    ('mototaxi',    'institucional'): (8.5, 0.8, 7.0, 0.6, 0.82, 0.00),
    ('camioneta',   'institucional'): (7.5, 0.4, 8.5, 0.4, 0.88, 0.00),
}

def get_profile(ev_type, bldg_type):
    key = (ev_type, bldg_type)
    if key in ARRIVAL_PROFILE:
        arr_mu, arr_sig, ses_mu, ses_sig, p_wd, p_we = ARRIVAL_PROFILE[key]
    else:
        # fallback genérico
        spec = EV_SPEC[ev_type]
        arr_mu, arr_sig = 9.0, 1.5
        ses_mu, ses_sig = spec['session_h_mu'], spec['session_h_sig']
        p_wd, p_we = 0.75, 0.25
    return {
        'arr_mu': arr_mu, 'arr_sig': arr_sig,
        'ses_mu': ses_mu, 'ses_sig': ses_sig,
        'prob_wd': p_wd, 'prob_we': p_we,
    }

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 5 — Generación del CSV por cargador (lógica de sesiones EV)
# ══════════════════════════════════════════════════════════════════════════════

def _make_index():
    """Índice horario 2023-2025 tz=America/Lima (26 304 filas)."""
    parts = [
        pd.date_range('2023-01-01', periods=8760,  freq='h', tz='America/Lima'),
        pd.date_range('2024-01-01', periods=8784,  freq='h', tz='America/Lima'),
        pd.date_range('2025-01-01', periods=8760,  freq='h', tz='America/Lima'),
    ]
    return parts[0].append(parts[1]).append(parts[2])

FULL_INDEX = _make_index()

def _find_row(ts):
    """Posición (entero) del timestamp ts en FULL_INDEX."""
    try:
        return FULL_INDEX.get_loc(ts)
    except KeyError:
        return None

def _charging_window_for_building(bldg_id: int) -> tuple[tuple[int, ...], tuple[int, ...], str]:
    """Return BESS/EV synchronized active hours and pandas day-of-week values."""
    hours, day_types, label = BUILDING_OPERATION_WINDOWS.get(
        bldg_id,
        (tuple(range(24)), tuple(range(1, 8)), "fallback_24h"),
    )
    # BUILDING_OPERATION_WINDOWS uses CityLearn day_type 1..7; pandas uses 0..6.
    pandas_dows = tuple(int(day_type) - 1 for day_type in day_types)
    return tuple(int(hour) for hour in hours), pandas_dows, label

def _charger_ev_id(bldg_id: int, charger_idx: int, ev_type: str) -> str:
    """Stable CityLearn EV id assigned to one controllable socket."""
    return f"EV_B{bldg_id:02d}_C{charger_idx:03d}_{EV_SPEC[ev_type]['ev_label']}"

def _ev_definition(ev_type: str) -> dict:
    """Build CityLearn electric_vehicles_def entry from the audited EV spec."""
    spec = EV_SPEC[ev_type]
    initial_soc = float(spec["soc_arr_mu"]) / 100.0
    return {
        "include": True,
        "battery": {
            "type": "citylearn.energy_model.Battery",
            "autosize": False,
            "attributes": {
                "capacity": float(spec["bat_kwh"]),
                "nominal_power": float(spec["bat_kwh"]),
                "initial_soc": initial_soc,
                "depth_of_discharge": 0.85 if ev_type == "camioneta" else 0.80,
                "efficiency": 0.94 if ev_type == "camioneta" else 0.92,
                "capacity_loss_coefficient": 1e-5,
            },
        },
    }

def _session_start_count(states: pd.Series) -> int:
    """Count charging sessions from 2/3 -> 1 transitions."""
    active = states.astype(int).eq(1)
    return int((active & ~active.shift(fill_value=False)).sum())

def generate_charger_csv(bldg_id, charger_idx, ev_type, bldg_type, seed):
    """
    Genera el DataFrame de 6 columnas para un cargador EV.

    state=1: EV conectado y cargando (countdown departure)
    state=2: señal predictiva incoming (1h antes de la llegada)
    state=3: EV fuera/commuting, sin control del cargador

    SOC en porcentaje [0-100] — CityLearn ChargerSimulation divide por 100 internamente.
    """
    spec    = EV_SPEC[ev_type]
    profile = get_profile(ev_type, bldg_type)
    rng     = np.random.default_rng(seed)
    ev_name = _charger_ev_id(bldg_id, charger_idx, ev_type)
    active_hours, active_dows, window_label = _charging_window_for_building(bldg_id)
    if not active_hours:
        raise ValueError(f"B{bldg_id}: ventana EV/BESS sin horas activas")
    window_start = min(active_hours)
    window_end = max(active_hours)

    n_rows  = len(FULL_INDEX)
    state   = np.full(n_rows, 3, dtype=int)
    ev_id   = np.full(n_rows, "NONE", dtype=object)
    dep_cdwn= np.full(n_rows, -1.0)     # CityLearn sentinel: sin salida activa
    req_soc = np.full(n_rows, -0.1)     # CityLearn sentinel: sin SOC objetivo
    arr_eta = np.full(n_rows, -1.0)     # CityLearn sentinel: sin llegada estimada
    arr_soc = np.full(n_rows, -0.1)     # CityLearn sentinel: sin SOC estimado

    dates = pd.date_range('2023-01-01', '2025-12-31', freq='D', tz='America/Lima')

    for dt in dates:
        dow = dt.dayofweek   # 0=lun…6=dom
        if dow not in active_dows:
            continue
        prob = profile['prob_wd'] if dow < 5 else profile['prob_we']
        if rng.random() > prob:
            continue

        # Hora de llegada con ruido gaussiano, limitada al horario real del edificio.
        # La sesion completa queda dentro de la ventana para que PV/EV/BESS usen
        # el mismo cierre operativo por edificio.
        arr_upper = max(window_start, window_end)
        arr_h_f = float(np.clip(rng.normal(profile['arr_mu'], profile['arr_sig']), window_start, arr_upper))
        arr_h   = int(arr_h_f)

        # Duración de sesión
        ses_h = max(0.5, rng.normal(profile['ses_mu'], profile['ses_sig']))
        dep_h = arr_h + math.ceil(ses_h)
        dep_h = min(dep_h, window_end)

        if dep_h <= arr_h:
            if arr_h < window_end:
                dep_h = arr_h + 1
            else:
                arr_h = max(window_start, window_end - 1)
                dep_h = window_end

        # SOC al llegar y requerido
        soc_a = float(np.clip(rng.normal(spec['soc_arr_mu'],  spec['soc_arr_sig']),  5, 85))
        soc_r = float(np.clip(rng.normal(spec['soc_req_mu'],  spec['soc_req_sig']),  60, 100))

        # Marcar state=1 durante la sesión
        for h in range(arr_h, dep_h + 1):
            ts = dt + pd.Timedelta(hours=h)
            pos = _find_row(ts)
            if pos is None or pos >= n_rows:
                continue
            countdown = dep_h - h   # horas restantes para salir
            state[pos]   = 1
            ev_id[pos]   = ev_name
            dep_cdwn[pos]= float(countdown)
            req_soc[pos] = soc_r
            arr_soc[pos] = soc_a

        # Marcar state=2 (1h antes de la sesión). Si la llegada cae al inicio
        # del día, la fila previa real es la última hora del día anterior.
        pre_h = arr_h - 1
        ts_pre = dt + pd.Timedelta(hours=pre_h) if pre_h >= 0 else dt - pd.Timedelta(hours=1)
        pos_pre = _find_row(ts_pre)
        if pos_pre is not None and 0 <= pos_pre < n_rows and state[pos_pre] == 3:
            state[pos_pre]   = 2
            ev_id[pos_pre]   = ev_name
            arr_eta[pos_pre] = float(arr_h)
            arr_soc[pos_pre] = soc_a

    return pd.DataFrame({
        'electric_vehicle_charger_state':          state,
        'electric_vehicle_id':                     ev_id,
        'electric_vehicle_departure_time':          dep_cdwn,
        'electric_vehicle_required_soc_departure':  req_soc,
        'electric_vehicle_estimated_arrival_time':  arr_eta,
        'electric_vehicle_estimated_soc_arrival':   arr_soc,
    }, index=FULL_INDEX)

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 6 — Dimensionamiento y configuración de cargadores por edificio
# ══════════════════════════════════════════════════════════════════════════════

def build_charger_config(return_summary=False):
    """
    Calcula N_stalls por (edificio, tipo EV) y construye la lista de cargadores.
    Retorna: dict {bldg_id: [(ev_type, stall_idx), ...]}
    """
    global LAST_SUMMARY_ROWS

    config = {}
    summary_rows = []
    inventory = load_building_inventory()

    for bid, bdata in BUILDING_DATA.items():
        fh        = bdata['facility_h']
        btype     = bdata['bldg_type']
        remote    = bdata.get('remote', False)
        meta      = inventory.get(bid)
        parking_area = float(meta.area_estacionamiento_m2) if meta is not None else 0.0
        vehicle_predominant = meta.tipo_vehiculo_predominante if meta is not None else ''
        ev_ready_share = _ev_ready_share(btype, remote=remote)
        ev_area_budget = parking_area * ev_ready_share
        priority_order = _priority_order_for_building(btype, vehicle_predominant)

        raw_counts = {}
        for ev_key, n_daily_key in [('moto_lineal','motos'), ('mototaxi','mototaxis'), ('camioneta','camionetas')]:
            n_daily = bdata[n_daily_key]
            raw_counts[ev_key] = calc_stalls(n_daily, ev_key, fh, remote=remote)

        final_counts, parking_capped = _cap_counts_to_parking_area(raw_counts, ev_area_budget, priority_order)
        chargers = _counts_to_ev_list(final_counts)
        ev_area_required = _parking_area_required(final_counts)

        config[bid] = chargers

        n_moto  = sum(1 for e in chargers if e == 'moto_lineal')
        n_moto2 = sum(1 for e in chargers if e == 'mototaxi')
        n_cam   = sum(1 for e in chargers if e == 'camioneta')
        kw_list = [EV_SPEC[e]['charger_kw'] for e in chargers]
        physical_mode3_units = math.ceil(len(chargers) / MODE3_SOCKET_COUNT)
        summary_rows.append({
            'B': bid,
            'name': BUILDING_NAMES.get(bid, f'Building_{bid}'),
            'type': btype,
            'motos_daily': bdata['motos'], 'mototaxis_daily': bdata['mototaxis'],
            'camionetas_daily': bdata['camionetas'],
            'parking_area_m2': parking_area,
            'vehicle_predominant': vehicle_predominant,
            'ev_ready_share': ev_ready_share,
            'ev_area_budget_m2': ev_area_budget,
            'ev_area_required_m2': ev_area_required,
            'ev_area_utilization_pct': ev_area_required / ev_area_budget * 100.0 if ev_area_budget > 0 else 0.0,
            'parking_capped': parking_capped,
            'raw_moto_stalls': raw_counts['moto_lineal'],
            'raw_mototaxi_stalls': raw_counts['mototaxi'],
            'raw_cam_stalls': raw_counts['camioneta'],
            'n_moto_stalls': n_moto, 'n_mototaxi_stalls': n_moto2, 'n_cam_stalls': n_cam,
            'total_chargers': len(chargers),
            'mode3_physical_units': physical_mode3_units,
            'mode3_socket_count': physical_mode3_units * MODE3_SOCKET_COUNT,
            'mode3_spare_sockets': physical_mode3_units * MODE3_SOCKET_COUNT - len(chargers),
            'total_kw': sum(kw_list),
            'remote': bdata.get('remote', False),
        })

    log.info("\n%s", _format_summary_table(summary_rows))
    LAST_SUMMARY_ROWS = summary_rows
    if return_summary:
        return config, summary_rows
    return config

def _format_summary_table(rows):
    lines = []
    W = 100
    hdr = (f"{'B':>3} {'Edificio':<24} {'Tipo':<18} {'Motos':>6} {'Motot':>6} {'Cam':>4}"
           f" | {'ML':>4} {'MT':>4} {'CV':>4} {'Tomas':>5} {'Eq':>3} {'kW':>7} {'Est%':>5} {'R':>1}")
    lines.append("=" * W)
    lines.append("DIMENSIONAMIENTO CARGADORES (Peak Demand Factor + Little's Law)")
    lines.append(
        "  ML=Moto_Lineal "
        f"{EV_SPEC['moto_lineal']['charger_kw']:.1f}kW | "
        "MT=Mototaxi "
        f"{EV_SPEC['mototaxi']['charger_kw']:.1f}kW | "
        "CV=Camioneta "
        f"{EV_SPEC['camioneta']['charger_kw']:.1f}kW | "
        "Eq=Modo3 doble toma | Est%=uso area EV-ready"
    )
    lines.append("=" * W)
    lines.append(hdr)
    lines.append("-" * W)
    total_ch = 0
    for r in rows:
        total_ch += r['total_chargers']
        name  = r['name'][:24]
        flag  = '*' if r.get('remote') else ' '
        lines.append(
            f"{r['B']:>3} {name:<24} {r['type']:<18} {r['motos_daily']:>6} {r['mototaxis_daily']:>6} "
            f"{r['camionetas_daily']:>4} | {r['n_moto_stalls']:>4} {r['n_mototaxi_stalls']:>4} "
            f"{r['n_cam_stalls']:>4} {r['total_chargers']:>5} {r['mode3_physical_units']:>3} {r['total_kw']:>7.1f} "
            f"{r['ev_area_utilization_pct']:>4.0f}% {flag}"
        )
    lines.append("-" * W)
    total_units = sum(r['mode3_physical_units'] for r in rows)
    lines.append(f"  TOTAL: {total_ch} tomas controlables | {total_units} equipos fisicos modo 3 doble toma | * = remoto")
    lines.append("=" * W)
    return "\n".join(lines)


def write_ev_sizing_audit(summary_rows):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(summary_rows)
    if not df.empty:
        df = df[[
            'B', 'name', 'type', 'remote',
            'parking_area_m2', 'vehicle_predominant', 'ev_ready_share',
            'ev_area_budget_m2', 'ev_area_required_m2', 'ev_area_utilization_pct',
            'motos_daily', 'mototaxis_daily', 'camionetas_daily',
            'raw_moto_stalls', 'raw_mototaxi_stalls', 'raw_cam_stalls',
            'n_moto_stalls', 'n_mototaxi_stalls', 'n_cam_stalls',
            'total_chargers', 'mode3_physical_units', 'mode3_socket_count',
            'mode3_spare_sockets', 'total_kw', 'parking_capped',
        ]]
    df.to_csv(EV_AUDIT_CSV, index=False)
    payload = {
        'method': {
            'arrival_model': 'Peak Demand Factor + Little Law by EV type and building type',
            'ev_types': {
                key: {
                    'charger_kw': value['charger_kw'],
                    'battery_kwh': value['bat_kwh'],
                    'dwell_h': value['dwell_h'],
                }
                for key, value in EV_SPEC.items()
            },
            'parking_model': {
                'source': 'CityLearn/data/buildingcsv/building.csv',
                'stall_area_m2': PARKING_STALL_AREA_M2,
                'ev_ready_share_by_type': EV_READY_SHARE_BY_TYPE,
                'remote_ev_ready_bonus': REMOTE_EV_READY_BONUS,
                'max_ev_ready_share': MAX_EV_READY_SHARE,
            },
            'charger_hardware_model': {
                'external_review': 'external/evcc used as charger-control reference: loadpoint, min/max current, phases, OCPP/device templates. It is not a parking dimensioning engine.',
                'external_folder_review': {
                    'evcc': 'charger/loadpoint controller reference: AC current limits, phase handling, OCPP and device templates',
                    'MicroGrids': 'microgrid PV/BESS optimization reference, not EVSE parking or charger-count sizing',
                    'prosumpy': 'PV self-consumption and battery dispatch reference, not EVSE parking or charger-count sizing',
                    'HARL_MAAC_MARL_MATD3': 'MADRL/MARL algorithm backends, not DER or EVSE physical sizing engines',
                },
                'citylearn_mapping': 'one schema charger = one controllable socket/loadpoint; two sockets are grouped by physical_charger_id metadata',
                'mode': 'IEC_61851_Mode_3_AC',
                'connector_standard': MODE3_CONNECTOR_STANDARD,
                'sockets_per_physical_unit': MODE3_SOCKET_COUNT,
                'voltage_v': MODE3_VOLTAGE_V,
                'min_current_a': MODE3_MIN_CURRENT_A,
                'min_power_kw': MODE3_MIN_POWER_KW,
                'phase_assignment': 'greedy balance across L1/L2/L3 by outlet nominal power',
            },
        },
        'rows': summary_rows,
    }
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    EV_AUDIT_JSON.write_text(text, encoding='utf-8')
    EV_DATASET_LOG.write_text(text, encoding='utf-8')
    EV_AUDIT_MD.parent.mkdir(parents=True, exist_ok=True)
    EV_AUDIT_MD.write_text(_build_ev_audit_markdown(summary_rows), encoding='utf-8')
    log.info("  Auditoria EV escrita: %s", EV_AUDIT_CSV)
    log.info("  Log EV dataset escrito: %s", EV_DATASET_LOG)
    log.info("  Informe EV escrito: %s", EV_AUDIT_MD)


def _build_ev_audit_markdown(summary_rows):
    total_outlets = sum(int(row['total_chargers']) for row in summary_rows)
    total_units = sum(int(row['mode3_physical_units']) for row in summary_rows)
    total_spares = sum(int(row['mode3_spare_sockets']) for row in summary_rows)
    total_kw = sum(float(row['total_kw']) for row in summary_rows)
    capped_count = sum(1 for row in summary_rows if row['parking_capped'])

    lines = [
        "# Informe de auditoria EV - Iquitos CityLearn V3",
        "",
        "## Resultado ejecutivo",
        "",
        "El dataset queda dimensionado con cargadores AC IEC 61851 modo 3. En CityLearn cada `charger_X_Y` representa una toma o loadpoint controlable; el equipo fisico real agrupa dos tomas mediante `physical_charger_id` y `socket_count_per_physical_unit = 2`.",
        "",
        f"- Tomas controlables CityLearn: {total_outlets}",
        f"- Equipos fisicos modo 3 de dos tomas: {total_units}",
        f"- Tomas de reserva por equipos con una toma libre: {total_spares}",
        f"- Potencia EV nominal total: {total_kw:.1f} kW",
        f"- Edificios recortados por limite de estacionamiento: {capped_count}",
        "",
        "## Revision de `external/evcc` y carpeta `external`",
        "",
        "Se reviso `external/evcc` como referencia tecnica de control de carga, no como motor de dimensionamiento de parqueo. EVCC modela loadpoints AC, corriente minima/maxima, fases, OCPP y plantillas de equipos, pero no calcula el numero de cargadores por edificio. Por eso el dimensionamiento del dataset usa afluencia diaria, tipo de edificio, permanencia, porcentaje que carga, utilizacion objetivo y area de estacionamiento del inventario local.",
        "",
        "Tambien se reviso la estructura restante de `external/`: `MicroGrids` y `prosumpy` son referencias de optimizacion/dispatch PV+BESS; `HARL`, `MAAC`, `MARL`, `MARLlib`, `MATD3implementation` y `off-policy` son backends de aprendizaje. Ninguno contiene un modelo local de dimensionamiento de cargadores por motos, mototaxis, camionetas, parqueo y afluencia de Iquitos, por lo que no se usan directamente para calcular las tomas EV.",
        "",
        "Parametros adoptados desde la logica de control tipo EVCC/IEC:",
        "",
        f"- Modo de carga: IEC 61851 modo 3 AC",
        f"- Conector/toma: {MODE3_CONNECTOR_STANDARD}",
        f"- Tension nominal monofasica: {MODE3_VOLTAGE_V} V",
        f"- Corriente minima por toma: {MODE3_MIN_CURRENT_A} A",
        f"- Potencia minima de control por toma: {MODE3_MIN_POWER_KW:.2f} kW",
        "- Balance de fases: asignacion L1/L2/L3 por potencia nominal de cada toma",
        "- V2G: deshabilitado (`max_discharging_power = 0.0`)",
        "",
        "## Metodo de dimensionamiento",
        "",
        "El numero de tomas por edificio se calcula con Peak Demand Factor y Ley de Little:",
        "",
        "`N_tomas = ceil(N_diario * min(permanencia_h, operacion_h) / operacion_h * pct_carga / utilizacion)`",
        "",
        "Luego se valida que el area EV-ready no exceda el estacionamiento disponible del edificio. El area por plaza usada es 2.5 m2 para moto lineal, 7.5 m2 para mototaxi y 25.0 m2 para camioneta. Los edificios remotos reciben mayor fraccion EV-ready porque el usuario necesita carga para el retorno.",
        "",
        "## Tipos EV usados",
        "",
        "| Tipo EV | Potencia toma | Bateria | Uso local |",
        "|---|---:|---:|---|",
        f"| Moto lineal electrica | {EV_SPEC['moto_lineal']['charger_kw']:.1f} kW | {EV_SPEC['moto_lineal']['bat_kwh']:.1f} kWh | Estudiantes, trabajadores, visitantes urbanos |",
        f"| Mototaxi electrica | {EV_SPEC['mototaxi']['charger_kw']:.1f} kW | {EV_SPEC['mototaxi']['bat_kwh']:.1f} kWh | Transporte publico ligero dominante en Iquitos |",
        "| Camioneta electrica | 7.4 kW | 47.0 kWh | Operacion institucional, salud, puerto, logistica y servicios |",
        "",
        "## Dimensionamiento final por edificio",
        "",
        "| ID | Edificio | Tipo | Estac. m2 | Vehiculo dominante | ML | MT | CV | Tomas | Equipos modo 3 | Reserva | kW | Uso EV-ready | Recorte |",
        "|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]

    for row in summary_rows:
        capped = "si" if row['parking_capped'] else "no"
        lines.append(
            f"| B{int(row['B']):02d} | {row['name']} | {row['type']} | "
            f"{float(row['parking_area_m2']):.0f} | {row['vehicle_predominant']} | "
            f"{int(row['n_moto_stalls'])} | {int(row['n_mototaxi_stalls'])} | {int(row['n_cam_stalls'])} | "
            f"{int(row['total_chargers'])} | {int(row['mode3_physical_units'])} | {int(row['mode3_spare_sockets'])} | "
            f"{float(row['total_kw']):.1f} | {float(row['ev_area_utilization_pct']):.1f}% | {capped} |"
        )

    lines.extend([
        "",
        "## Archivos modificados para entrenamiento",
        "",
        "- `CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json`: cargadores modo 3, dos tomas por equipo fisico, balance de fases y metadatos de hardware.",
        "- `CityLearn/data/datasets/citylearn_iquitos_2023_2025/charger_*.csv`: perfiles horarios de conexion, salida, SOC requerido y llegada estimada.",
        "- `CityLearn/data/datasets/citylearn_iquitos_2023_2025/ev_charger_sizing_log.json`: log reproducible dentro del dataset.",
        "- `outputs/dataset_audit/ev_charger_sizing_audit.csv`: tabla auditable del calculo.",
        "- `outputs/dataset_audit/ev_charger_sizing_audit.json`: parametros y resultados completos del modelo.",
        "",
        "## Criterio de control MADRL",
        "",
        "Cada edificio conserva sus tomas como recursos controlables dentro del entorno CityLearn. A nivel global, el algoritmo MADRL aprende politicas coordinadas para reducir costo, picos, emisiones y uso ineficiente de energia. A nivel de edificio, el agente decide acciones sobre bateria, carga flexible y cargadores EV observando demanda, PV, estado de carga, precio, emisiones y disponibilidad local. Las tomas EV no se dimensionan como cargas fijas: quedan expuestas como loadpoints controlables para que el entrenamiento pueda desplazar carga dentro de las restricciones de llegada, salida y SOC requerido.",
        "",
        "## Validacion esperada",
        "",
        "Antes de entrenar debe verificarse que el schema cargue con `CityLearnEnv`, que existan todos los CSV de cargadores, que cada CSV tenga 26 304 filas y que cada cargador tenga `charger_type = 3`, fase L1/L2/L3 y metadatos modo 3.",
        "",
    ])
    return "\n".join(lines)

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 7 — Actualización del schema.json
# ══════════════════════════════════════════════════════════════════════════════

def update_schema(charger_config, schema_path):
    with open(schema_path) as f:
        schema = json.load(f)

    # CityLearn v3 requires every electric_vehicle_id in charger CSVs to exist
    # here. Use one EV object per controllable socket to avoid sharing one EV
    # battery across concurrent chargers.
    schema['electric_vehicles_def'] = {
        _charger_ev_id(bid, idx, ev_type): _ev_definition(ev_type)
        for bid, ev_list in charger_config.items()
        for idx, ev_type in enumerate(ev_list, start=1)
    }

    # Actualizar cargadores por edificio
    buildings = schema['buildings']
    for bid, ev_list in charger_config.items():
        bkey = f'Building_{bid}'
        if bkey not in buildings:
            continue

        new_chargers = {}
        phase_assignments, phase_totals = _phase_assignments(ev_list)
        for idx, ev_type in enumerate(ev_list, start=1):
            cname = f'charger_{bid}_{idx}'
            spec  = EV_SPEC[ev_type]
            kw    = spec['charger_kw']
            physical_idx = math.ceil(idx / MODE3_SOCKET_COUNT)
            outlet_idx = 1 if idx % MODE3_SOCKET_COUNT == 1 else 2
            physical_id = f'mode3_B{bid:02d}_{physical_idx:02d}'
            phase_connection = phase_assignments[idx - 1]
            new_chargers[cname] = {
                'type': 'citylearn.electric_vehicle_charger.Charger',
                'charger_simulation': f'{cname}.csv',
                'autosize': False,
                'hardware': {
                    'charging_mode': 'IEC_61851_Mode_3_AC',
                    'equipment_type': MODE3_EQUIPMENT_LABEL,
                    'connector_standard': MODE3_CONNECTOR_STANDARD,
                    'physical_charger_id': physical_id,
                    'socket_count_per_physical_unit': MODE3_SOCKET_COUNT,
                    'outlet_index': outlet_idx,
                    'ev_type': ev_type,
                    'electric_vehicle_id': _charger_ev_id(bid, idx, ev_type),
                    'phase_connection': phase_connection,
                    'voltage_v': MODE3_VOLTAGE_V,
                    'min_current_a': MODE3_MIN_CURRENT_A,
                    'nominal_current_a': round(kw * 1000.0 / MODE3_VOLTAGE_V, 2),
                },
                'attributes': {
                    'nominal_power':         kw,
                    'efficiency':            0.95,
                    'charger_type':          3,
                    'max_charging_power':    kw,
                    'min_charging_power':    min(kw, MODE3_MIN_POWER_KW),
                    'max_discharging_power': 0.0,
                    'min_discharging_power': 0.0,
                    'phase_connection':      phase_connection,
                }
            }
        buildings[bkey]['chargers'] = new_chargers
        buildings[bkey]['electrical_service'] = {
            'mode': 'three_phase',
            'default_split': 'balanced',
            'ev_charger_phase_nominal_power_kw': {k: round(v, 3) for k, v in phase_totals.items()},
            'observations': {
                'headroom': False,
                'headroom_export': False,
                'violation': False,
                'phase_encoding': False,
            },
        }

    with open(schema_path, 'w', encoding='utf-8') as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)

    log.info("  schema.json actualizado: %d EV defs Iquitos + %d cargadores",
             len(schema['electric_vehicles_def']), sum(len(v) for v in charger_config.values()))

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 8 — Pipeline principal
# ══════════════════════════════════════════════════════════════════════════════

def main():
    log.info("=" * 80)
    log.info("dimension_ev_chargers.py v3.0 — EV reales Iquitos: moto + mototaxi + camioneta")
    log.info(
        "  moto_lineal: %.1f kW | mototaxi: %.1f kW | camioneta: %.1f kW (BYD/Maxus LatAm)",
        EV_SPEC["moto_lineal"]["charger_kw"],
        EV_SPEC["mototaxi"]["charger_kw"],
        EV_SPEC["camioneta"]["charger_kw"],
    )
    log.info("=" * 80)

    BASE.mkdir(parents=True, exist_ok=True)
    schema_path = BASE / 'schema.json'

    # 1 — Calcular dimensionamiento
    charger_config, summary_rows = build_charger_config(return_summary=True)

    total_chargers = sum(len(v) for v in charger_config.values())
    total_physical_units = sum(r['mode3_physical_units'] for r in summary_rows)
    log.info(f"\n  Total tomas controlables a generar: {total_chargers}")
    log.info(f"  Equipos fisicos modo 3 doble toma: {total_physical_units}")
    write_ev_sizing_audit(summary_rows)

    # 2 — Generar CSV por cargador
    log.info("\nGENERANDO CSV CHARGERS:")
    log.info("-" * 80)
    total_state1 = total_state2 = total_sessions = 0

    for bid, ev_list in charger_config.items():
        btype = BUILDING_DATA[bid]['bldg_type']
        kw_list = [EV_SPEC[e]['charger_kw'] for e in ev_list]
        ev_labels = [EV_SPEC[e]['ev_label'] for e in ev_list]
        log.info(f"  B{bid} ({len(ev_list)} cargadores @ {kw_list} kW | {btype}):")

        for idx, ev_type in enumerate(ev_list, start=1):
            cname = f'charger_{bid}_{idx}'
            seed  = bid * 1000 + idx
            df = generate_charger_csv(bid, idx, ev_type, btype, seed)
            fpath = BASE / f'{cname}.csv'
            df.to_csv(fpath, index=False)

            s1   = (df['electric_vehicle_charger_state'] == 1).sum()
            s2   = (df['electric_vehicle_charger_state'] == 2).sum()
            sess = _session_start_count(df['electric_vehicle_charger_state'])
            soc_req = df.loc[df['electric_vehicle_charger_state']==1,
                             'electric_vehicle_required_soc_departure'].dropna()
            soc_mean = soc_req.mean() if len(soc_req) > 0 else 0

            first_state = df.iloc[0]['electric_vehicle_charger_state']
            status = "OK" if int(first_state) == 3 else f"ERROR inicio={first_state}"

            log.info(f"    {cname} [{EV_SPEC[ev_type]['ev_label']} {EV_SPEC[ev_type]['charger_kw']}kW]: "
                     f"state1={s1}h ({s1/TOTAL_H*100:.1f}%) | state2={s2}h ({s2/TOTAL_H*100:.1f}%) | "
                     f"sessions={sess} | soc_req={soc_mean:.1f}% | {status}")

            total_state1 += s1
            total_state2 += s2
            total_sessions += sess

    # 3 — Actualizar schema.json
    log.info("\n  Actualizando schema.json...")
    update_schema(charger_config, schema_path)

    # 4 — Resumen final
    log.info("\n" + "=" * 80)
    log.info(f"  Archivos/tomas generados: {total_chargers}")
    log.info(f"  Equipos fisicos modo 3 : {total_physical_units}")
    log.info(f"  Total horas state=1    : {total_state1:,} ({total_state1/TOTAL_H/total_chargers*100:.1f}% avg)")
    log.info(f"  Total horas state=2    : {total_state2:,} ({total_state2/TOTAL_H/total_chargers*100:.1f}% avg)")
    log.info(f"  Total sesiones EV      : {total_sessions:,}")
    log.info("=" * 80)

    # 5 — Print charger count table for thesis
    log.info("\nRESUMEN CARGADORES POR EDIFICIO:")
    for bid, ev_list in charger_config.items():
        n_ml  = sum(1 for e in ev_list if e == 'moto_lineal')
        n_mt  = sum(1 for e in ev_list if e == 'mototaxi')
        n_cv  = sum(1 for e in ev_list if e == 'camioneta')
        kw_total = sum(EV_SPEC[e]['charger_kw'] for e in ev_list)
        name  = BUILDING_NAMES.get(bid, f'Building_{bid}')
        rem   = ' [REMOTO]' if BUILDING_DATA[bid].get('remote') else ''
        units = math.ceil(len(ev_list) / MODE3_SOCKET_COUNT)
        spare = units * MODE3_SOCKET_COUNT - len(ev_list)
        log.info(
            f"  B{bid:2d} {name:<26}{rem}: "
            f"{n_ml}×{EV_SPEC['moto_lineal']['charger_kw']:.1f}kW + "
            f"{n_mt}×{EV_SPEC['mototaxi']['charger_kw']:.1f}kW + "
            f"{n_cv}×{EV_SPEC['camioneta']['charger_kw']:.1f}kW = "
            f"{len(ev_list)} tomas, {units} equipos modo 3 doble toma, "
            f"{spare} tomas reserva ({kw_total:.1f} kW)"
        )

if __name__ == '__main__':
    main()
