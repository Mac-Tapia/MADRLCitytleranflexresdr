"""
rebuild_per_building_profiles.py
=================================
Reconstruye los perfiles horarios de carga (NSL, CD, T_indoor, RH, unmet)
usando perfiles POR EDIFICIO (no por tipo genérico) basados en características
reales confirmadas por fuentes web en el plan de diseño.

Diferencias clave respecto al generador original:
  B1  ELOR: SCADA 24h + oficinas 08-17h (no perfil industrial genérico)
  B4  Tottus Oriente: abre 08:00, no 10:00 (es bodega, no mall)
  B7  UNAP Zungarococha: campus remoto 18km, fin de semana casi vacío
  B8  Escuela PNP: internado militar 24h (750 cadetes en dormitorios)
  B9  Complejo CNI: estadio 24 576 esp., eventos nocturnos vie-sab-dom
  B10 Gobierno Regional: cierra 15:00 exacto (confirmado regionloreto.gob.pe)
  B13 UNAP FACEN: clases nocturnas 18-21h (univ. peruana, común)
  B15 Colegio CNI: doble turno 07:15-12:45 y 13:00-18:30 (2 326 alumnos)
  B16 SIMA Iquitos: doble turno + piscina semi-olímpica + coliseo
  B17 Selva Amazonica Pedro Águila: talleres CNC Sab mañana + clases nocturnas adultos

Columnas que se recalculan (el resto se preserva del CSV existente):
  non_shiftable_load, cooling_demand,
  indoor_dry_bulb_temperature, indoor_relative_humidity,
  average_unmet_cooling_setpoint_difference

Columnas que se preservan (ya correctas):
  month, hour, day_type, daylight_savings_status,
  solar_generation, dhw_demand, heating_demand
"""

from __future__ import annotations
import math
import numpy as np
import pandas as pd
from pathlib import Path

BASE    = Path("CityLearn/data/datasets/citylearn_iquitos_2023_2025")
BACKUP  = Path("CityLearn/data/datasets/citylearn_iquitos_2023_2025_backup")
WEATHER = Path(".cache/weather")

# ─── Constantes de calibración (idénticas a calibrate_buildings.py) ────────────
CALIB = {
    1:  {'nsl_scale': 18.9,  'cd_scale': 1.0,   'dhw_scale': 1.0,   'nsl_floor':  17.7},
    2:  {'nsl_scale':  1.0,  'cd_scale': 1.0,   'dhw_scale': 1.0,   'nsl_floor':   3.76},
    3:  {'nsl_scale':  1.0,  'cd_scale': 1.0,   'dhw_scale': 1.0,   'nsl_floor':  55.3},
    4:  {'nsl_scale':  1.0,  'cd_scale': 1.0,   'dhw_scale': 1.0,   'nsl_floor':  14.8},
    5:  {'nsl_scale':  1.0,  'cd_scale': 1.0,   'dhw_scale': 1.0,   'nsl_floor':   5.4},
    6:  {'nsl_scale':  1.0,  'cd_scale': 1.0,   'dhw_scale': 1.0,   'nsl_floor':  78.5},
    7:  {'nsl_scale':  0.59, 'cd_scale': 0.59,  'dhw_scale': 1.0,   'nsl_floor':   9.5},
    8:  {'nsl_scale':  1.0,  'cd_scale': 1.0,   'dhw_scale': 1.0,   'nsl_floor':   6.9},
    9:  {'nsl_scale':  1.0,  'cd_scale': 1.0,   'dhw_scale': 1.0,   'nsl_floor':   2.18},
    10: {'nsl_scale':  4.70, 'cd_scale': 1.0,   'dhw_scale': 1.0,   'nsl_floor':  12.43},
    11: {'nsl_scale':  0.516,'cd_scale': 0.516, 'dhw_scale': 0.516, 'nsl_floor': 195.0},
    12: {'nsl_scale':  0.557,'cd_scale': 0.557, 'dhw_scale': 0.557, 'nsl_floor': 125.0},
    13: {'nsl_scale':  0.586,'cd_scale': 0.586, 'dhw_scale': 1.0,   'nsl_floor':   1.75},
    14: {'nsl_scale':  0.720,'cd_scale': 0.720, 'dhw_scale': 1.0,   'nsl_floor':  15.7},
    15: {'nsl_scale':  1.0,  'cd_scale': 1.0,   'dhw_scale': 1.0,   'nsl_floor':   2.76},
    16: {'nsl_scale':  1.0,  'cd_scale': 1.0,   'dhw_scale': 1.0,   'nsl_floor':   4.55},
    17: {'nsl_scale':  1.0,  'cd_scale': 1.0,   'dhw_scale': 1.0,   'nsl_floor':   4.2},
}

