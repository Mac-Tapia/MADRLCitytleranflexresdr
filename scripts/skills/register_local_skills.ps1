param([switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Push-Location $projectRoot
try {
    & powershell -ExecutionPolicy Bypass -File scripts/verify_project_context.ps1
    if ($LASTEXITCODE -ne 0) { throw 'Project context failed.' }
    $catalog = & .venv39-citylearn-v3/Scripts/python.exe tools/skills/validate_skills.py --catalog
    if ($LASTEXITCODE -ne 0) { throw 'Skill registry validation failed.' }
    $skillNames = $catalog | ConvertFrom-Json
    $folders = @($skillNames | ForEach-Object { Get-Item -LiteralPath (Join-Path 'tools/skills' $_) })
    foreach ($surface in @('.agents/skills', '.claude/skills')) {
        if (!(Test-Path -LiteralPath $surface)) {
            if ($CheckOnly) { throw "Missing discovery directory: $surface" }
            New-Item -ItemType Directory -Path $surface | Out-Null
        }
        $unexpected = @(Get-ChildItem -LiteralPath $surface -Force |
            Where-Object { $_.Name -notin $skillNames })
        if ($unexpected.Count -gt 0) {
            throw "Unexpected discovery entries (preserved): $($unexpected.Name -join ', ')"
        }
        foreach ($folder in $folders) {
            $link = Join-Path $surface $folder.Name
            $existing = Get-Item -LiteralPath $link -Force -ErrorAction SilentlyContinue
            if ($existing) {
                if (!$existing.LinkType -or !($existing.Target)) {
                    throw "Refusing to replace non-link: $link"
                }
                $actual = (Resolve-Path -LiteralPath $existing.Target[0]).Path
                if ($actual -ne $folder.FullName) { throw "Wrong discovery target: $link" }
            } elseif ($CheckOnly) {
                throw "Missing discovery link: $link"
            } else {
                New-Item -ItemType Junction -Path $link -Target $folder.FullName | Out-Null
            }
        }
    }
    & .venv39-citylearn-v3/Scripts/python.exe tools/skills/validate_skills.py --check-discovery
    if ($LASTEXITCODE -ne 0) { throw 'Discovery integrity check failed.' }
    Write-Host "[OK] Local discovery links verified for Codex and Claude."
} finally { Pop-Location }
