# Tareas — SPEC-013

**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`  
**Estado conciliado:** [STATUS](../STATUS.md)  
**Revisión:** 2026-11-04

`[x]` = implementado y verificado con el comando de aceptación. No implica aceptación científica.

- [x] **FR-013.3:** Dominio y extracción — `uc3m/domain/tariffs.py`, `uc3m/adapters/osinergmin/pba_pdf.py`
- [x] **FR-013.1, FR-013.2, FR-013.4:** Descarga, identidad e inmutabilidad — `uc3m/adapters/osinergmin/pba_pdf.py`
- [x] **FR-013.5, FR-013.6, FR-013.7:** Contraste, herramienta y artefactos reales (37 vigencias, 34 contrastadas, 0 fallos) — `uc3m/application/dataset/tariff_crosscheck.py`, `tools/dataset/ingest_osinergmin_pba.py`, `data/tariffs/osinergmin/`
- [x] **FR-013.8:** Puerta `tariff_crosscheck` y rechazo de tarifa con punta distinta. Probado con pruebas y con los 42 pliegos reales; **el constructor completo no se ejecutó**, porque ningún dataset se reconstruye en este módulo — `tools/dataset/build_fresh_campaign_dataset.py`

- [x] **FR-013.9, FR-013.10:** Factura con cargo por potencia (decisión D02): tabla de 612 tarifas y eje de costo `bill_cost_total`. La recompensa no cambia — `tools/dataset/build_bill_tariffs.py`, `uc3m/application/evaluation/bill_cost.py`, `configs/evaluation/kpis.yaml`

**Aceptación:** criterios 1 a 4 de [spec.md](spec.md).

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe -B -m pytest -p no:cacheprovider -q tests/fresh_training/test_tariff_busbar.py tests/fresh_training/test_bill_cost.py
.\.venv39-citylearn-v3\Scripts\python.exe -B tools/dataset/ingest_osinergmin_pba.py --offline
```

**Pendiente fuera de este módulo:** decisión D04 (recompensar la factura), localizar PDF de las 8 vigencias `sheet_only` si existen y causa del escalón de 2023-11.
