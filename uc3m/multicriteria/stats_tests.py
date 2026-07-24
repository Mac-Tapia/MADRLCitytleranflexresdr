"""Non-parametric significance tests for MADRL algorithm comparison.

Implements the methodology battery comparing HAPPO, MAAC, MASAC and MATD3
by scenario (OE.1/E1, OE.2/E2, OE.3/E3) and globally (OG):

Minimum OE battery (section 6)
  Shapiro-Wilk → Fligner-Killeen → Kruskal-Wallis → ε² → Dunn-Holm → Cliff's δ
  Winner: KW mean rank + Dunn-Holm validation (co-winners / Cliff / median)

Minimum OG battery
  Friedman → Kendall's W → Nemenyi → TOPSIS winner (validated vs Friedman-Nemenyi)

Complementary catalog (sections 1–4), behind ``complementary=True`` / flags:
  Mood's median, Quade, Scheirer-Ray-Hare, Conover-Iman, Wilcoxon, Mann-Whitney,
  Brunner-Munzel, rank-biserial, Spearman ρ, Kendall τ, Page's trend, Cochran's Q.
"""

from __future__ import annotations

from itertools import combinations
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

try:
    from scipy import stats
except ImportError:  # pragma: no cover
    stats = None

try:
    import scikit_posthocs as sp  # type: ignore
except ImportError:  # pragma: no cover
    sp = None

# Romano et al. thresholds for |Cliff's δ|
_CLIFF_THRESHOLDS = (
    (0.147, "negligible"),
    (0.33, "small"),
    (0.474, "medium"),
)


def _require_scipy() -> None:
    if stats is None:
        raise ImportError("scipy is required for non-parametric statistical tests")


def _finite(values: Sequence[float]) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    return arr[np.isfinite(arr)]


def _clean_groups(
    groups: Mapping[str, Sequence[float]],
    *,
    higher_is_better: bool = True,
) -> Tuple[List[str], List[np.ndarray]]:
    """Return ordered labels and finite samples; negate when lower-is-better."""

    labels: List[str] = []
    samples: List[np.ndarray] = []
    sign = 1.0 if higher_is_better else -1.0
    for name, values in groups.items():
        arr = _finite(values) * sign
        if arr.size == 0:
            continue
        labels.append(str(name))
        samples.append(arr)
    return labels, samples


def _groups_dict(labels: Sequence[str], samples: Sequence[np.ndarray]) -> Dict[str, np.ndarray]:
    return {lab: samp for lab, samp in zip(labels, samples)}


def holm_correction(p_values: Sequence[float]) -> List[float]:
    """Holm step-down adjusted p-values (same order as input)."""

    n = len(p_values)
    if n == 0:
        return []
    indexed = sorted(enumerate(float(p) for p in p_values), key=lambda t: t[1])
    adjusted = [1.0] * n
    running = 0.0
    for rank, (idx, p) in enumerate(indexed):
        candidate = min(1.0, (n - rank) * p)
        running = max(running, candidate)
        adjusted[idx] = running
    return adjusted


# ---------------------------------------------------------------------------
# Effect sizes
# ---------------------------------------------------------------------------


def cliffs_delta(x: Sequence[float], y: Sequence[float]) -> Optional[float]:
    """Cliff's δ: P(X>Y) − P(X<Y). Positive favours ``x`` (larger values)."""

    a = _finite(x)
    b = _finite(y)
    if a.size == 0 or b.size == 0:
        return None
    greater = 0
    lower = 0
    for va in a:
        for vb in b:
            if va > vb:
                greater += 1
            elif va < vb:
                lower += 1
    return float((greater - lower) / (a.size * b.size))


def cliffs_delta_magnitude(delta: Optional[float]) -> str:
    if delta is None:
        return "not_calculable"
    absolute = abs(float(delta))
    for thr, label in _CLIFF_THRESHOLDS:
        if absolute < thr:
            return label
    return "large"


def epsilon_squared_kw(H: float, n_total: int) -> Optional[float]:
    """ε² = H / ((n² − 1) / (n + 1)) ≈ H / (n − 1) for large n."""

    if n_total < 2 or not np.isfinite(H):
        return None
    return float(H / (n_total - 1))


def kendalls_w_from_friedman(chi2: float, n_blocks: int, k_treatments: int) -> Optional[float]:
    """Kendall's W = χ²_F / (n · (k − 1))."""

    if n_blocks < 1 or k_treatments < 2 or not np.isfinite(chi2):
        return None
    return float(chi2 / (n_blocks * (k_treatments - 1)))


def rank_biserial_from_mwu(U: float, n1: int, n2: int) -> Optional[float]:
    """Glass rank-biserial correlation from Mann-Whitney U."""

    if n1 < 1 or n2 < 1 or not np.isfinite(U):
        return None
    return float(1.0 - (2.0 * U) / (n1 * n2))


def rank_biserial_from_wilcoxon(W: float, n: int) -> Optional[float]:
    """Matched-pairs rank-biserial from Wilcoxon W (sum of positive ranks)."""

    if n < 1 or not np.isfinite(W):
        return None
    total = n * (n + 1) / 2.0
    if total <= 0:
        return None
    return float((2.0 * W) / total - 1.0)


# ---------------------------------------------------------------------------
# Normality / homogeneity / omnibus (independent groups)
# ---------------------------------------------------------------------------


def shapiro_wilk_per_group(
    groups: Mapping[str, Sequence[float]],
    *,
    alpha: float = 0.05,
) -> Dict[str, Dict[str, object]]:
    """Shapiro-Wilk normality check per algorithm (raw values, not reoriented)."""

    _require_scipy()
    out: Dict[str, Dict[str, object]] = {}
    for name, values in groups.items():
        arr = _finite(values)
        if arr.size < 3:
            out[str(name)] = {
                "statistic": None,
                "p_value": None,
                "normality_rejected": None,
                "n": int(arr.size),
                "status": "insufficient_data_n<3",
                "alpha": float(alpha),
            }
            continue
        # Shapiro requires n <= 5000 in scipy.
        sample = arr if arr.size <= 5000 else np.random.default_rng(0).choice(arr, 5000, replace=False)
        try:
            stat, p = stats.shapiro(sample)
            out[str(name)] = {
                "statistic": float(stat),
                "p_value": float(p),
                "normality_rejected": bool(float(p) < alpha),
                "n": int(arr.size),
                "status": "ok",
                "alpha": float(alpha),
            }
        except ValueError as exc:
            out[str(name)] = {
                "statistic": None,
                "p_value": None,
                "normality_rejected": None,
                "n": int(arr.size),
                "status": f"error:{exc}",
                "alpha": float(alpha),
            }
    return out


def fligner_killeen(
    groups: Mapping[str, Sequence[float]],
    *,
    alpha: float = 0.05,
) -> Dict[str, object]:
    """Fligner-Killeen test for homogeneity of variances."""

    _require_scipy()
    labels, samples = _clean_groups(groups, higher_is_better=True)
    if len(samples) < 2:
        return {
            "statistic": None,
            "p_value": None,
            "significant": False,
            "groups": labels,
            "status": "insufficient_groups",
            "alpha": float(alpha),
        }
    try:
        stat, p = stats.fligner(*samples)
        return {
            "statistic": float(stat),
            "p_value": float(p),
            "significant": bool(float(p) < alpha),
            "groups": labels,
            "status": "ok",
            "alpha": float(alpha),
            "note": "significant → variances heterogeneous (non-parametric path preferred)",
        }
    except ValueError as exc:
        return {
            "statistic": None,
            "p_value": None,
            "significant": False,
            "groups": labels,
            "status": f"error:{exc}",
            "alpha": float(alpha),
        }


