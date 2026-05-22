"""Test pvlib ModelChain SAPM pipeline for Iquitos solar generation."""
import pvlib, pandas as pd, numpy as np, math, sys

print('pvlib:', pvlib.__version__)

# 1. Sandia module selection
mods = pvlib.pvsystem.retrieve_sam('SandiaMod')
mods = mods.T if mods.shape[0] < mods.shape[1] else mods
print('Mods shape (after T):', mods.shape)

mods['Pmp_stc']   = mods['Vmpo'] * mods['Impo']
mods['eta_stc']   = mods['Pmp_stc'] / (mods['Area'] * 1000)
mods['abs_Bvoco'] = mods['Bvoco'].abs()

cands = mods[
    ~mods.index.str.contains('CPV', case=False, na=False) &
    (mods['eta_stc'] >= 0.15) &
    (mods['Area'].between(1.5, 2.6)) &
    (mods['Pmp_stc'] >= 250)
].sort_values(by=['eta_stc', 'abs_Bvoco'], ascending=[False, True])

print(f'Candidates: {len(cands)}')
best_key = cands.index[0]
mp = mods.loc[best_key].to_dict()
pmp = mp['Vmpo'] * mp['Impo']
eta = pmp / (mp['Area'] * 1000)
print(f'Best module: {best_key}')
print(f'  Pmp={pmp:.0f}W  Area={mp["Area"]:.3f}m2  eta={eta:.1%}  |Bvoco|={abs(mp["Bvoco"]):.5f}')

# 2. Load cached weather
df = pd.read_parquet('.cache/weather/2023.parquet')
print('Weather shape:', df.shape)
print('  cols:', list(df.columns))
print('  tz:', df.index.tz)
print('  first:', df.index[0])

# 3. Inverter selection (pdc for 10 modules)
n_mod = 10
mps   = 5
n_strings = max(1, math.ceil(n_mod / mps))
pdc_w = n_mod * mp['Vmpo'] * mp['Impo']

invs = pvlib.pvsystem.retrieve_sam('SandiaInverter')
invs = invs.T if invs.shape[0] < invs.shape[1] else invs
cands_inv = invs[(invs['Pdco'] >= pdc_w * 0.5) & (invs['Pdco'] <= pdc_w * 2.0)].copy()
if cands_inv.empty:
    cands_inv = invs.iloc[:3].copy()
cands_inv['eta_inv'] = cands_inv['Paco'] / cands_inv['Pdco']
inv_key = cands_inv.sort_values('eta_inv', ascending=False).index[0]
inv_params = invs.loc[inv_key].to_dict()
print(f'Inverter: {inv_key}')

# 4. ModelChain SAPM
TEMP_PARAMS = pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_glass']
location = pvlib.location.Location(
    latitude=-3.7491, longitude=-73.2538, tz='America/Lima', altitude=106)

array = pvlib.pvsystem.Array(
    mount=pvlib.pvsystem.FixedMount(surface_tilt=5, surface_azimuth=0),
    module_parameters=mp,
    temperature_model_parameters=TEMP_PARAMS,
    modules_per_string=mps,
    strings=n_strings,
)
system = pvlib.pvsystem.PVSystem(arrays=[array], inverter_parameters=inv_params)
mc = pvlib.modelchain.ModelChain(
    system, location, aoi_model='sapm', spectral_model='sapm')

weather = df.rename(columns={
    'GHI': 'ghi', 'DHI': 'dhi', 'DNI': 'dni',
    'T2M': 'temp_air', 'WS': 'wind_speed',
})[['ghi', 'dhi', 'dni', 'temp_air', 'wind_speed']]

print('Running ModelChain...')
mc.run_model(weather)
ac = (mc.results.ac / 1000.0).clip(lower=0.0).fillna(0.0)
print(f'AC result: min={ac.min():.4f}  max={ac.max():.4f}  mean={ac.mean():.4f} kWh')
print(f'  non-zero hours: {int((ac>0).sum())} / {len(ac)}')
print('pvlib ModelChain SAPM: OK')
