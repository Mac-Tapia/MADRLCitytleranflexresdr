# Módulo 1, tarifas oficiales: plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ingerir los PDF PBA de Osinergmin como fuente trazable y contrastarlos con los pliegos del dataset, sin alterar ningún dataset.

**Architecture:** Dominio puro (`uc3m/domain/tariffs.py`), adaptador de PDF y descarga (`uc3m/adapters/osinergmin/`), contraste puro (`uc3m/application/dataset/tariff_crosscheck.py`) y una herramienta como raíz de composición (`tools/dataset/ingest_osinergmin_pba.py`). No se crea puerto.

**Tech Stack:** Python 3.9 (`.venv39-citylearn-v3`), `pypdf` 6.10.2, `requests`, `pytest`.

**Spec:** [specs/013-modulo1-tarifas/spec.md](../../specs/013-modulo1-tarifas/spec.md)

## Global Constraints

- Sistema: `Electro Oriente`, nivel `MT`. Vigencias: 2022-12-04 a 2025-12-04.
- Base de URL: `https://www.osinergmin.gob.pe/seccion/centro_documental/gart/PliegosTarifarios/`. Variantes en orden: `1 PBA{ddmmaaaa}.pdf`, `PBA{ddmmaaaa}.pdf`.
- Pausa entre peticiones: 1,5 s. Agente: `Mozilla/5.0 (MADRL Iquitos thesis; dataset provenance)`.
- Un HTTP distinto de 200 y 404 detiene la ingesta. Nunca reintentar para eludir un bloqueo.
- Banda de contraste `RATIO_BAND = (1.005, 1.030)`, declarada como criterio del proyecto.
- Valores tal como se imprimen: coma decimal, sin IGV. No redondear ni convertir moneda.
- Salida de la herramienta: 0 correcto, 2 rechazo de fuente, 3 fallos de contraste.
- `data/campaigns/`, `CityLearn/` y `external/` no se escriben.
- Commits solo con autorización expresa y con rutas explícitas; nunca `git add -A`.

## Review Focus

1. Fila presente sin números (como `Electro Sur Este MT` en el PDF real): debe fallar, no dar cero.
2. El servidor responde con 200 y HTML, o con el PDF de otra fecha: debe rechazarse, no registrarse.
3. Un 403 o 500 durante la descarga: debe detener la ingesta, no contar como `missing`.
4. Un PDF ya registrado cambia en el servidor: se preserva el original y se informa `source_changed`.
5. Una vigencia sin PDF: debe figurar en `sheet_only`, no heredar el valor de otra vigencia.

---

### Task 1: Dominio y extracción de PDF

**Files:**
- Create: `uc3m/domain/tariffs.py`, `uc3m/adapters/osinergmin/__init__.py`, `uc3m/adapters/osinergmin/pba_pdf.py`
- Modify: `pyproject.toml` (añadir `pypdf>=6.10,<7` a los extras `dataset` y `all`)
- Test: `tests/fresh_training/test_tariff_busbar.py`

**Interfaces:**
- Produces:
  - `BusbarPrice(power_pen_kw_month: float, energy_peak_ctm_kwh: float, energy_offpeak_ctm_kwh: float)`, congelada, con propiedad `is_flat -> bool`. Rechaza con `ValueError` valores no finitos o no positivos.
  - `BusbarSheet(valid_from: date, system: str, resolutions: Tuple[str, ...], barra: BusbarPrice, efectivo: BusbarPrice)`, congelada.
  - `class PbaFormatError(ValueError)`.
  - `parse_pba_text(text: str, *, system: str = 'Electro Oriente') -> BusbarSheet`.
  - `parse_pba(payload: bytes, *, system: str = 'Electro Oriente') -> BusbarSheet`: lee solo la página 1; importa `pypdf` dentro de la función.

- [ ] **Step 1: Write the failing tests**