def kruskal_wallis(
    groups: Mapping[str, Sequence[float]],
    *,
    alpha: float = 0.05,
    higher_is_better: bool = True,
) -> Dict[str, object]:
    """Kruskal-Wallis H omnibus with mean ranks (higher rank = better)."""

    _require_scipy()
    labels, samples = _clean_groups(groups, higher_is_better=higher_is_better)
    if len(samples) < 2:
        return {
            "H": None,
            "p_value": None,
            "significant": False,
            "n_groups": len(samples),
            "groups": labels,
            "mean_ranks": {},
            "epsilon_squared": None,
            "n_total": 0,
            "status": "insufficient_groups",
            "alpha": float(alpha),
            "higher_is_better": higher_is_better,
        }
    try:
        H, p = stats.kruskal(*samples)
    except ValueError as exc:
        return {
            "H": None,
            "p_value": None,
            "significant": False,
            "n_groups": len(samples),
            "groups": labels,
            "mean_ranks": {},
            "epsilon_squared": None,
            "n_total": int(sum(s.size for s in samples)),
            "status": f"error:{exc}",
            "alpha": float(alpha),
            "higher_is_better": higher_is_better,
        }

    pooled = np.concatenate(samples)
    ranks = stats.rankdata(pooled)
    mean_ranks: Dict[str, float] = {}
    offset = 0
    for lab, samp in zip(labels, samples):
        r = ranks[offset : offset + samp.size]
        mean_ranks[lab] = float(np.mean(r))
        offset += samp.size
    n_total = int(pooled.size)
    return {
        "H": float(H),
        "p_value": float(p),
        "significant": bool(float(p) < alpha),
        "n_groups": len(samples),
        "groups": labels,
        "mean_ranks": mean_ranks,
        "epsilon_squared": epsilon_squared_kw(float(H), n_total),
        "n_total": n_total,
        "status": "ok",
        "alpha": float(alpha),
        "higher_is_better": higher_is_better,
    }


def moods_median_test(
    groups: Mapping[str, Sequence[float]],
    *,
    alpha: float = 0.05,
) -> Dict[str, object]:
    """Mood's median test (complementary omnibus)."""

    _require_scipy()
    labels, samples = _clean_groups(groups, higher_is_better=True)
    if len(samples) < 2:
        return {
            "statistic": None,
            "p_value": None,
            "significant": False,
            "groups": labels,
            "status": "insufficient_groups",
            "alpha": float(alpha),
        }
    try:
        stat, p, med, table = stats.median_test(*samples)
        return {
            "statistic": float(stat),
            "p_value": float(p),
            "significant": bool(float(p) < alpha),
            "grand_median": float(med),
            "contingency_table": np.asarray(table).tolist(),
            "groups": labels,
            "status": "ok",
            "alpha": float(alpha),
        }
    except ValueError as exc:
        return {
            "statistic": None,
            "p_value": None,
            "significant": False,
            "groups": labels,
            "status": f"error:{exc}",
            "alpha": float(alpha),
        }


# ---------------------------------------------------------------------------
# Post-hoc (independent groups)
# ---------------------------------------------------------------------------


def _dunn_z_p(
    mean_rank_i: float,
    mean_rank_j: float,
    n_i: int,
    n_j: int,
    n_total: int,
    tie_correction: float,
) -> Tuple[float, float]:
    """Two-sided Dunn z and p with optional tie correction factor."""

    _require_scipy()
    se = np.sqrt(
        tie_correction
        * (n_total * (n_total + 1) / 12.0)
        * (1.0 / n_i + 1.0 / n_j)
    )
    if se <= 0:
        return 0.0, 1.0
    z = (mean_rank_i - mean_rank_j) / se
    p = float(2.0 * stats.norm.sf(abs(z)))
    return float(z), min(1.0, p)


def _tie_correction_factor(ranks: np.ndarray) -> float:
    """1 − Σ(t³−t) / (N³−N) for Dunn/Conover SE."""

    n = ranks.size
    if n < 2:
        return 1.0
    _, counts = np.unique(ranks, return_counts=True)
    tie_sum = float(np.sum(counts**3 - counts))
    denom = float(n**3 - n)
    if denom <= 0:
        return 1.0
    return 1.0 - tie_sum / denom


def dunns_posthoc_holm(
    groups: Mapping[str, Sequence[float]],
    *,
    alpha: float = 0.05,
    higher_is_better: bool = True,
) -> List[Dict[str, object]]:
    """Dunn's pairwise post-hoc with Holm correction on pooled ranks."""

    _require_scipy()
    labels, samples = _clean_groups(groups, higher_is_better=higher_is_better)
    if len(samples) < 2:
        return []

    if sp is not None:
        # Prefer scikit-posthocs when installed (p-values already Holm-adjusted).
        frame_rows = []
        for lab, samp in zip(labels, samples):
            for v in samp:
                frame_rows.append({"algorithm": lab, "value": float(v)})
        import pandas as pd

        df = pd.DataFrame(frame_rows)
        try:
            p_mat = sp.posthoc_dunn(df, val_col="value", group_col="algorithm", p_adjust="holm")
            rows: List[Dict[str, object]] = []
            for a, b in combinations(labels, 2):
                p_adj = float(p_mat.loc[a, b])
                # Recompute z/delta on oriented samples for reporting.
                pooled = np.concatenate(samples)
                ranks = stats.rankdata(pooled)
                sizes = [s.size for s in samples]
                mean_r = {}
                offset = 0
                for lab, samp in zip(labels, samples):
                    mean_r[lab] = float(np.mean(ranks[offset : offset + samp.size]))
                    offset += samp.size
                idx = {lab: i for i, lab in enumerate(labels)}
                z, p_raw = _dunn_z_p(
                    mean_r[a],
                    mean_r[b],
                    sizes[idx[a]],
                    sizes[idx[b]],
                    int(pooled.size),
                    _tie_correction_factor(ranks),
                )
                gdict = _groups_dict(labels, samples)
                delta = cliffs_delta(gdict[a], gdict[b])
                rows.append(
                    {
                        "algorithm_a": a,
                        "algorithm_b": b,
                        "z": z,
                        "p_raw": p_raw,
                        "p_holm": p_adj,
                        "significant": bool(p_adj < alpha),
                        "mean_rank_a": mean_r[a],
                        "mean_rank_b": mean_r[b],
                        "cliffs_delta": delta,
                        "cliffs_delta_magnitude": cliffs_delta_magnitude(delta),
                        "method": "dunn_holm_scikit_posthocs",
                        "alpha": float(alpha),
                    }
                )
            return rows
        except Exception:
            pass  # fall through to manual

    pooled = np.concatenate(samples)
    ranks = stats.rankdata(pooled)
    n_total = int(pooled.size)
    tie_c = _tie_correction_factor(ranks)
    mean_r: Dict[str, float] = {}
    sizes: Dict[str, int] = {}
    offset = 0
    for lab, samp in zip(labels, samples):
        mean_r[lab] = float(np.mean(ranks[offset : offset + samp.size]))
        sizes[lab] = int(samp.size)
        offset += samp.size

    raw_rows: List[Dict[str, object]] = []
    p_raws: List[float] = []
    gdict = _groups_dict(labels, samples)
    for a, b in combinations(labels, 2):
        z, p_raw = _dunn_z_p(mean_r[a], mean_r[b], sizes[a], sizes[b], n_total, tie_c)
        delta = cliffs_delta(gdict[a], gdict[b])
        raw_rows.append(
            {
                "algorithm_a": a,
                "algorithm_b": b,
                "z": z,
                "p_raw": p_raw,
                "mean_rank_a": mean_r[a],
                "mean_rank_b": mean_r[b],
                "cliffs_delta": delta,
                "cliffs_delta_magnitude": cliffs_delta_magnitude(delta),
            }
        )
        p_raws.append(p_raw)

    adjusted = holm_correction(p_raws)
    out: List[Dict[str, object]] = []
    for row, p_adj in zip(raw_rows, adjusted):
        out.append(
            {
                **row,
                "p_holm": float(p_adj),
                "significant": bool(p_adj < alpha),
                "method": "dunn_holm_manual",
                "alpha": float(alpha),
            }
        )
    return out