# ─── Parámetros por edificio ─────────────────────────────────────────────────────
BLDG_CFG = {
    1:  {'nsl_base': 17.7,  'cooling_peak': 126.86, 'cop': 2.8, 'setpoint': 24.0, 'tau': 4.0,
         'refrig': (0.0,  1.0)},
    2:  {'nsl_base': 3.76,  'cooling_peak': 29.0,   'cop': 2.5, 'setpoint': 26.0, 'tau': 2.0,
         'refrig': (0.0,  1.0)},
    3:  {'nsl_base': 55.3,  'cooling_peak': 67.0,   'cop': 3.0, 'setpoint': 24.0, 'tau': 2.0,
         'refrig': (30.0, 0.70)},
    4:  {'nsl_base': 14.8,  'cooling_peak': 29.5,   'cop': 3.0, 'setpoint': 23.0, 'tau': 3.0,
         'refrig': (12.0, 0.85)},
    5:  {'nsl_base': 5.4,   'cooling_peak': 150.5,  'cop': 3.0, 'setpoint': 23.0, 'tau': 4.0,
         'refrig': (18.0, 0.90)},
    6:  {'nsl_base': 78.5,  'cooling_peak': 850.0,  'cop': 3.0, 'setpoint': 23.0, 'tau': 3.0,
         'refrig': (515.0,0.85)},
    7:  {'nsl_base': 9.5,   'cooling_peak': 167.0,  'cop': 2.8, 'setpoint': 25.0, 'tau': 3.0,
         'refrig': (0.0,  1.0)},
    8:  {'nsl_base': 6.9,   'cooling_peak': 222.0,  'cop': 2.5, 'setpoint': 25.0, 'tau': 3.0,
         'refrig': (0.0,  1.0)},
    9:  {'nsl_base': 2.18,  'cooling_peak': 19.5,   'cop': 2.5, 'setpoint': 26.0, 'tau': 2.0,
         'refrig': (0.0,  1.0)},
    10: {'nsl_base': 12.43, 'cooling_peak': 117.5,  'cop': 2.8, 'setpoint': 24.0, 'tau': 3.5,
         'refrig': (0.0,  1.0)},
    11: {'nsl_base': 195.0, 'cooling_peak': 366.6,  'cop': 2.5, 'setpoint': 22.0, 'tau': 5.0,
         'refrig': (180.0,1.00)},
    12: {'nsl_base': 125.0, 'cooling_peak': 222.0,  'cop': 2.5, 'setpoint': 22.0, 'tau': 5.0,
         'refrig': (90.0, 1.00)},
    13: {'nsl_base': 1.75,  'cooling_peak': 62.5,   'cop': 2.8, 'setpoint': 25.0, 'tau': 3.0,
         'refrig': (0.0,  1.0)},
    14: {'nsl_base': 15.7,  'cooling_peak': 49.5,   'cop': 2.5, 'setpoint': 26.0, 'tau': 2.0,
         'refrig': (0.0,  1.0)},
    15: {'nsl_base': 2.76,  'cooling_peak': 48.0,   'cop': 2.5, 'setpoint': 25.0, 'tau': 2.5,
         'refrig': (0.0,  1.0)},
    16: {'nsl_base': 4.55,  'cooling_peak': 100.0,  'cop': 2.5, 'setpoint': 25.0, 'tau': 2.5,
         'refrig': (0.0,  1.0)},
    17: {'nsl_base': 4.2,   'cooling_peak': 93.0,   'cop': 2.5, 'setpoint': 25.0, 'tau': 2.5,
         'refrig': (0.0,  1.0)},
}

# ─── PERFILES POR EDIFICIO (24 factores horarios, 0-1) ───────────────────────────
# Cada valor es la fracción del pico de carga en esa hora
# Basados en los datos reales confirmados por fuentes web en el plan de diseño

