# SPEC-010 — Panel local de entrenamiento

Alcance aprobado por la petición de continuar backend, orquestador y frontend
sin consultas por tarea. Decisión de implementación: panel de solo lectura,
Python estándar, HTML/JS sin CDN, únicamente 127.0.0.1. Se conserva la demo de
inferencia Streamlit existente sin alterarla.

Requisitos: listar corridas mediante evidence.json; comprobar hashes antes de
mostrar evidencia verificada; marcar manifiestos ilegibles como inválidos;
no servir archivos arbitrarios; no ejecutar entrenamientos desde HTTP; no
exponer rutas personales ni errores internos. No inferir aceptación física,
estadística o del modelo por status=verified: solo integridad de esta corrida.

Alternativas: extender Streamlit requeriría instalarlo en el entorno actual;
React introduciría una segunda cadena de construcción. Se elige biblioteca
estándar para un monitor operativo pequeño, no una plataforma de producción.

Plan/tareas: prueba HTTP con servidor real en puerto efímero → servicio de
lectura/validación → rutas GET / y /api/runs → frontend con textContent →
prueba de navegación local. La CLI sigue siendo el único mando de ejecución.

Sustento: las tesis de Charbonnier (2023),
https://doi.org/10.5287/ora-ovzyxredj, y Costea (2026),
https://webthesis.biblio.polito.it/40396/, requieren distinguir métricas y
comparaciones. Charbonnier et al. (2024), Applied Energy, 377,
https://doi.org/10.1016/j.apenergy.2024.124406, estudian coordinación MARL.
La elección del servidor/UI es una decisión de ingeniería local, no una
arquitectura prescrita por estas fuentes.
