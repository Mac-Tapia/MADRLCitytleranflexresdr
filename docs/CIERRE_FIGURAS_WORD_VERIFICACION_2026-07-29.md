# Cierre multicriterio real Drive 50 ep — 2026-07-29

**Script:** `scripts/regenerate_multicriteria_drive_50ep_closure.py`  
**Modo:** `--real-only` (sin relleno ilustrativo / sin curvas sintéticas)

## Qué se reemplazó

| Antes (inventado) | Ahora (Drive 50 ep) |
|---|---|
| `hybrid_real_c1c3_plus_illustrative` | `real_drive_50ep_c1c6` |
| C4–C6 de matriz metodológica §3.2 | C4 varianza episódica, C5 pasos a 90% asintota, C6 gap early–late desde `episode_summary.csv` |
| `learning_curves.png` sintéticas | Curvas reales `reward_mean` E1 (50 ep) |
| `degradation_bars.png` = C6 ilustrativo | Gap early–late real (título: Drive 50 ep) |
| Pareto con C3 real + contexto hybrid | Pareto C1–C3 desde `district_objectives_by_algorithm.csv` |

## Código tocado

- `uc3m/multicriteria/artifacts.py` — carga C4–C6 + curvas reales; flag `allow_illustrative_fill`
- `uc3m/multicriteria/pipeline.py` — no usa `_synthetic_learning_curves` en real-only
- `scripts/run_madrl_multicriteria_selection.py` — `--real-only`
- `scripts/regenerate_multicriteria_drive_50ep_closure.py` — regenera + parchea Word
- `tests/uc3m/test_madrl_multicriteria.py` — test real-only
- Validador integral: WARN hybrid solo si `hybrid_real|ilustrativ` (no “PV híbridos”)

## Word canónicos

- Media MC reemplazada por SHA (Tesis + Informe)
- Figura 5.8 Informe re-embebida (antes externa)
- Anclas evaluate_v2 **0,8805 / 0,8679** presentes
- Sin `hybrid_real_c1c3_plus_illustrative` en texto

## Validación

- `pytest …test_pipeline_real_only_drive_50ep_no_illustrative` → PASS
- `validate_integral_word_50ep_4madrl.py` → **0 FAIL** (CONDICIONAL por capas descriptivas TOPSIS ≠ OG; esperado)

## Cómo regenerar

```powershell
py -3.11 scripts/regenerate_multicriteria_drive_50ep_closure.py
# o solo artefactos:
py -3.11 scripts/run_madrl_multicriteria_selection.py --real-only --plots
```
