#  7.6  Benchmarks CityLearn v2 PPO/SAC/A2C (SB3 central-agent)
#
# Ejecutar solo despues de validar dataset y entorno. Estos scripts NO son MADRL v3:
# usan CityLearn v2 central_agent=True + StableBaselines3Wrapper sobre el mismo schema Iquitos.

CITYLEARN_V2_BENCHMARKS = ["PPO", "SAC", "A2C"]
RUN_CITYLEARN_V2_SB3_BENCHMARKS = False
SB3_BASELINE_SCENARIO = 'ALL'
SB3_BASELINE_TRAIN_EPISODES = 50
SB3_BASELINE_OUTPUT = str(Path(REPO) / 'outputs/citylearn_v2_original_benchmark')

if RUN_CITYLEARN_V2_SB3_BENCHMARKS:
    import subprocess
    sb3_scripts = {
        'ppo': 'CityLearn/scripts/benchmark_citylearn_v2_ppo.py',
        'sac': 'CityLearn/scripts/benchmark_citylearn_v2_sac.py',
        'a2c': 'CityLearn/scripts/benchmark_citylearn_v2_a2c.py',
    }
    for agent_name, script_rel in sb3_scripts.items():
        cmd = [
            PROJECT_PYTHON, '-B', str(Path(REPO) / script_rel),
            '--schema-path', SCHEMA_PATH,
            '--scenario', SB3_BASELINE_SCENARIO,
            '--seed', str(SEED),
            '--episode-time-steps', str(EPISODE_STEPS),
            '--train-episodes', str(SB3_BASELINE_TRAIN_EPISODES),
            '--output-dir', SB3_BASELINE_OUTPUT,
        ]
        print(f'[7.6] CityLearn v2 SB3 benchmark {agent_name.upper()}:')
        print(' '.join(map(str, cmd)))
        subprocess.check_call(cmd, cwd=REPO)
else:
    print('[7.6] PPO/SAC/A2C CityLearn v2 SB3 benchmarks desactivados por defecto.')
    print('      Activar RUN_CITYLEARN_V2_SB3_BENCHMARKS=True para generar artefactos comparables.')

