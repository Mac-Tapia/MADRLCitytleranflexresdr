"""
Tests para el módulo uc3m.env.bact
===================================
Cubre: ClimateVector, BACTEncoder, IQUITOS_CLIMATE, dimensiones del tensor.
"""
from __future__ import annotations

import numpy as np
import pytest

from uc3m.env.bact import (
    IQUITOS_CLIMATE,
    BLDG_TYPE_CODES,
    KOPPEN_CODES,
    KA, KC, KB,
    ClimateVector,
)


# ── ClimateVector ─────────────────────────────────────────────────────────────

class TestClimateVector:
    def test_iquitos_climate_values(self):
        """Valores de Iquitos correctos."""
        c = IQUITOS_CLIMATE
        assert abs(c.lat - (-3.7491)) < 0.001
        assert abs(c.lon - (-73.2538)) < 0.001
        assert c.koppen == "Af"
        assert c.alt_m == 106
        assert c.t_avg_c == pytest.approx(26.5, abs=1.0)
        assert c.hr_avg_pct == pytest.approx(85.0, abs=5.0)
        assert c.ghi_avg_wm2 == pytest.approx(520.0, abs=50.0)

    def test_climate_vector_to_array(self):
        """to_array() retorna vector de longitud KC=8."""
        arr = IQUITOS_CLIMATE.to_array()
        assert arr.shape == (KC,)
        assert arr.dtype in (np.float32, np.float64)
        # Ningún valor es NaN
        assert not np.any(np.isnan(arr))

    def test_climate_vector_lat_lon_encoded(self):
        """lat y lon aparecen en el array (primeras dos posiciones)."""
        arr = IQUITOS_CLIMATE.to_array()
        assert arr[0] == pytest.approx(IQUITOS_CLIMATE.lat)
        assert arr[1] == pytest.approx(IQUITOS_CLIMATE.lon)

    def test_custom_climate(self):
        """Se puede construir un ClimateVector custom."""
        c = ClimateVector(
            lat=40.4, lon=-3.7, alt_m=667,
            t_avg_c=14.0, hr_avg_pct=55.0, ghi_avg_wm2=350.0,
            koppen="Csa",
        )
        arr = c.to_array()
        assert arr.shape == (KC,)
        assert arr[0] == pytest.approx(40.4)

    def test_koppen_code_af_is_1(self):
        """Köppen Af tiene código 1 (tropical lluvioso)."""
        assert KOPPEN_CODES["Af"] == 1

    def test_koppen_code_unknown_is_0(self):
        assert KOPPEN_CODES["Unknown"] == 0


# ── Dimensiones del BACT ──────────────────────────────────────────────────────

class TestBACTDimensions:
    def test_ka_value(self):
        """KA = 14 activos según Definición 4.1."""
        assert KA == 14

    def test_kc_value(self):
        """KC = 8 dimensiones de clima."""
        assert KC == 8

    def test_kb_value(self):
        """KB = 7 dimensiones de edificio."""
        assert KB == 7

    def test_total_bact_dim(self):
        """Dimensión total BACT = KA + KC + KB = 29."""
        assert KA + KC + KB == 29

    def test_bldg_type_codes_not_empty(self):
        assert len(BLDG_TYPE_CODES) >= 10

    def test_bldg_salud_24h_has_code(self):
        assert "salud_24h" in BLDG_TYPE_CODES
        assert BLDG_TYPE_CODES["salud_24h"] > 0

    def test_bldg_educacion_variants_same_code(self):
        """educacion, educacion_motolineal, educacion_tec tienen el mismo código."""
        assert BLDG_TYPE_CODES["educacion"] == BLDG_TYPE_CODES["educacion_motolineal"]
        assert BLDG_TYPE_CODES["educacion"] == BLDG_TYPE_CODES["educacion_tec"]


# ── BACTEncoder (si existe en el módulo) ──────────────────────────────────────

class TestBACTEncoder:
    def test_encoder_produces_29d_vector(self):
        """BACTEncoder.encode() produce vector de 29 dimensiones."""
        try:
            from uc3m.env.bact import BACTEncoder
        except ImportError:
            pytest.skip("BACTEncoder no exportado")

        encoder = BACTEncoder(climate=IQUITOS_CLIMATE)
        # Datos mínimos de un edificio de prueba
        bldg_data = {
            "bldg_type": "industrial",
            "area_m2": 14000,
            "cap_bess_kwh": 4000,
            "p_bess_kw": 800,
            "dod": 0.80,
            "eta_rt": 0.9025,
            "pv_kwp": 2117,
            "n_ev_chargers": 2,
            "ev_charger_kw": 7.4,
            "has_dhw": False,
            "cop_design": 2.8,
        }
        vec = encoder.encode(bldg_data)
        assert vec.shape == (KA + KC + KB,)
        assert not np.any(np.isnan(vec))
