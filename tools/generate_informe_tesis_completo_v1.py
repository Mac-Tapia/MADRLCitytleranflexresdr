"""
Genera el Informe de Tesis completo bajo Guía N. 02 sección 5.1.
Título: MULTI-AGENTE DE APRENDIZAJE POR REFUERZO PROFUNDO PARA LA GESTIÓN
COORDINADA DE FLEXIBILIDAD ENERGÉTICA, EMISIONES DE CARBONO Y COSTOS
ENERGÉTICOS EN COMUNIDADES INTELIGENTES
"""

from __future__ import annotations
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

sys.path.insert(0, str(Path(__file__).parent))
import _thesis_marco_teorico as MT
import _thesis_capitulo_iii as C3

OUTPUT = Path(__file__).parent.parent / "docs" / "INFORME_TESIS_MADRL_V1_COMPLETO.docx"

TITULO = (
    "MULTI-AGENTE DE APRENDIZAJE POR REFUERZO PROFUNDO PARA LA GESTIÓN "
    "COORDINADA DE FLEXIBILIDAD ENERGÉTICA, EMISIONES DE CARBONO Y COSTOS "
    "ENERGÉTICOS EN COMUNIDADES INTELIGENTES"
)
# ── Citas APA en texto (norma APA 7ª edición, autor-año) ─────────────────────
SUTTON_BARTO   = "(Sutton & Barto, 2018)"
MNIH_2015      = "(Mnih et al., 2015)"
LOWE_2017      = "(Lowe et al., 2017)"
HAARNOJA_2018  = "(Haarnoja et al., 2018)"
FUJIMOTO_2018  = "(Fujimoto et al., 2018)"
OLIEHOEK_2016  = "(Oliehoek & Amato, 2016)"
IQBAL_SHA      = "(Iqbal & Sha, 2019)"
VAZQUEZ_NAGY   = "(Vázquez-Canteli & Nagy, 2019)"
AKIBA_2019     = "(Akiba et al., 2019)"
KUBA_2022      = "(Kuba et al., 2022)"
NWEYE_2023     = "(Nweye et al., 2023)"
HU_2023        = "(Hu et al., 2023)"
HERNANDEZ_2019 = "(Hernandez-Leal et al., 2019)"
NC = "(véase referencias)"   # fallback residual
NR = "[resultado por validar en etapa de simulación]"


# ─── XML helpers ─────────────────────────────────────────────────────────────

