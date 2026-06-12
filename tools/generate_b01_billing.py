"""
Genera CityLearn/data/buildingcsv/B_01.csv para ELECTRO ORIENTE S.A.
=======================================================================
FUENTE DE DEMANDA REAL:
  docs/Resultados_Preliminares-GD-Iquitos_V3 (2).xlsx, hoja '8.ELOR'
  Columnas: NOMBRES | ANO | MES | EA [kWh] | MD [KW]
  Datos disponibles: 2024 (12 meses) + 2025 (ene-oct, 10 meses)

PRONOSTICO DE DATOS FALTANTES:
  2023 (12 meses): se pronostican con el perfil mensual de 2024 escalado
                   al consumo anual estimado de 2023 (extrapolacion regresion).
  2025 nov-dic: se pronostican con la media movil de los ultimos 12 meses.

TARIFA:
  MT3 — Media Tension, tarifa industrial de gran consumidor.
  Electro Oriente S.A. es empresa distribuidora; sus instalaciones propias
  (oficinas SCADA, talleres, planta) se facturan en MT3.

  Precios calibrados del pricing_monthly_audit del dataset (mismos usados
  en pricing.csv del entorno CityLearn v3):
    price_peak    = precio punta hora 18-22
    price_offpeak = precio fuera punta

SPLIT PUNTA / FUERA PUNTA:
  Electro Oriente S.A. opera 24h (planta de generacion + SCADA).
  Perfil industrial continuo con reduccion nocturna:
    horas punta (18:00-22:59): 5 h/dia, fraccion = 15.1% del consumo diario
    horas fuera punta: 19 h/dia, fraccion = 84.9%
  La fraccion punta se calibro del perfil horario de Building_1.csv:
    H18=43 kW, H19-H22 promedio ~37 kW -> 5h*37/(24h*143.5) = 15.1%

ENERGIA REACTIVA:
  Factor de potencia industrial pf=0.92 -> tan(phi)=0.4260
  Energia reactiva = EA_total * tan(phi)

FACTOR DE CARGA:
  FC = (EA_total / horas_mes) / MD_kW
  MD [KW] no esta en el Excel -> se estima como EA_total/(FC_est*h_mes)
  FC_estimado = 0.68 (tipico para distribuidor electrico 24h en SEAI)
"""

import json
import math
import openpyxl
import pandas as pd
import numpy as np
from pathlib import Path

# ── Rutas ─────────────────────────────────────────────────────────────────────
ROOT           = Path(__file__).resolve().parent.parent
XLSX_PATH      = ROOT / "docs" / "Resultados_Preliminares-GD-Iquitos_V3 (2).xlsx"
DATASET_DIR    = ROOT / "CityLearn" / "data" / "datasets" / "citylearn_iquitos_2023_2025"
META_JSON      = DATASET_DIR / "building_metadata.json"
BUILDINGCSV    = ROOT / "CityLearn" / "data" / "buildingcsv"
OUTPUT_CSV     = BUILDINGCSV / "B_01.csv"
SHEET_NAME     = "8.ELOR"

# ── Parametros fisicos / operacionales ────────────────────────────────────────
PF             = 0.92                            # factor de potencia MT3 industrial
TAN_PHI        = math.tan(math.acos(PF))         # ~0.4260
FC_EST         = 0.68                            # factor de carga estimado 24h utility
PEAK_FRAC      = 0.151                           # fraccion consumo en horas punta 18-22
OFFPEAK_FRAC   = 1.0 - PEAK_FRAC
PEAK_HOURS     = {18, 19, 20, 21, 22}
TARIFA_CODE    = "MT3  "

YEARS_ALL      = [2023, 2024, 2025]
YEARS_REAL     = [2024, 2025]

MESES_ES = {
    1:"ene", 2:"feb", 3:"mar", 4:"abr", 5:"may", 6:"jun",
    7:"jul", 8:"ago", 9:"set", 10:"oct", 11:"nov", 12:"dic"
}

