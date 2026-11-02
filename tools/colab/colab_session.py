"""Colab-kernel helpers of the modular notebook (standard library only).

Interfaces of docs/plans/cuaderno_colab.md, Tarea 1 (plan under owner review):
the notebook cells stay thin and this module, shipped at the root of the overlay
zip, applies the bundle, verifies the checkout and runs the project CLI as
streamed subprocesses whose refusal JSON is always visible.
"""
from __future__ import annotations

import hashlib
import json
import stat
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Callable, Dict, List, Optional, Sequence
import zipfile

MANIFEST_NAME = 'colab_bundle_manifest.json'
SESSION_NAME = 'colab_session.py'


def _unsafe(name: str) -> bool:
    posix, windows = PurePosixPath(name), PureWindowsPath(name)
    return (posix.is_absolute() or windows.is_absolute() or bool(windows.drive)
            or '..' in posix.parts or '..' in windows.parts)


def _is_link(entry: zipfile.ZipInfo) -> bool:
    return stat.S_ISLNK(entry.external_attr >> 16)


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _in_scope(relative: str, manifest: Dict[str, object]) -> bool:
    """Same rule as preflight.fresh_source_paths: scope prefixes, source suffixes, configs JSON."""
    scope = manifest.get('source_scope') or []
    suffixes = manifest.get('source_suffixes')
    parts = PurePosixPath(relative).parts
    if '__pycache__' in parts or '.git' in parts:
        return False
    if relative in scope:
        return True
    prefix = next((item for item in scope if relative.startswith(item.rstrip('/') + '/')), None)
    if prefix is None:
        return False
    if suffixes is None:
        return True
    suffix = PurePosixPath(relative).suffix
    return suffix in suffixes or (suffix == '.json' and prefix in (manifest.get('source_json_prefixes') or []))


def apply_overlay(bundle: zipfile.ZipFile, project_root: Path) -> Dict[str, object]:
    """Write the bundle into the checkout and remove in-scope files the bundle does not carry."""
    project_root = Path(project_root).resolve()
    manifest = json.loads(bundle.read(MANIFEST_NAME))
    entries = []
    for entry in bundle.infolist():
        if _unsafe(entry.filename):
            raise ValueError(f'unsafe path in the bundle: {entry.filename}')
        if _is_link(entry):
            raise ValueError(f'symbolic link in the bundle: {entry.filename}')
        target = (project_root/entry.filename).resolve()
        if project_root not in target.parents:
            raise ValueError(f'path escapes the checkout: {entry.filename}')
        entries.append((entry, target))
    written = 0
    for entry, target in entries:
        if entry.is_dir() or entry.filename in (MANIFEST_NAME, SESSION_NAME):
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(bundle.read(entry))
        written += 1
    files, removed = manifest.get('files') or {}, []
    for path in sorted(p for p in project_root.rglob('*') if p.is_file() and '.git' not in p.parts):
        relative = path.relative_to(project_root).as_posix()
        if _in_scope(relative, manifest) and relative not in files:
            path.unlink()
            removed.append(relative)
    return {'written': written, 'removed': removed}


def _git(project_root: Path, *args: str) -> str:
    return subprocess.check_output(['git', *args], cwd=project_root, text=True).strip()


def verify_checkout(project_root: Path, manifest: Dict[str, object], *, origin: str) -> List[str]:
    """Reasons the checkout differs from the bundle; an empty list means accepted."""
    project_root = Path(project_root)
    reasons = []
    if _git(project_root, 'remote', 'get-url', 'origin') != origin:
        reasons.append('origin_mismatch')
    if _git(project_root, 'rev-parse', 'HEAD') != manifest.get('commit'):
        reasons.append('head_mismatch')
    actual = {}
    for line in _git(project_root, 'submodule', 'status').splitlines():
        fields = line.strip().lstrip('+-U').split()
        if len(fields) >= 2:
            actual[fields[1]] = fields[0]
    for path, commit in sorted((manifest.get('submodules') or {}).items()):
        if actual.get(path) != commit:
            reasons.append(f'submodule_mismatch:{path}')
    files = manifest.get('files') or {}
    for relative, digest in sorted(files.items()):
        path = project_root/relative
        if not path.is_file() or _sha256(path) != digest:
            reasons.append(f'file_mismatch:{relative}')
    for path in sorted(p for p in project_root.rglob('*') if p.is_file() and '.git' not in p.parts):
        relative = path.relative_to(project_root).as_posix()
        if _in_scope(relative, manifest) and relative not in files:
            reasons.append(f'extra_file:{relative}')
    return reasons


def project_python(project_root: Path, chosen: Optional[str]) -> Path:
    """The project Python 3.9 prepared by the installation cell (never another interpreter)."""
    candidate = Path(chosen) if chosen else Path(project_root)/'.venv39-citylearn-v3/bin/python'
    if not candidate.is_file():
        raise FileNotFoundError(f'project Python not found: {candidate}; run the installation cell first')
    return candidate


def drive_root(base: Path, alias: str, campaign_id: str) -> Path:
    """One Drive folder per campaign: two campaigns with the same alias never share attempts."""
    return Path(base)/alias/campaign_id/'outputs'


