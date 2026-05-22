"""
generate_chargers.py  v2.0
==========================
Genera los 50 archivos charger_X_Y.csv para el dataset CityLearn Iquitos 2023-2025.
Implementa tipos de vehículos eléctricos REALES para Iquitos, Perú 2023-2025.

═══════════════════════════════════════════════════════════════════════════════
TIPOS DE VEHÍCULOS ELÉCTRICOS EN IQUITOS 2023-2025
═══════════════════════════════════════════════════════════════════════════════

Iquitos es ciudad aislada (sin carretera al resto del Perú). El transporte
dominante es el mototaxi (triciclo a motor). La electrificación comenzó ~2022.

1. MOTOTAXI ELÉCTRICA (tipo principal, ~70 000 en Iquitos)
   Marcas: SUNRA RX3, Maverick 3R, Niubo Cargo
   Batería: 60V 60-80Ah LiFePO4  ≈ 3.6-4.8 kWh → modelo: 3.0 kWh
   Cargador: ladrillo AC 60V/16A = 960W → modelo: 1.0 kW
   Carga completa: 3.0 kWh / 1.0 kW ≈ 3h
   Patrón: carga en almuerzo (11:30-13:30) o cambio de turno (17:00-18:30)
   SOC llegada: 35-55% (carga oportunista post-turno mañana)
   SOC requerido: 75-85% (para continuar turno tarde)
   Fuentes: ITDP Peru 2023, MTC registros mototaxis eléctricos Loreto

2. MOTO LINEAL ELÉCTRICA (staff, trabajadores)
   Marcas: AIMA, SUNRA Wave, varias chinas
   Batería: 48V 30Ah LiFePO4 ≈ 1.44 kWh → modelo: 1.5 kWh
   Cargador: AC 48V/15A = 720W → modelo: 1.0 kW (mismo ladrillo que mototaxi)
   Patrón: estaciona TODO EL DÍA mientras el dueño trabaja (7-8h sesión)
   SOC llegada: 30-50% (sale de casa semi-cargada)
   SOC requerido: 85-95% (quiere salir cargada al terminar trabajo)

3. CAMIONETA ELÉCTRICA INSTITUCIONAL (flota pública/institucional)
   Equivalente: BYD M6 Van 55kWh o Wuling Rongguang EV 40kWh (importados x barco)
   El Perú empezó a adquirir flota eléctrica institucional 2022-2025 (PLANEVE 2030)
   Batería: 40 kWh (estimado conservador para flota institucional Perú 2023-2025)
   Cargador: Tipo 2 AC 32A = 7.4 kW (wallbox instalado en institución)
   Patrón: llega con la jornada (7:00-8:00), carga todo el día (6-8h sesión)
   SOC llegada: 35-45% (post-turno o desplazamiento desde base)
   SOC requerido: 85-90% (política institucional)
   Fuentes: MTC Perú PLANEVE 2030, ACN-Data workplace study (Caltech 2019)

4. VAN ELÉCTRICA HOTEL/HOSPITAL (servicio especializado 24h)
   Mismas specs que camioneta pero patrones de turno (hospital) u overnight (hotel)
   Batería: 40 kWh, Cargador: 7.4 kW
   Hospital: turnos 8h (07-15, 15-23, 23-07) → SOC llegada 28-38%, req 88%
   Hotel: arribo nocturno 19:00-22:00, sesión ~10h, req 90%

═══════════════════════════════════════════════════════════════════════════════
DISTRIBUCIÓN DE CARGADORES POR EDIFICIO (total = 50)
═══════════════════════════════════════════════════════════════════════════════
Criterios: tipo de edificio, playa de estacionamiento, flujo de tránsito,
           tiempo de estacionamiento, flota institucional vs. visitantes.

B1  Electro Oriente (50 esp.)   : 2 × camioneta 7.4kW  — flota inspección red
B2  Complejo Champios (200 esp.) : 4 × mototaxi  1.0kW  — visitantes eventos
B3  Aeropuerto IQT (150 esp.)   : 2 × camioneta 7.4kW + 2 × mototaxi 1.0kW
                                    (veh. tierra + zona taxi mototaxi)
B4  Hiperbodega (80 esp.)       : 3 × mototaxi  1.0kW  — clientes/delivery
B5  Hotel El Dorado (60 esp.)   : 1 × van_hotel 7.4kW + 2 × mototaxi 1.0kW
B6  Mall Aventura (500 esp.)    : 3 × camioneta 7.4kW + 5 × mototaxi 1.0kW
B7  UNAP Zungarococha (100 esp.): 1 × camioneta 7.4kW + 2 × mototaxi 1.0kW
B8  Escuela PNP (100 esp.)      : 2 × camioneta 7.4kW  — flota PNP
B9  Complejo CNI (30 esp.)      : 2 × mototaxi  1.0kW  — espectadores
B10 Gobierno Regional (60 esp.) : 3 × camioneta 7.4kW  — flota gubernamental
B11 Hospital Regional (100 esp.): 2 × van_hosp  7.4kW + 2 × mototaxi 1.0kW
B12 EsSalud (80 esp.)           : 2 × van_hosp  7.4kW + 1 × mototaxi 1.0kW
B13 UNAP FACEN (40 esp.)        : 2 × mototaxi  1.0kW  — estudiantes/staff
B14 ENAPU Terminal (50 esp.)    : 2 × camioneta 7.4kW  — flota portuaria
B15 Colegio CNI (30 esp.)       : 2 × mototaxi  1.0kW  — docentes (motos)
B16 I.E. San Juan (20 esp.)     : 1 × mototaxi  1.0kW  — docente
B17 IEST Pedro Águila (40 esp.) : 2 × mototaxi  1.0kW  — estudiantes técnicos

Conteo: 1.0kW=30 (mototaxi/moto) | 7.4kW=20 (camioneta/van) | Total=50

═══════════════════════════════════════════════════════════════════════════════
FORMATO CITYLEARN v2 — ChargerSimulation (citylearn/data.py)
═══════════════════════════════════════════════════════════════════════════════
electric_vehicle_charger_state:
  0 = idle/sin EV
  1 = EV conectado (estado parked/cargando)
  2 = EV aproximándose (incoming — señal predictiva MADRL 1-2h antes)
electric_vehicle_id: str  (p.ej. "EV_B1_C1_001")
electric_vehicle_departure_time: int COUNTDOWN horas hasta partida | NaN
electric_vehicle_required_soc_departure: float PORCENTAJE 0-100 | NaN
  (CityLearn divide por 100 internamente en data.py:922-942)
electric_vehicle_estimated_arrival_time: int COUNTDOWN horas hasta arribo | NaN
electric_vehicle_estimated_soc_arrival: float PORCENTAJE 0-100 | NaN

Fuentes:
  ACN-Data Caltech workplace (2018-2020): https://github.com/zach401/acnportal
  ElaadNL Open Data (2021): https://github.com/ElaadNL
  ITDP Peru mototaxi electrification study (2023)
  MTC Peru PLANEVE 2030 — Plan de electromovilidad
  e-rickshaw/e-tuk-tuk data (India/Bangladesh) como proxy mototaxi Iquitos
  NREL EV Workplace Charging Study (2015) — doi.org/10.2172/1233142
  European Hospital Fleet EV Study (Saarinen et al. 2022)
"""

