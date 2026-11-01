"""Validate canonical local skills without importing or executing their helpers."""
import hashlib
import argparse
import json
import re
from pathlib import Path

import yaml


def validate_skill(path):
    path = Path(path)
    errors = []
    entry = path / "SKILL.md"
    if not entry.is_file():
        return [f"{path.name}: missing SKILL.md"]
    text = entry.read_text(encoding="utf-8-sig")
    match = re.match(r"\A---\s*\n(.*?)\n---", text, re.S)
    try:
        header = yaml.safe_load(match.group(1)) if match else {}
        if not isinstance(header, dict):
            header = {}
    except yaml.YAMLError:
        header = {}
    if header.get("name") != path.name:
        errors.append(f"{path.name}: name must match folder")
    if not header.get("description"):
        errors.append(f"{path.name}: missing description")
    if not any((path / name).is_file() for name in ("LICENSE", "LICENSE.txt")):
        errors.append(f"{path.name}: missing license notice")
    return errors


def validate_registry(root, registry=None):
    root = Path(root).resolve()
    if registry is None:
        registry = yaml.safe_load((root / "tools/skills/registry.yaml").read_text(encoding="utf-8"))
    errors, names = [], set()
    records = registry.get("skills", []) if isinstance(registry, dict) else []
    if not isinstance(records, list) or not records:
        errors.append("skill inventory must be a non-empty list")
        records = []
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("name"), str) or not isinstance(record.get("path"), str):
            errors.append("invalid skill record")
            continue
        name = record["name"]
        if name in names:
            errors.append(f"duplicate skill: {name}")
        names.add(name)
        folder = (root / record["path"]).resolve()
        if root not in folder.parents:
            errors.append(f"{name}: path outside repository")
            continue
        if folder != (root / "tools/skills" / name).resolve():
            errors.append(f"{name}: non-canonical skill path")
        if record.get("license") not in {"MIT", "Apache-2.0"}:
            errors.append(f"{name}: license not approved")
        errors.extend(validate_skill(folder))
        hashes = record.get("sha256")
        if not isinstance(hashes, dict) or not hashes:
            errors.append(f"{name}: missing file hashes")
            hashes = {}
        actual_files = {
            file.relative_to(folder).as_posix()
            for file in folder.rglob("*")
            if file.is_file() and "__pycache__" not in file.parts and file.suffix != ".pyc"
        }
        if set(hashes) != actual_files:
            errors.append(f"{name}: hash coverage differs from distributed files")
        for relative, expected in hashes.items():
            file = (folder / relative).resolve()
            if folder not in file.parents or not file.is_file():
                errors.append(f"{name}: missing or outside hash file {relative}")
            elif hashlib.sha256(file.read_bytes()).hexdigest() != expected:
                errors.append(f"{name}: hash mismatch {relative}")
    canonical = root / "tools/skills"
    discovered = {folder.name for folder in canonical.iterdir()
                  if folder.is_dir() and (folder / "SKILL.md").is_file()} if canonical.is_dir() else set()
    for name in sorted(discovered - names):
        errors.append(f"unregistered canonical skill: {name}")
    return errors


def validate_discovery(surface, expected):
    surface = Path(surface)
    errors = []
    found = {entry.name: entry for entry in surface.iterdir()} if surface.is_dir() else {}
    for name in sorted(set(found) - set(expected)):
        errors.append(f"unexpected discovery entry: {surface.name}/{name}")
    for name, target in expected.items():
        if name not in found:
            errors.append(f"missing discovery entry: {name}")
        elif found[name].resolve() != Path(target).resolve():
            errors.append(f"wrong discovery target: {name}")
    return errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", action="store_true")
    parser.add_argument("--check-discovery", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    failures = validate_registry(root)
    records = yaml.safe_load((root / "tools/skills/registry.yaml").read_text(encoding="utf-8"))["skills"]
    if args.check_discovery and not failures:
        expected = {record["name"]: root / record["path"] for record in records}
        for client in (".agents", ".claude"):
            failures.extend(validate_discovery(root / client / "skills", expected))
    if args.catalog and not failures:
        print(json.dumps([record["name"] for record in records]))
    else:
        print("\n".join(failures) if failures else "Local skill registry: OK")
    raise SystemExit(bool(failures))