BUILDING_PROFILES = {
    # B1 — Electro Oriente S.A. (Utility/Administrativo, 14,000 m², ~11 pisos/áreas)
    # Fuente: xentic.com.pe caso éxito ELOR — SCADA 24h, oficinas 08-17h L-V
    # Centro de control + data center: operativo 24h/365
    # Oficinas (11 áreas, 40 AC splits 36,000 BTU): 07:30-17:00 L-V
    # Seguridad exterior: 24h
    # H:  00    01    02    03    04    05    06    07    08    09    10    11
    1: [0.22, 0.20, 0.20, 0.20, 0.20, 0.22, 0.30, 0.62, 0.93, 0.97, 0.97, 0.94,
    #   12    13    14    15    16    17    18    19    20    21    22    23
        0.87, 0.92, 0.97, 0.93, 0.85, 0.45, 0.30, 0.25, 0.23, 0.22, 0.22, 0.22],

    # B2 — Municipalidad San Juan Bautista (Deportivo multidisciplinar, 8,000 m²)
    # Fuente: estimación tipo complejo deportivo Iquitos
    # Gimnasio: 06-22h; canchas: tarde; eventos: 15-22h
    # Fines de semana: principal actividad (eventos deportivos)
    # H:  00    01    02    03    04    05    06    07    08    09    10    11
    2: [0.08, 0.07, 0.07, 0.07, 0.07, 0.10, 0.22, 0.30, 0.35, 0.40, 0.44, 0.47,
    #   12    13    14    15    16    17    18    19    20    21    22    23
        0.48, 0.52, 0.60, 0.77, 0.90, 0.94, 0.97, 0.92, 0.77, 0.52, 0.22, 0.10],

    # B3 — Aeropuerto Francisco Secada Vignetta (Transporte 24h, 6,000 m²)
    # Fuente: Wikipedia aeropuerto IQT — vuelos: 05:30-20:00
    # Torre de control + FIDS + seguridad + iluminación: 24h
    # Vuelos pico mañana (05-09h) y tarde (13-19h), no hay vuelos overnight
    # H:  00    01    02    03    04    05    06    07    08    09    10    11
    3: [0.55, 0.50, 0.48, 0.48, 0.52, 0.85, 0.97, 0.92, 0.88, 0.85, 0.82, 0.80,
    #   12    13    14    15    16    17    18    19    20    21    22    23
        0.78, 0.85, 0.93, 0.97, 0.93, 0.88, 0.85, 0.75, 0.65, 0.60, 0.58, 0.55],

    # B4 — Tottus Oriente Precio UNO (Retail/Bodega, 2,500 m²)
    # Fuente: tiendeo.pe — hiperbodega GRAN SUPERFICIE abre 08:00 (no mall 10:00)
    # Refrigeración perecederos: 24h crítica
    # Apertura 08:00-22:00 (formato bodega, no centro comercial)
    # H:  00    01    02    03    04    05    06    07    08    09    10    11
    4: [0.22, 0.20, 0.20, 0.20, 0.20, 0.22, 0.28, 0.48, 0.88, 0.93, 0.92, 0.90,
    #   12    13    14    15    16    17    18    19    20    21    22    23
        0.88, 0.90, 0.92, 0.90, 0.90, 0.92, 0.93, 0.88, 0.82, 0.68, 0.35, 0.25],

    # B5 — Hotel El Dorado Plaza (Hotelero 5★, 65 habitaciones confirmadas, 24h)
    # Fuente: Expedia 2026 — 65 hab. + restaurant + piscina + business center
    # Restaurant picos: 07-10h desayuno, 12-15h almuerzo, 18-22h cena
    # Check-out: 07-12h; Check-in: 14-22h; Piscina: 07-19h
    # H:  00    01    02    03    04    05    06    07    08    09    10    11
    5: [0.58, 0.55, 0.52, 0.50, 0.52, 0.60, 0.70, 0.85, 0.90, 0.87, 0.83, 0.80,
    #   12    13    14    15    16    17    18    19    20    21    22    23
        0.80, 0.83, 0.87, 0.90, 0.93, 0.96, 0.98, 0.95, 0.88, 0.80, 0.72, 0.65],

    # B6 — Mall Aventura Iquitos (Mall 3 pisos, ~110 tiendas, 20,637 m² GLA)
    # Fuente: Wikipedia + mallaventura.pe — inaugurado 31 agosto 2023
    # Tottus: pre-abastecimiento 07-10h; apertura general 10-21h
    # SmartFit: 06-22h; Movie Time: pico 16-22h; Food court: 12-14h y 18-21h
    # H:  00    01    02    03    04    05    06    07    08    09    10    11
    6: [0.08, 0.07, 0.07, 0.07, 0.07, 0.08, 0.12, 0.20, 0.28, 0.42, 0.72, 0.88,
    #   12    13    14    15    16    17    18    19    20    21    22    23
        0.92, 0.90, 0.87, 0.90, 0.93, 0.95, 0.98, 0.92, 0.78, 0.55, 0.22, 0.10],

    # B7 — UNAP Zungarococha (Universitario/Forestal, 8,300 m², campus remoto 18km)
    # Fuente: unapiquitos.edu.pe — 5 facultades, CIEFOR, campus 18km de Iquitos
    # Clases: 08-13h y 14-18h; Labs especializados (microscopios, HPLC, incubadoras)
    # Campus REMOTO: fin de semana casi vacío (menor que universidad urbana)
    # H:  00    01    02    03    04    05    06    07    08    09    10    11
    7: [0.08, 0.07, 0.07, 0.07, 0.07, 0.10, 0.18, 0.52, 0.88, 0.93, 0.92, 0.90,
    #   12    13    14    15    16    17    18    19    20    21    22    23
        0.82, 0.90, 0.93, 0.88, 0.72, 0.48, 0.28, 0.17, 0.12, 0.10, 0.08, 0.08],

    # B8 — Escuela Técnica Superior PNP (INTERNADO MILITAR, 21,000 m², 750 cadetes)
    # Fuente: MININTER — inversión 40M soles, dormitorios 750 cadetes (320+320+80+80 oficiales)
    # PERFIL MUY DIFERENTE a escuela civil: 750 cadetes VIVEN en el campus
    # Horario militar: diana 05:30, desayuno 06:30-07:30, clases 07:30-12:00,
    #   almuerzo 12:00-14:00, clases/prácticas 14:00-18:00, cena 18:00-19:00,
    #   estudio 19:00-22:00, silencio 22:00 (dormitorios con cargadores/ilum. mínima)
    # H:  00    01    02    03    04    05    06    07    08    09    10    11
    8: [0.45, 0.42, 0.40, 0.40, 0.43, 0.68, 0.85, 0.96, 0.98, 0.97, 0.95, 0.90,
    #   12    13    14    15    16    17    18    19    20    21    22    23
        0.92, 0.88, 0.93, 0.90, 0.82, 0.88, 0.87, 0.80, 0.72, 0.65, 0.52, 0.47],

    # B9 — Complejo CNI (Estadio 24,576 espectadores + instalaciones)
    # Fuente: Wikipedia + fichajes.com — Estadio CNI 24,576 esp., Club CNI Iquitos
    # Partidos: principalmente vie-sab-dom 19:00-22:00
    # Base diaria muy baja (seguridad + mantenimiento + admin)
    # Pico fuerte solo en noches de partido (iluminación 70kW + sonido + marcador)
    # H:  00    01    02    03    04    05    06    07    08    09    10    11
    9: [0.05, 0.04, 0.04, 0.04, 0.04, 0.06, 0.08, 0.13, 0.20, 0.27, 0.32, 0.35,
    #   12    13    14    15    16    17    18    19    20    21    22    23
        0.35, 0.32, 0.40, 0.58, 0.83, 0.93, 0.97, 0.92, 0.78, 0.52, 0.18, 0.07],

    # B10 — Gobierno Regional Loreto (Administrativo, 5,000 m²)
    # Fuente: regionloreto.gob.pe — CONFIRMADO horario L-V 07:00-15:00
    # 5 gerencias regionales + data center 24h
    # CIERRE A LAS 15:00 (no 17:00 como admin genérico)
    # Caída brusca en hora 15 → solo servidores + seguridad
    # H:  00    01    02    03    04    05    06    07    08    09    10    11
    10:[0.13, 0.11, 0.11, 0.11, 0.11, 0.13, 0.18, 0.55, 0.92, 0.98, 0.98, 0.95,
    #   12    13    14    15    16    17    18    19    20    21    22    23
        0.88, 0.96, 0.98, 0.30, 0.17, 0.14, 0.13, 0.13, 0.13, 0.13, 0.13, 0.13],

    # B11 — Hospital Regional Loreto (Salud 24h, 6 pisos, 176 camas, 35 especialidades)
    # Fuente: hrloreto.gob.pe + Doctoralia — UCI 11 camas, 6 quirófanos, 35 especialidades
    # UCI/Emergencia/Quirófanos: 24h constante (crítico)
    # Consultorios externos: 08:00-17:00 (fuerte pico diurno)
    # H:  00    01    02    03    04    05    06    07    08    09    10    11
    11:[0.72, 0.70, 0.68, 0.68, 0.70, 0.72, 0.78, 0.85, 0.95, 0.98, 0.98, 0.96,
    #   12    13    14    15    16    17    18    19    20    21    22    23
        0.93, 0.93, 0.93, 0.90, 0.87, 0.85, 0.83, 0.80, 0.78, 0.75, 0.73, 0.72],

    # B12 — EsSalud Hospital III (Salud 24h, 11 camas UCI, 3 quirófanos, 600 consultas/día)
    # Fuente: essalud.gob.pe + EsSalud en línea — UCI 11 camas, 12 ventiladores
    # Más consulta-intensivo que B11 (600 consultas/día confirmadas)
    # H:  00    01    02    03    04    05    06    07    08    09    10    11
    12:[0.70, 0.68, 0.67, 0.67, 0.68, 0.70, 0.76, 0.83, 0.95, 0.98, 0.97, 0.95,
    #   12    13    14    15    16    17    18    19    20    21    22    23
        0.92, 0.92, 0.92, 0.88, 0.85, 0.83, 0.80, 0.78, 0.75, 0.72, 0.71, 0.70],

    # B13 — Facultad Economía y Negocios UNAP / FACEN (Universitario, 3,000 m², campus urbano)
    # Fuente: enlinea.unapiquitos.edu.pe — 5 escuelas (Adm, Cont, Econ, Neg.Int, Turismo)
    # CLASES NOCTURNAS 18-21h: muy común en universidades peruanas
    # Labs cómputo usados en 2 turnos (mañana + noche)
    # H:  00    01    02    03    04    05    06    07    08    09    10    11
    13:[0.08, 0.07, 0.07, 0.07, 0.07, 0.08, 0.15, 0.52, 0.87, 0.93, 0.92, 0.90,
    #   12    13    14    15    16    17    18    19    20    21    22    23
        0.82, 0.88, 0.93, 0.90, 0.80, 0.87, 0.93, 0.88, 0.68, 0.38, 0.17, 0.09],

    # B14 — Terminal Portuario ENAPU (Portuario 24h, 5,000 m²)
    # Fuente: enapu.com.pe — muelles 2, almacenes 3, terminal pasajeros, grúa 22t
    # Botes Amazon: arribo pico 06-08h (madrugada) y 16-18h (tardía)
    # Almacenes: seguridad 24h; Terminal pasajeros: horario de botes
    # H:  00    01    02    03    04    05    06    07    08    09    10    11
    14:[0.55, 0.50, 0.48, 0.45, 0.48, 0.72, 0.95, 0.98, 0.93, 0.85, 0.80, 0.78,
    #   12    13    14    15    16    17    18    19    20    21    22    23
        0.75, 0.78, 0.85, 0.95, 0.97, 0.88, 0.75, 0.65, 0.60, 0.58, 0.57, 0.55],

    # B15 — Colegio Nacional de Iquitos CNI (Educación, 2,500 m², 2,326 alumnos)
    # Fuente: MINEDU Identicole + guiadecolegios.info — 2326 alumnos, 70 secciones
    # DOBLE TURNO confirmado: mañana 07:15-12:45 y tarde 13:00-18:30
    # Carga distribuida 07:00-19:00 (ambos turnos, no solo mañana)
    # Talleres cocina/arte/música: principalmente turno mañana
    # H:  00    01    02    03    04    05    06    07    08    09    10    11
    15:[0.05, 0.04, 0.04, 0.04, 0.04, 0.06, 0.13, 0.85, 0.97, 0.98, 0.96, 0.93,
    #   12    13    14    15    16    17    18    19    20    21    22    23
        0.93, 0.95, 0.97, 0.93, 0.87, 0.72, 0.22, 0.10, 0.07, 0.06, 0.05, 0.05],

    # B16 — SIMA Iquitos (Educación emblemática, 6,500 m²)
    # Fuente: iesanjuan.edu.pe + MINEDU Identicole — piscina semi-olímpica, coliseo, bib. tipo III
    # DOBLE TURNO como B15; más grande y con instalaciones especiales
    # Piscina: bomba recirculación 24h (baja potencia nocturna); Coliseo: eventos eventuales
    # Comedor escolar: 11:00-13:00 (cambio de turno)
    # H:  00    01    02    03    04    05    06    07    08    09    10    11
    16:[0.06, 0.05, 0.05, 0.05, 0.05, 0.08, 0.15, 0.87, 0.98, 0.98, 0.95, 0.93,
    #   12    13    14    15    16    17    18    19    20    21    22    23
        0.93, 0.95, 0.97, 0.93, 0.83, 0.72, 0.25, 0.12, 0.08, 0.07, 0.06, 0.06],

    # B17 — Asociacion Civil Selva Amazonica (Laboratorio 24h, 1 611 m²)
    # Fuente: logrosperu.com + deperu.com — Laboratorio biomedico, ultracongeladores -80C,
    #   Construcción Civil, Agropecuaria, Contabilidad, Secretariado
    # SÁBADOS CON CLASES: institutos técnicos en Perú frecuentemente tienen clases Sab
    # CLASES NOCTURNAS para adultos trabajadores: Contabilidad + Secretariado 18:00-22:00
    # Talleres CNC/mecánica pico 09-12h (torno CNC 15kW + fresadora 10kW)
    # H:  00    01    02    03    04    05    06    07    08    09    10    11
    17:[0.05, 0.04, 0.04, 0.04, 0.04, 0.07, 0.15, 0.65, 0.92, 0.97, 0.95, 0.92,
    #   12    13    14    15    16    17    18    19    20    21    22    23
        0.83, 0.88, 0.92, 0.88, 0.75, 0.80, 0.90, 0.87, 0.72, 0.35, 0.12, 0.06],
}