import logging
import numpy as np
import pandas as pd
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("chargers")

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent.parent
DATASET_DIR = BASE_DIR / "CityLearn/data/datasets/citylearn_iquitos_2023_2025"
YEARS       = [2023, 2024, 2025]
TZ          = "America/Lima"

COLS = [
    'electric_vehicle_charger_state',
    'electric_vehicle_id',
    'electric_vehicle_departure_time',
    'electric_vehicle_required_soc_departure',
    'electric_vehicle_estimated_arrival_time',
    'electric_vehicle_estimated_soc_arrival',
]

# ─── Índice horario completo 2023-2025 ────────────────────────────────────────
def _make_index():
    parts = [pd.date_range(f"{y}-01-01", f"{y}-12-31 23:00", freq="h", tz=TZ) for y in YEARS]
    idx = parts[0]
    for p in parts[1:]:
        idx = idx.append(p)
    return idx

FULL_INDEX = _make_index()   # 26 304 filas
N          = len(FULL_INDEX)
TS_TO_POS  = {ts: i for i, ts in enumerate(FULL_INDEX)}

# ─── Tipos de EV para Iquitos 2023-2025 ──────────────────────────────────────
# Cada tipo define los parámetros base del perfil de sesión.
# Los campos se mezclan con overrides en CHARGER_CFG.

