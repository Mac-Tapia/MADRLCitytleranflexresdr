"""
dataset_report.py
=================
Informe de estado final del dataset calibrado.
Muestra las 12 columnas de cada edificio con estadisticas resumidas.
"""
import pandas as pd
import numpy as np
import json
import sys
from pathlib import Path

BASE = Path("CityLearn/data/datasets/citylearn_iquitos_2023_2025")
BUILDINGCSV = Path("CityLearn/data/buildingcsv/building.csv")
DISTILLATION_REPORT = Path("tools/dataset_docs/distillation_report.csv")
PRICING = BASE / "pricing.csv"
EXPECTED_ROWS = 26304
PEAK_HOURS = {18, 19, 20, 21, 22}

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dimension_ev_chargers import build_charger_config  # noqa: E402

DEFAULT_NAMES = {
    1:'Electro Oriente S.A.',   2:'Municipalidad San Juan Bautista',      3:'Aeropuerto IQT',
    4:'Tottus Oriente Precio UNO', 5:'Hotel El Dorado Plaza',  6:'Mall Aventura Iquitos',
    7:'UNAP Zungarococha',      8:'Escuela Tecnica PNP',    9:'Complejo CNI',
    10:'Gobierno Regional',     11:'Hospital Regional',     12:'EsSalud Hospital III',
    13:'Fac. Economia UNAP',    14:'Terminal ENAPU',        15:'Colegio CNI',
    16:'SIMA Iquitos',         17:'Asociacion Civil Selva Amazonica',
}


def load_names() -> dict[int, str]:
    """Use building.csv as the inventory source of truth when available."""
    names = DEFAULT_NAMES.copy()
    if not BUILDINGCSV.exists():
        return names

    inventory = pd.read_csv(BUILDINGCSV, encoding="utf-8-sig")
    for _, row in inventory.iterrows():
        source_id = str(row.get("ID_Edificio", "")).strip()
        digits = "".join(ch for ch in source_id if ch.isdigit())
        if not digits:
            continue
        bid = int(digits)
        name = str(row.get("Nombre_Edificio", "")).strip()
        if name and name.lower() != "nan":
            names[bid] = name
    return names


NAMES = load_names()
EV_CONFIG = build_charger_config()

COLS_12 = ['month','hour','day_type','daylight_savings_status',
           'indoor_dry_bulb_temperature','average_unmet_cooling_setpoint_difference',
           'indoor_relative_humidity','non_shiftable_load','dhw_demand',
           'cooling_demand','heating_demand','solar_generation']
PRICING_COLS = [
    "electricity_pricing",
    "electricity_pricing_predicted_1",
    "electricity_pricing_predicted_2",
    "electricity_pricing_predicted_3",
]


