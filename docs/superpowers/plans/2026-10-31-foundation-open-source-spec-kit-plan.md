# Open Source Foundation and Spec Kit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Crear una línea base revisable, una constitución Spec Kit y puertas automáticas que impidan dependencias cerradas, licencias desconocidas y secretos versionados.

**Architecture:** Las reglas de gobierno permanecen fuera del dominio energético y se ejecutan como herramientas locales deterministas. Spec Kit se inicializa en una rama o worktree aislado y sus archivos se revisan antes de mezclarse con el árbol activo.

**Tech Stack:** Python 3.9 estándar, PyYAML, pytest, PowerShell, Spec Kit MIT, CycloneDX opcional solo si su licencia y compatibilidad se verifican.

**Spec:** `docs/superpowers/specs/2026-10-31-modernizacion-integral-open-source-design.md`

**Spec Kit slices covered:** `SPEC-000` and `SPEC-001`.

## Global Constraints

- No ejecutar `specify init --force` sobre el árbol sucio actual.
- El inventario inicial es de solo lectura y preserva los 43 cambios versionados y 183 no versionados detectados.
- No borrar Google Drive/NotebookLM existentes; retirarlos únicamente del flujo requerido y aislar sus secretos.
- Solo herramientas locales y abiertas; ningún control depende exclusivamente de un servicio alojado.
- Toda salida automática debe ser JSON estable y Markdown legible.

## Review Focus

- Licencia `null`, `NOASSERTION` o texto ambiguo: estado bloqueado.
- Submódulo con remoto propio pero sin licencia local: no inferir licencia del upstream.
- Referencia histórica a Drive/NotebookLM: permitir documentación histórica, bloquear dependencia requerida.
- Archivo de credenciales ignorado pero ya rastreado: reportar crítico.
- Árbol sucio: registrar, no alterar ni ocultar.

---

### Task 1: Capturar la línea base sin modificarla

**Files:**
- Create: `tools/ops/capture_modernization_baseline.py`
- Test: `tests/ops/test_capture_modernization_baseline.py`
- Produce: `data/audits/modernization_baseline.json`

**Interfaces:**
- Consumes: raíz del repositorio y comandos Git de solo lectura.
- Produces: `capture_baseline(project_root: Path) -> dict[str, object]`.

- [ ] **Step 1: Escribir la prueba fallida**

Assert: incluye raíz resuelta, origin, branch, cambios por categoría, commits de submódulos y hashes de archivos canónicos sin incluir contenido de secretos.

- [ ] **Step 2: Verificar que falle**

Run: `python -m pytest tests/ops/test_capture_modernization_baseline.py -v`

Expected: FAIL por módulo ausente.

- [ ] **Step 3: Implementar `capture_baseline(project_root: Path) -> dict[str, object]`**

El comando debe fallar si la raíz no coincide con `D:/MADRLCitytleranflexresdr` o el origin esperado.

- [ ] **Step 4: Ejecutar prueba y generar manifiesto**

Run: `python tools/ops/capture_modernization_baseline.py --output data/audits/modernization_baseline.json`

Expected: JSON válido; no modifica el estado Git.

- [ ] **Step 5: Commit**

```powershell
git add tools/ops/capture_modernization_baseline.py tests/ops/test_capture_modernization_baseline.py data/audits/modernization_baseline.json
git commit -m "chore: capture modernization baseline"
```

### Task 2: Inicializar Spec Kit en un worktree revisable

**Files:**
- Create: `.specify/memory/constitution.md`
- Create: `specs/000-foundation/spec.md`
- Create: `specs/000-foundation/plan.md`
- Create: `specs/000-foundation/tasks.md`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: diseño aprobado y `modernization_baseline.json`.
- Produces: constitución con los diez principios del diseño.

- [ ] **Step 1: Crear un worktree mediante `superpowers:using-git-worktrees`**

Expected: ruta aislada, rama `codex/modernization-foundation`, mismo commit base.

- [ ] **Step 2: Instalar Spec Kit en un entorno de tooling separado**

Run: `uv tool install specify-cli`

Expected: herramienta disponible sin modificar `.venv39-citylearn-v3`.

- [ ] **Step 3: Inicializar y revisar el diff generado**

Run: `specify init --here --force --integration codex`

Expected: solo rutas administradas por Spec Kit; ningún archivo de aplicación reemplazado sin revisión.

- [ ] **Step 4: Escribir la constitución y SPEC-000**

Copiar exactamente las restricciones aprobadas de la especificación de diseño; no inventar métricas.

- [ ] **Step 5: Ejecutar análisis de consistencia de Spec Kit**

Expected: constitución, spec, plan y tasks no se contradicen.

- [ ] **Step 6: Commit**

```powershell
git add .specify specs/000-foundation .gitignore
git commit -m "chore: initialize open source spec-driven workflow"
```

### Task 3: Definir la política de software abierto

**Files:**
- Create: `governance/open_source_policy.yaml`
- Create: `uc3m/governance/__init__.py`
- Create: `uc3m/governance/open_source.py`
- Test: `tests/unit/governance/test_open_source_policy.py`

**Interfaces:**
- Produces: `DependencyRecord`, `PolicyDecision`, `OpenSourcePolicy.evaluate(record) -> PolicyDecision`.

- [ ] **Step 1: Escribir pruebas fallidas para licencias admitidas y bloqueadas**

