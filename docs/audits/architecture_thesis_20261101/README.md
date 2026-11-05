# Auditoría de arquitectura y PT — 2026-11-01

Dictamen: **parcial / no conforme para afirmar completitud o aceptación científica**. La auditoría conserva el proyecto y entrega evidencia y criterios de cierre; no implementa las correcciones.

- [Informe principal](informe.md): árbol, conservación funcional, 23 hallazgos, correspondencia con PT, tupla y fuentes académicas.
- [Verificación final](validation.md): comando, contadores reales de pruebas y limitaciones.
- [Árbol por carpetas](tree.txt), [revisión de carpetas](folder_review.csv) e [inventario de archivos con hashes](files.csv).
- [Módulos](modules.csv), [importaciones](imports.csv), [hallazgos](findings.csv) y [rutas anteriores/traslados exactos](migration_paths.json).
- [Texto completo extraído del PT](PT_TAPIA_ZAMBRANO.extracted.txt) y [hash del Word original](thesis.json). Los identificadores P0000 son párrafos/celdas, no páginas.
- [Contrato del simulador medido](runtime_probe.json), [comparación de interfaces y datasets](interface_probe.json), [prueba de promoción incorrecta](promotion_probe.json), [horizonte y KPI diarios](horizon_probe.json), [modo ilustrativo heredado](legacy_default_probe.json).
- [Aceptación de layout](layout/repository_layout_acceptance.json), [comandos y códigos](commands.json), [JUnit](pytest.xml), [log de pruebas](pytest.log), [fallos](test_failures.json) y [deriva de fuentes](source_drift.json).
- [Manifiesto de integridad de esta entrega](artifact_manifest.json). Sus hashes prueban la integridad del paquete de auditoría; no son aceptación de un modelo.

`collect.py`, `probe.py`, `interface_probe.py`, `promotion_probe.py`, `horizon_probe.py`, `evidence.py` y `finalize.py` son helpers reproducibles de esta auditoría. Ejecutarlos solo desde la raíz verificada, con el entorno canónico. No ejecutan la campaña; las campañas sintéticas de las pruebas de límites se crean en temporales. Los comandos Git de `evidence.py` son de lectura y requieren la guarda previa indicada en AGENTS.md.

Los inventarios excluyen dependencias, entorno, cachés, conectores y auditorías previas según las fronteras explícitas. No se afirma lectura semántica exhaustiva de cada línea ni certificación de todos los binarios/filas de datos.
