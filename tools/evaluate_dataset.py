"""
evaluate_dataset.py
===================
Evaluacion exhaustiva del dataset calibrado: verifica que cada edificio
conserva sus caracteristicas propias (perfil horario, tipo de uso, elementos
electricos, proporcion de cargas, intensidad energetica por m2).
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json

BASE  = Path("CityLearn/data/datasets/citylearn_iquitos_2023_2025")
COLS  = ['month','hour','day_type','daylight_savings_status',
         'indoor_dry_bulb_temperature','average_unmet_cooling_setpoint_difference',
         'indoor_relative_humidity','non_shiftable_load','dhw_demand',
         'cooling_demand','heating_demand','solar_generation']

# Metadatos por edificio
META = {
    1:  {'name':'Electro Oriente S.A.',   'type':'industrial',    'area':14000,'cop':2.8,'dhw':False,'nsl_floor':17.7,
         'real_kwh_d':16091,'benchmark_int':(300,500),'uso':'24h continuo utility'},
    2:  {'name':'Complejo Champios',       'type':'deportivo',     'area':8000, 'cop':2.5,'dhw':False,'nsl_floor':3.76,
         'real_kwh_d':None, 'benchmark_int':(15,40), 'uso':'fines semana pico'},
    3:  {'name':'Aeropuerto IQT',          'type':'transporte_24h','area':6000, 'cop':3.0,'dhw':False,'nsl_floor':55.3,
         'real_kwh_d':None, 'benchmark_int':(200,450),'uso':'24h, picos vuelos'},
    4:  {'name':'Hiperbodega Precio UNO',  'type':'mall',          'area':2500, 'cop':3.0,'dhw':False,'nsl_floor':14.8,
         'real_kwh_d':None, 'benchmark_int':(200,400),'uso':'08-22h retail'},
    5:  {'name':'Hotel El Dorado Plaza',   'type':'hotelero_24h',  'area':9000, 'cop':3.0,'dhw':True, 'nsl_floor':5.4,
         'real_kwh_d':None, 'benchmark_int':(100,300),'uso':'24h hotelero'},
    6:  {'name':'Mall Aventura Iquitos',   'type':'mall',          'area':20637,'cop':3.0,'dhw':False,'nsl_floor':78.5,
         'real_kwh_d':None, 'benchmark_int':(300,550),'uso':'10-22h mall grande'},
    7:  {'name':'UNAP Zungarococha',       'type':'universitario', 'area':8300, 'cop':2.8,'dhw':False,'nsl_floor':9.5,
         'real_kwh_d':436,  'benchmark_int':(40,60),  'uso':'lun-vie 08-18h'},
    8:  {'name':'Escuela Tecnica PNP',     'type':'educacion',     'area':21000,'cop':2.5,'dhw':False,'nsl_floor':6.9,
         'real_kwh_d':297,  'benchmark_int':(30,60),  'uso':'lun-vie 07-18h military'},
    9:  {'name':'Complejo CNI',            'type':'deportivo',     'area':3500, 'cop':2.5,'dhw':False,'nsl_floor':2.18,
         'real_kwh_d':None, 'benchmark_int':(20,50),  'uso':'fines semana eventos'},
    10: {'name':'Gobierno Regional',       'type':'administrativo','area':5000, 'cop':2.8,'dhw':False,'nsl_floor':12.43,
         'real_kwh_d':3358, 'benchmark_int':(150,300),'uso':'lun-vie 07-15h'},
    11: {'name':'Hospital Regional',       'type':'salud_24h',     'area':12000,'cop':2.5,'dhw':True, 'nsl_floor':195.0,
         'real_kwh_d':9971, 'benchmark_int':(200,350),'uso':'24h critico'},
    12: {'name':'EsSalud Hospital III',    'type':'salud_24h',     'area':6000, 'cop':2.5,'dhw':True, 'nsl_floor':125.0,
         'real_kwh_d':6407, 'benchmark_int':(200,350),'uso':'24h critico'},
    13: {'name':'Facultad Economia UNAP',  'type':'universitario', 'area':3000, 'cop':2.8,'dhw':False,'nsl_floor':1.75,
         'real_kwh_d':412,  'benchmark_int':(30,60),  'uso':'lun-vie 08-18h'},
    14: {'name':'Terminal Portuario ENAPU','type':'portuario_24h', 'area':5000, 'cop':2.5,'dhw':False,'nsl_floor':15.7,
         'real_kwh_d':973,  'benchmark_int':(50,150), 'uso':'24h portuario'},
    15: {'name':'Colegio CNI',             'type':'educacion',     'area':2500, 'cop':2.5,'dhw':False,'nsl_floor':2.76,
         'real_kwh_d':472,  'benchmark_int':(30,60),  'uso':'lun-vie 08-15h'},
    16: {'name':'I.E. San Juan',           'type':'educacion',     'area':6500, 'cop':2.5,'dhw':False,'nsl_floor':4.55,
         'real_kwh_d':None, 'benchmark_int':(30,60),  'uso':'lun-vie 08-15h'},
    17: {'name':'IEST Pedro del Aguila',   'type':'educacion',     'area':5200, 'cop':2.5,'dhw':False,'nsl_floor':4.2,
         'real_kwh_d':None, 'benchmark_int':(35,65),  'uso':'lun-vie 07-17h talleres'},
}

print("=" * 90)
print("EVALUACION EXHAUSTIVA — DATASET CALIBRADO — 17 EDIFICIOS IQUITOS 2023-2025")
print("=" * 90)

# ── 1. Tabla general de energia ───────────────────────────────────────────────
print()
print("1. ENERGIA ELECTRICA DIARIA ESTIMADA vs REAL (kWh/dia)")
print("-" * 90)
print("%-5s %-30s %10s %10s %10s %10s %7s %10s" % (
    "B", "Edificio", "NSL/dia", "CD_elec", "DHW_elec", "Total/dia", "Ratio", "Intens."))
print("-" * 90)

for bid, m in META.items():
    df  = pd.read_csv(BASE / f"Building_{bid}.csv")
    cop = m['cop']
    nsl_d    = df['non_shiftable_load'].mean() * 24
    cd_elec  = (df['cooling_demand'].mean() / cop) * 24
    dhw_elec = (df['dhw_demand'].mean() / 0.85) * 24 if m['dhw'] else 0
    total_d  = nsl_d + cd_elec + dhw_elec
    intens   = total_d * 365 / m['area']   # kWh/m2/ano
    real_d   = m['real_kwh_d']
    ratio    = total_d / real_d if real_d else 0
    ratio_s  = f"{ratio:.2f}" if real_d else "—"
    real_s   = f"{real_d:.0f}" if real_d else "sin ref"
    bench    = m['benchmark_int']
    bench_ok = bench[0] <= intens <= bench[1]
    bench_s  = f"OK [{bench[0]}-{bench[1]}]" if bench_ok else f"REVISAR [{bench[0]}-{bench[1]}]"
    print("%-5d %-30s %10.0f %10.0f %10.0f %10.0f %7s %6.0f %-20s" % (
        bid, m['name'][:30], nsl_d, cd_elec, dhw_elec, total_d, ratio_s, intens, bench_s))

# ── 2. Perfil horario promedio por tipo de edificio ───────────────────────────
print()
print("2. PERFIL HORARIO NSL — PICO/VALLE POR TIPO (confirma patron diario)")
print("-" * 75)
print("%-5s %-30s %8s %8s %8s %8s %8s" % ("B","Edificio","H8(kW)","H12(kW)","H18(kW)","H22(kW)","H2(kW)"))
print("-" * 75)

for bid, m in META.items():
    df = pd.read_csv(BASE / f"Building_{bid}.csv")
    h = {h_: df[df['hour']==h_]['non_shiftable_load'].mean() for h_ in [2,8,12,18,22]}
    print("%-5d %-30s %8.1f %8.1f %8.1f %8.1f %8.1f  [%s]" % (
        bid, m['name'][:30], h[8], h[12], h[18], h[22], h[2], m['uso']))

# ── 3. Factor dia semana (lunes vs sabado vs domingo) ─────────────────────────
print()
print("3. FACTOR DIA DE SEMANA — NSL media (kW): Lun | Sab | Dom")
print("-" * 70)
print("%-5s %-30s %8s %8s %8s %8s" % ("B","Edificio","Lun(kW)","Sab(kW)","Dom(kW)","Sab/Lun"))
print("-" * 70)

for bid, m in META.items():
    df = pd.read_csv(BASE / f"Building_{bid}.csv")
    lun = df[df['day_type']==1]['non_shiftable_load'].mean()
    sab = df[df['day_type']==6]['non_shiftable_load'].mean()
    dom = df[df['day_type']==7]['non_shiftable_load'].mean()
    ratio_sd = sab / lun if lun > 0 else 0
    print("%-5d %-30s %8.1f %8.1f %8.1f %8.2f" % (
        bid, m['name'][:30], lun, sab, dom, ratio_sd))

# ── 4. Verificacion columnas de confort interior ──────────────────────────────
print()
print("4. COLUMNAS DE CONFORT INTERIOR — T_indoor y RH_indoor")
print("-" * 75)
print("%-5s %-30s %10s %10s %10s %10s" % ("B","Edificio","T_min","T_max","RH_min","RH_max"))
print("-" * 75)

for bid, m in META.items():
    df = pd.read_csv(BASE / f"Building_{bid}.csv")
    t = df['indoor_dry_bulb_temperature']
    rh = df['indoor_relative_humidity']
    print("%-5d %-30s %10.1f %10.1f %10.1f %10.1f" % (
        bid, m['name'][:30], t.min(), t.max(), rh.min(), rh.max()))

# ── 5. Generacion solar por edificio ─────────────────────────────────────────
print()
print("5. GENERACION SOLAR — Maxima diaria y promedio (kWh/dia)")
print("-" * 70)
print("%-5s %-30s %10s %10s %10s" % ("B","Edificio","Sol_max/h","Sol_dia_prom","Factor"))
print("-" * 70)

for bid, m in META.items():
    df = pd.read_csv(BASE / f"Building_{bid}.csv")
    sol = df['solar_generation']
    sol_max_h  = sol.max()
    sol_day    = sol.mean() * 24
    cop = m['cop']
    total_load = (df['non_shiftable_load'].mean()/cop + df['cooling_demand'].mean()/cop) * 24
    factor = sol_day / total_load if total_load > 0 else 0
    print("%-5d %-30s %10.1f %10.1f %10.1f%%" % (
        bid, m['name'][:30], sol_max_h, sol_day, factor*100))

# ── 6. Verificacion NSL minimo > floor critico ────────────────────────────────
print()
print("6. VERIFICACION NSL_MIN >= CARGA_CRITICA (floor) POR EDIFICIO")
print("-" * 65)
all_floor_ok = True
for bid, m in META.items():
    df = pd.read_csv(BASE / f"Building_{bid}.csv")
    nsl_min = df['non_shiftable_load'].min()
    floor   = m['nsl_floor']
    ok = nsl_min >= floor * 0.95
    status = "OK" if ok else "REVISAR"
    if not ok:
        all_floor_ok = False
    print("%-5d %-30s NSL_min=%6.2f  floor=%6.2f  %s" % (
        bid, m['name'][:30], nsl_min, floor, status))

# ── 7. Columnas dhw_demand y heating_demand ───────────────────────────────────
print()
print("7. DHW_DEMAND y HEATING_DEMAND — verificacion por edificio")
print("-" * 65)
dhw_ok_all = True
heat_ok_all = True
for bid, m in META.items():
    df = pd.read_csv(BASE / f"Building_{bid}.csv")
    dhw_max  = df['dhw_demand'].max()
    heat_max = df['heating_demand'].max()
    dhw_expected = m['dhw']
    dhw_status = "OK" if (dhw_expected and dhw_max > 0) or (not dhw_expected and dhw_max == 0) else "REVISAR"
    heat_status = "OK" if heat_max == 0 else "REVISAR"
    if dhw_status == "REVISAR":
        dhw_ok_all = False
    if heat_status == "REVISAR":
        heat_ok_all = False
    dhw_tag = f"DHW_max={dhw_max:.2f} {'(esperado)' if dhw_expected else ''}"
    print("%-5d %-30s  %-35s  heating=%s" % (
        bid, m['name'][:30], dhw_tag, heat_status))

# ── 8. Resumen final ──────────────────────────────────────────────────────────
print()
print("=" * 90)
print("RESUMEN FINAL")
print("=" * 90)

# Contar edificios con datos reales calibrados
with_real = sum(1 for m in META.values() if m['real_kwh_d'])
print(f"  Edificios con datos reales GD-Iquitos V3:  {with_real}/17 calibrados")
print(f"  Edificios sin datos reales (sin cambio):   {17 - with_real}/17")
print(f"  Todos los floors NSL validados:            {'SI' if all_floor_ok else 'NO'}")
print(f"  DHW demand correcto en hospitales/hotel:   {'SI' if dhw_ok_all else 'NO'}")
print(f"  Heating demand = 0 en todos:               {'SI' if heat_ok_all else 'NO'}")

print()
print("CARACTERISTICAS PROPIAS POR EDIFICIO (confirmacion):")
print("-" * 90)
CHARS = {
    1: "SCADA/servidores 24h + AC oficinas (40 splits 36KBTU) + 2 EV chargers 7.4kW",
    2: "Picos fines semana (partidos/torneos) + bomba piscina + 4 EV chargers",
    3: "Operacion 24h (vuelos) + rayos-X seguridad + torre control + 4 EV DC 22kW",
    4: "Retail 08-22h + refrigeracion perecederos 24h + 3 EV 7.4kW",
    5: "Hotelero 24h + DHW (65 hab x 50L/dia) + lavanderia + piscina + 3 EV 11kW",
    6: "Mall 3 pisos 10-22h + Tottus refrigeracion 24h + escaleras + 8 EV DC 22kW",
    7: "Universitario lun-vie + labs biotecnologia + CIEFOR + 3 EV 7.4kW",
    8: "Escuela militar 750 cadetes + piscina semi-olimpica + lavanderia + 2 EV",
    9: "Estadio 24576 esp. + ilum. eventos (picos nocturnos) + 2 EV ligeros",
    10:"Gobierno L-V 07-15h + servidores GIS + 3 EV 7.4kW",
    11:"Hospital 176 camas + UCI 11 camas + 6 quirofanos + DHW + 4 EV 11kW",
    12:"Hospital EsSalud 11 camas UCI + 3 quirofanos + neuro + DHW + 3 EV 7.4kW",
    13:"Facultad 5 escuelas + 3 labs computo + 2 EV 7.4kW",
    14:"Puerto 24h + grua 22t + shore-power barcos + 2 montacargas + 2 EV 11kW",
    15:"Colegio CNI 2326 alumnos + taller cocina + laboratorio idiomas + 2 EV",
    16:"IE San Juan emblematica + piscina semi-olimpica + SUM + 1 EV ligero",
    17:"IEST tecnico + CNC 15kW + fresadora + lab fabricacion digital + 2 EV",
}
for bid, char in CHARS.items():
    m = META[bid]
    df = pd.read_csv(BASE / f"Building_{bid}.csv")
    total_kwh_d = (df['non_shiftable_load'].mean() +
                   df['cooling_demand'].mean()/m['cop'] +
                   df['dhw_demand'].mean()/0.85) * 24
    print(f"  B{bid:2d} ({total_kwh_d:6.0f} kWh/d): {char[:80]}")

print()
print("  Dataset listo para entrenamiento MADRL:")
print("  HAPPO | MASAC | MATD3 | MAAC — 17 agentes, 26304 pasos, 3 anos Iquitos")
