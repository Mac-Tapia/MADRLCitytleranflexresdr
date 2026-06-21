import pathlib, sys
sys.stdout.reconfigure(encoding='utf-8')

readme = pathlib.Path(r'd:/MADRLCitytleranflexresdr/README.md')
txt = readme.read_text(encoding='utf-8')

def rep(old, new, label):
    if old in txt:
        return txt.replace(old, new, 1), label + ": OK"
    return txt, label + ": NOTFOUND"

msg = []

# 1. Estado actual - cambios
old = (
    "- ✅ Tutorial notebook Colab A100 corregido: badge, metadatos, celdas 1.2 y 1.2b\n"
    "- ✅ CityLearn submodulo vive en rama `citylearn-v3-madrl` (no detached HEAD)\n"
    "- ✅ 9 submodulos registrados e inicializados en `.gitmodules`\n"
    "- ✅ Git LFS configurado para checkpoints `.pt` — resultados versionados en GitHub\n"
    "- ✅ README actualizado con instrucciones de clonado y manual Colab A100"
)
new = (
    "- ✅ Tutorial notebook actualizado a **NVIDIA A100-SXM4-80GB + 167 GiB RAM** (eliminadas todas las referencias RTX 4060 como entorno objetivo)\n"
    "- ✅ Launcher `colab_a100_official_launcher.py`: `--parallel-scenarios 3`, hyperparams A100-80GB, MASAC buffer CPU (3x40 GiB = 120 GiB RAM)\n"
    "- ✅ 9 submodulos registrados e inicializados en `.gitmodules`\n"
    "- ✅ Git LFS configurado para checkpoints `.pt` — resultados versionados en GitHub\n"
    "\n"
    "### Corrida oficial activa — Google Colab A100-SXM4-80GB\n"
    "\n"
    "| Campo | Valor |\n"
    "| ----- | ----- |\n"
    "| Hardware | NVIDIA A100-SXM4-80GB · 80 GiB VRAM · 167 GiB RAM · CUDA 12.4 |\n"
    "| Run ID | `madrl_v3_20260621_002450` (en ejecucion) |\n"
    "| Episodios | 50 x 8760 pasos = 438 000 pasos/corrida |\n"
    "| Paralelismo | 3 escenarios concurrentes por algoritmo (`--parallel-scenarios 3`) |\n"
    "| MASAC buffer | CPU (`--masac-preload-batch-device cpu`): 3x40 GiB = 120 GiB RAM |\n"
    "| HAPPO hidden | [512, 512] |\n"
    "| MATD3 buffer | 1 000 000 steps · batch 1024 · hidden 512 |\n"
    "| MAAC buffer | 500 000 steps · batch 1024 · hidden 512 |\n"
    "| GPU profile | `aws` |\n"
    "| Tiempo estimado | ~4-5 dias (vs ~13 dias secuencial) |\n"
    "| Notebook Colab | `CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb` |"
)
txt, m = rep(old, new, "1-estado")
msg.append(m)

# 2. Hardware footnote
old2 = "Hardware: RTX 4060 Laptop, 8,188 MiB VRAM, driver 560.94, PyTorch 2.8.0+cu126, CUDA 12.6, `cuda_memory_fraction=0.812`."
new2 = "Hardware (referencia v4 piloto): RTX 4060 Laptop 8 GiB VRAM, CUDA 12.6. Corrida oficial: NVIDIA A100-SXM4-80GB 80 GiB VRAM, 167 GiB RAM, CUDA 12.4 (Colab)."
txt, m = rep(old2, new2, "2-hardware")
msg.append(m)

# 3. Config fija GPU profile
old3 = "- Perfil GPU: `local4060_fast` — RTX 4060 Laptop 8 GB, max 2 escenarios concurrentes (HAPPO/MATD3), max 1 para MASAC/MAAC."
new3 = "- Perfil GPU Colab (oficial): `aws` — A100-SXM4-80GB 80 GiB VRAM, 3 escenarios concurrentes por algoritmo (`--parallel-scenarios 3`). Perfil local de referencia: `local4060_fast` (RTX 4060 8 GiB, 1-2 escenarios)."
txt, m = rep(old3, new3, "3-gpuprofile")
msg.append(m)

