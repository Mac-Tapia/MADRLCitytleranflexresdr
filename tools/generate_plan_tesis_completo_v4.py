"""
Genera el Plan de Tesis completo con todo el contenido desarrollado.
Título: MULTI-AGENTE DE APRENDIZAJE POR REFUERZO PROFUNDO PARA LA GESTIÓN
COORDINADA DE FLEXIBILIDAD ENERGÉTICA, EMISIONES DE CARBONO Y COSTOS
ENERGÉTICOS EN COMUNIDADES INTELIGENTES
Guía N. 01 - Sección 5.1
"""

from __future__ import annotations
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

sys.path.insert(0, str(Path(__file__).parent))
import _thesis_marco_teorico as MT

OUTPUT = Path(__file__).parent.parent / "docs" / "PLAN_TESIS_MADRL_V4_COMPLETO.docx"

TITULO = (
    "MULTI-AGENTE DE APRENDIZAJE POR REFUERZO PROFUNDO PARA LA GESTIÓN "
    "COORDINADA DE FLEXIBILIDAD ENERGÉTICA, EMISIONES DE CARBONO Y COSTOS "
    "ENERGÉTICOS EN COMUNIDADES INTELIGENTES"
)

NOTA_CITA = "[cita APA pendiente de verificación en Módulo A]"


