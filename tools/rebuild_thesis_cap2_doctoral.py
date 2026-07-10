from __future__ import annotations

import json
import re
import shutil
from copy import deepcopy
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor


REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "docs" / "Tesis_Doctoral_MADRL_CityLearn_Iquitos_resultados_drive_integrados_ordenado_con_diagramas_estructura_skill_objetivos_operacionalizacion.docx"
OUT = REPO / "docs" / "Tesis_Doctoral_MADRL_CityLearn_Iquitos_resultados_drive_integrados_ordenado_con_diagramas_marco_teorico_doctoral_sustentado.docx"
METRICS = REPO / "outputs" / "_drive_madrl" / "full_data" / "analysis_real_drive" / "thesis_docx_marco_teorico_doctoral_metrics.json"

ACCENT = RGBColor(0x1F, 0x4E, 0x79)
GREY = RGBColor(0x59, 0x59, 0x59)


def text_of(el) -> str:
    return "".join(t.text or "" for t in el.iter(qn("w:t"))).strip()


def clear_body_keep_sectpr(document: Document) -> None:
    body = document.element.body
    sect_pr = None
    for child in list(body):
        if child.tag == qn("w:sectPr"):
            sect_pr = child
        body.remove(child)
    if sect_pr is not None:
        body.append(sect_pr)


def append_before_sectpr(document: Document, el) -> None:
    body = document.element.body
    sect_pr = body.find(qn("w:sectPr"))
    if sect_pr is None:
        body.append(el)
    else:
        body.insert(body.index(sect_pr), el)


def style_doc(document: Document) -> None:
    for name in ["Normal", "Heading 1", "Heading 2", "Heading 3"]:
        if name not in [s.name for s in document.styles]:
            continue
        st = document.styles[name]
        st.font.name = "Calibri"
        if name == "Normal":
            st.font.size = Pt(11)
            st.paragraph_format.space_after = Pt(6)
            st.paragraph_format.line_spacing = 1.15
        else:
            st.font.color.rgb = ACCENT
            st.font.bold = True
            st.font.size = Pt(16 if name == "Heading 1" else 13 if name == "Heading 2" else 11.5)


def set_bg(cell, color: str = "1F4E79") -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color)
    tc_pr.append(shd)


