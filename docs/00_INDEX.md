# Índice de documentación — MADRLCitytleranflexresdr

Punto de entrada a la documentación del proyecto. Para el contrato canónico
de dataset/entrenamiento/comparación, ver [`workflow_manifest.json`](workflow_manifest.json).

## Word canónicos (exactamente 2) y validez 50 ep Drive

**Regla dura:** no crear nuevos `.docx` en `docs/`. Toda mejora se aplica solo a estos dos.

- `Tesis_Doctoral_MADRL_CityLearn_Iquitos.docx` — **fuente de verdad**; Cap. V + KPIs Drive + Shapiro/no paramétricos.
- `Inforne_tesisV4_FINAL_REVISADO_50_EPISODIOS.docx` — informe final 50 episodios (TOC + Cap. 5 alineado a la tesis).
- Validez: corrida `madrl_v3_20260627_164047` — espejo `outputs/madrl_v3_20260627_164047/` + `outputs/_drive_madrl/kpi_recalc_20260728/` — Drive https://drive.google.com/drive/folders/1ihH6RqL2KpevfCQEUXj7PP1aS2QYssAX
- Detalle: [`CANON_WORD_Y_VALIDEZ_50EP_DRIVE_2026-07-29.md`](CANON_WORD_Y_VALIDEZ_50EP_DRIVE_2026-07-29.md)
- Capítulos MD: [`tesis_capitulos/00_INDICE.md`](tesis_capitulos/00_INDICE.md) · Cap. 5 [`tesis_capitulos/Capitulo_5_Resultados.md`](tesis_capitulos/Capitulo_5_Resultados.md)
- Limpieza raíz 2026-07-29 (política DELETE no vinculados, sin `_archive`): [`AUDITORIA_RAIZ_PROYECTO_2026-07-29.md`](AUDITORIA_RAIZ_PROYECTO_2026-07-29.md)
- Auditoría integral + readiness 4 MADRL 2026-07-29: [`AUDITORIA_INTEGRAL_PROYECTO_2026-07-29.md`](AUDITORIA_INTEGRAL_PROYECTO_2026-07-29.md)
- CityLearn: retención e integración en tesis (barrios/challenges/launchers **no** se borran): [`INTEGRACION_CITYLEARN_THESIS_2026-07-29.md`](INTEGRACION_CITYLEARN_THESIS_2026-07-29.md) · auditoría [`AUDITORIA_CITYLEARN_LIMPIEZA_2026-07-29.md`](AUDITORIA_CITYLEARN_LIMPIEZA_2026-07-29.md)
- Limpieza `tools/` 2026-07-29 (114 scripts activos, cero `_archive`): [`AUDITORIA_TOOLS_2026-07-29.md`](AUDITORIA_TOOLS_2026-07-29.md)

## Manuales operativos

- `MANUAL_EJECUCION_DESDE_CERO_COLAB_A100.md` — guia Colab A100 / VS Code.
- `LISTA_EJECUCION_COLAB_A100.md` — checklist corto.
- `MANUAL_INSTALACION_DEPENDENCIAS.md` — dependencias Python 3.9 / Windows / AWS.

## architecture/
Diagramas y documentos de arquitectura (CityLearn v3 + MADRL). Documento principal de defensa: `ARQUITECTURA_PROYECTO_DEFENSA.md`. Ver listado en carpeta.

## audits/
Auditorías de dataset, DER/EV y entrenamiento. Ver listado en carpeta.

## decisions/
Justificaciones de diseño experimental y reorganización. Ver listado en carpeta.

## thesis/
- `APORTES_SIMULACION_CITYLEARN_MADRL_TESIS.md`
- `Resultados_Preliminares-GD-Iquitos_V3 (2).xlsx`

> No hay Word en `thesis/`. Obsoletos legacy eliminados (política 2026-07-29: DELETE, no retención en `_archive`).

## contributions/
Cambios a submódulos con `CHANGES.md` y `bibliografia.bib` por componente.
