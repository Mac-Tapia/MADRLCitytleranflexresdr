# ADR — Almacén local y seguimiento

Estado: adoptado para la orquestación modular local. Se utiliza el almacén
atómico existente y manifests SHA-256. No se incorporan DVC, MLflow, cuentas,
servicios externos ni suscripciones como requisito operativo.

Motivo: ya existe una única máquina y estructura de corridas. Introducir
simultáneamente catálogo, tracking y almacenamiento remotos añade mecanismos
sin resolver la prioridad actual: persistencia y recuperación verificables.
Las pruebas de escritura real, interrupción durante replace, lectura posterior
y modificación de bytes justifican la opción simple para este alcance.

Desviación explícita del plan: no se instalan tres herramientas únicamente
para descartarlas; se aplaza el spike comparativo hasta necesitar búsqueda
multiusuario o restauración entre máquinas. No se atribuyen resultados de
rendimiento a herramientas que no se ejecutaron.

Limitaciones: los archivos permanecen en disco local; hashes no sustituyen
backups externos, retención o recuperación ante pérdida de la unidad. No se
declara preparación de producción ni recuperación de desastre.