def conover_iman_posthoc(
    groups: Mapping[str, Sequence[float]],
    *,
    alpha: float = 0.05,
    higher_is_better: bool = True,
) -> List[Dict[str, object]]:
    """Conover-Iman post-hoc after Kruskal-Wallis (t-approximation, Holm)."""

    _require_scipy()
    labels, samples = _clean_groups(groups, higher_is_better=higher_is_better)
    if len(samples) < 2:
        return []
    kw = kruskal_wallis(groups, alpha=alpha, higher_is_better=higher_is_better)
    if kw.get("status") != "ok" or kw.get("H") is None:
        return []

    if sp is not None:
        frame_rows = []
        for lab, samp in zip(labels, samples):
            for v in samp:
                frame_rows.append({"algorithm": lab, "value": float(v)})
        import pandas as pd

        df = pd.DataFrame(frame_rows)
        try:
            p_mat = sp.posthoc_conover(df, val_col="value", group_col="algorithm", p_adjust="holm")
            rows = []
            for a, b in combinations(labels, 2):
                p_adj = float(p_mat.loc[a, b])
                rows.append(
                    {
                        "algorithm_a": a,
                        "algorithm_b": b,
                        "p_holm": p_adj,
                        "significant": bool(p_adj < alpha),
                        "method": "conover_iman_scikit_posthocs",
                        "alpha": float(alpha),
                    }
                )
            return rows
        except Exception:
            pass

    pooled = np.concatenate(samples)
    ranks = stats.rankdata(pooled)
    n = int(pooled.size)
    k = len(samples)
    H = float(kw["H"])
    # Residual mean square on ranks (Conover & Iman / scikit-posthocs form).
    tie_c = _tie_correction_factor(ranks)
    s2 = (n * (n + 1) / 12.0) * tie_c * (n - 1 - H) / max(n - k, 1)

    mean_r: Dict[str, float] = {}
    sizes: Dict[str, int] = {}
    offset = 0
    for lab, samp in zip(labels, samples):
        mean_r[lab] = float(np.mean(ranks[offset : offset + samp.size]))
        sizes[lab] = int(samp.size)
        offset += samp.size

    raw: List[Dict[str, object]] = []
    p_raws: List[float] = []
    df = n - k
    for a, b in combinations(labels, 2):
        se = np.sqrt(s2 * (1.0 / sizes[a] + 1.0 / sizes[b]))
        if se <= 0 or df < 1:
            t_stat, p_raw = 0.0, 1.0
        else:
            t_stat = (mean_r[a] - mean_r[b]) / se
            p_raw = float(2.0 * stats.t.sf(abs(t_stat), df))
        raw.append(
            {
                "algorithm_a": a,
                "algorithm_b": b,
                "t": float(t_stat),
                "p_raw": p_raw,
                "df": int(df),
            }
        )
        p_raws.append(p_raw)

    adjusted = holm_correction(p_raws)
    return [
        {
            **row,
            "p_holm": float(p_adj),
            "significant": bool(p_adj < alpha),
            "method": "conover_iman_manual",
            "alpha": float(alpha),
        }
        for row, p_adj in zip(raw, adjusted)
    ]


def mann_whitney_u(
    x: Sequence[float],
    y: Sequence[float],
    *,
    alpha: float = 0.05,
    alternative: str = "two-sided",
) -> Dict[str, object]:
    """Mann-Whitney U with Glass rank-biserial effect size."""

    _require_scipy()
    a = _finite(x)
    b = _finite(y)
    if a.size < 1 or b.size < 1:
        return {
            "U": None,
            "p_value": None,
            "significant": False,
            "rank_biserial": None,
            "n_a": int(a.size),
            "n_b": int(b.size),
            "status": "insufficient_data",
            "alpha": float(alpha),
        }
    try:
        result = stats.mannwhitneyu(a, b, alternative=alternative)
        U = float(result.statistic)
        p = float(result.pvalue)
        return {
            "U": U,
            "p_value": p,
            "significant": bool(p < alpha),
            "rank_biserial": rank_biserial_from_mwu(U, int(a.size), int(b.size)),
            "n_a": int(a.size),
            "n_b": int(b.size),
            "status": "ok",
            "alpha": float(alpha),
            "alternative": alternative,
        }
    except ValueError as exc:
        return {
            "U": None,
            "p_value": None,
            "significant": False,
            "rank_biserial": None,
            "n_a": int(a.size),
            "n_b": int(b.size),
            "status": f"error:{exc}",
            "alpha": float(alpha),
        }


def brunner_munzel(
    x: Sequence[float],
    y: Sequence[float],
    *,
    alpha: float = 0.05,
) -> Dict[str, object]:
    """Brunner-Munzel test (robust to heteroscedasticity)."""

    _require_scipy()
    a = _finite(x)
    b = _finite(y)
    if a.size < 2 or b.size < 2:
        return {
            "statistic": None,
            "p_value": None,
            "significant": False,
            "n_a": int(a.size),
            "n_b": int(b.size),
            "status": "insufficient_data",
            "alpha": float(alpha),
        }
    try:
        result = stats.brunnermunzel(a, b)
        p = float(result.pvalue)
        return {
            "statistic": float(result.statistic),
            "p_value": p,
            "significant": bool(p < alpha),
            "n_a": int(a.size),
            "n_b": int(b.size),
            "status": "ok",
            "alpha": float(alpha),
        }
    except ValueError as exc:
        return {
            "statistic": None,
            "p_value": None,
            "significant": False,
            "n_a": int(a.size),
            "n_b": int(b.size),
            "status": f"error:{exc}",
            "alpha": float(alpha),
        }


def wilcoxon_signed_rank(
    x: Sequence[float],
    y: Sequence[float],
    *,
    alpha: float = 0.05,
    alternative: str = "two-sided",
) -> Dict[str, object]:
    """Wilcoxon signed-rank test for paired algorithm comparisons."""

    _require_scipy()
    a = np.asarray(x, dtype=float)
    b = np.asarray(y, dtype=float)
    if a.shape != b.shape:
        raise ValueError("x and y must have the same shape for paired Wilcoxon")
    mask = np.isfinite(a) & np.isfinite(b)
    a = a[mask]
    b = b[mask]
    if a.size < 1:
        return {
            "statistic": None,
            "p_value": None,
            "significant": False,
            "rank_biserial": None,
            "n": 0,
            "status": "insufficient_data",
            "alpha": float(alpha),
        }
    if np.allclose(a, b):
        return {
            "statistic": 0.0,
            "p_value": 1.0,
            "significant": False,
            "rank_biserial": 0.0,
            "n": int(a.size),
            "status": "identical_samples",
            "alpha": float(alpha),
        }
    try:
        result = stats.wilcoxon(a, b, alternative=alternative, zero_method="wilcox")
        p = float(result.pvalue)
        W = float(result.statistic)
        return {
            "statistic": W,
            "p_value": p,
            "significant": bool(p < alpha),
            "rank_biserial": rank_biserial_from_wilcoxon(W, int(a.size)),
            "n": int(a.size),
            "status": "ok",
            "alpha": float(alpha),
            "alternative": alternative,
        }
    except ValueError as exc:
        return {
            "statistic": None,
            "p_value": None,
            "significant": False,
            "rank_biserial": None,
            "n": int(a.size),
            "status": f"error:{exc}",
            "alpha": float(alpha),
        }


def pairwise_wilcoxon(
    groups: Mapping[str, Sequence[float]],
    *,
    alpha: float = 0.05,
) -> List[Dict[str, object]]:
    """All pairwise Wilcoxon signed-rank comparisons."""

    rows: List[Dict[str, object]] = []
    for a, b in combinations(list(groups.keys()), 2):
        xa = np.asarray(groups[a], dtype=float)
        xb = np.asarray(groups[b], dtype=float)
        n = min(xa.size, xb.size)
        result = wilcoxon_signed_rank(xa[:n], xb[:n], alpha=alpha)
        rows.append({"algorithm_a": a, "algorithm_b": b, **result})
    return rows


def pairwise_mann_whitney(
    groups: Mapping[str, Sequence[float]],
    *,
    alpha: float = 0.05,
) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for a, b in combinations(list(groups.keys()), 2):
        result = mann_whitney_u(groups[a], groups[b], alpha=alpha)
        delta = cliffs_delta(groups[a], groups[b])
        rows.append(
            {
                "algorithm_a": a,
                "algorithm_b": b,
                **result,
                "cliffs_delta": delta,
                "cliffs_delta_magnitude": cliffs_delta_magnitude(delta),
            }
        )
    return rows


