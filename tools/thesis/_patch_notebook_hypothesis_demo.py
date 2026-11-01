"""Patch madrl_citylearn_v3_tutorial.ipynb for hypothesis demo methodology."""
from __future__ import annotations

import json
from pathlib import Path

NB_PATH = Path(r"d:\MADRLCitytleranflexresdr\examples_madrl_v3\madrl_citylearn_v3_tutorial.ipynb")


def src_lines(text: str) -> list[str]:
    if not text.endswith("\n"):
        text = text + "\n"
    return text.splitlines(keepends=True)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"[FAIL] {label}: pattern not found\n---\n{old[:200]}\n---")
    return text.replace(old, new, 1)


def main() -> None:
    nb = json.loads(NB_PATH.read_text(encoding="utf-8"))

    # ── Cell 42 (6.1) ──
    c42 = "".join(nb["cells"][42]["source"])
    old_seeds = """# Campaña canónica del proyecto: N_SEEDS=12 (seeds 0..11). Este notebook lanza
# 12 jobs = 4 algos × 3 escenarios × 1 semilla (SEED=0) como smoke/campaña single-seed.
# No expande a 4×3×12=144 jobs; para multi-seed, repetir el launcher con --seed 1..11.
N_SEEDS         = 12
SEEDS           = list(range(N_SEEDS))  # 0..11 (diseño multi-seed)
SEED            = 0                     # semilla activa de esta corrida (CLI/single-seed)
"""
    new_seeds = """# Diseño canónico: N_SEEDS=12 (seeds 0..11). HE/H0G Cap.5 usa KPI-gain vs baseline
# evaluate_v2; multi-seed aporta réplicas independientes (robustez).
# Default: single-seed SEED=0 → 12 jobs (4×3×1), alineada a Cap.5/6.
# MULTI_SEED_TRAINING=True → 7.2 lanza two_phase por cada TRAIN_SEEDS (hasta 144 jobs).
N_SEEDS         = 12
SEEDS           = list(range(N_SEEDS))  # 0..11 (diseño multi-seed)
SEED            = 0                     # semilla activa (CLI / primera de TRAIN_SEEDS)
MULTI_SEED_TRAINING = False             # True = bucle 7.2 sobre TRAIN_SEEDS
TRAIN_SEEDS     = [SEED] if not MULTI_SEED_TRAINING else list(SEEDS)
# Pesos de recompensa por escenario (OE.1 / OE.2 / OE.3)
OE_REWARD_WEIGHTS = {
    'E1': {'flexibility': 0.60, 'emissions': 0.15, 'cost': 0.25},  # OE.1
    'E2': {'flexibility': 0.25, 'emissions': 0.60, 'cost': 0.15},  # OE.2
    'E3': {'flexibility': 0.15, 'emissions': 0.25, 'cost': 0.60},  # OE.3
}
# Tras 8.x/9.x: Capa A Cap.5 (Friedman+Wilcoxon/Holm) + pe_answers_audit.json
RUN_CAPA_A_HYPOTHESIS = True
"""
    if "MULTI_SEED_TRAINING" not in c42:
        c42 = replace_once(c42, old_seeds, new_seeds, "6.1 seeds")
    else:
        print("[SKIP] 6.1 seeds already patched")

    old_post = (
        "POST_TRAINING_INCLUDE_SECTION_9 = True   # 9.1 (+resumen_comparativo)\n"
    )
    new_post = (
        "POST_TRAINING_INCLUDE_SECTION_9 = True   # 9.1 (+resumen_comparativo + Capa A HE/H0G)\n"
    )
    if old_post in c42:
        c42 = replace_once(c42, old_post, new_post, "post9 flag")

    if "print(f\"[6.1] MULTI_SEED_TRAINING=" not in c42 and "print(f'[6.1] MULTI_SEED_TRAINING=" not in c42:
        c42 = c42.rstrip() + (
            "\n\nprint(f\"[6.1] MULTI_SEED_TRAINING={MULTI_SEED_TRAINING} \"\n"
            "      f\"TRAIN_SEEDS={TRAIN_SEEDS} N_SEEDS={N_SEEDS}\")\n"
            "print(f\"[6.1] OE reward weights: {OE_REWARD_WEIGHTS}\")\n"
            "print(f\"[6.1] RUN_CAPA_A_HYPOTHESIS={RUN_CAPA_A_HYPOTHESIS} \"\n"
            "      f\"(baseline=evaluate_v2 mismo schema Iquitos)\")\n"
        )
    nb["cells"][42]["source"] = src_lines(c42)
    print("[OK] cell 42")

    # ── Cell 41 markdown ──
    c41 = "".join(nb["cells"][41]["source"])
    if "MULTI_SEED_TRAINING" not in c41:
        c41 = c41.rstrip() + (
            "\n\n"
            "**OE / hipótesis:** pesos E1/E2/E3 en `OE_REWARD_WEIGHTS` (celda code 6.1). "
            "Baseline oficial = `evaluate_v2` embebido (mismo `schema.json` Iquitos). "
            "`MULTI_SEED_TRAINING=False` (default) → seed 0; `True` → `TRAIN_SEEDS=0..11`. "
            "`RUN_CAPA_A_HYPOTHESIS=True` → sección 9 escribe Capa A Cap.5 "
            "(`problemas_objetivos_hipotesis/` + `pe_answers_audit.json`).\n"
        )
        nb["cells"][41]["source"] = src_lines(c41)
    print("[OK] cell 41")

    # ── Cell 46 launcher_base_args ──
    c46 = "".join(nb["cells"][46]["source"])
    if "def launcher_base_args(seed=None):" not in c46:
        c46 = replace_once(
            c46, "def launcher_base_args():", "def launcher_base_args(seed=None):", "launcher def"
        )
        c46 = replace_once(
            c46,
            "'--seed', str(SEED),",
            "'--seed', str(SEED if seed is None else int(seed)),",
            "launcher seed",
        )
        nb["cells"][46]["source"] = src_lines(c46)
        print("[OK] cell 46")
    else:
        print("[SKIP] cell 46")

    # ── Cell 50 multi-seed wrap around train_cmd…post ──
    c50 = "".join(nb["cells"][50]["source"])
    if "_seed_loop_72" not in c50:
        old_block_start = "    train_cmd = launcher_base_args() + ['--skip-completed']\n"
        if old_block_start not in c50:
            raise SystemExit("[FAIL] train_cmd line not found in cell 50")

        # Find the completion / failure handling split point: after _exit assignment
        # We replace from train_cmd through the end of success post-training before else FALLO
        marker_fail = "    else:\n        # Diagnostico de fallo\n"
        idx_start = c50.index(old_block_start)
        if marker_fail not in c50[idx_start:]:
            raise SystemExit("[FAIL] fail diagnostic marker not found")
        idx_fail = c50.index(marker_fail, idx_start)
        old_block = c50[idx_start:idx_fail]

        new_block = '''    # Multisemilla: TRAIN_SEEDS (celda 6.1). Default [0] = una campaña two_phase (12 jobs).
    _seed_loop_72 = [int(s) for s in globals().get('TRAIN_SEEDS', [globals().get('SEED', 0)])]
    if not _seed_loop_72:
        _seed_loop_72 = [int(globals().get('SEED', 0))]
    print(
        f"[7.2] TRAIN_SEEDS={_seed_loop_72} "
        f"(MULTI_SEED_TRAINING={globals().get('MULTI_SEED_TRAINING', False)})"
    )
    _seed_exit_codes_72 = []
    _exit = 1
    _root = None
    for _seed_i_72, _seed_val_72 in enumerate(_seed_loop_72):
        globals()['SEED'] = int(_seed_val_72)
        SEED = int(_seed_val_72)
        print(f"\\n{'=' * 78}\\n[7.2] Semilla {_seed_i_72 + 1}/{len(_seed_loop_72)}: SEED={SEED}\\n{'=' * 78}")
        train_cmd = launcher_base_args(seed=SEED) + ['--skip-completed']
        print('\\n' + _SEP)
        print('  Lanzando entrenamiento...')
        print('  protocol: two_phase_happo_masac_v3 | execution: two_phase_happo_masac')
        print('  ' + ' '.join(str(c) for c in train_cmd))
        print(_SEP + '\\n')
        sys.stdout.flush()

        proc = subprocess.Popen(
            train_cmd,
            cwd=_repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        # Hilo que imprime cada linea del launcher en tiempo real
        def _stream(p):
            try:
                for line in p.stdout:
                    sys.stdout.write(line)
                    sys.stdout.flush()
            except Exception:
                pass

        _th.Thread(target=_stream, args=(proc,), daemon=True).start()

        # ── stop gracioso ─────────────────────────────────────────────────────────
        def _graceful_stop(p):
            if p.poll() is not None:
                return
            print('\\n[7.2] SIGINT al launcher (checkpoints se guardan)...')
            try:
                p.send_signal(_signal.SIGINT)
            except Exception:
                pass
            try:
                p.wait(timeout=40)
            except subprocess.TimeoutExpired:
                p.kill()  # SIGKILL fallback after graceful SIGINT timeout
                p.wait(timeout=10)

        # ── bucle de monitoreo ────────────────────────────────────────────────────
        _last_panel = time.monotonic()
        try:
            while proc.poll() is None:
                _now = time.monotonic()
                if _now - _last_panel >= _MON_INTERVAL:
                    _root = resolve_output_root_or_latest()
                    if _root and _P(_root).exists():
                        _print_panel(_root)
                    _last_panel = _now
                time.sleep(_POLL_SLEEP)
        except KeyboardInterrupt:
            print('\\n[7.2] Interrumpido.')
            _graceful_stop(proc)
            print('[7.2] Para reanudar: Interrupt → git pull (celda 1.2) → run ONLY celda 7.2.')
            raise

        time.sleep(1)   # dar tiempo al hilo de streaming para vaciar el buffer
        _exit = int(proc.returncode or 0)
        _seed_exit_codes_72.append(_exit)

        # Panel final
        _root = resolve_output_root_or_latest()
        if _root and _P(_root).exists():
            _print_panel(_root)

        if _exit != 0:
            print(f'\\n[7.2] FALLO semilla SEED={SEED} (exit={_exit}) — se detiene el bucle multi-seed.')
            break
        print(f'[7.2] Semilla SEED={SEED} completada OK.')

    if _exit == 0 and all(int(c) == 0 for c in _seed_exit_codes_72):
        print(_SEP)
        print('  ENTRENAMIENTO COMPLETADO')
        print(f'  semillas OK: {_seed_loop_72}')
        print(_SEP + '\\n')
        _root_done = resolve_output_root_or_latest()
        _auto_post = bool(globals().get('AUTO_RUN_POST_TRAINING', True))
        _artifacts_ok = False
        if _root_done and 'verify_training_artifacts_complete' in globals():
            _verdict = verify_training_artifacts_complete(_root_done)
            print_training_artifacts_verdict(_verdict)
            _artifacts_ok = bool(_verdict.get('ok'))
        elif _root_done:
            print('[7.2] verify_training_artifacts_complete no disponible — re-ejecuta celda 7.0.')
        if _auto_post and _artifacts_ok and 'run_post_training_notebook_cells' in globals():
            print('\\n[7.2] Artefactos OK — ejecutando pipeline post-entrenamiento (7.3→9.x + Capa A)')
            try:
                run_post_training_notebook_cells(
                    include_section_8=bool(globals().get('POST_TRAINING_INCLUDE_SECTION_8', True)),
                    include_section_9=bool(globals().get('POST_TRAINING_INCLUDE_SECTION_9', True)),
                )
                print('\\n[7.2] Pipeline post-entrenamiento finalizado. Kernel activo.')
            except Exception as _post_exc:
                print(f'\\n[7.2] Post-proceso automatico fallo: {_post_exc}')
                print('  Ejecuta manualmente celdas 7.3 en adelante.')
        elif _auto_post and not _artifacts_ok:
            print('\\n[7.2] Artefactos incompletos — no se ejecuta pipeline automatico.')
            print('  Corrige y ejecuta 7.4+ manualmente, o re-lanza 7.2 con --skip-completed.')
        elif not _auto_post:
            print('\\n[7.2] AUTO_RUN_POST_TRAINING=False — ejecuta 7.3+ manualmente.')
        else:
            print('  Procede con seccion 7.3 — Monitor y auditoria.')
        _disconnect_colab('entrenamiento completado', delay_s=30)
'''
        c50 = c50[:idx_start] + new_block + c50[idx_fail:]
        # Also fix preflight to pass seed
        c50 = c50.replace(
            "_preflight = launcher_base_args() + ['--dry-run', '--skip-completed']",
            "_preflight = launcher_base_args(seed=int(globals().get('SEED', 0))) + ['--dry-run', '--skip-completed']",
            1,
        )
        nb["cells"][50]["source"] = src_lines(c50)
        print("[OK] cell 50 multi-seed")
    else:
        print("[SKIP] cell 50")

    # ── Cell 58 baseline wording ──
    c58 = "".join(nb["cells"][58]["source"])
    c58_new = c58.replace(
        "Cada job MADRL calcula la línea base RBC/local vía **`evaluate_v2`** y guarda en `results.json`",
        "Cada job MADRL calcula la línea base física CityLearn v2 (`WITHOUT_STORAGE*` / control vs baseline) vía **`evaluate_v2`** sobre el **mismo** `schema.json` Iquitos 2023-2025 y guarda en `results.json`",
    )
    nb["cells"][58]["source"] = src_lines(c58_new)
    print("[OK] cell 58")

    # ── Cell 65 markdown ──
    c65 = """## Sección 9: Evaluación estadística — Selección OG / OE.1 / OE.2 / OE.3 y Capa A (HE/H0G)

Protocolo alineado a Cap. III–V y CityLearn v3 (`objectives.py`, **54 KPIs** OE; distrito + edificio):

### Capa descriptiva / ranking (notebook)
1. **Score por escenario** — media del *signed relative gain* vs baseline `evaluate_v2` (mismo dataset Iquitos) sobre KPIs del OE emparejado (E1→OE1, E2→OE2, E3→OE3).
2. **Ganador OE.k** — mejor algoritmo en Ek (descriptivo).
3. **Ganador OG** — media de scores E1/E2/E3 (descriptivo; **no** sustituye H0G).

### Capa A inferencial Cap.5 (HE10–HE31 / H0G–H1G) — `RUN_CAPA_A_HYPOTHESIS=True`
4. Puerta **Shapiro–Wilk** sobre KPI-gains.
5. Principal: **Friedman pareado + Kendall W** + **Wilcoxon firmado vs 0** (impacto vs baseline) + **Wilcoxon pareado + Holm**.
6. Exploratorio: Kruskal–Wallis / Mann–Whitney U (no fundamentan HE).
7. Salidas: `{OUTPUT_ROOT}/resumen_comparativo/estadistica/problemas_objetivos_hipotesis/` + `pe_answers_audit.json`.

> Con `SEED=0` (campaña actual) la unidad HE es el KPI-gain pareado, no la semilla. Shapiro/KW/MWU *sobre semillas* solo aplica si `MULTI_SEED_TRAINING` aporta ≥3 semillas.
"""
    nb["cells"][65]["source"] = src_lines(c65)
    print("[OK] cell 65")

    # ── Cell 66 Cap A ──
    c66 = "".join(nb["cells"][66]["source"])
    if "9.3  Capa A Cap.5" not in c66:
        if "import subprocess" not in c66:
            c66 = "import subprocess\n" + c66
        c66 = c66.rstrip() + '''

# ── 9.3  Capa A Cap.5: HE/H0G desde results del entrenamiento (mismo OUTPUT_ROOT) ──
# Conecta scores KPI vs baseline evaluate_v2 → Friedman/Wilcoxon-Holm → pe_answers.
if bool(globals().get("RUN_CAPA_A_HYPOTHESIS", True)):
    import sys
    from pathlib import Path as _Pcapa
    _repo_capa = _Pcapa(str(globals().get("REPO", ".")))
    _pipe = _repo_capa / "tools" / "eval" / "run_notebook_hypothesis_pipeline.py"
    _out_capa = _Pcapa(str(OUTPUT_ROOT))
    if not _pipe.is_file():
        print(f"[9.3] AVISO: no se encontró {_pipe}; Capa A no ejecutada.")
    else:
        _py_capa = globals().get("PROJECT_PYTHON", globals().get("PYTHON", sys.executable))
        _cmd_capa = [
            str(_py_capa), "-B", str(_pipe),
            f"--output-root={_out_capa}",
            f"--seed={int(globals().get('SEED', 0))}",
        ]
        print("[9.3] Pipeline hipótesis Cap.5:", " ".join(_cmd_capa))
        _rc_capa = subprocess.run(_cmd_capa, cwd=str(_repo_capa)).returncode
        _capa_dir = _out_capa / "resumen_comparativo" / "estadistica" / "problemas_objetivos_hipotesis"
        _pe = _out_capa / "resumen_comparativo" / "estadistica" / "pe_answers_audit.json"
        if _rc_capa == 0 and _capa_dir.is_dir():
            print(f"[9.3] OK Capa A → {_capa_dir}")
            print(f"[9.3] Decisiones HE/H0G: {_capa_dir / 'decisiones_problemas_objetivos_hipotesis.csv'}")
            print(f"[9.3] pe_answers: {_pe}")
            try:
                import pandas as _pd_capa
                _dec = _pd_capa.read_csv(_capa_dir / "decisiones_problemas_objetivos_hipotesis.csv")
                cols = [c for c in ("scope", "null_hypothesis", "alternative_hypothesis",
                                     "descriptive_best_algorithm", "friedman_p",
                                     "hypothesis_decision") if c in _dec.columns]
                print(_dec[cols].to_string(index=False))
            except Exception as _exc_capa:
                print(f"[9.3] No se pudo imprimir decisiones: {_exc_capa}")
        else:
            print(f"[9.3] FALLO pipeline hipótesis rc={_rc_capa}")
else:
    print("[9.3] RUN_CAPA_A_HYPOTHESIS=False — ranking 9.1/9.2 solo descriptivo.")
'''
        nb["cells"][66]["source"] = src_lines(c66)
        print("[OK] cell 66 Cap A")
    else:
        print("[SKIP] cell 66")

    # Soften seed-unit claims in 9.1 docstring/text when n_seeds=1
    c66b = "".join(nb["cells"][66]["source"])
    c66b = c66b.replace(
        '"Pruebas Shapiro/KW/Mann-Whitney se aplican a las N_SEEDS=12 semillas "',
        '"Pruebas Shapiro/KW/Mann-Whitney sobre semillas requieren cobertura multi-seed; '
        'con SEED=0 la inferencia HE/H0G es Capa A (9.3) sobre KPI-gains. N_SEEDS diseño="',
    )
    nb["cells"][66]["source"] = src_lines(c66b)

    # ── Cell 73 ──
    c73 = "".join(nb["cells"][73]["source"])
    old73 = "- Diseño multi-seed del proyecto: **12 semillas** (`N_SEEDS=12`, seeds `0..11`). Esta campaña notebook usa `SEED=0` (12 jobs = 4×3×1).\n"
    new73 = (
        "- Diseño multi-seed: **12 semillas** (`N_SEEDS=12`). Default: `SEED=0` (12 jobs). "
        "Campaña completa: `MULTI_SEED_TRAINING=True` en 6.1.\n"
        "- Demostración de hipótesis Cap.5: sección **9.3** → "
        "`problemas_objetivos_hipotesis/` + `pe_answers_audit.json`.\n"
    )
    if old73 in c73:
        c73 = c73.replace(old73, new73, 1)
        nb["cells"][73]["source"] = src_lines(c73)
        print("[OK] cell 73")
    else:
        print("[SKIP] cell 73")

    NB_PATH.write_text(json.dumps(nb, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[DONE] {NB_PATH}")


if __name__ == "__main__":
    main()
