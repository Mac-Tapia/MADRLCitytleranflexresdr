# Backend Evaluation

Evaluate HAPPO, MASAC, MATD3, and MAAC as proposed MADRL backends for CityLearn v3 propuesto.

## Criteria

For each backend, record:

1. Compatibility with Dec-POMDP.
2. Compatibility with CTDE.
3. Cooperation capacity between agents.
4. Training stability.
5. Sample efficiency.
6. Robustness to partial observability.
7. Multi-objective optimization capacity.
8. Ease of integration with CityLearn v2.
9. Ease of integration with Gymnasium.
10. Ease of integration with PettingZoo.
11. GitHub implementation availability.
12. PyTorch compatibility.
13. MARLlib compatibility.
14. Optuna tuning possibility.
15. Usefulness for CityLearn v3 propuesto.

## Required Comparison Columns for `Backends_MADRL`

1. Tipo de algoritmo
2. Tipo de política
3. Acción continua o discreta
4. Compatibilidad con observabilidad parcial
5. Compatibilidad con CTDE
6. Compatibilidad con Dec-POMDP
7. Tipo de cooperación
8. Ventajas
9. Limitaciones
10. Hiperparámetros principales
11. Métricas de entrenamiento
12. Repositorios GitHub disponibles
13. Soporte en MARLlib
14. Disponibilidad en MARLlib oficial
15. Disponibilidad mediante extensión personalizada
16. Compatibilidad con RLlib/Ray
17. Compatibilidad con wrapper multiagente
18. Compatibilidad con PettingZoo/Gymnasium
19. Complejidad de integración con CityLearn v2
20. Uso propuesto dentro de CityLearn v3
21. Limitaciones de MARLlib para CityLearn v3
22. Idoneidad para flexibilidad energética
23. Idoneidad para emisiones de CO2
24. Idoneidad para costos energéticos
25. Idoneidad para CityLearn v3 propuesto

## Algorithm Notes

- HAPPO/HATRPO: on-policy cooperative policy optimization; evaluate trust-region or PPO style stability and decentralized actors with centralized training.
- MASAC: entropy-regularized multi-agent soft actor-critic; evaluate discrete/continuous variants, centralized critics or value decomposition, exploration, and memory cost.
- MATD3: off-policy deterministic actor-critic with twin delayed critics; evaluate continuous control, replay buffer, policy delay, target smoothing, and sample efficiency.
- MAAC: attention-based multi-agent actor-critic; evaluate centralized attention critic, variable relevance across agents, and scalability.

Do not state support in MARLlib unless verified from MARLlib documentation or repository. If unsupported, use `no identificado publicamente` or `requiere extensión personalizada`.