def pairwise_brunner_munzel(
    groups: Mapping[str, Sequence[float]],
    *,
    alpha: float = 0.05,
) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for a, b in combinations(list(groups.keys()), 2):
        result = brunner_munzel(groups[a], groups[b], alpha=alpha)
        rows.append({"algorithm_a": a, "algorithm_b": b, **result})
    return rows


# ---------------------------------------------------------------------------
# Block designs (Friedman family) — OG global synthesis
# ---------------------------------------------------------------------------


def _block_matrix(
    blocks: Mapping[str, Mapping[str, float]],
    *,
    higher_is_better: Mapping[str, bool] | bool = True,
) -> Tuple[List[str], List[str], np.ndarray]:
    """Convert {block: {algo: value}} → (block_names, algo_names, matrix n×k).

    Values are oriented so that higher is always better within each block.
    """

    block_names = list(blocks.keys())
    algo_set: List[str] = []
    for b in block_names:
        for a in blocks[b]:
            if a not in algo_set:
                algo_set.append(a)
    mat = np.full((len(block_names), len(algo_set)), np.nan, dtype=float)
    for i, b in enumerate(block_names):
        hib = higher_is_better[b] if isinstance(higher_is_better, Mapping) else bool(higher_is_better)
        sign = 1.0 if hib else -1.0
        for j, a in enumerate(algo_set):
            if a in blocks[b] and np.isfinite(blocks[b][a]):
                mat[i, j] = float(blocks[b][a]) * sign
    return block_names, algo_set, mat


def friedman_test(
    blocks: Mapping[str, Mapping[str, float]],
    *,
    alpha: float = 0.05,
    higher_is_better: Mapping[str, bool] | bool = True,
) -> Dict[str, object]:
    """Friedman omnibus across algorithms with scenarios/seeds as blocks."""

    _require_scipy()
    block_names, algos, mat = _block_matrix(blocks, higher_is_better=higher_is_better)
    # Drop incomplete blocks.
    complete = np.all(np.isfinite(mat), axis=1)
    mat = mat[complete]
    used_blocks = [b for b, ok in zip(block_names, complete) if ok]
    n, k = mat.shape
    if n < 2 or k < 2:
        return {
            "chi2": None,
            "p_value": None,
            "significant": False,
            "n_blocks": int(n),
            "n_algorithms": int(k),
            "algorithms": algos,
            "blocks": used_blocks,
            "mean_ranks": {},
            "kendalls_w": None,
            "status": "insufficient_data",
            "alpha": float(alpha),
        }
    try:
        # scipy expects one array per treatment (column).
        cols = [mat[:, j] for j in range(k)]
        chi2, p = stats.friedmanchisquare(*cols)
    except ValueError as exc:
        return {
            "chi2": None,
            "p_value": None,
            "significant": False,
            "n_blocks": int(n),
            "n_algorithms": int(k),
            "algorithms": algos,
            "blocks": used_blocks,
            "mean_ranks": {},
            "kendalls_w": None,
            "status": f"error:{exc}",
            "alpha": float(alpha),
        }

    # Within-block ranks (higher value → higher rank → better).
    ranks = np.apply_along_axis(stats.rankdata, 1, mat)
    mean_ranks = {algo: float(np.mean(ranks[:, j])) for j, algo in enumerate(algos)}
    w = kendalls_w_from_friedman(float(chi2), n, k)
    return {
        "chi2": float(chi2),
        "p_value": float(p),
        "significant": bool(float(p) < alpha),
        "n_blocks": int(n),
        "n_algorithms": int(k),
        "algorithms": algos,
        "blocks": used_blocks,
        "mean_ranks": mean_ranks,
        "rank_matrix": ranks.tolist(),
        "kendalls_w": w,
        "status": "ok",
        "alpha": float(alpha),
    }


def nemenyi_posthoc(
    blocks: Mapping[str, Mapping[str, float]],
    *,
    alpha: float = 0.05,
    higher_is_better: Mapping[str, bool] | bool = True,
) -> Dict[str, object]:
    """Nemenyi post-hoc via critical difference on Friedman mean ranks."""

    fr = friedman_test(blocks, alpha=alpha, higher_is_better=higher_is_better)
    if fr.get("status") != "ok":
        return {**fr, "pairs": [], "critical_difference": None}

    n = int(fr["n_blocks"])
    k = int(fr["n_algorithms"])
    algos = list(fr["algorithms"])
    mean_ranks = dict(fr["mean_ranks"])

    # Studentized range critical value q_{α,k,∞} / √2  (common Nemenyi form).
    # Approximate via scipy studentized_range when available.
    try:
        q_crit = float(stats.studentized_range.ppf(1.0 - alpha, k, np.inf))
        q_alpha = q_crit / np.sqrt(2.0)
    except Exception:
        # Fallback table for α=0.05, k=2..10 (Demšar 2006 style approximations).
        _Q05 = {2: 1.960, 3: 2.343, 4: 2.569, 5: 2.728, 6: 2.850, 7: 2.949, 8: 3.031, 9: 3.102, 10: 3.164}
        q_alpha = float(_Q05.get(k, 2.569))

    cd = float(q_alpha * np.sqrt(k * (k + 1) / (6.0 * n)))
    pairs: List[Dict[str, object]] = []
    for a, b in combinations(algos, 2):
        diff = abs(mean_ranks[a] - mean_ranks[b])
        pairs.append(
            {
                "algorithm_a": a,
                "algorithm_b": b,
                "rank_diff": float(diff),
                "critical_difference": cd,
                "significant": bool(diff > cd),
                "mean_rank_a": mean_ranks[a],
                "mean_rank_b": mean_ranks[b],
            }
        )
    return {
        "critical_difference": cd,
        "q_alpha": float(q_alpha),
        "alpha": float(alpha),
        "n_blocks": n,
        "n_algorithms": k,
        "mean_ranks": mean_ranks,
        "pairs": pairs,
        "status": "ok",
        "method": "nemenyi_critical_difference",
    }


def quade_test(
    blocks: Mapping[str, Mapping[str, float]],
    *,
    alpha: float = 0.05,
    higher_is_better: Mapping[str, bool] | bool = True,
) -> Dict[str, object]:
    """Quade test (weighted Friedman alternative for block designs)."""

    _require_scipy()
    block_names, algos, mat = _block_matrix(blocks, higher_is_better=higher_is_better)
    complete = np.all(np.isfinite(mat), axis=1)
    mat = mat[complete]
    n, k = mat.shape
    if n < 2 or k < 2:
        return {
            "F": None,
            "p_value": None,
            "significant": False,
            "status": "insufficient_data",
            "alpha": float(alpha),
        }

    if sp is not None and hasattr(sp, "quade"):
        try:
            # scikit-posthocs expects samples as columns of a 2d array in some APIs;
            # fall through to manual if signature differs.
            pass
        except Exception:
            pass

    # Manual Quade (Conover 1999):
    # 1) Within-block ranks R_ij
    # 2) Block range ranks Q_i (rank of within-block range)
    # 3) S_ij = Q_i * (R_ij - (k+1)/2)
    ranks = np.apply_along_axis(stats.rankdata, 1, mat)
    ranges = np.ptp(mat, axis=1)
    q = stats.rankdata(ranges)
    center = (k + 1) / 2.0
    S = q[:, None] * (ranks - center)
    A2 = float(np.sum(S**2))
    B2 = float(np.sum(np.sum(S, axis=0) ** 2) / n)
    if abs(A2 - B2) < 1e-12:
        return {
            "F": 0.0,
            "p_value": 1.0,
            "significant": False,
            "n_blocks": int(n),
            "n_algorithms": int(k),
            "algorithms": algos,
            "status": "identical_block_patterns",
            "alpha": float(alpha),
        }
    F = ((n - 1) * B2) / (A2 - B2)
    df1 = k - 1
    df2 = (n - 1) * (k - 1)
    p = float(stats.f.sf(F, df1, df2))
    return {
        "F": float(F),
        "p_value": p,
        "significant": bool(p < alpha),
        "df1": int(df1),
        "df2": int(df2),
        "n_blocks": int(n),
        "n_algorithms": int(k),
        "algorithms": algos,
        "status": "ok",
        "alpha": float(alpha),
    }