# ─── FACTORES DÍA DE SEMANA POR EDIFICIO (L-V, Sábado, Domingo) ─────────────────
# Basados en el tipo de operación real de cada edificio

BUILDING_DAY_FACTORS = {
    # B1 ELOR: L-V oficinas plenas, Sab reducido (SCADA siempre activo), Dom mínimo
    1:  (1.0, 0.38, 0.22),
    # B2 Municipalidad San Juan Bautista: fines de semana son sus días de mayor actividad (deportes/eventos)
    2:  (0.70, 1.55, 1.38),
    # B3 Aeropuerto: fines de semana ligeramente más turistas (Amazon)
    3:  (1.0, 1.10, 1.05),
    # B4 Tottus Oriente: fines de semana +afluencia familiar
    4:  (1.0, 1.05, 1.02),
    # B5 Hotel: fines de semana +turismo (Amazon lodge, ecoturismo)
    5:  (1.0, 1.18, 1.22),
    # B6 Mall: fines de semana principal día de compras en Iquitos
    6:  (1.0, 1.07, 1.05),
    # B7 UNAP Zungarococha: campus REMOTO 18km → fines de semana casi vacío
    7:  (1.0, 0.12, 0.04),
    # B8 PNP Militar: cadetes SIEMPRE en campus; Sab/Dom sin clases pero con actividades
    8:  (1.0, 0.90, 0.78),
    # B9 Estadio CNI: fines de semana = días de partido (principales)
    9:  (0.55, 1.65, 1.48),
    # B10 Gobierno Regional: CIERRA Sab/Dom (solo servidores en funcionamiento)
    10: (1.0, 0.07, 0.03),
    # B11 Hospital Regional: Sab/Dom menor actividad (consultorios cierran, UCI 24h)
    11: (1.0, 0.93, 0.88),
    # B12 EsSalud: similar B11
    12: (1.0, 0.90, 0.85),
    # B13 UNAP FACEN: clases Sab AM es común en Perú, Dom casi nada
    13: (1.0, 0.38, 0.05),
    # B14 ENAPU: río Amazon activo sábados, menos domingo
    14: (1.0, 0.72, 0.52),
    # B15 Colegio CNI: cerrado fines de semana (institución educativa pública)
    15: (1.0, 0.05, 0.02),
    # B16 SIMA Iquitos: cerrado fines de semana (bomba piscina ciclo nocturno bajo)
    16: (1.0, 0.08, 0.03),
    # B17 Selva Amazonica: SÁBADOS con clases técnicas (38-50% del día laboral), Dom cerrado
    17: (1.0, 0.48, 0.05),
}

