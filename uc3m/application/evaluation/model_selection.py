"""Best model selection: highest mean hypervolume, tiebreak by lowest variance."""


def select_best_model(evaluation: dict) -> dict:
    if not evaluation.get('campaign_complete'):
        raise ValueError("Cannot select best model from incomplete campaign")
    algorithms = evaluation['algorithms']
    ranked = sorted(
        algorithms.items(),
        key=lambda item: (-item[1]['mean_hypervolume'], item[1]['variance_hypervolume']),
    )
    best_name, best_stats = ranked[0]
    return {
        'best_algorithm': best_name,
        'mean_hypervolume': best_stats['mean_hypervolume'],
        'variance_hypervolume': best_stats['variance_hypervolume'],
        'justification': (
            f"{best_name} has highest mean hypervolume "
            f"({best_stats['mean_hypervolume']:.4f}) with variance "
            f"{best_stats['variance_hypervolume']:.4f}"
        ),
        'ranking': [{'algorithm': name, **stats} for name, stats in ranked],
    }
