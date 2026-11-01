# Tareas — SPEC-001

**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`  
**Diseño:** [aprobado](../../docs/superpowers/specs/2026-10-31-modernizacion-integral-open-source-design.md) · **Estado conciliado:** [STATUS](../STATUS.md)  
**Revisión:** 2026-10-31

`[x]` = archivo verificado en el árbol el 2026-10-31; no implica aceptación.

- [x] **FR-001.1:** Política y evaluador implementados — `governance/open_source_policy.yaml, uc3m/governance/open_source.py`
- [x] **FR-001.2:** Auditor de dependencias e inventario inicial — `tools/ops/audit_open_source_dependencies.py, data/audits/open_source_dependency_manifest.json`
- [ ] **FR-001.2:** Resolver 3 licencias ausentes y 2 copyleft (sin editar dependencias sin autorización) — `data/audits/open_source_dependency_manifest.json`
- [ ] **FR-001.3:** Generar SBOM local — `data/audits/sbom.cdx.json`
- [x] **FR-001.4:** Registro de repositorios — `docs/research/repository_registry.yaml`
- [x] **FR-001.5:** Auditor de secretos y servicios cerrados — `tools/ops/audit_closed_services_and_secrets.py`

**Aceptación:** `powershell -ExecutionPolicy Bypass -File scripts/quality/run_foundation_gates.ps1`