@dataclass(frozen=True)
class CliResult:
    returncode: int
    report: Optional[dict]
    tail: str


class CliRefused(RuntimeError):
    def __init__(self, returncode: int, report: Optional[dict], tail: str):
        reason = (report or {}).get('status') or (report or {}).get('reason')
        super().__init__(f'CLI exit {returncode}: {reason or "see output"}')
        self.returncode, self.report, self.tail = returncode, report, tail


def _last_json(lines: Sequence[str]) -> Optional[dict]:
    for line in reversed(lines):
        line = line.strip()
        if line.startswith('{'):
            try:
                return json.loads(line)
            except ValueError:
                continue
    return None


def _stream(child: subprocess.Popen, on_line: Callable[[str], object], keep: List[str]) -> int:
    for line in child.stdout:
        keep.append(line)
        del keep[:-200]
        on_line(line.rstrip('\n'))
    return child.wait()


def _stop(child: subprocess.Popen) -> None:
    if child.poll() is None:
        child.terminate()
        try:
            child.wait(timeout=30)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()


def run_cli(argv: Sequence[str], *, cwd: Path, on_line=print, allowed=(0,)) -> CliResult:
    """Run a CLI streaming every line; the last JSON line is the report. Refusals raise CliRefused."""
    child = subprocess.Popen(list(argv), cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, bufsize=1)
    lines: List[str] = []
    try:
        returncode = _stream(child, on_line, lines)
    finally:
        _stop(child)
    result = CliResult(returncode, _last_json(lines), ''.join(lines)[-4000:])
    if returncode not in allowed:
        raise CliRefused(returncode, result.report, result.tail)
    return result


def run_stage_with_sync(stage_argv: Sequence[str], sync_argv: Sequence[str], *, cwd: Path,
                        interval_seconds: int = 60, on_line=print, allowed=(0,)) -> CliResult:
    """Run a stage while finished attempts are synced; always stops the child and syncs a last time."""
    stop = threading.Event()

    def sync():
        subprocess.run(list(sync_argv), cwd=cwd, capture_output=True, text=True)

    def keep_syncing():
        while not stop.wait(interval_seconds):
            sync()
    syncer = threading.Thread(target=keep_syncing, daemon=True)
    syncer.start()
    child = subprocess.Popen(list(stage_argv), cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, bufsize=1)
    lines: List[str] = []
    try:
        returncode = _stream(child, on_line, lines)
    finally:
        _stop(child)
        stop.set()
        syncer.join()
        sync()
    result = CliResult(returncode, _last_json(lines), ''.join(lines)[-4000:])
    if returncode not in allowed:
        raise CliRefused(returncode, result.report, result.tail)
    return result


def phase_plan_lines(report: Optional[dict], stage: str) -> List[str]:
    """Display of `cli --stage prepare`: measured resources and the phase table of one stage, as given.

    Phases are labelled by their algorithms, never by a number: run_stage skips the empty
    phases of a stage, so a position would not match the campaign phase number.
    """
    report = report or {}
    plan = (report.get('phase_plan') or {}).get(stage)
    if plan is None:
        return [f'El JSON de prepare no trae phase_plan para {stage}']
    measured = report.get('measured_resources') or {}
    lines = ['Recursos medidos: ' + ', '.join(f'{k}={v}' for k, v in measured.items()),
             f"Fases de entrenamiento de la campaña: {report.get('training_phases')}", f'Plan de la etapa {stage}:']
    for phase in plan:
        lines.append(f"  Fase {phase.get('algorithms')}: treatments={phase.get('treatments')} "
                     f"T={phase.get('episode_time_steps')} workers={phase.get('workers')} "
                     f"razones={phase.get('reasons') or []} límites={phase.get('bounds')}")
        if phase.get('workers') == 0:
            lines.append(f"    NO correrá en este runtime: {phase.get('reasons') or []}")
    return lines


def stopped_phase_label(report: Optional[dict]) -> Optional[str]:
    """Algorithms of the phase where the stage stopped (stopped_at_phase indexes report['phases'])."""
    report = report or {}
    index, phases = report.get('stopped_at_phase'), report.get('phases') or []
    if index is None or not isinstance(index, int) or not 0 <= index < len(phases):
        return None
    return str(phases[index].get('algorithms'))


def stage_result_lines(report: Optional[dict], stage_result: Optional[dict] = None) -> List[str]:
    """Display of the final `--execute` JSON and the treatments of the stage result that hold an error."""
    report = report or {}
    stopped = stopped_phase_label(report)
    lines = [f"Estado={report.get('status')}" + (f'; se detuvo en la fase {stopped}' if stopped else '')]
    for phase in report.get('phases') or []:
        lines.append(f"  Fase {phase.get('algorithms')}: workers={phase.get('workers')} "
                     f"failed={phase.get('failed')}")
    for treatment in (stage_result or {}).get('treatments') or []:
        if treatment.get('error'):
            lines.append(f"  ERROR {treatment.get('treatment_id')}: {treatment['error']}")
    return lines