```python
ROW_B = 'Electro Oriente MT 32,12 78,58 78,58 Electro Oriente MT 32,12 78,58 78,58 32,12 78,58 78,58 8,11 78,58 86,69'
ROW_E = 'Electro Oriente MT 32,12 34,71 34,71 Electro Oriente MT 32,12 34,71 34,71 32,12 34,71 34,71 8,11 34,71 42,82'
HEAD = 'TARIFAS EN BARRA (Res. N° 048-2025-OS/CD y N° 109-2025-OS/CD)\nACTUALIZADO AL 04/Julio/2025 CON REDONDEO\n'

def test_parse_real_rows():
    sheet = parse_pba_text(HEAD + ROW_B + '\n' + ROW_E)
    assert sheet.valid_from == date(2025, 7, 4)
    assert sheet.resolutions == ('048-2025', '109-2025')
    assert sheet.barra == BusbarPrice(32.12, 78.58, 78.58)
    assert sheet.efectivo == BusbarPrice(32.12, 34.71, 34.71)
    assert sheet.barra.is_flat

def test_updated_column_wins_over_base():
    row = 'Electro Oriente MT 32,12 25,18 25,18 Electro Oriente MT 32,13 25,19 25,19'
    assert parse_pba_text(HEAD + ROW_B + '\n' + row).efectivo == BusbarPrice(32.13, 25.19, 25.19)

@pytest.mark.parametrize('body', ['', ROW_B, ROW_B + '\n' + ROW_E + '\n' + ROW_E,
                                  'Electro Oriente MT\n' + ROW_E])
def test_wrong_row_count_or_empty_row_is_rejected(body):
    with pytest.raises(PbaFormatError):
        parse_pba_text(HEAD + body)

def test_missing_date_is_rejected():
    with pytest.raises(PbaFormatError):
        parse_pba_text(ROW_B + '\n' + ROW_E)

def test_non_positive_price_is_rejected():
    with pytest.raises(ValueError):
        BusbarPrice(0.0, 1.0, 1.0)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.\.venv39-citylearn-v3\Scripts\python.exe -B -m pytest -p no:cacheprovider -q tests/fresh_training/test_tariff_busbar.py`
Expected: FAIL en la recolección, `ModuleNotFoundError: uc3m.domain.tariffs`.

- [ ] **Step 3: Implement the types and parsers**

Regex de fila: nombre + `MT` + 3 números `\d+,\d+`, repetido una segunda vez, con `\s+` entre elementos; se toma el segundo trío. La primera coincidencia es barra y la segunda es efectivo. El contenido de `body=ROW_B` da una sola coincidencia, por lo que se rechaza. Fecha: `ACTUALIZADO AL dd/Mes/aaaa`, sin distinguir mayúsculas, con los meses de `osinergmin_pliegos.MONTHS` reescritos en el adaptador (el adaptador no importa `tools/`). Resoluciones: `\d{3}-\d{4}` antes de `-OS/CD`, únicas y ordenadas.

- [ ] **Step 4: Run tests to verify they pass**

Run: el comando del paso 2.
Expected: todas aprobadas, sin omisiones.

- [ ] **Step 5: Commit, si está autorizado**

`git add uc3m/domain/tariffs.py uc3m/adapters/osinergmin/__init__.py uc3m/adapters/osinergmin/pba_pdf.py pyproject.toml tests/fresh_training/test_tariff_busbar.py`, solo el bloque propio de `pyproject.toml` (el archivo ya tiene cambios ajenos: usar `git add -p` no es posible aquí, así que se pide confirmación antes).

### Task 2: Descarga, identidad e inmutabilidad

**Files:**
- Modify: `uc3m/adapters/osinergmin/pba_pdf.py`
- Test: `tests/fresh_training/test_tariff_busbar.py`

