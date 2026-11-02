"""Best model selection: a descriptive candidate, kept apart from the inferential decision.

Descriptive rule (fixed on validation): highest mean hypervolume, ties broken by
lowest variance and then by algorithm id. It runs only over a complete campaign
whose algorithms all report finite statistics over the same positive number of
verified seeds. The candidate is not a winner: ``inferential_winner`` is set only
when the evaluation carries an omnibus test significant after Holm and a
significant post hoc comparison of that algorithm; a study may end without one.
"""
import math

ALPHA = 0.05


def _finite_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _inferential(evaluation: dict, candidates) -> tuple:
    inference = evaluation.get('inference')
    if not inference:
        return None, 'not_evaluated'
    p = inference.get('omnibus_p_holm')
    if not _finite_number(p) or not 0.0 <= p <= 1.0:
        raise ValueError('inference.omnibus_p_holm must be a finite p-value')
    winner = inference.get('winner')
    if p < ALPHA and inference.get('posthoc_significant') is True and winner in candidates:
        return winner, 'detected'
    return None, 'no_inferential_winner'


def select_best_model(evaluation: dict) -> dict:
    if not evaluation.get('campaign_complete'):
        raise ValueError("Cannot select best model from incomplete campaign")
    algorithms = evaluation['algorithms']
    seeds = set()
    for name, stats in algorithms.items():
        if not (_finite_number(stats.get('mean_hypervolume')) and _finite_number(stats.get('variance_hypervolume'))):
            raise ValueError(f"{name}: hypervolume statistics must be finite numbers")
        n_seeds = stats.get('n_seeds')
        if not isinstance(n_seeds, int) or isinstance(n_seeds, bool) or n_seeds <= 0:
            raise ValueError(f"{name}: n_seeds must be a positive count of verified runs")
        seeds.add(n_seeds)
    if len(seeds) != 1:
        raise ValueError(f"algorithms report different numbers of verified seeds: {sorted(seeds)}")
    ranked = sorted(
        algorithms.items(),
        key=lambda item: (-item[1]['mean_hypervolume'], item[1]['variance_hypervolume'], item[0]),
    )
    best_name, best_stats = ranked[0]
    inferential_winner, inferential_status = _inferential(evaluation, algorithms)
    return {
        'best_algorithm': best_name,
        'descriptive_candidate': best_name,
        'selection_kind': 'descriptive',
        'inferential_winner': inferential_winner,
        'inferential_status': inferential_status,
        'mean_hypervolume': best_stats['mean_hypervolume'],
        'variance_hypervolume': best_stats['variance_hypervolume'],
        'justification': (
            f"{best_name} has highest mean hypervolume "
            f"({best_stats['mean_hypervolume']:.4f}) with variance "
            f"{best_stats['variance_hypervolume']:.4f}; descriptive candidate, "
            f"inferential status: {inferential_status}"
        ),
        'ranking': [{'algorithm': name, **stats} for name, stats in ranked],
    }
