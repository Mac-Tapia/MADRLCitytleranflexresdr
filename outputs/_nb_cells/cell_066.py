# ── 10.  Resumen final de la sesión Colab ───────────────────────────────────
import json
import glob
import os
from datetime import datetime

print("=" * 65)
print("  RESUMEN FINAL — MADRL CityLearn v3 · Colab A100")
print("=" * 65)
print(f"  Output root : {OUTPUT_ROOT}")
print(f"  Timestamp   : {TIMESTAMP}")
print(f"  Modo        : {'QUICK_TEST' if QUICK_TEST else 'FULL TRAINING (50 ep)'}")

n_json = len(glob.glob(f"{OUTPUT_ROOT}/**/*.json",  recursive=True))
n_csv  = len(glob.glob(f"{OUTPUT_ROOT}/**/*.csv",   recursive=True))
n_png  = len(glob.glob(f"{OUTPUT_ROOT}/**/*.png",   recursive=True))
n_ckpt = len(glob.glob(f"{OUTPUT_ROOT}/**/*.pt",    recursive=True))
print(f"\n  Artefactos : {n_json} JSON · {n_csv} CSV · {n_png} PNG · {n_ckpt} .pt")

if stat_results and "ranking" in stat_results:
    _best = stat_results.get("best_madrl", stat_results["ranking"][0]["algorithm"] if stat_results["ranking"] else "N/A")
    print("\n  ═══════════════════════════════════════════════════════════════")
    print(f"  MEJOR ALGORITMO MADRL SELECCIONADO: {_best}")
    print("  ═══════════════════════════════════════════════════════════════")
    print("\n  RANKING FINAL:")
    for i, r in enumerate(stat_results["ranking"], 1):
        mark = " ★" if i == 1 else ""
        print(f"    {i}. {r['algorithm']:<6} {r['mean_score']:.4f}{mark}")
    kw = stat_results.get("kruskal_wallis", {})
    if kw:
        print(f"  KW: p={kw.get('p','?')} ({'✅' if kw.get('significant') else ''})")
else:
    print("\n  Referencia oficial v4:")
    print("    1. MATD3  0.7445 ★")
    print("    2. MASAC  ~0.73")
    print("    3. MAAC   ~0.72")
    print("    4. HAPPO  ~0.70")
    print("    KW p=0.0459 ✅")

summary = {
    "timestamp":        TIMESTAMP,
    "output_root":      OUTPUT_ROOT,
    "run_context":      RUN_CONTEXT,
    "mode":             "quick_test" if QUICK_TEST else "full_training",
    "episodes":         EPISODES,
    "episode_steps":    EPISODE_STEPS,
    "num_env_steps":    NUM_ENV_STEPS,
    "algorithms":       ALGORITHMS,
    "scenarios":        SCENARIOS,
    "a100_tuning": {
        "happo_hidden_size"    : 512,
        "masac_buffer_episodes": 8,
        "masac_critic_batch"   : 1,
        "masac_rnn_hidden_dim" : 64,
        "masac_qmix_hidden"    : 32,
        "masac_hyper_hidden"   : 64,
        "masac_actor_samples"  : 10,
        "masac_critic_steps"   : 2,
        "masac_max_buf_gib"    : 12,
        "matd3_batch_size"     : 256,
        "matd3_buffer_size"    : 4096,
        "matd3_hidden_size"    : 256,
        "maac_batch_size"      : 512,
        "maac_buffer_length"   : 1000000,
        "maac_hidden_size"     : 768,
        "maac_num_updates"     : 16,
        "maac_attention_heads" : 8,
        "torch_threads"        : 4,
        "parallel_scenarios"   : 3,
    },
    "artifacts": {"json": n_json, "csv": n_csv, "png": n_png, "pt": n_ckpt},
    "statistical_analysis": stat_results if stat_results else "run training first",
}
with open(f"{OUTPUT_ROOT}/colab_session_summary.json", "w") as f:
    json.dump(summary, f, indent=2, default=str)

print(f"\n  ✅  Resumen: {OUTPUT_ROOT}/colab_session_summary.json")
print("=" * 65)