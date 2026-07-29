#!/usr/bin/env python3
"""
Genera los PNG de arquitectura y flujo de trabajo CityLearn v3 MADRL
usando Chrome headless screenshot. Produce imágenes de alta resolución (1600px).
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
ARCH_DIR = Path(__file__).resolve().parents[2] / "docs" / "architecture"

# ─────────────────────────────────────────────────────────────────────────────
# HTML: ARQUITECTURA PROFESIONAL
# ─────────────────────────────────────────────────────────────────────────────
HTML_ARQUITECTURA = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'Segoe UI', Arial, sans-serif;
    background: #ffffff;
    padding: 28px 32px 32px 32px;
    width: 1600px;
  }
  h1 { font-size: 22px; font-weight: 700; color: #0f172a; margin-bottom: 4px; }
  .subtitle { font-size: 11px; color: #475569; margin-bottom: 20px; }
  .section-title {
    font-size: 13px; font-weight: 700; color: #1e3a5f;
    border-bottom: 2px solid #0891b2; padding-bottom: 4px; margin: 16px 0 10px 0;
  }
  .row { display: flex; gap: 12px; margin-bottom: 12px; }
  .box {
    flex: 1; border-radius: 8px; padding: 12px 14px; font-size: 11px;
    border: 1.5px solid; line-height: 1.5;
  }
  .box-title { font-weight: 700; font-size: 12px; margin-bottom: 6px; }
  .box-text { color: #475569; font-size: 10.5px; }
  /* colores por sección */
  .data  { background:#dbeafe; border-color:#2563eb; }
  .data .box-title { color:#1e40af; }
  .core  { background:#ccfbf1; border-color:#0f766e; }
  .core .box-title { color:#0f766e; }
  .gpu   { background:#ede9fe; border-color:#7c3aed; }
  .gpu .box-title { color:#6d28d9; }
  .marl  { background:#fef3c7; border-color:#d97706; }
  .marl .box-title { color:#b45309; }
  .algo  { background:#f0fdf4; border-color:#16a34a; }
  .algo .box-title { color:#15803d; }
  .axis  { background:#fef9c3; border-color:#ca8a04; }
  .axis .box-title { color:#a16207; }
  .contrib { background:#fce7f3; border-color:#db2777; }
  .contrib .box-title { color:#be185d; }
  /* backend row */
  .happo { background:#e0f2fe; border-color:#0284c7; }
  .happo .box-title { color:#0369a1; }
  .masac { background:#dcfce7; border-color:#16a34a; }
  .masac .box-title { color:#15803d; }
  .matd3 { background:#ede9fe; border-color:#7c3aed; }
  .matd3 .box-title { color:#6d28d9; }
  .maac  { background:#fee2e2; border-color:#ef4444; }
  .maac  .box-title { color:#b91c1c; }
  /* legend */
  .legend {
    display: flex; gap: 16px; flex-wrap: wrap; align-items: center;
    border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px 12px;
    background: #f8fafc; font-size: 10px; margin-bottom: 12px;
  }
  .legend-item { display: flex; align-items: center; gap: 5px; }
  .legend-dot { width: 12px; height: 12px; border-radius: 3px; }
  /* estado corrida */
  .ok   { color: #15803d; font-weight: 700; }
  .run  { color: #b45309; font-weight: 700; }
  .pend { color: #6b7280; }
  .badge {
    display: inline-block; font-size: 9px; font-weight: 700;
    padding: 1px 6px; border-radius: 10px; vertical-align: middle;
  }
  .badge-ok   { background:#dcfce7; color:#15803d; border:1px solid #86efac; }
  .badge-run  { background:#fef3c7; color:#b45309; border:1px solid #fcd34d; }
  .badge-pend { background:#f1f5f9; color:#64748b; border:1px solid #cbd5e1; }
  tag { font-size: 9.5px; font-family: Consolas, monospace; background: #f1f5f9;
        border-radius: 3px; padding: 1px 5px; color: #334155; }
  .divider { border: none; border-top: 1px solid #e2e8f0; margin: 14px 0; }
</style>
</head>
<body>

<h1>Arquitectura profesional CityLearn v3 MADRL</h1>
<div class="subtitle">Proyecto: Multi-agente de aprendizaje por refuerzo profundo para gestión coordinada de flexibilidad energética, emisiones de carbono y eficiencia económica en comunidades inteligentes. · Actualizado: 2026-06-15</div>

<!-- ROW 1: pipeline de datos -->
<div class="section-title">Pipeline de datos y simulador</div>
<div class="row">
  <div class="box data">
    <div class="box-title">Dataset oficial</div>
    <div class="box-text">
      <tag>citylearn_iquitos_2023_2025</tag><br>
      17 edificios reales Iquitos<br>
      26,304 h · 222 CSV · 0 NaN<br>
      PV 48,790 kWp · BESS 26,266 kWh<br>
      EV 185 tomas · 749 kW · 1,850 vehículos
    </div>
  </div>
  <div class="box core">
    <div class="box-title">CityLearn v2 base</div>
    <div class="box-text">
      <tag>CityLearn/citylearn</tag><br>
      Simulador físico · energía<br>
      KPIs v2 · precios · carbono<br>
      edificios · DERs · EVs<br>
      Conservado como núcleo
    </div>
  </div>
  <div class="box core">
    <div class="box-title">Capa CityLearn v3</div>
    <div class="box-text">
      <tag>CityLearn/citylearn/v3/</tag><br>
      environment.py · objectives.py<br>
      config.py · backends.py<br>
      scenario_manager.py (E1/E2/E3)<br>
      CityLearnV3MADRLRewardFunction
    </div>
  </div>
  <div class="box contrib">
    <div class="box-title">Aportes originales al simulador</div>
    <div class="box-text">
      A1 Degradación BESS C-rate + Arrhenius LiFePO4<br>
      A2 Corrección PV temperatura tropical (IEC 61215)<br>
      A3 KPI pico ventana facturación OSINERGMIN MT<br>
      A4 Intensidad carbono dinámica diesel+PV<br>
      <span style="font-size:9px;color:#db2777;">fork: Mac-Tapia/CityLearn.git · commit 54b1938e</span>
    </div>
  </div>
  <div class="box gpu">
    <div class="box-title">Ejecución GPU</div>
    <div class="box-text">
      Python 3.9 · Torch 2.8.0+cu126<br>
      RTX 4060 Laptop · 8,188 MiB<br>
      Driver 560.94 · CUDA 12.6<br>
      cuda_fraction 0.812<br>
      GpuProfile: local4060_fast
    </div>
  </div>
</div>

<!-- ROW 2: formulación multiagente -->
<div class="section-title">Formulación multiagente</div>
<div class="row">
  <div class="box marl">
    <div class="box-title">Dec-POMDP descentralizado</div>
    <div class="box-text">
      17 edificios = 17 agentes<br>
      Obs. local: 54–327 dim/edificio<br>
      Acción local: 2–44 dim/edificio<br>
      Política: πᵢ(aᵢ | oᵢ) — solo obs local<br>
      Ejecución completamente descentralizada
    </div>
  </div>
  <div class="box marl">
    <div class="box-title">CTDE — Critic centralizado</div>
    <div class="box-text">
      Critic: Q(s, a₁,…,a₁₇) o V(s)<br>
      Estado global: s = [o₁,…,o₁₇]<br>
      team_reward = mean(rᵢ)<br>
      mixed_reward = 0.30·rᵢ + 0.70·team_r<br>
      reward_aggregation: team_mean
    </div>
  </div>
  <div class="box marl">
    <div class="box-title">Multiobjetivo — Escalarización lineal</div>
    <div class="box-text">
      r = w₁·flex + w₂·CO₂ + w₃·costo + w₄·EV<br>
      E1: w=(0.70, 0.15, 0.15, ~) → flexibilidad<br>
      E2: w=(0.15, 0.70, 0.15, ~) → carbono<br>
      E3: w=(0.25, 0.15, 0.60, ~) → costos<br>
      Pesos por eje + perfil por algoritmo
    </div>
  </div>
  <div class="box marl">
    <div class="box-title">Adaptador común</div>
    <div class="box-text">
      <tag>citylearn_v3_training_common.py</tag><br>
      Normalización · trazas · figuras<br>
      live_progress.json · trace.csv<br>
      timeseries.csv · checkpoint_manifest<br>
      KPIs por eje · tablas · reportes
    </div>
  </div>
</div>

<!-- ROW 3: backends -->
<div class="section-title">Backends MADRL oficiales</div>
<div class="legend">
  <b>Leyenda:</b>
  <div class="legend-item"><div class="legend-dot" style="background:#0284c7"></div>HAPPO · On-policy</div>
  <div class="legend-item"><div class="legend-dot" style="background:#16a34a"></div>MASAC · Off-policy + QMIX</div>
  <div class="legend-item"><div class="legend-dot" style="background:#7c3aed"></div>MATD3 · Off-policy actor-critic</div>
  <div class="legend-item"><div class="legend-dot" style="background:#ef4444"></div>MAAC · Attention actor-critic</div>
  <div class="legend-item"><div class="legend-dot" style="background:#f1f5f9;border:1px solid #94a3b8"></div>Simulador / entorno</div>
</div>
<div class="row">
  <div class="box happo">
    <div class="box-title">HAPPO</div>
    <div class="box-text">
      <tag>train_citylearn_v3_happo.py</tag><br>
      Wrapper: CityLearnHARLEnv<br>
      Backend: external/HARL<br>
      Tipo: on-policy · hidden 256<br>
      ~66 min/escenario (E1+E2 paralelo)
    </div>
  </div>
  <div class="box masac">
    <div class="box-title">MASAC</div>
    <div class="box-text">
      <tag>train_citylearn_v3_masac.py</tag><br>
      Wrapper: CityLearnSMACDiscreteEnv<br>
      Backend: external/MARL/src<br>
      Tipo: off-policy · QMIX · discrete<br>
      ~126-148 min/escenario (secuencial)
    </div>
  </div>
  <div class="box matd3">
    <div class="box-title">MATD3</div>
    <div class="box-text">
      <tag>train_citylearn_v3_matd3.py</tag><br>
      Wrapper: CityLearnOffPolicyVecEnv<br>
      Backend: external/off-policy<br>
      Tipo: off-policy · doble critic<br>
      ~95 min/escenario (E1+E2 paralelo)
    </div>
  </div>
  <div class="box maac">
    <div class="box-title">MAAC</div>
    <div class="box-text">
      <tag>train_citylearn_v3_maac.py</tag><br>
      Wrapper: CityLearnMAACVecEnv<br>
      Backend: external/MAAC<br>
      Tipo: off-policy · 4 attention heads<br>
      ~52 min/escenario (secuencial)
    </div>
  </div>
</div>

<!-- ROW 4: ejes -->
<div class="section-title">Tres ejes del proyecto — OE.1 / OE.2 / OE.3</div>
<div class="row">
  <div class="box axis">
    <div class="box-title">E1 / OE.1 — Flexibilidad energética</div>
    <div class="box-text">
      Pesos: flex=0.70 · CO₂=0.15 · costo=0.15<br>
      KPIs: peak_average · ramping_average<br>
      one_minus_load_factor_average<br>
      Uso PV · BESS · EV · autoconsumo<br>
      Pregunta: ¿MADRL reduce pico distrital?
    </div>
  </div>
  <div class="box axis">
    <div class="box-title">E2 / OE.2 — Emisiones de CO₂</div>
    <div class="box-text">
      Pesos: flex=0.15 · CO₂=0.70 · costo=0.15<br>
      KPIs: carbon_emissions_total<br>
      carbon_emissions_delta<br>
      Gestión carbon-aware · red diesel aislada<br>
      CI(t) = 0.790 × (1 − 0.15 × GHI/1000)
    </div>
  </div>
  <div class="box axis">
    <div class="box-title">E3 / OE.3 — Costos energéticos</div>
    <div class="box-text">
      Pesos: flex=0.25 · CO₂=0.15 · costo=0.60<br>
      KPIs: electricity_cost_total<br>
      electricity_cost_delta · cost_peak_average<br>
      Tarifa TOU: 0.26/0.38 USD/kWh<br>
      Arbitraje tarifario y respuesta a demanda
    </div>
  </div>
</div>

<!-- ROW 5: estado actual -->
<div class="section-title">Estado actual de entrenamiento (2026-06-15)</div>
<div class="row">
  <div class="box" style="background:#f0fdf4;border-color:#16a34a;flex:1.4;">
    <div class="box-title" style="color:#15803d;">Corrida v3 — COMPLETADA <span class="badge badge-ok">✓ 12/12</span></div>
    <div class="box-text">
      <tag>outputs/citylearn_v3_madrl_full_20260613_010234</tag><br>
      HAPPO E1/E2/E3 ✓ · MASAC E1/E2/E3 ✓ · MATD3 E1/E2/E3 ✓ · MAAC E1/E2/E3 ✓<br>
      Perfil: recompensa v3 base · status: completed · duración total: ~5.5 h
    </div>
  </div>
  <div class="box" style="background:#fffbeb;border-color:#f59e0b;flex:1.6;">
    <div class="box-title" style="color:#b45309;">Corrida v4 — EN CURSO <span class="badge badge-run">⟳ 6/12</span> (re-run definitivo)</div>
    <div class="box-text">
      <tag>outputs/citylearn_v3_madrl_full_20260615_074011_v4</tag><br>
      HAPPO ✓ (66/66/58 min) · MASAC ✓ (126/148/136 min) · MATD3 ⟳ E1+E2 corriendo · MAAC ⏳ pendiente<br>
      Perfil: BESS penalty C-rate/Arrhenius + EV urgency · KPIs de tesis al completarse
    </div>
  </div>
</div>

</body>
</html>"""

