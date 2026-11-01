from __future__ import annotations

from pathlib import Path
import re
from typing import Iterable

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_ROW_HEIGHT_RULE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(r"D:\MADRLCitytleranflexresdr")
SOURCE = ROOT / "docs" / "Inforne_tesisV4_FINAL_REVISADO_50_EPISODIOS.docx"
OUTPUT = ROOT / "docs" / "Informe_tesis_MADRL_auditoria_IV_V_VI_VII_final.docx"


TITLE = (
    "COORDINACIÓN ENERGÉTICA MULTIOBJETIVO MEDIANTE APRENDIZAJE POR "
    "REFUERZO PROFUNDO MULTIAGENTE EN UNA COMUNIDAD INTELIGENTE "
    "HETEROGÉNEA DE IQUITOS: EFECTOS Y DESEMPEÑO ALGORÍTMICO, 2026"
)

PG = (
    "PG. ¿En qué medida los algoritmos HAPPO, MASAC, MATD3 y MAAC producen "
    "efectos diferenciales en la coordinación energética multiobjetivo de una comunidad "
    "inteligente heterogénea de Iquitos, considerando la flexibilidad energética, "
    "las emisiones de CO₂ y los costos energéticos, y cuál presenta el mejor "
    "desempeño global?"
)
PE1 = (
    "PE.1. ¿En qué medida los algoritmos HAPPO, MASAC, MATD3 y MAAC producen "
    "efectos diferenciales sobre la flexibilidad energética (eje E1) y cuál presenta "
    "el mejor desempeño en la comunidad inteligente heterogénea de Iquitos?"
)
PE2 = (
    "PE.2. ¿En qué medida los algoritmos HAPPO, MASAC, MATD3 y MAAC producen "
    "efectos diferenciales sobre las emisiones de CO₂ (eje E2) y cuál presenta "
    "el mejor desempeño en la comunidad inteligente heterogénea de Iquitos?"
)
PE3 = (
    "PE.3. ¿En qué medida los algoritmos HAPPO, MASAC, MATD3 y MAAC producen "
    "efectos diferenciales sobre los costos energéticos (eje E3) y cuál presenta "
    "el mejor desempeño en la comunidad inteligente heterogénea de Iquitos?"
)

OG = (
    "OG. Determinar y cuantificar los efectos diferenciales de los algoritmos "
    "HAPPO, MASAC, MATD3 y MAAC en la coordinación energética multiobjetivo "
    "de una comunidad inteligente heterogénea de Iquitos, considerando la "
    "flexibilidad energética, las emisiones de CO₂ y los costos energéticos, "
    "e identificar el algoritmo de mejor desempeño global."
)
OE1 = (
    "OE.1. Determinar y cuantificar los efectos diferenciales de los algoritmos "
    "HAPPO, MASAC, MATD3 y MAAC sobre la flexibilidad energética (eje E1) "
    "e identificar el algoritmo de mejor desempeño en la comunidad inteligente "
    "heterogénea de Iquitos."
)
OE2 = (
    "OE.2. Determinar y cuantificar los efectos diferenciales de los algoritmos "
    "HAPPO, MASAC, MATD3 y MAAC sobre las emisiones de CO₂ (eje E2) "
    "e identificar el algoritmo de mejor desempeño en la comunidad inteligente "
    "heterogénea de Iquitos."
)
OE3 = (
    "OE.3. Determinar y cuantificar los efectos diferenciales de los algoritmos "
    "HAPPO, MASAC, MATD3 y MAAC sobre los costos energéticos (eje E3) "
    "e identificar el algoritmo de mejor desempeño en la comunidad inteligente "
    "heterogénea de Iquitos."
)

HG0 = (
    "HG0. Los algoritmos HAPPO, MASAC, MATD3 y MAAC no producen efectos "
    "diferenciales estadísticamente significativos en la coordinación energética "
    "multiobjetivo de la comunidad inteligente heterogénea de Iquitos, "
    "considerando conjuntamente la flexibilidad energética, las emisiones de CO₂ "
    "y los costos energéticos."
)
HG1 = (
    "HG1. Al menos uno de los algoritmos HAPPO, MASAC, MATD3 y MAAC produce "
    "un efecto diferencial estadísticamente significativo en la coordinación "
    "energética multiobjetivo de la comunidad inteligente heterogénea de Iquitos, "
    "considerando conjuntamente la flexibilidad energética, las emisiones de CO₂ "
    "y los costos energéticos."
)
HE10 = (
    "HE10. Los algoritmos HAPPO, MASAC, MATD3 y MAAC no producen efectos "
    "diferenciales estadísticamente significativos sobre la flexibilidad energética "
    "(eje E1) de la comunidad inteligente heterogénea de Iquitos."
)
HE11 = (
    "HE11. Al menos uno de los algoritmos HAPPO, MASAC, MATD3 y MAAC produce "
    "un efecto diferencial estadísticamente significativo sobre la flexibilidad "
    "energética (eje E1) de la comunidad inteligente heterogénea de Iquitos."
)
HE20 = (
    "HE20. Los algoritmos HAPPO, MASAC, MATD3 y MAAC no producen efectos "
    "diferenciales estadísticamente significativos sobre las emisiones de CO₂ "
    "(eje E2) de la comunidad inteligente heterogénea de Iquitos."
)
HE21 = (
    "HE21. Al menos uno de los algoritmos HAPPO, MASAC, MATD3 y MAAC produce "
    "un efecto diferencial estadísticamente significativo sobre las emisiones "
    "de CO₂ (eje E2) de la comunidad inteligente heterogénea de Iquitos."
)
HE30 = (
    "HE30. Los algoritmos HAPPO, MASAC, MATD3 y MAAC no producen efectos "
    "diferenciales estadísticamente significativos sobre los costos energéticos "
    "(eje E3) de la comunidad inteligente heterogénea de Iquitos."
)
HE31 = (
    "HE31. Al menos uno de los algoritmos HAPPO, MASAC, MATD3 y MAAC produce "
    "un efecto diferencial estadísticamente significativo sobre los costos "
    "energéticos (eje E3) de la comunidad inteligente heterogénea de Iquitos."
)


