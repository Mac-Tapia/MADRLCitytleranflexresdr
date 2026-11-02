# Revisión de módulos propios, uno por uno

Cada módulo Python de uc3m tiene una fila. AST es revisión estructural automática, no certificación semántica. La columna de hallazgos enlaza los módulos cuyo comportamiento fue revisado manualmente en detalle. Archivos sin hallazgo siguen sujetos a sus tests y no se declaran libres de defectos.

| Archivo | Símbolos de primer nivel | Alcance | Hallazgos |
|---|---|---|---|
| `uc3m/__init__.py` | (inicialización/exportaciones) | manual_focused_plus_automatic | A15 |
| `uc3m/adapters/__init__.py` | (inicialización/exportaciones) | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/adapters/local_artifacts.py` | LocalArtifactStore | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/adapters/algorithms/__init__.py` | (inicialización/exportaciones) | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/adapters/algorithms/evidence.py` | checkpoint_bundle | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/adapters/algorithms/learning_observer.py` | LearningEvidence, _named_parameters, parameter_hash, LearningObserver | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/adapters/algorithms/native.py` | NativeBackend | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/adapters/algorithms/native_entrypoint.py` | trainer_script, native_arguments, load_native_common, attempt_isolation, _option, job_directory, salvage_reason, _bundle_hash, main | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/adapters/citylearn/__init__.py` | (inicialización/exportaciones) | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/adapters/citylearn/fresh_observations.py` | _limits_by_building, design_device_sizes, citylearn_limits, citylearn_periodic_limits, frozen_observation_limits, load_normalizer, smoke_splits | manual_focused_plus_automatic | A16 |
| `uc3m/adapters/citylearn/objectives.py` | project_reward_weights | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/adapters/citylearn/policy_inference.py` | RbcPolicy, NoStorageReferencePolicy, FrozenRun, _split_record, _storage_kwh, run_frozen_episode, load_native_policy | manual_focused_plus_automatic | A06,A08,A31 |
| `uc3m/adapters/citylearn/rbc_baseline.py` | run_rbc_baseline | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/algorithms/__init__.py` | (inicialización/exportaciones) | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/algorithms/factory.py` | AlgorithmFactory, _BaseAdapter, _HARLAdapter, _MARLlibAdapter, _OffPolicyAdapter | manual_focused_plus_automatic | A15 |
| `uc3m/application/__init__.py` | (inicialización/exportaciones) | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/application/configuration.py` | _mapping, _load_yaml_mapping, _load_objective_policies, load_scenario_catalog, project_runtime_config | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/application/sensitivity.py` | _weight_key, generate_weight_grid, ExperimentMatrix | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/application/artifacts/__init__.py` | (inicialización/exportaciones) | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/application/artifacts/backup.py` | _digest, _inside, _experiment_fingerprint, _load_evidence, _write_checked, backup_run, RestoreReport, restore_run | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/application/artifacts/retention.py` | BackupVerificationError, _strings, _flag, ArtifactClass, RetentionPolicy | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/application/dataset/__init__.py` | (inicialización/exportaciones) | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/application/dataset/construction.py` | MonthlyRecord, _number, _read_text, _key, parse_billing_csv, energy_only_records, _flag_partial_months, _fit_usable, _year_shape, DeclaredBackcast, _backcast, complete_monthly_targets, write_monthly_targets, check_monthly_balance, DatasetBuildConfig, GeneratorRequest, DatasetBuildManifest, hash_directory, build_dataset | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/application/dataset/provenance.py` | sha256_file, _is_link, RawSource, RawSourceManifest, audit_raw_sources | manual_focused_plus_automatic | A09 |
| `uc3m/application/dataset/splits.py` | SplitRecord, SplitManifest, NormalizerSpec, _csv_references, _deactivate_future, effective_observation_names, assert_no_future_fields, _iso, _fix_devices, materialize_splits, fit_normalizer, apply_frozen_normalizer | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/application/evaluation/__init__.py` | (inicialización/exportaciones) | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/application/evaluation/baselines.py` | compute_rbc_baseline | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/application/evaluation/fresh_analysis.py` | rows_from_kpi_report, SeedTable, iqm, _statistic, bootstrap_ci, holm, clip_gains, hypervolume, FrozenProtocol, ScientificReport, _p_or_none, analyze_campaign | manual_focused_plus_automatic | A05,A13 |
| `uc3m/application/evaluation/kpi_contract.py` | _check_series, PhysicalTrace, KpiDefinition, KpiCatalog, load_kpi_catalog, KpiReport, ValidationResult, _Unavailable, _district_power, _require, _days, _quantity, _measure, _energy_balance, compute_fresh_kpis, validate_kpi_report | manual_focused_plus_automatic | A31 |
| `uc3m/application/evaluation/model_selection.py` | select_best_model | manual_focused_plus_automatic | A14 |
| `uc3m/application/evaluation/results_catalog.py` | AmbiguousCampaign, CampaignRun, resolve_results_root, discover_runs, campaign_layout | manual_focused_plus_automatic | A11 |
| `uc3m/application/evaluation/scientific_evaluation.py` | validate_kpis, compute_multiseed_stats, compute_pareto_summary | manual_focused_plus_automatic | A13 |
| `uc3m/application/evaluation/training_report.py` | build_training_report, TrainingReportBuilder | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/application/thesis/__init__.py` | (inicialización/exportaciones) | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/application/thesis/evidence_registry.py` | EvidenceRef, EvidenceRegistry | manual_focused_plus_automatic | A10 |
| `uc3m/application/training/__init__.py` | (inicialización/exportaciones) | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/application/training/cli.py` | native_learner, main | changed_during_audit_reverification_required | A01,A02,A27 |
| `uc3m/application/training/completion.py` | CompletionDecision, evaluate_completion | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/application/training/context.py` | validate_colab_context, verify_runtime_context, repository_revision | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/application/training/dataset_gate.py` | DatasetNotValidated, require_validated_dataset | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/application/training/fresh_campaign.py` | _strict, load_algorithm_config, load_campaign_config, effective_hyperparameters, resolve_native_arguments, sensitivity_weights, Treatment, CampaignDag, _distinct_candidates, build_dag, attempt_completion, _sha256, catalog_sha256, prepare_campaign, freeze_configuration, _is_candidate, write_configuration_freezes, load_configuration_freezes, write_derived_scenario_catalog, _treatment_key, _materialize, run_stage | changed_during_audit_reverification_required | A01,A02,A03,A04 |
| `uc3m/application/training/fresh_policy.py` | FreshInputError, RetiredHistoricalInput, ForeignCampaignInput, UntrustedCheckpoint, CampaignRootExists, CampaignRoots, load_layout, _roots_for, _check_root_path, _campaign_claim, create_campaign_roots, open_campaign_roots, _is_link, _under, _sha256, assert_campaign_input, _existing_attempts, attempt_base, create_attempt, read_attempt | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/application/training/layout.py` | storage_label, campaign_path, treatment_path, normalize_algorithm_dir, experiment_path, iter_evidence_paths, normalize_scenario_dir, job_run_relative_parts, resolve_job_run_dir, ensure_artifact_layout | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/application/training/lock.py` | run_lock | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/application/training/monitor.py` | list_runs | manual_focused_plus_automatic | A11 |
| `uc3m/application/training/persistence.py` | _atomic, write_json_atomic, _csv_safe, write_csv_atomic, append_csv_stable_schema, ProgressHeartbeat | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/application/training/preflight.py` | hash_files, dataset_digest, source_snapshot, _is_secret, fresh_source_paths, _scoped_paths, _source_paths, archive_sources | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/application/training/resume.py` | ResumePlan, plan_resume | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/application/training/runner.py` | read_manifest, ExperimentRunner | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/data/__init__.py` | (inicialización/exportaciones) | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/data/contracts.py` | DatasetValidationError, DatasetManifest | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/data/ports.py` | DatasetSource | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/data/registry.py` | _build_http, _build_s3, register_source, available_sources, build_source | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/data/adapters/__init__.py` | (inicialización/exportaciones) | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/data/adapters/local_csv.py` | LocalCsvDatasetAdapter | manual_focused_plus_automatic | A26 |
| `uc3m/data/adapters/remote_http.py` | RemoteHttpDatasetAdapter | manual_focused_plus_automatic | A26 |
| `uc3m/data/adapters/s3.py` | S3DatasetAdapter | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/domain/__init__.py` | (inicialización/exportaciones) | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/domain/campaigns.py` | canonical_hash, _require_sha256, _freeze, _thaw, CampaignStatus, CampaignSpec, TreatmentKey, AttemptIdentity, CampaignManifest, ConfigurationFreeze | changed_during_audit_reverification_required | A03 |
| `uc3m/domain/evidence.py` | _sha256, finite_kpis, verify_artifact, ArtifactRef, EvidenceManifest | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/domain/experiments.py` | RunStatus, ExperimentSpec, RunIdentity | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/domain/objectives.py` | ObjectiveAxis, RewardVector, HierarchyLevels, ObjectivePolicy, canonical_objective_policies | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/domain/pareto.py` | _matrix, _orientation, dominates, non_dominated_indices, hypervolume_3d, expected_utility, sparsity | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/domain/scenarios.py` | _fingerprint, TariffPolicy, ConstraintPolicy, ScenarioDefinition, ScenarioCatalog | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/env/__init__.py` | (inicialización/exportaciones) | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/env/bact.py` | _DefaultZeroDict, ClimateVector, building_type_code, BACTEncoder | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/env/uc3m_env.py` | _first_space_dimension, UC3MEnv | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/env/wrappers.py` | HARLWrapper, PettingZooWrapper | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/geography/__init__.py` | (inicialización/exportaciones) | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/geography/ingest.py` | UniversalDataIngester | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/governance/__init__.py` | (inicialización/exportaciones) | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/governance/foundation.py` | _load, validate_foundation_manifests | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/governance/open_source.py` | DependencyRecord, PolicyDecision, classify_license_text, OpenSourcePolicy | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/kpis/__init__.py` | (inicialización/exportaciones) | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/kpis/evaluator.py` | EpisodeKPIs, KPIEvaluator | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/multicriteria/__init__.py` | (inicialización/exportaciones) | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/multicriteria/ahp.py` | _principal_eigen, consistency_ratio, ahp_priority_weights, ahp_rank_alternatives, default_weights_or_ahp | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/multicriteria/artifacts.py` | pareto_quality_from_decision_matrix, default_results_root, resolve_run_dir, _safe_float, decision_matrix_from_district_objectives, merge_with_illustrative, _summary_table, episode_summary_path, load_episode_reward_series, training_stability_from_episode_rewards, load_real_c4c6_from_drive, load_decision_matrix | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/multicriteria/consolidation.py` | master_table_from_seed_metrics, decision_matrix_frame, learning_curve_bands, plot_learning_curves, plot_pareto_cost_co2_flex, plot_degradation_bars, save_consolidation_bundle | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/multicriteria/criteria.py` | SelectionCriterion, MetricAggregate, mean_std_report, aggregate_seed_values, total_operating_cost, co2_avoided, flexibility_activated, mean_cumulative_reward, violation_rate, mean_violation_severity, inter_seed_variance, reward_drop_count, steps_to_fraction_of_asymptotic, compute_time_per_1000_steps, reward_degradation, training_time_growth_slope, train_test_gap, forecast_noise_degradation, compute_dimension_metrics, criteria_manifest | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/multicriteria/pipeline.py` | _criteria_kind, run_selection_pipeline, _synthetic_learning_curves | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/multicriteria/reward.py` | MultiObjectiveWeights, _minmax, _zscore, normalize_components, multiobjective_reward, equal_step_budget_mask | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/multicriteria/scenarios.py` | ScenarioConfig, EmpiricalProtocol, list_scenarios | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/multicriteria/stats_tests.py` | _require_scipy, _finite, _clean_groups, _groups_dict, holm_correction, cliffs_delta, cliffs_delta_magnitude, epsilon_squared_kw, kendalls_w_from_friedman, rank_biserial_from_mwu, rank_biserial_from_wilcoxon, shapiro_wilk_per_group, fligner_killeen, kruskal_wallis, moods_median_test, _dunn_z_p, _tie_correction_factor, dunns_posthoc_holm, conover_iman_posthoc, mann_whitney_u, brunner_munzel, wilcoxon_signed_rank, pairwise_wilcoxon, pairwise_mann_whitney, pairwise_brunner_munzel, _block_matrix, friedman_test, nemenyi_posthoc, quade_test, scheirer_ray_hare, spearman_rho, kendall_tau, pages_trend_test, cochran_q, decide_oe_winner, validate_topsis_vs_friedman, sample_coverage, run_oe_battery, run_og_battery, run_full_methodology_battery, format_oe_report, format_og_report, format_full_report, significance_gate_top_metrics | manual_focused_plus_automatic | A14 |
| `uc3m/multicriteria/topsis.py` | decision_matrix_to_frame, vector_normalize, topsis_rank, weight_sweep_sensitivity, pareto_nondominated | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/ports/__init__.py` | (inicialización/exportaciones) | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/ports/artifact_store.py` | ArtifactStore | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/ports/learner.py` | TrainingResult, LearnerPort | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/ports/simulator.py` | SimulatorPort | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/presentation/__init__.py` | (inicialización/exportaciones) | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/presentation/training_panel.py` | make_server, main | manual_focused_plus_automatic | A11 |
| `uc3m/reward/__init__.py` | (inicialización/exportaciones) | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/reward/axes.py` | AxisValues, RewardAxes | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
| `uc3m/reward/hphi.py` | _hypervolume_2d, _hypervolume_nd, HPHI, compute_global_score | manual_focused_plus_automatic | A12 |
| `uc3m/reward/term_telemetry.py` | RewardTermDecomposition, _clip01, _local_terms, _build, decompose_citylearn_v3_breakdown, decompose_reward_function, verify_reward_decomposition | AST_and_text_review_automatic | sin hallazgo confirmado en esta revisión |