# 4. Tiempos section title
old4 = "### Tiempos reales corrida v3 (referencia valida)"
new4 = "### Tiempos reales corrida v3 (referencia historica — RTX 4060 Laptop 5 ep piloto)"
txt, m = rep(old4, new4, "4-tiempos-title")
msg.append(m)

# 5. Insert A100 timing table after MAAC row in timing table
old5 = "### Cambios aplicados en v3 y v4"
new5 = (
    "### Tiempos estimados corrida oficial A100-SXM4-80GB (50 ep, --parallel-scenarios 3)\n"
    "\n"
    "| Algoritmo | FPS estimado A100 | Tiempo total (3 escenarios paralelos) | Nota |\n"
    "| --------- | ----------------: | ------------------------------------: | ---- |\n"
    "| HAPPO | ~11 FPS | ~11 h | Dominado por simulador Python |\n"
    "| MASAC | ~5 FPS | ~45 h | Buffer 40 GiB en RAM; critico GPU |\n"
    "| MATD3 | ~8 FPS | ~23 h | GPU-intensivo; A100 13x RTX 4060 |\n"
    "| MAAC | ~6 FPS | ~26 h | Attention SAC |\n"
    "| **Total** | | **~4-5 dias** | vs ~13 dias secuencial |\n"
    "\n"
    "FPS limitado principalmente por simulacion Python de 17 edificios. A100 acelera GPU training (MATD3 2 FPS -> 8 FPS) pero el simulador CityLearn es el cuello de botella dominante en HAPPO.\n"
    "\n"
    "### Cambios aplicados en v3 y v4"
)
txt, m = rep(old5, new5, "5-a100-timing")
msg.append(m)

# 6. Colab section: add hardware note + launch command
old6 = "El notebook ejecuta las 12 corridas (4 algoritmos × 3 escenarios) con `N_EPISODES=50` y genera los artefactos canonicos en `outputs/{ALGO}/{escenario}/`."
new6 = (
    "El notebook ejecuta las 12 corridas (4 algoritmos × 3 escenarios) con `N_EPISODES=50` y genera los artefactos canonicos en `outputs/{ALGO}/{escenario}/`.\n"
    "\n"
    "**Hardware requerido: NVIDIA A100-SXM4-80GB + 167 GiB RAM** (Colab Pro+ > runtime A100 High-RAM).\n"
    "\n"
    "Verificacion de hardware en celda 1.2 del notebook (salida esperada):\n"
    "\n"
    "```text\n"
    "[OK] GPU: NVIDIA A100-SXM4-80GB (80.0 GiB VRAM)\n"
    "[OK] RAM: ~167 GiB\n"
    "[OK] Python: 3.11.13 (Linux x86_64)\n"
    "[OK] CUDA: 12.4\n"
    "```\n"
    "\n"
    "Lanzar entrenamiento (celda 6 del notebook — ya configurada):\n"
    "\n"
    "```bash\n"
    "python -B CityLearn/scripts/colab_a100_official_launcher.py \\\n"
    "  --scenario ALL --seed 0 --episodes 50 --episode-time-steps 8760 \\\n"
    "  --parallel-scenarios 3 --masac-preload-batch-device cpu \\\n"
    "  --gpu-profile aws --cuda-memory-fraction 0.92 \\\n"
    "  --require-a100 --oom-retry --skip-completed --live-monitor\n"
    "```"
)
txt, m = rep(old6, new6, "6-colab-launch")
msg.append(m)

# 7. Perfil local section title
old7 = "### Perfil GPU-tuned local (RTX 4060 Laptop 8 GB)"
new7 = "### Perfil GPU-tuned local (referencia historica — RTX 4060 Laptop 8 GB)"
txt, m = rep(old7, new7, "7-local-title")
msg.append(m)

