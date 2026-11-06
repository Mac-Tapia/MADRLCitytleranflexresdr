"""Adapter to existing HAPPO, MASAC, MATD3 and MAAC native launchers."""
from __future__ import annotations

import importlib
import os
import subprocess
import sys
import json
from pathlib import Path

from uc3m.application.configuration import load_scenario_catalog
from uc3m.application.training.layout import normalize_scenario_dir
from uc3m.domain.evidence import ArtifactRef
from uc3m.ports.learner import TrainingResult


class NativeBackend:
    def __init__(self, project_root: Path, schema_path: Path, *, episode_time_steps=None):
        self.project_root = Path(project_root).resolve()
        self.schema_path = Path(schema_path).resolve()
        self.episode_time_steps = episode_time_steps

    def command(self, spec, run_root, resume):
        if spec.algorithm not in {'HAPPO', 'MASAC', 'MATD3', 'MAAC'}:
            raise ValueError('Unsupported native algorithm')
        return [sys.executable, str(self.project_root/'CityLearn/scripts'/
                f'train_citylearn_v3_{spec.algorithm.lower()}.py'),
                '--schema-path', str(self.schema_path), '--scenario', spec.scenario.scenario_id,
                '--seed', str(spec.seed), '--episodes', str(spec.target_episodes),
                '--episode-time-steps', str(self.episode_time_steps or spec.episode_time_steps),
                '--output-dir', str(Path(run_root).resolve()/normalize_scenario_dir(spec.scenario.scenario_id, spec.seed)),
                '--artifact-profile', 'efficient'] + (
                    ['--num-env-steps', str(spec.target_episodes*spec.episode_time_steps)]
                    if spec.algorithm in {'HAPPO', 'MATD3'} else []) + list(spec.backend_args) + ([] if resume else ['--no-resume'])

    def execute(self, spec, run_root, resume):
        from uc3m.application.training.preflight import dataset_digest, source_snapshot, archive_sources
        if dataset_digest(self.schema_path) != spec.dataset_sha256:
            raise ValueError('dataset bytes differ from experiment identity')
        if not spec.source_sha256 or source_snapshot(self.project_root) != spec.source_sha256:
            raise ValueError('source bytes differ from experiment identity')
        archive = run_root/'source_snapshot.zip'
        if not archive.exists() and archive_sources(self.project_root, archive) != spec.source_sha256:
            raise ValueError('source changed while archiving')
        if self.episode_time_steps is not None and self.episode_time_steps != spec.episode_time_steps:
            raise ValueError('training horizon differs from experiment identity')
        catalog_path = self.project_root/'configs/scenarios.yaml'
        if load_scenario_catalog(catalog_path)[spec.scenario.scenario_id].fingerprint() != spec.scenario.fingerprint():
            raise ValueError('scenario catalog differs from experiment identity')
        env = dict(os.environ)
        env['UC3M_SCENARIO_CATALOG'] = str(catalog_path)
        env['PYTHONPATH'] = os.pathsep.join([str(self.project_root), str(self.project_root/'CityLearn'), env.get('PYTHONPATH', '')])
        from uc3m.adapters.process_tree import run_child
        with (run_root/'backend.log').open('a', encoding='utf-8') as stream:
            # A cancellable tree that ends with its launcher (SPEC-003 FR-003.5).
            return_code = run_child(self.command(spec, run_root, resume), cwd=self.project_root,
                                    env=env, stdout=stream, stderr=subprocess.STDOUT)
        return self._collect(spec, run_root, return_code)

    def recover(self, spec, run_root):
        """Index durable native artifacts after an interrupted matching run."""
        return self._collect(spec, run_root, 1)

    def _collect(self, spec, run_root, return_code):
        # Native completion remains stricter than process success: KPI audit,
        # checkpoint availability and completed episode evidence must all agree.
        scripts = str(self.project_root/'CityLearn/scripts')
        if scripts not in sys.path:
            sys.path.insert(0, scripts)
        common = importlib.import_module('citylearn_v3_training_common')
        output = run_root/normalize_scenario_dir(spec.scenario.scenario_id, spec.seed)
        from uc3m.adapters.algorithms.evidence import checkpoint_bundle, finite_kpis
        schema = json.loads(self.schema_path.read_text(encoding='utf-8'))
        agents = sum(1 for building in schema['buildings'].values() if building.get('include', True))
        bundle = set(checkpoint_bundle(output/'checkpoints', spec.algorithm, agents))
        payload = common.read_job_results_json(output) or {}
        numeric = finite_kpis(payload.get('citylearn_v3_report', {}).get('all_values'))
        complete = bool(bundle) and numeric and common.job_counts_as_launcher_complete(output, target_episodes=spec.target_episodes)
        count = common.infer_trustable_completed_episodes(output, algorithm=spec.algorithm.lower(),
            episode_time_steps=spec.episode_time_steps, rollout_threads=1,
            live_progress=common.read_live_progress_json(output))
        artifacts = []
        archive = run_root/'source_snapshot.zip'
        if archive.is_file():
            artifacts.append(ArtifactRef.from_file(run_root, archive, kind='source_snapshot',
                media_type='application/zip', producer='uc3m'))
        for path in sorted(output.rglob('*')):
            if not path.is_file() or path.suffix == '.tmp':
                continue
            kind = 'artifact'
            if path in bundle:
                kind = 'checkpoint'
            elif path.name == 'results.json' and complete:
                kind = 'kpi'
            elif path.name == 'training_summary.json':
                kind = 'training_summary'
            elif path.name == 'training_state.pt':
                kind = 'training_state'
            artifacts.append(ArtifactRef.from_file(run_root, path, kind=kind,
                media_type='application/octet-stream', producer=spec.algorithm))
        return TrainingResult(return_code, min(spec.target_episodes,
            spec.target_episodes if complete else count), tuple(artifacts))