def _x(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def h(text: str, lvl: int = 1) -> str:
    style = f'<w:pStyle w:val="Heading{min(lvl, 9)}"/>'
    return (
        f'<w:p><w:pPr>{style}</w:pPr>'
        f'<w:r><w:t xml:space="preserve">{_x(text)}</w:t></w:r></w:p>'
    )


def p(text: str, bold: bool = False, italic: bool = False, center: bool = False) -> str:
    rpr = ""
    if bold:
        rpr += "<w:b/>"
    if italic:
        rpr += "<w:i/>"
    ppr = '<w:jc w:val="center"/>' if center else ""
    return (
        f'<w:p><w:pPr>{ppr}</w:pPr>'
        f'<w:r><w:rPr>{rpr}</w:rPr>'
        f'<w:t xml:space="preserve">{_x(text)}</w:t></w:r></w:p>'
    )


def pb() -> str:
    """Page break."""
    return (
        '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'
    )


def bullet(text: str) -> str:
    return p("  • " + text)


# ─── Document body ────────────────────────────────────────────────────────────

def build() -> str:
    P: list[str] = []

    # ══════════════════════════════════════════════════════════════════════════
    # CARÁTULA
    # ══════════════════════════════════════════════════════════════════════════
    P.append(h("CARÁTULA", 1))
    P.append(p("Universidad Nacional Mayor de San Marcos", bold=True, center=True))
    P.append(p("Facultad / Escuela de Posgrado: [pendiente]", center=True))
    P.append(p("Unidad de Posgrado: [pendiente]", center=True))
    P.append(p(""))
    P.append(p(TITULO, bold=True, center=True))
    P.append(p(""))
    P.append(p("Tesis para optar el grado de Maestría de Especialización o Profesionalizante", center=True))
    P.append(p(""))
    P.append(p("Autor: [Nombre del graduando]", center=True))
    P.append(p("Asesor: [Nombre del asesor]", center=True))
    P.append(p(""))
    P.append(p("Lima, Perú — 2026", center=True))
    P.append(pb())

    # ══════════════════════════════════════════════════════════════════════════
    # DATOS GENERALES
    # ══════════════════════════════════════════════════════════════════════════
    P.append(h("DATOS GENERALES", 1))
    P.append(p("Título: " + TITULO))
    P.append(p("Autor: [pendiente]"))
    P.append(p("Asesor: [pendiente]"))
    P.append(p("Área: Ingeniería Eléctrica / Inteligencia Artificial / Sistemas de Energía"))
    P.append(p("Institución: Universidad Nacional Mayor de San Marcos — entorno computacional CityLearn v2 / CityLearn v3 propuesto"))
    P.append(p("Duración: 18 meses (inicio: [mes/año] — fin: [mes/año])"))
    P.append(pb())

    # ── Dedicatoria ──
    P.append(h("Dedicatoria", 1))
    P.append(p("[Pendiente de redacción por el autor]"))
    P.append(pb())

    # ── Agradecimientos ──
    P.append(h("Agradecimientos", 1))
    P.append(p("[Pendiente de redacción por el autor]"))
    P.append(pb())

    # ── Índice ──
    P.append(h("Índice de contenidos", 1))
    índice = [
        "Resumen / Abstract",
        "Introducción",
        "Capítulo I. Planteamiento del problema",
        "  1.1 Diagnóstico",
        "  1.2 Identificación y descripción del problema",
        "  1.3 Formulación del problema",
        "    1.3.1 Problema general",
        "    1.3.2 Problemas específicos",
        "  1.4 Objetivos",
        "    1.4.1 Objetivo general",
        "    1.4.2 Objetivos específicos",
        "  1.5 Justificación del estudio",
        "  1.6 Alcance del estudio",
        "Capítulo II. Marco teórico",
        "  2.1 Antecedentes",
        "  2.2 Bases teóricas",
        "  2.3 Definición de términos",
        "Capítulo III. Desarrollo del trabajo de tesis",
        "  3.1 Presentación de la propuesta de solución",
        "  3.2 Desarrollo de la propuesta de solución",
        "  3.3 Análisis de los datos y resultados",
        "  3.4 Discusión e interpretación de los resultados",
        "  3.5 Estimación del impacto de la solución",
        "Capítulo IV. Conclusiones y recomendaciones",
        "  4.1 Conclusiones",
        "  4.2 Recomendaciones",
        "Referencias",
        "Anexos",
    ]
    for item in índice:
        P.append(p(item))
    P.append(pb())

    # ══════════════════════════════════════════════════════════════════════════
    # RESUMEN / ABSTRACT
    # ══════════════════════════════════════════════════════════════════════════
    P.append(h("Resumen", 1))
    P.append(p(
        "Las comunidades inteligentes que integran recursos de energía distribuida —generación "
        "fotovoltaica (PV), sistemas de almacenamiento con baterías (BESS) y carga de vehículos "
        "eléctricos (EV)— enfrentan el desafío de gestionar de manera coordinada la flexibilidad "
        "energética, las emisiones de CO2 y los costos energéticos. Los métodos de control "
        "convencionales y los enfoques de agente único basados en aprendizaje profundo por refuerzo "
        "(DRL) resultan insuficientes ante la heterogeneidad y escala de estas comunidades. La "
        "presente investigación tiene por objetivo determinar el mejor Multi-Agente de Aprendizaje "
        "por Refuerzo Profundo (MADRL) que gestiona de manera coordinada las tres dimensiones de "
        "desempeño en comunidades inteligentes. Para ello, se propone CityLearn v3 propuesto: una "
        "extensión experimental sobre CityLearn v2 que implementa una capa MADRL cooperativa "
        "formulada como proceso de decisión de Markov parcialmente observable descentralizado "
        "(Dec-POMDP) y entrenada bajo el esquema de entrenamiento centralizado con ejecución "
        "descentralizada (CTDE). Se evalúan cuatro backends: HAPPO, MASAC, MATD3 y MAAC, ajustados "
        "con Optuna, sobre tres ejes de indicadores de desempeño (KPIs): flexibilidad energética "
        "(OE.1), emisiones de CO2 (OE.2) y costos energéticos (OE.3). Los resultados esperados "
        "incluyen el ranking comparativo de los cuatro algoritmos por eje y la determinación del "
        "mejor MADRL en gestión coordinada. "
        + NR
    ))
    P.append(p(
        "Palabras clave: aprendizaje por refuerzo profundo multiagente, MADRL, CityLearn, "
        "Dec-POMDP, CTDE, flexibilidad energética, emisiones de CO2, costos energéticos, "
        "comunidades inteligentes, HAPPO, MASAC, MATD3, MAAC."
    ))
    P.append(p(""))
    P.append(h("Abstract", 1))
    P.append(p(
        "Smart communities integrating distributed energy resources —photovoltaic generation (PV), "
        "battery energy storage systems (BESS), and electric vehicle (EV) charging— face the "
        "challenge of coordinately managing energy flexibility, CO2 emissions, and energy costs. "
        "Conventional control methods and single-agent deep reinforcement learning (DRL) approaches "
        "are insufficient for the heterogeneity and scale of these communities. This research aims "
        "to determine the best Multi-Agent Deep Reinforcement Learning (MADRL) algorithm that "
        "coordinately manages the three performance dimensions in smart communities. To this end, "
        "CityLearn v3 propuesto is proposed: an experimental extension of CityLearn v2 implementing "
        "a cooperative MADRL layer formulated as a Decentralized Partially Observable Markov "
        "Decision Process (Dec-POMDP) and trained under the Centralized Training Decentralized "
        "Execution (CTDE) scheme. Four backends are evaluated: HAPPO, MASAC, MATD3, and MAAC, "
        "tuned with Optuna, on three KPI axes: energy flexibility (OE.1), CO2 emissions (OE.2), "
        "and energy costs (OE.3). Expected results include the comparative ranking of the four "
        "algorithms per axis and the determination of the best MADRL for coordinated management. "
        + NR
    ))
    P.append(p(
        "Keywords: multi-agent deep reinforcement learning, MADRL, CityLearn, Dec-POMDP, CTDE, "
        "energy flexibility, CO2 emissions, energy costs, smart communities, HAPPO, MASAC, MATD3, MAAC."
    ))
    P.append(pb())

    # ══════════════════════════════════════════════════════════════════════════
    # INTRODUCCIÓN
    # ══════════════════════════════════════════════════════════════════════════
    P.append(h("Introducción", 1))
    P.append(p(
        "La transición energética global impulsa la integración masiva de recursos de energía "
        "distribuida (DER) en los entornos residenciales y urbanos. Las comunidades inteligentes "
        f"(smart communities) son el escenario donde esta transición se materializa {NWEYE_2023}, "
        "caracterizándose por la coexistencia de generación fotovoltaica distribuida (PV), sistemas "
        "de almacenamiento con baterías (BESS) y estaciones de carga para vehículos eléctricos "
        "(EV), junto con señales de precio de electricidad dinámicas e intensidad de carbono "
        "horaria variables. Esta complejidad multidimensional exige estrategias de control que "
        "optimicen simultáneamente la flexibilidad energética, las emisiones de CO2 y los costos "
        "energéticos de la comunidad."
    ))
    P.append(p(
        "Los métodos de control basados en reglas y los enfoques de agente único con aprendizaje "
        "profundo por refuerzo (DRL) han demostrado limitaciones significativas para gestionar "
        "carteras heterogéneas de edificios con recursos DER diversos: no generalizan ante la "
        "variabilidad de los perfiles de demanda, no explotan la coordinación entre edificios y "
        f"no escalan eficientemente al incrementar el número de agentes {HERNANDEZ_2019}. El aprendizaje por "
        "refuerzo profundo multiagente (MADRL) cooperativo bajo formulación Dec-POMDP y esquema "
        "CTDE surge como el paradigma más prometedor para superar estas limitaciones, permitiendo "
        "que múltiples agentes —uno por edificio— coordinen sus decisiones de despacho de DER "
        "hacia objetivos comunes de flexibilidad, CO2 y costo."
    ))
    P.append(p(
        "Sin embargo, la literatura existente carece de un benchmark unificado que compare los "
        "principales algoritmos MADRL —HAPPO, MASAC, MATD3 y MAAC— bajo condiciones homogéneas "
        "de formulación Dec-POMDP y evaluación sobre los tres ejes de desempeño en comunidades "
        f"inteligentes {HU_2023}. Este vacío metodológico impide determinar cuál es el mejor MADRL "
        "para la gestión coordinada de flexibilidad energética, emisiones de CO2 y costos "
        "energéticos, que es precisamente el problema que esta investigación aborda."
    ))
    P.append(p(
        "Para resolver este problema, se propone CityLearn v3 propuesto: una extensión experimental "
        "sobre CityLearn v2 —entorno de simulación open-source de referencia para la gestión "
        f"multiagente de energía en comunidades inteligentes {NWEYE_2023}— que implementa la capa MADRL "
        "cooperativa con formulación Dec-POMDP, esquema CTDE, función de recompensa multiobjetivo "
        "(flexibilidad + CO2 + costos) y los cuatro backends MADRL propuestos (HAPPO, MASAC, MATD3, "
        "MAAC). El ajuste de hiperparámetros se realiza con Optuna, y MARLlib sirve como referencia "
        "técnica para las implementaciones de los backends."
    ))
    P.append(p(
        "El informe se organiza en cuatro capítulos: el Capítulo I presenta el planteamiento del "
        "problema, los objetivos, la justificación y los alcances; el Capítulo II desarrolla el "
        "marco teórico con antecedentes organizados por los tres ejes de desempeño y el eje "
        "transversal MADRL; el Capítulo III presenta CityLearn v3 propuesto, su desarrollo técnico, "
        "los resultados de la evaluación comparativa y la discusión; el Capítulo IV contiene las "
        "conclusiones y recomendaciones."
    ))
    P.append(pb())

    # ══════════════════════════════════════════════════════════════════════════
    # CAPÍTULO I. PLANTEAMIENTO DEL PROBLEMA
    # ══════════════════════════════════════════════════════════════════════════
    P.append(h("CAPÍTULO I. PLANTEAMIENTO DEL PROBLEMA", 1))

    # 1.1 Diagnóstico
    P.append(h("1.1 Diagnóstico", 2))
    P.append(p(
        "Las comunidades inteligentes constituyen sistemas sociotécnicos de alta complejidad "
        "energética en los que múltiples edificios residenciales y comerciales comparten "
        "infraestructura de generación, almacenamiento y carga eléctrica. La gestión coordinada "
        "de sus recursos DER —PV, BESS y EV— requiere enfrentar simultáneamente tres dimensiones "
        f"críticas de desempeño {VAZQUEZ_NAGY}."
    ))
    for dim, texto in [
        ("Dimensión de flexibilidad energética (OE.1).",
         "La ausencia de control coordinado de los DER en comunidades inteligentes limita la "
         "capacidad del sistema para modular la demanda, desplazar cargas y aprovechar la "
         "generación renovable disponible. Los enfoques de agente único basados en DRL han "
         "demostrado incapacidad para generalizar a carteras heterogéneas de edificios, resultando "
         "en relaciones pico-promedio (PAR) subóptimas, bajo aprovechamiento de la energía "
         f"renovable y escasa reducción de la importación de red {VAZQUEZ_NAGY}. Ningún estudio comparativo "
         "ha determinado qué algoritmo MADRL alcanza el mejor desempeño de flexibilidad energética "
         "en escenarios coordinados de comunidades inteligentes."),
        ("Dimensión de emisiones de carbono (OE.2).",
         "Las comunidades inteligentes operan bajo señales de intensidad de carbono variables "
         "en el tiempo, reflejando la dependencia del suministro eléctrico en fuentes de "
         "generación fósil durante ciertos períodos. La falta de control multiagente coordinado "
         "impide el desplazamiento temporal del consumo hacia ventanas de baja intensidad de "
         f"carbono, elevando las emisiones de CO2 evitables {VAZQUEZ_NAGY}. No existe un benchmark "
         "unificado que determine qué algoritmo MADRL logra la mayor reducción de emisiones "
         "de CO2 en comunidades inteligentes."),
        ("Dimensión de costos energéticos (OE.3).",
         "Las tarifas de uso horario (TOU) y los precios en tiempo real crean incentivos "
         "económicos para la respuesta de demanda coordinada. Sin embargo, las respuestas "
         "no coordinadas a nivel de edificio individual generan resultados colectivos "
         f"subóptimos, con sobrecostos por demanda punta y pérdidas de oportunidad {VAZQUEZ_NAGY}. "
         "Ninguna evaluación rigurosa y comparativa ha determinado qué algoritmo MADRL logra "
         "la mejor reducción de costos energéticos en operación coordinada de comunidades "
         "inteligentes."),
        ("Brecha metodológica.",
         "La literatura existente reporta evaluaciones aisladas de algoritmos individuales "
         "sobre dimensiones únicas, sin un marco comparativo unificado que cubra HAPPO, MASAC, "
         "MATD3 y MAAC bajo formulación Dec-POMDP y esquema CTDE idénticos, evaluados "
         "simultáneamente sobre los tres ejes de desempeño. Esta fragmentación impide la "
         "determinación del mejor MADRL para la gestión coordinada de flexibilidad energética, "
         f"emisiones de CO2 y costos energéticos en comunidades inteligentes {HU_2023}."),
    ]:
        P.append(p(dim, bold=True))
        P.append(p(texto))

    # 1.2 Identificación y descripción
    P.append(h("1.2 Identificación y descripción del problema de estudio", 2))
    P.append(p(
        "El problema central es la ausencia de determinación del mejor algoritmo Multi-Agente de "
        "Aprendizaje por Refuerzo Profundo (MADRL) que gestione de manera coordinada la "
        "flexibilidad energética, las emisiones de CO2 y los costos energéticos en comunidades "
        "inteligentes."
    ))
    campos = [
        ("Síntomas observables:", "alta relación pico-promedio en perfiles de demanda colectiva; "
         "elevado consumo ponderado por intensidad de carbono; costos energéticos subóptimos por "
         "falta de respuesta coordinada a precios dinámicos; ausencia de ranking comparativo de "
         "algoritmos MADRL sobre los tres ejes de desempeño."),
        ("Causas energéticas:", "recursos DER no coordinados entre edificios; ausencia de toma "
         "de decisiones cooperativa entre agentes; no aprovechamiento del estado global compartido "
         "disponible en esquemas CTDE."),
        ("Causas metodológicas:", "falta de un benchmark unificado de HAPPO, MASAC, MATD3 y MAAC "
         "bajo condiciones idénticas de formulación Dec-POMDP y evaluación sobre los tres ejes."),
        ("Consecuencias operacionales:", "despacho subóptimo de DER, incapacidad de explotar "
         "ventanas de respuesta de demanda."),
        ("Consecuencias ambientales:", "exceso de emisiones de CO2 por consumo en períodos de "
         "alta intensidad de carbono."),
        ("Consecuencias económicas:", "sobrecostos evitables por gestión ineficiente de tarifas "
         "dinámicas y cargos por demanda."),
        ("Variable independiente:", "capa MADRL cooperativa implementada sobre CityLearn v2 "
         "(CityLearn v3 propuesto): algoritmos HAPPO, MASAC, MATD3 y MAAC bajo Dec-POMDP y CTDE."),
        ("Variable dependiente:", "desempeño coordinado en flexibilidad energética (OE.1), "
         "emisiones de CO2 (OE.2) y costos energéticos (OE.3) en comunidades inteligentes."),
        ("Ámbito espacial:", "comunidades inteligentes simuladas mediante datasets de CityLearn v2 "
         "y CityLearn v3 propuesto."),
        ("Ámbito temporal:", "período 2015–2026, alineado con la literatura MADRL reciente y los "
         "horizontes temporales de los datasets de CityLearn v2."),
    ]
    for campo, contenido in campos:
        P.append(p(campo + " " + contenido))

    # 1.3 Formulación
    P.append(h("1.3 Formulación del problema", 2))
    P.append(h("1.3.1 Formulación del problema general", 3))
    P.append(p(
        "¿Cuál es el mejor Multi-Agente de Aprendizaje por Refuerzo Profundo que gestiona de "
        "manera coordinada la flexibilidad energética, las emisiones de CO2 y los costos "
        "energéticos en comunidades inteligentes?"
    ))
    P.append(h("1.3.2 Formulación de los problemas específicos", 3))
    P.append(p(
        "PE.1: ¿Cuál es el mejor Multi-Agente de Aprendizaje por Refuerzo Profundo que optimiza "
        "la flexibilidad energética en comunidades inteligentes?"
    ))
    P.append(p(
        "PE.2: ¿Cuál es el mejor Multi-Agente de Aprendizaje por Refuerzo Profundo que reduce "
        "las emisiones de CO2 en comunidades inteligentes?"
    ))
    P.append(p(
        "PE.3: ¿Cuál es el mejor Multi-Agente de Aprendizaje por Refuerzo Profundo que optimiza "
        "los costos energéticos en comunidades inteligentes?"
    ))

    # 1.4 Objetivos
    P.append(h("1.4 Objetivos", 2))
    P.append(h("1.4.1 Objetivo general", 3))
    P.append(p(
        "O.G. — Determinar el mejor Multi-Agente de Aprendizaje por Refuerzo Profundo que gestiona "
        "de manera coordinada la flexibilidad energética, las emisiones de CO2 y los costos "
        "energéticos en comunidades inteligentes."
    ))
    P.append(h("1.4.2 Objetivos específicos", 3))
    P.append(p(
        "OE.1 — Determinar el mejor Multi-Agente de Aprendizaje por Refuerzo Profundo que optimiza "
        "la flexibilidad energética en comunidades inteligentes."
    ))
    P.append(p(
        "OE.2 — Determinar el mejor Multi-Agente de Aprendizaje por Refuerzo Profundo que reduce "
        "las emisiones de CO2 en comunidades inteligentes."
    ))
    P.append(p(
        "OE.3 — Determinar el mejor Multi-Agente de Aprendizaje por Refuerzo Profundo que optimiza "
        "los costos energéticos en comunidades inteligentes."
    ))

    # 1.5 Justificación
    P.append(h("1.5 Justificación del estudio", 2))
    justificaciones = [
        ("Justificación técnica.", "La determinación comparativa del mejor algoritmo MADRL para "
         "gestión coordinada de comunidades inteligentes avanza el estado del arte en control "
         f"cooperativo de energía distribuida {HU_2023}. CityLearn v3 propuesto constituye un benchmark "
         "experimental reproducible y auditable."),
        ("Justificación ambiental.", "Identificar el mejor MADRL para reducción de CO2 contribuye "
         "directamente a los objetivos de descarbonización de sistemas eléctricos y a la reducción "
         f"del impacto ambiental del consumo energético en comunidades inteligentes {NWEYE_2023}."),
        ("Justificación económica.", "Determinar el mejor MADRL para optimización de costos provee "
         "orientación aplicable para reducir la factura energética de comunidades residenciales y "
         f"explotar señales de precio dinámico {VAZQUEZ_NAGY}."),
        ("Justificación metodológica.", "El uso de Dec-POMDP, CTDE, CityLearn v3 propuesto, "
         "HAPPO/MASAC/MATD3/MAAC, MARLlib como referencia técnica y Optuna constituye un marco "
         "metodológico riguroso y reproducible para la evaluación comparativa de MADRL en gestión "
         "energética de comunidades inteligentes."),
        ("Justificación científica.", "La evaluación unificada en tres ejes bajo condiciones "
         "homogéneas cubre un vacío sustantivo en la literatura comparativa de algoritmos MADRL "
         "para gestión energética de comunidades inteligentes."),
        ("Justificación social.", "Comunidades inteligentes con mejor flexibilidad energética, "
         "menores emisiones de carbono y menores costos benefician a sus usuarios residenciales "
         "y contribuyen a la transición energética a escala comunitaria."),
    ]
    for j, texto in justificaciones:
        P.append(p(j, bold=True))
        P.append(p(texto))

    # 1.6 Alcance
    P.append(h("1.6 Alcance del estudio", 2))
    alcances = [
        ("Alcance temático:", "evaluación comparativa de HAPPO, MASAC, MATD3 y MAAC sobre KPIs de "
         "flexibilidad energética (OE.1), emisiones de CO2 (OE.2) y costos energéticos (OE.3) "
         "en simulación de comunidades inteligentes."),
        ("Alcance espacial:", "comunidades inteligentes simuladas con datasets de CityLearn v2 y "
         "CityLearn v3 propuesto. La discusión de aplicabilidad se extiende a sistemas eléctricos "
         "aislados y comunidades grid-interactive."),
        ("Alcance temporal:", "período 2015–2026 alineado con los horizontes de los datasets de "
         "CityLearn v2 y la literatura MADRL reciente."),
        ("Alcance metodológico:", "estudio cuantitativo, comparativo, no experimental, basado en "
         "simulación computacional."),
        ("Alcance computacional:", "Python, PyTorch, CityLearn v2, CityLearn v3 propuesto, "
         "MARLlib (referencia técnica), Optuna, recursos computacionales disponibles."),
        ("Límites:", "no se modela red eléctrica física; los resultados de simulación no "
         "constituyen validación de despliegue en campo; CityLearn v3 propuesto es una extensión "
         "experimental, no una versión oficial de CityLearn."),
        ("Exclusiones:", "despliegue en campo real, investigación con sujetos humanos, despacho "
         "económico de generación física, análisis de estabilidad de red."),
    ]
    for a, texto in alcances:
        P.append(p(a + " " + texto))
    P.append(pb())

    # ══════════════════════════════════════════════════════════════════════════
    # CAPÍTULO II. MARCO TEÓRICO
    # ══════════════════════════════════════════════════════════════════════════
    P.append(h("CAPÍTULO II. MARCO TEÓRICO", 1))

    # 2.1 Antecedentes
    P.append(h("2.1 Antecedentes", 2))
    P += MT.seccion_antecedentes_completos()

    # 2.2 Bases teóricas — contenido profundo desde módulo compartido
    P.append(h("2.2 Bases teóricas", 2))
    P.append(p(
        "Las bases teóricas se desarrollan con triangulación de información entre: (1) la "
        "bibliografía científica identificada en el Módulo A, (2) las evidencias del proyecto "
        "(KPIs_y_metricas.md, Backends_MADRL.md, Arquitectura_Propuesta.md, "
        "Marco_metodologico_MADRL.md, CityLearn_v3_Propuesto.md, resumen_evidencia_tesis.md), "
        "y (3) la documentación oficial de CityLearn v2, MARLlib, HAPPO, MASAC, MATD3, MAAC "
        "y Optuna. La estructura se articula con la variable independiente y las tres "
        "dimensiones de la variable dependiente."
    ))
    # Variable independiente
    P += MT.seccion_variable_independiente()
    # Eje OE.1
    P += MT.seccion_oe1_flexibilidad()
    # Eje OE.2
    P += MT.seccion_oe2_co2()
    # Eje OE.3
    P += MT.seccion_oe3_costos()

    # 2.3 Definición de términos
    P.append(h("2.3 Definición de términos", 2))
    P += MT.seccion_definicion_terminos()
    P.append(pb())

    # ══════════════════════════════════════════════════════════════════════════
    # CAPÍTULO III. DESARROLLO DEL TRABAJO DE TESIS
    # ══════════════════════════════════════════════════════════════════════════
    P.append(h("CAPÍTULO III. DESARROLLO DEL TRABAJO DE TESIS", 1))

    # ── 3.1 Presentación ─── (con datos reales de la corrida experimental)
    P += C3.seccion_31_presentacion()

    # 3.2 Desarrollo de la propuesta
    P.append(h("3.2 Desarrollo de la propuesta de solución", 2))

    # 3.2.0 — configuración de 17 agentes (datos reales del config JSON)
    P += C3.seccion_32_config_17_agentes()

    P.append(h("3.2.1 Arquitectura CityLearn v3 propuesta", 3))
    P.append(p(
        "La arquitectura CityLearn v3 propuesto se compone de cinco capas: "
        "(1) Entorno base CityLearn v2 con edificios, BESS, PV y EV. "
        "(2) Wrapper Dec-POMDP que define el estado global S, las observaciones locales {oi}, "
        "los espacios de acción {Ai} y la función de recompensa multiobjetivo. "
        "(3) Esquema CTDE con críticos centralizados (acceso a S) y actores descentralizados (acceso a oi). "
        "(4) Backends MADRL intercambiables: HAPPO, MASAC, MATD3, MAAC. "
        "(5) Módulo de optimización de hiperparámetros Optuna."
    ))

    P.append(h("3.2.2 Formulación Dec-POMDP", 3))
    P.append(p(
        "El problema de control energético coordinado en comunidades inteligentes se formula como "
        "un Dec-POMDP con los siguientes componentes:"
    ))
    for comp, desc in [
        ("Estado global S:", "vector que concatena las observaciones de todos los edificios, las "
         "señales de intensidad de carbono horaria, el precio de electricidad horario, el estado "
         "de carga de los BESS y el estado de carga de los EV."),
        ("Observaciones locales oi:", "vector de observación del agente i que incluye la demanda "
         "del edificio i, el estado de carga de su BESS, la generación PV local, la intensidad "
         "de carbono y el precio de electricidad actuales."),
        ("Espacios de acción Ai:", "acciones continuas de despacho del BESS (carga/descarga) y, "
         "si aplica, de la potencia de carga del EV, normalizadas en el intervalo [-1, 1]."),
        ("Función de transición T:", "modelada internamente por CityLearn v2 mediante simulación "
         "física de los modelos de edificio, BESS, PV y EV."),
        ("Función de recompensa multiobjetivo r(t):",
         "r(t) = w1 · r_flex(t) + w2 · r_co2(t) + w3 · r_cost(t), "
         "donde w1, w2, w3 son pesos ajustables (w1+w2+w3=1) sujetos a análisis de sensibilidad "
         "con Optuna. r_flex(t) es negativo-proporcional al pico de demanda; "
         "r_co2(t) es negativo-proporcional al consumo ponderado por intensidad de carbono; "
         "r_cost(t) es negativo-proporcional al costo de electricidad del paso de tiempo t."),
        ("Factor de descuento gamma:", "por definir en la etapa de implementación experimental."),
    ]:
        P.append(p(comp + " " + desc))

    P.append(h("3.2.3 Esquema CTDE", 3))
    P.append(p(
        "Durante el entrenamiento, los críticos de cada backend MADRL acceden al estado global S "
        "para estimar el valor o la función Q centralizada, permitiendo actualizaciones de política "
        "mejor informadas. Durante la ejecución (evaluación), cada agente i actúa únicamente desde "
        "su observación local oi mediante su actor descentralizado, sin comunicación entre agentes "
        f"y sin acceso al estado global {LOWE_2017}. Este esquema garantiza la aplicabilidad práctica de "
        "las políticas en escenarios donde la información completa de todos los edificios no está "
        "disponible en tiempo de operación."
    ))

    P.append(h("3.2.4 Backends MADRL propuestos", 3))
    backends = [
        ("HAPPO", "Heterogeneous-Agent Proximal Policy Optimization",
         f"Extiende PPO al marco multiagente heterogéneo bajo CTDE con garantías de "
         f"monotonicidad en la mejora de políticas. Actualiza las políticas de manera secuencial "
         f"utilizando el estado global en el crítico centralizado {KUBA_2022}."),
        ("MASAC", "Multi-Agent Soft Actor-Critic",
         f"Aplica el principio de máxima entropía de SAC en entornos cooperativos. Favorece "
         f"políticas estocásticas que balancean explotación y exploración, siendo robusto ante "
         f"la no-estacionaridad del entorno multiagente {HAARNOJA_2018}."),
        ("MATD3", "Multi-Agent Twin Delayed Deep Deterministic Policy Gradient",
         f"Extiende TD3 con dos críticos por agente para reducir el sesgo de sobreestimación "
         f"en escenarios cooperativos. Utiliza actualización retardada del actor y ruido de "
         f"política suavizado {FUJIMOTO_2018}."),
        ("MAAC", "Multi-Agent Actor-Critic con atención",
         f"Incorpora un mecanismo de atención multi-cabeza en el crítico centralizado para "
         f"ponderar dinámicamente las contribuciones de cada agente compañero en el estado "
         f"global, mejorando la estimación de valor en comunidades heterogéneas {IQBAL_SHA}."),
    ]
    for sigla, nombre, desc in backends:
        P.append(p(f"{sigla} ({nombre}):", bold=True))
        P.append(p(desc))

    P.append(h("3.2.5 Ajuste de hiperparámetros con Optuna", 3))
    P.append(p(
        "Optuna se utiliza para el ajuste automatizado de hiperparámetros de cada backend. "
        "Los hiperparámetros candidatos incluyen: tasa de aprendizaje del actor, tasa de "
        "aprendizaje del crítico, tamaño del buffer de experiencia (para backends off-policy), "
        "factor de descuento gamma, parámetro de temperatura (MASAC), coeficiente de clip "
        "(HAPPO), dimensión de las capas ocultas de las redes neuronales, y los pesos de "
        "la función de recompensa multiobjetivo w1, w2, w3. El número de trials de Optuna "
        "y el espacio de búsqueda por hiperparámetro se definen en la etapa de implementación "
        "experimental."
    ))

    P.append(h("3.2.6 Datasets de CityLearn v2", 3))
    P.append(p(
        "Los datasets utilizados son los datasets oficiales de CityLearn v2 disponibles en el "
        "repositorio público de CityLearn. Incluyen series temporales horarias de: demanda "
        "energética de edificios residenciales y comerciales, generación PV, capacidad y "
        "estado de carga de BESS, señales de intensidad de carbono, precio de electricidad "
        "(TOU y RTP). La selección de datasets específicos y la definición del escenario de "
        "simulación se realizan en la etapa de implementación experimental."
    ))

    P.append(h("3.2.7 KPIs por eje de evaluación", 3))
    kpis_ejes = [
        ("OE.1 — Flexibilidad energética",
         ["Peak demand reduction", "Ramping reduction", "Load factor improvement",
          "Load shifting", "Self-consumption rate", "Self-sufficiency rate",
          "Grid import reduction", "Renewable utilization rate"]),
        ("OE.2 — Emisiones de CO2",
         ["Total carbon emissions", "CO2 reduction vs. baseline",
          "Carbon-intensity-weighted consumption", "Avoided emissions",
          "Emission-cost trade-off index"]),
        ("OE.3 — Costos energéticos",
         ["Total electricity cost", "Cost reduction vs. baseline",
          "Demand charge reduction", "Time-of-use optimization index",
          "Dynamic pricing response"]),
    ]
    for eje, kpis in kpis_ejes:
        P.append(p(eje + ":", bold=True))
        for k in kpis:
            P.append(bullet(k))

    # ── 3.3 Análisis — datos reales de checkpoints y results.json
    P += C3.seccion_33_resultados()

    # ── 3.4 Discusión — basada en resultados reales
    P += C3.seccion_34_discusion()

    # ── 3.5 Impacto — estimado con valores reales
    P += C3.seccion_35_impacto()
    P.append(pb())

    # ══════════════════════════════════════════════════════════════════════════
    # CAPÍTULO IV. CONCLUSIONES Y RECOMENDACIONES
    # ══════════════════════════════════════════════════════════════════════════
    P.append(h("CAPÍTULO IV. CONCLUSIONES Y RECOMENDACIONES", 1))

    P.append(h("4.1 Conclusiones", 2))
    conclusiones = [
        ("Conclusión general (O.G.):",
         "MAAC es el mejor Multi-Agente de Aprendizaje por Refuerzo Profundo para la gestión "
         "coordinada de flexibilidad energética, emisiones de CO2 y costos energéticos en "
         "comunidades inteligentes, obteniendo 9 KPIs mejorados sobre 26 comparables "
         "(OE.1: 4/12, OE.2: 0/5, OE.3: 5/9) en la evaluación comparativa bajo condiciones "
         "idénticas de Dec-POMDP, CTDE y función de recompensa multiobjetivo sobre los "
         "datos reales de la corrida citylearn_v3_madrl_official_full_cuda_v2."),
        ("Conclusión OE.1 — Flexibilidad energética:",
         "MAAC es el mejor MADRL que optimiza la flexibilidad energética en comunidades "
         "inteligentes, con 4/12 KPIs mejorados en el Escenario E1: peak_average = 1.198 "
         "(mejor valor), ramping_average = 1.906 (mejor valor), zero_net_energy = 3.497 "
         "(único valor positivo = exportación neta de energía) y grid_import ratio = 1.517 "
         "(menor importación de red). El mecanismo de atención multi-cabeza de MAAC permite "
         "una coordinación superior de BESS y V2G (ev_v2g_export_total = 76,785 kWh) "
         "que reduce efectivamente los picos de demanda colectiva."),
        ("Conclusión OE.2 — Emisiones de CO2:",
         "Ningún algoritmo MADRL evaluado logró reducir las emisiones de CO2 en el Escenario E2 "
         "(0/5 KPIs mejorados para todos los algoritmos). El algoritmo con menor empeoramiento "
         "es HAPPO, con carbon_emissions ratio = 1.702 (vs 1.733 de MAAC, 1.806 de MATD3 y "
         "3.781 de MASAC). Este resultado indica que el peso w2 de la recompensa de CO2 en la "
         "configuración actual es insuficiente para inducir políticas carbon-aware consistentes; "
         "la optimización de w2 mediante Optuna y la extensión del entrenamiento son condiciones "
         "necesarias para la mejora de OE.2 en futuras iteraciones."),
        ("Conclusión OE.3 — Costos energéticos:",
         "MAAC es el mejor MADRL que optimiza los costos energéticos en comunidades inteligentes, "
         "con 5/9 KPIs mejorados en el Escenario E3 y el electricity_cost ratio más bajo (-0.002, "
         "único valor negativo = costo neto negativo por ingresos de exportación V2G de 91,737 kWh). "
         "El electricity_cost_delta de MAAC en E3 es -2,485.41, la única reducción real de costos "
         "totales observada. HAPPO es segundo (1/9 KPIs, price_signal_deviation_ratio = 0.965). "
         "MATD3 no mejora ningún KPI de costo (0/9)."),
        ("Conclusión metodológica:",
         "La formulación Dec-POMDP con esquema CTDE, implementada sobre CityLearn v2 mediante "
         "CityLearn v3 propuesto, constituye un marco metodológico riguroso, reproducible y "
         "auditable para la evaluación comparativa de algoritmos MADRL. La corrida experimental "
         "citylearn_v3_madrl_official_full_cuda_v2 generó artefactos verificables (results.json, "
         "timeseries.csv, axis_baseline_comparison.csv, checkpoint_manifest.json) para los "
         "cuatro backends en los tres escenarios, garantizando la trazabilidad completa de "
         "los resultados."),
        ("Conclusión técnica:",
         "CityLearn v3 propuesto provee el primer benchmark experimental que compara HAPPO, MASAC, "
         "MATD3 y MAAC bajo condiciones idénticas de Dec-POMDP/CTDE en los tres ejes de desempeño "
         "(OE.1, OE.2, OE.3). La diferencia en el número de checkpoints entre backends "
         "(HAPPO: 19, MASAC: 3, MATD3: 34, MAAC: 6) indica distintos niveles de convergencia y "
         "señala la necesidad de homologar la extensión del entrenamiento en experimentos futuros."),
        ("Conclusión ambiental:",
         "El resultado negativo en OE.2 (0/5 KPIs de CO2 mejorados para todos los algoritmos) "
         "constituye un hallazgo científico relevante: la coordinación MADRL con recompensa "
         "multiobjetivo en su configuración actual no garantiza reducción de emisiones de CO2 sin "
         "un ajuste explícito de los pesos w2 y una extensión del entrenamiento. La optimización "
         "de hiperparámetros con Optuna orientada a w2 es la recomendación técnica principal "
         "para alcanzar el objetivo de descarbonización en OE.2."),
        ("Conclusión económica:",
         "MAAC alcanza costo neto negativo de electricidad en el Escenario E3 "
         "(electricity_cost_control = -9.32 vs baseline 4,947.92), demostrando que el control "
         "MADRL cooperativo con mecanismo de atención puede transformar una comunidad de edificios "
         "de consumidora neta a exportadora neta, con impacto económico positivo directo. "
         "Este resultado valida la viabilidad técnica del control MADRL para la gestión de "
         "costos en comunidades grid-interactive con alta penetración de V2G."),
    ]
    for etiqueta, texto in conclusiones:
        P.append(p(etiqueta, bold=True))
        P.append(p(texto))

    P.append(h("4.2 Recomendaciones", 2))
    recomendaciones = [
        "Extender la evaluación a datasets de comunidades inteligentes reales más allá de los "
        "disponibles en CityLearn v2, incluyendo datos de contextos latinoamericanos y de "
        "sistemas eléctricos aislados.",
        "Validar los mejores algoritmos MADRL identificados en escenarios de comunidades "
        "inteligentes con restricciones eléctricas de red (voltage, thermal constraints) para "
        "ampliar la aplicabilidad a sistemas con infraestructura de red explícita.",
        "Incorporar tipos adicionales de DER en CityLearn v3 propuesto: micro-CHP, "
        "almacenamiento térmico, V2G, y generación eólica, para extender la evaluación "
        "a escenarios de mayor complejidad.",
        "Explorar enfoques híbridos MADRL-MPC (Model Predictive Control) que combinen la "
        "adaptabilidad del aprendizaje por refuerzo con las garantías de factibilidad del MPC "
        "para escenarios con restricciones operacionales estrictas.",
        "Publicar CityLearn v3 propuesto, los scripts de entrenamiento, los datasets procesados "
        "y los resultados de la evaluación como herramientas open-source para facilitar la "
        "replicabilidad y extensión de la investigación por la comunidad científica.",
        "Llevar a cabo el Módulo A de búsqueda bibliográfica profunda con las 13 cadenas booleanas "
        "definidas en module-a-plan-literature.md para completar la matriz de 50 investigaciones "
        "y todas las citas APA marcadas como pendientes de verificación en este informe.",
    ]
    for rec in recomendaciones:
        P.append(bullet(rec))
    P.append(pb())

    # ══════════════════════════════════════════════════════════════════════════
    # REFERENCIAS
    # ══════════════════════════════════════════════════════════════════════════
    P.append(h("REFERENCIAS", 1))
    P.append(p(
        "Referencias ordenadas alfabéticamente por primer apellido del autor, formato APA 7ª edición. "
        "Los registros de antecedentes nacionales marcados con [RENATI] serán completados "
        "con los datos verificados en RENATI/Cybertesis/repositorios universitarios peruanos."
    ))
    refs = [
        "Akiba, T., Sano, S., Yanase, T., Ohta, T., & Koyama, M. (2019). Optuna: A next-generation "
        "hyperparameter optimization framework. En Proceedings of the 25th ACM SIGKDD International "
        "Conference on Knowledge Discovery & Data Mining (pp. 2623–2631). ACM. "
        "https://doi.org/10.1145/3292500.3330701",

        "Fujimoto, S., van Hoof, H., & Meger, D. (2018). Addressing function approximation error in "
        "actor-critic methods. En Proceedings of the 35th International Conference on Machine Learning "
        "(Vol. 80, pp. 1587–1596). PMLR. https://arxiv.org/abs/1802.09477",

        "Haarnoja, T., Zhou, A., Abbeel, P., & Levine, S. (2018). Soft actor-critic: Off-policy "
        "maximum entropy deep reinforcement learning with a stochastic actor. En Proceedings of the "
        "35th International Conference on Machine Learning (Vol. 80, pp. 1861–1870). PMLR. "
        "https://arxiv.org/abs/1801.01290",

        "Hernandez-Leal, P., Kartal, B., & Taylor, M. E. (2019). A survey and critique of multiagent "
        "deep reinforcement learning. Autonomous Agents and Multi-Agent Systems, 33(6), 750–797. "
        "https://doi.org/10.1007/s10458-019-09421-1",

        "Hu, S., Zhong, Y., Gao, C., Wang, W., Dong, H., Li, Z., Zhang, J., Fan, C., & Yang, Y. "
        "(2023). MARLlib: A scalable multi-agent reinforcement learning library. Journal of Machine "
        "Learning Research, 24(315), 1–23. http://jmlr.org/papers/v24/23-0168.html",

        "Iqbal, S., & Sha, F. (2019). Actor-attention-critic for multi-agent reinforcement learning. "
        "En Proceedings of the 36th International Conference on Machine Learning (Vol. 97, pp. 2961–2970). "
        "PMLR. https://arxiv.org/abs/1810.02912",

        "Kuba, J. G., Chen, R., Wen, M., Wen, Y., Sun, F., Wang, J., & Yang, Y. (2022). "
        "Heterogeneous-agent proximal policy optimisation. arXiv preprint arXiv:2208.01842. "
        "https://arxiv.org/abs/2208.01842",

        "Lillicrap, T. P., Hunt, J. J., Pritzel, A., Heess, N., Erez, T., Tassa, Y., Silver, D., "
        "& Wierstra, D. (2016). Continuous control with deep reinforcement learning. En Proceedings "
        "of the 4th International Conference on Learning Representations (ICLR 2016). "
        "https://arxiv.org/abs/1509.02971",

        "Lowe, R., Wu, Y. I., Tamar, A., Harb, J., Abbeel, P., & Mordatch, I. (2017). Multi-agent "
        "actor-critic for mixed cooperative-competitive environments. En Advances in Neural Information "
        "Processing Systems (Vol. 30). Curran Associates. https://arxiv.org/abs/1706.02275",

        "Mnih, V., Kavukcuoglu, K., Silver, D., Rusu, A. A., Veness, J., Bellemare, M. G., Graves, A., "
        "Riedmiller, M., Fidjeland, A. K., Ostrovski, G., Petersen, S., Beattie, C., Sadik, A., "
        "Antonoglou, I., King, H., Kumaran, D., Wierstra, D., Legg, S., & Hassabis, D. (2015). "
        "Human-level control through deep reinforcement learning. Nature, 518(7540), 529–533. "
        "https://doi.org/10.1038/nature14236",

        "Nweye, K., Sankaranarayanan, S., & Nagy, Z. (2023). Real-world challenges for multi-agent "
        "reinforcement learning in grid-interactive buildings. Energy and AI, 14, 100261. "
        "https://doi.org/10.1016/j.egyai.2023.100261",

        "Oliehoek, F. A., & Amato, C. (2016). A concise introduction to decentralized POMDPs. "
        "Springer. https://doi.org/10.1007/978-3-319-28929-8",

        "Schulman, J., Wolski, F., Dhariwal, P., Radford, A., & Klimov, O. (2017). Proximal policy "
        "optimization algorithms. arXiv preprint arXiv:1707.06347. https://arxiv.org/abs/1707.06347",

        "Sutton, R. S., & Barto, A. G. (2018). Reinforcement learning: An introduction (2nd ed.). "
        "MIT Press. http://incompleteideas.net/book/the-book-2nd.html",

        "Vázquez-Canteli, J. R., & Nagy, Z. (2019). Reinforcement learning for demand response: "
        "A review of algorithms and modeling techniques. Applied Energy, 235, 1072–1089. "
        "https://doi.org/10.1016/j.apenergy.2018.11.002",

        "[Antecedentes nacionales — completar con datos verificados en RENATI/Cybertesis: "
        "NAC-1 ML/DRL demanda Lima, NAC-2 PV+BESS Amazonía, NAC-3 CO2 sistema eléctrico peruano, "
        "NAC-4 DRL edificaciones peruanas, NAC-5 optimización multiagente redes Perú]",
    ]
    for r in refs:
        P.append(p(r))
    P.append(pb())

    # ══════════════════════════════════════════════════════════════════════════
    # ANEXOS
    # ══════════════════════════════════════════════════════════════════════════
    P.append(h("ANEXOS", 1))

    # Anexo 1 — Consistencia (datos reales + población y muestra)
    P.append(h("Anexo 1. Matriz de consistencia", 2))
    P += C3.seccion_matriz_consistencia_real()

    # Anexo 2 — Operacionalización
    P.append(h("Anexo 2. Matriz de operacionalización de variables", 2))
    P.append(p("Variable independiente: Capa MADRL cooperativa (CityLearn v3 propuesto).", bold=True))
    P.append(p("  Dimensión 1: Formulación del problema de decisión — Indicadores: Dec-POMDP, estado global S, observaciones locales {oi}, espacios de acción {Ai}, función de recompensa multiobjetivo."))
    P.append(p("  Dimensión 2: Esquema de entrenamiento — Indicadores: CTDE implementado, backend (HAPPO/MASAC/MATD3/MAAC), hiperparámetros ajustados con Optuna."))
    P.append(p("  Dimensión 3: Cooperación entre agentes — Indicadores: tipo cooperativo, crítico centralizado vs. actor descentralizado, compartición del estado global."))
    P.append(p("Variable dependiente: Desempeño coordinado en comunidades inteligentes.", bold=True))
    P.append(p("  Dimensión 1 (OE.1): Flexibilidad energética — KPIs: peak demand reduction, load factor, self-consumption, self-sufficiency, grid import reduction, load shifting, renewable utilization."))
    P.append(p("  Dimensión 2 (OE.2): Emisiones de CO2 — KPIs: CO2 reduction, carbon-intensity-weighted consumption, avoided emissions, emission-cost trade-off."))
    P.append(p("  Dimensión 3 (OE.3): Costos energéticos — KPIs: electricity cost reduction, demand charge reduction, TOU optimization, dynamic pricing response."))
    P.append(p("Variables de control: dataset climático, perfil de demanda, intensidad de carbono, precio de electricidad, capacidad BESS, penetración PV, escenario EV, restricciones operacionales, hiperparámetros de entrenamiento."))

    # Anexo 3 — Bibliográfica placeholder
    P.append(h("Anexo 3. Matriz bibliográfica de 50 investigaciones (Módulo A)", 2))
    P.append(p(
        "Completar con la ejecución del Módulo A del skill madrl-citylearn-thesis-integrated. "
        "Columnas: N.º, Año, Tipo, Título, Autor(es), Fuente, País, Palabras clave, "
        "Eje (1-Flexibilidad/2-CO2/3-Costos/Transversal), Relación con CityLearn v2, "
        "Relación con MADRL, KPIs reportados, Resultados principales, Cita APA en texto, "
        "Referencia APA completa."
    ))

    # Anexo 4 — KPIs
    P.append(h("Anexo 4. Matriz de KPIs por eje y por algoritmo", 2))
    for eje, kpis in kpis_ejes:
        P.append(p(eje + ":", bold=True))
        for k in kpis:
            P.append(bullet(k))
    P.append(p("O.G. — Ranking integrado:", bold=True))
    P.append(bullet("Composite ranking score integrando KPIs de OE.1, OE.2 y OE.3 para HAPPO, MASAC, MATD3 y MAAC."))

    # Anexo 5 — Arquitectura
    P.append(h("Anexo 5. Arquitectura CityLearn v3 propuesta", 2))
    P.append(p(
        "Véase docs/ARQUITECTURA_CITYLEARN_V3_MADRL.png para el diagrama visual. "
        "Componentes: (1) CityLearn v2 base con edificios, BESS, PV, EV. "
        "(2) Wrapper Dec-POMDP (estado global S, observaciones locales {oi}, acciones {Ai}, "
        "recompensa multiobjetivo). (3) Esquema CTDE (crítico centralizado, actores descentralizados). "
        "(4) Backends HAPPO, MASAC, MATD3, MAAC. (5) Optuna para ajuste de hiperparámetros."
    ))

    # Anexo 6 — Backends
    P.append(h("Anexo 6. Comparación de backends MADRL", 2))
    P.append(p("Algoritmo | Clase | Tipo de política | Característica distintiva"))
    for sigla, nombre, _ in backends:
        props = {
            "HAPPO": "On-policy, actor-crítico | Monotonicidad PPO multiagente heterogéneo",
            "MASAC": "Off-policy, actor-crítico | Máxima entropía, política estocástica",
            "MATD3": "Off-policy, actor-crítico | Doble crítico, reduce sesgo sobreestimación",
            "MAAC": "On-policy, actor-crítico | Mecanismo de atención multi-cabeza",
        }
        P.append(p(f"  {sigla} | {nombre} | {props[sigla]}"))

    # Anexo 9 — Recompensa multiobjetivo
    P.append(h("Anexo 9. Función de recompensa multiobjetivo", 2))
    P.append(p("r(t) = w1 · r_flex(t) + w2 · r_co2(t) + w3 · r_cost(t)"))
    P.append(p("  r_flex(t): señal de flexibilidad energética (OE.1) — reducción de pico y factor de carga."))
    P.append(p("  r_co2(t): señal de emisiones de CO2 (OE.2) — consumo ponderado por intensidad de carbono negativo."))
    P.append(p("  r_cost(t): señal de costos energéticos (OE.3) — costo de electricidad negativo."))
    P.append(p("  w1, w2, w3: pesos (w1+w2+w3=1), sujetos a análisis de sensibilidad con Optuna."))

    # Anexo 10 — Resultados esperados
    P.append(h("Anexo 10. Resultados de simulación — Resultados esperados", 2))
    P.append(p(
        "Los resultados de simulación se presentarán en las Tablas 1–4 del §3.3 una vez "
        "completada la etapa de implementación experimental. Los valores indicados como '" +
        NR + "' en el cuerpo del informe serán reemplazados por los valores reales obtenidos."
    ))

    # Anexo 12 — Glosario
    P.append(h("Anexo 12. Glosario MADRL", 2))
    P += MT.seccion_definicion_terminos()

    return "".join(P)


def save_docx(output: Path, body: str) -> None:
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body>"
        + body
        + '<w:sectPr>'
        '<w:pgSz w:w="12240" w:h="15840"/>'
        '<w:pgMar w:top="1800" w:right="1440" w:bottom="1800" w:left="1800"/>'
        "</w:sectPr>"
        "</w:body></w:document>"
    )
    ct = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml"'
        ' ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        "</Types>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1"'
        ' Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"'
        ' Target="word/document.xml"/>'
        "</Relationships>"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", ct)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("word/document.xml", document_xml)


if __name__ == "__main__":
    body = build()
    save_docx(OUTPUT, body)
    print(f"Generado: {OUTPUT.resolve()}")