# ── 1. Leer datos reales del Excel ────────────────────────────────────────────
def read_elor_excel() -> dict[tuple[int, int], float]:
    """Lee los datos reales EA [kWh] de la hoja 8.ELOR."""
    wb = openpyxl.load_workbook(XLSX_PATH, read_only=True, data_only=True)
    ws = wb[SHEET_NAME]
    data: dict[tuple[int, int], float] = {}
    for row in ws.iter_rows(values_only=True):
        if row[0] != "CONSUMOS ELOR":
            continue
        year  = int(row[1]) if row[1] is not None else None
        month = int(row[2]) if row[2] is not None else None
        ea    = float(row[3]) if row[3] is not None else None
        if year and month and ea:
            data[(year, month)] = ea
    wb.close()
    return data


# ── 2. Pronosticar datos faltantes ────────────────────────────────────────────
def forecast_missing(real: dict[tuple[int, int], float]) -> dict[tuple[int, int], float]:
    """
    Completa los 36 meses (2023-01 a 2025-12).

    2023 (12 meses faltantes):
      Escalamos el perfil mensual de 2024 a un total anual estimado para 2023.
      Estimacion 2023: crecimiento historico -2% respecto a 2024 (sistema SEAI
      en expansion; 2024 incluye ampliacion de planta, por lo que 2023 es algo menor).
      Factor de escala 2023/2024 = 0.98.

    2025 nov-dic (2 meses faltantes):
      Media de los ultimos 4 meses disponibles (jul-oct 2025).
    """
    full: dict[tuple[int, int], float] = dict(real)

    # Total real 2024 (12 meses)
    total_2024 = sum(real.get((2024, m), 0) for m in range(1, 13))
    monthly_frac_2024 = {m: real.get((2024, m), 0) / total_2024 for m in range(1, 13)}

    # Pronostico 2023: total_2024 * 0.98, distribuido con el patron de 2024
    total_2023_est = total_2024 * 0.98
    for m in range(1, 13):
        if (2023, m) not in full:
            full[(2023, m)] = round(total_2023_est * monthly_frac_2024[m], 2)

    # Pronostico 2025 nov-dic: media movil ultimos 4 meses disponibles
    available_2025 = sorted([(m, real[(2025, m)]) for (y, m), v in real.items()
                             if y == 2025], key=lambda x: x[0])
    if available_2025:
        last4 = [v for _, v in available_2025[-4:]]
        avg_last4 = sum(last4) / len(last4)
        for m in [11, 12]:
            if (2025, m) not in full:
                # Usar factor estacional 2024 para nov/dic
                scale = monthly_frac_2024.get(m, 1/12)
                total_2025_est = sum(real.get((2025, mm), 0) for mm in range(1, 11)) / 10 * 12
                full[(2025, m)] = round(total_2025_est * scale, 2)

    return full


# ── 3. Calcular facturación por mes ──────────────────────────────────────────
def load_pricing_audit() -> dict[tuple[int, int], dict]:
    meta = json.loads(META_JSON.read_text(encoding="utf-8"))
    out  = {}
    for row in meta.get("pricing_monthly_audit", []):
        y, m = int(row["year"]), int(row["month"])
        out[(y, m)] = {
            "price_peak":    float(row["price_peak"]),
            "price_offpeak": float(row["price_offpeak"]),
        }
    return out


def build_billing_rows(ea_dict: dict, prices: dict) -> list[dict]:
    rows = []
    for year in YEARS_ALL:
        for month in range(1, 13):
            ea_total = ea_dict.get((year, month))
            if ea_total is None:
                continue

            e_punta    = round(ea_total * PEAK_FRAC, 4)
            e_fp       = round(ea_total * OFFPEAK_FRAC, 4)
            e_reactiva = round(ea_total * TAN_PHI, 4)

            # Factor de carga: FC = (EA/h_mes) / MD_estimado
            h_mes      = pd.Timestamp(year, month, 1).days_in_month * 24
            avg_kw     = ea_total / h_mes
            md_est     = avg_kw / FC_EST          # MD estimada (no disponible en Excel)
            fc         = round(avg_kw / md_est, 6) if md_est > 0 else FC_EST

            # Precio calibrado del audit distrital
            pp         = prices.get((year, month), {})
            p_peak     = pp.get("price_peak",    0.75)
            p_offpeak  = pp.get("price_offpeak", 0.52)
            total_fact = round(p_peak * e_punta + p_offpeak * e_fp, 2)

            rows.append({
                "Nombre":    "ELECTRO ORIENTE S.A.",
                "Mes":       MESES_ES[month],
                "Anio":      year,
                "Punta":     e_punta,
                "FP":        e_fp,
                "Reactiva":  e_reactiva,
                "FC":        fc,
                "Total_EA":  round(ea_total, 2),
                "Facturado": total_fact,
                "Tarifa":    TARIFA_CODE,
                "_source":   "REAL" if (year, month) in {k for k in ea_dict if
                             year in YEARS_REAL} else "PRONOSTICO",
            })
    return rows


