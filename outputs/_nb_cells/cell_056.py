# ── 7.5  Diagnostico de Drive + senales de problema + relaunch ──────────────
import json
import sys
import os
from pathlib import Path
from datetime import datetime, timezone

_repo = globals().get('REPO', '/content/MADRLCitytleranflexresdr')

# Auto-descubrir OUTPUT_ROOT aunque se haya reiniciado el kernel.
# Usa el helper de 7.0 si existe; si no, fallback autocontenido.
if 'resolve_output_root_or_latest' in globals():
    _out = resolve_output_root_or_latest()
else:
    _ref = Path(_repo) / 'outputs' / 'latest_colab_output_root.txt'
    _out = globals().get('OUTPUT_ROOT', '') or (
        _ref.read_text(encoding='utf-8').strip() if _ref.exists() else ''
    )
if not _out:
    print('[DIAG] ERROR: OUTPUT_ROOT desconocido.')
    print('  Opcion A: ejecuta celda 2.1 primero.')
    print('  Opcion B: define manualmente:')
    print('    _out = "/content/drive/MyDrive/MADRLCitytleranflexresdr/outputs/madrl_v3_YYYYMMDD_HHMMSS"')
    _out = None

if _out:
    print(f'OUTPUT_ROOT = {_out}')
    print()

    # ── SENAL 1: official_full_status.json existe? ───────────────────────────
    status_path = Path(_out) / 'official_full_status.json'
    if not status_path.exists():
        print('[SENAL 1] FAIL  official_full_status.json NO EXISTE')
        print('         El launcher no arranco o Drive no esta montado.')
        print(f'         Ruta esperada: {status_path}')
    else:
        with open(status_path) as _f:
            _s = json.load(_f)
        _jobs   = _s.get('jobs', [])
        _failed = [j for j in _jobs
                   if j.get('exit_code') not in (None, 0) and not j.get('skipped')]
        _active = [j for j in _jobs
                   if j.get('completed_at') is None
                   and not j.get('planned_only') and not j.get('skipped')]
        _done   = [j for j in _jobs
                   if j.get('exit_code') == 0 and not j.get('skipped')]

        _status_str = _s.get('status', '?')
        print(f'[SENAL 1] OK    status="{_status_str}"  '
              f'completados={len(_done)}/12  fallidos={len(_failed)}  '
              f'activos={len(_active)}')
        for _j in _jobs:
            if _j.get('planned_only'):
                continue
            if _j.get('skipped'):
                _st = 'SKIP'
            elif _j.get('exit_code') == 0:
                _st = 'OK  '
            elif _j.get('completed_at') is None:
                _st = 'RUN '
            else:
                _st = 'FAIL'
            _name = _j.get('name', '?').upper()
            _scen = _j.get('scenario', '?')
            _att  = _j.get('attempt', 0)
            print(f'  {_name:<6} {_scen:<3} -> {_st}  attempt={_att}')
        print()

        # ── SENAL 2: live_progress.json reciente? ────────────────────────────
        _pfiles = sorted(Path(_out).rglob('live_progress.json'))
        if _pfiles:
            _pf = _pfiles[-1]
            try:
                _prog = json.loads(_pf.read_text())
                _ts   = _prog.get('live_status_updated_at', '')
                _step = _prog.get('global_step', '?')
                _algo = _prog.get('algorithm', '?')
                _scen = _prog.get('scenario', '?')
                _ep   = _prog.get('episode', '?')
                if _ts:
                    _dt  = datetime.fromisoformat(_ts.replace('Z', '+00:00'))
                    _lag = (datetime.now(timezone.utc) - _dt).total_seconds()
                    if _lag < 120:
                        _sig = 'OK  ACTIVO'
                    else:
                        _sig = f'WARN COLGADO ({_lag:.0f}s sin actualizar)'
                else:
                    _lag, _sig = 0, '? sin timestamp'
                print(f'[SENAL 2] {_sig} -- {_algo}/{_scen} ep={_ep} step={_step}')
                print(f'          {_pf.relative_to(Path(_out))}')
            except Exception as _e:
                print(f'[SENAL 2] WARN live_progress.json ilegible: {_e}')
        else:
            print('[SENAL 2] INFO  Sin live_progress.json aun '
                  '(primer job en inicializacion o training no ha arrancado)')
        print()

        # ── SENAL 3: stderr con errores? ─────────────────────────────────────
        _errs = sorted(Path(_out).glob('logs/*.stderr.log'))
        _bad  = [(p, p.read_text(errors='replace'))
                 for p in _errs if p.stat().st_size > 0]
        if _bad:
            print(f'[SENAL 3] FAIL  {len(_bad)} archivo(s) stderr con contenido:')
            for _p, _txt in _bad:
                print(f'  === {_p.name} ===')
                _lines = _txt.strip().splitlines()
                print('  ' + '\n  '.join(_lines[-25:]))
        else:
            print(f'[SENAL 3] OK    Sin errores stderr '
                  f'({len(_errs)} logs revisados)')
        print()

        # ── SENAL 4: artefactos generados ────────────────────────────────────
        _nres  = len(list(Path(_out).rglob('results.json')))
        _nckpt = len(list(Path(_out).rglob('*.pt')))
        _ncsv  = len(list(Path(_out).rglob('*.csv')))
        _nlogs = len(list(Path(_out).glob('logs/*.log')))
        print(f'[SENAL 4] Artefactos en Drive: '
              f'results.json={_nres}/12  checkpoints={_nckpt}  '
              f'CSVs={_ncsv}  logs={_nlogs}')
        print()

        # ── Instrucciones de relaunch si hay problemas ────────────────────────
        _needs_relaunch = _failed or _s.get('status') in ('failed', 'running')
        if _needs_relaunch:
            print('=' * 72)
            print('RELAUNCH RECOMENDADO')
            print('  --skip-completed reanuda automaticamente los jobs ya completados.')
            print('  Pasos:')
            print('    1. En celda 2.1 establece RESUME_OUTPUT_ROOT:')
            print(f'       RESUME_OUTPUT_ROOT = "{_out}"')
            print('    2. Ejecuta las celdas en orden: 1.x setup -> 2.1 -> 6.1 -> 7.2')
        elif _s.get('status') == 'completed':
            print('El entrenamiento esta COMPLETO. Procede con la Seccion 8 (analisis).')
        else:
            print('Entrenamiento en curso. Vuelve a ejecutar esta celda para actualizar.')
