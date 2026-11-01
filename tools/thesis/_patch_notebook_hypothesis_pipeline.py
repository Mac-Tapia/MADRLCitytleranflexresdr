"""Patch madrl_citylearn_v3_tutorial.ipynb for hypothesis-demo methodology.

Updates:
- 6.1: MULTI_SEED_TRAINING / TRAIN_SEEDS / RUN_CAPA_A_HYPOTHESIS + OE weights
- 7.0: launcher_base_args(seed=...)
- 7.2: loop TRAIN_SEEDS when multi-seed enabled
- 7.6 / 9 markdown: Cap5 protocol + baseline wording
- 9.1: call tools/eval/run_notebook_hypothesis_pipeline.py → Capa A HE/H0G
"""

from __future__ import annotations

import json
from pathlib import Path


NB_PATH = Path("examples_madrl_v3/madrl_citylearn_v3_tutorial.ipynb")


def _src_lines(cell: dict) -> list[str]:
    src = cell.get("source", [])
    if isinstance(src, str):
        return src.splitlines(keepends=True)
    return list(src)


def _set_source(cell: dict, text: str) -> None:
    if not text.endswith("\n"):
        text += "\n"
    cell["source"] = [line + "\n" for line in text.split("\n")[:-1]]
    # preserve trailing newline as last empty? nbformat usually stores lines with \n
    # Rebuild cleanly:
    lines = text.splitlines(keepends=True)
    cell["source"] = lines


def patch_cell_42_config(cell: dict) -> bool:
    text = "".join(_src_lines(cell))
    old = (
        "# Campaña canónica del proyecto: N_SEEDS=12 (seeds 0..11). Este notebook lanza\n"
        "# 12 jobs = 4 algos × 3 escenarios × 1 semilla (SEED=0) como smoke/campaña single-seed.\n"
        "# No expande a 4×3×12=144 jobs; para multi-seed, repetir el launcher con --seed 1..11.\n"
        "N_SEEDS         = 12\n"
        "SEEDS           = list(range(N_SEEDS))  # 0..11 (diseño multi-seed)\n"
        "SEED            = 0                     # semilla activa de esta corrida (CLI/single-seed)\n"
    )
    new = (
        "# Diseño factorial tesis: N_SEEDS=12 (0..11). Por defecto campaña seed=0 (12 jobs = 4×3×1).\n"
        "# MULTI_SEED_TRAINING=True → 7.2 itera TRAIN_SEEDS (hasta 4×3×12=144 jobs) en el mismo OUTPUT_ROOT.\n"
        "N_SEEDS         = 12\n"
        "SEEDS           = list(range(N_SEEDS))  # 0..11 (diseño multi-seed)\n"
        "SEED            = 0                     # semilla activa (single-seed / primera de TRAIN_SEEDS)\n"
        "MULTI_SEED_TRAINING = False             # True = lanzar TRAIN_SEEDS secuencialmente en 7.2\n"
        "TRAIN_SEEDS     = [SEED] if not MULTI_SEED_TRAINING else list(SEEDS)\n"
        "# Pesos de recompensa por escenario (OE.1/OE.2/OE.3) — ScenarioManager / reward_function\n"
        "OE_REWARD_WEIGHTS = {\n"
        "    'E1': {'flexibility': 0.60, 'emissions': 0.15, 'cost': 0.25},  # OE.1\n"
        "    'E2': {'flexibility': 0.25, 'emissions': 0.60, 'cost': 0.15},  # OE.2\n"
        "    'E3': {'flexibility': 0.15, 'emissions': 0.25, 'cost': 0.60},  # OE.3\n"
        "}\n"
        "RUN_CAPA_A_HYPOTHESIS = True  # 9.x → problemas_objetivos_hipotesis/ (Friedman+Wilcoxon/Holm)\n"
    )
    if old not in text:
        if "MULTI_SEED_TRAINING" in text and "RUN_CAPA_A_HYPOTHESIS" in text:
            return False
        raise RuntimeError("cell 42 seed block not found")
    text = text.replace(old, new, 1)

    # Ensure AUTO_RUN / POST flags mention Cap A; append print of OE weights near end if missing
    if "OE_REWARD_WEIGHTS" in text and "print.*OE_REWARD" not in text:
        marker = "print(f\"[6.1] N_EPISODES={N_EPISODES}"
        # find a print near end of config - append after SEED prints
        inject_after = "SEED            = 0"
        # Better: append near existing print statements at end of cell
        if "print(" in text and "OE.1/E1 flex=0.60" not in text:
            # Find last print block - inject before final lines
            tip = (
                "\nprint('[6.1] OE reward weights (tesis Cap.4):')\n"
                "for _sc, _w in OE_REWARD_WEIGHTS.items():\n"
                "    print(f'  {_sc}: flex={_w[\"flexibility\"]:.2f}  "
                "co2={_w[\"emissions\"]:.2f}  cost={_w[\"cost\"]:.2f}')\n"
                "print(f'[6.1] MULTI_SEED_TRAINING={MULTI_SEED_TRAINING} "
                "TRAIN_SEEDS={TRAIN_SEEDS}  RUN_CAPA_A_HYPOTHESIS={RUN_CAPA_A_HYPOTHESIS}')\n"
            )
            # Insert before AUTO_RUN if present, else append
            if "AUTO_RUN_POST_TRAINING" in text:
                text = text.replace(
                    "AUTO_RUN_POST_TRAINING",
                    tip + "AUTO_RUN_POST_TRAINING",
                    1,
                )
            else:
                text = text.rstrip() + "\n" + tip

    _set_source(cell, text)
    return True