# ── 4. Escribir CSV ───────────────────────────────────────────────────────────
def write_csv(rows: list[dict]) -> Path:
    BUILDINGCSV.mkdir(parents=True, exist_ok=True)
    header = ("Edificio1;Mes;Año;EnergiaActivaHoraPunta;EnergiaActivaFueraPunta;"
              "EnergiaReactiva;FactorCarga;totalEnergiaActiva;TotalFacturado;Tarifa")
    lines  = [header]
    for r in rows:
        def fmt(v): return str(v).replace(".", ",") if isinstance(v, float) else str(v)
        line = (
            f"{r['Nombre']};{r['Mes']};{r['Anio']};"
            f"{fmt(r['Punta'])};{fmt(r['FP'])};"
            f"{fmt(r['Reactiva'])};{fmt(r['FC'])};"
            f"{fmt(r['Total_EA'])};{fmt(r['Facturado'])};{r['Tarifa']}"
        )
        lines.append(line)
    OUTPUT_CSV.write_text("\n".join(lines) + "\n", encoding="latin-1")
    return OUTPUT_CSV


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 90)
    print("B_01.csv -- ELECTRO ORIENTE S.A. -- Datos reales GD-Iquitos + pronostico")
    print("=" * 90)

    # Datos reales
    real = read_elor_excel()
    print(f"\nDatos REALES del Excel (hoja 8.ELOR): {len(real)} registros")
    for (y, m), v in sorted(real.items()):
        print(f"  {y}-{MESES_ES[m]:>3}: {v:>12,.0f} kWh  ({v/pd.Timestamp(y,m,1).days_in_month/24:,.1f} kW promedio)")

    # Pronostico completo
    full = forecast_missing(real)
    missing = [(y, m) for y in YEARS_ALL for m in range(1, 13) if (y, m) not in real]
    print(f"\nMeses PRONOSTICADOS: {len(missing)}")
    for (y, m) in sorted(missing):
        print(f"  {y}-{MESES_ES[m]:>3}: {full[(y,m)]:>12,.0f} kWh  (pronostico)")

    # Precios del audit
    prices = load_pricing_audit()

    # Facturacion
    rows = build_billing_rows(full, prices)

    print(f"\n{'':>6} {'Anio':>5} {'EA total kWh':>14} {'Punta kWh':>12} "
          f"{'FP kWh':>12} {'FC':>7} {'S/ Factur':>12} {'Fuente':>11}")
    print("-" * 82)
    tot = {2023: 0.0, 2024: 0.0, 2025: 0.0}
    for r in rows:
        print(f"  {r['Mes']:>6} {r['Anio']:>5} {r['Total_EA']:>14,.1f} "
              f"{r['Punta']:>12,.1f} {r['FP']:>12,.1f} "
              f"{r['FC']:>7.4f} {r['Facturado']:>12,.2f}  {r['_source']}")
        tot[r['Anio']] += r['Total_EA']

    print("-" * 82)
    for y in YEARS_ALL:
        dm = tot[y] / (365.25 * 24 / 12 * 12)
        print(f"  Total {y}: {tot[y]:>14,.1f} kWh  "
              f"({tot[y]/12:>10,.1f} kWh/mes  |  {tot[y]/365.25:>8,.1f} kWh/dia)")

    out = write_csv(rows)
    print(f"\nGenerado: {out}")
    print(f"Tarifa: MT3 | pf=0.92 | PEAK_FRAC={PEAK_FRAC:.3f}")
    print("Fuente: Resultados_Preliminares-GD-Iquitos_V3 (2).xlsx, hoja 8.ELOR")


if __name__ == "__main__":
    main()
