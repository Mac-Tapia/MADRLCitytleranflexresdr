# Real Drive MADRL Training Artifact Analysis

Source: `outputs/_drive_madrl/full_data`, downloaded from the user-provided Google Drive folder.
No synthetic time-series, trace, building KPI, or checkpoint values are generated.

## Complete Runs

MAAC-E1, MAAC-E2, MAAC-E3, MASAC-E1, MASAC-E2, MASAC-E3, MATD3-E1, MATD3-E2, MATD3-E3

## Missing Or Incomplete Artifacts

| algorithm   | scenario   | file                                   | exists   |   bytes |
|:------------|:-----------|:---------------------------------------|:---------|--------:|
| HAPPO       | E1         | timeseries.csv                         | False    |       0 |
| HAPPO       | E1         | trace.csv                              | False    |       0 |
| HAPPO       | E1         | building_kpis.csv                      | False    |       0 |
| HAPPO       | E1         | building_behavior_summary.csv          | False    |       0 |
| HAPPO       | E1         | building_observation_action_schema.csv | False    |       0 |
| HAPPO       | E1         | building_trace_sample.csv              | False    |       0 |
| HAPPO       | E1         | checkpoint_manifest.json               | False    |       0 |
| HAPPO       | E1         | results.json                           | False    |       0 |
| HAPPO       | E1         | training_summary.json                  | False    |       0 |
| HAPPO       | E2         | timeseries.csv                         | False    |       0 |
| HAPPO       | E2         | trace.csv                              | False    |       0 |
| HAPPO       | E2         | building_kpis.csv                      | False    |       0 |
| HAPPO       | E2         | building_behavior_summary.csv          | False    |       0 |
| HAPPO       | E2         | building_observation_action_schema.csv | False    |       0 |
| HAPPO       | E2         | building_trace_sample.csv              | False    |       0 |
| HAPPO       | E2         | checkpoint_manifest.json               | False    |       0 |
| HAPPO       | E2         | results.json                           | False    |       0 |
| HAPPO       | E2         | training_summary.json                  | False    |       0 |
| HAPPO       | E3         | timeseries.csv                         | False    |       0 |
| HAPPO       | E3         | trace.csv                              | False    |       0 |
| HAPPO       | E3         | building_kpis.csv                      | False    |       0 |
| HAPPO       | E3         | building_behavior_summary.csv          | False    |       0 |
| HAPPO       | E3         | building_observation_action_schema.csv | False    |       0 |
| HAPPO       | E3         | building_trace_sample.csv              | False    |       0 |
| HAPPO       | E3         | checkpoint_manifest.json               | False    |       0 |
| HAPPO       | E3         | results.json                           | False    |       0 |
| HAPPO       | E3         | training_summary.json                  | False    |       0 |

## District-Level Interpretation

Highest mean reward: MAAC-E2 with reward_mean=-0.523716.
Lowest mean district cost: MATD3-E1 with district_cost_mean=631.506.
Lowest mean district emissions: MAAC-E3 with district_emission_mean=1053.55.

## Building-Level Interpretation

Most negative electricity_cost_delta_eur row: MATD3-E1 Building_14 with electricity_cost_delta_eur=-3532.42.
Building tables preserve all 17 buildings per complete run.

## Controlled / Uncontrolled Equipment

Controlled action variables are read from `building_observation_action_schema.csv` (`variable_type == action`). Uncontrolled/base demand is read from the dataset audit `Carga_base_medida_MWh`; controlled scenario loads are EV plus machine loads from the same audit.

Equipment rows generated: 153.

## Checkpoints

| algorithm   | scenario   | backend              |   checkpoint_count_declared |   checkpoint_files_listed |   matd3_policies_with_checkpoints |   maac_checkpoint_episodes |   masac_checkpoint_groups | checkpoint_file_types   |   checkpoint_bytes_total |
|:------------|:-----------|:---------------------|----------------------------:|--------------------------:|----------------------------------:|---------------------------:|--------------------------:|:------------------------|-------------------------:|
| MAAC        | E1         | external/MAAC        |                          52 |                        52 |                                 0 |                         50 |                         0 | .pt                     |              41622957662 |
| MAAC        | E2         | external/MAAC        |                          52 |                        52 |                                 0 |                         50 |                         0 | .pt                     |              41622957662 |
| MAAC        | E3         | external/MAAC        |                          52 |                        52 |                                 0 |                         50 |                         0 | .pt                     |              41622957662 |
| MASAC       | E1         | external/MADRL-MASAC |                          12 |                        12 |                                 0 |                          0 |                         4 | .pkl                    |                  2554372 |
| MASAC       | E2         | external/MADRL-MASAC |                          12 |                        12 |                                 0 |                          0 |                         4 | .pkl                    |                  2554372 |
| MASAC       | E3         | external/MADRL-MASAC |                          12 |                        12 |                                 0 |                          0 |                         4 | .pkl                    |                  2554372 |
| MATD3       | E1         | external/off-policy  |                          34 |                        34 |                                17 |                          0 |                         0 | .pt                     |                149731036 |
| MATD3       | E2         | external/off-policy  |                          34 |                        34 |                                17 |                          0 |                         0 | .pt                     |                149731036 |
| MATD3       | E3         | external/off-policy  |                          34 |                        34 |                                17 |                          0 |                         0 | .pt                     |                149731036 |

## Generated Tables

- `tables/district_episode_kpis.csv`
- `tables/district_summary_by_algorithm_scenario.csv`
- `tables/building_behavior_summary_all.csv`
- `tables/building_kpis_all.csv`
- `tables/trace_agent_summary_by_building.csv`
- `tables/controlled_uncontrolled_equipment_by_building.csv`
- `tables/checkpoint_summary.csv`
- `tables/checkpoint_policy_files.csv`

## Generated Figures

- `figures/district_reward_by_episode.png`
- `figures/district_net_energy_by_episode.png`
- `figures/district_cost_summary.png`
- `figures/district_emission_summary.png`
- `figures/building_cost_delta_heatmap.png`
- `figures/building_carbon_delta_heatmap.png`
- `figures/controlled_actions_by_building.png`
- `figures/controlled_vs_uncontrolled_load_mwh.png`
- `figures/checkpoint_manifest_bytes.png`