def patch_launcher_base_args(cell: dict) -> bool:
    text = "".join(_src_lines(cell))
    old = (
        "def launcher_base_args():\n"
    )
    # Find the function and make seed parameterizable
    if "def launcher_base_args(seed=None)" in text:
        return False
    if "def launcher_base_args():" not in text:
        raise RuntimeError("launcher_base_args not found")
    text = text.replace(
        "def launcher_base_args():",
        "def launcher_base_args(seed=None):",
        1,
    )
    # Replace '--seed', str(SEED) inside launcher_base_args
    # Be careful - there may be multiple. Only the one in launcher_base_args.
    needle = "'--seed', str(SEED),"
    if needle not in text:
        needle = '"--seed", str(SEED),'
    if needle not in text:
        raise RuntimeError("seed arg in launcher_base_args not found")
    # Replace first occurrence after launcher_base_args
    idx = text.find("def launcher_base_args")
    idx2 = text.find(needle, idx)
    if idx2 < 0:
        raise RuntimeError("seed needle after launcher_base_args not found")
    replacement = (
        "'--seed', str(SEED if seed is None else int(seed)),"
        if needle.startswith("'")
        else '"--seed", str(SEED if seed is None else int(seed)),'
    )
    text = text[:idx2] + replacement + text[idx2 + len(needle) :]
    _set_source(cell, text)
    return True