EV_TYPES = {
    # ─────────────────────────────────────────────────────────────────────────
    # MOTOTAXI ELÉCTRICA (tipo dominante en Iquitos)
    # Batería 60V 60Ah LiFePO4 ≈ 3.0 kWh | Cargador ladrillo 60V/16A = 1.0 kW
    # Datos: ITDP Peru 2023; e-rickshaw studies (proxy)
    #   SOC llegada: 35-55% (post-turno mañana, carga oportunista)
    #   Sesión: almuerzo 11:30-13:30 o cambio turno 17:00-18:30
    #   Sesión: 1.5-2.5h (no carga completa — solo recarga parcial en pausa)
    # ─────────────────────────────────────────────────────────────────────────
    'mototaxi': {
        'charger_kw':  1.0,
        'bat_kwh':     3.0,
        'arr_mu':     12.0,  # hora media de arribo (almuerzo)
        'arr_sig':     1.5,  # desviación (llegan escalonados)
        'ses_mu':      1.8,  # duración media sesión [h]
        'ses_sig':     0.4,
        'soc_arr_mu':  42,   # SOC al llegar [%]
        'soc_arr_sig': 12,
        'soc_req_mu':  80,   # SOC requerido al salir [%]
        'soc_req_sig':  8,
        'prob_wd':     0.75, # prob sesión día laboral (lun-vie)
        'prob_we':     0.50, # prob sesión fin de semana (mototaxistas trabajan 6/7 días)
        'ev_label':   'mototaxi_electrica',
    },
    # ─────────────────────────────────────────────────────────────────────────
    # MOTOTAXI VISITANTE (en edificios públicos: mall, deportivo, hiperbodega)
    # Mismos specs técnicos pero arribo más aleatorio (cliente, no empleado)
    # ─────────────────────────────────────────────────────────────────────────
    'mototaxi_visitante': {
        'charger_kw':  1.0,
        'bat_kwh':     3.0,
        'arr_mu':     13.5,  # visitante llega más tarde (hora compras/recreo)
        'arr_sig':     2.5,
        'ses_mu':      1.5,
        'ses_sig':     0.5,
        'soc_arr_mu':  48,
        'soc_arr_sig': 15,
        'soc_req_mu':  78,
        'soc_req_sig': 10,
        'prob_wd':     0.65,
        'prob_we':     0.82,  # más visitantes fin de semana
        'ev_label':   'mototaxi_electrica',
    },
    # ─────────────────────────────────────────────────────────────────────────
    # MOTOTAXI NOCTURNA (aeropuerto, zona taxi)
    # Operan turnos que incluyen madrugada y noche
    # ─────────────────────────────────────────────────────────────────────────
    'mototaxi_taxi_area': {
        'charger_kw':  1.0,
        'bat_kwh':     3.0,
        'arr_mu':     10.0,  # entre vuelos (vuelos principales ~07:00, 12:00, 17:00)
        'arr_sig':     3.5,
        'ses_mu':      1.5,
        'ses_sig':     0.5,
        'soc_arr_mu':  40,
        'soc_arr_sig': 15,
        'soc_req_mu':  78,
        'soc_req_sig':  8,
        'prob_wd':     0.88,
        'prob_we':     0.88,
        'ev_label':   'mototaxi_electrica',
    },
    # ─────────────────────────────────────────────────────────────────────────
    # CAMIONETA ELÉCTRICA INSTITUCIONAL
    # Equivalente BYD M6 Van 40kWh o similar (flota pública Perú PLANEVE)
    # Datos: ACN-Data workplace (Caltech 2019); MTC PLANEVE 2030
    #   SOC llegada: 35-45% (post-turno o desde base)
    #   Sesión: todo el día laborable (6-8h)
    #   SOC requerido: 85-90% (política institucional)
    # ─────────────────────────────────────────────────────────────────────────
    'camioneta': {
        'charger_kw':  7.4,
        'bat_kwh':    40.0,
        'arr_mu':      7.8,  # llega con jornada laboral 07:30-08:00
        'arr_sig':     0.5,
        'ses_mu':      7.5,  # estaciona todo el día
        'ses_sig':     0.6,
        'soc_arr_mu':  38,
        'soc_arr_sig': 10,
        'soc_req_mu':  85,
        'soc_req_sig':  5,
        'prob_wd':     0.85,
        'prob_we':     0.02,  # muy raro fin de semana
        'ev_label':   'camioneta_electrica',
    },
    # ─────────────────────────────────────────────────────────────────────────
    # CAMIONETA PNP (flota policial, horario estricto)
    # Mayor disciplina horaria, SOC requerido más alto (emergencias)
    # ─────────────────────────────────────────────────────────────────────────
    'camioneta_pnp': {
        'charger_kw':  7.4,
        'bat_kwh':    40.0,
        'arr_mu':      7.0,  # horario estricto 07:00
        'arr_sig':     0.3,
        'ses_mu':      8.0,
        'ses_sig':     0.3,
        'soc_arr_mu':  32,
        'soc_arr_sig':  8,
        'soc_req_mu':  90,
        'soc_req_sig':  3,
        'prob_wd':     0.88,
        'prob_we':     0.30,  # algunos sábados
        'ev_label':   'camioneta_electrica',
    },
    # ─────────────────────────────────────────────────────────────────────────
    # VAN ELÉCTRICA HOSPITAL (3 turnos, 24h/365)
    # Datos: European Hospital Fleet EV Study (Saarinen et al. 2022)
    #   Turnos: 07-15h, 15-23h, 23-07h
    #   SOC llegada: 28-38% (post-turno intensivo)
    #   SOC requerido: 88% (emergencias, must have range)
    # ─────────────────────────────────────────────────────────────────────────
    'van_hospital': {
        'charger_kw':  7.4,
        'bat_kwh':    40.0,
        'arr_mu':      7.0,   # turno mañana como base
        'arr_sig':     0.5,
        'ses_mu':      7.8,
        'ses_sig':     0.4,
        'soc_arr_mu':  30,
        'soc_arr_sig': 10,
        'soc_req_mu':  88,
        'soc_req_sig':  4,
        'prob_wd':     0.92,
        'prob_we':     0.90,  # hospitales operan 24h/7
        'shifts':     [(7, 15), (15, 23), (23, 7)],  # 3 turnos médicos
        'ev_label':   'camioneta_electrica',
    },
    # ─────────────────────────────────────────────────────────────────────────
    # VAN ELÉCTRICA HOTEL (sesiones overnight, huéspedes y traslado aeropuerto)
    # Hotel: check-in nocturno ~20:00-22:00, check-out ~08:00-11:00 → 10h sesión
    # ─────────────────────────────────────────────────────────────────────────
    'van_hotel': {
        'charger_kw':  7.4,
        'bat_kwh':    40.0,
        'arr_mu':     20.5,  # huésped check-in 19:00-22:00
        'arr_sig':     1.2,
        'ses_mu':     10.0,  # overnight
        'ses_sig':     1.5,
        'soc_arr_mu':  35,
        'soc_arr_sig': 12,
        'soc_req_mu':  90,
        'soc_req_sig':  4,
        'prob_wd':     0.65,
        'prob_we':     0.78,  # más visitantes fin de semana
        'overnight':   True,
        'ev_label':   'camioneta_electrica',
    },
    # ─────────────────────────────────────────────────────────────────────────
    # VAN AEROPUERTO (vehículos de tierra, personal de vuelo, 3 turnos)
    # IQT aeropuerto pequeño (~8-10 vuelos/día, 06:00-19:00)
    # ─────────────────────────────────────────────────────────────────────────
    'van_aeropuerto': {
        'charger_kw':  7.4,
        'bat_kwh':    40.0,
        'arr_mu':      6.5,
        'arr_sig':     1.5,
        'ses_mu':      7.0,
        'ses_sig':     1.0,
        'soc_arr_mu':  32,
        'soc_arr_sig': 10,
        'soc_req_mu':  88,
        'soc_req_sig':  4,
        'prob_wd':     0.90,
        'prob_we':     0.88,  # vuelos sábado y domingo también
        'shifts':     [(5, 13), (13, 21)],  # 2 turnos (IQT cierra ~19:00)
        'ev_label':   'camioneta_electrica',
    },
    # ─────────────────────────────────────────────────────────────────────────
    # CAMIONETA PORTUARIA (ENAPU, vehículos de muelle)
    # Operación portuaria: turnos variables según atraques de barcos
    # ─────────────────────────────────────────────────────────────────────────
    'camioneta_portuaria': {
        'charger_kw':  7.4,
        'bat_kwh':    40.0,
        'arr_mu':      6.5,
        'arr_sig':     1.5,
        'ses_mu':      7.5,
        'ses_sig':     1.5,
        'soc_arr_mu':  28,    # carga pesada → batería más baja al volver
        'soc_arr_sig': 10,
        'soc_req_mu':  88,
        'soc_req_sig':  5,
        'prob_wd':     0.88,
        'prob_we':     0.70,  # puerto opera 6/7 días
        'shifts':     [(6, 14), (14, 22), (22, 6)],
        'ev_label':   'camioneta_electrica',
    },
}


