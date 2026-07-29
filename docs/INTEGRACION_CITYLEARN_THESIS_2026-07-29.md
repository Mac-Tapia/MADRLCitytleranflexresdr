# Integración CityLearn → tesis (retener, no purgar)

**Fecha:** 2026-07-29  
**Repo:** `D:/MADRLCitytleranflexresdr`  
**Decisión del usuario:** **NO borrar** barrios upstream, challenges ni launchers `*_iquitos_training.ps1`; **integrarlos** en la elaboración de la tesis como evidencia de reproducibilidad / contexto metodológico / anexo técnico.  
**Canónicos:** `docs/Tesis_Doctoral_MADRL_CityLearn_Iquitos.docx`, `docs/Inforne_tesisV4_FINAL_REVISADO_50_EPISODIOS.docx`, `docs/tesis_capitulos/`, auditoría `docs/AUDITORIA_CITYLEARN_LIMPIEZA_2026-07-29.md`.

---

## 1. Qué se retuvo y por qué

| Bloque | Ruta(s) | ~Tamaño | Rol en tesis | Por qué retener |
|---|---|---:|---|---|
| Dataset empírico principal | `CityLearn/data/datasets/citylearn_iquitos_2023_2025/` | ~236 MB | Caso SEAI; Caps. 3–5; OE.1–OE.3 | Canónico (manifest + Word) |
| Barrios upstream | `quebec_neighborhood_*` (×2), `ca_alameda_county_neighborhood`, `tx_travis_county_neighborhood`, `vt_chittenden_county_neighborhood` | ~860 MB | Contexto benchmark CityLearn v2 / reproducibilidad del árbol del paquete | Distribución offline; contraste metodológico con Iquitos; **sin métricas de corrida MADRL en esta tesis** |
| Challenges CityLearn | `citylearn_challenge_2020_*`, `2021`, `2022_phase_*`, `2023_phase_*` | ~59 MB | Antecedente histórico de benchmarking comunitario; tests del submódulo (2022) | Literatura (Nweye et al.); integridad `pytest`; no resultados fantasma |
| Demo / BAEDA | `citylearn_three_phase_electrical_service_demo`, `baeda_3dem` | ~15 MB | Suite de tests del submódulo | KEEP_SUPPORT (auditoría) |
| Capa v3 + scripts | `CityLearn/citylearn/v3/`, `scripts/train_citylearn_v3_*.py` | — | Cap. 2/4; aporte Dec-POMDP/CTDE | Núcleo tesis |
| Notebook canónico | `examples_madrl_v3/madrl_citylearn_v3_tutorial.ipynb` | — | Caps. 3–4; protocolo 50 ep | Canónico |
| Launcher oficial | `launch_citylearn_v3_official_training.ps1` (+ monitor) | — | Procedimiento Cap. 3 / flujo Cap. 4 | Canónico local |
| Launchers Iquitos (legado) | `launch_citylearn_v3_iquitos_training.ps1`, `monitor_citylearn_v3_iquitos_training.ps1` | — | Reproducibilidad histórica / anexo operativo | Retenidos; no sustituyen al launcher *official* ni a Colab 50 ep |
| Config | `CityLearn/configs/citylearn_v3_madrl_training.yaml` | — | Hiperparámetros / schema | Canónico |

**Limpieza ya hecha (no revertida):** caches `__pycache__`/pytest, backups del notebook tutorial, `citylearn_iquitos_2023_2025_backup/` (~77 MB). Eso no afecta barrios/challenges/launchers.

---

## 2. Inventario de integración (clasificación)

Leyenda: **Ya** = citado en md/Word · **Ahora** = integrado en este pase · **Solo inv.** = mencón metodológica/anexo sin claim de resultados.

| Activo | Clasificación | Encaje tesis | Relación OE / Caps. |
|---|---|---|---|
| `citylearn_iquitos_2023_2025` | **Ya** | Dataset empírico | OE.1–3 · Cap. 3–5 |
| `citylearn/v3/`, reward, trainers | **Ya** | Propuesta / Dec-POMDP | Cap. 2, 4 |
| Tutorial v3 + Colab launcher | **Ya** | Procedimiento 50 ep | Cap. 3 §3.6, Cap. 4 |
| `launch_*_official_*.ps1` | **Ya** | Procedimiento local | Cap. 3–4 |
| Barrios Quebec/Alameda/Travis/Chittenden | **Ahora** | Árbol reproducible CityLearn v2; contraste climas/mercados vs SEAI aislado | Cap. 3 §3.4.6; anexo técnico; **no** Cap. 5 |
| Challenges 2020–2023 | **Ahora** | Contexto histórico de challenges; tests 2022 | Cap. 2 (literatura) + Cap. 3 §3.4.6; **no** Cap. 5 |
| Challenge 2022 / three_phase / baeda | **Ya** (tests) / **Ahora** (texto tesis) | Integridad del submódulo | Cap. 3 anexo / reproducibilidad |
| `*_iquitos_training.ps1` | **Ahora** | Launcher legado documentado | Cap. 4 §4.x launchers |
| Benchmarks v2 `baseline`/`hour_rbc` | **Ya** | Línea base sobre schema Iquitos | Cap. 3–5 |

