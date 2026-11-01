# Harness local de agentes y estado de adopción

Fecha: 2026-10-31. Ámbito: este repositorio. Estado integral: **parcial**, no aceptación científica ni despliegue productivo.

## Decisiones y límites

Una sola fuente canónica en `tools/skills/`, con registro, licencia y hashes. Codex y Claude descubren esa fuente mediante enlaces locales generados; no se modifica la configuración global ni se reinstala Superpowers. Los skills añaden procedimientos, no herramientas, permisos, créditos o inteligencia garantizada. No se contrata ningún servicio ni se configura un MCP remoto.

Selección tras consultar skills.sh y `npx skills find` para backend, frontend, despliegue y harness engineering. Se revisaron las fuentes GitHub y licencias MIT/Apache-2.0. Los contadores de instalaciones y estrellas son señales de búsqueda, no una garantía de seguridad. Revisar scripts y referencias antes de ejecutarlos; la instalación no equivale a validación de todos sus ejemplos.

| Área | Skills instalados | Uso y límite |
|---|---|---|
| Backend | fastapi-templates | Solo un cambio FastAPI aprobado; no migrar el panel actual por instalarlo |
| Arquitectura | architecture-patterns | Puertos/adaptadores y dominio; mantener el monolito modular |
| Frontend | frontend-design, webapp-testing | Diseño y pruebas reales de UI; instalar navegadores/dependencias solo si hace falta |
| Despliegue | docker-build-strategies, docker-compose-patterns | Contenedores solicitados; no nube de pago ni publicación automática |
| Harness | harness-engineering | Instrucciones, restricciones y checks específicos, no plantillas ciegas |
| Proyecto | madrl-agent-coordination, madrl-spec-conformance, madrl-experiment-evidence-audit, madrl-scientific-literature-audit | Contratos, evidencias y revisión independiente |

Docker publica guías Apache-2.0, pero esto no concede licencia a Docker Desktop ni implica aceptar sus condiciones comerciales. Los skills de Docker pueden usarse con Docker Engine/Moby y Compose abiertos; no se instala Desktop. Codex, Claude y Colab son clientes/servicios elegidos por el usuario, no componentes que se conviertan en open source por instalar skills. No se compra ni exige una suscripción nueva. El núcleo de entrenamiento sigue local/abierto; Colab es el destino opcional expresamente solicitado.

## Coordinación

Flujo: coordinador → implementador acotado → auditor independiente → verificación del coordinador principal. Cada encargo incluye requisito, entradas, archivos permitidos, salida y comando de aceptación. Un escritor por archivo; tareas dependientes no se ejecutan en paralelo. Compartir solo el contexto necesario y reutilizar trabajadores para correcciones. Ningún skill habilita delegación universal.

Claude tiene tres perfiles en `.claude/agents/`. El auditor solo dispone de lectura/búsqueda: no shell, escrituras ni MCP. Por ello informa evidencia suministrada y pide al principal ejecutar pruebas. El implementador conserva permisos normales, sin bypass; el coordinador no tiene herramientas de escritura ni shell. Codex utiliza las mismas instrucciones en AGENTS y skills con las herramientas efectivamente disponibles; no se afirma haber configurado roles nativos TOML ni nuevos modelos.

## Verificación y uso

Desde la raíz y con el entorno canónico activo:

```powershell
python tools/skills/validate_skills.py
python -m pytest tests/skills -q
powershell -ExecutionPolicy Bypass -File scripts/skills/register_local_skills.ps1
powershell -ExecutionPolicy Bypass -File scripts/skills/register_local_skills.ps1 -CheckOnly
```