def set_text(paragraph, text: str, style: str | None = None) -> None:
    paragraph.text = text
    if style:
        paragraph.style = style
    paragraph.paragraph_format.space_after = Pt(6)
    paragraph.paragraph_format.line_spacing = 1.5
    for run in paragraph.runs:
        run.font.name = "Arial"
        run.font.size = Pt(11)


def find_paragraph(doc: Document, starts: str):
    for paragraph in doc.paragraphs:
        if paragraph.text.strip().startswith(starts):
            return paragraph
    raise ValueError(f"Paragraph not found: {starts}")


def replace_between(doc: Document, start_prefix: str, end_prefix: str, texts: Iterable[str]) -> None:
    paragraphs = doc.paragraphs
    start = next(i for i, p in enumerate(paragraphs) if p.text.strip().startswith(start_prefix))
    end = next(i for i, p in enumerate(paragraphs[start + 1 :], start + 1) if p.text.strip().startswith(end_prefix))
    body = paragraphs[start + 1 : end]
    texts = list(texts)
    for i, paragraph in enumerate(body):
        if i < len(texts):
            set_text(paragraph, texts[i], "Body Text First Indent")
        else:
            paragraph.text = ""
    end_paragraph = paragraphs[end]
    for text in texts[len(body) :]:
        paragraph = end_paragraph.insert_paragraph_before(text)
        paragraph.style = "Body Text First Indent"
        paragraph.paragraph_format.space_after = Pt(6)
        paragraph.paragraph_format.line_spacing = 1.5
        for run in paragraph.runs:
            run.font.name = "Arial"
            run.font.size = Pt(11)


