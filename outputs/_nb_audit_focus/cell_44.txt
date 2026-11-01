# ── 6.2  Prueba rapida de validacion — 1 episodio (NO es entrenamiento oficial) ──
# Solo verifica que el pipeline funciona. El entrenamiento oficial usa N_EPISODES=50 por corrida.
# Controla con QUICK_TEST: si True, ejecuta; si False, imprime instrucciones y sale.

_N_EPISODES_TEST = 1   # Prueba rapida: 1 episodio por corrida
_EPISODE_STEPS   = 168 # 1 semana en pasos horarios (rapido para validar)

print("=" * 70)
print("  PRUEBA RAPIDA DE VALIDACION — 1 episodio x algoritmo x escenario")
print("  Este bloque NO genera resultados de tesis.")
print("  Para entrenamiento oficial: ejecuta la Seccion 7 (N_EPISODES=50 por corrida).")
print("=" * 70)

if not globals().get('QUICK_TEST', False):
    print()
    print("  QUICK_TEST = False → prueba desactivada.")
    print("  Para activar: cambia QUICK_TEST = True en la celda 6.1.")
    print("  Para entrenamiento oficial: ejecuta directamente la celda 7.2.")
else:
    import subprocess
    import sys
    import os
    import json
    from pathlib import Path

    _REPO    = globals().get('REPO', '/content/MADRLCitytleranflexresdr')
    _PYTHON  = globals().get('PROJECT_PYTHON', globals().get('PYTHON', sys.executable))
    _SCHEMA  = globals().get('SCHEMA_PATH', f'{_REPO}/CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json')
    _LAUNCHER = f'{_REPO}/CityLearn/scripts/colab_a100_official_launcher.py'
    _OUT_ROOT = str(Path(globals().get('OUTPUT_ROOT', f'{_REPO}/outputs')) / 'quick_test')
    Path(_OUT_ROOT).mkdir(parents=True, exist_ok=True)

    _test_algos = ['happo', 'masac', 'matd3', 'maac']
    _test_scenarios = ['E1', 'E2', 'E3']
    _results_quick = {}

    for algo in _test_algos:
        for scenario in _test_scenarios:
            script = f'{_REPO}/CityLearn/scripts/train_citylearn_v3_{algo}.py'
            if not Path(script).exists():
                print(f"  [SKIP] {algo.upper()} {scenario}: script no encontrado")
                continue
            cmd = [
                _PYTHON, '-B', script,
                '--schema-path', _SCHEMA,
                '--scenario', scenario,
                '--episodes', str(_N_EPISODES_TEST),
                '--episode-time-steps', str(_EPISODE_STEPS),
                '--seed', '0',
                '--output-dir', f'{_OUT_ROOT}/{algo}/{scenario}_seed_0',
                '--gpu-profile', 'aws',
            ]
            print(f"  Probando {algo.upper()} {scenario} ...", end=' ', flush=True)
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=_REPO)
                ok = r.returncode == 0
                _results_quick[f'{algo}_{scenario}'] = 'OK' if ok else f'ERROR(exit={r.returncode})'
                print('OK' if ok else f'FALLO (exit={r.returncode})')
                if not ok:
                    print('    stderr:', r.stderr[-300:])
            except subprocess.TimeoutExpired:
                _results_quick[f'{algo}_{scenario}'] = 'TIMEOUT'
                print('TIMEOUT (>300s)')
            except Exception as e:
                _results_quick[f'{algo}_{scenario}'] = f'EXCEPTION({e})'
                print(f'EXCEPCION: {e}')

    ok_count = sum(1 for v in _results_quick.values() if v == 'OK')
    total    = len(_results_quick)
    print()
    print(f"  Resultado prueba rapida: {ok_count}/{total} corridas OK")
    if ok_count == total:
        print("  ✅ Pipeline validado. Procede a la Seccion 7 para el entrenamiento oficial (50 ep).")
    else:
        failed = [k for k, v in _results_quick.items() if v != 'OK']
        print(f"  ⚠️  Fallos: {failed}")
        print("     Revisa logs antes de ejecutar el entrenamiento oficial.")
