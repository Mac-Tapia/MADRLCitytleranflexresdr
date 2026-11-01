# Thesis Evidence and Local Agents Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generar evidencia de tesis exclusivamente desde manifiestos aceptados y establecer skills/agentes locales, abiertos y auditables sin conectores cerrados.

**Architecture:** La tesis consume una vista de solo lectura de `EvidenceManifest`; nunca consulta arbitrariamente la carpeta más reciente. Los skills son instrucciones locales versionadas con permisos mínimos. MCP y credenciales se separan de los skills y ningún servicio cerrado forma parte del camino requerido.

**Tech Stack:** Python 3.9, python-docx, PyMuPDF/LibreOffice según disponibilidad abierta, pytest, Markdown, BibTeX/APA, PowerShell, Zotero local opcional.

**Spec:** `docs/superpowers/specs/2026-10-31-modernizacion-integral-open-source-design.md`

**Spec Kit slices covered:** `SPEC-006` and `SPEC-007`.

## Conciliación de estado — 2026-10-31

Ver [SPEC-000–010 y pendientes](../../../specs/STATUS.md). Normalizar skills
y roles no equivale a promover evidencia de tesis. Instalar instrucciones o
validar su estructura no acredita mejor rendimiento ni cierra APA, render,
§3.1.3 o experimentos. Tareas sin entregables/verificación siguen abiertas;
RED y commits históricos no se marcan retrospectivamente sin evidencia.

El corte de skills se materializó en [SPEC-007](../../../specs/007-local-agent-harness/spec.md): siete skills externos y cuatro propios, registro con hashes/licencias, validación bidireccional, perfiles Claude y descubrimiento local. Nombres propios con prefijo `madrl-` para delimitar el ámbito; sustituyen las rutas genéricas previstas en Task 6, sin instalar duplicados globales. Nueve pruebas de skills y tres de SPEC/panel pasan en este corte. Invocación real en ambos clientes, eficiencia medida, migración de cuatro skills heredados (no cinco), decisión del hook Stop y la puerta integral de tesis siguen pendientes.

## Global Constraints

- Mantener exactamente los dos DOCX canónicos declarados en `docs/workflow_manifest.json`; no crear terceros permanentes.
- La coordinación multiobjetivo debe quedar integrada en §3.1.3, sin duplicación lateral.
- No actualizar cifras o conclusiones con runs parciales o de otra política.
- Cada cita debe tener fuente verificable; no atribuir pesos exactos a literatura que solo respalda el método.
- Skills específicos únicamente en `tools/skills/`; ningún duplicado global activo.
- Google Drive, NotebookLM, Scite, W&B o servicios de suscripción quedan fuera del flujo requerido.

## Review Focus

- DOCX abre pero la inserción quedó fuera de §3.1.3: rechazar.
- Referencia citada en cuerpo pero ausente en bibliografía: rechazar.
- Tabla usa run más reciente en vez de manifiesto promovido: rechazar.
- Skill puede escribir fuera del repositorio sin declararlo: rechazar.
- Perfil de navegador o token permanece en árbol rastreado: bloquear aceptación.

---

### Task 1: Crear el registro de evidencia promovida

**Files:**
- Create: `uc3m/application/thesis/__init__.py`
- Create: `uc3m/application/thesis/evidence_registry.py`
- Test: `tests/unit/application/thesis/test_evidence_registry.py`
- Create: `docs/thesis/evidence_registry.yaml`

**Interfaces:**
- Consumes: `EvidenceManifest` del Plan 3.
- Produces: `PromotedEvidence`, `EvidenceRegistry`, `load_promoted_evidence(...)`.

- [ ] **Step 1: Escribir pruebas fallidas de promoción**

Assertions: solo `VERIFIED`; hash válido; política y dataset explícitos; una evidencia no puede ocupar dos roles incompatibles; run de pesos antiguos queda histórico.

- [ ] **Step 2: Implementar interfaces**