def x(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def h(text: str, lvl: int = 1) -> str:
    style = f'<w:pStyle w:val="Heading{lvl}"/>'
    return f"<w:p><w:pPr>{style}</w:pPr><w:r><w:t>{x(text)}</w:t></w:r></w:p>"


def p(text: str, bold: bool = False) -> str:
    b = "<w:b/>" if bold else ""
    return f"<w:p><w:r><w:rPr>{b}</w:rPr><w:t xml:space=\"preserve\">{x(text)}</w:t></w:r></w:p>"


def build_body() -> str:
    parts = []

    # ── CARÁTULA ──────────────────────────────────────────────────────────────
    parts.append(h("CARÁTULA", 1))
    parts.append(p("Universidad Nacional Mayor de San Marcos"))
    parts.append(p("Unidad de Posgrado / Escuela de Posgrado: [pendiente]"))
    parts.append(p(TITULO, bold=True))
    parts.append(p("Modalidad: Plan de Tesis de Maestría de Especialización o Profesionalizante"))
    parts.append(p("Presentado por: [Nombre del graduando]"))
    parts.append(p("Asesor: [Nombre del asesor]"))
    parts.append(p("Lima, Perú — 2026"))

    # ── DATOS GENERALES ───────────────────────────────────────────────────────
    parts.append(h("DATOS GENERALES", 1))
    parts.append(p("1. Título propuesto: " + TITULO))
    parts.append(p("2. Nombre del graduando: [pendiente]"))
    parts.append(p("3. Nombre del asesor: [pendiente]"))
    parts.append(p("4. Área involucrada: Ingeniería Eléctrica / Inteligencia Artificial / Sistemas de Energía"))
    parts.append(p("5. Lugar o institución donde se desarrolla el proyecto: Universidad Nacional Mayor de San Marcos / "
                   "Entorno computacional con CityLearn v2 y CityLearn v3 propuesto"))
    parts.append(p("6. Duración estimada del proyecto: 18 meses (inicio: [mes/año] — fin: [mes/año])"))

    # ══════════════════════════════════════════════════════════════════════════
    # CAPÍTULO I. PLANTEAMIENTO DEL PROBLEMA
    # ══════════════════════════════════════════════════════════════════════════
    parts.append(h("CAPÍTULO I. PLANTEAMIENTO DEL PROBLEMA", 1))

    # 1.1 DIAGNÓSTICO
    parts.append(h("1.1 Diagnóstico", 2))
    parts.append(p(
        "Las comunidades inteligentes (smart communities) representan entornos urbanos y residenciales de alta "
        "complejidad energética que integran múltiples recursos de energía distribuida (DER): generación "
        "fotovoltaica (PV), sistemas de almacenamiento con baterías (BESS) y estaciones de carga para vehículos "
        "eléctricos (EV). La proliferación de estos recursos, combinada con tarifas eléctricas dinámicas y señales "
        "de intensidad de carbono variables en el tiempo, configura un problema de gestión multiobjetivo de alta "
        "dimensionalidad que los métodos de control convencionales no pueden resolver de manera óptima "
        f"{NOTA_CITA}."
    ))
    parts.append(p(
        "Dimensión de flexibilidad energética. La ausencia de un control coordinado de los DER en comunidades "
        "inteligentes limita la capacidad del sistema para modular la demanda, desplazar cargas y aprovechar "
        "la generación renovable disponible. Los métodos de control por reglas y los enfoques de agente único "
        "basados en aprendizaje profundo por refuerzo (DRL) han demostrado incapacidad para generalizar a "
        "carteras heterogéneas de edificios con perfiles de demanda diversos, resultando en relaciones "
        f"pico-promedio (PAR) subóptimas y bajo aprovechamiento de la energía renovable {NOTA_CITA}. "
        "Ningún estudio comparativo ha determinado qué algoritmo de aprendizaje por refuerzo profundo multiagente "
        "(MADRL) alcanza el mejor desempeño de flexibilidad energética en escenarios coordinados de comunidades "
        "inteligentes."
    ))
    parts.append(p(
        "Dimensión de emisiones de CO2. Las comunidades inteligentes operan bajo señales de intensidad de carbono "
        "variables que reflejan la dependencia del suministro eléctrico en fuentes de generación fósil en distintos "
        "periodos del día. La falta de control multiagente coordinado impide el desplazamiento temporal óptimo del "
        "consumo hacia ventanas de baja intensidad de carbono, elevando innecesariamente las emisiones de CO2 "
        f"asociadas al consumo eléctrico {NOTA_CITA}. No existe un benchmark unificado que establezca qué "
        "algoritmo MADRL logra la mayor reducción de emisiones de CO2 en comunidades inteligentes bajo condiciones "
        "dinámicas de intensidad de carbono."
    ))
    parts.append(p(
        "Dimensión de costos energéticos. Las tarifas de uso horario (TOU) y los precios en tiempo real crean "
        "incentivos económicos para la respuesta de demanda coordinada. Sin embargo, las respuestas no coordinadas "
        "a nivel de edificio individual generan resultados colectivos subóptimos, con sobrecostos por demanda "
        f"punta y pérdidas de oportunidad en periodos de precio bajo {NOTA_CITA}. Ninguna evaluación rigurosa "
        "y comparativa ha determinado qué algoritmo MADRL logra la mejor reducción de costos energéticos en "
        "operación coordinada de comunidades inteligentes."
    ))
    parts.append(p(
        "Limitaciones metodológicas del estado del arte. La literatura existente reporta evaluaciones aisladas de "
        "algoritmos individuales sobre dimensiones únicas, sin un marco comparativo unificado que cubra HAPPO, "
        "MASAC, MATD3 y MAAC bajo formulación Dec-POMDP y esquemas de entrenamiento centralizado con ejecución "
        "descentralizada (CTDE). Esta fragmentación metodológica impide la determinación del mejor agente MADRL "
        "para la gestión coordinada y simultánea de flexibilidad energética, emisiones de CO2 y costos "
        f"energéticos en comunidades inteligentes {NOTA_CITA}."
    ))
    parts.append(p(
        "Oportunidad de CityLearn v2 y CityLearn v3 propuesto. CityLearn v2 es un entorno de simulación "
        "open-source validado para la gestión multiagente de energía en comunidades interactivas con la red "
        f"{NOTA_CITA}. Su integración con CityLearn v3 propuesto —extensión experimental de esta tesis que "
        "implementa la capa MADRL cooperativa, la formulación Dec-POMDP, el esquema CTDE y los backends "
        "HAPPO, MASAC, MATD3 y MAAC compatibles con MARLlib— permite la evaluación comparativa rigurosa y "
        "reproducible de los algoritmos MADRL sobre los tres ejes de desempeño."
    ))

    # 1.2 IDENTIFICACIÓN Y DESCRIPCIÓN DEL PROBLEMA
    parts.append(h("1.2 Identificación y descripción del problema de estudio", 2))
    parts.append(p(
        "El problema central de esta investigación es la ausencia de determinación del mejor algoritmo "
        "Multi-Agente de Aprendizaje por Refuerzo Profundo (MADRL) que gestione de manera coordinada la "
        "flexibilidad energética, las emisiones de CO2 y los costos energéticos en comunidades inteligentes. "
        "Los síntomas observables incluyen: alta relación pico-promedio en perfiles de demanda colectiva, "
        "elevado consumo ponderado por intensidad de carbono, costos energéticos subóptimos por falta de "
        "respuesta coordinada a precios dinámicos, y ausencia de un ranking comparativo de algoritmos MADRL "
        "sobre las tres dimensiones de desempeño."
    ))
    parts.append(p(
        "Las causas energéticas identificadas son: recursos DER no coordinados entre edificios, ausencia de "
        "toma de decisiones cooperativa entre agentes, y no aprovechamiento del estado global compartido "
        "disponible en esquemas CTDE. Las causas metodológicas son: falta de un benchmark unificado de HAPPO, "
        "MASAC, MATD3 y MAAC bajo condiciones idénticas de formulación Dec-POMDP y evaluación sobre los "
        "tres ejes de desempeño. Las consecuencias son operacionales (despacho subóptimo), ambientales "
        "(exceso de emisiones de CO2) y económicas (sobrecostos evitables por gestión ineficiente)."
    ))
    parts.append(p(
        "Variable independiente: Capa MADRL cooperativa implementada sobre CityLearn v2 (CityLearn v3 "
        "propuesto), que integra algoritmos HAPPO, MASAC, MATD3 y MAAC bajo formulación Dec-POMDP y esquema "
        "CTDE. Variable dependiente: Desempeño coordinado en flexibilidad energética (OE.1), emisiones de "
        "CO2 (OE.2) y costos energéticos (OE.3) en comunidades inteligentes simuladas. Ámbito espacial: "
        "comunidades inteligentes simuladas mediante los datasets de CityLearn v2 y CityLearn v3 propuesto. "
        "Ámbito temporal: período 2015–2026, alineado con la literatura MADRL reciente y los horizontes "
        "temporales de los datasets de CityLearn v2."
    ))

    # 1.2.1 ANTECEDENTES BIBLIOGRÁFICOS
    parts.append(h("1.2.1 Antecedentes bibliográficos", 3))
    parts += MT.seccion_antecedentes_completos()

    # 1.2.2 FORMULACIÓN DEL PROBLEMA
    parts.append(h("1.2.2 Formulación del problema", 3))

    # 1.2.2.1
    parts.append(h("1.2.2.1 Formulación del problema general", 4))
    parts.append(p(
        "¿Cuál es el mejor Multi-Agente de Aprendizaje por Refuerzo Profundo que gestiona de manera "
        "coordinada la flexibilidad energética, las emisiones de CO2 y los costos energéticos en "
        "comunidades inteligentes?"
    ))

    # 1.2.2.2
    parts.append(h("1.2.2.2 Formulación de los problemas específicos", 4))
    parts.append(p(
        "PE.1: ¿Cuál es el mejor Multi-Agente de Aprendizaje por Refuerzo Profundo que optimiza la "
        "flexibilidad energética en comunidades inteligentes?"
    ))
    parts.append(p(
        "PE.2: ¿Cuál es el mejor Multi-Agente de Aprendizaje por Refuerzo Profundo que reduce las "
        "emisiones de CO2 en comunidades inteligentes?"
    ))
    parts.append(p(
        "PE.3: ¿Cuál es el mejor Multi-Agente de Aprendizaje por Refuerzo Profundo que optimiza los "
        "costos energéticos en comunidades inteligentes?"
    ))

    # 1.2.3 JUSTIFICACIÓN Y ALCANCES
    parts.append(h("1.2.3 Justificación y alcances", 3))

    parts.append(h("1.2.3.1 Justificación", 4))
    parts.append(p(
        "Justificación técnica. La determinación comparativa del mejor algoritmo MADRL para gestión "
        "coordinada de comunidades inteligentes avanza el estado del arte en control cooperativo de "
        f"energía distribuida {NOTA_CITA}. La propuesta de CityLearn v3 propuesto como extensión "
        "experimental de CityLearn v2 constituye una contribución metodológica reproducible."
    ))
    parts.append(p(
        "Justificación ambiental. Identificar el algoritmo MADRL que mejor reduce las emisiones de CO2 "
        "en comunidades inteligentes contribuye directamente a los objetivos de descarbonización de "
        f"sistemas eléctricos y a la reducción del impacto ambiental del consumo energético {NOTA_CITA}."
    ))
    parts.append(p(
        "Justificación económica. Determinar el mejor MADRL para optimización de costos provee orientación "
        "aplicable para la reducción de la factura energética en comunidades residenciales y la explotación "
        f"de señales de precio dinámico {NOTA_CITA}."
    ))
    parts.append(p(
        "Justificación metodológica. El uso de formulación Dec-POMDP, esquema CTDE, entornos CityLearn v2 "
        "y CityLearn v3 propuesto, algoritmos HAPPO/MASAC/MATD3/MAAC, MARLlib como referencia técnica, "
        "y Optuna para ajuste de hiperparámetros constituye un marco metodológico riguroso, reproducible "
        "y auditable para la evaluación comparativa de MADRL en gestión energética."
    ))
    parts.append(p(
        "Justificación científica. La evaluación unificada en tres ejes de desempeño (flexibilidad, CO2, "
        "costos) bajo condiciones experimentales homogéneas cubre un vacío sustantivo en la literatura "
        "comparativa de algoritmos MADRL para gestión energética de comunidades inteligentes."
    ))
    parts.append(p(
        "Justificación social. Comunidades inteligentes con mejor flexibilidad energética, menores "
        "emisiones de carbono y menores costos benefician directamente a sus usuarios residenciales "
        "y contribuyen a la transición energética a escala comunitaria."
    ))

    parts.append(h("1.2.3.2 Alcances", 4))
    parts.append(p(
        "Alcance temático: evaluación comparativa de HAPPO, MASAC, MATD3 y MAAC sobre KPIs de "
        "flexibilidad energética (OE.1), emisiones de CO2 (OE.2) y costos energéticos (OE.3) en "
        "simulación de comunidades inteligentes."
    ))
    parts.append(p(
        "Alcance espacial: comunidades inteligentes simuladas mediante datasets de CityLearn v2 y "
        "CityLearn v3 propuesto. La discusión de aplicabilidad se extiende a sistemas eléctricos "
        "aislados y comunidades grid-interactive."
    ))
    parts.append(p(
        "Alcance temporal: período 2015–2026, alineado con los horizontes temporales de los datasets "
        "de CityLearn v2 y la literatura MADRL reciente."
    ))
    parts.append(p(
        "Alcance metodológico: estudio cuantitativo, comparativo, no experimental, basado en "
        "simulación computacional."
    ))
    parts.append(p(
        "Alcance computacional: Python, PyTorch, CityLearn v2, CityLearn v3 propuesto, MARLlib "
        "(referencia técnica), Optuna, recursos computacionales disponibles."
    ))
    parts.append(p(
        "Límites y supuestos: no se modela una red eléctrica física. Los resultados de simulación "
        "no constituyen validación de despliegue en campo real. CityLearn v3 propuesto es una "
        "extensión experimental de esta tesis y no una versión oficial de CityLearn."
    ))
    parts.append(p(
        "Exclusiones: despliegue en campo real, investigación con sujetos humanos, despacho económico "
        "de unidades de generación física, y análisis de estabilidad de red eléctrica."
    ))

    # ══════════════════════════════════════════════════════════════════════════
    # CAPÍTULO II. OBJETIVOS
    # ══════════════════════════════════════════════════════════════════════════
    parts.append(h("CAPÍTULO II. OBJETIVOS", 1))

    parts.append(h("2.1 Objetivo general", 2))
    parts.append(p(
        "O.G. — Determinar el mejor Multi-Agente de Aprendizaje por Refuerzo Profundo que gestiona "
        "de manera coordinada la flexibilidad energética, las emisiones de CO2 y los costos energéticos "
        "en comunidades inteligentes."
    ))

    parts.append(h("2.2 Objetivos específicos", 2))
    parts.append(p(
        "OE.1 — Determinar el mejor Multi-Agente de Aprendizaje por Refuerzo Profundo que optimiza "
        "la flexibilidad energética en comunidades inteligentes."
    ))
    parts.append(p(
        "OE.2 — Determinar el mejor Multi-Agente de Aprendizaje por Refuerzo Profundo que reduce "
        "las emisiones de CO2 en comunidades inteligentes."
    ))
    parts.append(p(
        "OE.3 — Determinar el mejor Multi-Agente de Aprendizaje por Refuerzo Profundo que optimiza "
        "los costos energéticos en comunidades inteligentes."
    ))
    parts.append(p(
        "Regla de coherencia vertical: cada objetivo específico responde directamente a su problema "
        "específico correspondiente, se operacionaliza mediante su conjunto de KPIs y se evalúa "
        "mediante la comparación de HAPPO, MASAC, MATD3 y MAAC bajo formulación Dec-POMDP y CTDE "
        "en CityLearn v3 propuesto."
    ))

    # ══════════════════════════════════════════════════════════════════════════
    # CAPÍTULO III. MARCO TEÓRICO — contenido profundo desde módulo compartido
    # ══════════════════════════════════════════════════════════════════════════
    parts.append(h("CAPÍTULO III. MARCO TEÓRICO", 1))

    parts.append(h("3.1 Bases teóricas", 2))
    parts.append(p(
        "Las bases teóricas se desarrollan articuladas con la variable independiente "
        "(Capa MADRL cooperativa — CityLearn v3 propuesto) y las tres dimensiones de la "
        "variable dependiente: flexibilidad energética (OE.1), emisiones de CO2 (OE.2) y "
        "costos energéticos (OE.3). Todas las afirmaciones teóricas, conceptuales y "
        "metodológicas se sustentan en fuentes verificables citadas en formato APA vigente. "
        "La triangulación de información utiliza las evidencias del proyecto: "
        "KPIs_y_metricas.md (57 KPIs en 3 ejes), Backends_MADRL.md (4 backends "
        "implementados), Arquitectura_Propuesta.md, Marco_metodologico_MADRL.md, "
        "CityLearn_v3_Propuesto.md y resumen_evidencia_tesis.md."
    ))

    # Eje: Variable independiente
    parts += MT.seccion_variable_independiente()

    # Eje OE.1: Flexibilidad energética
    parts += MT.seccion_oe1_flexibilidad()

    # Eje OE.2: Emisiones de CO2
    parts += MT.seccion_oe2_co2()

    # Eje OE.3: Costos energéticos
    parts += MT.seccion_oe3_costos()

    parts.append(h("3.2 Definición de términos", 2))
    parts += MT.seccion_definicion_terminos()

    # ══════════════════════════════════════════════════════════════════════════
    # CAPÍTULO IV. DISEÑO METODOLÓGICO
    # ══════════════════════════════════════════════════════════════════════════
    parts.append(h("CAPÍTULO IV. DISEÑO METODOLÓGICO", 1))

    parts.append(h("4.1 Tipo y nivel de investigación", 2))
    parts.append(p(
        "La investigación es de enfoque cuantitativo, dado que los resultados se expresan en "
        "indicadores de desempeño numéricos (KPIs) y se someten a análisis estadístico comparativo. "
        "El tipo es aplicado, pues el conocimiento generado se orienta a la resolución de un problema "
        "concreto de gestión energética en comunidades inteligentes. El nivel es descriptivo, "
        "comparativo y propositivo: descriptivo, porque se caracterizan los KPIs de cada algoritmo "
        "MADRL; comparativo, porque se determina el mejor algoritmo por eje y en gestión coordinada; "
        "y propositivo, porque se propone CityLearn v3 propuesto como arquitectura experimental para "
        "la evaluación. El diseño es no experimental, transversal, basado en simulación computacional "
        "y comparación de algoritmos. El método comprende modelamiento computacional, simulación de "
        "entornos energéticos de comunidades inteligentes, comparación de algoritmos MADRL y análisis "
        "de indicadores de desempeño."
    ))

    parts.append(h("4.2 Unidad de análisis", 2))
    parts.append(p(
        "La unidad de análisis es la comunidad inteligente simulada mediante CityLearn v2 y CityLearn "
        "v3 propuesto, compuesta por edificios con BESS, PV y EV, controlados por agentes MADRL "
        "cooperativos (HAPPO, MASAC, MATD3, MAAC) bajo formulación Dec-POMDP y esquema CTDE. "
        "Se observan: las políticas de los agentes y sus recompensas acumuladas. Se simulan: episodios "
        "de entrenamiento y episodios de evaluación. Se miden: los KPIs de flexibilidad energética "
        "(OE.1), emisiones de CO2 (OE.2) y costos energéticos (OE.3). Se comparan: los cuatro "
        "algoritmos MADRL en cada eje y en gestión coordinada (O.G.)."
    ))

    parts.append(h("4.3 Población de estudio", 2))
    parts.append(p(
        "La investigación no involucra sujetos humanos. La población de estudio está constituida por: "
        "escenarios simulados de comunidades inteligentes con múltiples edificios y recursos DER; "
        "series temporales de demanda energética, precio de electricidad e intensidad de carbono "
        "provenientes de los datasets de CityLearn v2; y configuraciones de agentes MADRL bajo los "
        "cuatro backends (HAPPO, MASAC, MATD3, MAAC) con distintos ajustes de hiperparámetros "
        "optimizados mediante Optuna."
    ))

    parts.append(h("4.4 Tamaño de muestra", 2))
    parts.append(p(
        "Número de algoritmos MADRL comparados: 4 (HAPPO, MASAC, MATD3, MAAC) más un baseline de "
        "control por reglas o DRL de agente único. Número de episodios de entrenamiento, pasos de "
        "tiempo y horizonte de evaluación: por definir en la etapa de implementación experimental. "
        "Número de configuraciones de hiperparámetros exploradas por Optuna: por definir en la etapa "
        "de implementación experimental. Número de semillas aleatorias para análisis de robustez: "
        "por definir en la etapa de implementación experimental. Datasets: datasets oficiales de "
        "CityLearn v2 disponibles en el repositorio público de CityLearn."
    ))

    parts.append(h("4.5 Selección de muestra", 2))
    parts.append(p(
        "Se utiliza muestreo no probabilístico, intencional y técnicamente conveniente, justificado "
        "por: la disponibilidad y relevancia de los datasets de CityLearn v2, la pertinencia de los "
        "algoritmos HAPPO, MASAC, MATD3 y MAAC para el problema de gestión cooperativa en comunidades "
        "inteligentes, y la aplicabilidad de los escenarios simulados al problema de gestión coordinada "
        "de flexibilidad energética, emisiones de CO2 y costos energéticos."
    ))

    parts.append(h("4.6 Técnicas de recolección de datos", 2))
    parts.append(p(
        "1) Revisión bibliográfica sistemática y construcción de la matriz de 50 antecedentes (Módulo A), "
        "organizada por Eje 1 (flexibilidad), Eje 2 (CO2), Eje 3 (costos) y Eje transversal (marco MADRL). "
        "2) Análisis de documentación oficial de CityLearn v2, MARLlib, HAPPO, MASAC, MATD3, MAAC y Optuna. "
        "3) Extracción y preprocesamiento de datasets de CityLearn v2. "
        "4) Registro de métricas de entrenamiento MADRL: recompensa acumulada, pérdida del actor, pérdida "
        "del crítico, entropía, velocidad de convergencia. "
        "5) Registro de KPIs de evaluación por eje: flexibilidad energética (OE.1), emisiones de CO2 (OE.2), "
        "costos energéticos (OE.3). "
        "6) Registro de configuraciones de hiperparámetros y resultados de optimización con Optuna."
    ))

    parts.append(h("4.7 Técnicas e instrumentos de análisis y procesamiento de datos", 2))
    parts.append(p(
        "Técnicas: limpieza y normalización de series temporales; análisis descriptivo de KPIs por "
        "algoritmo y por eje; comparación de algoritmos MADRL mediante tablas comparativas de HAPPO, "
        "MASAC, MATD3 y MAAC por KPI en cada eje (OE.1, OE.2, OE.3) y ranking integrado para el O.G.; "
        "análisis de convergencia, estabilidad y robustez del entrenamiento; análisis multiobjetivo y "
        "multicriterio para la determinación del mejor algoritmo; comparación contra baseline. "
        "Visualizaciones: curvas de entrenamiento, gráficas de KPIs por eje, matrices de comparación "
        "y tablas de ranking."
    ))
    parts.append(p(
        "Instrumentos: matriz bibliográfica de 50 investigaciones (Módulo A); matriz de KPIs por eje; "
        "CityLearn v2; CityLearn v3 propuesto (extensión experimental); scripts MADRL en Python/PyTorch; "
        "backends HAPPO, MASAC, MATD3 y MAAC; MARLlib como referencia técnica; Optuna; Gymnasium; "
        "PettingZoo si aplica; datasets de CityLearn v2; hojas de resultados comparativos."
    ))

    parts.append(h("4.8 Etapas de intervención del estudio", 2))
    parts.append(p(
        "Fase preparatoria: "
        "1) Revisión bibliográfica profunda y construcción de la matriz de 50 antecedentes (Módulo A) "
        "organizada por Eje 1 (flexibilidad), Eje 2 (CO2), Eje 3 (costos) y Eje transversal (marco MADRL). "
        "2) Diagnóstico del problema energético en comunidades inteligentes y definición de variables. "
        "3) Selección de datasets de CityLearn v2 y definición de KPIs por eje."
    ))
    parts.append(p(
        "Fase de diseño técnico: "
        "4) Diseño de la arquitectura CityLearn v3 propuesta (extensión experimental sobre CityLearn v2). "
        "5) Formulación Dec-POMDP: estado global, observaciones locales, acciones y función de recompensa "
        "multiobjetivo (flexibilidad + CO2 + costos). "
        "6) Implementación del esquema CTDE. "
        "7) Integración del backend HAPPO. "
        "8) Integración del backend MASAC. "
        "9) Integración del backend MATD3. "
        "10) Integración del backend MAAC. "
        "11) Ajuste de hiperparámetros con Optuna."
    ))
    parts.append(p(
        "Fase de evaluación por eje: "
        "12) Entrenamiento y simulación de los cuatro backends. "
        "13) Evaluación de flexibilidad energética (OE.1): reducción de pico, factor de carga, "
        "auto-consumo, desplazamiento de carga. "
        "14) Evaluación de emisiones de CO2 (OE.2): reducción de emisiones, consumo ponderado por "
        "intensidad de carbono, emisiones evitadas. "
        "15) Evaluación de costos energéticos (OE.3): reducción de costo, optimización de tarifas "
        "horarias, reducción de cargo por demanda."
    ))
    parts.append(p(
        "Fase de determinación y cierre: "
        "16) Comparación de resultados por eje y ranking integrado de los cuatro backends (O.G.). "
        "17) Determinación del mejor MADRL por eje y en gestión coordinada. "
        "18) Discusión de aplicabilidad a comunidades inteligentes y sistemas eléctricos aislados. "
        "19) Redacción final del plan de tesis y preparación de anexos."
    ))

    # ══════════════════════════════════════════════════════════════════════════
    # CAPÍTULO V. ADMINISTRACIÓN DEL PLAN DE TESIS
    # ══════════════════════════════════════════════════════════════════════════
    parts.append(h("CAPÍTULO V. ADMINISTRACIÓN DEL PLAN DE TESIS", 1))

    parts.append(h("5.1 Cronograma", 2))
    parts.append(p(
        "El cronograma se organiza en cuatro fases coherentes con las etapas de intervención del estudio "
        "(§4.8). Las duraciones en meses son indicativas y serán confirmadas al inicio del proyecto."
    ))
    cronograma = [
        ("Fase preparatoria", [
            "Revisión bibliográfica y matriz de 50 antecedentes (Módulo A)",
            "Diagnóstico del problema en comunidades inteligentes",
            "Selección de datasets CityLearn v2 y definición de KPIs por eje",
        ]),
        ("Fase de diseño técnico", [
            "Diseño de la arquitectura CityLearn v3 propuesta",
            "Formulación Dec-POMDP y función de recompensa multiobjetivo",
            "Implementación del esquema CTDE",
            "Integración del backend HAPPO",
            "Integración del backend MASAC",
            "Integración del backend MATD3",
            "Integración del backend MAAC",
            "Ajuste de hiperparámetros con Optuna",
        ]),
        ("Fase de evaluación por eje", [
            "Entrenamiento y simulación de los cuatro backends",
            "Evaluación de KPIs de flexibilidad energética (OE.1)",
            "Evaluación de KPIs de emisiones de CO2 (OE.2)",
            "Evaluación de KPIs de costos energéticos (OE.3)",
        ]),
        ("Fase de determinación y cierre", [
            "Análisis comparativo y determinación del mejor MADRL (O.G.)",
            "Redacción del informe final del plan de tesis",
            "Revisión, corrección y sustentación",
        ]),
    ]
    for fase, actividades in cronograma:
        parts.append(p(fase + ":", bold=True))
        for act in actividades:
            parts.append(p("  • " + act))

    parts.append(h("5.2 Presupuesto", 2))
    presupuesto = [
        ("Equipo informático duradero", "[pendiente de especificación]"),
        ("Software y servicios computacionales", "Python, PyTorch, CityLearn v2, MARLlib, Optuna — costo cero (open-source)"),
        ("Servicios tecnológicos", "[pendiente: recursos cloud/HPC si se requiere]"),
        ("Análisis estadístico/computacional", "[pendiente]"),
        ("Revisión bibliográfica y adquisición de documentos", "[pendiente]"),
        ("Publicación científica", "[pendiente si aplica]"),
        ("Asesoría especializada", "[pendiente si aplica]"),
        ("Materiales de oficina", "[pendiente]"),
        ("Contingencia (10%)", "[pendiente]"),
    ]
    for rubro, valor in presupuesto:
        parts.append(p(f"  {rubro}: {valor}"))

    parts.append(h("5.3 Financiamiento", 2))
    parts.append(p(
        "La investigación se financia con recursos propios del graduando. Las herramientas de software "
        "utilizadas (Python, PyTorch, CityLearn v2, MARLlib, Optuna, Gymnasium) son de código abierto "
        "y tienen costo cero. Los recursos computacionales propios son suficientes para la fase de "
        "diseño técnico; el uso de servicios cloud o HPC se evaluará según los requerimientos de la "
        "fase de entrenamiento y simulación."
    ))

    # ══════════════════════════════════════════════════════════════════════════
    # REFERENCIAS
    # ══════════════════════════════════════════════════════════════════════════
    parts.append(h("REFERENCIAS", 1))
    parts.append(p(
        "Las referencias se generan exclusivamente a partir de la matriz bibliográfica de 50 "
        "investigaciones del Módulo A (Anexo 3). Se listan a continuación las referencias "
        "fundacionales que se verificarán y completarán con los datos del Módulo A:"
    ))
    refs = [
        "[Referencia APA completa — Nweye et al., CityLearn v2 — dato bibliográfico pendiente de verificación en Módulo A]",
        "[Referencia APA completa — Oliehoek & Amato, Dec-POMDP — dato bibliográfico pendiente de verificación en Módulo A]",
        "[Referencia APA completa — Lowe et al., MADDPG/CTDE — dato bibliográfico pendiente de verificación en Módulo A]",
        "[Referencia APA completa — Kuba et al., HAPPO — dato bibliográfico pendiente de verificación en Módulo A]",
        "[Referencia APA completa — MASAC — dato bibliográfico pendiente de verificación en Módulo A]",
        "[Referencia APA completa — MATD3 — dato bibliográfico pendiente de verificación en Módulo A]",
        "[Referencia APA completa — MAAC — dato bibliográfico pendiente de verificación en Módulo A]",
        "[Referencia APA completa — MARLlib — dato bibliográfico pendiente de verificación en Módulo A]",
        "[Referencia APA completa — Akiba et al., Optuna — dato bibliográfico pendiente de verificación en Módulo A]",
        "[Referencia APA completa — Vazquez-Canteli et al. — dato bibliográfico pendiente de verificación en Módulo A]",
        "[Completar con todas las referencias de la Matriz de 50 investigaciones del Módulo A]",
    ]
    for r in refs:
        parts.append(p(r))

    # ══════════════════════════════════════════════════════════════════════════
    # ANEXOS
    # ══════════════════════════════════════════════════════════════════════════
    parts.append(h("ANEXOS", 1))

    # ANEXO 1 — MATRIZ DE CONSISTENCIA
    parts.append(h("Anexo 1. Matriz de consistencia", 2))
    consistencia = [
        ("Problema general", "¿Cuál es el mejor MADRL que gestiona de manera coordinada la flexibilidad energética, las emisiones de CO2 y los costos energéticos en comunidades inteligentes?"),
        ("PE.1", "¿Cuál es el mejor MADRL que optimiza la flexibilidad energética en comunidades inteligentes?"),
        ("PE.2", "¿Cuál es el mejor MADRL que reduce las emisiones de CO2 en comunidades inteligentes?"),
        ("PE.3", "¿Cuál es el mejor MADRL que optimiza los costos energéticos en comunidades inteligentes?"),
        ("O.G.", "Determinar el mejor MADRL que gestiona de manera coordinada la flexibilidad energética, las emisiones de CO2 y los costos energéticos en comunidades inteligentes."),
        ("OE.1", "Determinar el mejor MADRL que optimiza la flexibilidad energética en comunidades inteligentes."),
        ("OE.2", "Determinar el mejor MADRL que reduce las emisiones de CO2 en comunidades inteligentes."),
        ("OE.3", "Determinar el mejor MADRL que optimiza los costos energéticos en comunidades inteligentes."),
        ("Variable independiente", "Capa MADRL cooperativa sobre CityLearn v2 (CityLearn v3 propuesto): HAPPO, MASAC, MATD3, MAAC bajo Dec-POMDP y CTDE."),
        ("Variable dependiente", "Desempeño coordinado en flexibilidad energética (OE.1), emisiones de CO2 (OE.2) y costos energéticos (OE.3) en comunidades inteligentes."),
        ("Metodología", "Cuantitativa, aplicada, comparativa, no experimental, simulación computacional."),
        ("Técnicas", "Simulación, comparación de algoritmos, evaluación de KPIs, análisis multicriterio."),
        ("Instrumentos", "CityLearn v2, CityLearn v3 propuesto, backends MADRL, MARLlib (referencia), Optuna, Python/PyTorch, datasets CityLearn v2."),
        ("Resultados esperados", "Ranking de HAPPO, MASAC, MATD3 y MAAC por eje (OE.1, OE.2, OE.3) y determinación del mejor MADRL en gestión coordinada (O.G.)."),
    ]
    for campo, contenido in consistencia:
        parts.append(p(f"  {campo}: {contenido}"))

    # ANEXO 2 — OPERACIONALIZACIÓN DE VARIABLES
    parts.append(h("Anexo 2. Matriz de operacionalización de variables", 2))
    parts.append(p("Variable independiente: Capa MADRL cooperativa (CityLearn v3 propuesto).", bold=True))
    parts.append(p("  Dimensión: Formulación del problema de decisión."))
    parts.append(p("  Indicadores: tipo de modelo (Dec-POMDP), estado global S, observaciones locales {oi}, espacio de acciones {Ai}, función de recompensa multiobjetivo."))
    parts.append(p("  Dimensión: Esquema de entrenamiento."))
    parts.append(p("  Indicadores: CTDE implementado, backend utilizado (HAPPO/MASAC/MATD3/MAAC), hiperparámetros ajustados con Optuna."))
    parts.append(p("  Dimensión: Cooperación entre agentes."))
    parts.append(p("  Indicadores: tipo de cooperación (totalmente cooperativo), política centralizada vs. descentralizada, compartición del estado global."))
    parts.append(p("Variable dependiente: Desempeño coordinado en comunidades inteligentes.", bold=True))
    parts.append(p("  Dimensión 1 — Flexibilidad energética (OE.1)."))
    parts.append(p("  Indicadores: reducción de pico de demanda, factor de carga, auto-consumo, auto-suficiencia, reducción de importación de red, desplazamiento de carga, utilización de renovables."))
    parts.append(p("  Dimensión 2 — Emisiones de CO2 (OE.2)."))
    parts.append(p("  Indicadores: reducción de emisiones de carbono, consumo ponderado por intensidad de carbono, emisiones evitadas, índice emisiones-costo."))
    parts.append(p("  Dimensión 3 — Costos energéticos (OE.3)."))
    parts.append(p("  Indicadores: reducción de costo de electricidad, optimización TOU, reducción de cargo por demanda, respuesta a precios dinámicos."))
    parts.append(p("Variables de control: dataset climático, perfil de demanda, intensidad de carbono, precio de electricidad, capacidad BESS, penetración PV, escenario EV, restricciones operacionales, hiperparámetros de entrenamiento."))

    # ANEXO 4 — KPIS
    parts.append(h("Anexo 4. Matriz de KPIs por eje y por algoritmo", 2))
    parts.append(p("OE.1 — Flexibilidad energética:", bold=True))
    kpis_flex = [
        "Peak demand reduction (reducción de pico de demanda)",
        "Ramping reduction (reducción de rampas)",
        "Load factor improvement (mejora del factor de carga)",
        "Load shifting (desplazamiento de carga)",
        "Self-consumption rate (tasa de auto-consumo)",
        "Self-sufficiency rate (tasa de auto-suficiencia)",
        "Grid import reduction (reducción de importación de red)",
        "Renewable utilization rate (tasa de utilización de renovables)",
    ]
    for k in kpis_flex:
        parts.append(p(f"  • {k}"))
    parts.append(p("OE.2 — Emisiones de CO2:", bold=True))
    kpis_co2 = [
        "Total carbon emissions (emisiones totales de carbono)",
        "CO2 reduction vs. baseline (reducción de CO2 respecto al baseline)",
        "Carbon-intensity-weighted consumption (consumo ponderado por intensidad de carbono)",
        "Avoided emissions (emisiones evitadas)",
        "Emission-cost trade-off index (índice de equilibrio emisiones-costo)",
    ]
    for k in kpis_co2:
        parts.append(p(f"  • {k}"))
    parts.append(p("OE.3 — Costos energéticos:", bold=True))
    kpis_cost = [
        "Total electricity cost (costo total de electricidad)",
        "Cost reduction vs. baseline (reducción de costo respecto al baseline)",
        "Demand charge reduction (reducción de cargo por demanda)",
        "Time-of-use optimization index (índice de optimización de tarifas horarias)",
        "Dynamic pricing response (respuesta a precios dinámicos)",
    ]
    for k in kpis_cost:
        parts.append(p(f"  • {k}"))
    parts.append(p("O.G. — Gestión coordinada:", bold=True))
    parts.append(p("  • Composite ranking score integrando KPIs de OE.1, OE.2 y OE.3 para HAPPO, MASAC, MATD3 y MAAC."))
    parts.append(p("KPIs de entrenamiento MADRL (transversal):", bold=True))
    kpis_train = [
        "Cumulative reward (recompensa acumulada)",
        "Average episode reward (recompensa promedio por episodio)",
        "Convergence speed (velocidad de convergencia)",
        "Actor loss (pérdida del actor)",
        "Critic loss (pérdida del crítico)",
        "Policy entropy (entropía de la política)",
        "Stability (estabilidad entre semillas)",
        "Sample efficiency (eficiencia de muestras)",
        "Robustness (robustez entre semillas aleatorias)",
    ]
    for k in kpis_train:
        parts.append(p(f"  • {k}"))

    # ANEXO 5
    parts.append(h("Anexo 5. Arquitectura CityLearn v3 propuesta", 2))
    parts.append(p(
        "CityLearn v3 propuesto es la extensión experimental de esta tesis sobre CityLearn v2. "
        "Componentes principales: (1) Entorno base CityLearn v2 con edificios, BESS, PV y EV. "
        "(2) Wrapper Dec-POMDP que define el estado global S (observaciones de todos los edificios + "
        "señales de precio e intensidad de carbono), las observaciones locales oi por agente, los "
        "espacios de acción Ai, y la función de recompensa multiobjetivo (ponderación de flexibilidad + CO2 + costos). "
        "(3) Esquema CTDE: críticos centralizados que acceden a S durante entrenamiento, actores "
        "descentralizados que actúan desde oi en ejecución. "
        "(4) Backends intercambiables: HAPPO, MASAC, MATD3, MAAC. "
        "(5) Ajuste de hiperparámetros con Optuna. "
        "Véase docs/ARQUITECTURA_CITYLEARN_V3_MADRL.png para diagrama visual."
    ))

    # ANEXO 6
    parts.append(h("Anexo 6. Comparación de backends MADRL", 2))
    algoritmos = [
        ("HAPPO", "Actor-crítico, off-policy/on-policy", "CTDE", "Cooperativo", "Garantías de monotonicidad PPO multiagente heterogéneo"),
        ("MASAC", "Actor-crítico, off-policy", "CTDE", "Cooperativo", "Máxima entropía, exploración estocástica"),
        ("MATD3", "Actor-crítico, off-policy", "CTDE", "Cooperativo", "Múltiples críticos, reduce sesgo de sobreestimación"),
        ("MAAC", "Actor-crítico, on-policy", "CTDE", "Cooperativo", "Mecanismo de atención para ponderación de agentes"),
    ]
    parts.append(p("Algoritmo | Clase | Entrenamiento | Tipo | Característica distintiva"))
    for alg in algoritmos:
        parts.append(p(" | ".join(alg)))

    # ANEXO 9 — FUNCIÓN DE RECOMPENSA
    parts.append(h("Anexo 9. Función de recompensa multiobjetivo", 2))
    parts.append(p(
        "La función de recompensa multiobjetivo de CityLearn v3 propuesto pondera las tres dimensiones "
        "de desempeño alineadas con los objetivos específicos:"
    ))
    parts.append(p("  r(t) = w1 · r_flex(t) + w2 · r_co2(t) + w3 · r_cost(t)"))
    parts.append(p("Donde:"))
    parts.append(p("  r_flex(t): señal de recompensa de flexibilidad energética (OE.1) — basada en reducción de pico y factor de carga."))
    parts.append(p("  r_co2(t): señal de recompensa de emisiones de CO2 (OE.2) — basada en consumo ponderado por intensidad de carbono negativo."))
    parts.append(p("  r_cost(t): señal de recompensa de costos energéticos (OE.3) — basada en costo de electricidad negativo."))
    parts.append(p("  w1, w2, w3: pesos de ponderación ajustables (w1 + w2 + w3 = 1), sujetos a análisis de sensibilidad con Optuna."))

    # ANEXO 12 — GLOSARIO
    parts.append(h("Anexo 12. Glosario MADRL", 2))
    parts += MT.seccion_definicion_terminos()

    # ANEXO 3 placeholder
    parts.append(h("Anexo 3. Matriz bibliográfica de 50 investigaciones", 2))
    parts.append(p(
        "La matriz de 50 investigaciones se genera mediante el Módulo A del skill "
        "madrl-citylearn-thesis-plan. Incluye columnas: N.º, Año, Tipo, Título, Autor(es), "
        "Fuente, País, Palabras clave, Relación con CityLearn v2, Relación con MADRL, "
        "Eje (1-Flexibilidad / 2-CO2 / 3-Costos / Transversal), KPIs reportados, "
        "Resultados principales, Cita APA en texto, Referencia APA completa. "
        "Completar con la ejecución del Módulo A."
    ))

    # ANEXO 7
    parts.append(h("Anexo 7. Datasets y fuentes", 2))
    parts.append(p(
        "Datasets principales: datasets oficiales de CityLearn v2 disponibles en el repositorio "
        "público de CityLearn (GitHub). Incluyen: series temporales horarias de demanda energética "
        "de edificios residenciales y comerciales, generación PV, capacidad BESS, señales de "
        "intensidad de carbono, precio de electricidad (TOU y RTP). "
        "Fuentes secundarias: NREL, OpenEI, Pecan Street, UK-DALE, REDD, Open Power System Data — "
        "verificar disponibilidad y compatibilidad con CityLearn v2 en el Módulo A."
    ))

    # ANEXO 8
    parts.append(h("Anexo 8. Configuración preliminar de hiperparámetros", 2))
    parts.append(p(
        "La configuración preliminar de hiperparámetros para cada backend (HAPPO, MASAC, MATD3, MAAC) "
        "se define por definir en la etapa de implementación experimental. Se ajustará con Optuna "
        "mediante búsqueda bayesiana sobre: tasa de aprendizaje del actor, tasa de aprendizaje del "
        "crítico, tamaño del buffer de experiencia (off-policy), factor de descuento gamma, "
        "parámetro de temperatura (MASAC), coeficiente de clip (HAPPO), dimensión de capas ocultas, "
        "y pesos de la función de recompensa multiobjetivo (w1, w2, w3)."
    ))

    # ANEXO 10
    parts.append(h("Anexo 10. Cadenas de búsqueda", 2))
    parts.append(p(
        "Las cadenas de búsqueda del Módulo A se organizan en 13 cadenas booleanas sobre Google Scholar, "
        "IEEE Xplore, ScienceDirect, SpringerLink, MDPI, ACM, arXiv, OpenReview, PMLR, y repositorios "
        "universitarios (RENATI, Cybertesis, ProQuest). Véase module-a-plan-literature.md para el "
        "listado completo de cadenas."
    ))

    # ANEXO 11
    parts.append(h("Anexo 11. Evidencias de GitHub", 2))
    parts.append(p(
        "Repositorios de referencia verificados en el Módulo A: "
        "CityLearn (repositorio oficial de CityLearn v2), "
        "MARLlib (implementaciones de HAPPO, MASAC, MATD3, MAAC), "
        "Optuna (marco de optimización de hiperparámetros). "
        "URLs y commits de referencia: pendiente de verificación en Módulo A."
    ))

    return "".join(parts)


def _xml_escape(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def minimal_docx(output: Path, body: str) -> None:
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
    content_types = (
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
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("word/document.xml", document_xml)


if __name__ == "__main__":
    body = build_body()
    minimal_docx(OUTPUT, body)
    print(f"Generado: {OUTPUT.resolve()}")
