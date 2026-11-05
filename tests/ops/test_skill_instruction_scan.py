"""The root guard scans instruction sources without entering browser state."""
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_skill_scan_prunes_runtime_before_enumeration(tmp_path):
    skill = tmp_path/'skills/example'
    skill.mkdir(parents=True)
    (skill/'SKILL.md').write_text('local instructions', encoding='utf-8')
    (skill/'check.py').write_text('pass\n', encoding='utf-8')
    private = tmp_path/'skills/notebooklm-mcp/data'
    private.mkdir(parents=True)
    (private/'auth_info.json').write_text('{"synthetic": true}', encoding='utf-8')
    script = (ROOT/'scripts/quality/skill_instruction_paths.ps1').as_posix().replace("'", "''")
    scan_root = (tmp_path/'skills').as_posix().replace("'", "''")
    command = f". '{script}'; @(Get-LocalSkillInstructionFiles -Root '{scan_root}' | ForEach-Object {{ $_.FullName }}) | ConvertTo-Json -Compress"
    result = subprocess.run(['powershell', '-NoProfile', '-Command', command],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    names = {Path(p).relative_to(tmp_path/'skills').as_posix() for p in json.loads(result.stdout)}
    assert names == {'example/SKILL.md', 'example/check.py'}