---

## 3. Dónde se integró

| Artefacto | Cambio |
|---|---|
| `docs/tesis_capitulos/Capitulo_3_Metodologia.md` | Nueva §3.4.6: datasets usados vs disponibles en el árbol local |
| `docs/tesis_capitulos/Capitulo_4_Desarrollo_Propuesta.md` | Clarificación launchers official vs iquitos; árbol CityLearn retenido |
| `docs/tesis_capitulos/Capitulo_2_Marco_Teorico.md` | Nota breve: challenges/barrios como contexto del ecosistema CityLearn (sin resultados propios) |
| `docs/tesis_capitulos/00_INDICE.md` | Puntero al informe de integración |
| `docs/00_INDEX.md` | Enlace al informe |
| `docs/AUDITORIA_CITYLEARN_LIMPIEZA_2026-07-29.md` | Sección **Decisión: RETENER e INTEGRAR** |
| `docs/tesis_capitulos/AUDITORIA_CUMPLIMIENTO.md` | Addendum 2026-07-29 |
| Word canónico | Parche mínimo vía `tools/thesis/patch_citylearn_assets_integration_docx.py` (si aplica) |
| Este informe | Fuente de verdad del pase de integración |

---

## 4. Qué NO se claim-ea

- **No** hay resultados MADRL (KPIs, tablas Cap. 5, Shapiro/KW/MWU) sobre Quebec, Alameda, Travis, Chittenden ni challenges 2020–2023 en `outputs/` de esta tesis.
- **No** se afirma que se entrenaron los 4×3 escenarios fuera de Iquitos.
- Los barrios/challenges **no** sustituyen ni “validan externamente” las hipótesis HE/HG; solo documentan el ecosistema CityLearn embebido en el fork.
- El launcher `*_iquitos_training.ps1` **no** es la vía canónica de la corrida 50 episodios (esa es Colab + `colab_a100_official_launcher.py` / notebook tutorial).

---

## 5. Checklist de reproducción (ligero)

Ejecutado / verificable sin entrenamiento largo:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify_project_context.ps1

# Existencia de rutas retenidas (inventario)
.\.venv39-citylearn-v3\Scripts\python.exe -c "from pathlib import Path; r=Path('CityLearn/data/datasets');
names=['citylearn_iquitos_2023_2025','quebec_neighborhood_with_demand_response_set_points','quebec_neighborhood_without_demand_response_set_points','ca_alameda_county_neighborhood','tx_travis_county_neighborhood','vt_chittenden_county_neighborhood','citylearn_challenge_2022_phase_all','citylearn_challenge_2022_phase_all_plus_evs'];
print({n:(r/n).is_dir() for n in names})"

# Schema Iquitos listo para entrenamiento (smoke readiness)
.\.venv39-citylearn-v3\Scripts\python.exe CityLearn\scripts\check_citylearn_v3_training_ready.py --schema-path CityLearn\data\datasets\citylearn_iquitos_2023_2025\schema.json --scenario E1
```

Opcional (tests del submódulo; consume challenge 2022 / baeda / three_phase — **no** es corrida MADRL de tesis):

```powershell
cd CityLearn; ..\.venv39-citylearn-v3\Scripts\python.exe -m pytest tests -q --tb=no -x
```

**No** lanzar entrenamientos MADRL en barrios upstream salvo validación corta ya documentada.

---

## 6. Patch Word

- Script: `tools/thesis/patch_citylearn_assets_integration_docx.py`
- Informe JSON: `docs/CITYLEARN_ASSETS_INTEGRATION_PATCH_REPORT_2026-07-29.json`
- **Ejecutado 2026-07-29:** parche aplicado a ambos Word canónicos (`insert_heading` + 3 párrafos en Cap. III).
  - `docs/Tesis_Doctoral_MADRL_CityLearn_Iquitos.docx` (backup en `docs/_working/`)
  - `docs/Inforne_tesisV4_FINAL_REVISADO_50_EPISODIOS.docx` (backup en `docs/_working/`)
- Texto insertado (factual): árbol CityLearn retenido; rol de barrios/challenges/launchers; caso empírico = Iquitos 2023–2025 + MADRL v3.

---

## 7. Pendientes (coordinador)

1. Revisar Cap. III en Word (F9 TOC si aplica) tras el parche.
2. Medio plazo: LFS / descarga bajo demanda del `data/` grande **sin** borrar contenido científico.
3. No reabrir propuesta de purga de barrios/challenges/launchers iquitos sin nueva decisión explícita del usuario.
4. Opcional: `pytest` en CityLearn (challenge 2022 / baeda) como smoke de integridad del submódulo.
