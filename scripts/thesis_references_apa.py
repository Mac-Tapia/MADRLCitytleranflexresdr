"""Carga referencias APA desde docs/tesis_capitulos/Referencias_APA.md (skill integrado)."""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
APA_MD = REPO / "docs" / "tesis_capitulos" / "Referencias_APA.md"

# Citadas en Cap. 2-4 del borrador pero ausentes del .md consolidado.
SUPPLEMENTAL_CITED_IN_TEXT = [
    "Abels, A., Roijers, D., Lenaerts, T., Nowe, A., & Steckelmacher, D. (2019). Dynamic weights in multi-objective deep reinforcement learning. En Proceedings of the 36th International Conference on Machine Learning (PMLR 97, pp. 11-20). https://arxiv.org/abs/1809.07803",
    "Felten, F., Talbi, E.-G., & Danoy, G. (2024). Multi-objective reinforcement learning based on decomposition: A taxonomy and framework. Journal of Artificial Intelligence Research, 79. https://arxiv.org/abs/2311.12495",
    "Felten, F., Ucak, B., Azmani, M., et al. (2024). MOMAland: A set of benchmarks for multi-objective multi-agent reinforcement learning. arXiv. https://arxiv.org/abs/2407.16312",
    "Fujimoto, S., van Hoof, H., & Meger, D. (2018). Addressing function approximation error in actor-critic methods (TD3). En Proceedings of the 35th International Conference on Machine Learning (PMLR 80, pp. 1587-1596). https://arxiv.org/abs/1802.09477",
    "Roijers, D. M., Vamplew, P., Whiteson, S., & Dazeley, R. (2013). A survey of multi-objective sequential decision-making. Journal of Artificial Intelligence Research, 47, 67-113.",
    "Zhou, M., Wan, J., Wang, H., et al. (2021). MALib: A parallel framework for population-based multi-agent reinforcement learning. Journal of Machine Learning Research, 24(1). https://arxiv.org/abs/2106.07551",
    "Chevarria Moscoso, M. (2024). Analisis de la generacion hidroelectrica en la central hidroelectrica de Machupicchu aplicando metodos estocasticos y modelo de optimizacion (Tesis doctoral). Universidad Nacional de Ingenieria. http://hdl.handle.net/20.500.14076/28894",
    "Dominguez-Barbero, C. (2026). Modeling and optimizing isolated microgrids using Reinforcement Learning techniques (Tesis doctoral). Universidad Pontificia Comillas.",
    "Peñalva Sanchez, J. J. (2024). Optimizacion de un sistema fotovoltaico hibrido y la prediccion de la demanda energetica y variables climaticas utilizando la inteligencia artificial (Tesis doctoral). Universidad Nacional de Ingenieria. http://hdl.handle.net/20.500.14076/27731",
    "Rosero Bernal, D. G. (2024). Modelo de un sistema de administracion de energia autonomo operado desde la nube para optimizar la gestion de un grupo de microredes (Tesis doctoral). Universidad Distrital Francisco Jose de Caldas. [PV]",
    "Electro Oriente S.A. (2023-2025). Facturas mensuales de edificios institucionales del SEAI Iquitos. Loreto, Peru.",
]

# Protocolo estadistico RL (module-b-thesis-report.md, Cap. 3.7 / 5.4).
STATS_METHODOLOGY = [
    "Agarwal, R., Schwarzer, M., Castro, P. S., Courville, A., & Bellemare, M. G. (2021). Deep reinforcement learning at the edge of the statistical precipice. En Advances in Neural Information Processing Systems, 34, 29304-29320. https://arxiv.org/abs/2108.13264",
    "Colas, C., Sigaud, O., & Oudeyer, P.-Y. (2019). A hitchhiker's guide to statistical comparisons of reinforcement learning algorithms. arXiv. https://arxiv.org/abs/1904.06979",
    "Demsar, J. (2006). Statistical comparisons of classifiers over multiple data sets. Journal of Machine Learning Research, 7, 1-30.",
    "Dunn, O. J. (1964). Multiple comparisons using rank sums. Technometrics, 6(3), 241-252. https://doi.org/10.1080/00401706.1964.10490181",
    "Henderson, P., Islam, R., Bachman, P., Pineau, J., Precup, D., & Meger, D. (2018). Deep reinforcement learning that matters. Proceedings of the AAAI Conference on Artificial Intelligence, 32(1). https://doi.org/10.1609/aaai.v32i1.11694",
    "Patterson, A., Neumann, S., White, M., & White, A. (2024). Empirical design in reinforcement learning. Journal of Machine Learning Research, 25. https://arxiv.org/abs/2304.01315",
]


def _normalize_ref(text: str) -> str:
    ref = text.strip()
    ref = re.sub(r"\s*✓\s*$", "", ref)
    ref = ref.replace("*", "")
    ref = re.sub(r"\s+", " ", ref)
    return ref


def _ref_key(ref: str) -> str:
    m = re.match(r"^([^,(]+)", ref)
    author = (m.group(1).strip() if m else ref[:20]).lower()
    ym = re.search(r"\((\d{4})", ref)
    year = ym.group(1) if ym else "0000"
    return f"{author}|{year}"


def parse_apa_markdown(path: Path = APA_MD) -> list[str]:
    if not path.is_file():
        raise FileNotFoundError(f"Falta fuente APA del skill: {path}")
    refs: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line.startswith("- "):
            continue
        ref = _normalize_ref(line[2:])
        if ref and not ref.startswith("░░"):
            refs.append(ref)
    return refs


def load_all_thesis_references() -> list[str]:
    """Referencias consolidadas: Referencias_APA.md + citadas en texto + estadistica RL."""
    merged: dict[str, str] = {}
    for ref in parse_apa_markdown() + SUPPLEMENTAL_CITED_IN_TEXT + STATS_METHODOLOGY:
        merged.setdefault(_ref_key(ref), ref)
    return sorted(merged.values(), key=lambda r: r.lower())


def reference_stats() -> dict:
    apa_only = parse_apa_markdown()
    all_refs = load_all_thesis_references()
    return {
        "source": str(APA_MD),
        "from_apa_md": len(apa_only),
        "supplemental": len(SUPPLEMENTAL_CITED_IN_TEXT),
        "stats_methodology": len(STATS_METHODOLOGY),
        "total_unique": len(all_refs),
        "pv_marked": sum(1 for r in all_refs if "[PV" in r.upper()),
    }
