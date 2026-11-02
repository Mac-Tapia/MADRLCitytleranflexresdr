"""Builders of fresh, synthetic campaign objects for the strict profile tests."""
from uc3m.domain.campaigns import CampaignSpec, TreatmentKey, canonical_hash


def fresh_spec(campaign_id='fresh_test_v1', **overrides):
    values = dict(
        campaign_id=campaign_id,
        algorithms=('HAPPO', 'MASAC', 'MATD3', 'MAAC'),
        scenarios=('E1', 'E2', 'E3'),
        development_seeds=(901, 902, 903),
        confirmatory_seeds=tuple(range(1001, 1013)),
        stage_budgets={'confirm': {'episodes': 50, 'episode_time_steps': 8760}},
        split_ids=('train_2023', 'validation_2024', 'test_2025'),
        policy_hash=canonical_hash({'policy': 'synthetic'}),
        storage_alias=campaign_id.removesuffix('_v1').removesuffix('_v2'),
    )
    values.update(overrides)
    return CampaignSpec(**values)


def treatment_key(spec, *, stage='confirm', algorithm='MATD3', scenario='E1', seed=1001):
    digest = lambda label: canonical_hash({'synthetic': label})  # noqa: E731
    return TreatmentKey(spec.campaign_id, stage, algorithm, scenario, seed, digest('config'),
                        digest('contract'), digest('normalizer'), digest('dataset'), digest('source'))
