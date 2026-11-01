"""Write a local CycloneDX SBOM of installed packages and pinned submodules."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from importlib import metadata
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

import tomli

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.ops.audit_open_source_dependencies import (  # noqa: E402
    PROJECT_ROOT,
    audit_dependencies,
    installed_package_license,
)


def _licenses(license_spdx: Optional[str]) -> Optional[List[Dict[str, Any]]]:
    if not license_spdx or license_spdx == "NOASSERTION":
        return None
    return [{"license": {"id": license_spdx}}]


def _component(
    name: str,
    version: str,
    purl: str,
    license_spdx: Optional[str],
    properties: List[Dict[str, str]],
    external_url: Optional[str] = None,
) -> Dict[str, Any]:
    component: Dict[str, Any] = {"type": "library", "name": name, "version": version, "purl": purl}
    licenses = _licenses(license_spdx)
    if licenses is None:
        properties = properties + [{"name": "uc3m:license_status", "value": "unverified"}]
    else:
        component["licenses"] = licenses
    if external_url:
        component["externalReferences"] = [{"type": "vcs", "url": external_url}]
    if properties:
        component["properties"] = properties
    return component


def build_sbom(
    *,
    project_name: str,
    project_version: str,
    distributions: Iterable[Dict[str, Optional[str]]],
    submodules: Iterable[Dict[str, Optional[str]]],
) -> Dict[str, Any]:
    components = [
        _component(
            name=str(dist["name"]),
            version=str(dist["version"]),
            purl=f"pkg:pypi/{str(dist['name']).lower()}@{dist['version']}",
            license_spdx=dist.get("license_spdx"),
            properties=[],
        )
        for dist in distributions
    ]
    for submodule in submodules:
        owner_repo = re.sub(r"\.git$", "", str(submodule["url"]).rstrip("/")).split("/")[-2:]
        components.append(
            _component(
                name=str(submodule["path"]),
                version=str(submodule["commit"]),
                purl=f"pkg:github/{'/'.join(owner_repo).lower()}@{submodule['commit']}",
                license_spdx=submodule.get("license_spdx"),
                properties=[{"name": "uc3m:role", "value": str(submodule["role"])}],
                external_url=str(submodule["url"]),
            )
        )
    components.sort(key=lambda component: component["name"].casefold())
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {
            "component": {"type": "application", "name": project_name, "version": project_version}
        },
        "components": components,
    }


def _installed_distributions() -> List[Dict[str, Optional[str]]]:
    seen = {}
    for distribution in metadata.distributions():
        name = distribution.metadata.get("Name")
        if not name or name.casefold() in seen:
            continue
        resolved = installed_package_license(name) or {}
        seen[name.casefold()] = {
            "name": name,
            "version": distribution.version,
            "license_spdx": resolved.get("license_spdx"),
        }
    return list(seen.values())


def _pinned_submodules(project_root: Path) -> List[Dict[str, Optional[str]]]:
    manifest = audit_dependencies(project_root, project_root / "docs/research/repository_registry.yaml")
    records = []
    for submodule in manifest["submodules"]:
        tree = subprocess.run(
            ["git", "ls-tree", "HEAD", submodule["path"]],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.split()
        records.append(
            {
                "path": submodule["path"],
                "url": submodule["url"],
                "commit": tree[2] if len(tree) > 2 else "unknown",
                "license_spdx": submodule.get("license_spdx"),
                "role": submodule["role"],
            }
        )
    return records


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)
    project = tomli.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    sbom = build_sbom(
        project_name=project["name"],
        project_version=project["version"],
        distributions=_installed_distributions(),
        submodules=_pinned_submodules(PROJECT_ROOT),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(sbom, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
