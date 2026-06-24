# Search Protocol

## Scope

Search 50 relevant investigations from the last 10 years when possible, covering:

- CityLearn v2, CityLearn Challenge 2022/2023, CityLearn Gymnasium, CityLearn datasets, CityLearn carbon intensity, pricing, energy cost, demand response, flexibility, BESS, EV charging, wrappers, PettingZoo, Dec-POMDP, CTDE, MADRL, and DRL.
- Cooperative and collaborative MADRL, Dec-POMDP, partially observable games, CTDE, global state, local observations, joint actions, shared reward, hybrid reward, reward shaping, and multi-objective optimization.
- HAPPO, HATRPO, MASAC, Multi-Agent Soft Actor-Critic, MATD3, Multi-Agent TD3, MAAC, Multi-Actor-Attention-Critic, MADDPG, MAPPO, IPPO, COMA, QMIX, VDN, MADQN.
- MARLlib as framework/repository/library reference for wrappers, policy mapping, scenario config, algorithm config, RLlib/Ray, PyTorch, CTDE, POMDP/Dec-POMDP, cooperative learning, custom environments, and reproducibility.
- Energy flexibility, demand response, CO2 emissions, carbon intensity, energy cost, dynamic pricing, BESS, EV charging, V2G, smart grids, smart buildings, digital twins, and datasets.
- Optuna and hyperparameter optimization for DRL/MADRL.
- SEAI Iquitos applicability: isolated power system, PV, BESS, EV charging, emissions, energy cost, safe operation, electrical constraints.

## Mandatory Boolean Strings

1. `("CityLearn v2" OR "CityLearn") AND ("carbon emissions" OR "CO2 emissions" OR "carbon intensity") AND ("energy cost" OR "electricity pricing" OR "electricity cost")`
2. `("CityLearn v2" OR "CityLearn Challenge" OR "CityLearn") AND ("multi-agent deep reinforcement learning" OR MADRL OR "cooperative multi-agent reinforcement learning") AND ("demand response" OR "energy flexibility" OR "grid-interactive communities")`
3. `("CityLearn v2" OR "CityLearn") AND ("Dec-POMDP" OR "partially observable game") AND ("centralized training decentralized execution" OR CTDE)`
4. `("multi-agent deep reinforcement learning" OR MADRL) AND ("centralized training decentralized execution" OR CTDE) AND ("Dec-POMDP" OR "partially observable stochastic game" OR "partially observable game")`
5. `(HAPPO OR MASAC OR MATD3 OR MAAC) AND ("multi-agent deep reinforcement learning" OR MADRL) AND ("energy management" OR "demand response" OR "smart grid" OR "building control")`
6. `("HAPPO" OR "HATRPO") AND ("cooperative multi-agent reinforcement learning" OR "multi-agent deep reinforcement learning" OR CTDE)`
7. `("multi-agent soft actor-critic" OR MASAC) AND ("demand response" OR "energy management" OR "power systems" OR "smart grid")`
8. `("multi-agent twin delayed deep deterministic policy gradient" OR MATD3) AND ("energy management" OR "microgrid" OR "demand response" OR "power system")`
9. `("multi-actor-attention-critic" OR MAAC OR "attention-based multi-agent reinforcement learning") AND ("energy management" OR "demand response" OR "smart grid")`
10. `("MARLlib" OR "Multi-Agent RLlib") AND ("multi-agent reinforcement learning" OR "multi-agent deep reinforcement learning" OR MADRL) AND (CTDE OR "centralized training decentralized execution")`
11. `("MARLlib" OR "Multi-Agent RLlib") AND ("custom environment" OR "environment wrapper" OR Gymnasium OR PettingZoo) AND ("CityLearn" OR "energy management" OR "demand response")`
12. `("MARLlib" OR "Multi-Agent RLlib") AND (HAPPO OR HATRPO OR MASAC OR MATD3 OR MAAC OR MADDPG OR MAPPO) AND ("GitHub" OR "source code" OR "implementation")`
13. `("MARLlib" OR "Multi-Agent RLlib") AND ("cooperative" OR "collaborative" OR "centralized critic" OR "value decomposition" OR "policy mapping")`
14. `("MARLlib" OR "Multi-Agent RLlib") AND ("smart grid" OR "building control" OR "demand response" OR "energy flexibility" OR "carbon emissions" OR "energy cost")`
15. `("energy flexibility" OR "electric flexibility" OR "demand flexibility") AND ("multi-agent deep reinforcement learning" OR MADRL) AND (KPI OR metrics OR benchmark)`
16. `("carbon emissions" OR "CO2 emissions" OR "carbon intensity") AND ("multi-agent deep reinforcement learning" OR MADRL OR "deep reinforcement learning") AND ("energy management" OR "demand response")`
17. `("energy cost" OR "electricity cost" OR "electricity pricing" OR tariff) AND ("multi-agent deep reinforcement learning" OR MADRL OR "deep reinforcement learning") AND ("demand response" OR "building energy management")`
18. `("PhD thesis" OR "doctoral dissertation" OR "master thesis" OR "MSc thesis" OR "tesis doctoral" OR "tesis de maestría") AND ("multi-agent deep reinforcement learning" OR MADRL OR "deep reinforcement learning") AND ("demand response" OR "smart grid" OR "energy management" OR "CityLearn")`
19. `("CityLearn" OR "multi-agent deep reinforcement learning" OR MADRL OR "MARLlib") AND ("dataset" OR "benchmark" OR "GitHub" OR "source code" OR "repository") AND ("energy management" OR "demand response" OR "carbon emissions" OR "energy cost")`

## Priority Sources

Search: Google Scholar, IEEE Xplore, ScienceDirect, SpringerLink, MDPI, ACM Digital Library, Wiley, Taylor & Francis, arXiv, OpenReview, PMLR, NeurIPS, ICML, ICLR, AAMAS, Elsevier Energy and Buildings, Applied Energy, Energy AI, Sustainable Cities and Society, Electric Power Systems Research, International Journal of Electrical Power & Energy Systems, IEEE Transactions on Smart Grid, IEEE Transactions on Sustainable Energy, IEEE Transactions on Power Systems, IEEE Access, JMLR, university repositories, ProQuest Dissertations, EThOS, DART-Europe, TDX, Cybertesis, RENATI, GitHub, Papers with Code, CityLearn official documentation, CityLearn GitHub, MARLlib GitHub, MARLlib documentation, NREL, OpenEI, Pecan Street, UK-DALE, REDD, and Open Power System Data.

## Inclusion Criteria

- Last 10 years when possible.
- Indexed articles, doctoral theses, PhD dissertations, master theses, proceedings, benchmarks, and technical reports.
- Direct relation to MADRL, DRL, CityLearn, MARLlib, demand response, energy flexibility, CO2 emissions, energy costs, BESS, EV charging, communities, smart grids, or power systems.
- Verifiable academic link, PDF, DOI, dataset, or repository when possible.
- Contribution to CityLearn v3 propuesto, Dec-POMDP, CTDE, cooperation, partial observability, multi-objective reward, or Optuna tuning.

## Exclusion Criteria

- No relation to energy systems, multiagent control, DRL, MADRL, CityLearn, or MARLlib.
- No minimal source traceability.
- Missing year, author, or source, unless clearly marked as incomplete and uniquely relevant.
- Purely conceptual work without methodological contribution, except strong systematic reviews.
- Unverifiable PDF/article/DOI/dataset/GitHub unless marked as `no identificado publicamente`.

