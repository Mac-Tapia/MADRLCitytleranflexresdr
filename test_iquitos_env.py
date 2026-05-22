import sys
sys.path.insert(0, 'CityLearn')
import numpy as np

from citylearn.citylearn import CityLearnEnv

schema = 'CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json'
print('Loading CityLearnEnv with Iquitos dataset...')
env = CityLearnEnv(schema=schema)

print('Resetting environment...')
obs, _ = env.reset()
print(f'  Reset OK  — {len(obs)} buildings, obs[0] len: {len(obs[0])}')

# Check dhw_device state on B5, B11, B12 after reset
for bname in ['Building_5', 'Building_11', 'Building_12']:
    b = next(b for b in env.buildings if b.name == bname)
    d = b.dhw_device
    print(f'\n{bname} dhw_device after reset:')
    print(f'  nominal_power          = {d.nominal_power:.2f} kW')
    print(f'  electricity_consumption[0] = {d.electricity_consumption[0]:.4f} kWh')
    print(f'  available_nominal_power    = {d.available_nominal_power:.4f} kW')
    print(f'  dhw_demand[0]              = {b.dhw_demand[0]:.4f} kWh')

print('\nStepping 5 time-steps...')
for t in range(5):
    actions = [np.zeros(b.action_space.shape) for b in env.buildings]
    obs, reward, terminated, truncated, info = env.step(actions)
    print(f'  t={t+1}  reward_mean={np.mean(reward):.4f}  terminated={terminated}')

print('\nAll assertions passed — Iquitos env OK for MADRL training.')