**Interfaces:**
- Consumes: `parse_pba` de la tarea 1.
- Produces:
  - `candidate_names(valid_from: date) -> Tuple[str, str]`.
  - `candidate_dates(start: date, end: date, sheet_dates: Iterable[date]) -> List[date]`: unión ordenada de las fechas de los pliegos y el día 4 de cada mes del rango.
  - `class SourceChangedError(ValueError)`.
  - `fetch_pba(valid_from: date, raw_dir: Path, *, session, known_sha256: Optional[str] = None, pause_s: float = 1.5) -> Optional[dict]`: devuelve `{'path', 'source_uri', 'sha256', 'obtained_at', 'valid_from'}`, o `None` si todas las variantes dan 404.

- [ ] **Step 1: Write the failing tests** con una sesión falsa que devuelve estado y contenido por URL y un `parse` real sustituido por `monkeypatch` de `parse_pba`.

```python
def test_first_variant_404_second_200(tmp_path, fake_pdf): ...
    # entry['source_uri'] termina en 'PBA04122022.pdf'; el archivo existe y su sha256 coincide
def test_all_404_is_missing(tmp_path): assert fetch_pba(D, tmp_path, session=all_404, pause_s=0) is None
@pytest.mark.parametrize('status', [403, 500])
def test_other_http_error_stops(status, tmp_path): ...  # raises requests.HTTPError; ningún archivo escrito
def test_html_with_200_is_rejected(tmp_path): ...       # PbaFormatError; ningún archivo escrito
def test_pdf_of_other_date_is_rejected(tmp_path, monkeypatch): ...  # PbaFormatError; ningún archivo escrito
def test_changed_source_keeps_original(tmp_path, fake_pdf): ...
    # known_sha256 distinto: SourceChangedError; los bytes originales siguen intactos
def test_candidate_dates_union():
    dates = candidate_dates(date(2024, 3, 1), date(2024, 3, 31), [date(2024, 3, 15)])
    assert dates == [date(2024, 3, 4), date(2024, 3, 15)]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.\.venv39-citylearn-v3\Scripts\python.exe -B -m pytest -p no:cacheprovider -q tests/fresh_training/test_tariff_busbar.py -k "variant or missing or http or html or other_date or changed or candidate"`
Expected: FAIL con `ImportError` o `AttributeError`.

- [ ] **Step 3: Implement `fetch_pba`**

Validar antes de escribir: `%PDF` y fecha impresa == `valid_from`. Nombre local: `pba_{aaaa-mm-dd}.pdf`. Escritura atómica (temporal + `os.replace`). Si el archivo existe o hay `known_sha256`, comparar y lanzar `SourceChangedError` sin escribir.

- [ ] **Step 4: Run tests to verify they pass**

Run: el comando del paso 2.
Expected: todas aprobadas.

- [ ] **Step 5: Commit, si está autorizado**

`git add uc3m/adapters/osinergmin/pba_pdf.py tests/fresh_training/test_tariff_busbar.py`

### Task 3: Contraste, herramienta y artefactos reales

**Files:**
- Create: `uc3m/application/dataset/tariff_crosscheck.py`, `tools/dataset/ingest_osinergmin_pba.py`
- Create por ejecución: `data/tariffs/osinergmin/busbar_electro_oriente.csv`, `data/tariffs/osinergmin/pba_manifest.json`
- Modify: `governance/repository_layout.yaml` (`approved_raw_roots`: añadir `data/tariffs/osinergmin/raw`), `.gitignore` (añadir `data/tariffs/osinergmin/raw/`), `specs/013-modulo1-tarifas/tasks.md`, `specs/STATUS.md`, `tools/dataset/README.md`
- Test: `tests/fresh_training/test_tariff_busbar.py`

