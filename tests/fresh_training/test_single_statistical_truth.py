"""Module 4, task 4.1 step 3 (SPEC-009): one statistical truth.

Every inferential figure of the thesis comes from tools/eval/build_campaign_statistical_report.py on the fresh
campaign. A document under docs/ (outside audits and plans, which are records) that quotes a p-value must either
cite that report or carry the banner of the retired historical results (owner decision 2026-11-01).
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PATTERN = re.compile(r'p ?= ?0[.,]\d{2,}|p ?< ?0[.,]05|KW p ?=|Friedman p|p-Holm ?=')
BANNER = 'Resultados históricos retirados'
REPORT = 'build_campaign_statistical_report'


def quoting_documents():
    for path in sorted((REPO/'docs').rglob('*.md')):
        rel = path.relative_to(REPO).as_posix()
        if rel.startswith(('docs/audits/', 'docs/plans/')):
            continue
        text = path.read_text(encoding='utf-8', errors='ignore')
        if PATTERN.search(text):
            yield rel, text


def test_every_document_with_inferential_figures_is_marked_or_cites_the_single_report():
    offenders = [rel for rel, text in quoting_documents() if BANNER not in text[:2000] and REPORT not in text]
    assert offenders == []


def test_the_check_is_not_vacuous():
    assert any(True for _ in quoting_documents())
    assert PATTERN.search('Friedman p = 0,0611') and not PATTERN.search('p = 1')