def clean_cell(cell) -> None:
    for paragraph in cell.paragraphs:
        paragraph.text = paragraph.text.replace("**", "").replace("`", "")
        paragraph.paragraph_format.space_after = Pt(0)
        paragraph.paragraph_format.line_spacing = 1.0
        for run in paragraph.runs:
            run.font.name = "Arial"
            run.font.size = Pt(8)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=40, start=45, bottom=40, end=45) -> None:
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for tag, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{tag}"))
        if node is None:
            node = OxmlElement(f"w:{tag}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_repeat_table_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


doc = Document(SOURCE)

# Marco rector definitivo.
set_text(doc.paragraphs[4], TITLE, "Body Text First Indent")
set_text(doc.paragraphs[74], PG, "Body Text First Indent")
set_text(doc.paragraphs[76], PE1, "Body Text First Indent")
set_text(doc.paragraphs[77], PE2, "Body Text First Indent")
set_text(doc.paragraphs[78], PE3, "Body Text First Indent")
set_text(doc.paragraphs[140], OG, "Body Text First Indent")
set_text(doc.paragraphs[142], OE1, "Body Text First Indent")
set_text(doc.paragraphs[143], OE2, "Body Text First Indent")
set_text(doc.paragraphs[144], OE3, "Body Text First Indent")
set_text(doc.paragraphs[147], HG0, "Body Text First Indent")
set_text(doc.paragraphs[148], HG1, "Body Text First Indent")
set_text(doc.paragraphs[150], HE10, "Body Text First Indent")
set_text(doc.paragraphs[151], HE11, "Body Text First Indent")
set_text(doc.paragraphs[152], HE20, "Body Text First Indent")
set_text(doc.paragraphs[153], HE21, "Body Text First Indent")
set_text(doc.paragraphs[154], HE30, "Body Text First Indent")
set_text(doc.paragraphs[155], HE31, "Body Text First Indent")

# Resumen y Abstract, cerrados después de IV–VII.
set_text(
    doc.paragraphs[23],
    "La investigación determinó y cuantificó los efectos diferenciales de HAPPO, MASAC, MATD3 y MAAC sobre la flexibilidad energética, las emisiones de CO₂ y los costos energéticos de una comunidad inteligente heterogénea de 17 edificios de Iquitos. La campaña canónica comprendió 12 tratamientos de 50 episodios nominales y una semilla. La contrastación principal empleó KPI-gains emparejados por indicador para MAAC, MASAC y MATD3; HAPPO careció de KPI-gains finales comparables y se mantuvo en el análisis descriptivo. Se aplicaron Shapiro–Wilk, Wilcoxon frente a la línea base con corrección Holm, Friedman, Kendall W y Wilcoxon pareado con Holm.",
    "Body Text First Indent",
)
set_text(
    doc.paragraphs[24],
    "En E1 no se rechazó la igualdad del subconjunto comparable (χ² = 5,5897; p = 0,0611; W = 0,2329); MATD3 obtuvo el mejor KPI físico distrital y MAAC la mejor mediana de KPI-gain. En E2 se rechazó la igualdad global del subconjunto (χ² = 6,0000; p = 0,0498; W = 0,6000), aunque los post hoc Holm no localizaron diferencias por pares; MATD3 presentó el menor incremento de CO₂. En E3 no se rechazó la igualdad (χ² = 3,4286; p = 0,1801; W = 0,1905) y MAAC mostró el menor incremento de costo. Globalmente se detectó diferenciación débil (χ² = 9,2911; p = 0,0096; W = 0,1787), con MAAC como mejor compromiso observado en el score integrado (0,9538) y TOPSIS (0,9827), sin superioridad universal demostrada. El alcance inferencial quedó limitado por la semilla única y por la ausencia de HAPPO en los KPI-gains.",
    "Body Text First Indent",
)
set_text(
    doc.paragraphs[25],
    "Palabras clave: aprendizaje por refuerzo profundo multiagente; coordinación energética multiobjetivo; CityLearn; flexibilidad energética; emisiones de CO₂; costos energéticos; Iquitos.",
    "Body Text First Indent",
)
set_text(
    doc.paragraphs[27],
    "This study determined and quantified the differential effects of HAPPO, MASAC, MATD3, and MAAC on energy flexibility, CO₂ emissions, and energy costs in a heterogeneous 17-building smart community in Iquitos. The canonical campaign comprised 12 nominal 50-episode treatments and one seed. The primary inference used KPI gains paired by indicator for MAAC, MASAC, and MATD3; HAPPO had no comparable final KPI gains and was retained only for descriptive analysis. Shapiro–Wilk, baseline Wilcoxon tests with Holm correction, Friedman tests, Kendall's W, and paired Wilcoxon–Holm comparisons were applied.",
    "Body Text First Indent",
)
set_text(
    doc.paragraphs[28],
    "For E1, equality was not rejected (χ² = 5.5897, p = .0611, W = .2329); MATD3 led the district physical KPI and MAAC led median KPI gain. For E2, global equality was rejected for the comparable subset (χ² = 6.0000, p = .0498, W = .6000), but Holm post hoc tests did not locate a significant pair; MATD3 showed the smallest CO₂ increase. For E3, equality was not rejected (χ² = 3.4286, p = .1801, W = .1905), and MAAC showed the smallest cost increase. Globally, weak differentiation was detected (χ² = 9.2911, p = .0096, W = .1787); MAAC was the best observed compromise in the integrated score (.9538) and TOPSIS (.9827), without demonstrated universal superiority. Inference was limited by the single seed and HAPPO's missing KPI gains.",
    "Body Text First Indent",
)
set_text(
    doc.paragraphs[29],
    "Keywords: multi-agent deep reinforcement learning; multi-objective energy coordination; CityLearn; energy flexibility; CO₂ emissions; energy costs; Iquitos.",
    "Body Text First Indent",
)

# Correcciones puntuales de Capítulo IV y residuos de marcado.
find_paragraph(doc, "Capitulo 4.").text = "Capítulo 4. Desarrollo e implementación de la coordinación energética multiobjetivo mediante MADRL"
find_paragraph(doc, "Capitulo 5.").text = "Capítulo 5. Resultados, efectos diferenciales y desempeño algorítmico"
find_paragraph(doc, "Capitulo 6.").text = "Capítulo 6. Conclusiones"
find_paragraph(doc, "Capitulo 7.").text = "Capítulo 7. Recomendaciones y trabajo futuro"
find_paragraph(doc, "flowchart LR").text = (
    "La arquitectura implementada enlaza las fuentes del SEAI, la radiación, la meteorología y las señales tarifarias con CityLearn; instancia 17 agentes de edificio en un Dec-POMDP, aplica CTDE con HAPPO, MASAC, MATD3 y MAAC, controla BESS, EV/V2G y cargas desplazables, y materializa artefactos de entrenamiento, evaluación y trazabilidad para E1, E2 y E3."
)

# Capítulo V: elementos definitivos, C1–C5 y decisiones estadísticas coherentes.
set_text(find_paragraph(doc, "PE.1."), PE1, "Body Text First Indent")
set_text(find_paragraph(doc, "OE.1. Determinar y cuantificar"), OE1, "Body Text First Indent")
set_text(find_paragraph(doc, "HE10 / HE11"), f"{HE10} {HE11}", "Body Text First Indent")
set_text(find_paragraph(doc, "PE.2."), PE2, "Body Text First Indent")
set_text(find_paragraph(doc, "OE.2. Determinar y cuantificar"), OE2, "Body Text First Indent")
set_text(find_paragraph(doc, "HE20 / HE21"), f"{HE20} {HE21}", "Body Text First Indent")
set_text(find_paragraph(doc, "PE.3."), PE3, "Body Text First Indent")
set_text(find_paragraph(doc, "OE.3. Determinar y cuantificar"), OE3, "Body Text First Indent")
set_text(find_paragraph(doc, "HE30 / HE31"), f"{HE30} {HE31}", "Body Text First Indent")
set_text(find_paragraph(doc, "PG."), PG, "Body Text First Indent")
set_text(find_paragraph(doc, "OG. Determinar y cuantificar"), OG, "Body Text First Indent")
set_text(find_paragraph(doc, "H0G / H1G"), f"{HG0} {HG1}", "Body Text First Indent")

set_text(
    find_paragraph(doc, "No se dispone en este capítulo de una tabla completa edificio-a-edificio"),
    "En los 17 edificios, MATD3 registró flex_gain_vs_baseline > 0 en 5 edificios y una mediana de −0,01497; HAPPO lo hizo en 1 edificio y presentó una mediana de −0,18342; MAAC y MASAC no registraron edificios con ganancia positiva y sus medianas fueron −0,01832 y −0,03860, respectivamente. Por tanto, la heterogeneidad de C4 respalda el liderazgo físico descriptivo de MATD3, pero no una mejora comunitaria generalizada.",
    "Body Text First Indent",
)
set_text(
    find_paragraph(doc, "- ranking distrital E1:"),
    "La desagregación procede de building_kpis_4madrl.csv (17 edificios × 4 algoritmos × 3 escenarios); estos resultados por edificio son descriptivos y no se emplean como réplicas independientes para HE.1.",
    "Body Text First Indent",
)
set_text(
    find_paragraph(doc, "El ranking de distrito sitúa a MATD3"),
    "En C3, MATD3 alcanzó el menor flex_composite distrital (1,000923). En C4, el conteo de edificios con mejora fue coherente con ese liderazgo relativo, aunque 12 de 17 edificios de MATD3 tampoco superaron la línea base.",
    "Body Text First Indent",
)
set_text(
    find_paragraph(doc, "Throughput BESS E1"),
    "En C5, el throughput BESS de E1 fue 8,85×10⁶ kWh para HAPPO, 6,24×10⁵ kWh para MASAC, 3,41×10⁵ kWh para MAAC y 8,49×10³ kWh para MATD3. La mediana de éxito de salida EV fue 0,541 para HAPPO, 0,384 para MATD3, 0,044 para MASAC y 0,040 para MAAC. Los cuatro tratamientos controlaron 17 BESS, 185 cargadores EV y 17 cargas flexibles.",
    "Body Text First Indent",
)

set_text(
    find_paragraph(doc, "Friedman es significativo al α = 0,05"),
    "Friedman fue significativo para el subconjunto comparable (χ² = 6,0000; p = 0,0498; Kendall W = 0,6000); conforme a la regla p < 0,05, se rechazó la igualdad global de MAAC, MASAC y MATD3. La ausencia de impacto frente a cero y de pares significativos tras Holm impidió localizar qué par originó la diferencia, pero no anuló el resultado omnibus.",
    "Body Text First Indent",
)
set_text(
    find_paragraph(doc, "Sin tabla completa en este capítulo."),
    "En C4, MATD3 presentó reducción de CO₂ respecto de la línea base en 5 de 17 edificios y una mediana de −557 kgCO₂; HAPPO, MAAC y MASAC no registraron edificios con reducción y mostraron medianas de −53 834, −6 411 y −5 828 kgCO₂, respectivamente. La evidencia por edificio confirma heterogeneidad y no se interpreta como réplica independiente.",
    "Body Text First Indent",
)
set_text(
    find_paragraph(doc, "Throughput BESS E2"),
    "En C5 para E2, el throughput BESS fue 1,67×10⁷ kWh en HAPPO, 6,38×10⁵ kWh en MASAC, 6,04×10⁵ kWh en MAAC y 9,48×10³ kWh en MATD3. La mediana de éxito EV fue 0,474, 0,035, 0,042 y 0,345, respectivamente. MATD3 combinó el menor incremento distrital de CO₂ con una actuación BESS sustancialmente menor; esta asociación es descriptiva y no demuestra causalidad.",
    "Body Text First Indent",
)
set_text(
    find_paragraph(doc, "- Descriptivo: MATD3 (mediana KPI-gain"),
    "El mejor desempeño descriptivo de E2 correspondió a MATD3 por mediana de KPI-gain (−0,04214), menor ΔCO₂ distrital (23 070 kg) y score OE2 (1,0000). Inferencialmente, Friedman detectó una diferencia global en el subconjunto comparable, aunque Wilcoxon–Holm no identificó un par específico.",
    "Body Text First Indent",
)
set_text(
    find_paragraph(doc, "Respuesta a PE.2."),
    "En respuesta a PE.2 y OE.2, MATD3 presentó el mejor desempeño ambiental observado y se cuantificó una diferencia global para MAAC, MASAC y MATD3 (p = 0,0498; W = 0,6000). Sin embargo, la comparación no incluyó HAPPO y los post hoc no localizaron pares, por lo que la respuesta completa de cuatro algoritmos permanece incompleta.",
    "Body Text First Indent",
)
set_text(
    find_paragraph(doc, "- HE20: no se rechaza."),
    "Para el subconjunto comparable se rechazó HE20 y se obtuvo evidencia compatible con HE21 mediante Friedman; no obstante, la hipótesis específica completa, que nombra a los cuatro algoritmos, no se declaró cerrada por la ausencia de HAPPO en los KPI-gains y por la semilla única.",
    "Body Text First Indent",
)

set_text(
    find_paragraph(doc, "Fuentes: district_ranking_by_scenario.csv (MAAC primero en E3)"),
    "En C4, el número de edificios con cost_reduction_eur > 0 fue 12/17 para HAPPO, 7/17 para MAAC, 7/17 para MASAC y 3/17 para MATD3. No obstante, las medias de reducción fueron negativas para los cuatro y el Δcosto distrital fue positivo; por ello, la mejora de edificios particulares no se confundió con ahorro comunitario.",
    "Body Text First Indent",
)
set_text(
    find_paragraph(doc, "Éxito EV E3:"),
    "En C5 para E3, el throughput BESS fue 1,42×10⁷ kWh en HAPPO, 7,17×10⁵ kWh en MASAC, 6,15×10⁵ kWh en MAAC y 9,01×10³ kWh en MATD3. La mediana de éxito EV fue 0,507, 0,043, 0,047 y 0,466, respectivamente. La intensidad de actuación no coincidió con el menor costo distrital, obtenido por MAAC.",
    "Body Text First Indent",
)

set_text(
    find_paragraph(doc, "- H0G: se rechaza"),
    "Para MAAC, MASAC y MATD3 se rechazó HG0 y se obtuvo evidencia compatible con HG1 (Friedman global p = 0,0096; W = 0,1787). La decisión no se extendió a la hipótesis completa de cuatro algoritmos porque HAPPO careció de KPI-gains finales comparables; tampoco estableció un ganador global único.",
    "Body Text First Indent",
)
set_text(
    find_paragraph(doc, "KW exploratorio:"),
    "Como sensibilidad independiente, Kruskal–Wallis produjo OE1 p = 0,4685, OE2 p = 0,7648, OE3 p = 0,7357 y GLOBAL p = 0,4044; estos valores no se usaron para sustituir la prueba pareada. Frente a baseline, solo MASAC en OE1 mostró un cambio significativo y desfavorable (p-Holm = 0,0483); globalmente, los tres algoritmos comparables mostraron cambios significativos y desfavorables.",
    "Body Text First Indent",
)
set_text(
    find_paragraph(doc, "Veredicto de cierre Cap. V."),
    "El capítulo respondió los objetivos mediante C1–C5, pero la auditoría calificó el cierre como incompleto: los cuatro algoritmos cuentan con KPI físicos, resultados por edificio y actuación de recursos, mientras que la inferencia de KPI-gains solo incluye MAAC, MASAC y MATD3 y procede de una semilla. Los liderazgos por eje y global son descriptivos, salvo las diferencias omnibus delimitadas indicadas expresamente.",
    "Body Text First Indent",
)

# Tablas consolidadas existentes.
for table in doc.tables:
    if not table.rows:
        continue
    header = [cell.text.strip() for cell in table.rows[0].cells]
    if header[:3] == ["Hipótesis", "Prueba", "Estadístico"] and len(table.rows) >= 5:
        rows = [
            ["HG0 / HG1", "Friedman GLOBAL; KPI-gains pareados", "χ² = 9,2911", "0,0096", "W = 0,1787", "MAAC–MASAC p-Holm = 0,0172", "Se rechaza HG0 en MAAC–MASAC–MATD3; decisión completa de cuatro algoritmos: incompleta", "MAAC como compromiso observado; sin ganador inferencial único", "Inferencial exploratorio"],
            ["HE10 / HE11", "Friedman OE1", "χ² = 5,5897", "0,0611", "W = 0,2329", "Todos no significativos; mínimo p-Holm = 0,110", "No se rechaza HE10 en el subconjunto comparable; hipótesis completa: incompleta", "MATD3 (KPI físico) / MAAC (mediana gain)", "Descriptivo + inferencial exploratorio"],
            ["HE20 / HE21", "Friedman OE2", "χ² = 6,0000", "0,0498", "W = 0,6000", "Todos p-Holm = 0,307", "Se rechaza HE20 en el subconjunto comparable; hipótesis completa: incompleta", "MATD3", "Omnibus significativo; pares no localizados"],
            ["HE30 / HE31", "Friedman OE3", "χ² = 3,4286", "0,1801", "W = 0,1905", "Todos no significativos", "No se rechaza HE30 en el subconjunto comparable; hipótesis completa: incompleta", "MAAC", "Descriptivo + inferencial exploratorio"],
        ]
        for row, values in zip(table.rows[1:5], rows):
            for cell, value in zip(row.cells, values):
                cell.text = value
    if header[:2] == ["Cadena", "¿Efecto respondido?"] and len(table.rows) >= 5:
        values = [
            ["PG → OG → HG0/HG1", "Sí para el trío comparable; cuatro algoritmos: incompleto", "MAAC como compromiso observado; sin ganador inferencial único", "INCOMPLETO"],
            ["PE.1 → OE.1 → HE10/HE11", "No significativo en el trío; HAPPO sin KPI-gains", "MATD3 físico / MAAC gain; no inferencial", "INCOMPLETO"],
            ["PE.2 → OE.2 → HE20/HE21", "Friedman significativo en el trío; post hoc no localiza pares", "MATD3; respaldo descriptivo", "INCOMPLETO"],
            ["PE.3 → OE.3 → HE30/HE31", "No significativo en el trío; HAPPO sin KPI-gains", "MAAC; respaldo descriptivo", "INCOMPLETO"],
        ]
        for row, row_values in zip(table.rows[1:5], values):
            for cell, value in zip(row.cells, row_values):
                cell.text = value

# Capítulo VI: conclusiones en tercera persona, prosa y respuesta C1–C5.
replace_between(
    doc,
    "6.1 Conclusión general",
    "6.2 Conclusión OE.1",
    [
        f"La conclusión general responde al objetivo inmodificable: {OG}",
        "El criterio C1 mostró que, frente a la línea base, las medianas globales de KPI-gain fueron −0,01226 para MAAC, −0,01951 para MASAC y −0,00694 para MATD3; los tres cambios fueron significativos después de Holm (p = 0,00233; p = 0,000155; p = 0,00293) y de dirección desfavorable. Por consiguiente, se cuantificó un efecto global, pero no una mejora agregada.",
        "El criterio C2 estableció diferencias entre los algoritmos comparables: Friedman produjo χ² = 9,2911, p = 0,009604 y Kendall W = 0,1787, tamaño de concordancia débil. Wilcoxon–Holm localizó únicamente la diferencia MAAC–MASAC (p-Holm = 0,01718); los otros pares no fueron significativos.",
        "Los criterios C3, C4 y C5 explicaron la dirección y la relevancia energética. En C3, MATD3 lideró flexibilidad física y presentó el menor incremento de CO₂, mientras MAAC presentó el menor incremento de costo. En C4, el número de edificios favorables cambió por eje y no apareció un dominador uniforme. En C5, las diferencias de throughput BESS y éxito EV evidenciaron políticas de actuación distintas, sin que una mayor intensidad de control implicara un mejor KPI.",
        "Como mejor compromiso global observado se identificó a MAAC por el score integrado E1–E3 de 0,9538 y la cercanía TOPSIS de 0,9827; MATD3 mantuvo el mejor valor en otra agregación 3×3 y la mejor mediana global de KPI-gain. En consecuencia, MAAC se recomendó como compromiso multicriterio descriptivo, sin afirmar superioridad global estadísticamente demostrada ni dominancia universal.",
        "Conforme a la regla p < 0,05, HG0 se rechazó para el subconjunto comparable MAAC–MASAC–MATD3 y se obtuvo evidencia compatible con HG1. No obstante, el objetivo y la hipótesis completos quedaron INCOMPLETOS porque HAPPO no aportó KPI-gains finales comparables y solo se materializó una semilla. El alcance se restringió a la comunidad simulada, al periodo 2023–2025 y a la corrida canónica auditada.",
    ],
)

replace_between(
    doc,
    "6.2 Conclusión OE.1",
    "6.3 Conclusión OE.2",
    [
        f"La primera conclusión específica responde al objetivo inmodificable: {OE1}",
        "En C1, las medianas de KPI-gain fueron −0,00119 para MAAC, −0,00289 para MATD3 y −0,01363 para MASAC. Solo MASAC mostró un cambio significativo frente a la línea base después de Holm (p-Holm = 0,04834), y la dirección fue desfavorable; por tanto, no se demostró una mejora significativa de flexibilidad frente al baseline.",
        "En C2, Friedman produjo χ² = 5,5897, p = 0,06112 y Kendall W = 0,23291; no se rechazó la igualdad en el subconjunto comparable. Ningún par de Wilcoxon–Holm fue significativo. En C3, MATD3 obtuvo el menor flex_composite distrital (1,000923), mientras MAAC alcanzó la mejor mediana de KPI-gain, lo que configuró un liderazgo descriptivo mixto.",
        "En C4, MATD3 mejoró la flexibilidad respecto de la línea base en 5 de 17 edificios, HAPPO en 1 y MAAC y MASAC en ninguno. En C5, HAPPO presentó el mayor throughput BESS y la mayor mediana de éxito EV, pero no el mejor flex_composite; esta divergencia confirmó que la intensidad de actuación no debía confundirse con desempeño físico.",
        "Bajo el KPI físico principal de E1 se identificó a MATD3 como el algoritmo de mejor desempeño descriptivo; MAAC conservó el liderazgo por mediana de gain. HE10 no se rechazó en MAAC–MASAC–MATD3 y HE11 no quedó respaldada en ese subconjunto. La decisión completa de cuatro algoritmos se calificó INCOMPLETA por la falta de KPI-gains de HAPPO y por la semilla única.",
    ],
)

replace_between(
    doc,
    "6.3 Conclusión OE.2",
    "6.4 Conclusión OE.3",
    [
        f"La segunda conclusión específica responde al objetivo inmodificable: {OE2}",
        "En C1, las medianas de KPI-gain fueron negativas para MATD3 (−0,04214), MAAC (−0,04700) y MASAC (−0,05164); ninguna diferencia frente a cero permaneció significativa tras Holm (p-Holm = 0,1875). En C3, todos los ΔCO₂ distritales fueron positivos, por lo que no se calificaron como reducciones: MATD3 presentó el menor incremento (23 070 kg), seguido por MAAC (70 654 kg), MASAC (77 649 kg) y HAPPO (1 431 341 kg).",
        "En C2, Friedman produjo χ² = 6,0000, p = 0,04979 y Kendall W = 0,6000. Se rechazó la igualdad para MAAC–MASAC–MATD3, con una magnitud de concordancia moderada-alta; sin embargo, los tres post hoc Wilcoxon–Holm fueron no significativos (p-Holm = 0,3074), por lo que no se localizó un par responsable de la diferencia.",
        "En C4, MATD3 logró reducción de CO₂ en 5 de 17 edificios, mientras HAPPO, MAAC y MASAC no registraron edificios con reducción. En C5, MATD3 combinó el menor ΔCO₂ con el menor throughput BESS del eje y una mediana de éxito EV de 0,345; el patrón se interpretó como asociación descriptiva y no como causalidad.",
        "MATD3 fue identificado como el mejor MADRL ambiental observado por KPI-gain, ΔCO₂ y score OE2. Conforme a p < 0,05, HE20 se rechazó y se obtuvo evidencia compatible con HE21 en el subconjunto comparable; la ausencia de pares significativos limitó la localización del efecto. La hipótesis completa de cuatro algoritmos y el cumplimiento total de OE.2 quedaron INCOMPLETOS por la falta de HAPPO en la inferencia y por la semilla única.",
    ],
)

replace_between(
    doc,
    "6.4 Conclusión OE.3",
    "6.5 Contribuciones científicas",
    [
        f"La tercera conclusión específica responde al objetivo inmodificable: {OE3}",
        "En C1, las medianas de KPI-gain fueron −0,00268 para MAAC, −0,00918 para MATD3 y −0,01403 para MASAC. Ningún algoritmo mostró ahorro significativo frente a la línea base después de Holm (MAAC y MASAC p-Holm = 0,07813; MATD3 p-Holm = 0,05859), y la dirección agregada fue desfavorable.",
        "En C2, Friedman produjo χ² = 3,4286, p = 0,18009 y Kendall W = 0,19048; no se rechazó la igualdad y ningún post hoc fue significativo. En C3, MAAC presentó el menor Δcosto distrital (9 515 EUR), seguido por MASAC (19 793 EUR), MATD3 (44 399 EUR) y HAPPO (106 828 EUR). El menor valor observado no se interpretó como ahorro demostrado.",
        "En C4, HAPPO mostró reducciones de costo en 12 de 17 edificios, MAAC y MASAC en 7 y MATD3 en 3; pese a ello, las medias por edificio y el resultado distrital fueron desfavorables. En C5, la actuación BESS y el éxito EV variaron ampliamente y no reprodujeron el orden del KPI de costo, lo que confirmó la necesidad de separar actividad de control y desempeño económico.",
        "MAAC fue identificado como el mejor MADRL descriptivo en E3 por mediana de gain, Δcosto, score OE3 y TOPSIS. HE30 no se rechazó en el subconjunto comparable y HE31 no quedó respaldada. El cumplimiento total de OE.3 se calificó INCOMPLETO porque HAPPO no participó en los KPI-gains inferenciales y la campaña solo contó con una semilla.",
    ],
)

replace_between(
    doc,
    "6.5 Contribuciones científicas",
    "6.6 Limitaciones",
    [
        "El aporte al estado del arte consistió en articular, dentro de un mismo protocolo auditable, la coordinación energética multiobjetivo, cuatro familias MADRL, una comunidad heterogénea de 17 edificios y una separación explícita entre señal de recompensa, KPI físicos y KPI-gains. Esta integración cubrió una brecha recurrente de los estudios que comparan curvas de recompensa sin demostrar su correspondencia con flexibilidad, CO₂ y costos.",
        "El aporte metodológico fue el criterio C1–C5: efecto frente a baseline, diferencias entre algoritmos, KPI distrital, resultados de los 17 edificios y actuación de recursos controlables. La secuencia Shapiro–Wilk, Wilcoxon–Holm frente a cero, Friedman, Kendall W y Wilcoxon pareado con Holm mantuvo la dependencia por KPI; Kruskal–Wallis y Mann–Whitney se conservaron únicamente como sensibilidad independiente.",
        "El aporte algorítmico fue la comparación homogénea de HAPPO, MASAC, MATD3 y MAAC bajo el mismo Dec-POMDP, CTDE, comunidad, horizonte y perfiles E1–E3. Los resultados mostraron que MATD3 y MAAC ocuparon regiones distintas del compromiso multiobjetivo y que ningún mecanismo produjo dominancia universal.",
        "El aporte energético fue cuantificar conjuntamente flexibilidad, emisiones y costos a escala distrital, por edificio y por recurso. La desagregación reveló que una mejora local no garantizó mejora comunitaria y que mayor throughput BESS o mayor éxito EV no implicaron necesariamente mejores KPI finales.",
        "El aporte multiobjetivo fue distinguir el mejor compromiso observado de la superioridad estadística. MAAC encabezó el score integrado y TOPSIS, mientras MATD3 lideró flexibilidad física, CO₂ y otra agregación robusta; esta divergencia fue tratada como trade-off y no como contradicción que debiera ocultarse.",
        "El aporte computacional y de reproducibilidad fue conservar la corrida madrl_v3_20260627_164047, sus configuraciones, checkpoints, series temporales, trazas, KPI distritales, KPI por edificio y manifiestos. Esta trazabilidad permitió reconstruir cada afirmación y declarar como incompleta cualquier dimensión sin evidencia comparable.",
        "El aporte aplicado a Iquitos fue instanciar el problema en el SEAI con señales meteorológicas, tarifarias y de carbono del caso de estudio, sin generalizar la simulación a la operación real. De este modo, la contribución científica se formuló como evidencia computacional situada y reproducible, no como validación de campo.",
    ],
)

replace_between(
    doc,
    "6.6 Limitaciones",
    "Capítulo 7.",
    [
        "La principal limitación fue la semilla única (seed = 0); los episodios correlacionados de una corrida no constituyeron réplicas independientes. Por ello, los p-valores y tamaños del efecto se interpretaron como evidencia intra-corrida y no como robustez multisemilla.",
        "HAPPO conservó 50 episodios nominales mediante 49 registros históricos y un episodio post-resume, pero no dispuso de KPI-gains finales comparables. En consecuencia, la descripción física incluyó cuatro algoritmos y la inferencia principal solo tres; esta asimetría impidió cerrar literalmente HG0/HG1 y HE10–HE31 para los cuatro algoritmos.",
        "El emparejamiento se realizó por KPI orientado (n = 12 en E1, n = 5 en E2, n = 9 en E3 y n = 26 global), no por semillas. Los bloques de KPI poseen significados físicos distintos y no sustituyen una campaña de réplicas; por ello, la prueba global se mantuvo exploratoria.",
        "El estudio se limitó a simulación CityLearn, a 17 edificios, al periodo 2023–2025 y a la configuración de recompensas e hiperparámetros auditada. No se efectuaron pruebas fuera de muestra, HIL/SIL, piloto ni despliegue real.",
        "Los resultados por edificio y por recurso se analizaron descriptivamente. No se efectuó una batería inferencial completa de C4 y C5, y no se atribuyó causalidad a la relación entre acciones, throughput y KPI.",
        "Los rankings dependieron del criterio de agregación: MAAC lideró score integrado y TOPSIS, mientras MATD3 lideró otras medidas robustas y dos ejes físicos. Esta sensibilidad impidió declarar un ganador global único.",
    ],
)

# Capítulo VII: correcciones de alcance y decisión de E2/HG.
for paragraph in doc.paragraphs:
    if paragraph.text:
        paragraph.text = paragraph.text.replace("H0G", "HG0").replace("H1G", "HG1")

set_text(
    find_paragraph(doc, "Se recomienda evaluar robustez de las decisiones HG0/HG1"),
    "Se recomienda evaluar la robustez de HG0/HG1 y HE10–HE31 con semillas independientes, intervalos de confianza y análisis de potencia, manteniendo los KPI-gains emparejados como una capa separada de los descriptivos episódicos y de los KPI físicos.",
    "Body Text First Indent",
)
set_text(
    find_paragraph(doc, "Síntesis. Bajo las condiciones experimentales estudiadas"),
    "Bajo las condiciones experimentales estudiadas, se recomienda MATD3 para E1 cuando el criterio principal sea la flexibilidad física distrital; MATD3 para E2 por presentar el menor incremento de CO₂; MAAC para E3 por registrar el menor incremento de costo; y MAAC como mejor compromiso global observado por score integrado y TOPSIS. Estas recomendaciones son descriptivas, no constituyen superioridad universal y deberán revalidarse con HAPPO comparable y múltiples semillas.",
    "Body Text First Indent",
)

# Jerarquía visual de títulos y limpieza de residuos Markdown en IV–VII.
for paragraph in doc.paragraphs:
    text = paragraph.text.strip()
    if text == "---":
        paragraph.text = ""
        continue
    if "**" in paragraph.text or "`" in paragraph.text:
        paragraph.text = paragraph.text.replace("**", "").replace("`", "")
    if text.startswith(("Capítulo 4.", "Capítulo 5.", "Capítulo 6.", "Capítulo 7.")):
        paragraph.style = "Heading 1"
    elif re.match(r"^[4-7]\.\d+\s", text):
        paragraph.style = "Heading 2"
    elif any(text.startswith(prefix) for prefix in (
        "4.1.1", "4.2.1", "4.2.2", "4.3.1", "4.3.2", "4.4.1", "4.4.2", "4.7.1", "4.7.2", "4.7.3", "4.7.4", "4.8.1", "4.8.2", "4.8.3", "4.14.1", "4.14.2",
        "5.3.1", "5.3.2", "5.3.3", "5.3.4", "5.3.5", "5.3.6", "5.3.7", "5.3.8", "5.3.9", "5.3.10", "5.3.11", "5.3.12", "5.3.13",
        "5.4.1", "5.4.2", "5.4.3", "5.4.4", "5.4.5", "5.4.6", "5.4.7", "5.4.8", "5.4.9", "5.4.10", "5.4.11", "5.4.12", "5.4.13",
        "5.5.1", "5.5.2", "5.5.3", "5.5.4", "5.5.5", "5.5.6", "5.5.7", "5.5.8", "5.5.9", "5.5.10", "5.5.11", "5.5.12", "5.5.13",
        "5.6.1", "5.6.2", "5.6.3", "5.6.4", "5.8.1", "5.8.2", "5.8.3",
    )):
        paragraph.style = "Heading 3"

for table in doc.tables:
    for row in table.rows:
        row.height_rule = WD_ROW_HEIGHT_RULE.AT_LEAST
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                paragraph.text = paragraph.text.replace("H0G", "HG0").replace("H1G", "HG1")
            clean_cell(cell)

# Matriz final de 13 columnas, antes de referencias.
references = find_paragraph(doc, "Referencias bibliográficas")
heading = references.insert_paragraph_before("7.8 Matriz final de alineamiento y auditoría")
heading.style = "Heading 2"
intro = references.insert_paragraph_before(
    "La matriz verifica la correspondencia PG–OG–HG y PE–OE–HE con los mecanismos del Capítulo IV, los resultados C1–C5 del Capítulo V, las conclusiones del Capítulo VI y las recomendaciones del Capítulo VII. El estado INCOMPLETO señala una limitación de evidencia y no una reformulación de los elementos definitivos."
)
intro.style = "Body Text First Indent"
caption = references.insert_paragraph_before("Tabla 7.8\nMatriz final de alineamiento y auditoría de objetivos")
caption.style = "titlulotabla" if "titlulotabla" in [s.name for s in doc.styles] else "Caption"

headers = [
    "Problema", "Objetivo", "Hipótesis", "Desarrollo Cap. IV", "KPI", "Resultado descriptivo",
    "Prueba inferencial", "p", "Tamaño del efecto", "Mejor MADRL", "Conclusión", "Recomendación", "Estado",
]
matrix_rows = [
    [
        PG,
        OG,
        f"{HG0} {HG1}",
        "4.1–4.15: arquitectura, comunidad, Dec-POMDP, CTDE, 4×3, evaluación y trazabilidad E1+E2+E3.",
        "26 KPI-gains globales por algoritmo comparable; flex_composite, ΔCO₂ y Δcosto.",
        "Medianas: MAAC −0,01226; MASAC −0,01951; MATD3 −0,00694. Score integrado: MAAC 0,9538.",
        "Friedman pareado por KPI + Kendall W; Wilcoxon–Holm.",
        "0,009604",
        "W = 0,1787 (débil)",
        "MAAC, compromiso observado; sin ganador inferencial único.",
        "Se rechaza HG0 en el trío comparable; no se cierra la hipótesis literal de cuatro algoritmos.",
        "Completar HAPPO comparable y campaña multisemilla; revalidar ranking.",
        "INCOMPLETO",
    ],
    [
        PE1,
        OE1,
        f"{HE10} {HE11}",
        "4.9 E1; 4.10 tratamiento E1; 4.12 KPI; 4.15 correspondencia OE.1–E1.",
        "12 KPI-gains; flex_composite; flex_gain por 17 edificios; BESS/EV/cargas.",
        "MATD3 flex_composite 1,000923 y 5/17 edificios favorables; MAAC mediana gain −0,00119.",
        "Friedman pareado; Wilcoxon–Holm; Wilcoxon vs baseline.",
        "0,061123",
        "W = 0,2329 (débil)",
        "MATD3 por KPI físico; MAAC por mediana gain.",
        "No se rechaza HE10 en el trío; liderazgo descriptivo mixto.",
        "Priorizar MATD3 para flexibilidad física y repetir con semillas/HAPPO.",
        "INCOMPLETO",
    ],
    [
        PE2,
        OE2,
        f"{HE20} {HE21}",
        "4.9 E2; 4.10 tratamiento E2; 4.12 KPI; 4.15 correspondencia OE.2–E2.",
        "5 KPI-gains; ΔCO₂ distrital y por 17 edificios; BESS/EV/cargas.",
        "MATD3 ΔCO₂ 23 070 kg y 5/17 edificios con reducción; los Δ distritales fueron positivos.",
        "Friedman pareado; Wilcoxon–Holm; Wilcoxon vs baseline.",
        "0,049787",
        "W = 0,6000",
        "MATD3, descriptivo.",
        "Se rechaza HE20 en el trío; post hoc no localiza pares; hipótesis de cuatro algoritmos incompleta.",
        "Revalidar MATD3 con HAPPO comparable, semillas e intervalos de confianza.",
        "INCOMPLETO",
    ],
    [
        PE3,
        OE3,
        f"{HE30} {HE31}",
        "4.9 E3; 4.10 tratamiento E3; 4.12 KPI; 4.15 correspondencia OE.3–E3.",
        "9 KPI-gains; Δcosto distrital y por 17 edificios; BESS/EV/cargas.",
        "MAAC Δcosto 9 515 EUR y mediana gain −0,00268; no hubo ahorro distrital demostrado.",
        "Friedman pareado; Wilcoxon–Holm; Wilcoxon vs baseline.",
        "0,180092",
        "W = 0,1905 (débil)",
        "MAAC, descriptivo.",
        "No se rechaza HE30 en el trío; el menor costo observado no equivale a ahorro demostrado.",
        "Priorizar MAAC para costo observado y repetir con semillas/HAPPO.",
        "INCOMPLETO",
    ],
]

table = doc.add_table(rows=1, cols=len(headers))
table.style = "Table Grid"
table.autofit = False
for cell, value in zip(table.rows[0].cells, headers):
    cell.text = value
    set_cell_shading(cell, "1F4E78")
    for paragraph in cell.paragraphs:
        for run in paragraph.runs:
            run.font.color.rgb = RGBColor(255, 255, 255)
            run.font.bold = True
            run.font.size = Pt(6)
            run.font.name = "Arial"
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
set_repeat_table_header(table.rows[0])

for values in matrix_rows:
    row = table.add_row()
    for cell, value in zip(row.cells, values):
        cell.text = value
        set_cell_margins(cell)
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
        for paragraph in cell.paragraphs:
            paragraph.paragraph_format.space_after = Pt(0)
            paragraph.paragraph_format.line_spacing = 1.0
            for run in paragraph.runs:
                run.font.name = "Arial"
                run.font.size = Pt(5.5)
    set_cell_shading(row.cells[-1], "FFF2CC")

widths = [1.20, 1.20, 1.20, 0.85, 0.75, 0.95, 0.75, 0.45, 0.65, 0.75, 0.95, 0.95, 0.55]
for row in table.rows:
    for cell, width in zip(row.cells, widths):
        cell.width = Inches(width)

# Move table from the document end to immediately before Referencias.
references._p.addprevious(table._tbl)
note = references.insert_paragraph_before(
    "Nota. Los p-valores principales corresponden a Friedman sobre KPI-gains emparejados por indicador. HAPPO participa en C3–C5, pero no en la inferencia C1–C2 por ausencia de KPI-gains finales comparables. Fuente: elaboración propia a partir de la corrida madrl_v3_20260627_164047 y sus artefactos canónicos."
)
note.style = "nota" if "nota" in [s.name for s in doc.styles] else "Body Text"

# Propiedades base de fuente y títulos.
for style_name in ("Normal", "Body Text First Indent"):
    if style_name in [style.name for style in doc.styles]:
        style = doc.styles[style_name]
        style.font.name = "Arial"
        style.font.size = Pt(11)
for style_name in ("Heading 1", "Heading 2", "Heading 3"):
    style = doc.styles[style_name]
    style.font.name = "Arial"
    style.font.bold = True

doc.core_properties.title = TITLE
doc.core_properties.subject = "Auditoría, reestructuración e integración final de los capítulos IV–VII"
doc.core_properties.comments = "Documento generado desde una copia; el original permanece intacto."
doc.save(OUTPUT)
print(OUTPUT)
