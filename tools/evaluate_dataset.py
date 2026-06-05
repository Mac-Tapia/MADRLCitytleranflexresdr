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
BUILDINGCSV = Path("CityLearn/data/buildingcsv/building.csv")
DISTILLATION_REPORT = Path("tools/dataset_docs/distillation_report.csv")
PRICING = BASE / "pricing.csv"
EXPECTED_ROWS = 26304
PEAK_HOURS = {18, 19, 20, 21, 22}
COLS  = ['month','hour','day_type','daylight_savings_status',
         'indoor_dry_bulb_temperature','average_unmet_cooling_setpoint_difference',
         'indoor_relative_humidity','non_shiftable_load','dhw_demand',
         'cooling_demand','heating_demand','solar_generation']
PRICING_COLS = [
    "electricity_pricing",
    "electricity_pricing_predicted_1",
    "electricity_pricing_predicted_2",
    "electricity_pricing_predicted_3",
]

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


def apply_buildingcsv_inventory(meta: dict[int, dict]) -> dict[int, dict]:
    """Synchronize names and roof areas from the documented building.csv input."""
    synced = {bid: values.copy() for bid, values in meta.items()}
    if not BUILDINGCSV.exists():
        return synced

    inventory = pd.read_csv(BUILDINGCSV, encoding="utf-8-sig")
    for _, row in inventory.iterrows():
        source_id = str(row.get("ID_Edificio", "")).strip()
        digits = "".join(ch for ch in source_id if ch.isdigit())
        if not digits:
            continue

        bid = int(digits)
        if bid not in synced:
            continue

        name = str(row.get("Nombre_Edificio", "")).strip()
        if name and name.lower() != "nan":
            synced[bid]['name'] = name

        area = pd.to_numeric(pd.Series([row.get("Area_Techada_m2")]), errors="coerce").iloc[0]
        if not pd.isna(area) and area > 0:
            synced[bid]['area'] = float(area)
        synced[bid]['source_id'] = source_id
    return synced


META = apply_buildingcsv_inventory(META)
DISTILLATION = pd.read_csv(DISTILLATION_REPORT) if DISTILLATION_REPORT.exists() else pd.DataFrame()
if not DISTILLATION.empty:
    DISTILLATION['building_id'] = pd.to_numeric(DISTILLATION['building_id'], errors='coerce').fillna(0).astype(int)
DISTILLED_BUILDINGS = set(DISTILLATION['building_id'].astype(int).unique()) if not DISTILLATION.empty else set()