# ─────────────────────────────────────────────────────────────────────────────
# HTML: FLUJO DE TRABAJO OFICIAL
# ─────────────────────────────────────────────────────────────────────────────
HTML_FLUJO = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'Segoe UI', Arial, sans-serif;
    background: #ffffff;
    padding: 28px 32px 32px 32px;
    width: 1600px;
  }
  h1 { font-size: 21px; font-weight: 700; color: #0f172a; margin-bottom: 3px; }
  .subtitle { font-size: 11px; color: #475569; margin-bottom: 18px; }
  .section-title {
    font-size: 13px; font-weight: 700; color: #1e3a5f;
    border-bottom: 2px solid #0891b2; padding-bottom: 4px; margin: 14px 0 10px 0;
  }
  .row { display: flex; gap: 12px; margin-bottom: 12px; }
  .box {
    flex: 1; border-radius: 8px; padding: 11px 13px; font-size: 11px;
    border: 1.5px solid; line-height: 1.5;
  }
  .box-title { font-weight: 700; font-size: 12px; margin-bottom: 5px; }
  .box-text  { color: #475569; font-size: 10.5px; }

  .step { background:#dbeafe; border-color:#2563eb; }
  .step .box-title { color:#1e40af; }
  .step .num {
    display:inline-block; background:#2563eb; color:#fff; border-radius:50%;
    width:20px; height:20px; text-align:center; line-height:20px;
    font-size:11px; font-weight:700; margin-right:6px; vertical-align:middle;
  }

  .art   { background:#ccfbf1; border-color:#0f766e; }
  .art .box-title   { color:#0f766e; }
  .fig   { background:#ede9fe; border-color:#7c3aed; }
  .fig .box-title   { color:#6d28d9; }
  .bench { background:#fee2e2; border-color:#ef4444; }
  .bench .box-title { color:#b91c1c; }
  .cmp   { background:#fef3c7; border-color:#d97706; }
  .cmp .box-title   { color:#b45309; }
  .ok-box { background:#f0fdf4; border-color:#16a34a; }
  .ok-box .box-title { color:#15803d; }
  .run-box { background:#fffbeb; border-color:#f59e0b; }
  .run-box .box-title { color:#b45309; }

  tag { font-size: 9.5px; font-family: Consolas, monospace; background: #f1f5f9;
        border-radius: 3px; padding: 1px 5px; color: #334155; }
  code { font-family: Consolas, monospace; font-size: 9.5px; background: #f1f5f9;
         border-radius: 3px; padding: 0 3px; }

  /* matriz */
  table { width: 100%; border-collapse: collapse; font-size: 10.5px; margin: 8px 0; }
  th { background: #1e3a5f; color: #fff; padding: 7px 10px; text-align: center; font-weight: 600; }
  td { padding: 6px 10px; border: 1px solid #cbd5e1; text-align: center; }
  tr:nth-child(even) td { background: #f8fafc; }
  td.algo { background: #fff; font-weight: 600; text-align: left; }
  .cell-ok   { background:#dcfce7; color:#15803d; font-weight:700; }
  .cell-run  { background:#fef3c7; color:#b45309; font-weight:700; }
  .cell-pend { background:#f1f5f9; color:#6b7280; }
  .badge {
    display:inline-block; font-size:9px; font-weight:700;
    padding:1px 6px; border-radius:10px;
  }
  .badge-ok   { background:#dcfce7; color:#15803d; border:1px solid #86efac; }
  .badge-run  { background:#fef3c7; color:#b45309; border:1px solid #fcd34d; }
  .badge-pend { background:#f1f5f9; color:#64748b; border:1px solid #cbd5e1; }
</style>
</head>
<body>

<h1>Flujo de trabajo oficial de entrenamiento, evaluación y comparación</h1>
<div class="subtitle">Secuencia reproducible para lanzar los 4 MADRL sobre los tres ejes del proyecto y comparar CityLearn v2 contra CityLearn v3. · Actualizado: 2026-06-15</div>

<!-- pasos -->
<div class="section-title">Secuencia de pasos</div>
<div class="row">
  <div class="box step">
    <div class="box-title"><span class="num">1</span>Preparación</div>
    <div class="box-text">
      <code>verify_project_context.ps1</code><br>
      Python 3.9 · Torch 2.8.0+cu126<br>
      CUDA 12.6 · dataset 17 edificios<br>
      222 CSV · EV/V2G · PV · BESS<br>
      <code>check_training_dataset_ready.py</code>
    </div>
  </div>
  <div class="box step">
    <div class="box-title"><span class="num">2</span>Smoke test</div>
    <div class="box-text">
      <code>run_citylearn_v3_env_smoke.py</code><br>
      --scenario E1 --steps 3<br>
      Verifica carga CityLearn + dataset<br>
      <code>check_citylearn_v3_training_ready.py</code><br>
      Sin entrenamiento real
    </div>
  </div>
  <div class="box step">
    <div class="box-title"><span class="num">3</span>Launcher ALL</div>
    <div class="box-text">
      <code>run_citylearn_v3_full_training_visible.ps1</code><br>
      -Scenario ALL · -Episodes 75 · -Cuda<br>
      -GpuProfile local4060_fast<br>
      12 jobs: 4 MADRL × 3 ejes<br>
      -ArtifactProfile efficient
    </div>
  </div>
  <div class="box step">
    <div class="box-title"><span class="num">4</span>Monitor vivo</div>
    <div class="box-text">
      <code>monitor_citylearn_v3_official_training.ps1</code><br>
      GPU · global_step · reward<br>
      KPIs costo · CO₂ · carga<br>
      <code>live_progress.json</code> · logs<br>
      <code>official_full_status.json</code>
    </div>
  </div>
  <div class="box step">
    <div class="box-title"><span class="num">5</span>Evidencia tesis</div>
    <div class="box-text">
      <code>generate_thesis_objective_evidence.py</code><br>
      <code>benchmark_citylearn_v2_agents.py</code><br>
      <code>compare_citylearn_v2_vs_v3_madrl.py</code><br>
      KPIs · estadística · ranking<br>
      Score_OG · Pareto · Borda
    </div>
  </div>
</div>

<!-- matriz -->
<div class="section-title">Matriz oficial de 12 corridas — Estado (corrida v4: 2026-06-15)</div>
<table>
  <thead>
    <tr>
      <th style="text-align:left;">Algoritmo / Modo</th>
      <th>E1 — Flexibilidad<br><small style="font-weight:400">w_flex=0.70</small></th>
      <th>E2 — CO₂<br><small style="font-weight:400">w_CO₂=0.70</small></th>
      <th>E3 — Costos<br><small style="font-weight:400">w_costo=0.60</small></th>
      <th>Concurrencia</th>
      <th>Tiempo/escenario</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td class="algo">HAPPO <small style="color:#64748b">on-policy · hidden 256</small></td>
      <td class="cell-ok">✓ completado<br><small>happo/E1_seed_0</small></td>
      <td class="cell-ok">✓ completado<br><small>happo/E2_seed_0</small></td>
      <td class="cell-ok">✓ completado<br><small>happo/E3_seed_0</small></td>
      <td>2 paralelo → 1 sec</td>
      <td>66.5 · 66.2 · 57.8 min</td>
    </tr>
    <tr>
      <td class="algo">MASAC <small style="color:#64748b">off-policy · QMIX · discrete</small></td>
      <td class="cell-ok">✓ completado<br><small>masac/E1_seed_0</small></td>
      <td class="cell-ok">✓ completado<br><small>masac/E2_seed_0</small></td>
      <td class="cell-ok">✓ completado<br><small>masac/E3_seed_0</small></td>
      <td>1 secuencial</td>
      <td>125.9 · 148.3 · 135.7 min</td>
    </tr>
    <tr>
      <td class="algo">MATD3 <small style="color:#64748b">off-policy · doble critic</small></td>
      <td class="cell-run">⟳ corriendo<br><small>matd3/E1_seed_0</small></td>
      <td class="cell-run">⟳ corriendo<br><small>matd3/E2_seed_0</small></td>
      <td class="cell-pend">⏳ pendiente<br><small>matd3/E3_seed_0</small></td>
      <td>2 paralelo → 1 sec</td>
      <td>~95 · 95 · 81 min (v3)</td>
    </tr>
    <tr>
      <td class="algo">MAAC <small style="color:#64748b">off-policy · 4 attention heads</small></td>
      <td class="cell-pend">⏳ pendiente<br><small>maac/E1_seed_0</small></td>
      <td class="cell-pend">⏳ pendiente<br><small>maac/E2_seed_0</small></td>
      <td class="cell-pend">⏳ pendiente<br><small>maac/E3_seed_0</small></td>
      <td>1 secuencial</td>
      <td>~52 · 52 · 54 min (v3)</td>
    </tr>
  </tbody>
</table>
<div style="font-size:10px;color:#475569;margin-top:4px;">
  <span class="badge badge-ok">✓</span> completado exit_code=0 &nbsp;
  <span class="badge badge-run">⟳</span> en ejecución &nbsp;
  <span class="badge badge-pend">⏳</span> pendiente &nbsp;&nbsp;
  GPU: RTX 4060 Laptop 8,188 MiB · Torch 2.8.0+cu126 · 5 episodios · 8,760 pasos/ep · 43,800 env_steps/job
</div>

<!-- artefactos y cierre -->
<div class="section-title">Artefactos por corrida y cierre científico</div>
<div class="row">
  <div class="box art">
    <div class="box-title">Artefactos por job</div>
    <div class="box-text">
      <code>data/results.json</code><br>
      <code>data/training_summary.json</code><br>
      <code>data/timeseries.csv</code><br>
      <code>data/trace.csv</code><br>
      <code>data/checkpoint_manifest.json</code><br>
      <code>checkpoints/</code>
    </div>
  </div>
  <div class="box fig">
    <div class="box-title">Figuras y tablas</div>
    <div class="box-text">
      reward_timeseries.png<br>
      convergence_returns.png<br>
      axis_baseline_comparison.png<br>
      OE1_flexibility_kpis.png<br>
      OE2_co2_kpis.png<br>
      OE3_cost_kpis.png
    </div>
  </div>
  <div class="box bench">
    <div class="box-title">Baseline v2</div>
    <div class="box-text">
      <code>benchmark_citylearn_v2_agents.py</code><br>
      Agentes: baseline · hour_rbc<br>
      Mismo dataset Iquitos 2023-2025<br>
      Salida: <code>citylearn_v2_original_benchmark/</code><br>
      Línea base comparable con v3
    </div>
  </div>
  <div class="box cmp">
    <div class="box-title">Comparador maestro</div>
    <div class="box-text">
      <code>compare_citylearn_v2_vs_v3_madrl.py</code><br>
      --weights OE1=0.34,OE2=0.33,OE3=0.33<br>
      Score_OG · dominancia Pareto<br>
      Ranking Borda · MWU · Wilcoxon<br>
      Salida: <code>comparison_citylearn_v2_vs_v3_madrl/</code>
    </div>
  </div>
  <div class="box" style="background:#f0f9ff;border-color:#0891b2;">
    <div class="box-title" style="color:#0369a1;">Evidencia de tesis</div>
    <div class="box-text">
      <code>generate_thesis_objective_evidence.py</code><br>
      resumen_evidencia_tesis.md<br>
      matriz_resultados_madrl.csv<br>
      hipotesis_estadisticas_madrl.csv<br>
      thesis_skill_feed.json
    </div>
  </div>
</div>

<!-- criterio éxito -->
<div class="section-title">Criterio de resultado final válido</div>
<div class="row">
  <div class="box ok-box" style="flex:2;">
    <div class="box-title">Corrida válida para tesis</div>
    <div class="box-text" style="display:flex;gap:24px;">
      <div>
        ✓ <code>verify_project_context.ps1</code> pasa<br>
        ✓ Dataset readiness gate sin errores<br>
        ✓ <code>official_full_status.json</code> → status: completed<br>
        ✓ 12 jobs con exit_code = 0
      </div>
      <div>
        ✓ <code>data/results.json</code> + <code>timeseries.csv</code> + <code>trace.csv</code> por job<br>
        ✓ Sin Traceback/OOM/RuntimeError en logs<br>
        ✓ Benchmark v2 y comparador v2-v3 generados<br>
        ✓ Evidencia tesis desde corrida activa (no histórica)
      </div>
    </div>
  </div>
  <div class="box run-box">
    <div class="box-title">Corrida activa</div>
    <div class="box-text">
      <tag>outputs/citylearn_v3_madrl_full_20260615_074011_v4</tag><br>
      Perfil: BESS penalty + EV urgency (v4)<br>
      6/12 jobs completados · MATD3 corriendo<br>
      Referencia completa: corrida v3 (20260613)<br>
      <code>outputs/latest_visible_training_output_root.txt</code>
    </div>
  </div>
</div>

</body>
</html>"""


def screenshot_html(html_content: str, png_path: Path, width: int = 1600, height: int = 900):
    """Genera un PNG a partir de HTML usando Chrome headless screenshot."""
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", suffix=".html", delete=False,
        dir=png_path.parent
    ) as f:
        f.write(html_content)
        html_tmp = f.name

    try:
        url = f"file:///{html_tmp.replace(os.sep, '/')}"
        cmd = [
            CHROME,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            f"--window-size={width},{height}",
            "--hide-scrollbars",
            "--force-device-scale-factor=2",
            f"--screenshot={str(png_path.resolve())}",
            url,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if png_path.exists() and png_path.stat().st_size > 5000:
            print(f"  OK -> {png_path.name} ({png_path.stat().st_size // 1024} KB)")
            return True
        else:
            print(f"  ERROR: PNG no generado: {png_path.name}")
            if result.stderr:
                print(f"    stderr: {result.stderr[:300]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"  ERROR: timeout al generar {png_path.name}")
        return False
    finally:
        try:
            os.unlink(html_tmp)
        except Exception:
            pass


def main():
    if not os.path.exists(CHROME):
        print(f"ERROR: Chrome no encontrado en {CHROME}")
        sys.exit(1)
    print(f"Chrome: {CHROME}")

    jobs = [
        (HTML_ARQUITECTURA, ARCH_DIR / "ARQUITECTURA_CITYLEARN_V3_MADRL.png",     1600, 1080),
        (HTML_FLUJO,        ARCH_DIR / "FLUJO_TRABAJO_CITYLEARN_V3_MADRL.png",    1600, 1100),
    ]

    ok = 0
    for html, png_path, w, h in jobs:
        print(f"  Generando: {png_path.name}  ({w}×{h}×2 px)")
        if screenshot_html(html, png_path, width=w, height=h):
            ok += 1

    print(f"\nResumen: {ok}/{len(jobs)} PNGs generados.")


if __name__ == "__main__":
    main()
