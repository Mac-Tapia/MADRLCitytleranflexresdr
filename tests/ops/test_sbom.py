from __future__ import annotations

from tools.ops.generate_sbom import build_sbom


def test_sbom_lists_packages_and_submodules_deterministically() -> None:
    sbom = build_sbom(
        project_name="uc3m",
        project_version="1.0.0",
        distributions=[
            {"name": "scipy", "version": "1.10.1", "license_spdx": "BSD-3-Clause"},
            {"name": "Numpy", "version": "1.23.5", "license_spdx": "BSD-3-Clause"},
            {"name": "mystery", "version": "0.1", "license_spdx": "NOASSERTION"},
        ],
        submodules=[
            {
                "path": "external/HARL",
                "url": "https://github.com/Mac-Tapia/HARL.git",
                "commit": "a" * 40,
                "license_spdx": None,
                "role": "runtime",
            }
        ],
    )

    assert sbom["bomFormat"] == "CycloneDX"
    assert sbom["specVersion"] == "1.5"
    assert sbom["metadata"]["component"] == {
        "type": "application",
        "name": "uc3m",
        "version": "1.0.0",
    }
    names = [component["name"] for component in sbom["components"]]
    assert names == sorted(names, key=str.casefold)

    by_name = {component["name"]: component for component in sbom["components"]}
    assert by_name["Numpy"]["purl"] == "pkg:pypi/numpy@1.23.5"
    assert by_name["Numpy"]["licenses"] == [{"license": {"id": "BSD-3-Clause"}}]
    assert "licenses" not in by_name["mystery"]
    assert {"name": "uc3m:license_status", "value": "unverified"} in by_name["mystery"][
        "properties"
    ]

    harl = by_name["external/HARL"]
    assert harl["version"] == "a" * 40
    assert harl["purl"] == f"pkg:github/mac-tapia/harl@{'a' * 40}"
    assert harl["externalReferences"] == [
        {"type": "vcs", "url": "https://github.com/Mac-Tapia/HARL.git"}
    ]
    assert {"name": "uc3m:role", "value": "runtime"} in harl["properties"]
    assert "licenses" not in harl
