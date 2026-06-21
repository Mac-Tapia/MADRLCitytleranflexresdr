# ── 7.2  Lanzar entrenamiento + monitor en paralelo ─────────────────────────
# Usa Popen (no blocking) + bucle de monitoreo: mientras el launcher
# entrena, esta celda muestra snapshots de progreso cada 60 s.
# Si un job falla, imprime diagnostico S1-S3 con instrucciones de relaunch.
LAUNCH_FULL_TRAINING = True

if not LAUNCH_FULL_TRAINING:
    print('LAUNCH_FULL_TRAINING=False — cambia a True para entrenar.')
else:
    import signal as _signal
    import subprocess, sys, threading as _threading, time, json as _json
    from pathlib import Path as _P
    from datetime import datetime as _DT, timezone as _TZ

    _repo    = globals().get('REPO', '/content/MADRLCitytleranflexresdr')
    _mon     = f'{_repo}/CityLearn/scripts/colab_a100_live_monitor.py'
    _python  = globals().get('PROJECT_PYTHON', globals().get('PYTHON', sys.executable))
    _mon_interval = 60          # segundos entre snapshots del monitor
    _poll_sleep   = 5           # segundos entre polls al proceso

    train_cmd = launcher_base_args() + ['--skip-completed']
    print('\n' + '=' * 80)
    print(' '.join(str(c) for c in train_cmd))
    print('=' * 80)

    # Lanzar entrenamiento SIN bloquear (Popen)
    # PIPE + threads -> garantiza que launcher prints lleguen a la celda Colab
    def _pipe_to_cell(pipe):
        for line in pipe:
            sys.stdout.write(line)
            sys.stdout.flush()

    proc = subprocess.Popen(
        train_cmd,
        cwd=_repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    _t_out = _threading.Thread(target=_pipe_to_cell, args=(proc.stdout,), daemon=True)
    _t_err = _threading.Thread(target=_pipe_to_cell, args=(proc.stderr,), daemon=True)
    _t_out.start()
    _t_err.start()

    def _graceful_stop(proc, timeout_sigint=30, timeout_sigkill=10):
        # Detiene el proceso graciosamente: SIGINT -> espera -> SIGKILL.
        if proc.poll() is not None:
            return
        print('\n[7.2] Enviando SIGINT al launcher (checkpoints seran guardados)...')
        try:
            proc.send_signal(_signal.SIGINT)
        except Exception:
            pass
        try:
            proc.wait(timeout=timeout_sigint)
            print(f'[7.2] Launcher detenido (SIGINT) tras {timeout_sigint}s.')
            return
        except subprocess.TimeoutExpired:
            pass
        print(f'[7.2] SIGINT sin respuesta tras {timeout_sigint}s, enviando SIGKILL...')
        try:
            proc.kill()
            proc.wait(timeout=timeout_sigkill)
        except Exception:
            pass

    _last_mon = 0.0
    try:
        while proc.poll() is None:
            _now = time.time()
            if _now - _last_mon >= _mon_interval:
                # ── Monitor snapshot ────────────────────────────────────────
                _ref = _P(_repo) / 'outputs' / 'latest_colab_output_root.txt'
                _out = globals().get('OUTPUT_ROOT', '') or (
                    _ref.read_text(encoding='utf-8').strip()
                    if _ref.exists() else ''
                )
                if _out:
                    try:
                        _mr = subprocess.run(
                            [_python, '-B', _mon,
                             '--output-root', _out,
                             '--once', '--log-tail', '12'],
                            text=True, capture_output=True,
                        )
                        sys.stdout.write(_mr.stdout)
                        sys.stdout.flush()
                        if _mr.stderr.strip():
                            sys.stdout.write('[monitor stderr] ' + _mr.stderr + '
')
                            sys.stdout.flush()
                    except Exception as _em:
                        print(f'[monitor] error: {_em}')
                _last_mon = _now
            time.sleep(_poll_sleep)
    except KeyboardInterrupt:
        print('\n[7.2] Interrumpido — guardando checkpoints antes de detener...')
        _graceful_stop(proc)
        print('[7.2] Para reanudar: en celda 2.1 define RESUME_OUTPUT_ROOT y re-ejecuta 7.2.')
        raise

    _exit = int(proc.returncode or 0)
    if _exit == 0:
        print('\nEntrenamiento COMPLETADO — procede con celda 7.4 / Seccion 8.')
    else:
        # ── Diagnostico automatico al fallar ─────────────────────────────
        print(f'\n[7.2] FALLO (exit={_exit}) — Diagnostico automatico:\n')
        _ref = _P(_repo) / 'outputs' / 'latest_colab_output_root.txt'
        _out = globals().get('OUTPUT_ROOT', '') or (
            _ref.read_text(encoding='utf-8').strip() if _ref.exists() else ''
        )
        if not _out:
            print('  OUTPUT_ROOT desconocido — ejecuta celda 2.1 y reintenta.')
        else:
            # S1 — estado de jobs
            _sp = _P(_out) / 'official_full_status.json'
            if not _sp.exists():
                print(f'  [S1] official_full_status.json NO EXISTE en:\n  {_out}')
            else:
                _s    = _json.loads(_sp.read_text())
                _jobs = _s.get('jobs', [])
                _done = [j for j in _jobs
                         if j.get('exit_code') == 0 and not j.get('skipped')]
                _fail = [j for j in _jobs
                         if j.get('exit_code') not in (None, 0)
                         and not j.get('skipped')]
                print(f'  [S1] status="{_s.get("status")}"  '
                      f'OK={len(_done)}/12  FAIL={len(_fail)}')
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
                    print(f'    {_j.get("name","?").upper():<6}'
                          f' {_j.get("scenario","?"):<3} -> {_st}'
                          f'  attempt={_j.get("attempt",0)}')

            # S2 — live_progress reciente
            _pf = sorted(_P(_out).rglob('live_progress.json'))
            if _pf:
                try:
                    _pg  = _json.loads(_pf[-1].read_text())
                    _ts  = _pg.get('live_status_updated_at', '')
                    _lag = (
                        (_DT.now(_TZ.utc) -
                         _DT.fromisoformat(_ts.replace('Z', '+00:00'))
                         ).total_seconds() if _ts else None
                    )
                    _sig = ('ACTIVO' if _lag is not None and _lag < 120
                            else f'COLGADO ({_lag:.0f}s)' if _lag else '?')
                    print(f'  [S2] {_sig}  '
                          f'{_pg.get("algorithm","?")}/'
                          f'{_pg.get("scenario","?")} '
                          f'ep={_pg.get("episode","?")} '
                          f'step={_pg.get("global_step","?")}')
                except Exception as _e2:
                    print(f'  [S2] live_progress ilegible: {_e2}')

            # S3 — stderr con errores
            _errs = [(p, p.read_text(errors='replace'))
                     for p in sorted(_P(_out).glob('logs/*.stderr.log'))
                     if p.stat().st_size > 0]
            if _errs:
                print(f'  [S3] {len(_errs)} stderr con errores:')
                for _ep, _et in _errs:
                    print(f'    === {_ep.name} ===')
                    print('    ' + '\n    '.join(_et.strip().splitlines()[-20:]))
            else:
                print('  [S3] Sin errores stderr')

            print()
            print('  RELAUNCH: En celda 2.1 establece:')
            print(f'    RESUME_OUTPUT_ROOT = "{_out}"')
            print('  Luego: 1.x setup -> 2.1 -> 6.1 -> 7.2')
        raise RuntimeError(f'Entrenamiento fallo con exit={_exit}')