**Interfaces:**
- Consumes: `BusbarSheet`, `fetch_pba`, `candidate_dates`, `parse_pba`; `parse_sheet` de `tools/dataset/osinergmin_pliegos.py`, importado solo en la herramienta.
- Produces:
  - `RATIO_BAND = (1.005, 1.030)`.
  - `crosscheck(sheets: Mapping[date, BusbarSheet], charges: Mapping[date, Mapping[str, Mapping[str, float]]], *, tariff: str = 'MT3') -> dict` con claves `rows`, `pdf_only`, `sheet_only`, `failures`. Cada fallo es `{'valid_from', 'reason'}`, con `reason` en `non_flat_busbar`, `non_flat_sheet`, `ratio_out_of_band`, `missing_energy_charge`.
  - `main(argv=None) -> int` con `--start`, `--end`, `--root` (`data/tariffs/osinergmin`), `--sheets-dir` (`data/campaigns/iquitos_v4/raw/osinergmin`), `--offline`.

- [ ] **Step 1: Write the failing tests**

```python
def test_common_date_in_band_has_no_failure():
    out = crosscheck({D: sheet(34.71)}, {D: {'MT3': {'energy_peak_ctm_kwh': 35.10, 'energy_offpeak_ctm_kwh': 35.10}}})
    assert out['failures'] == [] and out['rows'][0]['ratio'] == pytest.approx(35.10/34.71)

def test_out_of_band_and_non_flat_are_reported():
    high = crosscheck({D: sheet(34.71)}, {D: {'MT3': {'energy_peak_ctm_kwh': 40.0, 'energy_offpeak_ctm_kwh': 40.0}}})
    assert high['failures'] == [{'valid_from': D.isoformat(), 'reason': 'ratio_out_of_band'}]
    tou = crosscheck({D: sheet(34.71)}, {D: {'MT3': {'energy_peak_ctm_kwh': 35.1, 'energy_offpeak_ctm_kwh': 30.0}}})
    assert {'valid_from': D.isoformat(), 'reason': 'non_flat_sheet'} in tou['failures']

def test_coverage_is_declared_and_never_filled():
    out = crosscheck({D: sheet(34.71)}, {E: {'MT3': {'energy_peak_ctm_kwh': 35.1, 'energy_offpeak_ctm_kwh': 35.1}}})
    assert out['pdf_only'] == [D.isoformat()] and out['sheet_only'] == [E.isoformat()] and out['rows'] == []

def test_mt4_energy_key_is_accepted():
    out = crosscheck({D: sheet(34.71)}, {D: {'MT4': {'energy_ctm_kwh': 35.10}}}, tariff='MT4')
    assert out['failures'] == []
```

Además, `test_offline_rebuild_checks_hashes`: con un PDF falso cuyo `parse_pba` se sustituye con `monkeypatch`, `main(['--offline', ...])` escribe CSV y manifiesto en `tmp_path`, y un byte cambiado devuelve 2.

- [ ] **Step 2: Run tests to verify they fail**

Run: `.\.venv39-citylearn-v3\Scripts\python.exe -B -m pytest -p no:cacheprovider -q tests/fresh_training/test_tariff_busbar.py -k "common or out_of_band or coverage or mt4 or offline"`
Expected: FAIL con `ImportError`.

- [ ] **Step 3: Implement `crosscheck` y `main`**

Columnas del CSV: `valid_from,resolutions,barra_power,barra_peak,barra_offpeak,efectivo_power,efectivo_peak,efectivo_offpeak,sheet_mt3_energy,ratio_mt3_efectivo`. Manifiesto: `schema_version`, `system`, `files` (uno por vigencia con `source_uri`, `sha256`, `obtained_at`, `source_type: official_tariff_sheet`), `missing`, `crosscheck`, `limitations`. Limitaciones literales: «La banda de contraste es criterio del proyecto»; «La causa del escalón de la razón en 2023-11 no está identificada»; «Punta igual a fuera de punta: no hay señal horaria oficial». El JSON y el CSV se escriben de forma atómica.

- [ ] **Step 4: Run tests to verify they pass**

Run: el comando del paso 2.
Expected: todas aprobadas.

- [ ] **Step 5: Tomar la huella de los datos, descargar y regenerar**