# ─── Configuración por edificio: lista de dicts (un dict por cargador) ───────
#
# Cada edificio tiene EXACTAMENTE len(lista) cargadores.
# El índice i en la lista corresponde al archivo charger_{bldg_id}_{i+1}.csv
#
# Se usan los EV_TYPES como base y se pueden sobrescribir campos individuales.
#
def _mk(ev_type, **overrides):
    """Crea config de cargador combinando EV_TYPES[ev_type] con overrides."""
    cfg = dict(EV_TYPES[ev_type])
    cfg.update(overrides)
    return cfg


CHARGER_CFG = {
    # ─────────────────────────────────────────────────────────────────────────
    # B1 — Electro Oriente S.A. (Utility, L-V)
    # Playa: 50 esp. institucionales | Flota: 2 camionetas de inspección de red
    # Justificación: empresa distribuidora de electricidad con flota técnica;
    # MTC PLANEVE 2030 priorizó utilities en electrificación de flota
    # ─────────────────────────────────────────────────────────────────────────
    1: [
        _mk('camioneta', arr_mu=7.5, ses_mu=8.5, prob_wd=0.88, prob_we=0.00),
        _mk('camioneta', arr_mu=8.0, ses_mu=8.0, prob_wd=0.82, prob_we=0.00),
    ],

    # ─────────────────────────────────────────────────────────────────────────
    # B2 — Complejo Champios (Deportivo, eventos vespertinos/fines de semana)
    # Playa: 200 esp. | Visitantes llegan en mototaxi (transporte dominante IQT)
    # 4 cargadores mototaxi para espectadores/visitantes durante eventos
    # ─────────────────────────────────────────────────────────────────────────
    2: [
        _mk('mototaxi_visitante', arr_mu=14.0, prob_wd=0.30, prob_we=0.70),
        _mk('mototaxi_visitante', arr_mu=15.5, prob_wd=0.30, prob_we=0.72),
        _mk('mototaxi_visitante', arr_mu=17.0, prob_wd=0.35, prob_we=0.75),
        _mk('mototaxi_visitante', arr_mu=18.5, prob_wd=0.35, prob_we=0.68),
    ],

    # ─────────────────────────────────────────────────────────────────────────
    # B3 — Aeropuerto IQT (Transporte 24h)
    # Playa: 150 esp. | Mix: vehículos de tierra institucionales + zona taxi mototaxi
    # IQT tiene ~8-10 vuelos diarios (06:00-19:00). Flota terrestre pequeña.
    # 2 × camioneta 7.4kW: vehículos de tierra/personal de vuelo
    # 2 × mototaxi 1.0kW: zona de taxi mototaxi en ingreso (predominante en IQT)
    # ─────────────────────────────────────────────────────────────────────────
    3: [
        _mk('van_aeropuerto', shifts=[(5, 13), (13, 21)]),   # van tierra turno A
        _mk('van_aeropuerto', shifts=[(13, 21), (5, 13)]),   # van tierra turno B
        _mk('mototaxi_taxi_area', arr_mu=9.0),               # taxi mototaxi vuelo 1
        _mk('mototaxi_taxi_area', arr_mu=15.0),              # taxi mototaxi vuelo 2
    ],

    # ─────────────────────────────────────────────────────────────────────────
    # B4 — Hiperbodega Precio UNO (Retail, 10:00-22:00)
    # Playa: 80 esp. | Clientes llegan mayoritariamente en mototaxi en IQT
    # 3 × mototaxi 1.0kW para clientes y delivery durante apertura
    # ─────────────────────────────────────────────────────────────────────────
    4: [
        _mk('mototaxi_visitante', arr_mu=11.5, ses_mu=1.5, prob_wd=0.62, prob_we=0.78),
        _mk('mototaxi_visitante', arr_mu=13.5, ses_mu=1.5, prob_wd=0.60, prob_we=0.80),
        _mk('mototaxi_visitante', arr_mu=16.0, ses_mu=1.5, prob_wd=0.58, prob_we=0.75),
    ],

    # ─────────────────────────────────────────────────────────────────────────
    # B5 — Hotel El Dorado Plaza (Hotelero 5★, 24h)
    # Playa: 60 esp. | Mix: van del hotel (traslado aeropuerto) + mototaxis staff
    # 1 × van_hotel 7.4kW: van de servicio hotelero (overnight, check-out 08:00)
    # 2 × mototaxi 1.0kW: staff que llega en mototaxi, estaciona turno completo
    # ─────────────────────────────────────────────────────────────────────────
    5: [
        _mk('van_hotel'),                                     # van hotel overnight
        _mk('mototaxi', arr_mu=7.0, ses_mu=8.0, prob_wd=0.70, prob_we=0.65),
        _mk('mototaxi', arr_mu=15.0, ses_mu=8.0, prob_wd=0.65, prob_we=0.60),
    ],

    # ─────────────────────────────────────────────────────────────────────────
    # B6 — Mall Aventura Iquitos (Mall grande, 10:00-21:00, 7 días)
    # Playa: 400 autos + zona motos/mototaxis | Inaugurado agosto 2023
    # 3 × camioneta 7.4kW: staff gerencial y empleados de tiendas ancla
    # 5 × mototaxi 1.0kW: visitantes que llegan en mototaxi (modo dominante IQT)
    # ElaadNL: sesión retail ~3h; ACN-Data: empleado ~9h
    # ─────────────────────────────────────────────────────────────────────────
    6: [
        _mk('camioneta', arr_mu=9.0, ses_mu=9.0, prob_wd=0.72, prob_we=0.85),   # staff ancla
        _mk('camioneta', arr_mu=9.5, ses_mu=8.5, prob_wd=0.70, prob_we=0.82),
        _mk('camioneta', arr_mu=10.0, ses_mu=8.0, prob_wd=0.68, prob_we=0.80),
        _mk('mototaxi_visitante', arr_mu=11.5, prob_wd=0.70, prob_we=0.88),
        _mk('mototaxi_visitante', arr_mu=13.0, prob_wd=0.68, prob_we=0.88),
        _mk('mototaxi_visitante', arr_mu=15.0, prob_wd=0.65, prob_we=0.85),
        _mk('mototaxi_visitante', arr_mu=16.5, prob_wd=0.62, prob_we=0.82),
        _mk('mototaxi_visitante', arr_mu=18.0, prob_wd=0.60, prob_we=0.80),
    ],

    # ─────────────────────────────────────────────────────────────────────────
    # B7 — UNAP Zungarococha (Universitario, L-V + algunos S)
    # Playa: 100 esp. | Staff llega en mototaxi/moto; 1 camioneta institucional UNAP
    # 1 × camioneta 7.4kW: camioneta UNAP (logística campus, visitas técnicas)
    # 2 × mototaxi 1.0kW: docentes/staff que llegan en mototaxi o moto eléctrica
    # ─────────────────────────────────────────────────────────────────────────
    7: [
        _mk('camioneta', arr_mu=7.5, ses_mu=8.0, prob_wd=0.80, prob_we=0.05),
        _mk('mototaxi', arr_mu=7.5, ses_mu=8.5, prob_wd=0.78, prob_we=0.08),
        _mk('mototaxi', arr_mu=8.0, ses_mu=8.0, prob_wd=0.75, prob_we=0.05),
    ],

    # ─────────────────────────────────────────────────────────────────────────
    # B8 — Escuela Técnica Superior PNP (Militar, L-S)
    # Playa: 100 esp. | Flota institucional PNP (2 camionetas patrulla)
    # Política PNP: alta disciplina horaria, SOC requerido ≥90% por emergencias
    # ─────────────────────────────────────────────────────────────────────────
    8: [
        _mk('camioneta_pnp'),
        _mk('camioneta_pnp', arr_mu=7.3, ses_mu=7.8),
    ],

    # ─────────────────────────────────────────────────────────────────────────
    # B9 — Complejo CNI (Deportivo/Estadio, eventos nocturnos)
    # Playa: 30 esp. | Espectadores llegan en mototaxi (modo dominante IQT)
    # Partidos CNI mayormente nocturnos (19:00-22:00)
    # ─────────────────────────────────────────────────────────────────────────
    9: [
        _mk('mototaxi_visitante', arr_mu=17.5, ses_mu=3.0, prob_wd=0.28, prob_we=0.62),
        _mk('mototaxi_visitante', arr_mu=18.5, ses_mu=3.0, prob_wd=0.25, prob_we=0.60),
    ],

    # ─────────────────────────────────────────────────────────────────────────
    # B10 — Gobierno Regional Loreto (Administrativo, L-V 07:00-15:00)
    # Playa: 60 esp. | Flota gubernamental: camionetas pick-up
    # PLANEVE 2030: el GORE Loreto debe electrificar flota (3 unidades estimadas)
    # ─────────────────────────────────────────────────────────────────────────
    10: [
        _mk('camioneta', arr_mu=7.5, ses_mu=7.5, prob_wd=0.85, prob_we=0.00),
        _mk('camioneta', arr_mu=7.8, ses_mu=7.2, prob_wd=0.82, prob_we=0.00),
        _mk('camioneta', arr_mu=8.0, ses_mu=7.0, prob_wd=0.80, prob_we=0.00),
    ],

    # ─────────────────────────────────────────────────────────────────────────
    # B11 — Hospital Regional Loreto (Salud 24h, 176 camas)
    # Playa: 100 esp. | 2 vans hospitalarias (3 turnos) + 2 mototaxi staff médico
    # Saarinen et al. (2022): hospital fleet 3 turnos 8h, SOC llegada 28-38%
    # Personal de salud también llega en mototaxi en Iquitos
    # ─────────────────────────────────────────────────────────────────────────
    11: [
        _mk('van_hospital', shifts=[(7, 15), (15, 23), (23, 7)]),
        _mk('van_hospital', shifts=[(15, 23), (23, 7), (7, 15)]),
        _mk('mototaxi', arr_mu=7.0, ses_mu=8.5, prob_wd=0.88, prob_we=0.85),
        _mk('mototaxi', arr_mu=15.0, ses_mu=8.5, prob_wd=0.85, prob_we=0.82),
    ],

    # ─────────────────────────────────────────────────────────────────────────
    # B12 — EsSalud Hospital III (Salud, 600 consultas/día)
    # Playa: 80 esp. | Similar a B11 pero más pequeño
    # 2 vans hospitalarias (3 turnos) + 1 mototaxi staff
    # ─────────────────────────────────────────────────────────────────────────
    12: [
        _mk('van_hospital', shifts=[(7, 15), (15, 23), (23, 7)]),
        _mk('van_hospital', shifts=[(15, 23), (23, 7), (7, 15)]),
        _mk('mototaxi', arr_mu=7.5, ses_mu=8.0, prob_wd=0.85, prob_we=0.82),
    ],

    # ─────────────────────────────────────────────────────────────────────────
    # B13 — Facultad Economía UNAP (Universitario pequeño, L-V)
    # Playa: 40 esp. | Estudiantes y docentes llegan en mototaxi/moto
    # ─────────────────────────────────────────────────────────────────────────
    13: [
        _mk('mototaxi', arr_mu=8.0, ses_mu=7.5, prob_wd=0.72, prob_we=0.03),
        _mk('mototaxi', arr_mu=8.5, ses_mu=7.0, prob_wd=0.68, prob_we=0.02),
    ],

    # ─────────────────────────────────────────────────────────────────────────
    # B14 — Terminal Portuario ENAPU (Portuario 24h)
    # Playa: 50 esp. | Vehículos portuarios eléctricos (montacargas pequeños, UTVs)
    # Puerto opera según atraques; 3 turnos variables
    # 2 × camioneta_portuaria 7.4kW: vehículos de patio/muelle
    # ─────────────────────────────────────────────────────────────────────────
    14: [
        _mk('camioneta_portuaria', shifts=[(6, 14), (14, 22), (22, 6)]),
        _mk('camioneta_portuaria', shifts=[(14, 22), (22, 6), (6, 14)]),
    ],

    # ─────────────────────────────────────────────────────────────────────────
    # B15 — Colegio Nacional de Iquitos CNI (Educación, 2 326 alumnos)
    # Playa: 30 esp. | Docentes y personal administrativo llegan en mototaxi/moto
    # 2 × mototaxi 1.0kW para docentes que estacionan durante jornada escolar
    # ─────────────────────────────────────────────────────────────────────────
    15: [
        _mk('mototaxi', arr_mu=7.0, ses_mu=7.0, prob_wd=0.78, prob_we=0.00),
        _mk('mototaxi', arr_mu=7.2, ses_mu=6.8, prob_wd=0.75, prob_we=0.00),
    ],

    # ─────────────────────────────────────────────────────────────────────────
    # B16 — I.E. San Juan (Educación, Bicentenario, escuela emblemática)
    # Playa: 20 esp. | 1 mototaxi para docente (estaciona durante jornada)
    # ─────────────────────────────────────────────────────────────────────────
    16: [
        _mk('mototaxi', arr_mu=7.0, ses_mu=7.0, prob_wd=0.72, prob_we=0.00),
    ],

    # ─────────────────────────────────────────────────────────────────────────
    # B17 — IEST Pedro del Águila Hidalgo (Educación técnica, L-S)
    # Playa: 40 esp. | Estudiantes técnicos y docentes en mototaxi/moto eléctrica
    # Electricidad Industrial y Mecánica Automotriz → familiarizados con EVs
    # ─────────────────────────────────────────────────────────────────────────
    17: [
        _mk('mototaxi', arr_mu=7.5, ses_mu=8.0, prob_wd=0.75, prob_we=0.12),
        _mk('mototaxi', arr_mu=7.8, ses_mu=7.5, prob_wd=0.72, prob_we=0.10),
    ],
}