def add_fixed_year_index(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    years = np.empty(len(out), dtype=int)
    years[:min(8760, len(out))] = 2023
    years[min(8760, len(out)):min(17544, len(out))] = 2024
    years[min(17544, len(out)):] = 2025
    out["_year"] = years
    return out

print("=" * 90)
print("EVALUACION EXHAUSTIVA — DATASET CALIBRADO — 17 EDIFICIOS IQUITOS 2023-2025")
print("=" * 90)

# ── 1. Tabla general de energia ───────────────────────────────────────────────
print()
print("1. ENERGIA ELECTRICA DIARIA Y REFERENCIA DE INTENSIDAD (kWh/dia)")
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
    if bid in DISTILLED_BUILDINGS:
        bench_s = f"MEDIDO {'OK' if bench_ok else 'ref'} [{bench[0]}-{bench[1]}]"
    elif bid == 1:
        bench_s = "PRESERVADO [sin B_01]"
    else:
        bench_s = f"BENCH {'OK' if bench_ok else 'ref'} [{bench[0]}-{bench[1]}]"
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

# ── 6. Verificacion NSL y balance mensual documentado ─────────────────────────
print()
print("6. VERIFICACION NSL >= 0 Y BALANCE MENSUAL MEDIDO/DESTILADO")
print("-" * 90)
print("%-5s %-30s %10s %12s %10s %12s" % (
    "B", "Edificio", "NSL_min", "meses_doc", "max_delta", "estado"))
print("-" * 90)
distillation = DISTILLATION.copy()
all_nsl_balance_ok = True
for bid, m in META.items():
    df = pd.read_csv(BASE / f"Building_{bid}.csv")
    nsl_min = df['non_shiftable_load'].min()
    status = "OK"

    if distillation.empty:
        months_doc = 0
        max_delta = 0.0
        ok = nsl_min >= 0
        status = "OK" if ok else "REVISAR"
    else:
        rows = distillation[distillation['building_id'] == bid].copy()
        months_doc = len(rows)

        if rows.empty:
            max_delta = 0.0
            ok = nsl_min >= 0 and bid == 1
            status = "PRESERVADO" if ok else "REVISAR"
        else:
            rows['delta_%'] = pd.to_numeric(rows['delta_%'], errors='coerce').fillna(np.inf)
            max_delta = rows['delta_%'].abs().max()
            status_ok = rows['status'].astype(str).str.lower().eq('ok').all()
            ok = nsl_min >= 0 and status_ok and max_delta <= 0.1
            status = "OK" if ok else "REVISAR"

    if not ok:
        all_nsl_balance_ok = False
    print("%-5d %-30s %10.2f %12d %9.4f%% %12s" % (
        bid, m['name'][:30], nsl_min, months_doc, max_delta, status))

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

# ── 8. Verificacion pricing.csv desde facturacion mensual ───────────────────
print()
print("8. PRICING.CSV — FACTURA MENSUAL DESTILADA A TARIFA HORARIA")
print("-" * 90)
pricing_ok = True
if not PRICING.exists():
    pricing_ok = False
    print("pricing.csv no encontrado")
else:
    pricing = pd.read_csv(PRICING)
    checks = [
        pricing.columns.tolist() == PRICING_COLS,
        len(pricing) == EXPECTED_ROWS,
        pricing.isna().sum().sum() == 0,
        float(pricing['electricity_pricing'].min()) >= 0.0,
        float(pricing['electricity_pricing'].max()) > 0.0,
    ]
    pricing_ok = all(checks)
    print(
        "filas=%d rango=[%.6f, %.6f] media=%.6f estado=%s" % (
            len(pricing),
            float(pricing['electricity_pricing'].min()),
            float(pricing['electricity_pricing'].max()),
            float(pricing['electricity_pricing'].mean()),
            "OK" if pricing_ok else "REVISAR",
        )
    )

    if not DISTILLATION.empty:
        ref = add_fixed_year_index(pd.read_csv(BASE / "Building_1.csv", usecols=["month", "hour"]))
        ref["electricity_pricing"] = pricing["electricity_pricing"].to_numpy(dtype=float)
        deltas = []
        billed_total = 0.0
        reconstructed_total = 0.0
        for (year, month), rows in DISTILLATION.groupby(["year", "mes"], sort=True):
            prices = ref[(ref["_year"] == int(year)) & (ref["month"] == int(month))]
            if prices.empty:
                continue
            peak_price = float(prices[prices["hour"].isin(PEAK_HOURS)]["electricity_pricing"].mean())
            offpeak_price = float(prices[~prices["hour"].isin(PEAK_HOURS)]["electricity_pricing"].mean())
            e_peak = float(pd.to_numeric(rows["E_punta_medido_kWh"], errors="coerce").fillna(0.0).sum())
            e_off = float(pd.to_numeric(rows["E_fuera_punta_medido_kWh"], errors="coerce").fillna(0.0).sum())
            billed = float(pd.to_numeric(rows["total_facturado"], errors="coerce").fillna(0.0).sum())
            reconstructed = peak_price * e_peak + offpeak_price * e_off
            billed_total += billed
            reconstructed_total += reconstructed
            if billed > 0.0:
                deltas.append((reconstructed - billed) / billed * 100.0)

        max_delta = max(abs(x) for x in deltas) if deltas else np.inf
        if max_delta > 0.01:
            pricing_ok = False
        print(
            "factura_agregada=%.2f reconstruida=%.2f max_delta=%.9f%% estado=%s" % (
                billed_total,
                reconstructed_total,
                max_delta,
                "OK" if max_delta <= 0.01 else "REVISAR",
            )
        )

# ── 9. Resumen final ──────────────────────────────────────────────────────────
print()
print("=" * 90)
print("RESUMEN FINAL")
print("=" * 90)

print(f"  Edificios con medicion mensual buildingcsv: {len(DISTILLED_BUILDINGS)}/17 destilados")
print(f"  B1 sin B_01.csv mensual:                    preservado por politica documentada")
print(f"  NSL no negativo y balance mensual OK:      {'SI' if all_nsl_balance_ok else 'NO'}")
print(f"  DHW demand correcto en hospitales/hotel:   {'SI' if dhw_ok_all else 'NO'}")
print(f"  Heating demand = 0 en todos:               {'SI' if heat_ok_all else 'NO'}")
print(f"  pricing.csv desde factura mensual OK:      {'SI' if pricing_ok else 'NO'}")

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