```bash
find data/campaigns -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum
.venv39-citylearn-v3/Scripts/python.exe -B tools/dataset/ingest_osinergmin_pba.py
.venv39-citylearn-v3/Scripts/python.exe -B tools/dataset/ingest_osinergmin_pba.py --offline
find data/campaigns -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum
```

Expected: salida 0 en ambas; 37 vigencias en el CSV; `pdf_only = [2023-05-04, 2024-03-04, 2025-01-04]` (2023-05-04 apareció en la ingesta real y se verificó contra los pliegos de mayo de 2023); `sheet_only` con las 8 fechas de SPEC-013; `failures = []`; las dos huellas iguales (`00afe20e…` si `data/campaigns` no cambió). Si aparecen más o menos vigencias, detenerse e informar; no ajustar la prueba para que coincida.

- [ ] **Step 6: Comprobar que la raíz nueva no rompe los contratos**

Run: `.\.venv39-citylearn-v3\Scripts\python.exe -B -m pytest -p no:cacheprovider -q tests/fresh_training/test_tariff_busbar.py tests/fresh_training/test_names.py tests/fresh_training/test_fresh_isolation.py tests/contract/test_spec_kit_consistency.py`
Expected: todas aprobadas.

- [ ] **Step 7: Actualizar `tasks.md`, `STATUS.md` y el README con los comandos y resultados reales**

- [ ] **Step 8: Commit, si está autorizado**

`git add uc3m/application/dataset/tariff_crosscheck.py tools/dataset/ingest_osinergmin_pba.py data/tariffs/osinergmin/busbar_electro_oriente.csv data/tariffs/osinergmin/pba_manifest.json governance/repository_layout.yaml .gitignore specs/013-modulo1-tarifas tests/fresh_training/test_tariff_busbar.py`. `STATUS.md` y el README tienen cambios ajenos: pedir confirmación antes de incluirlos.

### Task 4: Puerta en el constructor

**Desbloqueada** por el propietario el 2026-11-04. No depende de D02, porque no cambia el precio.

**Files:**
- Modify: `tools/dataset/build_fresh_campaign_dataset.py:355-356` y `:1249-1261`
- Test: `tests/fresh_training/test_tariff_busbar.py`

**Interfaces:**
- Consumes: `crosscheck` de la tarea 3 y `data/tariffs/osinergmin/pba_manifest.json`.
- Produces: `gates['tariff_crosscheck'] -> bool` en `dataset_acceptance.json` de construcciones nuevas.

- [ ] **Step 1: Write the failing tests**

```python
def test_energy_rate_refuses_time_of_use_sheet():
    with pytest.raises(ValueError):
        energy_rate_ctm({'energy_peak_ctm_kwh': 35.1, 'energy_offpeak_ctm_kwh': 30.0})

def test_gate_is_false_when_crosscheck_has_failures():
    assert tariff_crosscheck_gate({'failures': [{'valid_from': '2025-07-04', 'reason': 'ratio_out_of_band'}]}) is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.\.venv39-citylearn-v3\Scripts\python.exe -B -m pytest -p no:cacheprovider -q tests/fresh_training/test_tariff_busbar.py -k "time_of_use or gate"`
Expected: FAIL.

- [ ] **Step 3: Implement** el rechazo en `energy_rate_ctm` y `tariff_crosscheck_gate(report: Mapping) -> bool`, y añadir la puerta a `gates`.

- [ ] **Step 4: Run tests to verify they pass**

Run: el comando del paso 2, más `tests/fresh_training/test_dataset_tariff.py` y `tests/fresh_training/test_dataset_bess_rule.py`.
Expected: todas aprobadas. `iquitos_v1` a `iquitos_v4` no se reconstruyen.

- [ ] **Step 5: Commit, si está autorizado**

`git add tools/dataset/build_fresh_campaign_dataset.py tests/fresh_training/test_tariff_busbar.py`; el constructor tiene cambios sin confirmar del Revisor A: pedir confirmación antes.