def patch_cell_50_multiseed(cell: dict) -> bool:
    text = "".join(_src_lines(cell))
    if "for _seed_i, _train_seed in enumerate(_train_seeds)" in text:
        # still ensure launcher_base_args(seed=...)
        if "launcher_base_args(seed=" not in text and "launcher_base_args()" in text:
            text = text.replace(
                "launcher_base_args()",
                "launcher_base_args(seed=int(globals().get('SEED', 0)))",
            )
            _set_source(cell, text)
            return True
        return False

    # Seed-aware launcher calls (preflight + train)
    text = text.replace(
        "launcher_base_args()",
        "launcher_base_args(seed=int(globals().get('SEED', 0)))",
    )

    old_block = """    train_cmd = launcher_base_args(seed=int(globals().get('SEED', 0))) + ['--skip-completed']
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

    # Panel final
    _root = resolve_output_root_or_latest()
    if _root and _P(_root).exists():
        _print_panel(_root)
"""

    new_block = """    # Multi-seed: TRAIN_SEEDS (6.1). Default [0]. Cada seed = réplica experimental independiente.
    _train_seeds = [int(s) for s in list(globals().get('TRAIN_SEEDS', [globals().get('SEED', 0)]))]
    if not _train_seeds:
        _train_seeds = [int(globals().get('SEED', 0))]
    print(f"[7.2] TRAIN_SEEDS={_train_seeds} MULTI_SEED_TRAINING={bool(globals().get('MULTI_SEED_TRAINING', False))}")
    _exit = 1
    _root = resolve_output_root_or_latest()

    def _stream(p):
        try:
            for line in p.stdout:
                sys.stdout.write(line)
                sys.stdout.flush()
        except Exception:
            pass

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
            p.kill()
            p.wait(timeout=10)

    for _seed_i, _train_seed in enumerate(_train_seeds):
        globals()['SEED'] = int(_train_seed)
        SEED = int(_train_seed)
        train_cmd = launcher_base_args(seed=SEED) + ['--skip-completed']
        print('\\n' + _SEP)
        print(f'  Lanzando entrenamiento seed={SEED} ({_seed_i+1}/{len(_train_seeds)})...')
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
        _th.Thread(target=_stream, args=(proc,), daemon=True).start()

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

        time.sleep(1)
        _exit = int(proc.returncode or 0)
        _root = resolve_output_root_or_latest()
        if _root and _P(_root).exists():
            _print_panel(_root)
        if _exit != 0:
            print(f'[7.2] Fallo en seed={SEED} (exit={_exit}) — se detiene la campaña multi-seed.')
            break
        print(f'[7.2] Seed={SEED} OK.')
"""

    if old_block not in text:
        # Try without the seed= already applied (original launcher_base_args())
        old_alt = old_block.replace(
            "launcher_base_args(seed=int(globals().get('SEED', 0)))",
            "launcher_base_args()",
        )
        if old_alt in text:
            old_block = old_alt
        else:
            # Soft fallback: only seed-aware calls; document multi-seed via TRAIN_SEEDS sequential manual
            print("[warn] exact train block not found; applied seed-aware launcher only")
            tip = (
                "\n    # MULTI-SEED: con MULTI_SEED_TRAINING=True (celda 6.1), TRAIN_SEEDS itera aquí.\n"
                "    # Si este bloque no envuelve el Popen, re-ejecuta 7.2 cambiando SEED o activa el patch.\n"
            )
            if "train_cmd = launcher_base_args" in text and "TRAIN_SEEDS=" not in text:
                text = text.replace(
                    "    train_cmd = launcher_base_args",
                    tip + "    train_cmd = launcher_base_args",
                    1,
                )
            _set_source(cell, text)
            return True

    text = text.replace(old_block, new_block, 1)
    _set_source(cell, text)
    return True


def patch_markdown_76(cell: dict) -> bool:
    text = "".join(_src_lines(cell))
    old = (
        "Cada job MADRL calcula la línea base RBC/local vía **`evaluate_v2`** y guarda en "
        "`results.json` los campos `objective_kpis`, `axis_baseline_comparison` y "
        "`baseline_gain_by_kpi`. **Esa es la baseline oficial para ranking 8.x/9.x.**"
    )
    new = (
        "Cada job MADRL evalúa control vs línea base física CityLearn v2 vía **`evaluate_v2`** "
        "(mismo `schema.json` Iquitos `citylearn_iquitos_2023_2025` que el entrenamiento) y "
        "guarda en `results.json` los campos `objective_kpis`, `axis_baseline_comparison` y "
        "`baseline_gain_by_kpi`. **Esa es la baseline oficial para Cap.5 / 8.x / 9.x (HE/H0G).** "
        "Hour-RBC / SB3 son benchmarks secundarios opcionales, no sustituyen esta contraste."
    )
    if old not in text:
        if "mismo `schema.json` Iquitos" in text:
            return False
        raise RuntimeError("7.6 baseline paragraph not found")
    _set_source(cell, text.replace(old, new, 1))
    return True