# ─── Horas de ocupación por edificio (para cálculo de unmet cooling) ─────────────
BUILDING_OCCUPANCY = {
    1:  (7, 18),   # ELOR: oficinas 07-18h (con personal de guardia)
    2:  (6, 23),   # Municipalidad San Juan Bautista: deportes 06-23h
    3:  (0, 24),   # Aeropuerto: 24h
    4:  (8, 22),   # Tottus Oriente: apertura 08-22h
    5:  (0, 24),   # Hotel: 24h
    6:  (9, 22),   # Mall: 09-22h (Tottus pre-stock desde 07h)
    7:  (7, 19),   # UNAP Zungar: 07-19h
    8:  (0, 24),   # PNP Militar: 24h (cadetes)
    9:  (7, 23),   # Estadio CNI: 07-23h (entrenamiento + eventos)
    10: (7, 15),   # Gobierno: 07-15h EXACTO (confirmado)
    11: (0, 24),   # Hospital Regional: 24h
    12: (0, 24),   # EsSalud: 24h
    13: (7, 22),   # UNAP FACEN: 07-22h (clases nocturnas hasta 21h)
    14: (0, 24),   # ENAPU: 24h (terminal portuario)
    15: (7, 19),   # Colegio CNI: doble turno 07:15-18:30 → 07-19h
    16: (7, 19),   # SIMA Iquitos: doble turno 07-19h
    17: (0, 24),   # Selva Amazonica: laboratorio 24h continuo
}

