#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Regenerate Figura 5.1 checkpoint coverage (project MADRL only) and patch Words.

Counts = files listed in checkpoint_manifest.json for HAPPO/MAAC/MASAC/MATD3 x E1/E2/E3
from the canonical Drive mirror under outputs/_drive_madrl/full_data (madrl_v3_20260627_164047).
Does NOT use old v4 HAPPO manifests. Does NOT count only episode_* path matches.
"""
from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from docx import Document

REPO = Path(__file__).resolve().parents[1]
FULL = REPO / "outputs" / "_drive_madrl" / "full_data"
FIG_DIR = REPO / "outputs" / "_drive_madrl" / "gdrive_20260627_164047_objective_analysis" / "figures"
TABLE_DIR = FIG_DIR.parent / "tables"
PNG = FIG_DIR / "checkpoint_coverage_by_treatment.png"
REPORT = FIG_DIR.parent / "figura_5_1_checkpoint_coverage_report.json"

ALGOS = ["HAPPO", "MAAC", "MASAC", "MATD3"]
SCENARIOS = ["E1", "E2", "E3"]

DOC_TARGETS = [
    REPO / "docs" / "ABRIR_ESTE_WORD_FINAL_TODAS_FIGURAS_APA_INTERPRETADAS.docx",
    REPO / "docs" / "Tesis_Doctoral_MADRL_CityLearn_Iquitos_FINAL_COMPLETA.docx",
]


def scan_counts() -> pd.DataFrame:
    rows = []
    for algo in ALGOS:
        for scen in SCENARIOS:
            man = FULL / algo / scen / "data" / "checkpoint_manifest.json"
            listed = 0
            declared = None
            source = "missing"
            if man.exists():
                obj = json.loads(man.read_text(encoding="utf-8"))
                listed = len(obj.get("checkpoints") or [])
                declared = obj.get("checkpoint_count")
                source = str(man.relative_to(REPO)).replace("\\", "/")
            rows.append(
                {
                    "algorithm": algo,
                    "scenario": scen,
                    "treatment": f"{algo}-{scen}",
                    "checkpoint_files_listed": listed,
                    "checkpoint_count_declared": declared if declared is not None else listed,
                    "source": source,
                }
            )
    return pd.DataFrame(rows)


def plot_coverage(df: pd.DataFrame) -> Path:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    # Stable order: algo major, scenario minor
    df = df.copy()
    df["algorithm"] = pd.Categorical(df["algorithm"], ALGOS, ordered=True)
    df["scenario"] = pd.Categorical(df["scenario"], SCENARIOS, ordered=True)
    df = df.sort_values(["algorithm", "scenario"])

    labels = df["treatment"].tolist()
    values = df["checkpoint_files_listed"].astype(int).tolist()

    fig, ax = plt.subplots(figsize=(9.5, 4.4))
    colors = []
    palette = {"HAPPO": "#7A7A7A", "MAAC": "#406A9F", "MASAC": "#2E8B57", "MATD3": "#C45C26"}
    for lab in labels:
        colors.append(palette.get(lab.split("-")[0], "#406A9F"))
    bars = ax.bar(labels, values, color=colors)
    ax.set_title("Cobertura de checkpoints por tratamiento (MADRL del proyecto)")
    ax.set_ylabel("archivos listados en checkpoint_manifest.json")
    ax.tick_params(axis="x", rotation=65)
    ax.grid(axis="y", alpha=0.25)
    ymax = max(values) if values else 1
    ax.set_ylim(0, max(10, ymax * 1.15))
    for b, v in zip(bars, values):
        ax.text(b.get_x() + b.get_width() / 2, v + ymax * 0.02, str(v), ha="center", va="bottom", fontsize=8)
    # Note HAPPO absence honestly
    if any(df.loc[df["algorithm"] == "HAPPO", "checkpoint_files_listed"] == 0):
        ax.text(
            0.01,
            0.98,
            "HAPPO: sin checkpoint_manifest.json en corrida canonica madrl_v3_20260627_164047",
            transform=ax.transAxes,
            va="top",
            fontsize=7.5,
            color="#444444",
        )
    fig.tight_layout()
    fig.savefig(PNG, dpi=180, bbox_inches="tight")
    plt.close(fig)
    df.to_csv(TABLE_DIR / "figura_5_1_checkpoint_coverage_counts.csv", index=False)
    return PNG


def replace_image_after_caption(docx_path: Path, caption_token: str, png_path: Path) -> dict:
    info = {"file": docx_path.name, "replaced": False}
    if not docx_path.exists():
        info["error"] = "missing"
        return info
    png_bytes = png_path.read_bytes()
    try:
        with zipfile.ZipFile(docx_path, "r") as zin:
            xml = zin.read("word/document.xml").decode("utf-8")
            rels = zin.read("word/_rels/document.xml.rels").decode("utf-8")
    except Exception as exc:
        info["error"] = f"{type(exc).__name__}: {exc}"
        return info

    # Prefer Figura 5.1; fallback Cobertura de checkpoints
    m = re.search(re.escape(caption_token), xml)
    if not m:
        m = re.search(r"Cobertura de checkpoints por tratamiento", xml)
    if not m:
        info["error"] = f"caption token not found: {caption_token}"
        return info
    after = xml[m.end() :]
    blips = re.findall(r'a:blip[^>]*r:embed="(rId\d+)"', after)
    if not blips:
        info["error"] = "no blip after caption"
        return info
    rid = blips[0]
    rm = re.search(rf'Relationship[^>]*Id="{rid}"[^>]*Target="([^"]+)"', rels)
    if not rm:
        info["error"] = f"no relationship for {rid}"
        return info
    target = rm.group(1)
    media = "word/" + target.lstrip("/")
    tmp = docx_path.with_suffix(".docx.tmp_fig51")
    try:
        with zipfile.ZipFile(docx_path, "r") as zin, zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as zout:
            replaced = False
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename.replace("\\", "/") == media.replace("\\", "/"):
                    data = png_bytes
                    replaced = True
                zout.writestr(item, data)
        if not replaced:
            tmp.unlink(missing_ok=True)
            info["error"] = f"media part not in zip: {media}"
            return info
        tmp.replace(docx_path)
        info.update({"replaced": True, "rId": rid, "media": media, "bytes": len(png_bytes)})
    except PermissionError:
        alt = docx_path.with_name(docx_path.stem + "_FIG51_PATCHED.docx")
        if tmp.exists():
            tmp.replace(alt)
        info.update({"replaced": False, "saved_alt": alt.name, "note": "archivo bloqueado (abierto en Word)"})
    return info


def patch_caption_language(docx_path: Path) -> int:
    """Light caption note update only; no full rewrite."""
    try:
        doc = Document(str(docx_path))
    except Exception:
        return 0
    n = 0
    for p in doc.paragraphs:
        t = p.text or ""
        if "Figura 5.1" in t and "Cobertura de checkpoints" in t:
            # leave caption id; optional clarification in following note paras only if clearly wrong
            pass
        if re.search(r"doctorado|doctoral", t, re.I):
            # do not bulk rewrite here beyond this figure scope
            pass
    # also fix interpretation note near 5.1 if it invents alien algos — skipped unless found
    try:
        doc.save(str(docx_path))
    except PermissionError:
        return -1
    return n


def find_other_tesis_with_fig51() -> list[Path]:
    out = []
    for p in sorted((REPO / "docs").glob("Tesis_Doctoral_*.docx")):
        if ".bak" in p.name.lower() or p.name.startswith("~$"):
            continue
        try:
            with zipfile.ZipFile(p, "r") as z:
                xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
            if "Figura 5.1" in xml and "Cobertura de checkpoints" in xml:
                out.append(p)
        except Exception:
            continue
    return out


def main() -> int:
    df = scan_counts()
    png = plot_coverage(df)
    targets = list(DOC_TARGETS)
    for p in find_other_tesis_with_fig51():
        if p not in targets:
            targets.append(p)
    # also ABRIR siblings that contain Fig 5.1
    for p in sorted((REPO / "docs").glob("ABRIR_ESTE_*.docx")):
        if ".bak" in p.name.lower():
            continue
        try:
            with zipfile.ZipFile(p, "r") as z:
                xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
            if "Figura 5.1" in xml and "checkpoints" in xml.lower():
                if p not in targets:
                    targets.append(p)
        except Exception:
            pass

    embeds = []
    for docx in targets:
        embeds.append(replace_image_after_caption(docx, "Figura 5.1", png))

    report = {
        "counts": df.to_dict(orient="records"),
        "png": str(png),
        "png_bytes": png.stat().st_size,
        "wrong_previous_logic": (
            "El generador contaba solo filas cuyo relative_path coincidia con episode_(\\d+); "
            "eso dejaba MASAC/MATD3 en 0 pese a tener 12/34 archivos en el manifiesto, "
            "e ignoraba HAPPO (sin manifiesto en la corrida canonica). "
            "No se usan manifiestos HAPPO de la corrida antigua citylearn_v3_madrl_full_20260615_074011_v4."
        ),
        "algorithms_included": ALGOS,
        "scenarios_included": SCENARIOS,
        "embeds": embeds,
    }
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