Los enlaces son junctions locales Windows ignorados por Git. Tras clonar se regeneran; no son copias globales. La documentación oficial admite carpetas enlazadas en [Codex](https://developers.openai.com/codex/skills/) y [Claude](https://code.claude.com/docs/en/skills). Los [subagentes de Claude](https://code.claude.com/docs/en/sub-agents) permiten limitar herramientas. Aún se requiere comprobar el catálogo en una nueva sesión real de cada cliente; un check de rutas no prueba selección del modelo ni rendimiento.

## Riesgos y pendientes

- `.claude/settings.json` ya contenía un Stop hook que ejecuta `.claude/auto_save.sh`: agrega todo, cambia README y publica. No se instaló ni modificó ese hook. Riesgo alto de incluir trabajo concurrente no revisado; no usarlo como puerta de aceptación. Su desactivación o sustitución requiere decisión explícita del usuario.
- Los cuatro skills legados en `agent-skills/` quedan inventariados pero no promovidos, pendientes de licencia, comandos/rutas y duplicados globales. No mover el dataset skill homónimo de un global activo sin resolver esa colisión.
- Los dos MCP legados no son skills, no se arrancan y no forman parte de la ruta requerida. No se inspeccionan ni borran secretos.
- No se ejecutaron builds Docker ni pruebas Playwright por instalar instrucciones. Falta ensayo de descubrimiento/invocación en ambas aplicaciones y evaluación de eficiencia contra una línea base: éxito por tarea, hallazgos escapados, tiempo/tokens, conflictos y retrabajo.
- Persisten los pendientes científicos y de software de `specs/STATUS.md`; instalar skills no los cierra.

## Evidencia de esta instalación

- Siete skills de terceros y cuatro propios instalados; fuentes fijadas y licencias incluidas en `tools/skills/registry.yaml`.
- Revisión independiente encontró inventario unilateral y hashes opcionales. Se reprodujeron con cuatro pruebas rojas; se corrigieron exigiendo inventario no vacío, cobertura exacta, contraste de carpetas y enlaces y rechazo de entradas sobrantes sin borrado.
- `python -m pytest tests/skills tests/contract/test_spec_kit_consistency.py tests/integration/test_training_panel.py -q`: 12 pruebas aprobadas, sin omisiones.
- `python tools/skills/validate_skills.py --check-discovery`: OK para fuentes y 22 enlaces locales (11 por cliente).
- `powershell -ExecutionPolicy Bypass -File scripts/skills/register_local_skills.ps1 -CheckOnly`: OK en Windows PowerShell. Durante la prueba se detectó y corrigió una matriz JSON anidada por `@(...)` en PowerShell 5.1; se repitió el comando completo con resultado correcto.
- Ruff sobre validador y tests nuevos: sin hallazgos. Helper Playwright revisado, solo se ejecutó `--help`; no se arrancó ningún navegador o servicio por instalar skills.
- Se intentó instalar harness con el instalador oficial; la descarga del repositorio completo quedó detenida. Se canceló únicamente ese proceso y se recuperó el `SKILL.md` del commit fijado y su licencia por descarga selectiva, sin ejecutar código remoto.
- Suite general `python -m pytest`: **307 aprobadas, 15 advertencias, sin omisiones**, en 313.65 s. Advertencias: deprecaciones Matplotlib/Pyparsing y p-valor t no estimable en una prueba corta sin grados de libertad; no se silenciaron ni se consideran evidencia estadística de tesis.
- Se fijaron finales de línea LF únicamente en los once skills nuevos mediante `.gitattributes`, para que un checkout Windows no invalide sus hashes auditados. No se normalizaron conectores ni archivos heredados.

## Fundamento científico (APA, fuentes primarias)

Pineau et al. (2021) fundamentan registrar código, datos y protocolos reproducibles; se aplica aquí a procedencia, comandos y evidencia. Costea (2026) estudia evaluación MARL de energía en CityLearn; Charbonnier (2023) estudia coordinación de flexibilidad mediante MARL. Justifican separar método, evaluación y resultados, pero **no demuestran que estos skills aumenten el rendimiento de Codex/Claude ni validan los pesos exactos**. Son fuentes de investigación, no licencias de código redistribuido. Las fichas universitarias verifican tipo y autor; no se presupone indexación de tesis. JMLR es la fuente editorial del artículo; indexación por base específica queda sin nueva certificación.

- Costea, C. C. (2026). *Multi-Agent Reinforcement Learning Building Energy Optimization: Taxonomy and Experimental Evaluation in CityLearn* [Tesis de maestría, Politecnico di Torino]. https://webthesis.biblio.polito.it/40396/
- Charbonnier, F. V. J. (2023). *Multi-agent reinforcement learning for the coordination of residential energy flexibility* [Tesis doctoral, University of Oxford]. https://ora.ox.ac.uk/objects/uuid%3A4acf19ee-76b3-4e71-a424-259cd9e2d6f5
- Pineau, J., Vincent-Lamarre, P., Sinha, K., Larivière, V., Beygelzimer, A., d’Alché-Buc, F., Fox, E., & Larochelle, H. (2021). Improving reproducibility in machine learning research (A report from the NeurIPS 2019 reproducibility program). *Journal of Machine Learning Research, 22*(164), 1–20. https://www.jmlr.org/papers/v22/20-303.html
