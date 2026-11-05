# I13: revisión semántica compartida entre Revisor A y Revisor B (corte 2026-11-02)

Esta carpeta ejecuta la tarea I13 de [remediacion_integrada.md](../../plans/remediacion_integrada.md): revisar cada archivo propio hasta el final, con rol, consumidores, hallazgos y pruebas. La revisión se reparte entre dos agentes, de modo que **ninguno revisa lo que escribió**. Sustituye a la propuesta de lotes de la sección 4 del [addendum](../addendum_auditoria_20261101/README.md), que asignaba los cinco lotes solo al Revisor A.

## Reparto

| Regla | Revisor |
|---|---|
| Archivo escrito por el Revisor A en este corte (skill instalado, `registry.yaml`, `.gitattributes`, plan integrado, `AGENT_HARNESS.md`) | Revisor B |
| Archivo con cambios sin publicar (escritos por el Revisor B en I00–I15) | Revisor A |
| Archivo limpio de L1 (`uc3m/`, `configs/`), L3 (`tests/`) o L5 (raíz, `deploy/`, `governance/`, `examples_madrl_v3/`, `.github/`, `.claude/`) | Revisor A |
| Archivo limpio de L2 (`scripts/`, `tools/`) o L4 (`docs/`, `specs/`) | Revisor B |

Quedan fuera las dependencias protegidas (`CityLearn/`, `external/`, submódulos), `docs/audits/` y los datos (`data/`, `outputs/`, `results/`). Para revisarlas hace falta añadir un lote propio por decisión explícita.

Corte inicial:

| Revisor | Archivos | Líneas | Detalle |
|---|---:|---:|---|
| Revisor A | 343 | 47.966 | L1 122, L2 13, L3 138, L4 7, L5 63 |
| Revisor B | 333 | 82.565 | L2 226 (53 son skills de terceros), L4 106, L5 1 |

## Archivos y quién los escribe

- `build_lots.py`: regenera los dos registros desde `git ls-files` y `git status`. Si un archivo no ha cambiado su SHA-256, conserva lo ya revisado. Si cambió, su revisión vuelve a `pendiente`.
- `ledger_revisor_a.csv`: lo escribe solo Revisor A.
- `ledger_revisor_b.csv`: lo escribe solo Revisor B.
- `hallazgos_revisor_a.md` y `hallazgos_revisor_b.md`: detalle de cada hallazgo. Cada agente escribe solo el suyo.

Ejecutar desde la raíz, tras la guarda de contexto:

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe -B -X utf8 docs/audits/revision_semantica_20261102/build_lots.py
```

## Cómo se revisa un archivo

1. Leerlo completo y comprobar que el SHA-256 coincide con el del registro. Si no coincide, regenerar antes de seguir.
2. Rellenar en el registro:
   - `rol`: qué hace, en una frase.
   - `consumidores`: quién lo importa, ejecuta o cita, buscando también usos dinámicos y manuales.
   - `hallazgos`: IDs `R-<A|B>-NNN`, o `ninguno`.
   - `pruebas`: qué tests lo cubren y si comprueban comportamiento.
   - `estado_revision`: `revisado`, `revisado_con_hallazgos`, `bloqueado` (por ejemplo, contenido sensible que no se abre) o `fuera_de_alcance`, con su motivo.
   - `revisado_utc`.
3. Cada hallazgo se anota en el archivo de hallazgos del revisor con ubicación, evidencia, impacto, tarea I00–I18 que lo absorbe y criterio de cierre. **El revisor no corrige**: lo corrige la tarea dueña del archivo, siguiendo el plan.
4. Un hallazgo sobre un archivo en curso se entrega a su ejecutor por el traspaso o por mensaje, para que no se pierda entre cortes.

## Orden recomendado

- **Revisor A:**
  1. Archivos limpios de L1 y L5. No dependen del trabajo en curso.
  2. Los cambios del Revisor B, tarea por tarea, cuando su acta tenga `acceptance.json`. Esto se hace a la vez que la auditoría cruzada y repitiendo `../addendum_auditoria_20261101/reproductions.py`.
  3. L3.
- **Revisor B:**
  1. Lo escrito por el Revisor A: skill instalado, generador del plan y addendum.
  2. L2 y L4. En L2 conviene priorizar los 27 scripts obsoletos y los 16 por decidir, que alimentan I14.

## Cierre

I13 se cierra cuando:

- ambos registros están sin `pendiente` en un corte con hashes estables;
- cada hallazgo está asignado a una tarea o cerrado con evidencia;
- el otro agente ha muestreado al menos un 10 % de cada registro y ha repetido la revisión de esos archivos sin discrepancias que no estén explicadas.

Leer un archivo hasta el final de forma automática no cuenta como revisión semántica.
