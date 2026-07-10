"""Structured antecedents for Cap. 2 tables and Cap. 5 discussion contrast.

Sources: docs/tesis_capitulos/Referencias_APA.md, MODULO_A_Matriz_50_investigaciones.csv,
agent-skills/madrl-citylearn-thesis-plan/scripts/build_biblio_matrix.py,
scripts/thesis_references_apa.py. Entries marked [PV] when quantitative data is incomplete.
"""

from __future__ import annotations

from typing import TypedDict


class Antecedent(TypedDict):
    id: str
    scope: str
    cita: str
    titulo: str
    objetivo_general: str
    tipo_metodologia: str
    diseno_investigacion: str
    resultados_cuantitativos: str
    conclusion_general: str
    aporte_tesis: str
    doi: str
    variables_vi_vd: str
    pv: bool


TABLE_INTERNATIONAL = "Tabla 2.4"
TABLE_NATIONAL = "Tabla 2.5"

ANTECEDENTES_INTERNACIONALES: list[Antecedent] = [
    {
        "id": "INT-01",
        "scope": "internacional",
        "cita": "Nweye et al. (2024)",
        "titulo": (
            "CityLearn v2: Energy-flexible, resilient, occupant-centric, and carbon-aware "
            "management of grid-interactive communities"
        ),
        "objetivo_general": (
            "Desarrollar CityLearn v2 integrando EV/V2G, intensidad de carbono dinamica, "
            "BESS, PV y KPIs de flexibilidad, emisiones y costos en comunidades grid-interactive."
        ),
        "tipo_metodologia": "Desarrollo de entorno de simulacion; evaluacion multiobjetivo con SAC, RBC y MPC.",
        "diseno_investigacion": "Aplicada; no experimental; simulacion comparativa en CityLearn v2.",
        "resultados_cuantitativos": (
            "KPIs distritales y por edificio (peak_average, ramping, carbon_emissions, "
            "electricity_cost); magnitudes especificas dependen de configuracion experimental."
        ),
        "conclusion_general": (
            "CityLearn v2 habilita investigacion reproducible en comunidades inteligentes "
            "multidimensionales con flexibilidad, carbono y costo."
        ),
        "aporte_tesis": (
            "Entorno base oficial y KPIs D-VD.1-D-VD.3; justifica extension CityLearn v3 "
            "propuesto con Dec-POMDP/CTDE y cuatro backends MADRL."
        ),
        "doi": "10.1080/19401493.2024.2418813",
        "variables_vi_vd": "CityLearn; D-VD.1 flexibilidad; D-VD.2 CO2; D-VD.3 costos",
        "pv": False,
    },
    {
        "id": "INT-02",
        "scope": "internacional",
        "cita": "Nweye et al. (2023b)",
        "titulo": (
            "Heterogeneous Multi-Agent Reinforcement Learning for Grid-Interactive Communities"
        ),
        "objetivo_general": (
            "Evaluar HARL/HAPPO para gestion energetica heterogenea en comunidades "
            "grid-interactive modeladas en CityLearn."
        ),
        "tipo_metodologia": "MARL heterogeneo on-policy (HAPPO/HARL) bajo CTDE en CityLearn.",
        "diseno_investigacion": "Aplicada; no experimental; simulacion CityLearn con agentes heterogeneos.",
        "resultados_cuantitativos": (
            "HAPPO heterogeneo comparable o superior a MAPPO en KPIs CityLearn "
            "(peak, ramping, emisiones, costo); magnitudes exactas [PV] por configuracion."
        ),
        "conclusion_general": (
            "HAPPO es viable para coordinacion heterogenea en comunidades inteligentes "
            "grid-interactive."
        ),
        "aporte_tesis": (
            "Antecedente directo del backend HAPPO a escala multiedificio; precedente mas "
            "cercano antes de comparar HAPPO, MASAC, MATD3 y MAAC bajo recompensa unificada."
        ),
        "doi": "10.1145/3600100.3626276",
        "variables_vi_vd": "VI HAPPO; CityLearn; D-VD.1 flexibilidad; CTDE; Dec-POMDP",
        "pv": True,
    },
    {
        "id": "INT-03",
        "scope": "internacional",
        "cita": "Yao et al. (2023)",
        "titulo": "Multi-Agent Reinforcement Learning for Smart Community Energy Management",
        "objetivo_general": (
            "Proponer un marco MARL (LSD-MADDPG) para gestion coordinada de energia en "
            "comunidades inteligentes con PV, BESS y EV."
        ),
        "tipo_metodologia": "MARL cooperativo con estrategia local descentralizada (LSD-MADDPG); CTDE.",
        "diseno_investigacion": "Aplicada; no experimental; simulacion de comunidad inteligente sintetica.",
        "resultados_cuantitativos": "Reduccion de costo ~18% y de pico ~15% frente a MADDPG no cooperativo.",
        "conclusion_general": (
            "La estrategia local MARL mejora coordinacion y reduce fallos de escalabilidad "
            "en comunidades con DER."
        ),
        "aporte_tesis": (
            "Referente de flexibilidad y costos (OE.1/OE.3) para contrastar si MATD3/MAAC "
            "superan mejoras reportadas (~15-18%) bajo dataset SEAI Iquitos."
        ),
        "doi": "10.3390/en17205211",
        "variables_vi_vd": "MADRL; D-VD.1 flexibilidad; D-VD.3 costos; PV+BESS+EV",
        "pv": False,
    },
    {
        "id": "INT-04",
        "scope": "internacional",
        "cita": "Liu et al. (2022)",
        "titulo": (
            "Multi-agent deep reinforcement learning for building energy system with renewable energy"
        ),
        "objetivo_general": (
            "Proponer MADRL (MADDPG) para coordinar BESS y PV en edificios con energia renovable "
            "bajo incertidumbre operativa."
        ),
        "tipo_metodologia": "MADDPG cooperativo con critico centralizado; comparacion con control basado en reglas.",
        "diseno_investigacion": "Aplicada; no experimental; simulacion con datos reales de edificios en China.",
        "resultados_cuantitativos": "Reduccion de costo ~20% y de emisiones CO2 ~15% frente a reglas.",
        "conclusion_general": (
            "MADRL cooperativo supera agentes independientes en eficiencia energetica y emisiones."
        ),
        "aporte_tesis": (
            "Antecedente de D-VD.2 y D-VD.3 para contrastar deltas de CO2 y costo de MATD3/MAAC "
            "en escenario E2/E3 del SEAI Iquitos."
        ),
        "doi": "10.1016/j.apenergy.2022.118703",
        "variables_vi_vd": "MADRL; D-VD.2 CO2; D-VD.3 costos; BESS+PV",
        "pv": False,
    },
    {
        "id": "INT-05",
        "scope": "internacional",
        "cita": "Iqbal y Sha (2019)",
        "titulo": "Actor-Attention-Critic for Multi-Agent Reinforcement Learning",
        "objetivo_general": (
            "Introducir mecanismos de atencion en el critico centralizado MARL para coordinacion "
            "selectiva bajo observabilidad parcial."
        ),
        "tipo_metodologia": "Actor-critic multiagente con atencion multi-cabeza; evaluacion en benchmarks MPE y cooperativos.",
        "diseno_investigacion": "Basica-algoritmica; experimental con entornos benchmark MARL.",
        "resultados_cuantitativos": "Mejora de recompensa ~15-30% frente a MADDPG/COMA en tareas cooperativas.",
        "conclusion_general": (
            "La atencion mejora coordinacion selectiva entre agentes heterogeneos bajo CTDE."
        ),
        "aporte_tesis": (
            "Fundamento del backend MAAC; explica por que MAAC puede liderar costos (OE.3) al "
            "ponderar interacciones entre edificios bajo senales TOU."
        ),
        "doi": "proceedings.mlr.press/v97/iqbal19a.html",
        "variables_vi_vd": "VI MAAC; CTDE; Dec-POMDP/POMDP cooperativo",
        "pv": False,
    },
]