def scheirer_ray_hare(
    values: Sequence[float],
    factor_a: Sequence[str],
    factor_b: Sequence[str],
    *,
    alpha: float = 0.05,
) -> Dict[str, object]:
    """Scheirer-Ray-Hare: rank transform + two-way ANOVA SS decomposition.

    ``factor_a`` typically algorithm; ``factor_b`` typically scenario.
    """

    _require_scipy()
    y = np.asarray(values, dtype=float)
    a = np.asarray(list(map(str, factor_a)))
    b = np.asarray(list(map(str, factor_b)))
    mask = np.isfinite(y)
    y, a, b = y[mask], a[mask], b[mask]
    n = int(y.size)
    if n < 4:
        return {"status": "insufficient_data", "alpha": float(alpha)}

    ranks = stats.rankdata(y)
    levels_a = sorted(set(a.tolist()))
    levels_b = sorted(set(b.tolist()))
    grand = float(np.mean(ranks))
    ss_total = float(np.sum((ranks - grand) ** 2))

    def ss_main(factor: np.ndarray, levels: Sequence[str]) -> float:
        ss = 0.0
        for lev in levels:
            idx = factor == lev
            if not np.any(idx):
                continue
            ss += int(np.sum(idx)) * (float(np.mean(ranks[idx])) - grand) ** 2
        return float(ss)

    # Interaction: cell means.
    ss_cells = 0.0
    for la in levels_a:
        for lb in levels_b:
            idx = (a == la) & (b == lb)
            if not np.any(idx):
                continue
            ss_cells += int(np.sum(idx)) * (float(np.mean(ranks[idx])) - grand) ** 2

    ss_a = ss_main(a, levels_a)
    ss_b = ss_main(b, levels_b)
    ss_ab = max(0.0, ss_cells - ss_a - ss_b)
    ss_error = max(0.0, ss_total - ss_cells)

    # MS_error for H ≈ SS / MS_total style SRH uses chi-square on SS / (N(N+1)/12)
    ms_denom = n * (n + 1) / 12.0
    if ms_denom <= 0:
        return {"status": "degenerate", "alpha": float(alpha)}

    def chi_row(ss: float, df: int) -> Dict[str, object]:
        H = ss / ms_denom
        p = float(stats.chi2.sf(H, df)) if df > 0 else None
        return {
            "SS": float(ss),
            "df": int(df),
            "H": float(H),
            "p_value": p,
            "significant": bool(p is not None and p < alpha),
        }

    df_a = len(levels_a) - 1
    df_b = len(levels_b) - 1
    df_ab = df_a * df_b
    return {
        "factor_a_levels": levels_a,
        "factor_b_levels": levels_b,
        "n": n,
        "factor_a": chi_row(ss_a, df_a),
        "factor_b": chi_row(ss_b, df_b),
        "interaction": chi_row(ss_ab, df_ab),
        "ss_error": float(ss_error),
        "ss_total": float(ss_total),
        "status": "ok",
        "alpha": float(alpha),
        "method": "scheirer_ray_hare_rank_chi2",
    }


# ---------------------------------------------------------------------------
# Correlation / trend
# ---------------------------------------------------------------------------


def spearman_rho(
    x: Sequence[float],
    y: Sequence[float],
    *,
    alpha: float = 0.05,
) -> Dict[str, object]:
    _require_scipy()
    a = np.asarray(x, dtype=float)
    b = np.asarray(y, dtype=float)
    mask = np.isfinite(a) & np.isfinite(b)
    a, b = a[mask], b[mask]
    if a.size < 3:
        return {"rho": None, "p_value": None, "significant": False, "n": int(a.size), "status": "insufficient_data"}
    rho, p = stats.spearmanr(a, b)
    return {
        "rho": float(rho),
        "p_value": float(p),
        "significant": bool(float(p) < alpha),
        "n": int(a.size),
        "status": "ok",
        "alpha": float(alpha),
    }


def kendall_tau(
    x: Sequence[float],
    y: Sequence[float],
    *,
    alpha: float = 0.05,
) -> Dict[str, object]:
    _require_scipy()
    a = np.asarray(x, dtype=float)
    b = np.asarray(y, dtype=float)
    mask = np.isfinite(a) & np.isfinite(b)
    a, b = a[mask], b[mask]
    if a.size < 3:
        return {"tau": None, "p_value": None, "significant": False, "n": int(a.size), "status": "insufficient_data"}
    tau, p = stats.kendalltau(a, b)
    return {
        "tau": float(tau),
        "p_value": float(p),
        "significant": bool(float(p) < alpha),
        "n": int(a.size),
        "status": "ok",
        "alpha": float(alpha),
    }


def pages_trend_test(
    blocks: Mapping[str, Mapping[str, float]],
    ordered_algorithms: Sequence[str],
    *,
    alpha: float = 0.05,
    higher_is_better: Mapping[str, bool] | bool = True,
) -> Dict[str, object]:
    """Page's L trend test for ordered alternative (L larger → trend present).

    ``ordered_algorithms`` is the hypothesized increasing performance order
    (worst → best) after orientation.
    """

    _require_scipy()
    block_names, algos, mat = _block_matrix(blocks, higher_is_better=higher_is_better)
    complete = np.all(np.isfinite(mat), axis=1)
    mat = mat[complete]
    n, k = mat.shape
    order = [a for a in ordered_algorithms if a in algos]
    if n < 2 or len(order) != k:
        return {
            "L": None,
            "p_value": None,
            "significant": False,
            "status": "insufficient_data_or_order_mismatch",
            "alpha": float(alpha),
        }
    idx = [algos.index(a) for a in order]
    mat = mat[:, idx]
    ranks = np.apply_along_axis(stats.rankdata, 1, mat)
    # Predicted ranks 1..k for ordered columns
    pred = np.arange(1, k + 1, dtype=float)
    L = float(np.sum(pred * np.sum(ranks, axis=0)))
    # Normal approximation (Page 1963 / Siegel)
    mu = n * k * (k + 1) ** 2 / 4.0
    sigma2 = n * k**2 * (k + 1) * (k**2 - 1) / 144.0
    if sigma2 <= 0:
        z, p = 0.0, 1.0
    else:
        z = (L - mu) / np.sqrt(sigma2)
        p = float(stats.norm.sf(z))  # one-sided: larger L supports trend
    return {
        "L": L,
        "z": float(z),
        "p_value": p,
        "significant": bool(p < alpha),
        "ordered_algorithms": list(order),
        "n_blocks": int(n),
        "status": "ok",
        "alpha": float(alpha),
        "alternative": "increasing_performance_along_order",
    }


def cochran_q(
    binary_blocks: Mapping[str, Mapping[str, int]],
    *,
    alpha: float = 0.05,
) -> Dict[str, object]:
    """Cochran's Q for binary success/fail across algorithms (paired blocks).

    ``binary_blocks`` maps block_id → {algorithm: 0|1}. Skipped unless binary
    performance indicators are available.
    """

    _require_scipy()
    block_names = list(binary_blocks.keys())
    algos: List[str] = []
    for b in block_names:
        for a in binary_blocks[b]:
            if a not in algos:
                algos.append(a)
    mat = np.zeros((len(block_names), len(algos)), dtype=float)
    for i, b in enumerate(block_names):
        for j, a in enumerate(algos):
            mat[i, j] = float(binary_blocks[b].get(a, np.nan))
    complete = np.all(np.isfinite(mat), axis=1)
    mat = mat[complete]
    n, k = mat.shape
    if n < 2 or k < 2:
        return {
            "Q": None,
            "p_value": None,
            "significant": False,
            "status": "insufficient_data",
            "alpha": float(alpha),
        }
    # Only 0/1 allowed
    if not np.all((mat == 0) | (mat == 1)):
        return {
            "Q": None,
            "p_value": None,
            "significant": False,
            "status": "non_binary_values",
            "alpha": float(alpha),
        }
    row_sums = mat.sum(axis=1)
    col_sums = mat.sum(axis=0)
    T = float(mat.sum())
    denom = k * T - float(np.sum(row_sums**2))
    if denom <= 0:
        return {
            "Q": 0.0,
            "p_value": 1.0,
            "significant": False,
            "status": "degenerate",
            "alpha": float(alpha),
        }
    Q = (k - 1) * (k * float(np.sum(col_sums**2)) - T**2) / denom
    p = float(stats.chi2.sf(Q, k - 1))
    return {
        "Q": float(Q),
        "p_value": p,
        "significant": bool(p < alpha),
        "n_blocks": int(n),
        "algorithms": algos,
        "status": "ok",
        "alpha": float(alpha),
    }


