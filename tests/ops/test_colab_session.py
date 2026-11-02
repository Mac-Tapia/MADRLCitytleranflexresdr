"""tools/colab/colab_session.py (docs/plans/cuaderno_colab.md, Tarea 1; plan under review)."""
import hashlib
import io
import json
import stat
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO/'tools/colab'))

import colab_session as cs  # noqa: E402


def _zip(members, manifest):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as bundle:
        bundle.writestr(cs.MANIFEST_NAME, json.dumps(manifest))
        for name, data, mode in members:
            info = zipfile.ZipInfo(name)
            if mode is not None:
                info.external_attr = mode << 16
            bundle.writestr(info, data)
    buffer.seek(0)
    return zipfile.ZipFile(buffer)


@pytest.mark.parametrize('name', ['/x', '../x', 'C:/x'])
def test_overlay_refuses_absolute_parent_drive_and_symlink_members(tmp_path, name):
    with pytest.raises(ValueError):
        cs.apply_overlay(_zip([(name, b'x', None)], {}), tmp_path/'root')
    link = _zip([('uc3m/link', b'/etc/passwd', stat.S_IFLNK | 0o777)], {})
    with pytest.raises(ValueError):
        cs.apply_overlay(link, tmp_path/'root')
    assert not (tmp_path/'x').exists()


def test_overlay_removes_stale_files_in_scope(tmp_path):
    root = tmp_path/'root'
    (root/'uc3m').mkdir(parents=True)
    (root/'docs').mkdir()
    (root/'uc3m/viejo.py').write_text('old', encoding='utf-8')
    (root/'docs/keep.md').write_text('keep', encoding='utf-8')
    manifest = {'source_scope': ['uc3m'], 'files': {'uc3m/a.py': hashlib.sha256(b'new').hexdigest()}}
    result = cs.apply_overlay(_zip([('uc3m/a.py', b'new', None)], manifest), root)
    assert result['removed'] == ['uc3m/viejo.py'] and result['written'] == 1
    assert (root/'docs/keep.md').is_file() and (root/'uc3m/a.py').read_bytes() == b'new'


def test_verify_checkout_reports_each_mismatch(tmp_path):
    root = tmp_path/'repo'
    root.mkdir()
    git = lambda *a: subprocess.run(['git', *a], cwd=root, check=True, capture_output=True, text=True)  # noqa: E731
    git('init', '-q')
    git('config', 'user.email', 't@example.invalid')
    git('config', 'user.name', 't')
    git('remote', 'add', 'origin', 'https://example.invalid/repo.git')
    (root/'uc3m').mkdir()
    (root/'uc3m/a.py').write_text('a', encoding='utf-8')
    git('add', '.')
    git('commit', '-qm', 'init')
    manifest = {'commit': '0'*40, 'submodules': {'CityLearn': '1'*40}, 'source_scope': ['uc3m'],
                'files': {'uc3m/a.py': hashlib.sha256(b'other').hexdigest()}}
    reasons = cs.verify_checkout(root, manifest, origin='https://example.invalid/repo.git')
    assert reasons == ['head_mismatch', 'submodule_mismatch:CityLearn', 'file_mismatch:uc3m/a.py']


def _script(tmp_path, body):
    path = tmp_path/'script.py'
    path.write_text(body, encoding='utf-8')
    return [sys.executable, str(path)]


def test_run_cli_surfaces_json_reason(tmp_path):
    argv = _script(tmp_path, 'import json, sys\nprint(json.dumps({"status": "campaign_inputs_changed", '
                             '"reasons": ["config_changed"]}))\nsys.exit(2)\n')
    with pytest.raises(cs.CliRefused) as refused:
        cs.run_cli(argv, cwd=tmp_path, on_line=lambda line: None)
    assert refused.value.returncode == 2 and refused.value.report['reasons'] == ['config_changed']


def test_run_cli_streams_lines(tmp_path):
    seen = []
    result = cs.run_cli(_script(tmp_path, 'for i in range(3):\n    print(i, flush=True)\n'), cwd=tmp_path,
                        on_line=seen.append)
    assert seen == ['0', '1', '2'] and result.returncode == 0


def test_c6_interrupt_terminates_child_and_syncs(tmp_path):
    marker = tmp_path/'synced.txt'
    stage = _script(tmp_path, 'import time\nprint("start", flush=True)\ntime.sleep(60)\n')
    sync_script = tmp_path/'sync.py'
    sync_script.write_text(f'open({str(marker)!r}, "a").write("x")\n', encoding='utf-8')

    def interrupt(line):
        raise KeyboardInterrupt
    with pytest.raises(KeyboardInterrupt):
        cs.run_stage_with_sync(stage, [sys.executable, str(sync_script)], cwd=tmp_path, interval_seconds=3600,
                               on_line=interrupt)
    assert marker.read_text() == 'x'                     # one final sync even when interrupted