def add_chapter_2(doc: Document) -> None:
    def h(text: str, level: int):
        return doc.add_heading(text, level=level)

    def p(text: str):
        para = doc.add_paragraph()
        para.add_run(text)
        para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        para.paragraph_format.space_after = Pt(6)
        para.paragraph_format.line_spacing = 1.15
        return para

    def eq(text: str):
        para = doc.add_paragraph()
        run = para.add_run(text)
        run.italic = True
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        para.paragraph_format.space_before = Pt(4)
        para.paragraph_format.space_after = Pt(4)
        return para

    def table(caption: str, headers: list[str], rows: list[list[str]], font_size: float = 7.4):
        cap = doc.add_paragraph()
        run = cap.add_run(caption)
        run.bold = True
        run.font.size = Pt(9.5)
        run.font.color.rgb = GREY
        tbl = doc.add_table(rows=1, cols=len(headers))
        tbl.style = "Light Grid Accent 1"
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        for i, head in enumerate(headers):
            cell = tbl.rows[0].cells[i]
            cell.text = ""
            rr = cell.paragraphs[0].add_run(head)
            rr.bold = True
            rr.font.size = Pt(font_size)
            rr.font.color.rgb = RGBColor(255, 255, 255)
            set_bg(cell)
        for row in rows:
            cells = tbl.add_row().cells
            for i, val in enumerate(row):
                cells[i].text = ""
                rr = cells[i].paragraphs[0].add_run(str(val))
                rr.font.size = Pt(font_size)
        doc.add_paragraph()
        return tbl

    h("Capitulo 2. Marco teorico", 1)
    p("El marco teorico de esta tesis no se limita a definir conceptos generales de aprendizaje por refuerzo o energia. Su funcion es sustentar, con literatura especializada, la relacion causal entre la variable independiente -algoritmo MADRL aplicado bajo Dec-POMDP/CTDE- y la variable dependiente -desempeno coordinado de flexibilidad energetica, emisiones de CO2 y costos energeticos-. Por ello, este capitulo se organiza en cuatro ejes: CityLearn y comunidades energeticas, flexibilidad energetica, control bajo intensidad de carbono, optimizacion de costos, y fundamentos formales MADRL. Esta estructura responde directamente a OE.1, OE.2, OE.3 y al objetivo general.")
    p("La literatura revisada confirma que la gestion energetica de edificios ha transitado desde control basado en reglas hacia control por aprendizaje, y desde agentes centralizados hacia coordinacion multiagente. Sin embargo, tambien muestra una brecha: los estudios suelen evaluar un algoritmo, una metrica dominante o un conjunto limitado de edificios, mientras que esta tesis compara HAPPO, MASAC, MATD3 y MAAC bajo el mismo dataset, los mismos escenarios E1/E2/E3, la misma funcion de recompensa y el mismo protocolo de evidencia. Esa brecha teorica justifica el diseno experimental del Capitulo 3 y la contrastacion del Capitulo 5.")

    h("2.1 Antecedentes de la investigacion", 2)
    h("2.1.1 CityLearn como entorno base de simulacion multiobjetivo", 3)
    p("CityLearn constituye la linea de simulacion mas directamente vinculada con esta tesis. Vazquez-Canteli y Nagy (2019a) introdujeron CityLearn v1.0 como entorno compatible con OpenAI Gym para respuesta a la demanda en edificios, mostrando que un agente de aprendizaje profundo podia superar politicas basadas en reglas en reduccion de pico. Posteriormente, Vazquez-Canteli y Nagy (2019b) sistematizaron algoritmos y tecnicas de modelado para respuesta a la demanda con aprendizaje por refuerzo, y Vazquez-Canteli et al. (2020) reforzaron la necesidad de estandarizar entornos, KPIs y comparaciones en gestion energetica urbana.")
    p("La evolucion hacia CityLearn v2 es decisiva porque integra edificios grid-interactive, almacenamiento, PV, vehiculos electricos, senales de carbono y costos. Nweye et al. (2024) presentan CityLearn v2 como entorno para gestion energetica flexible, resiliente, centrada en ocupantes y consciente de carbono; Nweye et al. (2023c) describen su formalizacion como entorno Gym para benchmarking de respuesta a la demanda; y Nweye y Nagy (2024b) amplian el uso de CityLearn Gym a evaluacion multiobjetivo. Esta tesis toma CityLearn v2 como base validada, pero no afirma que CityLearn v3 exista oficialmente: CityLearn v3 propuesto es una extension experimental desarrollada para el Dec-POMDP, CTDE y backends MADRL del proyecto.")
    p("El paso de entornos de un edificio a comunidades heterogeneas demanda tratar problemas de escala, observabilidad parcial y no estacionariedad. Nweye et al. (2022) identifican desafios reales del aprendizaje por refuerzo multiagente en edificios grid-interactive, incluyendo generalizacion, seguridad, heterogeneidad, interaccion con ocupantes y reproducibilidad. Nweye et al. (2023a) proponen MERLIN para aprendizaje offline y transferencia en comunidades de 17 edificios, escala comparable al caso SEAI Iquitos, mientras Nweye et al. (2023b) aplican aprendizaje por refuerzo heterogeneo multiagente en comunidades grid-interactive. Estos antecedentes justifican que la unidad de analisis no sea un edificio aislado, sino una comunidad de 17 agentes.")

    h("2.1.2 Flexibilidad energetica y respuesta a la demanda", 3)
    p("La flexibilidad energetica se entiende como la capacidad de modificar el perfil temporal de demanda, importacion, exportacion, carga de almacenamiento y consumo flexible para aportar servicios al sistema electrico. En comunidades con PV, BESS y EV, la flexibilidad no equivale solamente a reducir demanda pico; incluye reducir rampas, mejorar factor de carga, incrementar autoconsumo y desplazar consumo hacia periodos de mayor disponibilidad renovable. Este concepto se alinea con los KPIs peak_average, ramping_average, one_minus_load_factor_average, autoconsumo y autosuficiencia empleados en CityLearn (Vazquez-Canteli et al., 2020; Nweye et al., 2024).")
    p("Los antecedentes recientes muestran que la flexibilidad requiere coordinacion y no solo optimizacion local. Yao et al. (2023) proponen una estrategia MADRL para gestion energetica de comunidades con PV, BESS y EV, reportando mejoras en pico y costo; Xie et al. (2023) introducen mecanismos de atencion multiagente para respuesta a la demanda en edificios grid-responsive; y Hribar et al. (2025) demuestran mejoras de autonomia energetica en distritos de energia positiva mediante MADRL. En paralelo, Felicetti et al. (2024) combinan programacion entera y aprendizaje por refuerzo para maximizar autoconsumo y recorte de picos, mientras Li et al. (2024) estudian programacion online de PV+BESS con DRL. Estos trabajos sustentan el eje OE.1.")
    p("La tesis se diferencia porque no evalua una politica unica de flexibilidad. Define E1 como escenario dominante de flexibilidad y compara cuatro familias MADRL bajo condiciones identicas. La literatura muestra que la flexibilidad depende de la interaccion entre edificios, almacenamiento y cargas flexibles; por ello, el Capitulo 5 no debe interpretar un KPI aislado como evidencia suficiente. La lectura correcta combina resultados distritales, resultados por edificio, trazas de accion y carga controlada/no controlada.")

    h("2.1.3 Emisiones de carbono y control consciente de intensidad de carbono", 3)
    p("El segundo eje teorico se relaciona con la gestion energetica orientada a carbono. En sistemas donde la intensidad de carbono varia temporalmente, el control puede reducir emisiones desplazando consumo hacia periodos de baja CI o cargando almacenamiento cuando la energia renovable desplaza generacion fosil. Tranberg et al. (2020) discuten metodos de contabilidad de carbono en tiempo real; Cao et al. (2023) estudian pronostico de intensidad de carbono para gestion energetica de edificios; y el Ministerio del Ambiente del Peru (2019) proporciona la referencia de factor de emision usada para contextualizar redes aisladas peruanas.")
    p("En aprendizaje por refuerzo aplicado a energia, Liu et al. (2022) muestran que MADRL puede reducir costos y emisiones en sistemas de edificios con energia renovable. Ye et al. (2025) y Ma et al. (2025) avanzan hacia MARL seguro para operacion baja en carbono en redes activas y microredes heterogeneas. Sarkar et al. (2024) plantea reduccion de huella de carbono mediante desplazamiento temporal de carga, lo que es conceptualmente transferible a la tesis porque E2 tambien depende de desplazar consumo respecto a una senal de CI. Ren et al. (2025) extienden la discusion a mercados P2P de baja emision con decisiones multiagente.")
    p("El caso SEAI Iquitos requiere adaptar este eje a una red aislada diesel+PV. La intensidad CI(t) de la tesis se deriva de un factor base de 0,790 kgCO2/kWh y un desplazamiento asociado a irradiancia, con rango aproximado 0,672-0,790 kgCO2/kWh. Esta construccion se sostiene teoricamente en la necesidad de hacer carbon-aware control, pero se implementa como CarbonIntensityModel en el motor CityLearn v3 propuesto. Asi, la teoria de carbono no queda desconectada del codigo: se transforma en senal de observacion, componente de recompensa y KPI de evaluacion en D-VD.2.")

    h("2.1.4 Costos energeticos, precios dinamicos y respuesta economica", 3)
    p("El tercer eje se refiere a costos energeticos y respuesta a precios. En edificios comerciales, los costos no dependen solo de energia total, sino de horarios de consumo, precios, cargos de demanda y comportamiento frente a picos. Dang et al. (2023) estudian reduccion de cargos por demanda mediante BESS bajo precios en tiempo real; Xiong et al. (2024) analiza estrategias DRL para sistemas con tarifa por uso horario y almacenamiento; y Chen et al. (2024) modelan EV como almacenamiento movil en sistemas energeticos integrados. Estas bases justifican que la tesis incorpore costo energetico como D-VD.3 y no como metrica secundaria.")
    p("La literatura MADRL de costos refuerza la necesidad de coordinacion. Fang et al. (2021) proponen gestion distribuida de energia y estrategia de mercado en microredes mediante MADRL; Gao et al. (2023) desarrolla MASAC mejorado para programacion colaborativa multi-microgrid; Shojaeighadikolaei et al. (2022) plantean gestion energetica distribuida y respuesta a la demanda en smart grids; y Shojaeighadikolaei et al. (2024) comparan enfoques centralizados y descentralizados para control de redes de carga EV. Estos estudios muestran que el costo emerge de decisiones coordinadas de multiples recursos, no de la optimizacion aislada de un edificio.")
    p("La tesis adopta una senal TOU propia del contexto Iquitos y la incorpora en E3. En consecuencia, el marco teorico de costos se vincula con decisiones de carga/descarga BESS, programacion EV, respuesta a precio y reduccion de picos facturables. La inclusion de OSINERGMIN (2024) permite conectar el KPI de pico y costo con reglas regulatorias peruanas, evitando que el analisis economico sea un ejercicio abstracto separado de la realidad institucional.")

    h("2.1.5 Sintesis critica de antecedentes y brecha cientifica", 3)
    p("La revision muestra cinco patrones. Primero, CityLearn proporciona un entorno estandarizado, pero no resuelve por si mismo la comparacion entre HAPPO, MASAC, MATD3 y MAAC. Segundo, los estudios de flexibilidad muestran beneficios de control aprendido, pero frecuentemente se concentran en pico o autoconsumo. Tercero, los estudios de carbono muestran utilidad de senales CI, pero rara vez se integran con costo y flexibilidad en un unico diseno factorial. Cuarto, la literatura de costos evidencia la importancia de precios y BESS, pero no siempre considera emisiones. Quinto, los algoritmos MADRL tienen fundamentos distintos, por lo que comparar solo resultados agregados sin control metodologico puede inducir conclusiones debiles.")
    p("La brecha que sostiene esta tesis es metodologica y experimental: falta una evaluacion comparativa, reproducible y multiobjetivo de HAPPO, MASAC, MATD3 y MAAC en una comunidad inteligente realista de 17 edificios, bajo Dec-POMDP, CTDE, dataset comun, recompensa unificada y resultados trazables por distrito, edificio, escenario, KPIs y checkpoints. Esta brecha justifica la variable independiente, la variable dependiente y la matriz de operacionalizacion.")

    table(
        "Tabla 2.1. Antecedentes usados por eje teorico y relacion con la tesis.",
        ["Eje", "Autores fuente", "Aporte teorico usado", "Limitacion que cubre esta tesis"],
        [
            ["CityLearn y benchmarking", "Vazquez-Canteli & Nagy (2019a, 2019b); Vazquez-Canteli et al. (2020); Nweye et al. (2023c, 2024); Nweye & Nagy (2024b)", "Entorno estandarizado, KPIs, comunidades grid-interactive, carbon-aware control.", "Se extiende a CityLearn v3 propuesto con Dec-POMDP/CTDE y cuatro backends MADRL."],
            ["Escala multiagente realista", "Nweye et al. (2022, 2023a, 2023b)", "Desafios reales, MERLIN y comunidades heterogeneas de 17 edificios.", "Se aplica a SEAI Iquitos con 17 edificios reales y artefactos Drive."],
            ["Flexibilidad energetica", "Yao et al. (2023); Xie et al. (2023); Hribar et al. (2025); Felicetti et al. (2024); Li et al. (2024); Zhao et al. (2024); Wu et al. (2025)", "Peak shaving, ramping, autoconsumo, coordinacion DR, PV+BESS, control seguro.", "E1 compara HAPPO/MASAC/MATD3/MAAC bajo mismo dataset y KPIs."],
            ["Emisiones CO2", "Liu et al. (2022); Ye et al. (2025); Ma et al. (2025); Sarkar et al. (2024); Ren et al. (2025); Tranberg et al. (2020); Cao et al. (2023)", "Control bajo intensidad de carbono, operacion baja en carbono, desplazamiento temporal de carga.", "E2 usa CI de red aislada Iquitos y CarbonIntensityModel."],
            ["Costos energeticos", "Fang et al. (2021); Gao et al. (2023); Shojaeighadikolaei et al. (2022, 2024); Xiong et al. (2024); Chen et al. (2024); Dang et al. (2023)", "Respuesta a precios, costo electrico, microredes, EV, BESS y demanda maxima.", "E3 vincula TOU local, BESS, EV, carga desplazable y costo distrital/edificio."],
            ["Fundamentos MADRL", "Sutton & Barto (2018); Oliehoek & Amato (2016); Lowe et al. (2017); Haarnoja et al. (2018); Iqbal & Sha (2019); Kuba et al. (2021); Zhong et al. (2023); Hu et al. (2023)", "MDP, Dec-POMDP, CTDE, SAC, atencion, HAPPO, MARLlib.", "Se operacionaliza en wrappers reales y tratamientos experimentales."],
            ["Modelado fisico y regulatorio", "Naumann et al. (2021); Rajagopalan et al. (2024); Reniers et al. (2022); Xu et al. (2021); Tamoor et al. (2022); Antonanzas et al. (2021); IEC (2021); MINAM (2019); OSINERGMIN (2024)", "Degradacion BESS, correccion PV tropical, carbono y tarifa.", "Aportes A1-A4 del motor CityLearn v3 propuesto."],
        ],
    )

    h("2.2 Bases teoricas", 2)
    h("2.2.1 Aprendizaje por refuerzo profundo y decision secuencial", 3)
    p("El aprendizaje por refuerzo modela un problema de decision secuencial donde un agente observa un estado, ejecuta una accion, recibe una recompensa y modifica su politica para maximizar retorno acumulado. Sutton y Barto (2018) formalizan este marco mediante procesos de decision de Markov, lo que permite definir estado, accion, transicion, recompensa y factor de descuento. En la tesis, esta base se proyecta a un sistema energetico donde las acciones representan cargar o descargar BESS, regular cargadores EV y desplazar cargas controlables.")
    p("El aprendizaje por refuerzo profundo incorpora aproximadores neuronales para politicas y funciones de valor, permitiendo espacios de estado y accion de alta dimension. Haarnoja et al. (2018) introducen Soft Actor-Critic como algoritmo off-policy de maxima entropia, base conceptual para MASAC y para enfoques donde la exploracion es crucial. Esta propiedad es importante en comunidades energeticas porque los agentes deben descubrir estrategias de coordinacion bajo incertidumbre temporal y recompensas multiobjetivo.")

    h("2.2.2 Sistemas multiagente, no estacionariedad y cooperacion", 3)
    p("En un sistema multiagente, cada politica modifica el entorno efectivo que observan las demas. Esto genera no estacionariedad desde la perspectiva individual: un edificio aprende mientras los demas tambien cambian su comportamiento. La literatura de CTDE responde a esta dificultad permitiendo criticos centralizados durante el entrenamiento y politicas descentralizadas durante la ejecucion (Lowe et al., 2017). En la tesis, cada edificio debe operar con observacion local, pero el aprendizaje puede usar informacion del distrito para internalizar picos, rampas, emisiones y costos agregados.")
    p("La cooperacion se implementa mediante una recompensa mixta que combina recompensa individual y recompensa de equipo. Esto evita dos extremos: politicas totalmente egoistas que reducen el costo de un edificio desplazando problemas al distrito, y politicas totalmente globales que ignoran la heterogeneidad operativa de cada edificio. La formulacion cooperativa se alinea con los desafios descritos por Nweye et al. (2022) y con la necesidad de coordinacion observada en demanda respuesta multiagente (Yao et al., 2023; Xie et al., 2023).")

    h("2.2.3 Dec-POMDP como formalizacion del problema doctoral", 3)
    p(
        "El Decentralized Partially Observable Markov Decision Process (Dec-POMDP) permite "
        "formalizar decision cooperativa con informacion local incompleta. Oliehoek y Amato (2016) "
        "lo definen como una estructura donde N agentes comparten un criterio cooperativo comun, "
        "pero cada uno recibe observaciones parciales del estado global. Esta tesis adopta esa "
        "formulacion porque ningun edificio del SEAI Iquitos observa completamente el estado "
        "interno de los demas durante la ejecucion: cada agente ve su demanda, PV, BESS, EV, "
        "precio, intensidad de carbono y variables locales, pero no accede a temperatura, SOC, "
        "demanda ni perfiles EV de los otros edificios."
    )
    p(
        "El problema doctoral se modela como el Dec-POMDP cooperativo M, definido por la tupla "
        "siguiente (Oliehoek y Amato, 2016; Sutton y Barto, 2018):"
    )
    eq("M = <S, {A_i}_{i=1}^N, T, R, {O_i}_{i=1}^N, Omega, gamma, T_hor>")
    p(
        "donde N = 17 edificios institucionales/comerciales del dataset citylearn_iquitos_2023_2025, "
        "gamma = 0.9999 (factor de descuento para episodios de 8 760 pasos horarios) y "
        "T_hor = 8 760 (un ano simulado). El objetivo cooperativo es maximizar el retorno "
        "esperado J(pi) = E[ sum_{t=0}^{T_hor-1} gamma^t R_t ], donde pi = (pi_1, ..., pi_N) "
        "denota el conjunto de politicas locales. La Tabla 2.2b resume la notacion formal; "
        "la operacionalizacion computacional se desarrolla en el Capitulo 4 sin alterar esta "
        "definicion teorica."
    )
    table(
        "Tabla 2.2b. Notacion formal del Dec-POMDP cooperativo (SEAI Iquitos, N = 17).",
        ["Simbolo", "Definicion teorica", "Valor / rango en esta tesis"],
        [
            ["N", "Numero de agentes cooperativos (edificios)", "17"],
            ["S", "Espacio de estado global", "Concatenacion s = [o_1, ..., o_17]; dim global = 1 856"],
            ["O_i", "Espacio de observacion local del agente i", "Heterogeneo: 57-330 dimensiones segun flota EV"],
            ["A_i", "Espacio de accion local del agente i", "Heterogeneo: 5-44 acciones (BESS, EV, carga desplazable)"],
            ["T", "Funcion de transicion estocastica S x A -> Delta(S)", "Balance energetico, modelo RC, BESS eta_RT = 0.9025, EV estocastico"],
            ["Omega", "Funcion de observacion O_i = Omega_i(s, a)", "Proyeccion parcial del estado global a informacion local"],
            ["R", "Recompensa cooperativa escalar o vector mixto", "CityLearnV3MADRLRewardFunction; agregacion team_mean"],
            ["gamma", "Factor de descuento", "0.9999"],
            ["T_hor", "Horizonte temporal del episodio", "8 760 pasos (1 h/paso)"],
            ["pi_i", "Politica descentralizada del edificio i", "pi_i(a_i | o_i); sin comunicacion inter-edificio"],
        ],
        font_size=7.0,
    )
    p(
        "Estado global y observaciones locales. El estado global S se construye como la "
        "concatenacion de observaciones locales (ctde_state = concatenated_local_observations). "
        "Cada observacion o_i combina variables temporales (mes, hora, day_type), fisica del "
        "edificio (non_shiftable_load, dhw_demand, cooling_demand, solar_generation), estado del "
        "BESS (SOC, potencia nominal, acciones previas), estado de cada cargador EV (SOC_k, hora "
        "de salida_k, SOC requerido_k, llegada estimada_k, estado_k) y senales globales "
        "(carbon_intensity, electricity_pricing, outdoor_dry_bulb_temperature, "
        "diffuse_solar_irradiance, direct_solar_irradiance). La heterogeneidad dimensional "
        "refleja la diversidad operativa del distrito: edificios con flotas EV extensas "
        "(p. ej. B06 con 32 cargadores, B07 con 42) concentran observaciones y acciones de "
        "mayor dimension."
    )
    p(
        "Espacios de accion. Cada accion a_i controla recursos flexibles del edificio i: "
        "potencia de carga/descarga del BESS (electrical_storage), potencia de carga de cada "
        "cargador EV (electric_vehicle_storage_charger_k) y control de carga desplazable "
        "(washing_machine). Las cargas no controlables permanecen como referencia de demanda "
        "base. La transicion T incorpora el balance energetico del distrito, el modelo RC de "
        "temperatura, la dinamica del almacenamiento con eficiencia round-trip 0.9025 y los "
        "perfiles estocasticos de llegada/salida de vehiculos electricos."
    )
    p(
        "Recompensa cooperativa multiobjetivo. La funcion R materializa los tres ejes "
        "doctorales (flexibilidad, CO2, costos) mediante una recompensa escalar por edificio "
        "y paso, con agregacion cooperativa tipo media de equipo. A nivel teorico:"
    )
    eq(
        "reward_i(t) = reward_scale * [ w_flex * flex_i(t) + w_carbon * carbon_i(t) "
        "+ w_cost * cost_i(t) + w_ev * ev_i(t) ]"
    )
    p(
        "El componente flex_i(t) penaliza, a nivel distrital compartido, el pico y la rampa "
        "mediante peak_share(t) = district_import(t) / N y ramp_share(t) = "
        "|district_import(t) - district_import(t-1)| / N, con funciones de suavizado tanh; "
        "carbon_i(t) pondera la importacion por la intensidad de carbono CI(t); cost_i(t) "
        "refleja la tarifa TOU mediante price_norm(t); y ev_i(t) incorpora urgencia de SOC y "
        "salida de vehiculos. Los pesos w_flex, w_carbon y w_cost se condicionan por escenario "
        "experimental (E1/E2/E3) segun la Tabla 3.1 del Capitulo 3."
    )
    eq("team_reward(t) = (1/N) * sum_{i=1}^N reward_i(t)")
    eq("mixed_reward_i(t) = (1 - r) * reward_i(t) + r * team_reward(t),   con r = 0.70")
    p(
        "La mezcla cooperativa con team_reward_ratio r = 0.70 evita politicas puramente "
        "egoistas (que desplazan picos o costos al distrito) y politicas puramente globales "
        "(que ignoran heterogeneidad operativa). Este esquema se alinea con la literatura de "
        "recompensa hibrida en MADRL energetico (Yao et al., 2023; Liu et al., 2022) y con "
        "los desafios de coordinacion identificados por Nweye et al. (2022). Los valores "
        "numericos del perfil unificado comparable v4 (peak_weight = 0.45, ramp_weight = 0.35, "
        "ev_weight = 0.25, reward_scale = 1.00) y la implementacion exacta de cada termino "
        "se documentan en las Secciones 4.2-4.5, evitando duplicar aqui el detalle de codigo."
    )
    p(
        "Condicion de observabilidad parcial estricta. Durante la ejecucion descentralizada, "
        "cada politica pi_i(a_i | o_i) actua solo con o_i; el estado global s solo es accesible "
        "durante el entrenamiento bajo CTDE (Seccion 2.2.4). Esta separacion es coherente con "
        "el paradigma Dec-POMDP: la informacion completa del distrito no esta disponible en "
        "operacion, pero puede usarse para aprender coordinacion. El Capitulo 4 desarrolla "
        "wrappers PettingZoo, espacios de estado/accion y la clase CityLearnV3MADRLRewardFunction "
        "que instancian esta formalizacion sobre CityLearn v2 extendido (CityLearn v3 propuesto)."
    )

    h("2.2.4 CTDE: entrenamiento centralizado y ejecucion descentralizada", 3)
    p("El paradigma Centralized Training, Decentralized Execution separa dos fases: durante el entrenamiento, los criticos o funciones de valor pueden acceder al estado global y a informacion conjunta; durante la ejecucion, las politicas actuan solo con observaciones locales. Lowe et al. (2017) muestran este principio en multi-agent actor-critic, e Iqbal y Sha (2019) lo extienden con mecanismos de atencion para seleccionar interacciones relevantes entre agentes. En la tesis, CTDE permite que los agentes aprendan coordinacion distrital sin requerir comunicacion completa en operacion.")
    p("La validez de CTDE para esta investigacion depende de mantener consistentes los instrumentos de medicion. Si el entrenamiento usa estado global y la ejecucion usa observacion local, los KPIs deben reflejar la ejecucion descentralizada de politicas, no una solucion centralizada ideal. Por ello, trace.csv y timeseries.csv son necesarios para interpretar si el comportamiento aprendido realmente corresponde a acciones por edificio y no solo a resultados agregados.")

    h("2.2.5 Algoritmos MADRL evaluados", 3)
    p("HAPPO se fundamenta en optimizacion de politica con restricciones de region de confianza para agentes heterogeneos. Kuba et al. (2021) desarrollan una formulacion de trust-region policy optimization multiagente, y Zhong et al. (2023) profundizan el aprendizaje por refuerzo de agentes heterogeneos. En la tesis, HAPPO es relevante porque los edificios difieren en area, cargas, PV, BESS y numero de EV. Sin embargo, su uso en resultados debe respetar la cobertura real: se dispone de timeseries y trace, pero no de todos los artefactos de edificio/checkpoint.")
    p("MASAC deriva conceptualmente de Soft Actor-Critic y su regularizacion de entropia (Haarnoja et al., 2018). Gao et al. (2023) muestran la aplicabilidad de un MASAC mejorado en programacion colaborativa multi-microgrid. En la tesis, MASAC representa un enfoque off-policy con exploracion robusta y discretizacion/adaptacion de acciones para el entorno CityLearn v3 propuesto. Su valor teorico esta en contrastar estrategias entropicas frente a politicas deterministicas y de atencion.")
    p("MATD3 se basa en la idea de reducir sobreestimacion mediante criticos dobles, retraso de actualizacion de politica y ruido objetivo en la familia TD3. Aunque la referencia especifica del backend se implementa en el proyecto, su justificacion teorica se relaciona con estabilidad off-policy en espacios continuos de accion. En la tesis, MATD3 se plantea en las hipotesis como candidato de mayor efecto coordinado porque su doble critico puede ser ventajoso en horizontes largos y acciones energeticas continuas.")
    p("MAAC se sustenta en Actor-Attention-Critic. Iqbal y Sha (2019) proponen que el critico utilice atencion para seleccionar los agentes mas relevantes durante la evaluacion de acciones. En comunidades energeticas, esta idea es pertinente porque no todos los edificios interactuan con la misma intensidad en cada hora: un hospital, un mall y una universidad presentan perfiles de carga y EV diferentes. La atencion ofrece una explicacion teorica para coordinacion selectiva entre edificios heterogeneos.")
    p("MARLlib se considera en la tesis solo como nombre propio de una biblioteca de referencia para aprendizaje por refuerzo multiagente, no como sustituto conceptual de MADRL. Hu et al. (2023) muestran su valor como framework escalable; sin embargo, el proyecto utiliza backends concretos en external/ y wrappers propios. Esta precision terminologica evita confundir marco teorico, herramienta y contribucion experimental.")

    table(
        "Tabla 2.2. Fundamento teorico de los algoritmos MADRL evaluados.",
        ["Algoritmo", "Base teorica", "Ventaja esperada", "Riesgo metodologico", "Relacion con VI"],
        [
            ["HAPPO", "Trust-region y agentes heterogeneos (Kuba et al., 2021; Zhong et al., 2023).", "Estabilidad on-policy y tratamiento de heterogeneidad entre edificios.", "Costo de muestreo y cobertura parcial de artefactos finales.", "Nivel D-VI.1 del factor algoritmo."],
            ["MASAC", "SAC y regularizacion de entropia (Haarnoja et al., 2018; Gao et al., 2023).", "Exploracion robusta y aprendizaje off-policy.", "Adaptacion de acciones continuas/discretas y sensibilidad a hiperparametros.", "Nivel D-VI.1 del factor algoritmo."],
            ["MATD3", "Criticos dobles, retardo de politica y control continuo off-policy.", "Reduccion de sobreestimacion y estabilidad en acciones continuas.", "Puede optimizar algunos ejes mejor que otros; requiere lectura por escenario.", "Nivel D-VI.1 e hipotesis direccional HG/HE.2/HE.3."],
            ["MAAC", "Critico con atencion multiagente (Iqbal & Sha, 2019).", "Coordinacion selectiva entre edificios heterogeneos.", "Complejidad computacional y sensibilidad a estructura de interacciones.", "Nivel D-VI.1 del factor algoritmo."],
        ],
    )

    h("2.2.6 Bases teoricas de la flexibilidad energetica", 3)
    p("La flexibilidad energetica es la capacidad de ajustar demanda, generacion distribuida y almacenamiento en respuesta a objetivos operativos. Lund et al. (2017) ubican esta capacidad dentro de los sistemas energeticos inteligentes, mientras CityLearn la operacionaliza con KPIs de pico, rampa y factor de carga (Vazquez-Canteli et al., 2020; Nweye et al., 2024). En el contexto de la tesis, D-VD.1 no se reduce a una metrica; es una dimension compuesta que incluye peak_average, ramping_average, one_minus_load_factor_average, autoconsumo PV, autosuficiencia, importacion/exportacion y respuesta de carga controlable.")
    p("Los recursos que producen flexibilidad en el SEAI Iquitos son BESS, EV, PV y cargas desplazables. La teoria de PV+BESS indica que el almacenamiento permite transferir energia solar a horas de demanda o costo mayor; los estudios de Li et al. (2024) y Felicetti et al. (2024) respaldan esa logica. En la tesis, dicha teoria se materializa con acciones electrical_storage, electric_vehicle_storage_charger_* y washing_machine_*, mientras la carga base no controlada se mantiene como referencia para evaluar el efecto real de la accion.")

    h("2.2.7 Bases teoricas de emisiones de CO2", 3)
    p("Las emisiones de CO2 asociadas al consumo electrico dependen de la energia importada y de la intensidad de carbono de la fuente. Tranberg et al. (2020) plantean la importancia de contabilidad temporal de carbono, y Cao et al. (2023) muestran la utilidad de pronosticar intensidad de carbono para gestion de edificios. En redes aisladas, la intensidad de carbono puede ser mayor y mas sensible a la generacion local. Por eso, el uso de MINAM (2019) como referencia del factor base peruano conecta la tesis con el contexto SEAI Iquitos.")
    p("D-VD.2 se operacionaliza mediante carbon_emissions_total, carbon_emissions_delta y consumo ponderado por intensidad de carbono. A diferencia de estudios donde el carbono es un KPI posterior, en esta tesis E2 modifica directamente la funcion de recompensa, asignando peso dominante al componente carbono. Esto permite contrastar si el algoritmo MADRL produce un efecto diferenciado sobre emisiones y si el efecto corresponde al algoritmo planteado en las hipotesis.")

    h("2.2.8 Bases teoricas de costos energeticos", 3)
    p("Los costos energeticos se explican por consumo, horario, precio, picos y capacidad de respuesta. OSINERGMIN (2024) justifica el uso de maxima demanda y tarifa en el contexto regulatorio peruano; Dang et al. (2023) muestran que BESS puede reducir cargos de demanda bajo precios dinamicos; y Xiong et al. (2024) confirma que DRL puede responder a TOU y almacenamiento. En la tesis, D-VD.3 se mide con electricity_cost_total, electricity_cost_delta y price_signal_deviation, lo que conecta costos con politicas concretas de carga/descarga y desplazamiento.")
    p("La importancia doctoral de este eje es que costo, flexibilidad y carbono pueden entrar en conflicto. Cargar BESS en una hora barata puede no coincidir con la hora de menor carbono; reducir pico puede aumentar emisiones si desplaza consumo a periodos diesel; y optimizar costo puede sacrificar flexibilidad. Por eso, la recompensa multiobjetivo y los escenarios E1/E2/E3 son teoricamente necesarios y no una decision arbitraria de implementacion.")

    h("2.2.9 Aportes fisicos al motor como base teorica de CityLearn v3 propuesto", 3)
    p("El marco teorico tambien debe sustentar los aportes del motor de simulacion. La degradacion BESS con C-rate y temperatura se justifica por literatura de envejecimiento de baterias LiFePO4 y modelado de degradacion (Naumann et al., 2021; Rajagopalan et al., 2024; Reniers et al., 2022; Xu et al., 2021). Esto evita que el entorno trate toda accion de almacenamiento como equivalente, ignorando condiciones termicas propias de Iquitos.")
    p("La correccion PV por temperatura tropical se sustenta en IEC 61215-1:2021, Tamoor et al. (2022) y Antonanzas et al. (2021). En Iquitos, alta temperatura y humedad pueden reducir produccion frente a condiciones STC, por lo que un modelo sin correccion termica sesgaria las politicas MADRL hacia una confianza excesiva en PV de mediodia. Este aporte conecta clima, generacion y decision multiagente.")
    p("El KPI de pico con ventana de facturacion se fundamenta en OSINERGMIN (2024) y en estudios de reduccion de demanda maxima con BESS, como Dang et al. (2023). Finalmente, CarbonIntensityModel se sostiene en MINAM (2019), Tranberg et al. (2020) y Cao et al. (2023), permitiendo que el eje de carbono sea parametrizable y no una constante exogena sin estructura teorica.")

    table(
        "Tabla 2.3. Constructos teoricos, indicadores y fuentes.",
        ["Constructo", "Indicadores en tesis", "Fuentes teoricas principales", "Uso en Cap. 5"],
        [
            ["Flexibilidad energetica", "peak_average, ramping_average, one_minus_load_factor_average, autoconsumo, autosuficiencia.", "Vazquez-Canteli et al. (2020); Nweye et al. (2024); Lund et al. (2017).", "Comparacion E1, figuras A.1-A.2/A.7-A.8 y KPIs edificio."],
            ["Emisiones CO2", "carbon_emissions_total, carbon_emissions_delta, CI-weighted consumption.", "Liu et al. (2022); Tranberg et al. (2020); Cao et al. (2023); MINAM (2019).", "Comparacion E2, figura A.4/A.6 y tablas por edificio."],
            ["Costos energeticos", "electricity_cost_total, electricity_cost_delta, price_signal_deviation.", "Dang et al. (2023); Xiong et al. (2024); OSINERGMIN (2024); Gao et al. (2023).", "Comparacion E3, figura A.3/A.5 y deltas por edificio."],
            ["Coordinacion MADRL", "reward, trace por agente, acciones controladas, checkpoints.", "Lowe et al. (2017); Oliehoek & Amato (2016); Iqbal & Sha (2019); Kuba et al. (2021).", "Interpretacion distrito-edificio y reproducibilidad de politica."],
            ["Fidelidad fisica del simulador", "degradacion BESS, PV tropical, CI dinamica, pico facturable.", "Naumann et al. (2021); Tamoor et al. (2022); IEC (2021); MINAM (2019).", "Justifica CityLearn v3 propuesto y anexos de arquitectura."],
        ],
    )

    h("2.3 Definicion de terminos y delimitaciones conceptuales", 2)
    p("MADRL: aprendizaje por refuerzo profundo multiagente, donde multiples agentes aprenden politicas mediante redes neuronales y senales de recompensa. En esta tesis se usa MADRL para referirse a HAPPO, MASAC, MATD3 y MAAC bajo formulacion cooperativa. No se sustituye por MARL salvo cuando aparece como parte del nombre propio de una referencia, repositorio o biblioteca.")
    p("CityLearn v2: entorno base oficial de simulacion para comunidades energeticas grid-interactive, con KPIs de energia, carbono y costo. CityLearn v3 propuesto: extension experimental de esta tesis, implementada localmente para Dec-POMDP, CTDE, recompensa multiobjetivo, wrappers MADRL y artefactos reproducibles. Esta distincion es obligatoria para no atribuir al paquete oficial una funcionalidad propia del proyecto.")
    p("Tratamiento experimental: combinacion de un nivel D-VI.1 algoritmo y un nivel D-VI.2 escenario. El diseno factorial completo tiene 12 tratamientos. Distrito: agregacion de los 17 edificios para medir efecto comunitario. Edificio: agente individual con observacion local y acciones propias. Equipo controlado: variable de accion sobre BESS, EV o carga desplazable. Carga no controlada: demanda base observada o de referencia que no es actuada directamente por el agente.")
    p("KPI: indicador cuantitativo usado para medir la variable dependiente. Los KPIs no son adornos del resultado; son la operacionalizacion de D-VD.1, D-VD.2 y D-VD.3. Por ello, toda grafica o tabla del Capitulo 5 debe indicar si corresponde a flexibilidad, carbono, costo, distrito, edificio, escenario o reproducibilidad de modelo.")

    h("2.4 Posicion teorica de la tesis", 2)
    p("La posicion teorica adoptada es que una comunidad inteligente con recursos DER heterogeneos debe modelarse como un sistema multiagente parcialmente observable y no como un problema de control centralizado unico. El criterio de calidad no es solo minimizar un KPI, sino producir desempeno coordinado medible en tres dimensiones. Esta posicion combina la teoria Dec-POMDP de Oliehoek y Amato (2016), el paradigma CTDE de Lowe et al. (2017), la estandarizacion de CityLearn de Vazquez-Canteli et al. (2020) y Nweye et al. (2024), y la literatura de gestion energetica multiobjetivo.")
    p("Desde esta posicion, el Capitulo 5 debe interpretar los resultados con tres reglas. Primero, no hay superioridad universal sin declarar escenario, KPI y escala. Segundo, un resultado distrital no reemplaza la evidencia por edificio. Tercero, un algoritmo con artefactos incompletos no debe usarse para comparaciones donde falten archivos. Estas reglas derivan directamente del marco teorico y evitan conclusiones no sustentadas.")


