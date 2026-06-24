$ErrorActionPreference = "Stop"

$expectedRoot = "D:/MADRLCitytleranflexresdr"
$expectedOrigin = "https://github.com/Mac-Tapia/MADRLCitytleranflexresdr.git"

$rootNative = (git rev-parse --show-toplevel).Trim()
$root = $rootNative -replace "\\", "/"
$origin = (git remote get-url origin).Trim()

if ($root -ne $expectedRoot) {
    throw "Wrong project root. Expected '$expectedRoot' but found '$root'."
}

if ($origin -ne $expectedOrigin) {
    throw "Wrong git origin. Expected '$expectedOrigin' but found '$origin'."
}

$canonicalVenvName = ".venv39-citylearn-v3"
$unexpectedVenvs = @(
    Get-ChildItem -LiteralPath $rootNative -Force -Directory |
        Where-Object { $_.Name -like ".venv*" -and $_.Name -ne $canonicalVenvName }
)

if ($unexpectedVenvs.Count -gt 0) {
    $names = ($unexpectedVenvs | ForEach-Object { $_.Name } | Sort-Object -Unique) -join ", "
    throw "Unexpected Python environment(s) in project root: $names. Use only '$canonicalVenvName' for this project."
}

$skillsRoot = Join-Path $rootNative "tools\skills"

if (Test-Path -LiteralPath $skillsRoot) {
    $localSkillNames = @(
        Get-ChildItem -LiteralPath $skillsRoot -Directory |
            Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName "SKILL.md") } |
            Select-Object -ExpandProperty Name
    )

    $globalSkillRoots = @(
        Join-Path $env:USERPROFILE ".agents\skills"
        Join-Path $env:USERPROFILE ".codex\skills"
    ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }

    foreach ($skillName in $localSkillNames) {
        foreach ($globalSkillRoot in $globalSkillRoots) {
            $globalSkillPath = Join-Path $globalSkillRoot $skillName

            if (Test-Path -LiteralPath $globalSkillPath) {
                throw "Project-specific skill '$skillName' is active globally at '$globalSkillPath'. Keep project skills local under 'tools/skills' or move the global duplicate outside the active skills root."
            }
        }
    }

    $globalReferencePatterns = @(
        ".agents\skills"
        ".agents/skills"
        ".codex\skills"
        ".codex/skills"
    )

    $globalReferences = @(
        Get-ChildItem -LiteralPath $skillsRoot -Recurse -File |
            Where-Object { $_.FullName -notmatch "\\__pycache__\\" } |
            Select-String -SimpleMatch -Pattern $globalReferencePatterns -List
    )

    if ($globalReferences.Count -gt 0) {
        $paths = ($globalReferences | ForEach-Object { $_.Path } | Sort-Object -Unique) -join ", "
        throw "Local skill files reference global skill root(s): $paths. Use repo-relative 'tools/skills' paths."
    }
}

Write-Host "[OK] Project context verified: $root"