# 8. Cambios Recientes
old8 = (
    "## Cambios Recientes\n"
    "- **2026-06-20 17:42**: outputs/citylearn_v3_madrl_full_20260615_074011_v4/masac/escenario_1/checkpoint.pt, outputs/citylearn_v3_madrl_full_20260615_074011_v4/masac/escenario_2/checkpoint.pt, outputs/citylearn_v3_madrl_full_20260615_074011_v4/masac/escenario_3/checkpoint.pt, outputs/citylearn_v3_madrl_full_20260615_074011_v4/resumen_comparativo/global_comparison.png (+7 mas)\n"
    "- **2026-06-20 17:28**: tools/generate_informe_final.py, tools/test_notebook_cells.py, tools/verify_notebook.py, tools/verify_workflow_integrity.py\n"
    "- **2026-06-20 15:55**: tools/fix_clone_submodule.py\n"
    "- **2026-06-20 15:50**: README.md, tools/fix_colab_cell2.py, tools/generate_informe_final.py, tools/patch_notebook_final.py\n"
    "- **2026-06-20 15:47**: tools/generate_informe_final.py, tools/patch_notebook_final.py\n"
    "- **2026-06-20 11:47**: docs/workflow_manifest.json, scripts/restart_happo_masac_v3.ps1, scripts/restart_masac_matd3_maac.ps1, scripts/run_3madrl_parallel.ps1 (+3 mas)\n"
    "- **2026-06-20 11:27**: tools/verify_notebook.py\n"
    "- **2026-06-20 11:11**: tools/verify_notebook.py\n"
    "- **2026-06-20 11:02**: tools/verify_notebook.py\n"
    "- **2026-06-20 10:41**: nb_gpu_cells.txt, tools/patch_notebook_a100.py, tools/verify_notebook.py\n"
    "- **2026-06-20 10:30**: nb_cells.txt, nb_cells2.txt, nb_keycells.txt, tools/verify_notebook.py"
)
new8 = (
    "## Cambios Recientes\n"
    "- **2026-06-20 (actual)**: `madrl_citylearn_v3_tutorial.ipynb` — actualizado a A100-SXM4-80GB (80 GiB VRAM, 167 GiB RAM, CUDA 12.4); eliminadas todas las referencias RTX 4060 como entorno objetivo; MIN_VRAM 39→78 GiB, MIN_RAM 60→120 GiB, --gpu-profile local→aws\n"
    "- **2026-06-20 (actual)**: `colab_a100_official_launcher.py` — `--parallel-scenarios 3` (ThreadPoolExecutor), hyperparams A100-80GB (HAPPO hidden 512, MATD3 buffer 1M batch 1024, MASAC buffer 40 GiB CPU), manifest thread-safe con threading.Lock\n"
    "- **2026-06-20 17:42**: outputs/citylearn_v3_madrl_full_20260615_074011_v4 — masac checkpoints E1/E2/E3, resumen_comparativo/global_comparison.png (+7 mas)\n"
    "- **2026-06-20 17:28**: tools/generate_informe_final.py, tools/test_notebook_cells.py, tools/verify_notebook.py, tools/verify_workflow_integrity.py\n"
    "- **2026-06-20 15:50**: README.md, tools/fix_colab_cell2.py, tools/generate_informe_final.py, tools/patch_notebook_final.py\n"
    "- **2026-06-20 11:47**: docs/workflow_manifest.json, scripts/restart_happo_masac_v3.ps1, scripts/restart_masac_matd3_maac.ps1, scripts/run_3madrl_parallel.ps1 (+3 mas)"
)
txt, m = rep(old8, new8, "8-recientes")
msg.append(m)

readme.write_text(txt, encoding='utf-8')
for m in msg:
    print(m)
print("Done. RTX 4060 count now:", txt.count('RTX 4060'))
print("A100-SXM4-80GB count now:", txt.count('A100-SXM4-80GB'))