# Verificar totales
_total = sum(len(v) for v in CHARGER_CFG.values())
assert _total == 50, f"Expected 50 chargers, got {_total}"


# ─── Funciones auxiliares ─────────────────────────────────────────────────────

def _sample_soc(mu, sig, rng, lo=5.0, hi=99.0):
    return float(np.clip(rng.normal(mu, sig), lo, hi))


def _find_pos(date, hour_offset):
    """Posición en FULL_INDEX para date + hour_offset horas (cruza días si >23h)."""
    total_h  = date.hour + hour_offset
    day_off  = total_h // 24
    h_in_day = total_h % 24
    target   = date + pd.Timedelta(days=day_off)
    ts = pd.Timestamp(year=target.year, month=target.month, day=target.day,
                      hour=h_in_day, tzinfo=date.tzinfo)
    return TS_TO_POS.get(ts)


def generate_charger_csv(bldg_id, charger_idx, cfg):
    """
    Genera un DataFrame charger_X_Y para un cargador de un edificio.

    cfg: dict con parámetros del EV (de EV_TYPES + overrides de CHARGER_CFG)

    Formato de columnas:
      state=0  : idle — EV_ID=NaN, todas las demás NaN
      state=2  : incoming — EV_ID=str, arr_time=countdown, arr_soc=%, resto NaN
      state=1  : parked  — EV_ID=str, dep_time=countdown, req_soc=%, arr_time, arr_soc
    """
    rng = np.random.default_rng(seed=bldg_id * 1000 + charger_idx)

    # Arrays de salida (inicialmente cero/NaN)
    state    = np.zeros(N, dtype=float)
    ev_id    = np.full(N, np.nan, dtype=object)
    dep_time = np.full(N, np.nan, dtype=float)
    req_soc  = np.full(N, np.nan, dtype=float)
    arr_time = np.full(N, np.nan, dtype=float)
    arr_soc  = np.full(N, np.nan, dtype=float)

    # Parámetros del EV desde cfg
    arr_mu    = cfg['arr_mu']
    arr_sig   = cfg['arr_sig']
    ses_mu    = cfg['ses_mu']
    ses_sig   = cfg['ses_sig']
    prob_wd   = cfg['prob_wd']
    prob_we   = cfg['prob_we']
    overnight = cfg.get('overnight', False)
    shifts    = cfg.get('shifts', None)
    ev_label  = cfg.get('ev_label', 'ev')

    ev_counter = 0

    # Iterar por cada día del dataset
    for day_start in pd.date_range(FULL_INDEX[0].date(), FULL_INDEX[-1].date(),
                                   freq='D', tz=TZ):
        dow = day_start.dayofweek  # 0=lun...6=dom

        # Si hay turnos, iterar sobre cada turno del día
        if shifts:
            for (shift_arr, shift_dep) in shifts:
                prob = prob_wd if dow < 5 else prob_we
                if rng.random() > prob:
                    continue  # no hay EV en este turno este día

                soc_a = _sample_soc(cfg['soc_arr_mu'], cfg['soc_arr_sig'], rng)
                soc_r = _sample_soc(cfg['soc_req_mu'], cfg['soc_req_sig'], rng)
                ev_counter += 1
                ev_name = f"EV_B{bldg_id}_C{charger_idx+1}_{ev_counter:03d}"

                # Hora de arribo con variabilidad
                actual_arr = int(np.clip(rng.normal(shift_arr, cfg['arr_sig']), 0, 23))
                # Duración de sesión = hasta fin de turno
                if shift_dep > shift_arr:
                    n_ses_h = shift_dep - actual_arr
                else:  # turno nocturno cruza medianoche
                    n_ses_h = (24 - actual_arr) + shift_dep
                n_ses_h = max(1, min(n_ses_h, 12))

                # Señal incoming (state=2) 1-2h antes del arribo
                pre_hrs = rng.integers(1, 3)
                for pre in range(pre_hrs, 0, -1):
                    pos = _find_pos(day_start, actual_arr - pre)
                    if pos is not None and state[pos] == 0:
                        state[pos]    = 2
                        ev_id[pos]    = ev_name
                        arr_time[pos] = float(pre)
                        arr_soc[pos]  = round(soc_a, 1)

                # Sesión parked (state=1) con countdown
                for h_off in range(n_ses_h):
                    pos = _find_pos(day_start, actual_arr + h_off)
                    if pos is None or state[pos] == 1:
                        continue
                    state[pos]    = 1
                    ev_id[pos]    = ev_name
                    dep_time[pos] = float(max(0, n_ses_h - h_off - 1))
                    req_soc[pos]  = round(soc_r, 1)
                    arr_time[pos] = float(actual_arr)
                    arr_soc[pos]  = round(soc_a, 1)

        else:
            # Modo estándar: una sesión por día (sin turnos explícitos)
            prob = prob_wd if dow < 5 else prob_we
            if rng.random() > prob:
                continue  # sin EV este día

            soc_a = _sample_soc(cfg['soc_arr_mu'], cfg['soc_arr_sig'], rng)
            soc_r = _sample_soc(cfg['soc_req_mu'], cfg['soc_req_sig'], rng)
            ev_counter += 1
            ev_name = f"EV_B{bldg_id}_C{charger_idx+1}_{ev_counter:03d}"

            # Hora de arribo con variabilidad gaussiana
            actual_arr = int(np.clip(rng.normal(arr_mu, arr_sig), 0, 23))
            # Duración de sesión
            n_ses_h = max(1, int(np.round(rng.normal(ses_mu, ses_sig))))
            if overnight:
                # Sesión nocturna — puede cruzar medianoche
                n_ses_h = max(6, min(n_ses_h, 13))
            else:
                # Sesión diurna — acotada a horas razonables
                n_ses_h = max(1, min(n_ses_h, 14))
                # No superar medianoche si no es overnight
                if actual_arr + n_ses_h > 24:
                    n_ses_h = 24 - actual_arr

            # Señal incoming (state=2) 1-2h antes
            pre_hrs = rng.integers(1, 3)
            for pre in range(pre_hrs, 0, -1):
                pos = _find_pos(day_start, actual_arr - pre)
                if pos is not None and state[pos] == 0:
                    state[pos]    = 2
                    ev_id[pos]    = ev_name
                    arr_time[pos] = float(pre)
                    arr_soc[pos]  = round(soc_a, 1)

            # Sesión parked (state=1) con countdown de horas
            for h_off in range(n_ses_h):
                pos = _find_pos(day_start, actual_arr + h_off)
                if pos is None or state[pos] == 1:
                    continue
                state[pos]    = 1
                ev_id[pos]    = ev_name
                dep_time[pos] = float(max(0, n_ses_h - h_off - 1))
                req_soc[pos]  = round(soc_r, 1)
                arr_time[pos] = float(actual_arr)
                arr_soc[pos]  = round(soc_a, 1)

    return pd.DataFrame({
        'electric_vehicle_charger_state':          state,
        'electric_vehicle_id':                     ev_id,
        'electric_vehicle_departure_time':          dep_time,
        'electric_vehicle_required_soc_departure':  req_soc,
        'electric_vehicle_estimated_arrival_time':  arr_time,
        'electric_vehicle_estimated_soc_arrival':   arr_soc,
    })


