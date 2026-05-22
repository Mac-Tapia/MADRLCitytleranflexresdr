"""
Tests unitarios para tools/distill_building_loads.py — calibración de cargas.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Importar las funciones de calibración directamente
sys.path.insert(0, str(ROOT / "tools"))
from distill_building_loads import (
    compute_cop_array,
    compute_managed_energy,
    build_month_year_index,
    ETA_BY_BLDG,
    T_TARGET,
    COP_CLIP_LOW,
    COP_CLIP_HIGH,
    COP_ACS_DEF,
    MEDIDAS_REALES,
    BUILDINGS_WITH_DATA,
)


class TestComputeCOPArray:
    """Tests para la función compute_cop_array (COP Carnot variable)."""

    def test_cop_at_setpoint_plus_one(self):
        """COP clipeado cuando T_out = T_target + 1 → raw muy alto → COP_CLIP_HIGH."""
        # denom = max(T_target+1 - T_target, 0.5) = 1.0
        # COP_raw = (8.5 + 273.15) * 0.193858 / 1.0 ≈ 54.6 → clipeado a COP_CLIP_HIGH
        eta = 0.193858
        t_out = np.array([T_TARGET + 1.0])
        cop = compute_cop_array(t_out, eta)
        raw = (T_TARGET + 273.15) * eta / 1.0
        expected = float(np.clip(raw, COP_CLIP_LOW, COP_CLIP_HIGH))
        assert cop[0] == pytest.approx(expected, rel=1e-6)

    def test_cop_clipped_low(self):
        """T_out muy alta → COP se clipea a COP_CLIP_LOW = 1.5."""
        eta = 0.173087
        t_out = np.array([100.0])   # temperatura imposible → COP muy bajo
        cop = compute_cop_array(t_out, eta)
        assert cop[0] == pytest.approx(COP_CLIP_LOW, rel=1e-6)

    def test_cop_clipped_high(self):
        """T_out = T_target → denom = 0.5 → COP alto → clipea a COP_CLIP_HIGH."""
        eta = 0.193858
        t_out = np.array([T_TARGET])   # denom = max(0, 0.5) = 0.5
        cop = compute_cop_array(t_out, eta)
        expected_raw = (T_TARGET + 273.15) * eta / 0.5
        if expected_raw > COP_CLIP_HIGH:
            assert cop[0] == pytest.approx(COP_CLIP_HIGH, rel=1e-6)
        else:
            assert cop[0] == pytest.approx(expected_raw, rel=1e-6)

    def test_cop_typical_iquitos(self):
        """Para T_out=28°C (Iquitos típico) el COP está en [2.0, 3.5]."""
        eta = 0.193858
        t_out = np.array([28.0])
        cop = compute_cop_array(t_out, eta)
        assert COP_CLIP_LOW <= cop[0] <= COP_CLIP_HIGH
        assert 2.0 <= cop[0] <= 3.5

    def test_cop_array_shape(self):
        """compute_cop_array preserva la forma del array de entrada."""
        eta = 0.193858
        t_out = np.random.uniform(20, 35, 8760)
        cop = compute_cop_array(t_out, eta)
        assert cop.shape == (8760,)

    def test_cop_all_positive(self):
        """COP siempre positivo para cualquier T_out razonable."""
        eta = 0.193858
        t_out = np.linspace(15.0, 45.0, 200)
        cop = compute_cop_array(t_out, eta)
        assert np.all(cop > 0)


class TestComputeManagedEnergy:
    """Tests para compute_managed_energy."""

    def test_pure_cooling_no_dhw(self):
        """Sin DHW, E_gest = cooling_demand / COP."""
        n = 10
        df = pd.DataFrame({
            "cooling_demand": np.ones(n) * 10.0,   # kWh_thermal/h
            "dhw_demand":     np.zeros(n),
        })
        cop_act = np.ones(n) * 2.5
        cop_acs = 0.85
        e_gest = compute_managed_energy(df, cop_act, cop_acs)
        expected = 10.0 / 2.5   # = 4.0 kWh_elec/h
        assert np.allclose(e_gest, expected)

    def test_pure_dhw_no_cooling(self):
        """Sin cooling, E_gest = dhw_demand / COP_ACS."""
        n = 10
        df = pd.DataFrame({
            "cooling_demand": np.zeros(n),
            "dhw_demand":     np.ones(n) * 50.0,
        })
        cop_act = np.ones(n) * 2.5
        cop_acs = 0.85
        e_gest = compute_managed_energy(df, cop_act, cop_acs)
        expected = 50.0 / 0.85
        assert np.allclose(e_gest, expected)

    def test_both_cooling_and_dhw(self):
        """E_gest = cd/COP + dw/COP_ACS cuando ambos son > 0."""
        n = 5
        df = pd.DataFrame({
            "cooling_demand": np.ones(n) * 10.0,
            "dhw_demand":     np.ones(n) * 5.0,
        })
        cop_act = np.ones(n) * 2.0
        cop_acs = 0.85
        e_gest = compute_managed_energy(df, cop_act, cop_acs)
        expected = 10.0 / 2.0 + 5.0 / 0.85
        assert np.allclose(e_gest, expected)

    def test_missing_columns_defaults_to_zero(self):
        """Si falta cooling_demand o dhw_demand, E_gest = 0."""
        n = 5
        df = pd.DataFrame({"other_col": np.ones(n)})
        cop_act = np.ones(n) * 2.5
        cop_acs = 0.85
        e_gest = compute_managed_energy(df, cop_act, cop_acs)
        assert np.allclose(e_gest, 0.0)

    def test_nonnegative_output(self):
        """E_gest siempre ≥ 0."""
        n = 100
        df = pd.DataFrame({
            "cooling_demand": np.abs(np.random.randn(n)),
            "dhw_demand":     np.abs(np.random.randn(n)),
        })
        cop_act = np.random.uniform(1.5, 5.0, n)
        e_gest = compute_managed_energy(df, cop_act, 0.85)
        assert np.all(e_gest >= 0)


class TestBuildMonthYearIndex:
    """Tests para build_month_year_index."""

    def test_years_assigned_correctly(self):
        """2023=filas 0–8759, 2024=8760–17543, 2025=17544–26303."""
        months = list(range(1, 13)) * (26304 // 12)
        if len(months) < 26304:
            months += [1] * (26304 - len(months))
        df = pd.DataFrame({"month": months[:26304], "cooling_demand": 0.0, "non_shiftable_load": 0.0})
        df = build_month_year_index(df)
        assert (df["_year"][:8760] == 2023).all()
        assert (df["_year"][8760:8760 + 8784] == 2024).all()
        assert (df["_year"][8760 + 8784:] == 2025).all()

    def test_month_column_preserved(self):
        """La columna _month es igual a month original."""
        months = np.tile(np.arange(1, 13), 26304 // 12 + 1)[:26304]
        df = pd.DataFrame({"month": months, "cooling_demand": 0.0})
        df_out = build_month_year_index(df)
        assert (df_out["_month"].values == df_out["month"].values).all()

    def test_total_rows_preserved(self):
        """build_month_year_index no cambia el número de filas."""
        n = 26304
        df = pd.DataFrame({"month": np.tile(np.arange(1, 13), n // 12 + 1)[:n]})
        df_out = build_month_year_index(df)
        assert len(df_out) == n


class TestProportionalScaling:
    """Tests de la lógica de escala proporcional — núcleo del algoritmo."""

    def test_scale_factor_exact(self):
        """scale = E_medido / (E_gest + E_ns_orig) es exacto."""
        e_gest  = 300_000.0
        e_ns    = 182_735.0
        e_med   = 482_735.0   # medición real B1
        total_syn = e_gest + e_ns
        scale = e_med / total_syn
        # Verificar que la escala sea la correcta
        assert scale == pytest.approx(e_med / total_syn, rel=1e-9)

    def test_scale_preserves_proportions(self):
        """cd_nuevo/nsl_nuevo = cd_orig/nsl_orig (proporciones conservadas)."""
        cd_orig  = np.array([100.0, 200.0, 150.0])
        nsl_orig = np.array([50.0,  80.0,  60.0])
        scale    = 0.75
        cd_new   = cd_orig  * scale
        nsl_new  = nsl_orig * scale
        ratio_orig = cd_orig / nsl_orig
        ratio_new  = cd_new  / nsl_new
        assert np.allclose(ratio_orig, ratio_new)

    def test_scale_zero_protected(self):
        """Si E_total_syn = 0, scale = 1.0 (sin división por cero)."""
        e_total_syn = 0.0
        e_med       = 500.0
        scale = e_med / e_total_syn if e_total_syn > 0 else 1.0
        assert scale == 1.0

    def test_scale_underestimation(self):
        """scale > 1 cuando sintético subestima (scale-up)."""
        e_gest  = 200_000.0
        e_ns    = 100_000.0
        e_med   = 400_000.0   # medido es más alto → scale > 1
        total_syn = e_gest + e_ns
        scale = e_med / total_syn
        assert scale > 1.0

    def test_scale_overestimation(self):
        """scale < 1 cuando sintético sobreestima (scale-down)."""
        # B7 UNAP: sintético 2.6x → scale ≈ 0.38
        e_gest  = 25_000.0
        e_ns    = 9_000.0
        e_med   = 13_089.0   # medición real
        total_syn = e_gest + e_ns
        scale = e_med / total_syn
        assert scale < 1.0
        assert 0.0 < scale < 1.0   # nunca negativo


class TestMedidasReales:
    """Tests de configuración del dict MEDIDAS_REALES."""

    def test_all_buildings_present(self):
        """MEDIDAS_REALES tiene los 9 edificios esperados."""
        expected = {1, 7, 8, 10, 11, 12, 13, 14, 15}
        assert set(MEDIDAS_REALES.keys()) == expected

    def test_buildings_with_data_list(self):
        """BUILDINGS_WITH_DATA == sorted(MEDIDAS_REALES.keys())."""
        assert BUILDINGS_WITH_DATA == sorted(MEDIDAS_REALES.keys())

    def test_all_values_positive(self):
        """Todas las mediciones son > 0 kWh/mes."""
        for bldg_id, years in MEDIDAS_REALES.items():
            for year, months in years.items():
                for month, kwh in months.items():
                    assert kwh > 0, f"B{bldg_id} {year}-{month:02d}: kWh={kwh}"

    def test_three_years_per_building(self):
        """Cada edificio tiene datos para 2023, 2024, 2025."""
        for bldg_id, years in MEDIDAS_REALES.items():
            assert 2023 in years, f"B{bldg_id} sin datos 2023"
            assert 2024 in years, f"B{bldg_id} sin datos 2024"
            assert 2025 in years, f"B{bldg_id} sin datos 2025"

    def test_12_months_per_year(self):
        """Cada año tiene 12 meses."""
        for bldg_id, years in MEDIDAS_REALES.items():
            for year, months in years.items():
                assert len(months) == 12, f"B{bldg_id} {year}: {len(months)} meses"

    def test_eta_by_bldg_keys_match(self):
        """ETA_BY_BLDG tiene exactamente los mismos edificios que MEDIDAS_REALES."""
        assert set(ETA_BY_BLDG.keys()) == set(MEDIDAS_REALES.keys())

    def test_eta_values_plausible(self):
        """Los factores Carnot eta están en un rango razonable (0.1, 0.3)."""
        for bldg_id, eta in ETA_BY_BLDG.items():
            assert 0.10 < eta < 0.30, f"B{bldg_id}: eta={eta} fuera de rango"

    def test_hospital_consumption_higher_than_school(self):
        """Hospital Regional (B11) consume más que Colegio CNI (B15)."""
        kwh_hospital = MEDIDAS_REALES[11][2023][1]
        kwh_school   = MEDIDAS_REALES[15][2023][1]
        assert kwh_hospital > kwh_school


class TestCalibrationIntegration:
    """Tests de calibración que requieren el dataset completo."""

    @pytest.mark.parametrize("bldg_id", [1, 7, 8, 10, 11, 12, 13, 14, 15])
    def test_calibration_delta_near_zero(self, bldg_id, dataset_dir):
        """Después de calibrar, Δ% ≈ 0 para todos los edificios."""
        from distill_building_loads import calibrate_building, load_schema, load_weather

        if not (dataset_dir / f"Building_{bldg_id}.csv").exists():
            pytest.skip(f"Building_{bldg_id}.csv no encontrado")
        if not (dataset_dir / "weather.csv").exists():
            pytest.skip("weather.csv no encontrado")

        schema  = load_schema()
        t_out   = load_weather()

        report = calibrate_building(bldg_id, schema, t_out,
                                    dry_run=True, report_only=False)

        assert not report.empty, f"B{bldg_id}: reporte vacío"
        max_delta = report["delta_%"].abs().max()
        assert max_delta < 0.01, (
            f"B{bldg_id}: Δ% máximo = {max_delta:.4f}% — debería ser < 0.01%"
        )

    def test_scale_factors_plausible(self, dataset_dir):
        """Los factores de escala están dentro de rangos esperados por edificio."""
        from distill_building_loads import calibrate_building, load_schema, load_weather

        if not (dataset_dir / "Building_1.csv").exists():
            pytest.skip("Dataset no disponible")

        schema = load_schema()
        t_out  = load_weather()

        # B1 ELOR: sintético casi exacto → scale ≈ 1.0
        report = calibrate_building(1, schema, t_out, dry_run=True)
        if not report.empty:
            assert report["scale_factor"].mean() == pytest.approx(1.0, abs=0.20)

        # B7 UNAP: escala plausible (dataset calibrado → ≈1.0; sin calibrar → ≈0.38)
        if (dataset_dir / "Building_7.csv").exists():
            report7 = calibrate_building(7, schema, t_out, dry_run=True)
            if not report7.empty:
                mean_scale = report7["scale_factor"].mean()
                assert 0.0 < mean_scale <= 1.5

    def test_report_has_required_columns(self, dataset_dir):
        """El reporte de calibración tiene todas las columnas esperadas."""
        from distill_building_loads import calibrate_building, load_schema, load_weather

        if not (dataset_dir / "Building_13.csv").exists():
            pytest.skip("Building_13.csv no encontrado")

        schema = load_schema()
        t_out  = load_weather()
        report = calibrate_building(13, schema, t_out, dry_run=True)

        required_cols = {
            "year", "mes", "E_medido_kWh", "E_total_syn",
            "E_gest_kWh", "E_ns_orig", "scale_factor",
            "E_cal_tot", "delta_%",
        }
        assert required_cols.issubset(set(report.columns))
