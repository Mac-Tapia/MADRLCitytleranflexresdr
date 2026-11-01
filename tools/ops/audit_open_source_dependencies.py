"""Audit declared packages, local submodules, and research repositories offline."""

from __future__ import annotations

import argparse
import configparser
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

import tomli
import yaml

from uc3m.governance.open_source import DependencyRecord, OpenSourcePolicy


PROJECT_ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = PROJECT_ROOT / "governance/open_source_policy.yaml"


def _normalize_url(url: str) -> str:
    return url.strip().rstrip("/").removesuffix(".git").casefold()


def _declared_packages(project_root: Path) -> List[Dict[str, Any]]:
    pyproject = project_root / "pyproject.toml"
    if not pyproject.is_file():
        return []
    payload = tomli.loads(pyproject.read_text(encoding="utf-8"))
    dependencies = payload.get("project", {}).get("dependencies", [])
    return [
        {
            "declaration": str(dependency),
            "status": "declared_unverified",
            "reason": "license_requires_inventory_resolution",
        }
        for dependency in dependencies
    ]


def _parse_submodules(project_root: Path) -> List[Dict[str, str]]:
    path = project_root / ".gitmodules"
    if not path.is_file():
        return []
    parser = configparser.ConfigParser()
    parser.read(path, encoding="utf-8")
    records = []
    for section in parser.sections():
        records.append(
            {
                "name": section.removeprefix('submodule "').removesuffix('"'),
                "path": parser.get(section, "path"),
                "url": parser.get(section, "url"),
            }
        )
    return sorted(records, key=lambda record: record["path"])


def _local_license(path: Path) -> Optional[Dict[str, str]]:
    candidates = sorted(
        candidate
        for candidate in path.glob("*")
        if candidate.is_file()
        and candidate.name.upper().split(".", 1)[0] in {"LICENSE", "LICENCE", "COPYING"}
    )
    if not candidates:
        return None
    license_path = candidates[0]
    sample = license_path.read_text(encoding="utf-8", errors="replace")[:4096].casefold()
    if "mit license" in sample:
        spdx = "MIT"
    elif "european union public licence" in sample and "1.1" in sample:
        spdx = "EUPL-1.1"
    elif "apache license" in sample and "version 2.0" in sample:
        spdx = "Apache-2.0"
    elif "gnu affero general public license" in sample:
        spdx = "AGPL-3.0-only"
    elif "gnu general public license" in sample:
        spdx = "GPL-3.0-only"
    else:
        spdx = "NOASSERTION"
    return {"file": license_path.name, "license_spdx": spdx}


def audit_dependencies(project_root: Path, registry_path: Path) -> Dict[str, Any]:
    policy = OpenSourcePolicy.from_yaml(POLICY_PATH)
    submodule_declarations = _parse_submodules(project_root)
    submodule_urls = {_normalize_url(record["url"]) for record in submodule_declarations}

    blockers: List[Dict[str, str]] = []
    submodules: List[Dict[str, Any]] = []
    for declaration in submodule_declarations:
        license_record = _local_license(project_root / declaration["path"])
        record: Dict[str, Any] = dict(declaration)
        if license_record is None:
            record.update(status="blocked", reason="missing_local_license")
            blockers.append({"kind": "submodule", "name": declaration["name"], "reason": record["reason"]})
        else:
            decision = policy.evaluate(
                DependencyRecord(
                    name=declaration["name"],
                    license_spdx=license_record["license_spdx"],
                )
            )
            record.update(license_record)
            record.update(status=decision.status, reason=";".join(decision.reasons) or None)
            if decision.status != "allow":
                blockers.append(
                    {
                        "kind": "submodule",
                        "name": declaration["name"],
                        "reason": record["reason"] or decision.status,
                    }
                )
        submodules.append(record)

    registry: Mapping[str, Any] = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
    research_records: List[Dict[str, Any]] = []
    for source in registry.get("repositories", []):
        entry = dict(source)
        desired = str(entry.get("decision", "reference_only"))
        duplicate = _normalize_url(str(entry["url"])) in submodule_urls
        if duplicate and desired != "integrated":
            entry.update(
                status="rejected",
                reason="duplicate_existing_submodule",
                blocks=False,
            )
        elif desired == "reference_only":
            entry.update(status="reference_only", reason=None, blocks=False)
        else:
            decision = policy.evaluate(
                DependencyRecord(
                    name=str(entry["name"]),
                    license_spdx=entry.get("license_spdx"),
                    requires_payment=bool(entry.get("requires_payment", False)),
                    requires_saas=bool(entry.get("requires_saas", False)),
                    required=desired == "integrated",
                )
            )
            if desired == "candidate" and decision.status == "allow":
                entry.update(status="candidate", reason=None, blocks=False)
            else:
                entry.update(
                    status=decision.status,
                    reason=";".join(decision.reasons) or None,
                    blocks=desired == "integrated" and decision.status != "allow",
                )
                if entry["blocks"]:
                    blockers.append(
                        {
                            "kind": "repository",
                            "name": str(entry["name"]),
                            "reason": str(entry["reason"]),
                        }
                    )
        research_records.append(entry)

    packages = _declared_packages(project_root)
    return {
        "schema_version": "1.0",
        "ok": not blockers,
        "packages": packages,
        "submodules": submodules,
        "research_repositories": research_records,
        "blockers": blockers,
    }


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--registry",
        type=Path,
        default=PROJECT_ROOT / "docs/research/repository_registry.yaml",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)
    manifest = audit_dependencies(PROJECT_ROOT, args.registry)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
