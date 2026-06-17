#!/usr/bin/env python3
"""Mirror stdin to stdout while writing size-rotated plain-text log files."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def parse_size(value: str) -> int:
    text = value.strip()
    if not text:
        raise ValueError("empty size")
    suffix = text[-1].upper()
    if suffix in {"K", "M", "G"}:
        number = float(text[:-1])
        factor = {"K": 1024, "M": 1024**2, "G": 1024**3}[suffix]
        return int(number * factor)
    return int(text)


def prune_old_logs(prefix: Path, current_index: int, max_files: int) -> None:
    if max_files <= 0:
        return
    first_kept = current_index - max_files + 1
    for index in range(1, max(1, first_kept)):
        candidate = Path(f"{prefix}{index:05d}.log")
        try:
            candidate.unlink()
        except FileNotFoundError:
            pass


def main() -> int:
    if len(sys.argv) != 4:
        print(
            "usage: rotate_training_log.py LOG_PREFIX CHUNK_SIZE MAX_FILES",
            file=sys.stderr,
        )
        return 2

    prefix = Path(sys.argv[1])
    chunk_size = parse_size(sys.argv[2])
    max_files = int(sys.argv[3])
    if chunk_size <= 0:
        raise ValueError("CHUNK_SIZE must be positive")
    if max_files < 0:
        raise ValueError("MAX_FILES must be >= 0")

    prefix.parent.mkdir(parents=True, exist_ok=True)

    index = 1
    current_size = 0
    current_file = None

    def open_next_file():
        nonlocal index, current_size, current_file
        if current_file is not None:
            current_file.close()
        path = Path(f"{prefix}{index:05d}.log")
        current_file = path.open("ab")
        current_size = path.stat().st_size if path.exists() else 0
        prune_old_logs(prefix, index, max_files)
        index += 1

    open_next_file()

    try:
        while True:
            data = sys.stdin.buffer.read(64 * 1024)
            if not data:
                break

            try:
                sys.stdout.buffer.write(data)
                sys.stdout.buffer.flush()
            except BrokenPipeError:
                os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())

            offset = 0
            while offset < len(data):
                remaining = chunk_size - current_size
                if remaining <= 0:
                    open_next_file()
                    remaining = chunk_size
                piece = data[offset : offset + remaining]
                current_file.write(piece)
                current_file.flush()
                current_size += len(piece)
                offset += len(piece)
    finally:
        if current_file is not None:
            current_file.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