ANTECEDENTES_NACIONALES: list[Antecedent] = [
    {
        "id": "NAT-01",
        "scope": "nacional",
        "cita": "Chevarria Moscoso (2024)",
        "titulo": (
            "Analisis de la generacion hidroelectrica en la central hidroelectrica de Machupicchu "
            "aplicando metodos estocasticos y modelo de optimizacion"
        ),
        "objetivo_general": (
            "Optimizar la generacion hidroelectrica de Machupicchu mediante metodos estocasticos "
            "y un modelo de optimizacion bajo incertidumbre hidrologica."
        ),
        "tipo_metodologia": (
            "Modelado estocastico y optimizacion matematica aplicada a generacion renovable peruana."
        ),
        "diseno_investigacion": "Aplicada; tesis doctoral UNI; estudio de caso en generacion hidroelectrica.",
        "resultados_cuantitativos": (
            "[PV] Mejoras de eficiencia operativa y asignacion de generacion respecto a escenarios "
            "base; magnitudes cuantitativas pendientes de extraccion del repositorio UNI."
        ),
        "conclusion_general": (
            "Los metodos estocasticos permiten decisiones mas robustas en generacion renovable "
            "bajo variabilidad hidrologica en el contexto peruano."
        ),
        "aporte_tesis": (
            "Contextualiza optimizacion energetica nacional y variabilidad de recursos renovables "
            "aplicable al balance PV+diesel del SEAI Iquitos."
        ),
        "doi": "http://hdl.handle.net/20.500.14076/28894",
        "variables_vi_vd": "Contexto Peru; generacion renovable; incertidumbre operativa",
        "pv": True,
    },
    {
        "id": "NAT-02",
        "scope": "nacional",
        "cita": "Peñalva Sanchez (2024)",
        "titulo": (
            "Optimizacion de un sistema fotovoltaico hibrido y la prediccion de la demanda energetica "
            "y variables climaticas utilizando la inteligencia artificial"
        ),
        "objetivo_general": (
            "Optimizar un sistema fotovoltaico hibrido e integrar prediccion de demanda y variables "
            "climaticas mediante inteligencia artificial."
        ),
        "tipo_metodologia": (
            "Modelado de sistema PV hibrido; aprendizaje automatico para pronostico de demanda y clima."
        ),
        "diseno_investigacion": "Aplicada; tesis doctoral UNI; estudio de caso con datos locales.",
        "resultados_cuantitativos": (
            "[PV] Reduccion de error de prediccion de demanda y mejora de desempeno del sistema "
            "hibrido; valores numericos pendientes de verificacion en repositorio UNI."
        ),
        "conclusion_general": (
            "La IA mejora la operacion de sistemas PV hibridos al anticipar demanda y condiciones "
            "climaticas en contexto peruano."
        ),
        "aporte_tesis": (
            "Sustenta el uso de datos climaticos y demanda reales (PVGIS/NASA POWER) en el dataset "
            "citylearn_iquitos_2023_2025 y la relevancia de prediccion para control flexible."
        ),
        "doi": "http://hdl.handle.net/20.500.14076/27731",
        "variables_vi_vd": "Contexto Peru/UNI; PV; demanda; clima tropical",
        "pv": True,
    },
    {
        "id": "NAT-03",
        "scope": "nacional",
        "cita": "Rosero Bernal (2024)",
        "titulo": (
            "Modelo de un sistema de administracion de energia autonomo operado desde la nube para "
            "optimizar la gestion de un grupo de microredes"
        ),
        "objetivo_general": (
            "Disenar un sistema autonomo de administracion de energia en la nube para optimizar "
            "la gestion coordinada de un grupo de microredes."
        ),
        "tipo_metodologia": (
            "Arquitectura de gestion energetica distribuida en la nube; optimizacion multi-microred."
        ),
        "diseno_investigacion": "Aplicada; tesis doctoral; estudio de caso en microredes.",
        "resultados_cuantitativos": (
            "[PV] Mejoras de eficiencia energetica y coordinacion inter-microred respecto a "
            "operacion descentralizada sin orquestacion en la nube."
        ),
        "conclusion_general": (
            "La administracion autonoma en la nube mejora la coordinacion operativa de microredes "
            "heterogeneas."
        ),
        "aporte_tesis": (
            "Paralelo latinoamericano de coordinacion multiagente en redes locales; informa la "
            "lectura CTDE del distrito SEAI como comunidad de 17 nodos energeticos."
        ),
        "doi": "[PV]",
        "variables_vi_vd": "Microredes; coordinacion; gestion energetica autonoma",
        "pv": True,
    },
    {
        "id": "NAT-04",
        "scope": "nacional",
        "cita": "MINAM (2019)",
        "titulo": "INFOCARBONO — RAGEI 2019 Energia (factor de emision del sector electrico peruano)",
        "objetivo_general": (
            "Documentar factores de emision de gases de efecto invernadero del sector energetico "
            "peruano para contabilidad de carbono nacional."
        ),
        "tipo_metodologia": "Inventario nacional de emisiones; contabilidad de carbono por sector y tecnologia.",
        "diseno_investigacion": "Descriptiva-documental; fuente regulatoria oficial del Estado peruano.",
        "resultados_cuantitativos": (
            "Factor de emision del sistema diesel aislado: 0,790 kgCO2/kWh (base para SEAI Iquitos); "
            "modulacion solar en tesis: CI(t) en rango 0,672-0,790 kgCO2/kWh."
        ),
        "conclusion_general": (
            "La contabilidad oficial peruana permite parametrizar control consciente de carbono "
            "en redes con alta dependencia de diesel."
        ),
        "aporte_tesis": (
            "Fundamenta CarbonIntensityModel (A4) y el escenario E2 (D-VD.2) con factor MINAM "
            "aplicado al SEAI Iquitos."
        ),
        "doi": "https://infocarbono.minam.gob.pe/",
        "variables_vi_vd": "D-VD.2 CO2; SEAI Iquitos; intensidad de carbono",
        "pv": False,
    },
    {
        "id": "NAT-05",
        "scope": "nacional",
        "cita": "OSINERGMIN (2024)",
        "titulo": (
            "Resolucion de Consejo Directivo N. 0024-2024-OS/CD — Tarifas de distribucion "
            "electrica MT-3/MT-4, Electro Oriente S.A."
        ),
        "objetivo_general": (
            "Establecer tarifas de distribucion electrica y estructura de facturacion por demanda "
            "maxima para usuarios MT-3/MT-4 de Electro Oriente S.A. (Loreto)."
        ),
        "tipo_metodologia": "Marco regulatorio tarifario; analisis de cargos por energia y demanda maxima.",
        "diseno_investigacion": "Normativa aplicada; estudio de caso regulatorio en red de distribucion Loreto.",
        "resultados_cuantitativos": (
            "Estructura TOU y cargo por demanda maxima en ventanas de facturacion (15 min); "
            "tarifas punta/fuera punta usadas en escenario E3 de la tesis."
        ),
        "conclusion_general": (
            "La regulacion peruana vincula costos energeticos a picos facturables, haciendo "
            "necesaria la coordinacion distrital de flexibilidad."
        ),
        "aporte_tesis": (
            "Justifica KPI de pico con ventana OSINERGMIN (A3) y el escenario E3 (D-VD.3 costos) "
            "con senales TOU locales de Iquitos."
        ),
        "doi": "[PV — resolucion OSINERGMIN 0024-2024-OS/CD]",
        "variables_vi_vd": "D-VD.3 costos; D-VD.1 flexibilidad (pico); SEAI Iquitos",
        "pv": True,
    },
]