NAMES = {
    1:'Electro Oriente S.A.', 2:'Municipalidad San Juan Bautista', 3:'Aeropuerto IQT',
    4:'Tottus Oriente Precio UNO', 5:'Hotel El Dorado Plaza', 6:'Mall Aventura Iquitos',
    7:'UNAP Zungarococha', 8:'Escuela Tecnica PNP', 9:'Complejo CNI',
    10:'Gobierno Regional', 11:'Hospital Regional', 12:'EsSalud Hospital III',
    13:'Fac. Economia UNAP', 14:'Terminal ENAPU', 15:'Colegio CNI',
    16:'SIMA Iquitos', 17:'Asociacion Civil Selva Amazonica',
}

def load_weather() -> pd.DataFrame:
    """Carga datos meteorológicos desde caché NASA POWER."""
    frames = []
    for year in [2023, 2024, 2025]:
        p = WEATHER / f"{year}.parquet"
        df = pd.read_parquet(p)
        frames.append(df)
    return pd.concat(frames)

def build_cooling_frac(bldg_id: int, index: pd.DatetimeIndex) -> np.ndarray:
    """Fracción de operación del AC: perfil_horario × factor_dia_semana."""
    prof = np.array(BUILDING_PROFILES[bldg_id])
    wf, sf, uf = BUILDING_DAY_FACTORS[bldg_id]
    h   = index.hour.values
    dow = index.dayofweek.values  # 0=Lun...6=Dom
    hour_fac = prof[h]
    day_fac  = np.where(dow < 5, wf, np.where(dow == 5, sf, uf))
    return np.clip(hour_fac * day_fac, 0.0, 1.0)