def test_drive_root_includes_campaign_id():
    assert cs.drive_root(Path('/d'), 'iquitos_v2', 'fresh_x_v1') == Path('/d/iquitos_v2/fresh_x_v1/outputs')


PREPARE = {'status': 'prepared_not_executed', 'budget': {}, 'training_phases': [['MASAC'], ['HAPPO', 'MATD3', 'MAAC']],
           'measured_resources': {'ram_gib': 83.5, 'vram_gib': 74.5, 'cpu_count': 12},
           'phase_plan': {'pilot': [
               {'algorithms': ['MASAC'], 'treatments': 1, 'episode_time_steps': 8760, 'workers': 0,
                'reasons': ['insufficient_resources:MASAC:vram'], 'bounds': {'cpu': 11, 'ram': 1, 'vram': 0}},
               {'algorithms': ['HAPPO', 'MATD3', 'MAAC'], 'treatments': 3, 'episode_time_steps': 8760, 'workers': 2,
                'reasons': [], 'bounds': {'cpu': 11, 'ram': 2, 'vram': 18}}]}}


def test_phase_plan_lines_show_resources_table_and_zero_worker_reasons():
    lines = cs.phase_plan_lines(PREPARE, 'pilot')
    text = '\n'.join(lines)
    assert 'ram_gib=83.5' in text and 'vram_gib=74.5' in text and 'cpu_count=12' in text
    assert "[['MASAC'], ['HAPPO', 'MATD3', 'MAAC']]" in text
    assert any('MASAC' in line and 'workers=0' in line and 'insufficient_resources:MASAC:vram' in line for line in lines)
    assert any('HAPPO' in line and 'treatments=3' in line and 'workers=2' in line for line in lines)
    assert any('NO correrá' in line for line in lines)
    assert cs.phase_plan_lines({'status': 'prepared_not_executed'}, 'pilot') == [
        'El JSON de prepare no trae phase_plan para pilot']


def test_stage_result_lines_show_phases_stop_and_errored_treatments():
    final = {'stage': 'pilot', 'status': 'insufficient_resources', 'stopped_at_phase': 0,
             'phases': [{'algorithms': ['MASAC'], 'workers': 0, 'failed': 0}], 'phase_plan': PREPARE['phase_plan']['pilot']}
    stage_result = {'treatments': [{'treatment_id': 'pilot/masac/e1/seed_901', 'error': 'KeyError: x'},
                                   {'treatment_id': 'pilot/happo/e1/seed_901', 'training_complete': True}]}
    text = '\n'.join(cs.stage_result_lines(final, stage_result))
    assert "se detuvo en la fase ['MASAC']" in text and 'workers=0' in text
    assert 'pilot/masac/e1/seed_901' in text and 'KeyError: x' in text
    assert 'pilot/happo/e1/seed_901' not in text


def test_phases_are_labelled_by_algorithms_when_the_first_phase_is_empty():
    # sensitivity has only MATD3: the campaign phase 1 (MASAC) is empty and run_stage skips it, so
    # stopped_at_phase=0 indexes the non-empty phases and must not read as "phase 1".
    plan = {'measured_resources': {'ram_gib': 30.0}, 'training_phases': [['MASAC'], ['HAPPO', 'MATD3', 'MAAC']],
            'phase_plan': {'sensitivity': [
                {'algorithms': ['MATD3'], 'treatments': 6, 'episode_time_steps': 8760, 'workers': 0,
                 'reasons': ['insufficient_resources:MATD3:ram'], 'bounds': {'ram': 0}}]}}
    table = '\n'.join(cs.phase_plan_lines(plan, 'sensitivity'))
    assert "Fase ['MATD3']" in table and 'Fase 1' not in table
    final = {'status': 'insufficient_resources', 'stopped_at_phase': 0,
             'phases': [{'algorithms': ['MATD3'], 'workers': 0, 'failed': 0}]}
    lines = '\n'.join(cs.stage_result_lines(final))
    assert "se detuvo en la fase ['MATD3']" in lines
    assert 'stopped_at_phase=0' not in lines and 'Fase 1' not in lines
    assert cs.stopped_phase_label(final) == "['MATD3']"
    assert cs.stopped_phase_label({'stopped_at_phase': None, 'phases': []}) is None