```python
@dataclass(frozen=True)
class PromotedEvidence:
    evidence_id: str
    role: str
    manifest_path: Path
    manifest_sha256: str

class EvidenceRegistry:
    @classmethod
    def from_yaml(cls, path: Path) -> "EvidenceRegistry": ...
    def resolve(self, role: str) -> EvidenceManifest: ...
```

- [ ] **Step 3: Ejecutar tests**

Expected: PASS; ningún fallback a “directorio más reciente”.

- [ ] **Step 4: Commit**

```powershell
git add uc3m/application/thesis docs/thesis/evidence_registry.yaml tests/unit/application/thesis/test_evidence_registry.py
git commit -m "feat: add promoted thesis evidence registry"
```

### Task 2: Generar una vista de tesis multiobjetivo trazable

**Files:**
- Create: `uc3m/application/thesis/multiobjective_view.py`
- Create: `tools/thesis/build_multiobjective_evidence.py`
- Test: `tests/unit/application/thesis/test_multiobjective_view.py`
- Produce: `outputs/thesis_objective_evidence/multiobjective_evidence.json`

**Interfaces:**
- Consumes: `EvidenceRegistry`, evaluación Pareto y catálogo canónico.
- Produces: `build_multiobjective_view(registry, catalog) -> dict[str, object]`.

- [ ] **Step 1: Escribir pruebas fallidas**

Assertions: pesos, método, tarifa, semillas, KPI y Pareto incluyen procedencia; falta de campaña nueva no reutiliza resultados antiguos.

- [ ] **Step 2: Implementar vista pura y CLI**

- [ ] **Step 3: Ejecutar contra fixtures y evidencia promovida**

Expected: si la campaña nueva no existe, estado `pending_retraining`; no inventa cifras.

- [ ] **Step 4: Commit**

```powershell
git add uc3m/application/thesis/multiobjective_view.py tools/thesis/build_multiobjective_evidence.py tests/unit/application/thesis/test_multiobjective_view.py
git commit -m "feat: build traceable multiobjective thesis evidence"
```

### Task 3: Consolidar §3.1.3 y eliminar contradicciones activas

**Files:**
- Modify: `docs/tesis_capitulos/Capitulo_3_Metodologia.md`
- Modify: `tools/thesis/patch_cap3_multiobjective_hierarchy_docx.py`
- Modify: `tools/thesis/thesis_doctoral_sections.py`
- Test: `tests/thesis/test_cap313_multiobjective_consistency.py`
- Modify: `docs/Tesis_Doctoral_MADRL_CityLearn_Iquitos.docx`
- Modify: `docs/Inforne_tesisV4_FINAL_REVISADO_50_EPISODIOS.docx`

**Interfaces:**
- Consumes: `multiobjective_evidence.json` y catálogo.
- Produces: texto único de §3.1.3 y auditoría de pesos/documentos.

- [ ] **Step 1: Respaldar ambos DOCX en directorio temporal recuperable**

No crear copias canónicas nuevas ni versionarlas.

- [ ] **Step 2: Escribir prueba de consistencia antes de parchear**

Assertions: nueva matriz aparece en §3.1.3; terminología compensatoria; pesos antiguos no aparecen como política activa; resultados de 50 episodios conservan etiqueta histórica; no existe §3.1.4 duplicada sobre el mismo contenido.

- [ ] **Step 3: Actualizar fuentes Markdown y generadores**

No codificar cifras experimentales en el generador; leer la vista promovida.

- [ ] **Step 4: Parchear los dos DOCX canónicos**

Insertar por ancla verificada; `document.add_paragraph()` al final no es aceptación.

- [ ] **Step 5: Reabrir y verificar estructura**

Run: `python -m pytest tests/thesis/test_cap313_multiobjective_consistency.py -v`

Expected: PASS para ambos documentos.

- [ ] **Step 6: Renderizar PDF/imágenes y revisar visualmente páginas afectadas**

Expected: estilos, tablas, referencias y saltos intactos.

- [ ] **Step 7: Commit**