def build_nsl(bldg_id: int, index: pd.DatetimeIndex,
              cooling_frac: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Non-shiftable load [kWh/h] antes de calibración."""
    cfg = BLDG_CFG[bldg_id]
    h   = index.hour.values
    base = cfg['nsl_base']
    # Estimación de equipos operativos proporcional al cooling_peak
    equip_peak = max(0.0, base + cfg['cooling_peak'] * 0.25 + 5.0 - base)
    refrig_kw, factor_noc = cfg['refrig']
    equip  = equip_peak * cooling_frac
    refrig = np.where(h < 6, refrig_kw * factor_noc, refrig_kw)
    noise  = rng.normal(1.0, 0.02, len(index))
    return np.clip((base + equip + refrig) * noise, 0.0, None)

def build_cooling_demand(bldg_id: int, cooling_frac: np.ndarray) -> np.ndarray:
    """Cooling demand [kWh_thermal/h] antes de calibración."""
    cfg = BLDG_CFG[bldg_id]
    return np.clip(cfg['cooling_peak'] * cfg['cop'] * cooling_frac, 0.0, None)

def build_indoor_temp(bldg_id: int, weather_df: pd.DataFrame,
                      cooling_frac: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Temperatura interior por modelo RC primer orden."""
    cfg   = BLDG_CFG[bldg_id]
    T_out = weather_df['T2M'].values
    T_set = cfg['setpoint']
    tau   = cfg['tau']
    T_in  = np.empty(len(T_out))
    T_in[0] = T_set
    for i in range(1, len(T_in)):
        tau_eff = (tau / 4.0) if cooling_frac[i] > 0.05 else tau
        alpha   = math.exp(-1.0 / tau_eff)
        target  = T_set if cooling_frac[i] > 0.05 else T_out[i]
        T_in[i] = alpha * T_in[i-1] + (1.0 - alpha) * target
    noise = rng.normal(0, 0.3, len(T_in))
    return np.clip(T_in + noise, 14.0, 45.0)

def build_indoor_rh(bldg_id: int, weather_df: pd.DataFrame,
                    cooling_frac: np.ndarray) -> np.ndarray:
    """Humedad relativa interior."""
    RH_out = weather_df['RH2M'].values
    return np.clip(RH_out * (1.0 - 0.35 * cooling_frac), 30.0, 98.0)

def build_unmet_cooling(T_indoor: np.ndarray, bldg_id: int,
                        index: pd.DatetimeIndex) -> np.ndarray:
    """Diferencia media del setpoint no satisfecho (>0 = calor)."""
    cfg = BLDG_CFG[bldg_id]
    T_set = cfg['setpoint']
    occ_start, occ_end = BUILDING_OCCUPANCY[bldg_id]
    h = index.hour.values
    if occ_end == 24:
        occ = np.ones(len(index), dtype=float)
    else:
        occ = np.where((h >= occ_start) & (h < occ_end), 1.0, 0.0)
    return np.maximum(0.0, T_indoor - T_set) * occ

def apply_calib_and_floor(bldg_id: int, nsl: np.ndarray,
                           cd: np.ndarray, dhw: np.ndarray):
    """Aplica escala de calibración y floor del NSL."""
    c = CALIB[bldg_id]
    nsl_new = (nsl * c['nsl_scale']).clip(lower=c['nsl_floor'])
    cd_new  = (cd  * c['cd_scale']).clip(lower=0.0)
    dhw_new = (dhw * c['dhw_scale']).clip(lower=0.0)
    return nsl_new, cd_new, dhw_new


# ─── EJECUCIÓN PRINCIPAL ─────────────────────────────────────────────────────────

print("=" * 90)
print("REBUILD DE PERFILES POR EDIFICIO — Dataset Iquitos 2023-2025")
print("=" * 90)
print()
print("Perfiles por edificio (no genéricos por tipo):")
print("  B8  Escuela PNP → internado militar 24h (750 cadetes en dormitorios)")
print("  B9  Complejo CNI → estadio 24,576 esp., eventos nocturnos vie-sáb-dom")
print("  B10 Gobierno Regional → cierre exacto a las 15:00 (L-V 07:00-15:00)")
print("  B13 UNAP FACEN → clases nocturnas 18-21h (univ. peruana)")
print("  B15 Colegio CNI → doble turno 07:15-12:45 y 13:00-18:30")
print("  B16 SIMA Iquitos → doble turno + piscina + coliseo deportivo")
print("  B17 Selva Amazonica → talleres CNC sábado + clases nocturnas adultos")
print("  B4  Tottus Oriente → abre 08:00 (bodega, no mall desde 10:00)")
print("  B7  UNAP Zungarococha → campus remoto 18km, fin de semana casi vacío")
print()

# Cargar weather
print("Cargando datos meteorológicos desde caché NASA POWER...")
weather_df = load_weather()
index = weather_df.index
print(f"  {len(index)} pasos temporales | {index[0]} → {index[-1]}")
print()

print("-" * 90)
print(f"{'B':>3} {'Edificio':<28} {'NSL_media':>10} {'CD_media':>10} {'T_in':>7} {'RH':>6}  Estado")
print("-" * 90)

all_ok = True
for bid in range(1, 18):
    fpath = BASE / f"Building_{bid}.csv"
    # Leer CSV existente para preservar solar_generation, dhw_demand, heating_demand
    df_exist = pd.read_csv(fpath)

    rng = np.random.default_rng(bid)

    # Recalcular cooling_frac con perfil por edificio
    cooling_frac = build_cooling_frac(bid, index)

    # Recalcular NSL y CD (antes de calibración)
    nsl_raw = build_nsl(bid, index, cooling_frac, rng)
    cd_raw  = build_cooling_demand(bid, cooling_frac)

    # DHW del CSV existente (ya está calibrado o es 0)
    dhw_exist = df_exist['dhw_demand'].values

    # Aplicar calibración y floor
    nsl_cal, cd_cal, dhw_cal = apply_calib_and_floor(
        bid, nsl_raw, cd_raw, dhw_exist
    )

    # Recalcular temperatura interior con nuevo cooling_frac
    T_in   = build_indoor_temp(bid, weather_df, cooling_frac, rng)
    RH_in  = build_indoor_rh(bid, weather_df, cooling_frac)
    unmet  = build_unmet_cooling(T_in, bid, index)

    # Verificaciones básicas
    errs = []
    if nsl_cal.min() < 0:               errs.append('NSL<0')
    if nsl_cal.min() < CALIB[bid]['nsl_floor'] * 0.95:
        errs.append(f'NSL<floor')
    if cd_cal.min() < 0:                errs.append('CD<0')
    if np.any(np.isnan(nsl_cal)):       errs.append('NaN_NSL')
    if np.any(np.isnan(T_in)):          errs.append('NaN_T')
    if T_in.min() < 14 or T_in.max() > 46: errs.append('T_rango')
    if RH_in.min() < 20 or RH_in.max() > 100: errs.append('RH_rango')
    if errs:
        all_ok = False

    status = 'OK' if not errs else 'ERR:' + ','.join(errs)

    # Construir dataframe final (preservar solar, dhw, heating del original)
    df_new = pd.DataFrame({
        'month':                                      df_exist['month'].values,
        'hour':                                       df_exist['hour'].values,
        'day_type':                                   df_exist['day_type'].values,
        'daylight_savings_status':                    df_exist['daylight_savings_status'].values,
        'indoor_dry_bulb_temperature':                np.round(T_in, 3),
        'average_unmet_cooling_setpoint_difference':  np.round(unmet, 4),
        'indoor_relative_humidity':                   np.round(RH_in, 2),
        'non_shiftable_load':                         np.round(nsl_cal, 4),
        'dhw_demand':                                 np.round(dhw_cal, 4),
        'cooling_demand':                             np.round(cd_cal, 4),
        'heating_demand':                             df_exist['heating_demand'].values,
        'solar_generation':                           df_exist['solar_generation'].values,
    })

    df_new.to_csv(fpath, index=False)

    print(f"{bid:>3} {NAMES[bid][:28]:<28} {nsl_cal.mean():>10.1f} {cd_cal.mean():>10.1f} "
          f"{T_in.mean():>6.1f}C {RH_in.mean():>5.0f}%  {status}")

print("-" * 90)
print(f"  Perfiles por edificio aplicados: {'OK - todos' if all_ok else 'CON ERRORES'}")
print()

# Validación final con CityLearnEnv
print("=" * 90)
print("VALIDACIÓN CON CityLearnEnv")
print("=" * 90)
try:
    import sys
    sys.path.insert(0, str(Path("CityLearn")))
    from citylearn.citylearn import CityLearnEnv
    env = CityLearnEnv(schema=str(BASE / 'schema.json'))
    obs, _ = env.reset()
    print(f"  reset() OK — {len(obs)} agentes")
    for step in range(100):
        actions = [env.action_space[i].sample() for i in range(len(env.buildings))]
        obs, rew, done, trunc, info = env.step(actions)
        if done: break
    kpis = env.evaluate()
    print(f"  100 pasos OK — {len(kpis)} KPIs calculados")
    print()
    print("  DATASET LISTO — perfiles por edificio validados con CityLearnEnv")
except Exception as e:
    print(f"  ERROR CityLearnEnv: {e}")

print()
print("=" * 90)
print("COMPARATIVA DE PERFILES: tipo genérico → por edificio")
print("=" * 90)
cambios = [
    ("B4",  "mall genérico (abre 10h)", "hiperbodega: abre 08:00, Sab/Dom semejante"),
    ("B7",  "universitario (Sab=0.15, Dom=0.05)", "REMOTO 18km: Sab=0.12, Dom=0.04"),
    ("B8",  "educacion (07-16h, cerr. fds)", "INTERNADO MILITAR 24h: 750 cadetes siempre"),
    ("B9",  "deportivo (tarde 0.70)", "ESTADIO: eventos nocturnos vie-sáb-dom 19-22h"),
    ("B10", "administrativo (07-16h)", "GOBIERNO: cierre exacto 15:00 L-V"),
    ("B13", "universitario (solo mañana-tarde)", "FACEN: clases nocturnas 18-21h"),
    ("B15", "educacion (07-16h 1 turno)", "DOBLE TURNO: 07:15-12:45 y 13:00-18:30"),
    ("B16", "educacion (07-16h 1 turno)", "DOBLE TURNO + piscina + coliseo: 07-19h"),
    ("B17", "salud_24h (lab continuo)", "Selva Amazonica: ultracongeladores -80C operacion 24h"),
]
for edif, antes, despues in cambios:
    print(f"  {edif}: {antes}")
    print(f"       → {despues}")
print()
print("Algoritmos MADRL compatibles: HAPPO | MASAC | MATD3 | MAAC")
print("=" * 90)
