import json

schema_path = 'CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json'
with open(schema_path, 'r', encoding='utf-8') as f:
    schema = json.load(f)

cooling_device_entry = {
    'type': 'citylearn.energy_model.HeatPump',
    'autosize': True,
    'attributes': {}
}

# Explicit nominal_power (kW) for dhw_device instead of autosize.
# Autosize fails because env.reset() calls update_energy_from_dhw_device() at t=0
# using outdoor_temp[0]=0°C (uninitialized) → COP≈1.80, consuming all nominal_power.
# Step then finds available_nominal_power≈0 and the demand>output assertion fires.
# Fix: set nominal_power >> (max_dhw_demand / COP_min) so that even after reset
# consumes electricity at t=0, plenty remains for the step.
#   B5  Hotel:    max dhw/h ≈ 74 kWh  → nominal_power 300 kW
#   B11 Hospital: max dhw/h ≈ 50 kWh  → nominal_power 300 kW
#   B12 EsSalud:  max dhw/h ≈ 33 kWh  → nominal_power 200 kW
DHW_NOMINAL_POWER = {
    'Building_5':  300,
    'Building_11': 300,
    'Building_12': 200,
}

dhw_buildings = {'Building_5', 'Building_11', 'Building_12'}

for bname, bdata in schema['buildings'].items():
    bdata['cooling_device'] = dict(cooling_device_entry)
    if bname in dhw_buildings:
        bdata['dhw_device'] = {
            'type': 'citylearn.energy_model.HeatPump',
            'autosize': False,
            'attributes': {
                'nominal_power': DHW_NOMINAL_POWER[bname]
            }
        }

with open(schema_path, 'w', encoding='utf-8') as f:
    json.dump(schema, f, indent=2, ensure_ascii=False)

# Verify
with open(schema_path, 'r', encoding='utf-8') as f:
    v = json.load(f)

ok = all('cooling_device' in v['buildings'][b] for b in v['buildings'])
dhw_ok = all('dhw_device' in v['buildings'][b] for b in dhw_buildings)
no_dhw_others = all('dhw_device' not in v['buildings'][b] for b in v['buildings'] if b not in dhw_buildings)

print(f'cooling_device in all 17 buildings: {ok}')
print(f'dhw_device in B5/B11/B12: {dhw_ok}')
print(f'dhw_device NOT in other buildings: {no_dhw_others}')

b1_cd = v['buildings']['Building_1']['cooling_device']
b5_dhw = v['buildings']['Building_5']['dhw_device']
b6_has_dhw = 'dhw_device' in v['buildings']['Building_6']

print(f'B1 cooling_device: {b1_cd}')
print(f'B5 dhw_device: {b5_dhw}')
print(f'B6 has dhw_device: {b6_has_dhw}')
