#!/usr/bin/env python
"""Same no-storage and RBC baselines on two campaigns, recorded with their input hashes (D01/S10).

No policy is trained and test_2025 stays sealed. Energy totals follow the KPI contract: cost and CO2
on each building's signed net power, with the export credited (net billing). The comparison is
evidence for the owner's decision; it does not accept or retire a dataset.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import time

REPO = Path(__file__).resolve().parents[2]
SPLITS = ('train_2023', 'validation_2024')
POLICIES = ('no_storage_reference', 'rbc')
SCENARIO_CATALOG = REPO/'configs/scenarios.yaml'
BILL_TARIFFS = REPO/'data/tariffs/osinergmin/bill_tariffs.csv'


def hourly_cost_co2(trace):
    """District hourly cost and CO2, each building at its own price."""
    carbon = trace.district_series['carbon_intensity']
    cost, co2 = [0.0]*len(carbon), [0.0]*len(carbon)
    for series in trace.series_by_building.values():
        for t, (net, price) in enumerate(zip(series['net_power'], series['price'])):
            cost[t] += net*price*trace.hours_per_step
            co2[t] += net*carbon[t]*trace.hours_per_step
    return cost, co2


def pearson(x, y):
    """Pearson correlation, or None when a series is constant."""
    n = len(x)
    mean_x, mean_y = math.fsum(x)/n, math.fsum(y)/n
    var_x = math.fsum((v - mean_x)**2 for v in x)
    var_y = math.fsum((v - mean_y)**2 for v in y)
    if var_x <= 0 or var_y <= 0:
        return None
    return math.fsum((a - mean_x)*(b - mean_y) for a, b in zip(x, y))/math.sqrt(var_x*var_y)


def load_rates():
    from uc3m.application.evaluation.bill_cost import load_bill_tariffs
    return load_bill_tariffs(BILL_TARIFFS)


def summarize_trace(trace) -> dict:
    from uc3m.application.evaluation.bill_cost import bill_components
    hours = trace.hours_per_step
    nets = [s['net_power'] for s in trace.series_by_building.values()]
    district = [math.fsum(values) for values in zip(*nets)]
    cost, co2 = hourly_cost_co2(trace)
    bill = bill_components(trace, load_rates())
    if bill is None:
        raise ValueError('the trace has a building or month without an official bill rate')
    return {'bill_total_usd': bill['total_usd'], 'bill_energy_usd': bill['energy_usd'],
            'bill_demand_usd': bill['demand_usd'], 'bill_fixed_usd': bill['fixed_usd'],
            'net_mwh': math.fsum(district)*hours/1000.0,
            'import_mwh': math.fsum(max(v, 0.0) for net in nets for v in net)*hours/1000.0,
            'export_mwh': math.fsum(max(-v, 0.0) for net in nets for v in net)*hours/1000.0,
            'cost_usd': math.fsum(cost), 'co2_kg': math.fsum(co2),
            'district_peak_kw': max(district),
            'battery_throughput_kwh': math.fsum(v for s in trace.series_by_building.values()
                                                for v in s['battery_throughput']),
            'hourly_cost_co2_pearson': pearson(cost, co2)}


def price_seen(trace) -> dict:
    """The price the environment actually used, after the scenario's tariff policy."""
    prices = {b: s['price'] for b, s in trace.series_by_building.items()}
    return {'distinct_price_series': len({tuple(p) for p in prices.values()}),
            'max_values_per_building_price': max(len(set(p)) for p in prices.values()),
            'price_min': min(min(p) for p in prices.values()),
            'price_max': max(max(p) for p in prices.values()),
            'carbon_values': len(set(trace.district_series['carbon_intensity']))}


def paired_delta(control: dict, base: dict) -> dict:
    cost = control['cost_usd'] - base['cost_usd']
    co2 = control['co2_kg'] - base['co2_kg']
    # A net-exporting district has negative totals; the magnitude keeps + meaning worse.
    bill = control['bill_total_usd'] - base['bill_total_usd']
    return {'bill_usd': bill, 'bill_percent': 100.0*bill/abs(base['bill_total_usd']),
            'bill_demand_usd': control['bill_demand_usd'] - base['bill_demand_usd'],
            'bill_and_co2_same_direction': bill*co2 > 0,
            'cost_usd': cost, 'cost_percent': 100.0*cost/abs(base['cost_usd']),
            'co2_kg': co2, 'co2_percent': 100.0*co2/abs(base['co2_kg']),
            'net_mwh': control['net_mwh'] - base['net_mwh'],
            'peak_percent': 100.0*(control['district_peak_kw'] - base['district_peak_kw'])/base['district_peak_kw'],
            'cost_and_co2_same_direction': cost*co2 > 0}


def _run_campaign(name: str, split: str, seed: int, log) -> dict:
    from uc3m.adapters.citylearn import policy_inference as pi
    root = REPO/'data/campaigns'/name
    split_dir = root/'splits'/split
    classes = {'no_storage_reference': pi.NoStorageReferencePolicy, 'rbc': pi.RbcPolicy}
    runs = {}
    for policy_name in POLICIES:
        started = time.time()
        # Without the catalog CityLearn applies its legacy amplified tariff instead of the declared policy.
        run = pi.run_frozen_episode(split_dir, classes[policy_name](), root, seed=seed, scenario='E1',
                                    scenario_catalog=SCENARIO_CATALOG)
        runs[policy_name] = {**summarize_trace(run.trace), **price_seen(run.trace),
                             'completed_steps': run.completed_steps,
                             'training_updates': run.training_updates,
                             'split_sha256': run.contract['split_sha256'],
                             'exogenous_hash': run.trace.exogenous_hash,
                             'seconds': time.time() - started}
        log(f'{name} {policy_name}: {runs[policy_name]}')
    manifest = (root/'split_manifest.json').read_bytes()
    return {'split_manifest_sha256': hashlib.sha256(manifest).hexdigest(), 'runs': runs,
            'rbc_vs_no_storage': paired_delta(runs['rbc'], runs['no_storage_reference'])}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--campaigns', nargs='+', required=True, metavar='CAMPAIGN')
    parser.add_argument('--split', choices=SPLITS, default='validation_2024')
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    report = {'schema_version': 1, 'split': args.split, 'seed': args.seed,
              'policies': list(POLICIES), 'scientific_acceptance': False,
              'campaigns': {name: _run_campaign(name, args.split, args.seed, print) for name in args.campaigns}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False), encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