def patch_markdown_9(cell: dict) -> bool:
    new = """## Sección 9: Evaluación estadística — OG / OE.1 / OE.2 / OE.3 y Capa A (HE/H0G)

Protocolo alineado a Cap. III–V y a CityLearn v3 (`objectives.py`, **54 KPIs** OE; distrito + edificio):

1. **Baseline** — `evaluate_v2` embebido en cada corrida (mismo dataset Iquitos que el entrenamiento).
2. **Score descriptivo por escenario** — media del *signed relative gain* vs baseline (E1→OE.1, E2→OE.2, E3→OE.3).
3. **Ganador OE.k / OG** — ranking descriptivo (no sustituye hipótesis).
4. **Capa A (decisión HE/H0G)** — Shapiro–Wilk → **Friedman pareado + Kendall W + Wilcoxon/Holm** (principal); Kruskal–Wallis / Mann–Whitney solo exploratorio. Unidad = KPI-gains (no episodios como réplicas).
5. **Salidas** — `{OUTPUT_ROOT}/resumen_comparativo/estadistica/problemas_objetivos_hipotesis/` + `pe_answers_audit.json`.

> Con `SEED=0` (campaña canónica) la inferencia es **exploratoria**. `MULTI_SEED_TRAINING=True` habilita réplicas independientes (`N_SEEDS=12`).
"""
    _set_source(cell, new)
    return True


CAPA_A_BLOCK = '''
# ── 9.1b  Capa A Cap.5: Friedman + Wilcoxon/Holm → HE/H0G ───────────────────
# Conecta results.json (entrenamiento + evaluate_v2) a decisiones de hipótesis.
_run_capa = bool(globals().get("RUN_CAPA_A_HYPOTHESIS", True))
if _run_capa:
    import subprocess as _sp_capa
    from pathlib import Path as _P_capa
    _repo_capa = _P_capa(str(globals().get("REPO")))
    _out_capa = _P_capa(str(OUTPUT_ROOT))
    _py_capa = str(globals().get("PROJECT_PYTHON", globals().get("PYTHON", "python")))
    _pipe = _repo_capa / "tools" / "eval" / "run_notebook_hypothesis_pipeline.py"
    assert _pipe.is_file(), f"Falta pipeline Cap A: {_pipe}"
    _cmd_capa = [
        _py_capa, "-B", str(_pipe),
        f"--output-root={_out_capa}",
        f"--seed={int(globals().get('SEED', 0))}",
    ]
    print("\\n[9.1b] Capa A / hipótesis (Friedman+Wilcoxon/Holm) ←", _out_capa)
    _rc_capa = _sp_capa.run(_cmd_capa, cwd=str(_repo_capa))
    if _rc_capa.returncode != 0:
        raise RuntimeError(
            f"Pipeline hipótesis falló (exit={_rc_capa.returncode}). "
            "Verifica results.json con objective_kpis/baseline_gain_by_kpi."
        )
    _capa_dir = _out_capa / "resumen_comparativo" / "estadistica" / "problemas_objetivos_hipotesis"
    _dec = _capa_dir / "decisiones_problemas_objetivos_hipotesis.csv"
    _pe = _out_capa / "resumen_comparativo" / "estadistica" / "pe_answers_audit.json"
    print(f"[9.1b] OK decisiones → {_dec}")
    print(f"[9.1b] OK pe_answers → {_pe}")
    if _dec.is_file():
        import pandas as _pd_capa
        _df_dec = _pd_capa.read_csv(_dec)
        cols = [c for c in [
            "scope", "null_hypothesis", "alternative_hypothesis",
            "descriptive_best_algorithm", "friedman_p", "hypothesis_decision",
        ] if c in _df_dec.columns]
        print(_df_dec[cols].to_string(index=False))
else:
    print("[9.1b] RUN_CAPA_A_HYPOTHESIS=False — omitido (ranking 9.1 descriptivo sigue OK).")
'''


