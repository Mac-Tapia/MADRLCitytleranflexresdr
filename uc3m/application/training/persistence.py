"""Local persistence primitives; no cloud mounts or background global state."""
from __future__ import annotations

import csv
import io
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence


def _atomic(path: Path, text: str, *, fsync: bool = True) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='',
                                         dir=path.parent, suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(text)
            stream.flush()
            if fsync:
                os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def write_json_atomic(path: Path, data: Mapping[str, Any], *, fsync: bool = True) -> None:
    _atomic(path, json.dumps(data, indent=2, sort_keys=True, default=str), fsync=fsync)


def _csv_safe(value):
    if value is None:
        return ''
    if isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, 'item'):
        return value.item()
    return json.dumps(value, sort_keys=True, default=str)


def write_csv_atomic(path: Path, rows: Sequence[Mapping[str, Any]], *, fsync: bool = True) -> None:
    fields = sorted({key for row in rows for key in row})
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    for row in rows:
        writer.writerow({key: _csv_safe(row.get(key)) for key in fields})
    _atomic(path, stream.getvalue(), fsync=fsync)


def append_csv_stable_schema(path: Path, rows: Sequence[Mapping[str, Any]],
                             fieldnames: Sequence[str], *, fsync: bool = False) -> None:
    if not rows:
        return
    fields = list(fieldnames)
    if len(set(fields)) != len(fields) or any(set(row) - set(fields) for row in rows):
        raise ValueError('CSV schema drift: unexpected columns')
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    header_needed = not path.exists() or path.stat().st_size == 0
    if not header_needed:
        with path.open(newline='', encoding='utf-8') as stream:
            if next(csv.reader(stream), None) != fields:
                raise ValueError('CSV schema drift: header differs')
    with path.open('a', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        if header_needed:
            writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_safe(row.get(key)) for key in fields})
        stream.flush()
        if fsync:
            os.fsync(stream.fileno())


class ProgressHeartbeat:
    """Explicit snapshots; caller owns scheduling and lifecycle."""
    def __init__(self, path: Path):
        self.path = Path(path)

    def update(self, **progress) -> None:
        write_json_atomic(self.path, progress)