def main() -> None:
    shutil.copyfile(SRC, OUT)
    doc = Document(OUT)
    style_doc(doc)

    children = list(doc.element.body)
    idx_cap2 = idx_cap3 = None
    for i, el in enumerate(children):
        txt = text_of(el)
        if idx_cap2 is None and txt.startswith("Capitulo 2. Marco teorico"):
            idx_cap2 = i
        if idx_cap3 is None and txt.startswith("Capitulo 3. Metodologia"):
            idx_cap3 = i
    if idx_cap2 is None or idx_cap3 is None:
        raise RuntimeError(f"No se ubicaron limites Cap2/Cap3: {idx_cap2}, {idx_cap3}")

    before = [deepcopy(el) for el in children[:idx_cap2]]
    after = [deepcopy(el) for el in children[idx_cap3:] if el.tag != qn("w:sectPr")]

    clear_body_keep_sectpr(doc)
    for el in before:
        append_before_sectpr(doc, el)
    add_chapter_2(doc)
    for el in after:
        append_before_sectpr(doc, el)

    doc.save(OUT)

    v = Document(OUT)
    paras = [p.text.strip() for p in v.paragraphs if p.text.strip()]
    full = "\n".join(paras)
    cap2_start = next(i for i, x in enumerate(paras) if x == "Capitulo 2. Marco teorico")
    cap3_start = next(i for i, x in enumerate(paras) if x == "Capitulo 3. Metodologia")
    cap2_text = "\n".join(paras[cap2_start:cap3_start])
    metrics = {
        "output": str(OUT),
        "size_bytes": OUT.stat().st_size,
        "paragraphs_non_empty": len(paras),
        "word_count_estimated": len(re.findall(r"\b[\wáéíóúÁÉÍÓÚñÑüÜ-]+\b", full, re.UNICODE)),
        "cap2_word_count_estimated": len(re.findall(r"\b[\wáéíóúÁÉÍÓÚñÑüÜ-]+\b", cap2_text, re.UNICODE)),
        "tables": len(v.tables),
        "inline_images": len(v.inline_shapes),
        "cap2_tables_expected": all(x in cap2_text for x in ["Tabla 2.1", "Tabla 2.2", "Tabla 2.2b", "Tabla 2.3"]),
        "cap2_has_dec_pomdp_ctde": "Dec-POMDP" in cap2_text and "CTDE" in cap2_text,
        "cap2_has_dec_pomdp_tuple": "M = <S, {A_i}_{i=1}^N" in cap2_text,
        "cap2_has_reward_equations": "reward_i(t)" in cap2_text and "team_reward(t)" in cap2_text,
        "cap2_has_n17_agents": "N = 17" in cap2_text,
        "cap2_has_citylearn_v3_propuesto": "CityLearn v3 propuesto" in cap2_text,
        "cap2_citation_year_markers": len(re.findall(r"\(\d{4}[a-z]?\)", cap2_text)),
        "wrong_redaccion_blocks": "Redaccion doctoral ampliada" in full,
        "figures_a_1_a_9": all(f"Figura A.{i}" in full for i in range(1, 10)),
        "figures_b_1_a_9": all(f"Figura B.{i}" in full for i in range(1, 10)),
    }
    METRICS.parent.mkdir(parents=True, exist_ok=True)
    METRICS.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