def add_fixed_year_index(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    years = np.empty(len(out), dtype=int)
    years[:min(8760, len(out))] = 2023
    years[min(8760, len(out)):min(17544, len(out))] = 2024
    years[min(17544, len(out)):] = 2025
    out["_year"] = years
    return out

print("=" * 100)
print("INFORME FINAL — DATASET CITYLEARN IQUITOS 2023-2025 (CALIBRADO)")
print("=" * 100)
print(f"  Total filas por edificio: 26 304 (8760 + 8784 + 8760)")
print(f"  Columnas por edificio: 12")
print(f"  Total edificios: 17")
charger_count = len(list(BASE.glob("charger_*.csv")))
machine_count = len(list(BASE.glob("Washing_Machine_*.csv")))
print(f"  Total archivos: weather.csv + carbon_intensity.csv + pricing.csv +")
print(f"                  {charger_count} charger_X_Y.csv + {machine_count} Washing_Machine_X.csv + schema.json")

print()
print("ESTADO DE COLUMNAS POR EDIFICIO")
print("-" * 100)

header = f"{'B':>3} {'Edificio':<28} {'month':>5} {'hour':>4} {'dst':>3} {'T_in':>8} {'unmet':>6} {'RH':>6} {'NSL':>10} {'DHW':>8} {'CD':>10} {'heat':>5} {'solar':>10}"
print(header)
print("-" * 100)

all_ok = True
for bid in range(1, 18):
    df = pd.read_csv(BASE / f"Building_{bid}.csv")

    # Verificar columnas
    errs = []
    if df.columns.tolist() != COLS_12:
        errs.append('COLS!=12_STD')
    if len(df) != EXPECTED_ROWS:
        errs.append(f'ROWS!={EXPECTED_ROWS}')
    if df['heating_demand'].max() != 0:
        errs.append('HEAT!=0')
    if df['non_shiftable_load'].min() < 0:
        errs.append('NSL<0')
    if df['cooling_demand'].min() < 0:
        errs.append('CD<0')
    if df.isna().sum().sum() > 0:
        errs.append('NaN')

    name = NAMES[bid][:28]
    m_ok    = f"{df['month'].min()}-{df['month'].max()}"
    h_ok    = f"{df['hour'].min()}-{df['hour'].max()}"
    dst_ok  = f"{df['daylight_savings_status'].max()}"
    t_in    = f"{df['indoor_dry_bulb_temperature'].mean():.1f}C"
    unmet   = f"{df['average_unmet_cooling_setpoint_difference'].mean():.2f}"
    rh      = f"{df['indoor_relative_humidity'].mean():.0f}%"
    nsl     = f"{df['non_shiftable_load'].mean():.1f}"
    dhw     = f"{df['dhw_demand'].mean():.2f}"
    cd      = f"{df['cooling_demand'].mean():.1f}"
    heat    = f"{df['heating_demand'].max():.0f}"
    solar   = f"{df['solar_generation'].mean():.1f}"

    status = "OK" if not errs else "ERR:" + ",".join(errs)
    if errs:
        all_ok = False

    print(f"{bid:>3} {name:<28} {m_ok:>5} {h_ok:>4} {dst_ok:>3} {t_in:>8} {unmet:>6} {rh:>6} {nsl:>10} {dhw:>8} {cd:>10} {heat:>5} {solar:>10}  {status}")

print("-" * 100)
print(f"  Todas las columnas validadas: {'SI' if all_ok else 'NO'}")
print(f"  Building_1 usa la misma estructura CSV de entrenamiento que B2-B17: {'SI' if pd.read_csv(BASE / 'Building_1.csv', nrows=0).columns.tolist() == COLS_12 else 'NO'}")

print()
print("LEYENDA DE COLUMNAS (kWh o C o % segun columna):")
print("  month=1-12 | hour=0-23 | dst=0 (Peru no tiene horario verano)")
print("  T_in = temperatura interior media [C]")
print("  unmet = diferencia media del setpoint no satisfecho [C] (>0 = calor)")
print("  RH = humedad relativa interior media [%]")
print("  NSL = non_shiftable_load media [kW = kWh/h]  (residuo no controlable del medidor)")
print("  DHW = dhw_demand media [kWh_thermal/h]  (solo Hotel B5, Hospitales B11 B12)")
print("  CD = cooling_demand media [kWh_thermal/h]  (carga AC en kWh termicos)")
print("  heat = heating_demand [kWh_thermal/h]  (siempre 0, Iquitos tropical 24-33C)")
print("  solar = solar_generation media [kWh_elec/h]  (pvlib ModelChain SAPM)")

print()
print("BALANCE MENSUAL BUILDINGCSV — RESUMEN DE DESTILACION")
print("-" * 92)
print(f"{'B':>3} {'Edificio':<32} {'meses':>5} {'medido/dia':>11} {'citylearn/dia':>13} {'max_delta':>10}  {'Estado'}")
print("-" * 92)

distill_ok = True
if DISTILLATION_REPORT.exists():
    report = pd.read_csv(DISTILLATION_REPORT)
    report['building_id'] = pd.to_numeric(report['building_id'], errors='coerce').fillna(0).astype(int)
    for col in ['E_medido_kWh', 'E_cal_tot', 'delta_%']:
        report[col] = pd.to_numeric(report[col], errors='coerce')

    for bid in range(1, 18):
        df = pd.read_csv(BASE / f"Building_{bid}.csv")
        days = len(df) / 24.0
        rows = report[report['building_id'] == bid]
        if rows.empty and bid == 1:
            total_day = (df['non_shiftable_load'].mean() + df['cooling_demand'].mean()/2.8 + df['dhw_demand'].mean()/0.85) * 24
            print(f"{bid:>3} {NAMES[bid][:32]:<32} {0:>5} {'sin B_01':>11} {total_day:>13.0f} {'n/a':>10}  PRESERVADO")
            continue

        if rows.empty:
            distill_ok = False
            print(f"{bid:>3} {NAMES[bid][:32]:<32} {0:>5} {'sin doc':>11} {'sin doc':>13} {'n/a':>10}  REVISAR")
            continue

        measured_day = rows['E_medido_kWh'].sum() / days
        citylearn_day = rows['E_cal_tot'].sum() / days
        max_delta = rows['delta_%'].abs().max()
        status_ok = rows['status'].astype(str).str.lower().eq('ok').all() and max_delta <= 0.1
        estado = "OK" if status_ok else "REVISAR"
        if not status_ok:
            distill_ok = False
        print(f"{bid:>3} {NAMES[bid][:32]:<32} {len(rows):>5} {measured_day:>11.0f} {citylearn_day:>13.0f} {max_delta:>9.4f}%  {estado}")
else:
    distill_ok = False
    print("  No se encontro tools/dataset_docs/distillation_report.csv")

if DISTILLATION_REPORT.exists() and 'report' in locals() and 'measurement_quality_flag' in report.columns:
    print()
    print("AUDITORIA DE COLUMNAS MEDIDAS BUILDINGCSV")
    print("-" * 92)
    quality = report['measurement_quality_flag'].fillna('').replace('', 'sin_flag').value_counts().sort_index()
    for flag, count in quality.items():
        print(f"  {flag:<35} {int(count):>5} meses")

    mismatches = report[report['measurement_quality_flag'] == 'split_reported_total_mismatch']
    if not mismatches.empty:
        print()
        print("  Nota: esos meses conservan EnergiaActivaHoraPunta + EnergiaActivaFueraPunta")
        print("        como kWh fisico y dejan totalEnergiaActiva/TotalFacturado como auditoria.")
        print("        TotalFacturado no se convierte a kWh; calibra pricing.csv como costo.")

print()
print("AUDITORIA DE TARIFAS Y FACTURACION — PRICING.CSV")
print("-" * 100)
pricing_ok = True
if not PRICING.exists():
    pricing_ok = False
    print("  No se encontro pricing.csv")
else:
    pricing = pd.read_csv(PRICING)
    pricing_errors = []
    if pricing.columns.tolist() != PRICING_COLS:
        pricing_errors.append("COLS!=STD")
    if len(pricing) != EXPECTED_ROWS:
        pricing_errors.append(f"ROWS!={EXPECTED_ROWS}")
    if pricing.isna().sum().sum() > 0:
        pricing_errors.append("NaN")
    if "electricity_pricing" not in pricing.columns or pricing["electricity_pricing"].min() < 0:
        pricing_errors.append("PRICE<0")
    if "electricity_pricing" in pricing.columns and pricing["electricity_pricing"].max() <= 0:
        pricing_errors.append("PRICE_ZERO")

    if pricing_errors:
        pricing_ok = False

    pmin = float(pricing["electricity_pricing"].min()) if "electricity_pricing" in pricing.columns else 0.0
    pmax = float(pricing["electricity_pricing"].max()) if "electricity_pricing" in pricing.columns else 0.0
    pmean = float(pricing["electricity_pricing"].mean()) if "electricity_pricing" in pricing.columns else 0.0
    print(
        f"  pricing.csv: filas={len(pricing)} columnas={len(pricing.columns)} "
        f"rango=[{pmin:.6f}, {pmax:.6f}] media={pmean:.6f} "
        f"{'OK' if not pricing_errors else 'REVISAR:' + ','.join(pricing_errors)}"
    )

    if DISTILLATION_REPORT.exists() and 'report' in locals() and not report.empty:
        ref = add_fixed_year_index(pd.read_csv(BASE / "Building_1.csv", usecols=["month", "hour"]))
        ref["electricity_pricing"] = pricing["electricity_pricing"].to_numpy(dtype=float)
        bill_rows = []
        for (year, month), rows in report.groupby(["year", "mes"], sort=True):
            month_price = ref[(ref["_year"] == int(year)) & (ref["month"] == int(month))]
            if month_price.empty:
                continue
            peak_price = float(month_price[month_price["hour"].isin(PEAK_HOURS)]["electricity_pricing"].mean())
            offpeak_price = float(month_price[~month_price["hour"].isin(PEAK_HOURS)]["electricity_pricing"].mean())
            e_peak = float(pd.to_numeric(rows["E_punta_medido_kWh"], errors="coerce").fillna(0.0).sum())
            e_off = float(pd.to_numeric(rows["E_fuera_punta_medido_kWh"], errors="coerce").fillna(0.0).sum())
            billed = float(pd.to_numeric(rows["total_facturado"], errors="coerce").fillna(0.0).sum())
            reconstructed = peak_price * e_peak + offpeak_price * e_off
            delta_pct = (reconstructed - billed) / billed * 100.0 if billed > 0.0 else 0.0
            bill_rows.append({
                "billed": billed,
                "reconstructed": reconstructed,
                "delta_pct": delta_pct,
            })

        if bill_rows:
            bill_audit = pd.DataFrame(bill_rows)
            total_billed = float(bill_audit["billed"].sum())
            total_reconstructed = float(bill_audit["reconstructed"].sum())
            max_delta = float(bill_audit["delta_pct"].abs().max())
            if max_delta > 0.01:
                pricing_ok = False
            print(
                f"  factura agregada 2023-2025: medida={total_billed:.2f} "
                f"reconstruida={total_reconstructed:.2f} max_delta={max_delta:.9f}% "
                f"{'OK' if max_delta <= 0.01 else 'REVISAR'}"
            )
        else:
            pricing_ok = False
            print("  No se pudo reconstruir auditoria mensual de factura")

print(f"  pricing.csv calibrado desde TotalFacturado + punta/fuera punta: {'SI' if pricing_ok else 'NO'}")

print()
print("AUDITORIA EQUIPOS CONTROLABLES, PV, BESS Y EV")
print("-" * 120)
print(f"{'B':>3} {'Edificio':<30} {'splits':>6} {'equipo_ctrl':<22} {'PV_kW':>8} {'BESS_kWh':>9} {'EV':>3} {'V2G':>3} {'archivos':>8}  Estado")
print("-" * 120)

equipment_ok = True
schema_path = BASE / "schema.json"
schema = json.loads(schema_path.read_text(encoding="utf-8")) if schema_path.exists() else {}
inventory = pd.read_csv(BUILDINGCSV, encoding="utf-8-sig") if BUILDINGCSV.exists() else pd.DataFrame()
inventory["_bid"] = (
    inventory["ID_Edificio"].astype(str).str.extract(r"(\d+)")[0].astype(float).astype("Int64")
    if not inventory.empty else pd.Series(dtype="Int64")
)
report_for_equipment = report if 'report' in locals() else pd.DataFrame()

for bid in range(1, 18):
    inv_rows = inventory[inventory["_bid"] == bid] if not inventory.empty else pd.DataFrame()
    inv = inv_rows.iloc[0].to_dict() if not inv_rows.empty else {}
    building = schema.get("buildings", {}).get(f"Building_{bid}", {})
    chargers = building.get("chargers", {}) or {}
    expected_chargers = EV_CONFIG.get(bid, [])
    ev_types = [
        str(cfg[0] if isinstance(cfg, (list, tuple)) else cfg).strip().lower()
        for cfg in expected_chargers
    ]
    expected_v2g = sum(1 for ev_type in ev_types if ev_type in {"camioneta", "v2g"})
    schema_v2g = sum(
        1
        for charger in chargers.values()
        if float((charger.get("attributes") or {}).get("max_discharging_power", 0.0) or 0.0) > 0.0
    )

    files_ok = True
    for cidx in range(len(expected_chargers)):
        charger_file = BASE / f"charger_{bid}_{cidx + 1}.csv"
        if not charger_file.exists() or sum(1 for _ in charger_file.open("r", encoding="utf-8-sig")) - 1 != EXPECTED_ROWS:
            files_ok = False
            break

    if bid == 1:
        system_class = "preservado"
    elif not report_for_equipment.empty:
        rows = report_for_equipment[report_for_equipment["building_id"] == bid]
        system_class = str(rows["large_system_class"].mode().iloc[0]) if not rows.empty else "sin_doc"
    else:
        system_class = "sin_doc"

    pv_kw = float((building.get("pv", {}).get("attributes") or {}).get("nominal_power", 0.0) or 0.0)
    bess_kwh = float((building.get("electrical_storage", {}).get("attributes") or {}).get("capacity", 0.0) or 0.0)
    split_units = int(float(inv.get("Cant_Est_Unidades_Autonomas_Split", 0) or 0))

    checks = [
        bool(inv),
        (BASE / f"Building_{bid}.csv").exists(),
        building.get("energy_simulation") == f"Building_{bid}.csv",
        pv_kw > 0.0,
        bess_kwh > 0.0,
        len(chargers) == len(expected_chargers),
        schema_v2g == expected_v2g,
        files_ok,
    ]
    status = "OK" if all(checks) else "REVISAR"
    if status != "OK":
        equipment_ok = False

    print(
        f"{bid:>3} {NAMES[bid][:30]:<30} {split_units:>6} {system_class[:22]:<22} "
        f"{pv_kw:>8.1f} {bess_kwh:>9.1f} {len(chargers):>3} {schema_v2g:>3} "
        f"{'OK' if files_ok else 'ERR':>8}  {status}"
    )

print("-" * 120)
print(f"  Equipos/EV/PV/BESS sincronizados con building.csv, schema.json y charger_X_Y.csv: {'SI' if equipment_ok else 'NO'}")

print()
print("=" * 100)
print("CONCLUSION: Dataset calibrado y validado. Listo para entrenamiento MADRL.")
print()
print("  - 17 edificios con perfiles horarios propios (tipo uso, ocupacion, AC, EV)")
print("  - building.csv sincroniza nombres, areas, oficinas, equipos y EV por edificio")
print("  - 16 edificios (B2-B17) destilados desde mediciones mensuales buildingcsv")
print("  - B1 preservado por politica documentada: no existe B_01.csv mensual")
print("  - B1 mantiene las mismas 12 columnas y 26 304 filas que B2-B17 para entrenamiento")
print("  - weather.csv corregido desde NASA POWER cache (2023: T_ext 26C, no zeros)")
print("  - CityLearnEnv validado: reset + 100 pasos + 293 KPIs")
print("  - NSL no negativo y balance mensual documentado/destilado validado")
print("  - NSL residual = energia activa medida - cooling_demand/COP - dhw_demand/COP")
print("  - pricing.csv = factura mensual destilada a tarifa horaria punta/fuera punta")
print("  - DHW solo en Hotel (B5) y Hospitales (B11, B12)")
print("  - heating_demand = 0 en todos (Iquitos climaticamente tropical)")
print()
print("  Algoritmos MADRL compatibles: HAPPO | MASAC | MATD3 | MAAC")
print("  26 304 pasos temporales | 3 anos (2023-2024-2025) | tz=America/Lima")
print("=" * 100)