def validate_charger(df, fname):
    """Validaciones básicas del CSV generado."""
    errors = []
    if df.iloc[0]['electric_vehicle_charger_state'] != 0:
        errors.append("PRIMERA FILA NO ES 0")
    mask1 = df['electric_vehicle_charger_state'] == 1
    if mask1.sum() > 0:
        req = df.loc[mask1, 'electric_vehicle_required_soc_departure'].dropna()
        if len(req) > 0 and req.max() <= 1.0:
            errors.append(f"SOC EN FRACCION (max={req.max():.3f}) — debe ser %")
        dep = df.loc[mask1, 'electric_vehicle_departure_time'].dropna()
        if len(dep) > 0 and dep.min() < 0:
            errors.append("departure_time NEGATIVO")
    return errors


def update_schema(schema_path):
    """
    Actualiza schema.json con:
      1. Nuevas definiciones de EV para Iquitos (Mototaxi, Camioneta)
      2. nominal_power correcto por cargador según CHARGER_CFG
      3. min_charging_power ajustado al tipo (mototaxi=0.1 kW, camioneta=0.96 kW)
    """
    import json
    schema = json.loads(schema_path.read_text(encoding='utf-8'))

    # ── Nuevas definiciones de EV para Iquitos ────────────────────────────────
    schema['electric_vehicles_def'] = {
        "Mototaxi_Electrica_Iquitos": {
            "include": True,
            "battery": {
                "type": "citylearn.energy_model.Battery",
                "autosize": False,
                "attributes": {
                    "capacity":             3.0,   # kWh — 60V 60Ah LiFePO4
                    "nominal_power":        3.0,
                    "initial_soc":          0.40,  # ~40% SOC inicial
                    "depth_of_discharge":   0.80,
                    "efficiency":           0.92,  # LiFePO4 efficiency
                    "capacity_loss_coefficient": 1e-5,
                }
            }
        },
        "Camioneta_Electrica_Institucional": {
            "include": True,
            "battery": {
                "type": "citylearn.energy_model.Battery",
                "autosize": False,
                "attributes": {
                    "capacity":             40.0,  # kWh — furgoneta/pick-up eléctrico
                    "nominal_power":        40.0,
                    "initial_soc":          0.35,
                    "depth_of_discharge":   0.85,
                    "efficiency":           0.94,
                    "capacity_loss_coefficient": 1e-5,
                }
            }
        },
    }

    # ── Actualizar potencia por cargador en cada edificio ─────────────────────
    bldg_names = list(schema['buildings'].keys())  # Building_1 ... Building_17

    for bldg_id, charger_list in CHARGER_CFG.items():
        bldg_key = f"Building_{bldg_id}"
        if bldg_key not in schema['buildings']:
            log.warning(f"  {bldg_key} no encontrado en schema")
            continue

        chargers_dict = schema['buildings'][bldg_key].get('chargers', {})
        for ci, cfg in enumerate(charger_list):
            ckey = f"charger_{bldg_id}_{ci+1}"
            if ckey not in chargers_dict:
                log.warning(f"  {ckey} no encontrado en schema")
                continue

            kw = cfg['charger_kw']
            is_moto = (kw <= 1.0)
            # min_charging_power: ~10% para mototaxi, ~13% (0.96kW) para camioneta L2
            min_kw = round(kw * 0.10, 2) if is_moto else 0.96

            chargers_dict[ckey]['attributes']['nominal_power']      = kw
            chargers_dict[ckey]['attributes']['max_charging_power']  = kw
            chargers_dict[ckey]['attributes']['min_charging_power']  = min_kw

        schema['buildings'][bldg_key]['chargers'] = chargers_dict

    schema_path.write_text(json.dumps(schema, indent=2, ensure_ascii=False), encoding='utf-8')
    log.info(f"  schema.json actualizado: EV defs Iquitos + {_total} charger powers")