```powershell
git add docs/tesis_capitulos/Capitulo_3_Metodologia.md tools/thesis/patch_cap3_multiobjective_hierarchy_docx.py tools/thesis/thesis_doctoral_sections.py tests/thesis/test_cap313_multiobjective_consistency.py docs/Tesis_Doctoral_MADRL_CityLearn_Iquitos.docx docs/Inforne_tesisV4_FINAL_REVISADO_50_EPISODIOS.docx
git commit -m "docs: align thesis multiobjective methodology and evidence"
```

### Task 4: Completar bibliografía APA verificable

**Files:**
- Modify: `docs/tesis_capitulos/Referencias_APA.md`
- Modify: `tools/thesis/thesis_references_apa.py`
- Test: `tests/thesis/test_apa_reference_integrity.py`
- Create: `docs/research/multiobjective_sources.yaml`

**Interfaces:**
- Produces: registro autor–año–DOI/URL–tipo–licencia/acceso y referencias deduplicadas.

- [ ] **Step 1: Escribir pruebas de autor-año y DOI**

Cubrir Felten 2023, Yeh 2023, Kreuzberger 2023, Liu 2025, Koruturk 2026, Parnas 1972 y Jiménez Perdomo/González Escobar 2024.

- [ ] **Step 2: Implementar registro estructurado y verificación**

No requerir Scite ni suscripción; usar DOI/URLs primarias y biblioteca Zotero local opcional.

- [ ] **Step 3: Regenerar y contar referencias**

Expected: conteo ejecutado coincide con texto; cuerpo no tiene citas huérfanas.

- [ ] **Step 4: Verificar DOCX y render**

- [ ] **Step 5: Commit**

```powershell
git add docs/tesis_capitulos/Referencias_APA.md docs/research/multiobjective_sources.yaml tools/thesis/thesis_references_apa.py tests/thesis/test_apa_reference_integrity.py
git commit -m "docs: verify open multiobjective thesis references"
```

### Task 5: Inventariar y normalizar skills locales

**Files:**
- Create: `tools/skills/registry.yaml`
- Create: `tools/skills/README.md`
- Create: `tools/skills/validate_skills.py`
- Test: `tests/skills/test_skill_registry.py`
- Read: `agent-skills/**`

**Interfaces:**
- Produces: `SkillRecord`, `validate_skill(path: Path) -> list[str]`.

- [ ] **Step 1: Inventariar sin mover**

Registrar cinco skills heredados, los dos directorios MCP actuales y cualquier duplicado global; no leer secretos.

- [ ] **Step 2: Escribir prueba de contrato `SKILL.md`**

Campos: nombre, finalidad, licencia, entradas, salidas, paths autorizados, herramientas, verificación, fuentes científicas y versión.

- [ ] **Step 3: Implementar validador y registro**

Los directorios MCP sin `SKILL.md` se clasifican `connector`, no skill válido.

- [ ] **Step 4: Ejecutar inventario**

Expected: estado actual reporta incumplimientos sin corregirlos silenciosamente.

- [ ] **Step 5: Commit**

```powershell
git add tools/skills/registry.yaml tools/skills/README.md tools/skills/validate_skills.py tests/skills/test_skill_registry.py
git commit -m "chore: add local skill governance"
```

### Task 6: Crear tres skills propios y abiertos

**Files:**
- Create: `tools/skills/scientific-literature-audit/SKILL.md`
- Create: `tools/skills/experiment-evidence-audit/SKILL.md`
- Create: `tools/skills/spec-conformance/SKILL.md`
- Test: `tests/skills/test_project_skills.py`

**Interfaces:**
- Produces: skills locales que consumen fuentes primarias, manifiestos y specs; no ejecutan servicios cerrados.

- [ ] **Step 1: Escribir pruebas fallidas de permisos y rutas**

Assert: ningún skill referencia `%USERPROFILE%/.agents/skills`, Scite, NotebookLM, Google Drive o W&B; comandos son relativos al repo.

- [ ] **Step 2: Implementar `scientific-literature-audit`**

Salida: matriz de fuente, DOI, indexación, diseño, aplicabilidad, límites y cita APA.

- [ ] **Step 3: Implementar `experiment-evidence-audit`**

Salida: validación de hashes, política, dataset, semillas, KPI y estado de promoción.