Assert: MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause y GPL/AGPL compatibles son evaluables; `null`, `NOASSERTION`, `LicenseRef-Proprietary`, pago requerido y SaaS requerido quedan bloqueados.

- [ ] **Step 2: Verificar FAIL**

Run: `python -m pytest tests/unit/governance/test_open_source_policy.py -v`

- [ ] **Step 3: Implementar los tipos y el evaluador**

Signatures:

```python
@dataclass(frozen=True)
class DependencyRecord: ...

@dataclass(frozen=True)
class PolicyDecision: ...

class OpenSourcePolicy:
    @classmethod
    def from_yaml(cls, path: Path) -> "OpenSourcePolicy": ...
    def evaluate(self, record: DependencyRecord) -> PolicyDecision: ...
```

- [ ] **Step 4: Ejecutar pruebas**

Expected: PASS; una licencia desconocida nunca se promueve automáticamente.

- [ ] **Step 5: Commit**

```powershell
git add governance/open_source_policy.yaml uc3m/governance tests/unit/governance/test_open_source_policy.py
git commit -m "feat: enforce open source dependency policy"
```

### Task 4: Inventariar paquetes, submódulos y repositorios de investigación

**Files:**
- Create: `tools/ops/audit_open_source_dependencies.py`
- Create: `docs/research/repository_registry.yaml`
- Test: `tests/ops/test_open_source_dependency_audit.py`
- Produce: `data/audits/open_source_dependency_manifest.json`

**Interfaces:**
- Consumes: `OpenSourcePolicy`.
- Produces: `audit_dependencies(project_root: Path, registry_path: Path) -> dict[str, object]`.

- [ ] **Step 1: Escribir pruebas fallidas con repositorio sin licencia y duplicado**

Assert: C-MORL queda `reference_only`; MO-Gymnasium y MORL-Baselines pueden quedar `candidate`; un submódulo ya presente no puede añadirse de nuevo.

- [ ] **Step 2: Implementar inventario de `pyproject.toml`, `.gitmodules` y registro YAML**

No consultar red durante la prueba; el registro guarda URL, commit candidato, SPDX, fuente de licencia, artículo y decisión.

- [ ] **Step 3: Ejecutar pruebas y auditoría real**

Run: `python tools/ops/audit_open_source_dependencies.py --output data/audits/open_source_dependency_manifest.json`

Expected: `ok=false` mientras existan dependencias requeridas con licencia no confirmada; referencias no integradas no bloquean.

- [ ] **Step 4: Commit**

```powershell
git add tools/ops/audit_open_source_dependencies.py tests/ops/test_open_source_dependency_audit.py docs/research/repository_registry.yaml data/audits/open_source_dependency_manifest.json
git commit -m "feat: audit open source supply chain"
```

### Task 5: Detectar secretos y servicios cerrados

**Files:**
- Create: `tools/ops/audit_closed_services_and_secrets.py`
- Test: `tests/ops/test_closed_services_and_secrets.py`
- Modify: `.gitignore`
- Produce: `data/audits/closed_services_and_secrets.json`

**Interfaces:**
- Produces: `audit_closed_services(project_root: Path) -> dict[str, object]`.

- [ ] **Step 1: Escribir pruebas fallidas**

Fixtures: perfil de navegador, token OAuth, URL Drive histórica, import obligatorio de W&B y referencia documental a NotebookLM.

Assert: secretos y dependencias ejecutables bloquean; referencias históricas se reportan sin falso positivo de ejecución.

- [ ] **Step 2: Implementar escaneo por rutas, nombres y configuración requerida**

Nunca imprimir valores de credenciales; solo ruta, categoría y hash seguro.

- [ ] **Step 3: Ejecutar prueba y auditoría real**

Expected: informe distingue `critical`, `excluded_legacy` y `documentation_only`.

- [ ] **Step 4: Commit**

```powershell
git add tools/ops/audit_closed_services_and_secrets.py tests/ops/test_closed_services_and_secrets.py .gitignore data/audits/closed_services_and_secrets.json
git commit -m "security: gate closed services and repository secrets"
```

### Task 6: Crear la puerta local de fundación

**Files:**
- Create: `scripts/quality/run_foundation_gates.ps1`
- Create: `tests/contract/test_foundation_manifests.py`
- Modify: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: manifiestos de Tasks 1, 4 y 5.
- Produces: un único exit code local reproducible por CI.

- [ ] **Step 1: Escribir prueba contractual de esquemas y estados**

- [ ] **Step 2: Implementar el script PowerShell**

Orden: contexto → unit governance → auditoría licencias → auditoría secretos → contratos de manifiestos.

- [ ] **Step 3: Ejecutar localmente**

Run: `powershell -ExecutionPolicy Bypass -File scripts/quality/run_foundation_gates.ps1`

Expected: salida resumida sin secretos; exit code no cero ante cualquier bloqueo.

- [ ] **Step 4: Añadir CI como espejo, no como única vía**

CI ejecuta el mismo script o equivalentes exactos; no añade servicios de terceros.

- [ ] **Step 5: Commit**

```powershell
git add scripts/quality/run_foundation_gates.ps1 tests/contract/test_foundation_manifests.py .github/workflows/ci.yml
git commit -m "ci: add local-first foundation gates"
```

