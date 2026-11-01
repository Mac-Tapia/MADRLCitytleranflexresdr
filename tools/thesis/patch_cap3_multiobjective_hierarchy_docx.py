"""Insert only §3.1.3 on the canonical thesis Word document.

The report Word keeps a different chapter structure and is intentionally not
modified: the user requested that this material appear only in numeral 3.1.3.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from pathlib import Path
import shutil

from docx import Document
from docx.oxml import OxmlElement
from docx.text.paragraph import Paragraph

from thesis_references_apa import load_all_thesis_references


REPO = Path(__file__).resolve().parents[2]
TARGET = REPO / "docs" / "Tesis_Doctoral_MADRL_CityLearn_Iquitos.docx"
BACKUP_DIR = REPO / "outputs" / "_word_backups"

ANCHOR = "3.2 Diseno cuasiexperimental"
HEADING = "3.1.3 Coordinación energética multiobjetivo (VD)"
BODY_1 = (
    "La coordinación se implementa mediante una suma ponderada de tres componentes acotados: "
    "Rₛ = w_F R_F + w_CO₂ R_CO₂ + w_cost R_cost. Se adopta una jerarquía compensatoria "
    "cíclica con nivel dominante 0,60, secundario 0,25 y residual 0,15, en el orden "
    "[flexibilidad, CO₂, costo]: E1=[0,60; 0,15; 0,25] se vincula con OE.1; "
    "E2=[0,25; 0,60; 0,15], con OE.2; y E3=[0,15; 0,25; 0,60], con OE.3. Cada fila suma "
    "uno, el peso dominante supera la suma de los otros dos (0,60 > 0,40) y cada objetivo "
    "recibe una vez cada nivel, por lo que la intensidad de preferencia es comparable entre "
    "escenarios. La escalarización lineal mediante vectores de preferencia se emplea en gestión "
    "energética con aprendizaje por refuerzo (Lu et al., 2022; Nweye et al., 2023a), mientras "
    "que estudios energéticos y tesis afines separan los compromisos técnicos, ambientales y "
    "económicos (Jiménez Perdomo & González Escobar, 2024; Mayanti et al., 2021)."
)
BODY_2 = (
    "Esta formulación es una suma ponderada jerarquizada y compensatoria, no optimización "
    "lexicográfica: los objetivos secundarios pueden compensar parcialmente el deterioro del "
    "dominante. Una jerarquía lexicográfica estricta exige optimizar los objetivos en secuencia "
    "y preservar el óptimo superior —o una tolerancia explícita— antes de atender el siguiente "
    "(Huy et al., 2023; Tostado-Véliz et al., 2022). Por ello, 0,60/0,25/0,15 es una decisión "
    "del diseño experimental, no un valor universal. Su validez se verificará con KPI "
    "independientes —pico y rampa para OE.1, CO₂ para OE.2 y costo para OE.3—, contribuciones "
    "efectivas |wⱼRⱼ|, sensibilidad del peso dominante y repetición por semillas; los resultados "
    "obtenidos con ponderaciones anteriores no se reinterpretan y requieren reentrenamiento."
)
REFERENCE_PREFIXES = (
    "Huy, T. H. B.",
    "Jiménez Perdomo, J. E.",
    "Lu, J.",
    "Mayanti, B.",
    "Tostado-Véliz, M.",
)


def insert_before(anchor: Paragraph, text: str, style: str) -> Paragraph:
    element = OxmlElement("w:p")
    anchor._p.addprevious(element)
    paragraph = Paragraph(element, anchor._parent)
    paragraph.style = style
    paragraph.add_run(text)
    return paragraph


def copy_run_format(source: Paragraph, target: Paragraph) -> None:
    if not source.runs or not target.runs:
        return
    source_rpr = source.runs[0]._r.rPr
    if source_rpr is not None:
        target.runs[0]._r.insert(0, deepcopy(source_rpr))


def main() -> int:
    document = Document(TARGET)
    paragraphs = document.paragraphs
    if any(paragraph.text.strip() == HEADING for paragraph in paragraphs):
        raise RuntimeError(f"Section already exists in {TARGET}")

    anchors = [paragraph for paragraph in paragraphs if paragraph.text.strip().startswith(ANCHOR)]
    if len(anchors) != 1:
        raise RuntimeError(f"Expected one anchor {ANCHOR!r}, found {len(anchors)}")
    anchor = anchors[0]

    prior_body = next(
        paragraph
        for paragraph in reversed(paragraphs[: paragraphs.index(anchor)])
        if paragraph.text.strip() and paragraph.style.name == "Normal"
    )
    heading = insert_before(anchor, HEADING, "Heading 3")
    first = insert_before(anchor, BODY_1, prior_body.style.name)
    second = insert_before(anchor, BODY_2, prior_body.style.name)
    copy_run_format(prior_body, first)
    copy_run_format(prior_body, second)

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = BACKUP_DIR / f"{TARGET.stem}_pre_cap313_hierarchy_{timestamp}{TARGET.suffix}"
    shutil.copy2(TARGET, backup)
    document.save(TARGET)

    verified = Document(TARGET)
    if sum(paragraph.text.strip() == HEADING for paragraph in verified.paragraphs) != 1:
        raise RuntimeError("Saved document does not contain exactly one §3.1.3 heading")
    if sum(BODY_1 in paragraph.text for paragraph in verified.paragraphs) != 1:
        raise RuntimeError("Saved document does not contain the first §3.1.3 paragraph")
    if sum(BODY_2 in paragraph.text for paragraph in verified.paragraphs) != 1:
        raise RuntimeError("Saved document does not contain the second §3.1.3 paragraph")

    print(f"updated={TARGET}")
    print(f"backup={backup}")
    return 0


def append_missing_references() -> int:
    document = Document(TARGET)
    heading_positions = [
        index
        for index, paragraph in enumerate(document.paragraphs)
        if paragraph.text.strip().lower().startswith("referencias bibliogr")
    ]
    if len(heading_positions) != 1:
        raise RuntimeError(f"Expected one references heading, found {len(heading_positions)}")

    reference_start = heading_positions[0]
    existing = "\n".join(paragraph.text for paragraph in document.paragraphs[reference_start:])
    selected = [
        reference
        for reference in load_all_thesis_references()
        if reference.startswith(REFERENCE_PREFIXES)
    ]
    missing = [reference for reference in selected if reference not in existing]
    for reference in missing:
        paragraph = document.add_paragraph(reference, style="Normal")
        paragraph.paragraph_format.first_line_indent = None
        paragraph.paragraph_format.left_indent = None

    if missing:
        document.save(TARGET)
    print(f"references_added={len(missing)}")
    return len(missing)


if __name__ == "__main__":
    if any(paragraph.text.strip() == HEADING for paragraph in Document(TARGET).paragraphs):
        append_missing_references()
        raise SystemExit(0)
    main()
    append_missing_references()