# ---------------------------------------------------------------------------
# Winner rules (section 7)
# ---------------------------------------------------------------------------


def decide_oe_winner(
    mean_ranks: Mapping[str, float],
    dunn_pairs: Sequence[Mapping[str, object]],
    groups: Mapping[str, Sequence[float]],
    *,
    higher_is_better: bool = True,
    alpha: float = 0.05,
) -> Dict[str, object]:
    """KW mean-rank winner + Dunn-Holm validation; Cliff/median tie-break."""

    if not mean_ranks:
        return {"winners": [], "status": "no_ranks"}

    ordered = sorted(mean_ranks.items(), key=lambda kv: kv[1], reverse=True)
    top_algo, top_rank = ordered[0]
    winners = [top_algo]
    rationale = [
        f"Highest KW mean rank: {top_algo} (Rmean={top_rank:.3f}).",
    ]

    if len(ordered) >= 2:
        second_algo, second_rank = ordered[1]
        pair = None
        for row in dunn_pairs:
            a, b = row.get("algorithm_a"), row.get("algorithm_b")
            if {a, b} == {top_algo, second_algo}:
                pair = row
                break
        if pair is not None and not bool(pair.get("significant")):
            winners = [top_algo, second_algo]
            rationale.append(
                f"Dunn-Holm vs 2nd ({second_algo}, Rmean={second_rank:.3f}) not significant "
                f"(p_holm={pair.get('p_holm')}) -> co-winners."
            )
            # Secondary tie-break: Cliff's δ then median on oriented metric.
            sign = 1.0 if higher_is_better else -1.0
            g_top = _finite(groups.get(top_algo, [])) * sign
            g_sec = _finite(groups.get(second_algo, [])) * sign
            delta = cliffs_delta(g_top, g_sec)
            med_top = float(np.median(g_top)) if g_top.size else float("nan")
            med_sec = float(np.median(g_sec)) if g_sec.size else float("nan")
            rationale.append(
                f"Tie-break Cliff's delta({top_algo},{second_algo})={delta} "
                f"({cliffs_delta_magnitude(delta)}); "
                f"oriented medians {top_algo}={med_top:.4f}, {second_algo}={med_sec:.4f}."
            )
            if delta is not None and abs(delta) >= 0.147:
                preferred = top_algo if delta > 0 else second_algo
                rationale.append(f"Cliff's delta prefers {preferred} (report as primary among co-winners).")
                return {
                    "winners": winners,
                    "primary_among_cowinners": preferred,
                    "mean_ranks": dict(mean_ranks),
                    "rationale": rationale,
                    "status": "cowinners_cliff_tiebreak",
                    "alpha": float(alpha),
                }
            if np.isfinite(med_top) and np.isfinite(med_sec) and med_top != med_sec:
                preferred = top_algo if med_top > med_sec else second_algo
                rationale.append(f"Median tie-break prefers {preferred}.")
                return {
                    "winners": winners,
                    "primary_among_cowinners": preferred,
                    "mean_ranks": dict(mean_ranks),
                    "rationale": rationale,
                    "status": "cowinners_median_tiebreak",
                    "alpha": float(alpha),
                }
        elif pair is not None:
            rationale.append(
                f"Dunn-Holm confirms {top_algo} > {second_algo} "
                f"(p_holm={pair.get('p_holm')}, alpha={alpha})."
            )
        else:
            rationale.append("Dunn pair vs 2nd not found; mean-rank winner retained.")

    return {
        "winners": winners,
        "primary_among_cowinners": winners[0],
        "mean_ranks": dict(mean_ranks),
        "rationale": rationale,
        "status": "ok",
        "alpha": float(alpha),
    }


def validate_topsis_vs_friedman(
    topsis_ranking: Sequence[Mapping[str, object]],
    friedman_mean_ranks: Mapping[str, float],
    nemenyi_pairs: Sequence[Mapping[str, object]],
) -> Dict[str, object]:
    """Compare official TOPSIS winner against Friedman-Nemenyi ranking."""

    if not topsis_ranking or not friedman_mean_ranks:
        return {"agreement": None, "discrepancy": True, "status": "missing_inputs"}

    topsis_winner = str(topsis_ranking[0]["algorithm"])
    fr_ordered = sorted(friedman_mean_ranks.items(), key=lambda kv: kv[1], reverse=True)
    fr_winner = fr_ordered[0][0]
    agreement = topsis_winner == fr_winner

    notes: List[str] = []
    if agreement:
        notes.append(f"TOPSIS and Friedman agree on winner: {topsis_winner}.")
    else:
        notes.append(
            f"DISCREPANCY: TOPSIS winner={topsis_winner}, "
            f"Friedman mean-rank winner={fr_winner}."
        )

    # Check whether TOPSIS winner is statistically separable from Friedman #1 via Nemenyi.
    if not agreement and nemenyi_pairs:
        pair = next(
            (
                r
                for r in nemenyi_pairs
                if {r.get("algorithm_a"), r.get("algorithm_b")} == {topsis_winner, fr_winner}
            ),
            None,
        )
        if pair is not None:
            if pair.get("significant"):
                notes.append(
                    "Nemenyi finds a significant rank gap between TOPSIS and Friedman winners; "
                    "report both and discuss multicriteria vs rank aggregation."
                )
            else:
                notes.append(
                    "Nemenyi does not separate TOPSIS vs Friedman winners; treat as co-leading."
                )

    return {
        "topsis_winner": topsis_winner,
        "friedman_winner": fr_winner,
        "agreement": bool(agreement),
        "discrepancy": (not agreement),
        "notes": notes,
        "status": "ok",
    }


# ---------------------------------------------------------------------------
# Batteries (sections 5–8)
# ---------------------------------------------------------------------------


def sample_coverage(
    groups: Mapping[str, Sequence[float]],
    *,
    expected_n_seeds: int = 12,
    unit: str = "seed",
) -> Dict[str, object]:
    """Report how many independent samples (seeds) each algorithm contributed."""

    n_by_algo = {str(a): int(_finite(v).size) for a, v in groups.items()}
    ns = list(n_by_algo.values())
    complete = bool(ns) and all(n >= int(expected_n_seeds) for n in ns)
    return {
        "unit": unit,
        "expected_n_seeds": int(expected_n_seeds),
        "n_by_algorithm": n_by_algo,
        "min_n": int(min(ns)) if ns else 0,
        "max_n": int(max(ns)) if ns else 0,
        "complete": complete,
        "warning": None
        if complete
        else (
            f"Incomplete seed coverage vs expected_n_seeds={expected_n_seeds}; "
            "interpret significance cautiously."
        ),
    }


