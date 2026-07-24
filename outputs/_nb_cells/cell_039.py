# ── 5.1  Visualizar pesos de recompensa por escenario ────────────────────
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import os

WEIGHTS = {
    "E1": {"Flexibilidad": 0.70, "CO₂": 0.15, "Costo": 0.15},
    "E2": {"Flexibilidad": 0.15, "CO₂": 0.70, "Costo": 0.15},
    "E3": {"Flexibilidad": 0.25, "CO₂": 0.15, "Costo": 0.60},
}
TEAM_RATIO  = 0.70
LOCAL_RATIO = 0.30
N_AGENTS    = 17

COLORS = ["#3b82f6", "#22c55e", "#f59e0b"]
LABELS = list(WEIGHTS["E1"].keys())

fig, axes = plt.subplots(1, 3, figsize=(13, 6.0), sharey=True)
fig.suptitle("Pesos de recompensa por escenario (CityLearnV3MADRLRewardFunction v4)",
             fontsize=13, fontweight="bold")
for ax, (sc, wts), in zip(axes, WEIGHTS.items()):
    vals = list(wts.values())
    bars = ax.bar(LABELS, vals, color=COLORS, edgecolor="white", linewidth=1.5, width=0.55)
    ax.set_title(f"Escenario {sc}", fontsize=12, fontweight="bold")
    ax.set_ylim(0, 0.85)
    ax.tick_params(axis="x", rotation=15)
    ax.grid(axis="y", alpha=0.25)
    ax.set_facecolor("#f8fafc")
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                f"{v:.2f}", ha="center", fontsize=11, fontweight="bold")

plt.tight_layout()
plt.subplots_adjust(bottom=0.20)
# Formula annotation using Unicode (no LaTeX needed)
_local  = LOCAL_RATIO
_team   = TEAM_RATIO
_n      = N_AGENTS
_formula = (
    f"r_i_mix = {_local:.2f} × r_i_local  +  {_team:.2f} × mean(r₁,...,r₁₇)"
    f"          [team_ratio={_team}, local_ratio={_local}]"
)
fig.text(0.5, 0.05, _formula,
         ha="center", va="center", fontsize=12, style="italic",
         bbox=dict(boxstyle="round,pad=0.4", facecolor="#eff6ff",
                   edgecolor="#3b82f6", alpha=0.9))

os.makedirs(f"{OUTPUT_ROOT}/figures", exist_ok=True)
plt.savefig(f"{OUTPUT_ROOT}/figures/reward_weights.png", dpi=150, bbox_inches="tight")
plt.show()
print(f"✅  Figura: {OUTPUT_ROOT}/figures/reward_weights.png")

# ── Imprimir recompensa mixta CTDE ────────────────────────────────────────
SEP = "─" * 64
print("")
print(SEP)
print("  RECOMPENSA MIXTA CTDE  (Centralized Training, Decentralized Execution)")
print(SEP)
print(f"  r_i_mix = {LOCAL_RATIO:.2f} × r_i_local  +  {TEAM_RATIO:.2f} × mean(r₁,...,r₁{N_AGENTS})")
print(f"  local_ratio = {LOCAL_RATIO:.2f}   |   team_ratio = {TEAM_RATIO:.2f}   |   N_agentes = {N_AGENTS}")
print(SEP)
for sc, wts in WEIGHTS.items():
    print(f"  Escenario {sc}  r_i_local = " + " + ".join(f"{w:.2f}·{c}" for c, w in wts.items()))
    print(f"             r_i_mix  = {LOCAL_RATIO:.2f}·r_i_local + {TEAM_RATIO:.2f}·mean_equipo")
    print("             Pesos:   " + "   |   ".join(f"{c}={v:.2f}" for c, v in wts.items()))
    print("")
print(SEP)
