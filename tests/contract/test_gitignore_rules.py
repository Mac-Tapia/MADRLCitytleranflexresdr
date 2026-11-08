"""SPEC-008 FR-008.4 and SPEC-012 FR-012.3: temporaries and bulky outputs stay out of Git, manifests and promoted
evidence stay in."""
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]


def _ignored(path: str) -> bool:
    result = subprocess.run(['git', 'check-ignore', '-q', '--no-index', path], cwd=REPO)
    assert result.returncode in (0, 1), path
    return result.returncode == 0


@pytest.mark.parametrize('path', ['outputs/x/source_snapshot.zip', 'a.tmp', 'tools/b.tmp', 'outputs/_tmp_x',
                                  '_tmp_y/file.txt', '.codex_tmp/z', 'docs/~$tesis.docx',
                                  'data/validation/cubems/raw/2018Floor1.csv'])
def test_temporaries_and_raw_files_are_ignored(path):
    assert _ignored(path), path


@pytest.mark.parametrize('path', ['outputs/campaigns/x/campaign_manifest.json',
                                  'data/campaigns/iquitos_v6_trial7/dataset_acceptance.json',
                                  'data/campaigns/iquitos_v6_trial7/split_manifest.json',
                                  'data/validation/cubems/validation_5r1c.json',
                                  'data/audits/repository_hygiene_manifest.json'])
def test_manifests_and_promoted_evidence_are_not_ignored(path):
    assert not _ignored(path), path
