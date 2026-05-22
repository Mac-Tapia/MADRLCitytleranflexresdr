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

TIPOS DE EV VERIFICADOS (red/web 2026-05-17):
  moto_lineal: Honda PCX Electric / Kymco Ionex / Sunra / Yadea → 2.5 kW AC, 2.0 kWh
  mototaxi:   trimotos eléctricas amazónicas 60V 75Ah LiFePO4   → 3.0 kW AC, 4.5 kWh
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
  → Dimensionamiento: 11 × 2.5kW + 4 × 3.0kW + 6 × 7.4kW = 21 cargadores B6
"""

import math
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

BASE  = Path("CityLearn/data/datasets/citylearn_iquitos_2023_2025")
TOTAL_H = 26304    # 2023 (8760) + 2024 bisiesto (8784) + 2025 (8760)
YEARS   = [2023, 2024, 2025]

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 1 — Especificaciones EV reales Iquitos 2023-2025
# ══════════════════════════════════════════════════════════════════════════════

EV_SPEC = {
    'moto_lineal': {
        # Honda PCX Electric (Asia/LatAm), Kymco Ionex 3.0, Sunra RK-6, Yadea G5
        # Cargador onboard AC 2.5 kW (230V 11A) — estándar motos eléctricas LatAm 2023-25
        # Batería: 60V 30Ah≈1.8 kWh / 48V 40Ah≈2.0 kWh (promedio 2.0 kWh)
        'charger_kw':    2.5,
        'bat_kwh':       2.0,
        'ev_label':      'Moto_Lineal_Electrica',
        'dwell_h':       1.5,      # permanencia media en el lugar [h]
        'session_h_mu':  1.2,      # duración media sesión de carga [h]
        'session_h_sig': 0.3,
        'soc_arr_mu':    45,       # SOC al llegar [%]
        'soc_arr_sig':   15,
        'soc_req_mu':    80,       # SOC requerido al partir [%]
        'soc_req_sig':   8,
        'min_kw_frac':   0.10,     # mínimo 10% de potencia nominal
    },
    'mototaxi': {
        # Trimotos eléctricas amazónicas: 60V 75Ah LiFePO4 ≈ 4.5 kWh
        # Cargador onboard 3.0 kW (60V 50A) — estándar mototaxis eléctricas Iquitos
        # Fuente: conductores mototaxi Iquitos + datos empíricos Loreto 2023
        'charger_kw':    3.0,
        'bat_kwh':       4.5,
        'ev_label':      'Mototaxi_Electrica',
        'dwell_h':       2.0,
        'session_h_mu':  1.8,
        'session_h_sig': 0.5,
        'soc_arr_mu':    42,
        'soc_arr_sig':   14,
        'soc_req_mu':    82,
        'soc_req_sig':   8,
        'min_kw_frac':   0.10,
    },
    'camioneta': {
        # BYD T3 (BYD Perú 2023): 47 kWh, cargador AC 6.6 kW
        # Maxus eDeliver 3 (LatAm): 58 kWh, cargador AC 7.4 kW (Type 2 Mennekes)
        # Verificado: no existe estándar >10 kW para furgonetas comerciales Perú 2023-25
        # Se usa 7.4 kW (Level 2, 32A monofásico 230V) como máximo disponible LatAm
        'charger_kw':    7.4,
        'bat_kwh':       47.0,
        'ev_label':      'Camioneta_Electrica',
        'dwell_h':       6.0,
        'session_h_mu':  4.5,
        'session_h_sig': 1.0,
        'soc_arr_mu':    35,
        'soc_arr_sig':   12,
        'soc_req_mu':    88,
        'soc_req_sig':   5,
        'min_kw_frac':   0.13,     # mínimo 13% = ~1 kW (no cortar sesión)
    },
}

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 2 — Afluencia diaria EV por edificio (observaciones + estimaciones)
# ══════════════════════════════════════════════════════════════════════════════

BUILDING_NAMES = {
    1:  'Electro Oriente S.A.',
    2:  'Complejo Champios',
    3:  'Aeropuerto IQT',
    4:  'Hiperbodega Precio UNO',
    5:  'Hotel El Dorado Plaza',
    6:  'Mall Aventura Iquitos',
    7:  'UNAP Zungarococha',
    8:  'Escuela Tecnica PNP',
    9:  'Complejo CNI',
    10: 'Gobierno Regional',
    11: 'Hospital Regional',
    12: 'EsSalud Hospital III',
    13: 'Fac. Economia UNAP',
    14: 'Terminal ENAPU',
    15: 'Colegio CNI',
    16: 'I.E. San Juan',
    17: 'IEST Pedro del Aguila',
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
    # B15-B17 colegios/IEST con alta densidad docente+estudiantil en moto (75k flota ciudad)
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
    'moto_lineal': {'charging_pct': 0.06, 'utilization': 0.70},
    'mototaxi':    {'charging_pct': 0.10, 'utilization': 0.70},
    'camioneta':   {'charging_pct': 0.38, 'utilization': 0.75},
}

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

def generate_charger_csv(bldg_id, charger_idx, ev_type, bldg_type, seed):
    """
    Genera el DataFrame de 6 columnas para un cargador EV.

    state=0: cargador libre
    state=1: EV conectado y cargando (countdown departure)
    state=2: señal predictiva incoming (1h antes de la llegada)

    SOC en porcentaje [0-100] — CityLearn ChargerSimulation divide por 100 internamente.
    """
    spec    = EV_SPEC[ev_type]
    profile = get_profile(ev_type, bldg_type)
    rng     = np.random.default_rng(seed)

    n_rows  = len(FULL_INDEX)
    state   = np.zeros(n_rows, dtype=float)
    ev_id   = np.full(n_rows, np.nan)
    dep_cdwn= np.full(n_rows, np.nan)   # countdown horas restantes hasta salida
    req_soc = np.full(n_rows, np.nan)
    arr_eta = np.full(n_rows, np.nan)   # ETA próximo EV (solo state=2)
    arr_soc = np.full(n_rows, np.nan)

    ev_counter = 0
    dates = pd.date_range('2023-01-01', '2025-12-31', freq='D', tz='America/Lima')

    for dt in dates:
        dow = dt.dayofweek   # 0=lun…6=dom
        prob = profile['prob_wd'] if dow < 5 else profile['prob_we']
        if rng.random() > prob:
            continue

        # Hora de llegada con ruido gaussiano
        arr_h_f = float(np.clip(rng.normal(profile['arr_mu'], profile['arr_sig']), 0, 22.5))
        arr_h   = int(arr_h_f)

        # Duración de sesión
        ses_h = max(0.5, rng.normal(profile['ses_mu'], profile['ses_sig']))
        dep_h = arr_h + math.ceil(ses_h)
        dep_h = min(dep_h, 23)

        if dep_h <= arr_h:
            dep_h = arr_h + 1

        # SOC al llegar y requerido
        soc_a = float(np.clip(rng.normal(spec['soc_arr_mu'],  spec['soc_arr_sig']),  5, 85))
        soc_r = float(np.clip(rng.normal(spec['soc_req_mu'],  spec['soc_req_sig']),  60, 100))

        ev_counter += 1

        # Marcar state=1 durante la sesión
        for h in range(arr_h, dep_h + 1):
            ts = dt + pd.Timedelta(hours=h)
            pos = _find_row(ts)
            if pos is None or pos >= n_rows:
                continue
            countdown = dep_h - h   # horas restantes para salir
            state[pos]   = 1
            ev_id[pos]   = float(ev_counter)
            dep_cdwn[pos]= float(countdown)
            req_soc[pos] = soc_r
            arr_soc[pos] = soc_a

        # Marcar state=2 (1h antes de la sesión)
        pre_h = arr_h - 1
        if pre_h >= 0:
            ts_pre = dt + pd.Timedelta(hours=pre_h)
            pos_pre = _find_row(ts_pre)
            if pos_pre is not None and pos_pre < n_rows and state[pos_pre] == 0:
                state[pos_pre]   = 2
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

def build_charger_config():
    """
    Calcula N_stalls por (edificio, tipo EV) y construye la lista de cargadores.
    Retorna: dict {bldg_id: [(ev_type, stall_idx), ...]}
    """
    config = {}
    summary_rows = []

    for bid, bdata in BUILDING_DATA.items():
        fh        = bdata['facility_h']
        btype     = bdata['bldg_type']
        chargers  = []

        remote    = bdata.get('remote', False)
        for ev_key, n_daily_key in [('moto_lineal','motos'), ('mototaxi','mototaxis'), ('camioneta','camionetas')]:
            n_daily = bdata[n_daily_key]
            n       = calc_stalls(n_daily, ev_key, fh, remote=remote)
            for i in range(n):
                chargers.append(ev_key)

        config[bid] = chargers

        n_moto  = sum(1 for e in chargers if e == 'moto_lineal')
        n_moto2 = sum(1 for e in chargers if e == 'mototaxi')
        n_cam   = sum(1 for e in chargers if e == 'camioneta')
        kw_list = [EV_SPEC[e]['charger_kw'] for e in chargers]
        summary_rows.append({
            'B': bid,
            'name': BUILDING_NAMES.get(bid, f'Building_{bid}'),
            'type': btype,
            'motos_daily': bdata['motos'], 'mototaxis_daily': bdata['mototaxis'],
            'camionetas_daily': bdata['camionetas'],
            'n_moto_stalls': n_moto, 'n_mototaxi_stalls': n_moto2, 'n_cam_stalls': n_cam,
            'total_chargers': len(chargers),
            'total_kw': sum(kw_list),
            'remote': bdata.get('remote', False),
        })

    log.info("\n%s", _format_summary_table(summary_rows))
    return config

def _format_summary_table(rows):
    lines = []
    W = 100
    hdr = (f"{'B':>3} {'Edificio':<24} {'Tipo':<18} {'Motos':>6} {'Motot':>6} {'Cam':>4}"
           f" | {'ML':>4} {'MT':>4} {'CV':>4} {'Tot':>5} {'kW':>7} {'R':>1}")
    lines.append("=" * W)
    lines.append("DIMENSIONAMIENTO CARGADORES (Peak Demand Factor + Little's Law)")
    lines.append("  ML=Moto_Lineal 2.5kW | MT=Mototaxi 3.0kW | CV=Camioneta 7.4kW | R=Remoto")
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
            f"{r['n_cam_stalls']:>4} {r['total_chargers']:>5} {r['total_kw']:>7.1f} {flag}"
        )
    lines.append("-" * W)
    lines.append(f"  TOTAL: {total_ch} cargadores | * = edificio remoto (parámetros PDF_REMOTE)")
    lines.append("=" * W)
    return "\n".join(lines)

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 7 — Actualización del schema.json
# ══════════════════════════════════════════════════════════════════════════════

def update_schema(charger_config, schema_path):
    with open(schema_path) as f:
        schema = json.load(f)

    # EV type definitions (CityLearn electric_vehicles_def)
    schema['electric_vehicles_def'] = {
        'Moto_Lineal_Electrica': {
            'include': True,
            'battery': {
                'type': 'citylearn.energy_model.Battery',
                'autosize': False,
                'attributes': {
                    'capacity':                 2.0,    # kWh
                    'nominal_power':            2.0,    # kW (max carga continua bat)
                    'initial_soc':              0.45,
                    'depth_of_discharge':       0.80,
                    'efficiency':               0.92,
                    'capacity_loss_coefficient':1e-5,
                }
            }
        },
        'Mototaxi_Electrica': {
            'include': True,
            'battery': {
                'type': 'citylearn.energy_model.Battery',
                'autosize': False,
                'attributes': {
                    'capacity':                 4.5,
                    'nominal_power':            4.5,
                    'initial_soc':              0.42,
                    'depth_of_discharge':       0.80,
                    'efficiency':               0.92,
                    'capacity_loss_coefficient':1e-5,
                }
            }
        },
        'Camioneta_Electrica': {
            'include': True,
            'battery': {
                'type': 'citylearn.energy_model.Battery',
                'autosize': False,
                'attributes': {
                    'capacity':                 47.0,
                    'nominal_power':            47.0,
                    'initial_soc':              0.35,
                    'depth_of_discharge':       0.85,
                    'efficiency':               0.94,
                    'capacity_loss_coefficient':1e-5,
                }
            }
        },
    }

    # Actualizar cargadores por edificio
    buildings = schema['buildings']
    for bid, ev_list in charger_config.items():
        bkey = f'Building_{bid}'
        if bkey not in buildings:
            continue

        new_chargers = {}
        for idx, ev_type in enumerate(ev_list, start=1):
            cname = f'charger_{bid}_{idx}'
            spec  = EV_SPEC[ev_type]
            kw    = spec['charger_kw']
            new_chargers[cname] = {
                'type': 'citylearn.electric_vehicle_charger.Charger',
                'charger_simulation': f'{cname}.csv',
                'autosize': False,
                'attributes': {
                    'nominal_power':        kw,
                    'efficiency':           0.95,
                    'charger_type':         1,
                    'max_charging_power':   kw,
                    'min_charging_power':   round(kw * spec['min_kw_frac'], 2),
                    'max_discharging_power':0.0,
                    'min_discharging_power':0.0,
                }
            }
        buildings[bkey]['chargers'] = new_chargers

    with open(schema_path, 'w', encoding='utf-8') as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)

    log.info("  schema.json actualizado: 3 EV defs Iquitos + %d cargadores",
             sum(len(v) for v in charger_config.values()))

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 8 — Pipeline principal
# ══════════════════════════════════════════════════════════════════════════════

def main():
    log.info("=" * 80)
    log.info("dimension_ev_chargers.py v3.0 — EV reales Iquitos: moto + mototaxi + camioneta")
    log.info("  moto_lineal: 2.5 kW | mototaxi: 3.0 kW | camioneta: 7.4 kW (BYD/Maxus LatAm)")
    log.info("=" * 80)

    BASE.mkdir(parents=True, exist_ok=True)
    schema_path = BASE / 'schema.json'

    # 1 — Calcular dimensionamiento
    charger_config = build_charger_config()

    total_chargers = sum(len(v) for v in charger_config.values())
    log.info(f"\n  Total cargadores a generar: {total_chargers}")

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
            sess = int(df['electric_vehicle_id'].dropna().nunique())
            soc_req = df.loc[df['electric_vehicle_charger_state']==1,
                             'electric_vehicle_required_soc_departure'].dropna()
            soc_mean = soc_req.mean() if len(soc_req) > 0 else 0

            first_state = df.iloc[0]['electric_vehicle_charger_state']
            status = "OK" if first_state == 0 else f"ERROR inicio={first_state}"

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
    log.info(f"  Archivos generados     : {total_chargers}")
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
        log.info(f"  B{bid:2d} {name:<26}{rem}: {n_ml}×2.5kW + {n_mt}×3.0kW + {n_cv}×7.4kW = {len(ev_list)} cargadores ({kw_total:.1f} kW)")

if __name__ == '__main__':
    main()
