"""
Generador del dataset CityLearn v2 para Iquitos 2023-2025.

17 edificios institucionales/comerciales reales.
Sistema electrico aislado ELECTRO ORIENTE S.A. (diesel).
Tres ejes MADRL: OE.1 Flexibilidad, OE.2 CO2, OE.3 Costos.

Uso:
    python tools/dataset/generate_iquitos_dataset.py
    python tools/dataset/generate_iquitos_dataset.py --buildings 1 6 11 12
    python tools/dataset/generate_iquitos_dataset.py --skip-cache --no-validate

Dependencias:
    pip install pvlib requests pandas numpy scipy tqdm pyarrow
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import subprocess
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import requests

try:
    from buildingcsv_inputs import (
        DEFAULT_BUILDINGS_WITH_MONTHLY_DATA,
        build_hourly_pricing_from_monthly_measurements,
        load_building_inventory,
        load_monthly_measurements,
    )
except ImportError:  # pragma: no cover - fallback when script is copied alone
    DEFAULT_BUILDINGS_WITH_MONTHLY_DATA = tuple(range(2, 18))
    build_hourly_pricing_from_monthly_measurements = None
    load_building_inventory = None
    load_monthly_measurements = None

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 1 — Constantes y configuración
# ═══════════════════════════════════════════════════════════════════════════════

# Fuente: CityLearn/data/buildingcsv/building.csv (nombres, areas, tipos, splits)
# Fuente: CityLearn/data/buildingcsv/B_02.csv..B_17.csv (potencia media real kWh/mes / 730h)
# cooling_peak = Cant_Est_Unidades_Autonomas_Split * 3.5 kW + sistema_central estimado
# non_shiftable_base = potencia_media_real * fraccion_base (30-50% segun tipo)
MADRL_BUILDING_CONSTANTS = {
    # ID  nombre_real (building.csv)                        base_kW  peak_AC_kW  shift   tipo               area_m2
    1:  {'name': 'Electro Oriente S.A.',                    'non_shiftable_base': 17.7,   'cooling_peak': 175.0,   'shiftable': 14.8,  'bldg_type': 'industrial',       'area_techada_m2': 14000.00},  # B_01: B_01.csv generado 2026-06-06 (MT2, COP=2.80)
    2:  {'name': 'Municipalidad Distrital San Juan Bautista','non_shiftable_base': 2.15,   'cooling_peak': 140.0,   'shiftable': 35.6,  'bldg_type': 'administrativo',   'area_techada_m2': 8000.00},   # B_02: Office, 40splits*3.5=140kW; P_med=7.17kW
    3:  {'name': 'Aeropuerto Internacional de Iquitos',      'non_shiftable_base': 62.5,   'cooling_peak': 465.0,   'shiftable': 95.0,  'bldg_type': 'transporte_24h',   'area_techada_m2': 6000.00},   # B_03: Assembly, Chiller+30splits; P_med=124.94kW
    4:  {'name': 'Hipermercados Tottus Oriente',             'non_shiftable_base': 78.2,   'cooling_peak': 350.0,   'shiftable': 22.2,  'bldg_type': 'mall',             'area_techada_m2': 2500.00},   # B_04: Retail, Food Cold Chain+11splits; P_med=156.49kW
    5:  {'name': 'Hotel Plaza S.A.',                         'non_shiftable_base': 54.9,   'cooling_peak': 157.5,   'shiftable': 99.0,  'bldg_type': 'hotelero_24h',     'area_techada_m2': 1141.89},   # B_05: Hotel, 45splits*3.5=157.5kW; P_med=109.81kW
    6:  {'name': 'Mall Aventura Iquitos',                    'non_shiftable_base': 691.2,  'cooling_peak': 1800.0,  'shiftable': 176.0, 'bldg_type': 'mall',             'area_techada_m2': 20637.00},  # B_06: Mall, Multi-Chiller+135splits; P_med=1382.39kW
    7:  {'name': 'UNAP Facultad de Biologia',                'non_shiftable_base': 7.45,   'cooling_peak': 59.5,    'shiftable': 39.2,  'bldg_type': 'universitario',    'area_techada_m2': 8103.45},   # B_07: Education, 17splits*3.5=59.5kW; P_med=24.84kW
    8:  {'name': 'PNP Escuela Tecnica Superior Iquitos',     'non_shiftable_base': 3.62,   'cooling_peak': 105.0,   'shiftable': 99.3,  'bldg_type': 'educacion',        'area_techada_m2': 21000.00},  # B_08: Military, 30splits*3.5=105kW; P_med=12.06kW
    9:  {'name': 'Gobierno Regional Loreto COER',            'non_shiftable_base': 2.86,   'cooling_peak': 150.0,   'shiftable': 12.1,  'bldg_type': 'transporte_24h',   'area_techada_m2': 4479.67},   # B_09: Office_Critical 24h, DataCenter N+1+27splits; P_med=5.71kW
    10: {'name': 'Gobierno Regional de Loreto',              'non_shiftable_base': 70.8,   'cooling_peak': 287.0,   'shiftable': 22.2,  'bldg_type': 'administrativo',   'area_techada_m2': 14295.73},  # B_10: Office, DuctCentralSplit+82splits; P_med=141.57kW
    11: {'name': 'Hospital Regional de Loreto',              'non_shiftable_base': 53.4,   'cooling_peak': 1000.0,  'shiftable': 73.0,  'bldg_type': 'salud_24h',        'area_techada_m2': 42649.33},  # B_11: Hospital, ClinicalChiller+HEPA+120splits; P_med=106.73kW
    12: {'name': 'Seguro Social de Salud EsSalud',           'non_shiftable_base': 133.3,  'cooling_peak': 427.5,   'shiftable': 34.5,  'bldg_type': 'salud_24h',        'area_techada_m2': 18197.48},  # B_12: Healthcare, MedicalArchiveAC+65splits; P_med=266.61kW
    13: {'name': 'UNAP Facultad de Ciencias Economicas',     'non_shiftable_base': 2.45,   'cooling_peak': 45.5,    'shiftable': 14.8,  'bldg_type': 'universitario',    'area_techada_m2': 2723.00},   # B_13: Education, 13splits*3.5=45.5kW; P_med=8.18kW
    14: {'name': 'Autoridad Portuaria Nacional Iquitos',     'non_shiftable_base': 2.59,   'cooling_peak': 77.0,    'shiftable': 47.0,  'bldg_type': 'portuario_24h',    'area_techada_m2': 17761.00},  # B_14: Port, 22splits*3.5=77kW; P_med=5.19kW
    15: {'name': 'DREL Colegio Nacional de Iquitos',         'non_shiftable_base': 5.94,   'cooling_peak': 35.0,    'shiftable': 23.4,  'bldg_type': 'educacion',        'area_techada_m2': 9889.92},   # B_15: Education, 10splits*3.5=35kW; P_med=19.81kW
    16: {'name': 'SIMA Iquitos S.R.Ltda',                   'non_shiftable_base': 35.8,   'cooling_peak': 237.5,   'shiftable': 51.24, 'bldg_type': 'industrial',       'area_techada_m2': 10294.00},  # B_16: Industrial shipyard, MobileVesselAC+25splits; P_med=71.56kW
    17: {'name': 'Asociacion Civil Selva Amazonica',         'non_shiftable_base': 22.3,   'cooling_peak': 206.0,   'shiftable': 26.3,  'bldg_type': 'salud_24h',        'area_techada_m2': 1611.23},   # B_17: Laboratory 24h, UltraFreezers-80C+16splits; P_med=44.53kW
}


def apply_buildingcsv_inventory(constants: dict[int, dict]) -> dict[int, dict]:
    """Synchronize building names and roof areas from CityLearn/data/buildingcsv."""
    if load_building_inventory is None:
        return constants

    try:
        inventory = load_building_inventory()
    except FileNotFoundError:
        return constants

    for bldg_id, meta in inventory.items():
        if bldg_id not in constants:
            continue
        constants[bldg_id]["name"] = meta.name
        constants[bldg_id]["area_techada_m2"] = meta.area_techada_m2
        constants[bldg_id]["source_tipo_uso_citylearn"] = meta.tipo_uso_citylearn
        constants[bldg_id]["oficinas_locales"] = meta.oficinas_locales
        constants[bldg_id]["sistemas_refrigeracion_grandes"] = meta.sistemas_refrigeracion_grandes
        constants[bldg_id]["split_units"] = meta.split_units
        constants[bldg_id]["area_estacionamiento_m2"] = meta.area_estacionamiento_m2
        constants[bldg_id]["tipo_vehiculo_predominante"] = meta.tipo_vehiculo_predominante
    return constants


MADRL_BUILDING_CONSTANTS = apply_buildingcsv_inventory(MADRL_BUILDING_CONSTANTS)

# Refrigeracion comercial continua (kW_24h, factor_nocturno)
# Fuente: Sistemas_Refrigeracion_Grandes en building.csv
REFRIGERACION_COMERCIAL = {
    3:  (80.0,  0.80),   # Chiller Central Water-Cooled (aeropuerto)
    4:  (100.0, 0.90),   # Food Cold Chain Racks + Rooftop (Tottus)
    5:  (35.0,  0.95),   # Commercial Kitchen Walk-in Cold Rooms (Hotel)
    6:  (800.0, 0.90),   # Multi-Chiller Plant (Mall Aventura)
    11: (200.0, 1.00),   # Clinical Chiller + Blood Bank Cold Room (Hospital)
    12: (100.0, 1.00),   # Medical Archive AC System (EsSalud)
    17: (150.0, 1.00),   # Scientific Ultra-Freezers -80C (Lab Selva Amazonica)
}

SHORE_POWER_B14 = {'kw_per_vessel': 15.0, 'max_vessels': 4}
EVENT_LOAD_B9   = {'event_kw': 70.0, 'event_hours': [19, 20, 21, 22]}

# COP real basado en Sistemas_Refrigeracion_Grandes de building.csv
# Splits autonomos: 2.8 | Chiller agua: 4.5 | Multi-Chiller: 5.0
# Precision DataCenter AC: 2.0 | Ultra-Freezers -80C: 0.8
COP_BY_TYPE = {
    'industrial':       2.5,   # B01 ELOR (DataCenter Precision), B16 SIMA (Mobile Vessel AC)
    'mall':             4.5,   # B04 Tottus (Rooftop), B06 Mall (Multi-Chiller 5.0 promedio)
    'salud_24h':        3.5,   # B11 ClinicalChiller(4.0) + B12 MedicalAC(3.0) + B17 UltraFreezers(0.8 promedio)
    'hotelero_24h':     2.8,   # B05 Commercial Kitchen Cold Rooms (splits)
    'universitario':    2.8,   # B07/B13 splits autonomos
    'educacion':        2.5,   # B08 PNP / B15 Colegio (splits autonomos)
    'portuario_24h':    2.5,   # B14 Autoridad Portuaria (splits autonomos)
    'transporte_24h':   4.0,   # B03 Aeropuerto (Chiller Water-Cooled), B09 COER (Precision N+1 promedio 3.0)
    'administrativo':   3.0,   # B02 Municipalidad (splits), B10 GRL (Duct Central Split)
}

DHW_KWH_THERMAL_DAY = {5: 614.0, 11: 1200.0, 12: 780.0}

# Margen numerico minimo para evitar fallos de CityLearn cuando el autosize
# queda exactamente en el pico horario y la comparacion usa floats estrictos.
COOLING_AUTOSIZE_SAFETY_FACTOR = 1.000001

# Setpoints reales de AC por tipo de uso (ASHRAE 55 / normativa peruana)
SETPOINTS_C = {
    'industrial':       24.0,   # B01 ELOR sala de control; B16 SIMA talleres
    'mall':             23.0,   # B04 Tottus; B06 Mall Aventura
    'salud_24h':        22.0,   # B11 Hospital; B12 EsSalud; B17 Lab (criogenica)
    'hotelero_24h':     23.0,   # B05 Hotel Plaza
    'universitario':    25.0,   # B07 UNAP Biologia; B13 UNAP Economia
    'educacion':        25.0,   # B08 PNP Escuela; B15 Colegio
    'portuario_24h':    26.0,   # B14 Autoridad Portuaria
    'transporte_24h':   24.0,   # B03 Aeropuerto; B09 COER
    'administrativo':   24.0,   # B02 Municipalidad; B10 Gobierno Regional
}

# Constante termica tau (horas) — masa termica del edificio
TAU_HOURS = {
    'industrial':       4.0,   # B01 galpones acero; B16 SIMA naves industriales
    'mall':             3.0,   # B04/B06 concreto con vidrio
    'salud_24h':        5.0,   # B11/B12 hospitales mamposteria densa; B17 lab aislado
    'hotelero_24h':     4.0,   # B05 hotel concreto
    'universitario':    3.0,   # B07/B13 aulas concreto
    'educacion':        2.5,   # B08/B15 estructura mixta
    'portuario_24h':    2.0,   # B14 instalacion portuaria metalica
    'transporte_24h':   2.0,   # B03 aeropuerto vidrio/acero; B09 COER modular
    'administrativo':   3.5,   # B02/B10 oficinas concreto
}

# Perfil horario de uso AC por tipo (hora 0-23, factor 0.0-1.0)
# Ajustado a horarios reales de cada edificio segun building.csv
LOAD_PROFILES = {
    # B01 ELOR (industrial utility 24h), B16 SIMA (turnos 6-18h)
    'industrial':       [0.65,0.62,0.60,0.60,0.62,0.70,0.85,0.92,0.95,0.95,0.95,0.92,0.88,0.90,0.95,0.90,0.85,0.75,0.60,0.45,0.40,0.38,0.35,0.30],
    # B04 Tottus (retail 9-22h), B06 Mall Aventura (10-22h)
    'mall':             [0.08,0.06,0.06,0.06,0.06,0.08,0.10,0.15,0.25,0.45,0.72,0.88,0.92,0.90,0.88,0.90,0.92,0.95,0.98,0.92,0.78,0.52,0.22,0.10],
    # B11 Hospital Regional (24h), B12 EsSalud (24h), B17 Lab Selva Amazonica (24h)
    'salud_24h':        [0.72,0.70,0.68,0.68,0.70,0.72,0.78,0.85,0.92,0.98,1.00,1.00,0.98,0.98,0.98,0.95,0.92,0.90,0.88,0.85,0.82,0.78,0.75,0.73],
    # B07 UNAP Biologia (7-19h), B13 UNAP Economia (7-19h)
    'universitario':    [0.10,0.08,0.08,0.08,0.08,0.10,0.22,0.58,0.88,0.92,0.92,0.90,0.82,0.90,0.92,0.88,0.78,0.62,0.38,0.20,0.14,0.11,0.10,0.10],
    # B08 PNP Escuela Tecnica (7-18h), B15 Colegio Nacional (7-15h)
    'educacion':        [0.05,0.05,0.05,0.05,0.05,0.08,0.18,0.60,0.90,0.95,0.92,0.92,0.82,0.90,0.92,0.82,0.50,0.18,0.08,0.07,0.06,0.06,0.05,0.05],
    # B14 Autoridad Portuaria Nacional (6-20h, operacion portuaria)
    'portuario_24h':    [0.48,0.45,0.42,0.42,0.45,0.68,0.90,0.98,0.95,0.88,0.82,0.80,0.78,0.80,0.88,0.90,0.85,0.78,0.70,0.62,0.55,0.52,0.50,0.48],
    # B03 Aeropuerto (24h vuelos), B09 COER (24h emergencias)
    'transporte_24h':   [0.58,0.52,0.50,0.50,0.52,0.68,0.88,0.98,0.95,0.90,0.88,0.85,0.82,0.82,0.82,0.85,0.88,0.90,0.92,0.88,0.80,0.72,0.68,0.62],
    # B02 Municipalidad San Juan Bautista (7-17h), B10 Gobierno Regional (7-17h)
    'administrativo':   [0.07,0.06,0.06,0.06,0.06,0.08,0.15,0.42,0.82,0.90,0.92,0.90,0.82,0.90,0.92,0.88,0.72,0.38,0.15,0.10,0.09,0.08,0.07,0.07],
    # B05 Hotel Plaza S.A. (24h, huespedes)
    'hotelero_24h':     [0.60,0.58,0.55,0.52,0.55,0.62,0.72,0.85,0.90,0.88,0.85,0.82,0.82,0.85,0.88,0.90,0.95,0.98,1.00,0.98,0.90,0.82,0.75,0.68],
}

# (factor_lunes_viernes, factor_sabado, factor_domingo)
DAY_FACTOR_MAP = {
    'industrial':       (1.00, 0.65, 0.40),   # B01 ELOR 24h; B16 SIMA turnos Sab
    'mall':             (1.00, 1.08, 1.05),   # B04 Tottus; B06 Mall (mas concurrido fin de semana)
    'salud_24h':        (1.00, 0.98, 0.95),   # B11/B12 hospitales; B17 lab continuo
    'universitario':    (1.00, 0.12, 0.04),   # B07/B13 UNAP (solo eventos sabado)
    'educacion':        (1.00, 0.05, 0.02),   # B08 PNP; B15 Colegio (cerrado fin semana)
    'portuario_24h':    (1.00, 0.75, 0.55),   # B14 APN (carga/descarga reducida fin semana)
    'transporte_24h':   (1.00, 1.12, 1.08),   # B03 Aeropuerto; B09 COER (emergencias siempre)
    'hotelero_24h':     (1.00, 1.18, 1.22),   # B05 Hotel Plaza (mayor ocupacion fin semana)
    'administrativo':   (1.00, 0.08, 0.03),   # B02 Municipalidad; B10 GRL (solo guardia)
}

# Horario de ocupacion activa (hora_inicio, hora_fin) — fuente: building.csv
OCCUPANCY_HOURS = {
    'industrial':       (6, 18),    # B01 ELOR turnos; B16 SIMA 6-18h dos turnos
    'mall':             (9, 22),    # B04 Tottus 9-22h; B06 Mall 10-22h
    'salud_24h':        (0, 24),    # B11/B12 hospitales; B17 lab 24h
    'universitario':    (7, 19),    # B07/B13 UNAP clases y laboratorios
    'educacion':        (7, 16),    # B08 PNP; B15 Colegio (turno manana)
    'portuario_24h':    (6, 20),    # B14 Autoridad Portuaria Nacional
    'transporte_24h':   (0, 24),    # B03 Aeropuerto vuelos; B09 COER 24h
    'hotelero_24h':     (0, 24),    # B05 Hotel Plaza huespedes 24h
    'administrativo':   (7, 17),    # B02 Municipalidad; B10 Gobierno Regional
}

# Controlled shiftable load exposed through CityLearn's WashingMachine API.
# The energy basis is the supplied per-building ``shiftable`` value in
# MADRL_BUILDING_CONSTANTS; the schedule window follows the building use type.
CONTROLLED_MACHINE_RULES = {
    'industrial':       {"days": "laboral", "profile": [0.45, 0.35, 0.20]},
    'mall':             {"days": "todos",   "profile": [0.25, 0.30, 0.25, 0.20]},
    'salud_24h':        {"days": "todos",   "profile": [0.40, 0.35, 0.25]},
    'hotelero_24h':     {"days": "todos",   "profile": [0.45, 0.35, 0.20]},
    'universitario':    {"days": "laboral", "profile": [0.60, 0.40]},
    'educacion':        {"days": "laboral", "profile": [0.55, 0.45]},
    'portuario_24h':    {"days": "todos",   "profile": [0.40, 0.35, 0.25]},
    'transporte_24h':   {"days": "todos",   "profile": [0.40, 0.35, 0.25]},
    'administrativo':   {"days": "laboral", "profile": [0.60, 0.40]},
}

# EV charger config base:
#   {bldg_id: [(tipo, arr_h, dep_h, soc_min, soc_max, soc_req, bat_kwh, kw)]}
#
# La fuente canonica de conteos EV es tools/dataset/dimension_ev_chargers.py. El
# generador base usa ese mismo dimensionamiento para no producir una etapa
# temporal con otro numero de tomas; la sincronizacion DER posterior reescribe
# los charger_*.csv y schema con pools EV por toma y metadatos Mode 3 completos.
def _build_canonical_ev_config() -> dict[int, list[tuple[str, int, int, float, float, float, float, float]]]:
    empty = {bid: [] for bid in MADRL_BUILDING_CONSTANTS}
    try:
        import dimension_ev_chargers as evdim
    except Exception as exc:  # pragma: no cover - only for isolated script copies
        logger.warning("No se pudo importar dimension_ev_chargers.py (%s); EV_CONFIG queda vacio.", exc)
        return empty

    try:
        charger_config = evdim.build_charger_config()
    except Exception as exc:  # pragma: no cover - protects isolated generation
        logger.warning("No se pudo calcular EV_CONFIG canonico (%s); EV_CONFIG queda vacio.", exc)
        return empty

    config: dict[int, list[tuple[str, int, int, float, float, float, float, float]]] = {}
    default_profile = (8.0, 1.5, 1.5, 0.4, 0.40, 0.20)

    for bldg_id in MADRL_BUILDING_CONSTANTS:
        bldg_type = evdim.BUILDING_DATA.get(bldg_id, {}).get("bldg_type", "institucional")
        entries = []
        for ev_type in charger_config.get(bldg_id, []):
            spec = evdim.EV_SPEC[ev_type]
            arr_mu, _arr_sig, session_mu, _session_sig, _prob_wd, _prob_we = evdim.ARRIVAL_PROFILE.get(
                (ev_type, bldg_type),
                default_profile,
            )
            arr_h = int(np.clip(round(arr_mu), 1, 22))
            dep_h = int(np.clip(math.ceil(arr_h + max(1.0, session_mu)), arr_h + 1, 23))
            soc_min = max(0.05, (spec["soc_arr_mu"] - spec["soc_arr_sig"]) / 100.0)
            soc_max = min(0.95, (spec["soc_arr_mu"] + spec["soc_arr_sig"]) / 100.0)
            soc_req = min(0.98, spec["soc_req_mu"] / 100.0)
            entries.append((
                ev_type,
                arr_h,
                dep_h,
                round(soc_min, 3),
                round(soc_max, 3),
                round(soc_req, 3),
                float(spec["bat_kwh"]),
                float(spec["charger_kw"]),
            ))
        config[bldg_id] = entries

    return config


EV_CONFIG = _build_canonical_ev_config()

# Dias activos por tipo de cargador: 'laboral' (lun-vie) o 'todos'.
EV_DAYS_ACTIVE = {
    'v2g':       'laboral',
    'mototaxi':  'todos',
    'motolineal':'laboral',
    'moto_lineal':'laboral',
    'camioneta': 'laboral',
    # Legacy aliases
    'utility':   'laboral', 'deportivo': 'todos', 'aeropuerto': 'todos',
    'mall':      'todos',   'hotelero':  'todos', 'univ':       'laboral',
    'militar':   'laboral', 'admin':     'laboral',
    'salud':     'todos',   'ambulancia':'todos',  'portuario':  'todos',
    'tec':       'laboral',
}

FE_DIESEL_KG_KWH   = 0.79
SOLAR_PENETRACION   = 0.15
TARIFA_PUNTA_USD    = 0.38
TARIFA_FUERA_USD    = 0.26
BESS_DOD            = 0.80
BESS_ETA_C          = 0.95
BESS_ETA_D          = 0.95
BESS_ETA_RT         = BESS_ETA_C * BESS_ETA_D
BESS_LOSS           = 1e-5
BESS_SOC_INI        = 0.50
BESS_TARGET_SS      = 0.70

AREA_UTIL_FACTOR    = 0.63   # 0.70 × 0.90
TILT_DEG            = 5.0
AZIMUTH_DEG         = 0.0    # norte (hemisferio sur)

LOCATION_LAT        = -3.7491
LOCATION_LON        = -73.2538
LOCATION_TZ         = 'America/Lima'
LOCATION_ALT        = 106

YEARS               = [2023, 2024, 2025]
N_HOURS_TOTAL       = 26_304

DHW_PROFILE_HOTEL = [
    0.02,0.01,0.01,0.01,0.02,0.06,0.10,0.12,0.08,0.05,0.04,0.04,
    0.05,0.04,0.04,0.04,0.05,0.08,0.10,0.08,0.06,0.04,0.03,0.02,
]
DHW_PROFILE_HOSPITAL = [1/24]*24

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR_DEFAULT = Path("CityLearn/data/datasets/citylearn_iquitos_2023_2025")
CACHE_DIR          = Path(".cache/weather")


# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 2 — WeatherDataManager
# ═══════════════════════════════════════════════════════════════════════════════

class WeatherDataManager:
    """Descarga, cachea y expone datos meteorológicos horarios PVGIS + NASA POWER."""

    def __init__(self, cache_dir: Path = CACHE_DIR, skip_cache: bool = False):
        self.cache_dir  = cache_dir
        self.skip_cache = skip_cache
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, year: int) -> pd.DataFrame:
        if not self.skip_cache:
            cached = self._from_cache(year)
            if cached is not None:
                logger.info(f"  Meteoro {year}: desde cache")
                return cached

        if year <= 2023:
            try:
                df = self._from_pvgis(year)
                logger.info(f"  Meteoro {year}: PVGIS-ERA5 OK")
            except Exception as e:
                logger.warning(f"  PVGIS {year} fallo ({e}), usando NASA POWER")
                df = self._from_nasa_power(year)
        else:
            df = self._from_nasa_power(year)
            logger.info(f"  Meteoro {year}: NASA POWER OK")

        self._save_cache(df, year)
        return df

    def _from_cache(self, year: int) -> pd.DataFrame | None:
        p = self.cache_dir / f"{year}.parquet"
        if p.exists():
            try:
                return pd.read_parquet(p)
            except Exception:
                return None
        return None

    def _from_pvgis(self, year: int) -> pd.DataFrame:
        import pvlib
        data, _, _ = pvlib.iotools.get_pvgis_hourly(
            latitude=LOCATION_LAT, longitude=LOCATION_LON,
            start=year, end=year,
            raddatabase='PVGIS-ERA5',
            components=True,
            outputformat='csv',
            pvcalculation=False,
            usehorizon=False,
        )
        df = data.rename(columns={
            'G(h)': 'GHI', 'Gd(h)': 'DHI', 'Gb(n)': 'DNI',
            'T2m': 'T2M', 'WS10m': 'WS',
        })
        if df.index.tz is None:
            df.index = df.index.tz_localize('UTC').tz_convert(LOCATION_TZ)
        else:
            df.index = df.index.tz_convert(LOCATION_TZ)
        df = df.reindex(self._make_index(year))
        if 'RH2M' not in df.columns:
            df['RH2M'] = 82.0
        for col in ['GHI', 'DHI', 'DNI', 'T2M', 'WS', 'RH2M']:
            if col not in df.columns:
                df[col] = 0.0
        df = df[['GHI', 'DHI', 'DNI', 'T2M', 'RH2M', 'WS']].ffill().bfill()
        df['GHI'] = df['GHI'].clip(lower=0)
        df['DHI'] = df['DHI'].clip(lower=0)
        df['DNI'] = df['DNI'].clip(lower=0)
        return df

    def _from_nasa_power(self, year: int) -> pd.DataFrame:
        url = (
            "https://power.larc.nasa.gov/api/temporal/hourly/point"
            f"?parameters=T2M,RH2M,ALLSKY_SFC_SW_DWN,ALLSKY_SFC_SW_DIFF,ALLSKY_SFC_SW_DNI,WS10M"
            f"&community=RE&longitude={LOCATION_LON}&latitude={LOCATION_LAT}"
            f"&start={year}0101&end={year}1231&format=JSON"
        )
        resp = requests.get(url, timeout=180)
        resp.raise_for_status()
        raw = resp.json()['properties']['parameter']

        idx = self._make_index(year)
        n   = len(idx)

        def extract(key):
            vals = list(raw[key].values())
            if len(vals) < n:
                vals += [vals[-1]] * (n - len(vals))
            return np.array(vals[:n], dtype=float)

        df = pd.DataFrame({
            'GHI':  extract('ALLSKY_SFC_SW_DWN'),
            'DHI':  extract('ALLSKY_SFC_SW_DIFF'),
            'DNI':  extract('ALLSKY_SFC_SW_DNI'),
            'T2M':  extract('T2M'),
            'RH2M': extract('RH2M'),
            'WS':   extract('WS10M'),
        }, index=idx)

        df['GHI'] = df['GHI'].clip(lower=0)
        df['DHI'] = df['DHI'].clip(lower=0)
        df['DNI'] = df['DNI'].clip(lower=0)
        df['T2M'] = df['T2M'].clip(lower=18, upper=42)
        df['RH2M'] = df['RH2M'].clip(lower=40, upper=100)
        return df

    def _make_index(self, year: int) -> pd.DatetimeIndex:
        n = 8784 if year == 2024 else 8760
        return pd.date_range(f'{year}-01-01', periods=n, freq='h', tz=LOCATION_TZ)

    def _save_cache(self, df: pd.DataFrame, year: int):
        try:
            df.to_parquet(self.cache_dir / f"{year}.parquet")
        except Exception as e:
            logger.warning(f"No se pudo guardar cache {year}: {e}")

    def get_full_df(self) -> pd.DataFrame:
        frames = [self.get(y) for y in YEARS]
        return pd.concat(frames)

    def get_full_index(self) -> pd.DatetimeIndex:
        return self.get_full_df().index


# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 3 — SandiaModelSelector
# ═══════════════════════════════════════════════════════════════════════════════

class SandiaModelSelector:
    """Selecciona módulo e inversor óptimos de la base Sandia."""

    def __init__(self):
        self._module_key    = None
        self._module_params = None

    def select_module(self) -> tuple[str, dict]:
        if self._module_key is not None:
            return self._module_key, self._module_params

        import pvlib
        mods = pvlib.pvsystem.retrieve_sam('SandiaMod')
        mods = mods.T if mods.shape[0] < mods.shape[1] else mods
        for col in ['Vmpo', 'Impo', 'Area', 'Bvoco']:
            mods[col] = pd.to_numeric(mods[col], errors='coerce')

        mods['Pmp_stc']   = mods['Vmpo'] * mods['Impo']
        mods['eta_stc']   = mods['Pmp_stc'] / (mods['Area'] * 1000)
        # Nombre correcto en pvlib SandiaMod: 'Bvoco' (no 'BVoco')
        mods['abs_Bvoco'] = mods['Bvoco'].abs()

        # Excluir modulos CPV: requieren seguidor solar y DNI directa alta;
        # no apropiados para tejados planos en Iquitos (alta irradiancia difusa).
        no_cpv = ~mods.index.str.contains('CPV', case=False, na=False)
        # Filtrar modulos de silicio cristalino planos estandar
        cands = mods[
            no_cpv &
            (mods['eta_stc'] >= 0.15) &
            (mods['Area'].between(1.5, 2.6)) &
            (mods['Pmp_stc'] >= 250)
        ].copy()

        if cands.empty:
            cands = mods[no_cpv].copy()
        if cands.empty:
            cands = mods.copy()

        cands = cands.sort_values(by=['eta_stc', 'abs_Bvoco'], ascending=[False, True])
        self._module_key    = cands.index[0]
        self._module_params = mods.loc[self._module_key].to_dict()

        p = self._module_params
        logger.info(
            f"  Modulo Sandia: {self._module_key} | "
            f"Pmp={p['Vmpo']*p['Impo']:.0f}W | "
            f"Area={p['Area']:.3f}m2 | "
            f"eta={p['Vmpo']*p['Impo']/(p['Area']*1000):.1%} | "
            f"|Bvoco|={abs(p['Bvoco']):.5f}"
        )
        return self._module_key, self._module_params

    def select_inverter(self, pdc_kw: float) -> tuple[str, dict]:
        import pvlib
        invs = pvlib.pvsystem.retrieve_sam('SandiaInverter')
        invs = invs.T if invs.shape[0] < invs.shape[1] else invs
        for col in ['Pdco', 'Paco']:
            invs[col] = pd.to_numeric(invs[col], errors='coerce')

        pdc_w = pdc_kw * 1000
        # Nombre correcto en pvlib SandiaInverter: 'Pdco' (no 'Pdc0')
        cands = invs[
            (invs['Pdco'] >= pdc_w * 0.80) &
            (invs['Pdco'] <= pdc_w * 1.30)
        ].copy()

        if cands.empty:
            diffs = (invs['Pdco'] - pdc_w).abs()
            cands = invs.loc[diffs.nsmallest(3).index].copy()

        cands['eta_inv'] = cands['Paco'] / cands['Pdco']
        best_key = cands.sort_values('eta_inv', ascending=False).index[0]
        params   = invs.loc[best_key].to_dict()
        return best_key, params

    def n_modules_for_building(self, bldg_id: int) -> int:
        _, mp = self.select_module()
        area_util = MADRL_BUILDING_CONSTANTS[bldg_id]['area_techada_m2'] * AREA_UTIL_FACTOR
        return max(1, int(area_util // mp['Area']))

    def pdc_kw(self, n_mod: int) -> float:
        _, mp = self.select_module()
        return n_mod * mp['Vmpo'] * mp['Impo'] / 1000

    def modules_per_string(self) -> int:
        _, mp = self.select_module()
        voc = mp.get('Voco', 40.0)
        return min(20, max(1, int(1000 / voc)))


# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 4 — BuildingDataGenerator
# ═══════════════════════════════════════════════════════════════════════════════

class BuildingDataGenerator:
    """Genera las 12 columnas del Building_X.csv para un edificio."""

    def __init__(
        self,
        bldg_id:      int,
        weather_df:   pd.DataFrame,
        solar_series: pd.Series,
    ):
        self.bldg_id = bldg_id
        self.cfg     = MADRL_BUILDING_CONSTANTS[bldg_id]
        self.btype   = self.cfg['bldg_type']
        self.index   = weather_df.index
        self.weather  = weather_df
        self.solar    = solar_series
        self.rng      = np.random.default_rng(bldg_id)

        h   = self.index.hour.values
        dow = self.index.dayofweek.values   # 0=Lun...6=Dom
        wf, sf, uf = DAY_FACTOR_MAP[self.btype]

        self._prof     = np.array(LOAD_PROFILES[self.btype])
        self._hour_fac = self._prof[h]
        self._day_fac  = np.where(dow < 5, wf, np.where(dow == 5, sf, uf))
        self._cooling_frac = np.clip(self._hour_fac * self._day_fac, 0.0, 1.0)

        occ_start, occ_end = OCCUPANCY_HOURS[self.btype]
        if occ_end == 24:
            self._occ = np.ones(len(self.index), dtype=float)
        else:
            self._occ = np.where((h >= occ_start) & (h < occ_end), 1.0, 0.0)
            if dow is not None:
                weekend = dow >= 5
                if self.btype in ('educacion', 'administrativo', 'universitario'):
                    self._occ[weekend] = 0.0

    # ── Columnas de contexto temporal ─────────────────────────────────

    def month(self)             -> np.ndarray: return self.index.month.values
    def hour(self)              -> np.ndarray: return self.index.hour.values
    def day_type(self)          -> np.ndarray: return (self.index.dayofweek.values + 1)
    def daylight_savings(self)  -> np.ndarray: return np.zeros(len(self.index), dtype=int)

    # ── Columnas de estado térmico interior ───────────────────────────

    def indoor_dry_bulb_temperature(self) -> np.ndarray:
        T_out  = self.weather['T2M'].values
        T_set  = SETPOINTS_C[self.btype]
        tau    = TAU_HOURS[self.btype]
        cf     = self._cooling_frac

        T_in   = np.empty(len(T_out))
        T_in[0] = T_set
        for i in range(1, len(T_in)):
            if cf[i] > 0.05:
                tau_eff = tau / 4.0
                target  = T_set
            else:
                tau_eff = tau
                target  = T_out[i]
            alpha   = math.exp(-1.0 / tau_eff)
            T_in[i] = alpha * T_in[i-1] + (1.0 - alpha) * target

        noise = self.rng.normal(0, 0.3, len(T_in))
        return np.clip(T_in + noise, 15.0, 45.0)

    def indoor_relative_humidity(self) -> np.ndarray:
        RH_out = self.weather['RH2M'].values
        eta_d  = 0.35
        RH_in  = RH_out * (1.0 - eta_d * self._cooling_frac)
        return np.clip(RH_in, 30.0, 98.0)

    def average_unmet_cooling(self, T_indoor: np.ndarray) -> np.ndarray:
        T_set = SETPOINTS_C[self.btype]
        unmet = np.maximum(0.0, T_indoor - T_set) * self._occ
        return unmet

    # ── Columnas de carga energética ─────────────────────────────────

    def non_shiftable_load(self) -> np.ndarray:
        h      = self.index.hour.values
        base   = self.cfg['non_shiftable_base']

        # Estimación de equipos operativos (toda la carga no-AC menos base)
        cooling_peak = self.cfg['cooling_peak']
        total_peak_estimate = base + cooling_peak * 0.25 + 5.0
        equip_peak   = max(0.0, total_peak_estimate - base)
        refrig_kw, factor_noc = REFRIGERACION_COMERCIAL.get(self.bldg_id, (0.0, 1.0))

        equip  = equip_peak * self._hour_fac * self._day_fac
        refrig = np.where(h < 6, refrig_kw * factor_noc, refrig_kw)

        noise  = self.rng.normal(1.0, 0.02, len(self.index))
        load   = (base + equip + refrig) * noise
        return np.clip(load, 0.0, None)

    def dhw_demand(self) -> np.ndarray:
        daily = DHW_KWH_THERMAL_DAY.get(self.bldg_id, 0.0)
        if daily == 0.0:
            return np.zeros(len(self.index))
        profile = DHW_PROFILE_HOTEL if self.bldg_id == 5 else DHW_PROFILE_HOSPITAL
        h       = self.index.hour.values
        factor  = np.array([profile[hh] for hh in h])
        return np.clip(daily * factor, 0.0, None)

    def cooling_demand(self) -> np.ndarray:
        cop      = COP_BY_TYPE[self.btype]
        p_ac_kw  = self.cfg['cooling_peak']
        cd       = p_ac_kw * cop * self._cooling_frac
        noise    = self.rng.normal(1.0, 0.015, len(self.index))
        return np.clip(cd * noise, 0.0, None)

    def heating_demand(self) -> np.ndarray:
        return np.zeros(len(self.index))

    def solar_generation_col(self) -> np.ndarray:
        return np.clip(self.solar.values, 0.0, None)

    # ── Generador de CSV completo ─────────────────────────────────────

    def build(self) -> pd.DataFrame:
        T_in  = self.indoor_dry_bulb_temperature()
        unmet = self.average_unmet_cooling(T_in)

        df = pd.DataFrame({
            'month':                                      self.month(),
            'hour':                                       self.hour(),
            'day_type':                                   self.day_type(),
            'daylight_savings_status':                    self.daylight_savings(),
            'indoor_dry_bulb_temperature':                T_in,
            'average_unmet_cooling_setpoint_difference':  unmet,
            'indoor_relative_humidity':                   self.indoor_relative_humidity(),
            'non_shiftable_load':                         self.non_shiftable_load(),
            'dhw_demand':                                 self.dhw_demand(),
            'cooling_demand':                             self.cooling_demand(),
            'heating_demand':                             self.heating_demand(),
            'solar_generation':                           self.solar_generation_col(),
        })
        return df


# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 5 — SupportFilesGenerator
# ═══════════════════════════════════════════════════════════════════════════════

class SupportFilesGenerator:
    """Genera archivos de soporte: weather, carbon, pricing, chargers, washing machine."""

    def build_weather_csv(self, weather_dfs: dict) -> pd.DataFrame:
        full = pd.concat([weather_dfs[y] for y in YEARS])
        df = pd.DataFrame(index=range(len(full)))

        df['outdoor_dry_bulb_temperature']  = full['T2M'].values
        df['outdoor_relative_humidity']     = full['RH2M'].values
        df['diffuse_solar_irradiance']      = full['DHI'].values
        df['direct_solar_irradiance']       = full['DNI'].values

        def shift_col(arr, n):
            out = np.empty_like(arr)
            if n <= 0:
                return arr.copy()
            out[:-n]  = arr[n:]
            out[-n:]  = arr[-1]
            return out

        for base, col in [
            ('outdoor_dry_bulb_temperature', 'T2M'),
            ('outdoor_relative_humidity',    'RH2M'),
            ('diffuse_solar_irradiance',     'DHI'),
            ('direct_solar_irradiance',      'DNI'),
        ]:
            arr = full[col].values
            for k in range(1, 4):
                df[f'{base}_predicted_{k}'] = shift_col(arr, k)

        return df

    def build_carbon_intensity(self, weather_full: pd.DataFrame) -> pd.DataFrame:
        ghi_frac = (weather_full['GHI'].values / 1000.0).clip(0, 1)
        ci = FE_DIESEL_KG_KWH * (1.0 - SOLAR_PENETRACION * ghi_frac)
        return pd.DataFrame({'carbon_intensity': ci})

    def build_pricing(self, n: int) -> pd.DataFrame:
        # Indice temporal completo para determinar hora punta
        idx = pd.date_range('2023-01-01', periods=n, freq='h', tz=LOCATION_TZ)
        pricing_from_bills = self._build_pricing_from_billing(idx)
        if pricing_from_bills is not None:
            return pricing_from_bills

        h = idx.hour.values
        is_punta = (h >= 18) & (h < 23)
        price = np.where(is_punta, TARIFA_PUNTA_USD, TARIFA_FUERA_USD)

        def shift_col(arr, k):
            out = np.empty_like(arr)
            out[:-k] = arr[k:]
            out[-k:] = arr[-1]
            return out

        df = pd.DataFrame({
            'electricity_pricing':              price,
            'electricity_pricing_predicted_1':  shift_col(price, 1),
            'electricity_pricing_predicted_2':  shift_col(price, 2),
            'electricity_pricing_predicted_3':  shift_col(price, 3),
        })
        return df

    def _build_pricing_from_billing(self, idx: pd.DatetimeIndex) -> pd.DataFrame | None:
        if build_hourly_pricing_from_monthly_measurements is None or load_monthly_measurements is None:
            return None

        try:
            from distill_building_loads import forecast_missing_measurements

            raw = load_monthly_measurements(buildings=DEFAULT_BUILDINGS_WITH_MONTHLY_DATA)
            measurements = forecast_missing_measurements(raw, buildings=DEFAULT_BUILDINGS_WITH_MONTHLY_DATA)
            hourly_index = pd.DataFrame({
                "_year": idx.year,
                "_month": idx.month,
                "hour": idx.hour,
            })
            pricing, audit = build_hourly_pricing_from_monthly_measurements(hourly_index, measurements)
            if pricing.empty:
                return None

            max_delta = float(audit["cost_delta_pct"].abs().max()) if not audit.empty else 0.0
            logger.info(
                "  pricing.csv: calibrado desde TotalFacturado mensual "
                f"(max_delta_factura={max_delta:.9f}%)"
            )
            return pricing
        except Exception as exc:
            logger.warning(f"  pricing desde facturacion fallo ({exc}); usando TOU por defecto")
            return None

    def build_charger_csv(
        self,
        bldg_id: int,
        charger_idx: int,
        n_hours: int,
    ) -> pd.DataFrame:
        """
        Genera charger CSV con formato CityLearn v2 correcto:
          Estado 3: cargador vacío, columnas auxiliares con centinelas CityLearn
          Estado 2: 1 fila pre-llegada, estimated_arrival_time=0.0, soc_arrival en %
          Estado 1: sesión completa, departure_time = cuenta regresiva (dur-1 → 0),
                    required_soc_departure en % (0-100)
        """
        cfg_list = EV_CONFIG[bldg_id]
        cfg_entry = cfg_list[charger_idx]
        ev_type, arr_h, dep_h, soc_min, soc_max, soc_req, bat_kwh, kw = cfg_entry
        days_active = EV_DAYS_ACTIVE.get(ev_type, 'laboral')

        rng = np.random.default_rng(seed=bldg_id * 100 + charger_idx)
        idx = pd.date_range('2023-01-01', periods=n_hours, freq='h', tz=LOCATION_TZ)

        # Mapa timestamp → posición para lookups O(1)
        ts_to_pos = {ts: i for i, ts in enumerate(idx)}

        # Default: estado 3 (cargador vacío), sin NaN en CSV. CityLearn usa
        # -1 para tiempos ausentes y -0.1 para SOC ausente.
        state   = np.full(n_hours, 3.0)
        ev_id   = np.full(n_hours, "NONE", dtype=object)
        dep_t   = np.full(n_hours, -1.0)
        req_soc = np.full(n_hours, -0.1)
        arr_t   = np.full(n_hours, -1.0)
        arr_soc = np.full(n_hours, -0.1)

        # Nombre fijo por cargador — CityLearn v2 usa objetos EV persistentes
        # que vuelven al mismo cargador múltiples veces durante el año
        ev_name = f"EV_B{bldg_id}_C{charger_idx + 1}"

        dates = pd.date_range('2023-01-01', periods=n_hours // 24 + 2, freq='D', tz=LOCATION_TZ)

        for day in dates:
            dow = day.dayofweek
            if days_active == 'laboral' and dow >= 5:
                continue
            if rng.random() > 0.90:
                continue

            # Hora de llegada mín. 1 para dejar espacio al estado 2 previo
            actual_arr = int(np.clip(rng.normal(arr_h, 1.0), 1, 22))
            actual_dep = int(np.clip(rng.normal(dep_h, 0.5), actual_arr + 1, 23))
            soc_arr_pct = float(np.clip(rng.uniform(soc_min, soc_max), 0, 1)) * 100.0

            # ── Estado 2: 1 fila pre-llegada. Si la llegada cae a medianoche,
            # la fila previa real es la última hora del día anterior.
            ts_pre = day + pd.Timedelta(hours=actual_arr - 1) if actual_arr > 0 else day - pd.Timedelta(hours=1)
            pos_pre = ts_to_pos.get(ts_pre)
            if pos_pre is not None and state[pos_pre] == 3.0:
                state[pos_pre]   = 2.0
                ev_id[pos_pre]   = ev_name
                arr_t[pos_pre]   = 0.0          # CityLearn v2: siempre 0.0
                arr_soc[pos_pre] = soc_arr_pct  # SOC de llegada en %

            # ── Estado 1: sesión completa con cuenta regresiva ────────────────
            for h_off in range(actual_arr, actual_dep + 1):
                ts = day + pd.Timedelta(hours=h_off)
                pos = ts_to_pos.get(ts)
                if pos is None or pos >= n_hours:
                    continue
                state[pos]   = 1.0
                ev_id[pos]   = ev_name
                dep_t[pos]   = float(actual_dep - h_off)  # cuenta regresiva → 0
                req_soc[pos] = soc_req * 100.0             # en % (ej. 0.85 → 85.0)

        df = pd.DataFrame({
            'electric_vehicle_charger_state':          state.astype(int),  # int requerido — str(1.0).isdigit()==False
            'electric_vehicle_id':                     ev_id,
            'electric_vehicle_departure_time':          dep_t,
            'electric_vehicle_required_soc_departure':  req_soc,
            'electric_vehicle_estimated_arrival_time':  arr_t,
            'electric_vehicle_estimated_soc_arrival':   arr_soc,
        })
        return df

    def build_washing_machine(self, n_hours: int, bldg_id: int = 1) -> pd.DataFrame:
        """
        Controlled shiftable load for one building through CityLearn's
        WashingMachine interface.

        Output format:
          - hour: int 1-24
          - day_type: int 1-7
          - wm_start_time_step: absolute 0-based window start, -1 when inactive
          - wm_end_time_step: absolute 0-based window end, -1 when inactive
          - load_profile: string list of kWh values or '[]' when inactive
        """
        idx    = pd.date_range('2023-01-01', periods=n_hours, freq='h', tz=LOCATION_TZ)
        h1     = (idx.hour.values + 1).astype(int)   # 0→1 … 23→24
        dow    = idx.dayofweek.values.astype(int)     # 0=Lun … 6=Dom
        dtype  = (dow + 1).astype(int)                # 1=Lun … 7=Dom

        cfg = MADRL_BUILDING_CONSTANTS[bldg_id]
        btype = cfg["bldg_type"]
        rule = CONTROLLED_MACHINE_RULES.get(
            btype,
            {"days": "laboral", "profile": [0.60, 0.40]},
        )
        occ_start, occ_end = OCCUPANCY_HOURS.get(btype, (7, 17))
        duration = len(rule["profile"])

        # Convert 0-based operating hours to CityLearn file hour convention.
        win_h_start = int(occ_start) + 1
        win_h_end = max(win_h_start, int(occ_end) - duration + 1)
        win_h_end = min(24, win_h_end)
        if int(occ_end) >= 24:
            win_h_end = 24 - duration + 1
        win_h_end = max(win_h_start, win_h_end)

        cycle_kwh = max(0.1, float(cfg.get("shiftable", 1.0)))
        profile = [round(cycle_kwh * float(frac), 6) for frac in rule["profile"]]
        cycle_load = "[" + ", ".join(f"{value:.6f}" for value in profile) + "]"

        start_ts  = np.full(n_hours, -1, dtype=int)
        end_ts    = np.full(n_hours, -1, dtype=int)
        load_prof = ['[]'] * n_hours

        for i in range(n_hours):
            if rule["days"] == "laboral" and dow[i] >= 5:
                continue
            if win_h_start <= h1[i] <= win_h_end:
                day_start  = i - (h1[i] - 1)             # fila 0 del mismo día
                win_s      = day_start + (win_h_start - 1)
                win_e      = day_start + (win_h_end - 1)
                start_ts[i]  = win_s
                end_ts[i]    = win_e
                load_prof[i] = cycle_load

        return pd.DataFrame({
            'day_type':           dtype,
            'hour':               h1,
            'wm_start_time_step': start_ts,
            'wm_end_time_step':   end_ts,
            'load_profile':       load_prof,
        })


# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 6 — BESSDesigner
# ═══════════════════════════════════════════════════════════════════════════════

class BESSDesigner:
    """Sizing BESS por balance energético acumulado (Hesse et al. 2017)."""

    def size(
        self,
        load_kwh:  np.ndarray,
        solar_kwh: np.ndarray,
    ) -> dict:
        p_net    = load_kwh - solar_kwh
        surplus  = np.maximum(0.0, -p_net)
        deficit  = np.maximum(0.0,  p_net)

        # Sizing por ventana diaria (24h) — promedio de los dias del año
        # para evitar acumulacion espuria sobre 3 años (Hesse et al. 2017)
        n_days = len(load_kwh) // 24
        E_raw_days = []
        for d in range(n_days):
            sl = slice(d*24, (d+1)*24)
            s_d = surplus[sl]
            def_d = deficit[sl]
            soc_d = np.cumsum(s_d * BESS_ETA_C - def_d / BESS_ETA_D)
            E_raw_days.append(soc_d.max() - soc_d.min())
        E_raw = float(np.percentile(E_raw_days, 95))   # percentil 95 de dias

        E_bess = (E_raw / BESS_DOD) * BESS_TARGET_SS
        E_bess = max(E_bess, 10.0)

        p99_discharge = float(np.percentile(deficit, 99))
        p99_charge    = float(np.percentile(surplus, 99))
        P_bess = max(p99_discharge, p99_charge, 5.0)

        # Cota superior: maximo 4 horas de potencia nominal (practica industria)
        E_bess = min(E_bess, P_bess * 4.0)

        return {
            'capacity':           round(E_bess, 1),
            'nominal_power':      round(P_bess, 1),
            'depth_of_discharge': BESS_DOD,
            'efficiency':         round(BESS_ETA_RT, 4),
            'loss_coefficient':   BESS_LOSS,
            'initial_charge':     BESS_SOC_INI,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 7 — SchemaBuilder
# ═══════════════════════════════════════════════════════════════════════════════

class SchemaBuilder:
    """Construye schema.json para CityLearn v2 con los 17 edificios."""

    def build(
        self,
        bess_params: dict,
        solar_kw:    dict,
        charger_map: dict,
    ) -> dict:

        # ── Observaciones activas (todas activadas para MADRL) ─────────────────
        observations = {
            "month":                                          {"active": True,  "shared_in_central_agent": True},
            "day_type":                                       {"active": True,  "shared_in_central_agent": True},
            "hour":                                           {"active": True,  "shared_in_central_agent": True},
            "daylight_savings_status":                        {"active": False, "shared_in_central_agent": True},
            "outdoor_dry_bulb_temperature":                   {"active": True,  "shared_in_central_agent": True},
            "outdoor_dry_bulb_temperature_predicted_1":       {"active": True,  "shared_in_central_agent": True},
            "outdoor_dry_bulb_temperature_predicted_2":       {"active": True,  "shared_in_central_agent": True},
            "outdoor_dry_bulb_temperature_predicted_3":       {"active": True,  "shared_in_central_agent": True},
            "outdoor_relative_humidity":                      {"active": True,  "shared_in_central_agent": True},
            "outdoor_relative_humidity_predicted_1":          {"active": True,  "shared_in_central_agent": True},
            "outdoor_relative_humidity_predicted_2":          {"active": True,  "shared_in_central_agent": True},
            "outdoor_relative_humidity_predicted_3":          {"active": True,  "shared_in_central_agent": True},
            "diffuse_solar_irradiance":                       {"active": True,  "shared_in_central_agent": True},
            "diffuse_solar_irradiance_predicted_1":           {"active": True,  "shared_in_central_agent": True},
            "diffuse_solar_irradiance_predicted_2":           {"active": True,  "shared_in_central_agent": True},
            "diffuse_solar_irradiance_predicted_3":           {"active": True,  "shared_in_central_agent": True},
            "direct_solar_irradiance":                        {"active": True,  "shared_in_central_agent": True},
            "direct_solar_irradiance_predicted_1":            {"active": True,  "shared_in_central_agent": True},
            "direct_solar_irradiance_predicted_2":            {"active": True,  "shared_in_central_agent": True},
            "direct_solar_irradiance_predicted_3":            {"active": True,  "shared_in_central_agent": True},
            "carbon_intensity":                               {"active": True,  "shared_in_central_agent": True},
            "indoor_dry_bulb_temperature":                    {"active": True,  "shared_in_central_agent": False},
            "average_unmet_cooling_setpoint_difference":      {"active": True,  "shared_in_central_agent": False},
            "indoor_relative_humidity":                       {"active": True,  "shared_in_central_agent": False},
            "non_shiftable_load":                             {"active": True,  "shared_in_central_agent": False},
            "solar_generation":                               {"active": True,  "shared_in_central_agent": False},
            "cooling_storage_soc":                            {"active": False, "shared_in_central_agent": False},
            "heating_storage_soc":                            {"active": False, "shared_in_central_agent": False},
            "dhw_storage_soc":                                {"active": False, "shared_in_central_agent": False},
            "electrical_storage_soc":                         {"active": True,  "shared_in_central_agent": False},
            "net_electricity_consumption":                    {"active": True,  "shared_in_central_agent": False},
            "electricity_pricing":                            {"active": True,  "shared_in_central_agent": True},
            "electricity_pricing_predicted_1":                {"active": True,  "shared_in_central_agent": True},
            "electricity_pricing_predicted_2":                {"active": True,  "shared_in_central_agent": True},
            "electricity_pricing_predicted_3":                {"active": True,  "shared_in_central_agent": True},
            "power_outage":                                   {"active": False, "shared_in_central_agent": False},
            "hvac_mode":                                      {"active": False, "shared_in_central_agent": False},
            "comfort_band":                                   {"active": False, "shared_in_central_agent": False},
            "electric_vehicle_charger_connected_state":                        {"active": True,  "shared_in_central_agent": True},
            "connected_electric_vehicle_at_charger_battery_capacity":          {"active": True,  "shared_in_central_agent": True},
            "connected_electric_vehicle_at_charger_departure_time":            {"active": True,  "shared_in_central_agent": True},
            "connected_electric_vehicle_at_charger_required_soc_departure":    {"active": True,  "shared_in_central_agent": True},
            "connected_electric_vehicle_at_charger_soc":                       {"active": True,  "shared_in_central_agent": True},
            "electric_vehicle_charger_incoming_state":                         {"active": True,  "shared_in_central_agent": True},
            "incoming_electric_vehicle_at_charger_estimated_arrival_time":     {"active": True,  "shared_in_central_agent": True},
            "washing_machine_start_time_step":                {"active": True,  "shared_in_central_agent": True},
            "washing_machine_end_time_step":                  {"active": True,  "shared_in_central_agent": True},
            "washing_machine_load_profile":                   {"active": True,  "shared_in_central_agent": True},
        }

        actions = {
            "cooling_storage":        {"active": False},
            "heating_storage":        {"active": False},
            "dhw_storage":            {"active": False},
            "electrical_storage":     {"active": True},
            "electric_vehicle_storage": {"active": True},
            "washing_machine":        {"active": True},
        }

        # ── EV base por cargador. La sincronizacion DER final reemplaza esto por
        # pools EV por toma para que cada sesion tenga SOC propio.
        EV_BATTERY_PARAMS = {
            'mototaxi':  {"capacity": 6,  "nominal_power": 4.0, "initial_soc": 0.40, "depth_of_discharge": 0.80},
            'motolineal':{"capacity": 4,  "nominal_power": 3.0, "initial_soc": 0.40, "depth_of_discharge": 0.80},
            'moto_lineal':{"capacity": 4,  "nominal_power": 3.0, "initial_soc": 0.40, "depth_of_discharge": 0.80},
            'camioneta': {"capacity": 40, "nominal_power": 7.4, "initial_soc": 0.35, "depth_of_discharge": 0.85},
            'v2g':       {"capacity": 40, "nominal_power": 7.4, "initial_soc": 0.25, "depth_of_discharge": 0.85},
        }
        electric_vehicles_def = {}
        for bldg_id_ev, cfg_list in EV_CONFIG.items():
            for cidx, cfg_entry in enumerate(cfg_list):
                ev_type_key = cfg_entry[0]
                ev_name = f"EV_B{bldg_id_ev}_C{cidx + 1}"
                bat_params = EV_BATTERY_PARAMS.get(ev_type_key, EV_BATTERY_PARAMS['v2g'])
                electric_vehicles_def[ev_name] = {
                    "include": True,
                    "battery": {
                        "type": "citylearn.energy_model.Battery",
                        "autosize": False,
                        "attributes": bat_params,
                    }
                }

        # ── Edificios (dict, no lista) ─────────────────────────────────────────
        buildings = {}
        for bldg_id in sorted(MADRL_BUILDING_CONSTANTS.keys()):
            bess     = bess_params.get(bldg_id, {
                'capacity': 100.0, 'nominal_power': 50.0,
                'depth_of_discharge': 0.80, 'efficiency': 0.9025,
                'loss_coefficient': 1e-5, 'initial_charge': 0.50,
            })
            pv_kw    = solar_kw.get(bldg_id, 100.0)
            chargers = charger_map.get(bldg_id, [])

            # DHW nominal_power explicit (autosize falla en t=0 con T_out=0°C no inicializado)
            DHW_NOMINAL_POWER = {5: 300, 11: 300, 12: 200}
            DHW_BLDGS = {5, 11, 12}

            b = {
                "include": True,
                "energy_simulation": f"Building_{bldg_id}.csv",
                "weather": "weather.csv",
                "carbon_intensity": "carbon_intensity.csv",
                "pricing": "pricing.csv",
                "inactive_observations": [],
                "inactive_actions":      [],
                "cooling_device": {
                    "type": "citylearn.energy_model.HeatPump",
                    "autosize": True,
                    "autosize_attributes": {
                        "safety_factor": COOLING_AUTOSIZE_SAFETY_FACTOR,
                    },
                    "attributes": {},
                },
                "electrical_storage": {
                    "type":     "citylearn.energy_model.Battery",
                    "autosize": False,
                    "attributes": {
                        "capacity":                  round(bess['capacity'], 1),
                        "efficiency":                round(bess['efficiency'], 4),
                        "capacity_loss_coefficient": round(bess['loss_coefficient'], 6),
                        "loss_coefficient":          0.0,
                        "nominal_power":             round(bess['nominal_power'], 1),
                        "initial_soc":               bess.get('initial_soc', bess.get('initial_charge', 0.50)),
                        "depth_of_discharge":        bess['depth_of_discharge'],
                    }
                },
                "pv": {
                    "type":     "citylearn.energy_model.PV",
                    "autosize": False,
                    "attributes": {"nominal_power": round(pv_kw, 1)},
                },
            }

            # Cargadores EV (dict)
            if chargers:
                chargers_dict = {}
                for c in chargers:
                    fname = c["file"].replace(".csv", "")  # "charger_1_1"
                    kw    = c["kw"]
                    ev_type = c.get("ev_type", "")
                    v2g_capable = ev_type in {"camioneta", "v2g"}
                    max_d = kw if v2g_capable else 0.0
                    charger_idx = int(fname.rsplit("_", 1)[-1])
                    physical_idx = math.ceil(charger_idx / 2)
                    outlet_idx = 1 if charger_idx % 2 == 1 else 2
                    phase_connection = ["L1", "L2", "L3"][(charger_idx - 1) % 3]
                    chargers_dict[fname] = {
                        "type": "citylearn.electric_vehicle_charger.Charger",
                        "charger_simulation": c["file"],
                        "autosize": False,
                        "hardware": {
                            "ev_type": ev_type,
                            "mode": 3,
                            "mode_label": "Mode_3_AC_dual_socket",
                            "connector_standard": "IEC_62196_Type_2_socket",
                            "physical_charger_id": f"mode3_B{bldg_id:02d}_{physical_idx:02d}",
                            "socket_count_per_physical_unit": 2,
                            "outlet_index": outlet_idx,
                            "v2g_capable": v2g_capable,
                            "power_flow_direction": "bidirectional_v2g" if v2g_capable else "charge_only",
                            "v2g_max_export_power_kw": round(max_d, 3),
                        },
                        "attributes": {
                            "nominal_power":        kw,
                            "efficiency":           0.95,
                            "charger_type":         3,
                            "max_charging_power":   kw,
                            "min_charging_power":   round(min(kw, 230.0 * 6.0 / 1000.0), 3),
                            "max_discharging_power": max_d,
                            "min_discharging_power": 0.0,
                            "phase_connection":     phase_connection,
                        }
                    }
                b["chargers"] = chargers_dict

            b["washing_machines"] = {
                f"washing_machine_{bldg_id}": {
                    "type": "citylearn.energy_model.WashingMachine",
                    "autosize": False,
                    "washing_machine_energy_simulation": f"Washing_Machine_{bldg_id}.csv",
                }
            }

            # DHW device (B5 Hotel, B11 Hospital Regional, B12 EsSalud)
            if bldg_id in DHW_BLDGS:
                b["dhw_device"] = {
                    "type": "citylearn.energy_model.HeatPump",
                    "autosize": False,
                    "attributes": {"nominal_power": DHW_NOMINAL_POWER[bldg_id]},
                }

            buildings[f"Building_{bldg_id}"] = b

        schema = {
            "random_seed":                2024,
            "root_directory":             None,
            "central_agent":              False,
            "simulation_start_time_step": 0,
            "simulation_end_time_step":   N_HOURS_TOTAL - 1,
            "episode_time_steps":         None,
            "rolling_episode_split":      False,
            "random_episode_split":       False,
            "seconds_per_time_step":      3600,
            "observations":               observations,
            "actions":                    actions,
            "agent": {
                "type":       "citylearn.agents.rbc.BasicElectricVehicleRBC_ReferenceController",
                "attributes": {},
            },
            "reward_function": {
                "type":       "citylearn.reward_function.Electric_Vehicles_Reward_Function",
                "attributes": {},
            },
            "community_market": {
                "enabled":                           True,
                "local_price_ratio_to_grid_import":  0.8,
                "intra_community_sell_ratio":         0.8,
                "grid_export_price":                  0.0,
                "import_member_weights":              {},
                "kpis": {
                    "community_local_traded_enabled":      True,
                    "community_self_consumption_enabled":  True,
                },
            },
            "electric_vehicles_def": electric_vehicles_def,
            "buildings":              buildings,
        }
        return schema


# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 8 — DatasetValidator
# ═══════════════════════════════════════════════════════════════════════════════

class DatasetValidator:
    """Valida cada CSV con reglas físicas y valida el schema con CityLearnEnv."""

    BUILDING_RULES = {
        'month':                                     lambda s: int(s.between(1,12).all()),
        'hour':                                      lambda s: int(s.between(0,23).all()),
        'day_type':                                  lambda s: int(s.between(1,7).all()),
        'daylight_savings_status':                   lambda s: int((s == 0).all()),
        'indoor_dry_bulb_temperature':               lambda s: int(s.between(14,46).all()),
        'average_unmet_cooling_setpoint_difference': lambda s: int((s >= 0).all()),
        'indoor_relative_humidity':                  lambda s: int(s.between(20,100).all()),
        'non_shiftable_load':                        lambda s: int((s >= 0).all()),
        'dhw_demand':                                lambda s: int((s >= 0).all()),
        'cooling_demand':                            lambda s: int((s >= 0).all()),
        'heating_demand':                            lambda s: int((s == 0).all()),
        'solar_generation':                          lambda s: int((s >= 0).all()),
    }

    def validate_building_csv(self, df: pd.DataFrame, bldg_id: int) -> bool:
        ok = True
        if len(df) != N_HOURS_TOTAL:
            logger.error(f"B{bldg_id}: filas={len(df)}, esperado={N_HOURS_TOTAL}")
            ok = False
        if df.isnull().any().any():
            nulls = df.isnull().sum()
            logger.error(f"B{bldg_id}: NaN en columnas: {nulls[nulls>0].to_dict()}")
            ok = False
        for col, rule in self.BUILDING_RULES.items():
            if col in df.columns:
                if not rule(df[col]):
                    logger.warning(f"B{bldg_id}: columna '{col}' fuera de rango")
        return ok

    def validate_weather_csv(self, df: pd.DataFrame) -> bool:
        if len(df) != N_HOURS_TOTAL:
            logger.error(f"weather.csv: filas={len(df)}, esperado={N_HOURS_TOTAL}")
            return False
        if df.isnull().values[:, :4].any():
            logger.warning("weather.csv: NaN en columnas observadas (se permiten en predicciones)")
        return True

    def validate_charger_csv(self, df: pd.DataFrame, bldg_id: int, cidx: int) -> bool:
        ok = True
        if len(df) != N_HOURS_TOTAL:
            logger.error(f"charger_{bldg_id}_{cidx+1}.csv: filas={len(df)}, esperado={N_HOURS_TOTAL}")
            ok = False
        return ok

    def validate_with_citylearn(self, schema_path: Path) -> bool:
        try:
            from citylearn.citylearn import CityLearnEnv
            env = CityLearnEnv(schema=str(schema_path))
            obs, _ = env.reset()
            if obs is None:
                raise ValueError("env.reset() retorno None")
            logger.info("  CityLearnEnv: dataset cargado y validado correctamente")
            return True
        except ImportError:
            logger.warning("  citylearn no instalado — omitiendo validacion con CityLearnEnv")
            return True
        except Exception as e:
            logger.error(f"  CityLearnEnv error: {e}")
            return False


# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 9 — IquitosDatasetPipeline
# ═══════════════════════════════════════════════════════════════════════════════

class IquitosDatasetPipeline:
    """Orquestador principal del pipeline de generación del dataset."""

    def __init__(
        self,
        output_dir: Path  = OUTPUT_DIR_DEFAULT,
        skip_cache: bool  = False,
        validate:   bool  = True,
        buildings:  list  = None,
        sync_der:   bool  = True,
    ):
        self.output_dir = output_dir
        self.skip_cache = skip_cache
        self.validate   = validate
        self.buildings  = buildings or list(range(1, 18))
        self.sync_der   = sync_der

    def run(self):
        try:
            from tqdm import tqdm
        except ImportError:
            def tqdm(it, **kw): return it

        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Directorio de salida: {self.output_dir.resolve()}")

        # ── Etapa 1: Descarga meteorológica ──────────────────────────
        logger.info("[Etapa 1] Descarga de datos meteorológicos")
        wdm = WeatherDataManager(cache_dir=CACHE_DIR, skip_cache=self.skip_cache)
        weather_dfs = {y: wdm.get(y) for y in YEARS}
        weather_full = pd.concat([weather_dfs[y] for y in YEARS])
        full_index   = weather_full.index
        assert len(full_index) == N_HOURS_TOTAL, f"Indice: {len(full_index)} != {N_HOURS_TOTAL}"
        logger.info(f"  Total horas: {len(full_index)} (2023+2024+2025)")

        # ── Etapa 2: Selección de módulo Sandia ──────────────────────
        logger.info("[Etapa 2] Selección de modulo e inversor Sandia")
        try:
            sms = SandiaModelSelector()
            mod_key, mod_params = sms.select_module()
            mps = sms.modules_per_string()
            sandia_available = True
        except ImportError:
            logger.warning("  pvlib no instalado — usando generacion solar simplificada")
            sandia_available = False
            mod_params = {'Area': 2.0, 'Vmpo': 40.0, 'Impo': 10.0}
            mps = 15
            sms = None

        # ── Etapa 3: Generación solar FV por edificio ─────────────────
        logger.info("[Etapa 3] Calculo de generacion solar FV por edificio")
        solar_dict  = {}
        solar_kw_dc = {}

        for bldg_id in tqdm(self.buildings, desc="Solar FV"):
            area_util = MADRL_BUILDING_CONSTANTS[bldg_id]['area_techada_m2'] * AREA_UTIL_FACTOR
            n_mod     = max(1, int(area_util // mod_params['Area']))
            pdc_kw    = n_mod * mod_params['Vmpo'] * mod_params['Impo'] / 1000

            if sandia_available:
                try:
                    solar_dict[bldg_id] = self._calc_solar_pvlib(
                        weather_full, n_mod, mps, mod_params, sms, pdc_kw
                    )
                except Exception as e:
                    logger.warning(f"  B{bldg_id} pvlib error ({e}), usando perfil simplificado")
                    solar_dict[bldg_id] = self._calc_solar_simple(weather_full, pdc_kw)
            else:
                solar_dict[bldg_id] = self._calc_solar_simple(weather_full, pdc_kw)

            solar_kw_dc[bldg_id] = pdc_kw
            logger.debug(f"  B{bldg_id}: {n_mod} modulos, {pdc_kw:.1f} kWp DC")

        # ── Etapa 4: BESS inicial mínimo ──────────────────────────────
        # El dimensionamiento fisico del BESS depende de Building_X.csv ya
        # calibrado, PV actualizado, cargadores EV y balance con red publica.
        # Por eso aqui solo se deja un placeholder para construir schema.json;
        # el valor final obligatorio se aplica en _run_der_synchronization().
        logger.info("[Etapa 4] BESS inicial minimo; el BESS final se calcula despues de PV y EV")
        bess_params = {
            bldg_id: {
                "capacity": 10.0,
                "nominal_power": 5.0,
                "depth_of_discharge": BESS_DOD,
                "efficiency": round(BESS_ETA_RT, 4),
                "loss_coefficient": BESS_LOSS,
                "initial_soc": BESS_SOC_INI,
            }
            for bldg_id in self.buildings
        }

        # ── Etapa 5: Generación Building_X.csv ───────────────────────
        logger.info("[Etapa 5] Generacion Building_X.csv")
        validator = DatasetValidator()

        for bldg_id in tqdm(self.buildings, desc="Building CSV"):
            gen = BuildingDataGenerator(bldg_id, weather_full, solar_dict[bldg_id])
            df  = gen.build()
            if self.validate:
                validator.validate_building_csv(df, bldg_id)
            out = self.output_dir / f"Building_{bldg_id}.csv"
            df.to_csv(out, index=False, float_format='%.6f')
            logger.debug(f"  Guardado: {out.name}")

        # ── Etapa 6: Generación charger_X_Y.csv base ─────────────────
        base_charger_count = sum(len(EV_CONFIG.get(bldg_id, [])) for bldg_id in self.buildings)
        logger.info(
            "[Etapa 6] Generacion charger_X_Y.csv base (%s archivos); "
            "la sincronizacion EV v3 posterior define el conteo final vigente.",
            base_charger_count,
        )
        sfg = SupportFilesGenerator()

        charger_map = {}
        charger_list = [
            (bldg_id, cidx)
            for bldg_id in self.buildings
            for cidx in range(len(EV_CONFIG.get(bldg_id, [])))
        ]

        for bldg_id, cidx in tqdm(charger_list, desc="Charger CSV"):
            df  = sfg.build_charger_csv(bldg_id, cidx, N_HOURS_TOTAL)
            if self.validate:
                validator.validate_charger_csv(df, bldg_id, cidx)
            fname = f"charger_{bldg_id}_{cidx+1}.csv"
            df.to_csv(self.output_dir / fname, index=False, float_format='%.6f')
            cfg_entry = EV_CONFIG[bldg_id][cidx]
            charger_map.setdefault(bldg_id, []).append({
                'file': fname,
                'kw':   cfg_entry[7],
                'ev_type': cfg_entry[0],
            })

        # ── Etapa 7: Washing_Machine_X.csv ───────────────────────────
        logger.info("[Etapa 7] Generacion de cargas controladas Washing_Machine_X.csv")
        for bldg_id in tqdm(self.buildings, desc="Controlled machine CSV"):
            wm_df = sfg.build_washing_machine(N_HOURS_TOTAL, bldg_id)
            wm_df.to_csv(self.output_dir / f"Washing_Machine_{bldg_id}.csv", index=False)

        # ── Etapa 8: weather, carbon_intensity, pricing ───────────────
        logger.info("[Etapa 8] Generacion weather.csv, carbon_intensity.csv, pricing.csv")
        weather_df = sfg.build_weather_csv(weather_dfs)
        if self.validate:
            validator.validate_weather_csv(weather_df)
        weather_df.to_csv(self.output_dir / "weather.csv", index=False, float_format='%.6f')
        logger.info(f"  weather.csv: {len(weather_df)} filas x {len(weather_df.columns)} columnas")

        carbon_df = sfg.build_carbon_intensity(weather_full)
        carbon_df.to_csv(self.output_dir / "carbon_intensity.csv", index=False, float_format='%.6f')
        logger.info(
            f"  carbon_intensity.csv: rango [{carbon_df.values.min():.3f}, "
            f"{carbon_df.values.max():.3f}] kgCO2/kWh"
        )

        pricing_df = sfg.build_pricing(N_HOURS_TOTAL)
        pricing_df.to_csv(self.output_dir / "pricing.csv", index=False, float_format='%.6f')
        price_min = float(pricing_df["electricity_pricing"].min())
        price_max = float(pricing_df["electricity_pricing"].max())
        logger.info(
            f"  pricing.csv: rango [{price_min:.6f}, {price_max:.6f}] "
            "moneda_factura/kWh"
        )

        self._save_carbon_metadata()

        # ── Etapa 9: schema.json ──────────────────────────────────────
        logger.info("[Etapa 9] Generacion schema.json")
        builder = SchemaBuilder()
        schema  = builder.build(bess_params, solar_kw_dc, charger_map)
        schema_path = self.output_dir / "schema.json"
        with open(schema_path, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)
        logger.info(f"  schema.json: {len(schema['buildings'])} edificios")

        # ── Etapa 10: Sincronización DER final ───────────────────────
        if self.sync_der:
            logger.info("[Etapa 10] Sincronizacion DER final para entrenamiento MADRL")
            self._run_der_synchronization()
            # PV, EV y BESS se actualizan en schema.json durante la sincronizacion.
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
        else:
            logger.warning(
                "[Etapa 10] Sincronizacion DER omitida por --no-sync-der; "
                "el BESS queda preliminar y no debe usarse para entrenamiento final."
            )

        # ── Etapa 11: Validación final ────────────────────────────────
        logger.info("[Etapa 11] Validacion final con CityLearnEnv")
        if self.validate:
            validator.validate_with_citylearn(schema_path)

        # ── Resumen ───────────────────────────────────────────────────
        files = list(self.output_dir.glob("*.csv")) + list(self.output_dir.glob("*.json"))
        charger_count = self._final_charger_count(schema_path)
        logger.info(f"\n{'='*60}")
        logger.info("DATASET GENERADO EXITOSAMENTE")
        logger.info(f"  Directorio: {self.output_dir.resolve()}")
        logger.info(f"  Archivos:   {len(files)}")
        logger.info(f"  Edificios:  {len(self.buildings)}")
        logger.info(f"  Horas:      {N_HOURS_TOTAL}")
        logger.info(f"  Cargadores: {charger_count}")
        logger.info(f"{'='*60}")

        self._save_generation_log(bess_params, solar_kw_dc)

    # ── Métodos auxiliares ────────────────────────────────────────────

    def _resolved_output_dir(self) -> Path:
        return (
            self.output_dir
            if self.output_dir.is_absolute()
            else PROJECT_ROOT / self.output_dir
        ).resolve()

    def _run_command(self, label: str, cmd: list[str]) -> None:
        logger.info("  %s", label)
        logger.debug("  comando: %s", " ".join(cmd))
        subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)

    def _run_der_synchronization(self) -> None:
        """Run the audited post-processing chain that CityLearn training uses.

        The base generator builds the initial files. The final training dataset
        must then be synchronized in this order because BESS depends on all
        earlier layers: calibrated base/controlled loads, PV, EV, then public
        grid balance.
        """
        expected = (PROJECT_ROOT / OUTPUT_DIR_DEFAULT).resolve()
        actual = self._resolved_output_dir()
        if actual != expected:
            raise RuntimeError(
                "La sincronizacion DER final solo esta habilitada para el dataset "
                f"activo {OUTPUT_DIR_DEFAULT}. Recibido: {self.output_dir}. "
                "Use el directorio activo o --no-sync-der para una corrida parcial."
            )

        py = sys.executable
        self._run_command(
            "Orquestar sincronizacion final y compuerta de entrenamiento",
            [
                py,
                "-B",
                "tools/dataset/orchestrate_citylearn_dataset.py",
                "--skip-base-generation",
                "--skip-project-context-check",
                "--dataset-dir",
                str(OUTPUT_DIR_DEFAULT),
            ],
        )

    def _final_charger_count(self, schema_path: Path) -> int:
        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            return sum(
                len((bdata.get("chargers") or {}))
                for bdata in schema.get("buildings", {}).values()
            )
        except Exception:
            return 0

    def _calc_solar_pvlib(
        self,
        weather_full: pd.DataFrame,
        n_mod:        int,
        mps:          int,
        mod_params:   dict,
        sms:          SandiaModelSelector,
        pdc_kw:       float,
    ) -> pd.Series:
        import pvlib

        TEMP_PARAMS = pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS[
            'sapm']['open_rack_glass_glass']

        location = pvlib.location.Location(
            latitude=LOCATION_LAT, longitude=LOCATION_LON,
            tz=LOCATION_TZ, altitude=LOCATION_ALT,
        )

        n_strings = max(1, math.ceil(n_mod / mps))
        inv_key, inv_params = sms.select_inverter(pdc_kw)

        array = pvlib.pvsystem.Array(
            mount=pvlib.pvsystem.FixedMount(
                surface_tilt=TILT_DEG, surface_azimuth=AZIMUTH_DEG
            ),
            module_parameters=mod_params,
            temperature_model_parameters=TEMP_PARAMS,
            modules_per_string=mps,
            strings=n_strings,
        )
        system = pvlib.pvsystem.PVSystem(
            arrays=[array],
            inverter_parameters=inv_params,
        )
        mc = pvlib.modelchain.ModelChain(
            system, location,
            aoi_model='sapm',
            spectral_model='sapm',
        )

        weather = weather_full.rename(columns={
            'GHI': 'ghi', 'DHI': 'dhi', 'DNI': 'dni',
            'T2M': 'temp_air', 'WS': 'wind_speed',
        })[['ghi', 'dhi', 'dni', 'temp_air', 'wind_speed']]

        mc.run_model(weather)
        ac_raw = mc.results.ac
        if ac_raw is None:
            raise RuntimeError("ModelChain no produjo resultados AC")
        ac_kw = (ac_raw / 1000.0).clip(lower=0.0).fillna(0.0)
        per_kw = (ac_kw / max(pdc_kw, 1e-9) * 1000.0).clip(lower=0.0)
        per_kw.name = 'solar_generation'
        return per_kw

    def _calc_solar_simple(
        self,
        weather_full: pd.DataFrame,
        pdc_kw:       float,
    ) -> pd.Series:
        ghi = weather_full['GHI'].values
        eta_inv = 0.97
        eta_temp_loss = 0.96
        ac = ghi / 1000.0 * pdc_kw * eta_inv * eta_temp_loss
        per_kw = ac / max(pdc_kw, 1e-9) * 1000.0
        return pd.Series(
            np.clip(per_kw, 0, None),
            index=weather_full.index,
            name='solar_generation',
        )

    def _save_carbon_metadata(self):
        meta = {
            "titulo": "Metadatos de Intensidad de Carbono — Sistema Aislado Iquitos",
            "fuente_principal": "MINAM INFOCARBONO — RAGEI 2019 Energia",
            "url": "https://infocarbono.minam.gob.pe/",
            "factor_emision_diesel": {
                "valor": FE_DIESEL_KG_KWH,
                "unidad": "kg CO2/kWh",
                "referencia": "RAGEI 2019 — Energia, MINAM Peru. Factor de emision para sistemas aislados diesel.",
                "validacion_IPCC": "IPCC Guidelines 2006 — diesel estacionario: 0.79 kg CO2/kWh",
            },
            "generadores": [
                {"empresa": "ELECTRO ORIENTE S.A.", "tipo": "termoelectrica diesel"},
                {"empresa": "GENRENT",               "tipo": "generadores diesel privados"},
            ],
            "penetracion_solar": {
                "valor": SOLAR_PENETRACION,
                "nota": "fraccion de generacion solar en el sistema",
            },
            "rango_carbon_intensity_kg_kwh": {
                "minimo": round(FE_DIESEL_KG_KWH * (1 - SOLAR_PENETRACION * 1.0), 3),
                "maximo": FE_DIESEL_KG_KWH,
                "nota": "varia hora a hora segun irradiancia GHI real",
            },
            "alcance_ghg": "Scope 2 — emisiones indirectas por consumo de electricidad",
            "fecha_acceso": "2025",
        }
        with open(self.output_dir / "carbon_intensity_metadata.json", 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)

    def _save_generation_log(self, bess_params: dict, solar_kw: dict):
        final_bess = {
            str(bid): {
                "capacidad_kwh": bess_params[bid]['capacity'],
                "potencia_kw": bess_params[bid]['nominal_power'],
            }
            for bid in self.buildings if bid in bess_params
        }
        final_solar = {
            str(bid): round(solar_kw.get(bid, 0), 1)
            for bid in self.buildings
        }
        schema_path = self.output_dir / "schema.json"
        if schema_path.exists():
            try:
                schema = json.loads(schema_path.read_text(encoding="utf-8"))
                final_bess = {}
                final_solar = {}
                for bkey, bdata in sorted(
                    schema.get("buildings", {}).items(),
                    key=lambda item: int(item[0].split("_")[1]),
                ):
                    bid = int(bkey.split("_")[1])
                    if bid not in self.buildings:
                        continue
                    storage = bdata.get("electrical_storage", {}).get("attributes", {}) or {}
                    pv_attrs = bdata.get("pv", {}).get("attributes", {}) or {}
                    final_bess[str(bid)] = {
                        "capacidad_kwh": float(storage.get("capacity", 0.0)),
                        "potencia_kw": float(storage.get("nominal_power", 0.0)),
                    }
                    final_solar[str(bid)] = round(float(pv_attrs.get("nominal_power", 0.0)), 1)
            except Exception as exc:
                logger.warning("  No se pudo leer BESS/PV final desde schema.json: %s", exc)

        pricing_path = self.output_dir / "pricing.csv"
        if pricing_path.exists():
            pricing = pd.read_csv(pricing_path, usecols=["electricity_pricing"])
            pricing_summary = {
                "source": "TotalFacturado mensual buildingcsv calibrado por energia punta/fuera punta",
                "currency": "moneda_factura/kWh",
                "min": round(float(pricing["electricity_pricing"].min()), 9),
                "max": round(float(pricing["electricity_pricing"].max()), 9),
                "mean": round(float(pricing["electricity_pricing"].mean()), 9),
            }
        else:
            pricing_summary = {
                "source": "TOU fallback",
                "currency": "USD/kWh",
                "punta_18_22h": TARIFA_PUNTA_USD,
                "fuera_punta": TARIFA_FUERA_USD,
            }

        log = {
            "fecha_generacion": pd.Timestamp.now().isoformat(),
            "anios": YEARS,
            "total_horas": N_HOURS_TOTAL,
            "edificios_generados": len(self.buildings),
            "fuentes_meteorologicas": {
                "2023": "PVGIS-ERA5 (primario) / NASA POWER (fallback)",
                "2024": "NASA POWER",
                "2025": "NASA POWER",
            },
            "bess_por_edificio": {
                bid: values for bid, values in final_bess.items()
            },
            "solar_pv_kwp_dc": final_solar,
            "der_sync_rule": (
                "Final schema is synchronized after generation: load distillation, "
                "pvlib/TMY PV, EV v3 chargers, BESS PV/EV/grid/load balance, DER audit, "
                "training validation."
            ),
            "carbon_intensity_range_kg_kwh": [
                round(FE_DIESEL_KG_KWH * (1 - SOLAR_PENETRACION), 3),
                FE_DIESEL_KG_KWH,
            ],
            "pricing": pricing_summary,
        }
        with open(self.output_dir / "dataset_generation_log.json", 'w', encoding='utf-8') as f:
            json.dump(log, f, indent=2, ensure_ascii=False)
        logger.info("  Log guardado: dataset_generation_log.json")


# ═══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 10 — main()
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Generador de dataset CityLearn v2 para Iquitos 2023-2025",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python tools/dataset/generate_iquitos_dataset.py
  python tools/dataset/generate_iquitos_dataset.py --buildings 1 6 11 12
  python tools/dataset/generate_iquitos_dataset.py --skip-cache --no-validate
  python tools/dataset/generate_iquitos_dataset.py --output-dir ruta/personalizada
        """,
    )
    parser.add_argument(
        "--output-dir", type=Path,
        default=OUTPUT_DIR_DEFAULT,
        help=f"Directorio de salida (default: {OUTPUT_DIR_DEFAULT})",
    )
    parser.add_argument(
        "--buildings", nargs="+", type=int,
        default=list(range(1, 18)),
        help="IDs de edificios a generar (default: 1-17)",
    )
    parser.add_argument(
        "--skip-cache", action="store_true",
        help="Forzar re-descarga de datos meteorologicos",
    )
    parser.add_argument(
        "--no-validate", action="store_true",
        help="Omitir validacion con CityLearnEnv",
    )
    parser.add_argument(
        "--no-sync-der", action="store_true",
        help=(
            "Omitir sincronizacion final de cargas reales, PV, EV, BESS y auditorias. "
            "Solo para corridas parciales; no usar para entrenamiento final."
        ),
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Mostrar mensajes de debug",
    )
    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    logger.info("=" * 60)
    logger.info("Dataset CityLearn v2 — Iquitos 2023-2025")
    logger.info(f"Edificios: {args.buildings}")
    logger.info(f"Salida:    {args.output_dir}")
    logger.info("=" * 60)

    pipeline = IquitosDatasetPipeline(
        output_dir=args.output_dir,
        skip_cache=args.skip_cache,
        validate=not args.no_validate,
        buildings=args.buildings,
        sync_der=not args.no_sync_der,
    )
    pipeline.run()


if __name__ == "__main__":
    main()