- [ ] **Step 4: Implementar `spec-conformance`**

Salida: cobertura requisito–tarea–prueba–evidencia y gaps.

- [ ] **Step 5: Ejecutar pruebas**

- [ ] **Step 6: Commit**

```powershell
git add tools/skills/scientific-literature-audit tools/skills/experiment-evidence-audit tools/skills/spec-conformance tests/skills/test_project_skills.py
git commit -m "feat: add audited open source project skills"
```

### Task 7: Migrar skills heredados de forma recuperable

**Files:**
- Move after validation: `agent-skills/<name>` → `tools/skills/<name>`
- Modify: references discovered by `rg`
- Modify: `tools/skills/registry.yaml`
- Test: `tests/skills/test_migrated_skills.py`

**Interfaces:**
- Consumes: inventario de Task 5.
- Produces: una ubicación canónica y sin duplicados.

- [ ] **Step 1: Clasificar cada skill como promover, fusionar, rechazar o bloquear**

No mover uno bloqueado por licencia o contenido desconocido.

- [ ] **Step 2: Añadir o corregir `SKILL.md` antes del movimiento**

- [ ] **Step 3: Mover solo los promovidos y actualizar referencias**

Usar una operación recuperable y revisión de diff; preservar historial Git.

- [ ] **Step 4: Verificar ausencia de duplicados activos**

- [ ] **Step 5: Commit por skill**

### Task 8: Separar MCP locales y retirar servicios cerrados del flujo requerido

**Files:**
- Create: `tools/connectors/README.md`
- Create: `tools/connectors/registry.yaml`
- Modify: `.cursor/mcp.json` if present
- Modify: `tools/README.md`
- Modify: `.gitignore`
- Test: `tests/connectors/test_connector_registry.py`

**Interfaces:**
- Produces: registro con `required`, `optional_legacy`, `rejected`, licencia cliente y tipo de backend.

- [ ] **Step 1: Escribir prueba que bloquea backend cerrado requerido**

- [ ] **Step 2: Clasificar Google Drive y NotebookLM como `optional_legacy` o `rejected`**

No borrar evidencia ni credenciales del usuario; retirar autoinicio y dependencia canónica.

- [ ] **Step 3: Mover el estado de navegador fuera del árbol o documentar bloqueo**

Antes de mover, resolver ruta absoluta y comprobar que el destino es un directorio local específico; nunca tocar perfiles generales del navegador.

- [ ] **Step 4: Verificar flujo sin MCP**

Expected: tests, especificaciones, entrenamiento local y generación de evidencia no los requieren.

- [ ] **Step 5: Commit**

### Task 9: Crear puerta final de tesis y agentes

**Files:**
- Create: `scripts/quality/run_thesis_agent_gates.ps1`
- Create: `data/audits/thesis_agent_acceptance.json`
- Create: `docs/audits/INFORME_VALIDACION_TESIS_Y_AGENTES_OPEN_SOURCE.md`
- Test: `tests/acceptance/test_thesis_agent_acceptance.py`

**Interfaces:**
- Produces: estados separados de documento, bibliografía, evidencia, skills, conectores y seguridad.

- [ ] **Step 1: Escribir prueba de agregación sin falsos completados**

- [ ] **Step 2: Implementar puerta local**

Orden: evidencia → coherencia §3.1.3 → APA → DOCX estructural → render → skills → conectores → secretos.

- [ ] **Step 3: Ejecutar**

Run: `powershell -ExecutionPolicy Bypass -File scripts/quality/run_thesis_agent_gates.ps1`

Expected: exit code `0` solo si todas las puertas críticas pasan; campaña experimental pendiente se reporta como pendiente y evita conclusiones nuevas.

- [ ] **Step 4: Commit**

```powershell
git add scripts/quality/run_thesis_agent_gates.ps1 data/audits/thesis_agent_acceptance.json docs/audits/INFORME_VALIDACION_TESIS_Y_AGENTES_OPEN_SOURCE.md tests/acceptance/test_thesis_agent_acceptance.py
git commit -m "test: gate thesis evidence and local agents"
```