def run_oe_battery(
    groups: Mapping[str, Sequence[float]],
    *,
    objective: str = "OE.1",
    higher_is_better: bool = True,
    alpha: float = 0.05,
    complementary: bool = False,
    expected_n_seeds: int = 12,
    sample_unit: str = "seed",
) -> Dict[str, object]:
    """Full per-objective non-parametric battery (sections 5–6 / 8).

    ``groups`` must map algorithm → independent seed scores (canonical n=12).
    """

    coverage = sample_coverage(
        groups, expected_n_seeds=expected_n_seeds, unit=sample_unit
    )
    shapiro = shapiro_wilk_per_group(groups, alpha=alpha)
    fligner = fligner_killeen(groups, alpha=alpha)
    kw = kruskal_wallis(groups, alpha=alpha, higher_is_better=higher_is_better)
    dunn = dunns_posthoc_holm(groups, alpha=alpha, higher_is_better=higher_is_better)

    # Cliff δ for every pair on oriented values
    labels, samples = _clean_groups(groups, higher_is_better=higher_is_better)
    oriented = _groups_dict(labels, samples)
    cliff_pairs: List[Dict[str, object]] = []
    for a, b in combinations(labels, 2):
        delta = cliffs_delta(oriented[a], oriented[b])
        cliff_pairs.append(
            {
                "algorithm_a": a,
                "algorithm_b": b,
                "cliffs_delta": delta,
                "cliffs_delta_magnitude": cliffs_delta_magnitude(delta),
                "note": "positive delta favours algorithm_a on oriented metric (higher=better)",
            }
        )

    winner = decide_oe_winner(
        kw.get("mean_ranks") or {},
        dunn,
        groups,
        higher_is_better=higher_is_better,
        alpha=alpha,
    )

    result: Dict[str, object] = {
        "objective": objective,
        "higher_is_better": higher_is_better,
        "alpha": float(alpha),
        "sample_coverage": coverage,
        "shapiro_wilk": shapiro,
        "fligner_killeen": fligner,
        "kruskal_wallis": kw,
        "epsilon_squared": kw.get("epsilon_squared"),
        "dunn_holm": dunn,
        "cliffs_delta_pairs": cliff_pairs,
        "winner": winner,
    }

    if complementary:
        result["complementary"] = {
            "moods_median": moods_median_test(groups, alpha=alpha),
            "conover_iman": conover_iman_posthoc(
                groups, alpha=alpha, higher_is_better=higher_is_better
            ),
            "mann_whitney": pairwise_mann_whitney(groups, alpha=alpha),
            "brunner_munzel": pairwise_brunner_munzel(groups, alpha=alpha),
            "wilcoxon_paired": pairwise_wilcoxon(groups, alpha=alpha),
        }
    return result


def run_og_battery(
    blocks: Mapping[str, Mapping[str, float]],
    *,
    higher_is_better: Mapping[str, bool] | bool = True,
    topsis_means: Optional[Mapping[str, Mapping[str, float]]] = None,
    topsis_weights: Optional[Mapping[str, float]] = None,
    topsis_criteria_kind: Optional[Mapping[str, str]] = None,
    alpha: float = 0.05,
    complementary: bool = False,
    binary_blocks: Optional[Mapping[str, Mapping[str, int]]] = None,
    page_order: Optional[Sequence[str]] = None,
) -> Dict[str, object]:
    """Global OG battery: Friedman → W → Nemenyi → TOPSIS (+ validation)."""

    fr = friedman_test(blocks, alpha=alpha, higher_is_better=higher_is_better)
    nem = nemenyi_posthoc(blocks, alpha=alpha, higher_is_better=higher_is_better)

    topsis_result: Optional[Dict[str, object]] = None
    validation: Optional[Dict[str, object]] = None
    if topsis_means is not None:
        from uc3m.multicriteria.topsis import topsis_rank

        weights = topsis_weights or {c: 1.0 / max(len(next(iter(topsis_means.values()))), 1) for c in next(iter(topsis_means.values()))}
        # Default kinds from higher_is_better map when not provided.
        kinds = dict(topsis_criteria_kind or {})
        if not kinds:
            if isinstance(higher_is_better, Mapping):
                for crit, hib in higher_is_better.items():
                    kinds[crit] = "benefit" if hib else "cost"
            else:
                for crit in next(iter(topsis_means.values())):
                    kinds[crit] = "benefit" if higher_is_better else "cost"
        raw_topsis = topsis_rank(
            topsis_means,
            weights=weights,
            criteria_kind=kinds,
        )
        # Drop DataFrame artefacts for JSON-friendly reports.
        topsis_result = {
            key: value
            for key, value in raw_topsis.items()
            if key not in {"normalized", "weighted"}
        }
        validation = validate_topsis_vs_friedman(
            topsis_result.get("ranking") or [],
            fr.get("mean_ranks") or {},
            nem.get("pairs") or [],
        )

    result: Dict[str, object] = {
        "scope": "OG",
        "alpha": float(alpha),
        "friedman": fr,
        "kendalls_w": fr.get("kendalls_w"),
        "nemenyi": nem,
        "topsis": topsis_result,
        "topsis_vs_friedman": validation,
        "official_winner_rule": "TOPSIS (validated by Friedman mean ranks + Nemenyi)",
    }

    if complementary:
        comp: Dict[str, object] = {
            "quade": quade_test(blocks, alpha=alpha, higher_is_better=higher_is_better),
        }
        # Scheirer-Ray-Hare from long-format of block means
        vals: List[float] = []
        fa: List[str] = []
        fb: List[str] = []
        hib_map = higher_is_better if isinstance(higher_is_better, Mapping) else None
        for block, by_algo in blocks.items():
            hib = hib_map.get(block, True) if hib_map is not None else bool(higher_is_better)
            sign = 1.0 if hib else -1.0
            for algo, val in by_algo.items():
                if np.isfinite(val):
                    vals.append(float(val) * sign)
                    fa.append(str(algo))
                    fb.append(str(block))
        comp["scheirer_ray_hare"] = scheirer_ray_hare(vals, fa, fb, alpha=alpha)

        if page_order:
            comp["pages_trend"] = pages_trend_test(
                blocks,
                page_order,
                alpha=alpha,
                higher_is_better=higher_is_better,
            )
        if binary_blocks:
            comp["cochran_q"] = cochran_q(binary_blocks, alpha=alpha)

        # Spearman / Kendall on flattened oriented block vectors vs mean ranks order
        if fr.get("mean_ranks"):
            ordered_algos = sorted(fr["mean_ranks"], key=lambda a: fr["mean_ranks"][a], reverse=True)
            # Correlate algorithm index with mean performance across blocks
            _, algos, mat = _block_matrix(blocks, higher_is_better=higher_is_better)
            complete = np.all(np.isfinite(mat), axis=1)
            mat = mat[complete]
            if mat.size:
                mean_perf = {a: float(np.mean(mat[:, j])) for j, a in enumerate(algos)}
                x = [mean_perf[a] for a in ordered_algos if a in mean_perf]
                y = list(range(len(x), 0, -1))  # rank positions
                if len(x) >= 3:
                    comp["spearman_mean_vs_order"] = spearman_rho(x, y, alpha=alpha)
                    comp["kendall_mean_vs_order"] = kendall_tau(x, y, alpha=alpha)
        result["complementary"] = comp
    return result


def run_full_methodology_battery(
    oe_groups: Mapping[str, Mapping[str, Sequence[float]]],
    *,
    oe_higher_is_better: Optional[Mapping[str, bool]] = None,
    og_blocks: Optional[Mapping[str, Mapping[str, float]]] = None,
    topsis_weights: Optional[Mapping[str, float]] = None,
    alpha: float = 0.05,
    complementary: bool = False,
    binary_blocks: Optional[Mapping[str, Mapping[str, int]]] = None,
    page_order: Optional[Sequence[str]] = None,
    expected_n_seeds: int = 12,
    sample_unit: str = "seed",
) -> Dict[str, object]:
    """Run OE.1/OE.2/OE.3 batteries then OG synthesis (section 8 flow).

    Each OE group must be algorithm → seed scores (canonical ``expected_n_seeds=12``).
    """

    hib_default = {"OE.1": True, "OE.2": False, "OE.3": False, "E1": True, "E2": False, "E3": False}
    hib = dict(hib_default)
    if oe_higher_is_better:
        hib.update(oe_higher_is_better)

    oe_results: Dict[str, object] = {}
    block_means: Dict[str, Dict[str, float]] = {}
    for name, groups in oe_groups.items():
        higher = bool(hib.get(name, True))
        oe_results[name] = run_oe_battery(
            groups,
            objective=name,
            higher_is_better=higher,
            alpha=alpha,
            complementary=complementary,
            expected_n_seeds=expected_n_seeds,
            sample_unit=sample_unit,
        )
        block_means[name] = {
            algo: float(np.mean(_finite(vals)))
            for algo, vals in groups.items()
            if _finite(vals).size
        }

    blocks = og_blocks if og_blocks is not None else block_means
    # TOPSIS decision matrix: algorithms × OE criteria (raw means; kinds encode cost/benefit)
    algos = sorted({a for by in blocks.values() for a in by})
    topsis_means: Dict[str, Dict[str, float]] = {a: {} for a in algos}
    kinds: Dict[str, str] = {}
    block_hib: Dict[str, bool] = {}
    for block, by_algo in blocks.items():
        higher = bool(hib.get(block, True))
        block_hib[block] = higher
        kinds[block] = "benefit" if higher else "cost"
        for algo, val in by_algo.items():
            topsis_means.setdefault(algo, {})[block] = float(val)

    weights = topsis_weights or {b: 1.0 / max(len(blocks), 1) for b in blocks}
    og = run_og_battery(
        blocks,
        higher_is_better=block_hib,
        topsis_means=topsis_means,
        topsis_weights=weights,
        topsis_criteria_kind=kinds,
        alpha=alpha,
        complementary=complementary,
        binary_blocks=binary_blocks,
        page_order=page_order,
    )
    return {
        "oe": oe_results,
        "og": og,
        "topsis_weights": weights,
        "topsis_criteria_kind": kinds,
        "alpha": float(alpha),
        "complementary": bool(complementary),
        "expected_n_seeds": int(expected_n_seeds),
        "sample_unit": sample_unit,
    }