def patch_cell_66_capa(cell: dict) -> bool:
    text = "".join(_src_lines(cell))
    if "run_notebook_hypothesis_pipeline" in text or "9.1b" in text:
        return False
    # Clarify seed-based KW as exploratorio / vacuous if n_seeds<3
    text = text.replace(
        '"Pruebas Shapiro/KW/Mann-Whitney se aplican a las N_SEEDS=12 semillas "',
        '"Capa B exploratoria: Shapiro/KW/MWU sobre semillas si cobertura>=3; '
        'HE/H0G = Capa A (9.1b Friedman+Wilcoxon/Holm sobre KPI-gains). "',
    )
    # Append Cap A block at end
    text = text.rstrip() + "\n\n" + CAPA_A_BLOCK.lstrip("\n")
    if not text.endswith("\n"):
        text += "\n"
    _set_source(cell, text)
    return True


def patch_cell_73_next_steps(cell: dict) -> bool:
    text = "".join(_src_lines(cell))
    if "problemas_objetivos_hipotesis" in text:
        return False
    add = (
        "\n\n### Demostración de hipótesis (Capa A)\n"
        "- Tras 8.x/9.x con `RUN_CAPA_A_HYPOTHESIS=True`, revisar "
        "`{OUTPUT_ROOT}/resumen_comparativo/estadistica/problemas_objetivos_hipotesis/`.\n"
        "- Decisiones HE10–HE31 / H0G–H1G: `decisiones_problemas_objetivos_hipotesis.csv`.\n"
        "- Resumen PE/OE: `pe_answers_audit.json`.\n"
        "- Multi-semilla real: `MULTI_SEED_TRAINING=True` en 6.1 (`TRAIN_SEEDS=0..11`).\n"
    )
    _set_source(cell, text.rstrip() + add)
    return True


def main() -> None:
    nb = json.loads(NB_PATH.read_text(encoding="utf-8"))
    actions = []

    # Identify cells by markers
    for i, cell in enumerate(nb["cells"]):
        src = "".join(_src_lines(cell))
        first = src.strip().split("\n", 1)[0] if src.strip() else ""
        if first.startswith("# ── 6.1") or (
            "N_SEEDS" in src and "EXECUTION_MODE" in src and "SIX_JOB" in src and cell["cell_type"] == "code"
        ):
            if "N_EPISODES" in src and "QUICK_TEST" in src:
                try:
                    if patch_cell_42_config(cell):
                        actions.append(f"patched config cell {i}")
                except Exception as exc:
                    actions.append(f"FAIL config cell {i}: {exc}")

        if "def launcher_base_args" in src and cell["cell_type"] == "code":
            try:
                if patch_launcher_base_args(cell):
                    actions.append(f"patched launcher_base_args cell {i}")
            except Exception as exc:
                actions.append(f"FAIL launcher cell {i}: {exc}")

        if first.startswith("# ── 7.2") and "LAUNCH_FULL_TRAINING" in src:
            try:
                if patch_cell_50_multiseed(cell):
                    actions.append(f"patched 7.2 multiseed cell {i}")
            except Exception as exc:
                actions.append(f"FAIL 7.2 cell {i}: {exc}")

        if first.startswith("### 7.6") and cell["cell_type"] == "markdown":
            try:
                if patch_markdown_76(cell):
                    actions.append(f"patched 7.6 md cell {i}")
            except Exception as exc:
                actions.append(f"FAIL 7.6 md {i}: {exc}")

        if first.startswith("## Sección 9:") and cell["cell_type"] == "markdown":
            if patch_markdown_9(cell):
                actions.append(f"patched sec9 md cell {i}")

        if first.startswith("# ── 9.1") and cell["cell_type"] == "code":
            try:
                if patch_cell_66_capa(cell):
                    actions.append(f"patched 9.1 capa cell {i}")
            except Exception as exc:
                actions.append(f"FAIL 9.1 cell {i}: {exc}")

        if first.startswith("## Próximos pasos") and cell["cell_type"] == "markdown":
            if patch_cell_73_next_steps(cell):
                actions.append(f"patched next-steps cell {i}")

    NB_PATH.write_text(json.dumps(nb, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("DONE")
    for a in actions:
        print("-", a)


if __name__ == "__main__":
    main()