# ─── Pipeline principal ───────────────────────────────────────────────────────

def main():
    log.info("=" * 70)
    log.info("generate_chargers.py v2.0 — EVs reales Iquitos: mototaxi + camioneta")
    log.info("=" * 70)
    log.info(f"  Total horas dataset: {N} | Edificios: {len(CHARGER_CFG)}")
    log.info(f"  Tipos EV: {list(EV_TYPES.keys())}")
    log.info("")

    total_s1 = total_s2 = total_sessions = 0

    for bldg_id, charger_list in CHARGER_CFG.items():
        n = len(charger_list)
        kws = [c['charger_kw'] for c in charger_list]
        labels = [c.get('ev_label', '?') for c in charger_list]
        log.info(f"  B{bldg_id} ({n} cargadores @ {kws} kW | {labels}):")

        for ci, cfg in enumerate(charger_list):
            charger_idx = ci
            df = generate_charger_csv(bldg_id, charger_idx, cfg)

            errs = validate_charger(df, f"charger_{bldg_id}_{ci+1}.csv")
            s1 = (df['electric_vehicle_charger_state'] == 1).sum()
            s2 = (df['electric_vehicle_charger_state'] == 2).sum()
            sessions = df.loc[df['electric_vehicle_charger_state'] == 1,
                              'electric_vehicle_id'].nunique()
            req_s = df.loc[df['electric_vehicle_charger_state'] == 1,
                           'electric_vehicle_required_soc_departure'].dropna()
            soc_mean = req_s.mean() if len(req_s) else float('nan')

            status = "OK" if not errs else "ERR:" + ",".join(errs)
            log.info(f"    charger_{bldg_id}_{ci+1}.csv [{cfg['ev_label']} {cfg['charger_kw']}kW]: "
                     f"state1={s1}h ({s1/N*100:.1f}%) | state2={s2}h ({s2/N*100:.1f}%) | "
                     f"sessions={sessions} | soc_req={soc_mean:.1f}% | {status}")

            # Guardar CSV
            fpath = DATASET_DIR / f"charger_{bldg_id}_{ci+1}.csv"
            df.to_csv(fpath, index=False)

            total_s1 += s1
            total_s2 += s2
            total_sessions += sessions

    log.info("")
    log.info("=" * 70)
    log.info(f"  Archivos generados     : {_total}")
    log.info(f"  Total horas state=1    : {total_s1:,} ({total_s1/N/50*100:.1f}% avg por cargador)")
    log.info(f"  Total horas state=2    : {total_s2:,} ({total_s2/N/50*100:.1f}% avg por cargador)")
    log.info(f"  Total sesiones EV      : {total_sessions:,}")
    log.info("")
    log.info("  Actualizando schema.json...")
    update_schema(DATASET_DIR / "schema.json")
    log.info("=" * 70)


if __name__ == "__main__":
    main()