# ---------------------------------------------------------------------------
# Narrative reporting (section 8 style)
# ---------------------------------------------------------------------------


def format_oe_report(result: Mapping[str, object]) -> str:
    """Human-readable OE narrative (H, p, epsilon^2, Dunn pairs, Cliff delta)."""

    obj = result.get("objective", "OE")
    kw = result.get("kruskal_wallis") or {}
    cov = result.get("sample_coverage") or {}
    lines = [
        f"### {obj} — bateria no parametrica",
        "",
        f"Orientacion: {'mayor es mejor' if result.get('higher_is_better') else 'menor es mejor (coste/emision)'}.",
        f"Unidad de analisis: {cov.get('unit', 'seed')} | "
        f"n_esperado={cov.get('expected_n_seeds')} | "
        f"n_por_algoritmo={cov.get('n_by_algorithm')} | "
        f"cobertura_completa={cov.get('complete')}.",
    ]
    if cov.get("warning"):
        lines.append(f"AVISO: {cov.get('warning')}")
    lines += [
        "",
        "**Shapiro-Wilk (por algoritmo)**",
    ]
    for algo, sw in (result.get("shapiro_wilk") or {}).items():
        lines.append(
            f"- {algo}: W={sw.get('statistic')}, p={sw.get('p_value')}, "
            f"normalidad_rechazada={sw.get('normality_rejected')} [{sw.get('status')}]"
        )
    fl = result.get("fligner_killeen") or {}
    lines += [
        "",
        f"**Fligner-Killeen**: estadistico={fl.get('statistic')}, p={fl.get('p_value')}, "
        f"heterocedasticidad={fl.get('significant')}.",
        "",
        f"**Kruskal-Wallis**: H={kw.get('H')}, p={kw.get('p_value')}, "
        f"epsilon^2={result.get('epsilon_squared')}, significativo={kw.get('significant')}.",
        f"Rangos medios: {kw.get('mean_ranks')}",
        "",
        "**Dunn post-hoc (Holm)**",
    ]
    for row in result.get("dunn_holm") or []:
        lines.append(
            f"- {row.get('algorithm_a')} vs {row.get('algorithm_b')}: "
            f"z={row.get('z')}, p_raw={row.get('p_raw')}, p_holm={row.get('p_holm')}, "
            f"sig={row.get('significant')}, Cliff d={row.get('cliffs_delta')} "
            f"({row.get('cliffs_delta_magnitude')})"
        )
    lines += ["", "**Cliff's delta (todos los pares, metrica orientada)**"]
    for row in result.get("cliffs_delta_pairs") or []:
        lines.append(
            f"- {row.get('algorithm_a')} vs {row.get('algorithm_b')}: "
            f"d={row.get('cliffs_delta')} ({row.get('cliffs_delta_magnitude')})"
        )
    win = result.get("winner") or {}
    lines += [
        "",
        f"**Ganador(es)**: {win.get('winners')} "
        f"(primary={win.get('primary_among_cowinners')}, status={win.get('status')})",
    ]
    for note in win.get("rationale") or []:
        lines.append(f"- {note}")
    return "\n".join(lines)


def format_og_report(result: Mapping[str, object]) -> str:
    fr = result.get("friedman") or {}
    nem = result.get("nemenyi") or {}
    topsis = result.get("topsis") or {}
    val = result.get("topsis_vs_friedman") or {}
    lines = [
        "### OG — sintesis global (E1+E2+E3 como bloques)",
        "",
        f"**Friedman**: chi2={fr.get('chi2')}, p={fr.get('p_value')}, "
        f"W={result.get('kendalls_w')}, significativo={fr.get('significant')}.",
        f"Rangos medios Friedman: {fr.get('mean_ranks')}",
        "",
        f"**Nemenyi**: CD={nem.get('critical_difference')} (alpha={nem.get('alpha')})",
    ]
    for row in nem.get("pairs") or []:
        lines.append(
            f"- {row.get('algorithm_a')} vs {row.get('algorithm_b')}: "
            f"|dR|={row.get('rank_diff')}, sig={row.get('significant')}"
        )
    lines += ["", "**TOPSIS (declaracion oficial de ganador)**"]
    for row in topsis.get("ranking") or []:
        lines.append(
            f"- #{row.get('rank')} {row.get('algorithm')}: C*={row.get('closeness')}"
        )
    lines += ["", "**Validacion TOPSIS vs Friedman-Nemenyi**"]
    for note in val.get("notes") or []:
        lines.append(f"- {note}")
    if val.get("discrepancy"):
        lines.append("- [!] Discrepancia reportada entre TOPSIS y Friedman.")
    return "\n".join(lines)


def format_full_report(battery: Mapping[str, object]) -> str:
    parts = [
        "# Bateria no parametrica MADRL (HAPPO, MAAC, MASAC, MATD3)",
        "",
        f"alpha={battery.get('alpha')}, complementary={battery.get('complementary')}",
        f"expected_n_seeds={battery.get('expected_n_seeds', 12)}, "
        f"sample_unit={battery.get('sample_unit', 'seed')}",
        f"TOPSIS weights: {battery.get('topsis_weights')}",
        f"TOPSIS criteria kinds: {battery.get('topsis_criteria_kind')}",
        "",
    ]
    for _name, oe in (battery.get("oe") or {}).items():
        parts.append(format_oe_report(oe))
        parts.append("")
    if battery.get("og"):
        parts.append(format_og_report(battery["og"]))
    return "\n".join(parts)


def significance_gate_top_metrics(
    per_seed_metrics: Mapping[str, Mapping[str, Sequence[float]]],
    *,
    top_criteria: Sequence[str] = ("C1", "C2"),
    first: str,
    second: str,
    alpha: float = 0.05,
) -> Dict[str, object]:
    """Check whether 1st vs 2nd differ significantly on the heaviest criteria.

    ``per_seed_metrics`` maps criterion -> algorithm -> seed values.
    For cost criteria, lower is better; tests remain two-sided on raw values.
    """

    details: Dict[str, object] = {}
    any_significant = False
    for cid in top_criteria:
        if cid not in per_seed_metrics:
            details[cid] = {"status": "missing_criterion"}
            continue
        by_algo = per_seed_metrics[cid]
        if first not in by_algo or second not in by_algo:
            details[cid] = {"status": "missing_algorithm"}
            continue
        test = wilcoxon_signed_rank(by_algo[first], by_algo[second], alpha=alpha)
        details[cid] = test
        any_significant = any_significant or bool(test.get("significant"))
    return {
        "first": first,
        "second": second,
        "top_criteria": list(top_criteria),
        "any_significant": bool(any_significant),
        "defensible": bool(any_significant),
        "details": details,
        "alpha": float(alpha),
    }
