#!/usr/bin/env python3
"""Patch madrl_citylearn_v3_tutorial.ipynb for two_phase_happo_masac on current branch."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

NOTEBOOK = Path(__file__).resolve().parents[1] / "CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb"
nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
changes = 0


def sub(src: str, old: str, new: str) -> str:
    global changes
    if old in src:
        changes += 1
        return src.replace(old, new)
    return src


def patch_text(src: str) -> str:
    src = sub(
        src,
        "TORCH_THREADS        = 4     # 4 hilos CPU por proceso; 3 procesos paralelos = 12 hilos = todos los cores Colab A100",
        "TORCH_THREADS        = 2     # 6 jobs/fase en A100 Colab (12 vCPU) -> 2 hilos/job",
    )
    src = sub(
        src,
        "LIVE_PROGRESS_INT    = 5000  # menos escrituras live_progress.json en Drive/hot path",
        "LIVE_PROGRESS_INT    = 300   # snapshot cada 300 pasos (~2-3 FPS con 6 jobs/fase)",
    )
    src = sub(
        src,
        "print(f'Launcher      : {LAUNCHER}')\n",
        "print(f'Launcher      : {LAUNCHER}')\n"
        "EXECUTION_MODE = 'two_phase_happo_masac'\n"
        "print(f'Ejecucion     : {EXECUTION_MODE} (Fase1 HAPPO+MASAC x3, Fase2 MATD3+MAAC x3)')\n"
        "# Budget A100 80GB / 167 GiB RAM\n"
        "_masac_frac = 0.26\n"
        "_gpu_p1 = 3 + 3 * (10.28 + 0.9)  # HAPPO + MASAC buffers on GPU\n"
        "_ram_p1 = 6 * 11.0\n"
        "_ram_p2_peak = 6 * 11.0 + 18.0   # MATD3 env-load peak (staggered)\n"
        "print(f'  Fase1 GPU ~{_gpu_p1:.0f}/80 GiB | RAM ~{_ram_p1:.0f}/167 GiB')\n"
        "print(f'  Fase2 RAM peak ~{_ram_p2_peak:.0f}/167 GiB (MATD3 stagger 600/3600/6600s)')\n",
    )

    # launcher_base_args block
    old_launcher = """    base += _opt('--parallel-scenarios', '3')
    return base"""
    new_launcher = """    base += [
        '--execution-mode', 'two_phase_happo_masac',
        '--two-phase-torch-threads', '2',
        '--two-phase-masac-cuda-fraction', '0.26',
    ]
    return base"""
    src = sub(src, old_launcher, new_launcher)

    # Colab-safe hyperparams in launcher_base_args
    src = sub(src, "'--happo-n-rollout-threads', '4'", "'--happo-n-rollout-threads', '1'")
    src = sub(src, "'--masac-critic-batch-size', '1024'", "'--masac-critic-batch-size', '512'")
    src = sub(src, "'--masac-buffer-size', '40'", "'--masac-buffer-size', '15'")
    src = sub(src, "'--masac-max-replay-buffer-gib', '40.0'", "'--masac-max-replay-buffer-gib', '20.0'")
    src = sub(src, "'--masac-rnn-hidden-dim', '1024'", "'--masac-rnn-hidden-dim', '128'")
    src = sub(src, "'--masac-qmix-hidden-dim', '512'", "'--masac-qmix-hidden-dim', '128'")
    src = sub(src, "'--masac-hyper-hidden-dim', '1024'", "'--masac-hyper-hidden-dim', '256'")
    src = sub(src, "'--masac-preload-batch-device', 'cpu'", "'--masac-preload-batch-device', 'cuda'")
    src = sub(src, "'--matd3-batch-size', '1024'", "'--matd3-batch-size', '4096'")
    src = sub(src, "'--matd3-buffer-size', '2000000'", "'--matd3-buffer-size', '100000'")
    src = sub(src, "'--matd3-hidden-size', '1024'", "'--matd3-hidden-size', '512'")
    src = sub(src, "'--maac-batch-size', '1024'", "'--maac-batch-size', '1024'")
    src = sub(src, "'--maac-buffer-length', '1000000'", "'--maac-buffer-length', '100000'")
    src = sub(src, "'--maac-hidden-size', '1024'", "'--maac-hidden-size', '512'")
    src = sub(src, "'--maac-num-updates', '16'", "'--maac-num-updates', '8'")

    return src


for cell in nb["cells"]:
    if cell.get("cell_type") not in ("code", "markdown"):
        continue
    joined = "".join(cell.get("source", []))
    patched = patch_text(joined)
    if patched != joined:
        cell["source"] = [patched]

two_phase_md = """### Estrategia de entrenamiento en dos fases (Colab A100)

| Fase | Algoritmos | Jobs paralelos | Notas |
|:---:|:---|:---:|:---|
| **1** | HAPPO + MASAC | 6 (E1/E2/E3) | MASAC buffer en GPU VRAM; 2 vCPU/job |
| **2** | MATD3 + MAAC | 6 (E1/E2/E3) | Tras Fase 1; MATD3 stagger 600/3600/6600s |

Modo launcher: `--execution-mode two_phase_happo_masac`. Reanudacion: `--skip-completed`.
"""

for i, cell in enumerate(nb["cells"]):
    if cell.get("cell_type") == "markdown" and "## Seccion 6:" in "".join(cell.get("source", [])):
        if i > 0 and "Estrategia de entrenamiento en dos fases" not in "".join(nb["cells"][i - 1].get("source", [])):
            nb["cells"].insert(i, {"cell_type": "markdown", "metadata": {}, "source": [two_phase_md]})
            changes += 1
        break

NOTEBOOK.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"Patched {NOTEBOOK.name}: {changes} edits")
