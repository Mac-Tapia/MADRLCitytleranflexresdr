"""Audit declared packages, local submodules, and research repositories offline."""

from __future__ import annotations

import argparse
import configparser
import json
import re
from datetime import date
from importlib import metadata
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence

import tomli
import yaml

from uc3m.governance.open_source import (
    DependencyRecord,
    OpenSourcePolicy,
    classify_license_text,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = PROJECT_ROOT / "governance/open_source_policy.yaml"
ROLES_RELATIVE_PATH = Path("governance/dependency_roles.yaml")
LICENSE_STEMS = {"LICENSE", "LICENCE", "COPYING"}
CLASSIFIER_SPDX = {
    "License :: OSI Approved :: MIT License": "MIT",
    "License :: OSI Approved :: Apache Software License": "Apache-2.0",
    "License :: OSI Approved :: ISC License (ISCL)": "ISC",
    "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)": "MPL-2.0",
    "License :: OSI Approved :: Python Software Foundation License": "PSF-2.0",
}

PackageResolver = Callable[[str], Optional[Dict[str, str]]]


def _normalize_url(url: str) -> str:
    return url.strip().rstrip("/").removesuffix(".git").casefold()


def license_file_candidates(files: Sequence[object]) -> List[object]:
    """License files of a distribution, its own dist-info license first.

    Files elsewhere in the package usually belong to bundled components.
    """
    candidates = [f for f in files if Path(str(f)).name.upper().split(".", 1)[0] in LICENSE_STEMS]
    return sorted(candidates, key=lambda f: ".dist-info/" not in Path(str(f)).as_posix())


def installed_package_license(name: str) -> Optional[Dict[str, str]]:
    """Read version and license of an installed distribution, or None if absent."""
    try:
        distribution = metadata.distribution(name)
    except metadata.PackageNotFoundError:
        return None
    expression = distribution.metadata.get("License-Expression")
    license_spdx = expression.strip() if expression else None
    if not license_spdx:
        own = [f for f in license_file_candidates(list(distribution.files or ())) if ".dist-info/" in Path(str(f)).as_posix()]
        if own:
            text = Path(distribution.locate_file(own[0])).read_text(encoding="utf-8", errors="replace")
            license_spdx = classify_license_text(text)
    if not license_spdx or license_spdx == "NOASSERTION":
        classifiers = distribution.metadata.get_all("Classifier") or []
        mapped = {CLASSIFIER_SPDX[c] for c in classifiers if c in CLASSIFIER_SPDX}
        license_spdx = mapped.pop() if len(mapped) == 1 else "NOASSERTION"
    return {"version": distribution.version, "license_spdx": license_spdx}


def _declared_packages(
    project_root: Path, policy: OpenSourcePolicy, resolve: PackageResolver
) -> List[Dict[str, Any]]:
    pyproject = project_root / "pyproject.toml"
    if not pyproject.is_file():
        return []
    payload = tomli.loads(pyproject.read_text(encoding="utf-8"))
    records = []
    for declaration in payload.get("project", {}).get("dependencies", []):
        name = re.match(r"[A-Za-z0-9._-]+", str(declaration)).group(0)
        record: Dict[str, Any] = {"declaration": str(declaration), "name": name}
        resolved = resolve(name)
        if resolved is None:
            record.update(status="declared_unverified", reason="package_not_installed")
        else:
            decision = policy.evaluate(
                DependencyRecord(name=name, license_spdx=resolved["license_spdx"])
            )
            record.update(resolved)
            record.update(status=decision.status, reason=";".join(decision.reasons) or None)
        records.append(record)
    return records


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


def _load_roles(roles_path: Path) -> Mapping[str, Any]:
    if not roles_path.is_file():
        return {}
    payload = yaml.safe_load(roles_path.read_text(encoding="utf-8")) or {}
    return payload.get("submodules") or {}


def _load_exceptions(policy_path: Path) -> Dict[str, Mapping[str, Any]]:
    """Owner-approved, expiring exceptions keyed by submodule path."""
    payload = yaml.safe_load(policy_path.read_text(encoding="utf-8")) or {}
    return {str(entry["name"]): entry for entry in payload.get("exceptions") or []}


def _local_license(path: Path) -> Optional[Dict[str, str]]:
    candidates = sorted(
        candidate
        for candidate in path.glob("*")
        if candidate.is_file() and candidate.name.upper().split(".", 1)[0] in LICENSE_STEMS
    )
    if not candidates:
        return None
    license_path = candidates[0]
    text = license_path.read_text(encoding="utf-8", errors="replace")
    return {"file": license_path.name, "license_spdx": classify_license_text(text)}


def audit_dependencies(
    project_root: Path,
    registry_path: Path,
    roles_path: Optional[Path] = None,
    package_resolver: Optional[PackageResolver] = None,
    policy_path: Optional[Path] = None,
    today: Optional[date] = None,
) -> Dict[str, Any]:
    policy_file = policy_path or POLICY_PATH
    policy = OpenSourcePolicy.from_yaml(policy_file)
    exceptions = _load_exceptions(policy_file)
    today = today or date.today()
    accepted_exceptions: List[Dict[str, str]] = []
    roles = _load_roles(roles_path or project_root / ROLES_RELATIVE_PATH)
    submodule_declarations = _parse_submodules(project_root)
    submodule_urls = {_normalize_url(record["url"]) for record in submodule_declarations}

    blockers: List[Dict[str, str]] = []
    submodules: List[Dict[str, Any]] = []
    for declaration in submodule_declarations:
        # An undeclared submodule is treated as part of the required runtime (fail closed).
        role = str((roles.get(declaration["path"]) or {}).get("role", "runtime"))
        license_record = _local_license(project_root / declaration["path"])
        record: Dict[str, Any] = dict(declaration, role=role)
        if license_record is None:
            policy_status, reason = "blocked", "missing_local_license"
        else:
            decision = policy.evaluate(
                DependencyRecord(
                    name=declaration["name"],
                    license_spdx=license_record["license_spdx"],
                    required=role == "runtime",
                )
            )
            record.update(license_record)
            policy_status, reason = decision.status, ";".join(decision.reasons) or None
        record.update(policy_status=policy_status, reason=reason)
        exception = exceptions.get(declaration["path"])
        if role == "reference_only":
            record["status"] = "reference_only"
        elif policy_status == "allow":
            record["status"] = policy_status
        elif exception and date.fromisoformat(str(exception["expires_on"])) >= today:
            # Reported, never counted as a verified license.
            record["status"] = "accepted_exception"
            accepted_exceptions.append(
                {
                    "name": declaration["path"],
                    "reason": reason or policy_status,
                    **{
                        key: str(exception[key])
                        for key in ("scope", "approved_by", "approved_on", "expires_on")
                    },
                }
            )
        else:
            record["status"] = policy_status
            blockers.append(
                {
                    "kind": "submodule",
                    "name": declaration["name"],
                    "reason": "license_exception_expired" if exception else reason or policy_status,
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

    packages = _declared_packages(project_root, policy, package_resolver or installed_package_license)
    for package in packages:
        if package["status"] not in ("allow", "declared_unverified"):
            blockers.append(
                {
                    "kind": "package",
                    "name": package["name"],
                    "reason": package["reason"] or package["status"],
                }
            )
    return {
        "schema_version": "1.0",
        "ok": not blockers,
        "packages": packages,
        "submodules": submodules,
        "research_repositories": research_records,
        "blockers": blockers,
        "accepted_exceptions": accepted_exceptions,
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
