"""Build the I13 per-file review ledgers for the shared Revisor A / Revisor B audit.

Each reviewer owns exactly one ledger file (one writer per file). Re-running
keeps review columns already filled for paths whose sha256 is unchanged.
"""
import csv
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
EXTERNAL = ('CityLearn/', 'external/', 'docs/audits/', 'data/', 'outputs/', 'results/')
TEXT_EXT = {'.py', '.ps1', '.sh', '.md', '.yaml', '.yml', '.toml', '.json', '.ipynb', '.cfg',
            '.ini', '.txt', '.tf', '.conf', '.csv', '.html', '.js', '.css'}
TEXT_NAMES = {'Dockerfile', '.gitignore', '.gitattributes', '.gitmodules', '.dockerignore'}
LOTS = [('L1', ('uc3m/', 'configs/')), ('L2', ('scripts/', 'tools/')), ('L3', ('tests/',)),
        ('L4', ('docs/', 'specs/'))]
LOT_OWNER = {'L1': 'revisor_a', 'L2': 'revisor_b', 'L3': 'revisor_a', 'L4': 'revisor_b', 'L5': 'revisor_a'}
# Files the Revisor A wrote at this cut: always reviewed by the Revisor B.
AUTHORED_BY_A = ('tools/skills/task-coordination-strategies/', 'tools/skills/registry.yaml',
                   '.gitattributes', 'docs/plans/remediacion_integrada.md',
                   'docs/plans/remediacion_integrada.json', 'docs/architecture/AGENT_HARNESS.md')
REVIEW = ['rol', 'consumidores', 'hallazgos', 'pruebas', 'estado_revision', 'revisado_utc']
HEAD = ['ruta', 'lote', 'lineas', 'sha256', 'estado_git', 'motivo_revisor'] + REVIEW


def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, capture_output=True, text=True,
                          encoding='utf-8', check=True).stdout


def lot(path):
    for name, prefixes in LOTS:
        if path.startswith(prefixes):
            return name
    return 'L5'


def reviewer(path, name, dirty):
    if path.startswith(AUTHORED_BY_A):
        return 'revisor_b', 'escrito por el Revisor A en este corte'
    if dirty:
        return 'revisor_a', 'cambio en curso del Revisor B'
    return LOT_OWNER[name], 'lote asignado'


def main():
    submodules = {line.split()[1] + '/' for line in git('submodule', 'status').splitlines() if line.strip()}
    status = {}
    for line in git('status', '--porcelain', '--untracked-files=all').splitlines():
        status[line[3:].strip('"')] = line[:2].strip() or 'M'
    tracked = set(git('ls-files').splitlines()) | {p for p, s in status.items() if s == '??'}
    rows = {'revisor_a': [], 'revisor_b': []}
    for path in sorted(tracked):
        p = ROOT / path
        if path.startswith(EXTERNAL) or path.startswith(tuple(submodules)) or not p.is_file():
            continue
        if p.suffix.lower() not in TEXT_EXT and p.name not in TEXT_NAMES:
            continue
        data = p.read_bytes()
        name = lot(path)
        who, why = reviewer(path, name, path in status)
        rows[who].append(dict(ruta=path, lote=name, lineas=data.count(b'\n') + (not data.endswith(b'\n') and bool(data)),
                              sha256=hashlib.sha256(data).hexdigest(), estado_git=status.get(path, 'limpio'),
                              motivo_revisor=why, estado_revision='pendiente'))
    for who, items in rows.items():
        target = OUT / f'ledger_{who}.csv'
        previous = {}
        if target.exists():
            with target.open(encoding='utf-8', newline='') as fh:
                previous = {r['ruta']: r for r in csv.DictReader(fh)}
        for row in items:
            old = previous.get(row['ruta'])
            if old and old['sha256'] == row['sha256']:
                row.update({k: old[k] for k in REVIEW})
        with target.open('w', encoding='utf-8', newline='') as fh:
            writer = csv.DictWriter(fh, HEAD, lineterminator='\n')
            writer.writeheader()
            writer.writerows(items)
    summary = {who: {} for who in rows}
    for who, items in rows.items():
        for row in items:
            cell = summary[who].setdefault(row['lote'], [0, 0])
            cell[0] += 1
            cell[1] += row['lineas']
    for who in summary:
        print(who, {k: f'{v[0]} archivos/{v[1]} líneas' for k, v in sorted(summary[who].items())})
    return 0


if __name__ == '__main__':
    sys.exit(main())