TABLE_HEADERS = [
    "Campo",
    "Contenido",
]

ROW_FIELDS = [
    ("Titulo", "titulo"),
    ("Objetivo general", "objetivo_general"),
    ("Tipo de metodologia", "tipo_metodologia"),
    ("Diseno de investigacion", "diseno_investigacion"),
    ("Resultados cuantitativos", "resultados_cuantitativos"),
    ("Conclusion general", "conclusion_general"),
    ("Aporte para esta tesis", "aporte_tesis"),
]


def all_antecedents() -> list[Antecedent]:
    return ANTECEDENTES_INTERNACIONALES + ANTECEDENTES_NACIONALES


def antecedent_table_rows(antecedent: Antecedent) -> list[list[str]]:
    rows: list[list[str]] = []
    for label, key in ROW_FIELDS:
        val = antecedent[key]
        if antecedent["pv"] and key == "resultados_cuantitativos" and "[PV]" not in val:
            val = f"[PV] {val}"
        rows.append([label, val])
    return rows


def antecedent_summary_table_rows(antecedents: list[Antecedent]) -> list[list[str]]:
    """Compact rows for Cap. 2 summary tables (one row per antecedent)."""
    out: list[list[str]] = []
    for a in antecedents:
        pv = " [PV]" if a["pv"] else ""
        out.append(
            [
                a["cita"],
                a["titulo"][:120] + ("..." if len(a["titulo"]) > 120 else ""),
                a["variables_vi_vd"],
                a["aporte_tesis"][:180] + ("..." if len(a["aporte_tesis"]) > 180 else ""),
                a["doi"] if a["doi"] else "—",
            ]
        )
    return out


def audit_json_payload() -> dict:
    from datetime import datetime, timezone

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_files": [
            "docs/tesis_capitulos/Referencias_APA.md",
            "outputs/_archive/plan_tesis/MODULO_A_Matriz_50_investigaciones.csv",
            "agent-skills/madrl-citylearn-thesis-plan/scripts/build_biblio_matrix.py",
            "scripts/thesis_references_apa.py",
        ],
        "cap2_tables": {
            "internacionales": TABLE_INTERNATIONAL,
            "nacionales": TABLE_NATIONAL,
        },
        "antecedentes_internacionales": ANTECEDENTES_INTERNACIONALES,
        "antecedentes_nacionales": ANTECEDENTES_NACIONALES,
        "pv_count": sum(1 for a in all_antecedents() if a["pv"]),
        "verified_doi_count": sum(
            1 for a in all_antecedents() if a["doi"] and not a["doi"].startswith("[")
        ),
    }
