param(
    [ValidateSet('Plan', 'Execute', 'Verify')][string]$Phase = 'Plan',
    [Parameter(Mandatory = $true)][string]$Manifest,
    [string]$Root
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if (-not $Root) { $Root = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path }

# Context is checked even when the operation is used against a temporary tree.
& (Join-Path $PSScriptRoot '../verify_project_context.ps1')
if (-not $?) { throw 'Project context verification failed' }
$Root = [IO.Path]::GetFullPath($Root).TrimEnd('\', '/')
$map = Get-Content -LiteralPath $Manifest -Raw -Encoding UTF8 | ConvertFrom-Json
if ($map.schema_version -ne 1 -or [IO.Path]::GetFullPath($map.root).TrimEnd('\', '/') -ne $Root) {
    throw 'Manifest root/schema mismatch'
}

function Safe-Path([string]$Relative) {
    if ([IO.Path]::IsPathRooted($Relative) -or $Relative.Contains(':') -or
        ($Relative -split '[/\\]' -contains '..') -or $Relative -match '(^|[/\\])(\.git|CityLearn|external|\.superpowers)([/\\]|$)' -or
        $Relative -match '^tools[/\\]skills([/\\]|$)') { throw "Unsafe relative path: $Relative" }
    $full = [IO.Path]::GetFullPath((Join-Path $Root $Relative))
    if (-not $full.StartsWith($Root + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path outside intended root: $Relative"
    }
    $current = $full
    while ($current -and $current.Length -ge $Root.Length) {
        if (Test-Path -LiteralPath $current) {
            if ((Get-Item -LiteralPath $current -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
                throw "Linked path rejected: $current"
            }
            if ((Test-Path -LiteralPath (Join-Path $current '.runner.lock') -ErrorAction SilentlyContinue) -or
                (Test-Path -LiteralPath (Join-Path $current '.campaign.lock') -ErrorAction SilentlyContinue)) {
                throw "Active run rejected: $current"
            }
        }
        if ($current -eq $Root) { break }
        $current = [IO.Path]::GetDirectoryName($current)
    }
    return $full
}

function Hash-Stream($Stream) {
    $hasher = [Security.Cryptography.SHA256]::Create()
    $position = $Stream.Position
    try {
        $Stream.Position = 0
        return ([BitConverter]::ToString($hasher.ComputeHash($Stream))).Replace('-', '').ToLowerInvariant()
    } finally { $Stream.Position = $position; $hasher.Dispose() }
}
function Hash-File([string]$Path) {
    $stream = [IO.File]::OpenRead($Path)
    try { return Hash-Stream $stream } finally { $stream.Dispose() }
}
function Hash-Bytes([byte[]]$Bytes) {
    $hasher = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($hasher.ComputeHash($Bytes))).Replace('-', '').ToLowerInvariant() }
    finally { $hasher.Dispose() }
}
$moves = @($map.moves)
$refs = @($map.references)
$duplicates = @($map.duplicates)
$updates = @{}
foreach ($ref in $refs) { $updates[$ref.old_path] = $ref }
$targets = @{}
foreach ($move in $moves) {
    $null = Safe-Path $move.old_path
    $dest = Safe-Path $move.new_path
    if ($targets.ContainsKey($dest.ToLowerInvariant())) { throw "Destination collision: $dest" }
    $targets[$dest.ToLowerInvariant()] = $true
}

if ($Phase -eq 'Verify') {
    foreach ($move in $moves) {
        $destination = Safe-Path $move.new_path
        $expected = $move.source_hash
        if ($updates.ContainsKey($move.old_path)) { $expected = $updates[$move.old_path].after_sha256 }
        if (-not (Test-Path -LiteralPath $destination -PathType Leaf) -or (Hash-File $destination) -ne $expected) {
            throw "Moved content verification failed: $destination"
        }
        if ($move.old_path -ine $move.new_path -and (Test-Path -LiteralPath (Safe-Path $move.old_path))) {
            throw "Old source still exists: $($move.old_path)"
        }
    }
    foreach ($ref in $refs) {
        if ((Hash-File (Safe-Path $ref.new_path)) -ne $ref.after_sha256) { throw "Consumer verification failed: $($ref.new_path)" }
    }
    foreach ($duplicate in $duplicates) {
        if ((Test-Path -LiteralPath (Safe-Path $duplicate.old_path)) -or
            (Hash-File (Safe-Path $duplicate.new_path)) -ne $duplicate.source_hash) { throw 'Duplicate verification failed' }
    }
    Write-Output "Verified: $($moves.Count) moves, $($refs.Count) consumers, $($duplicates.Count) exact duplicates"
    exit 0
}

$handles = @{}
$completed = [Collections.Generic.List[object]]::new()
$written = [Collections.Generic.List[object]]::new()
$removed = [Collections.Generic.List[object]]::new()
$replacementHandles = [Collections.Generic.List[object]]::new()
$stageFiles = @{}
$stageDirectory = Safe-Path 'data/maintenance/names/stage'
$script:replacementSequence = 0

function Replace-Consumer([string]$Relative, [byte[]]$Bytes) {
    $script:replacementSequence++
    $temporary = Safe-Path ('data/maintenance/names/stage/ref_{0}.tmp' -f $script:replacementSequence)
    $destination = Safe-Path $Relative
    $stream = [IO.File]::Open($temporary, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
    try { $stream.Write($Bytes, 0, $Bytes.Length); $stream.Flush($true) } finally { $stream.Dispose() }
    $stageFiles[$temporary] = Hash-Bytes $Bytes
    # A mapped read-only snapshot can keep the original inode alive. Replacing
    # the directory entry preserves that snapshot without truncating its file.
    [IO.File]::Replace($temporary, $destination, [NullString]::Value)
    # ReplaceFile opens the replacement exclusively. Acquire the read lock on
    # its final name afterwards, not on the staging file before replacement.
    $read = [IO.File]::Open($destination, [IO.FileMode]::Open, [IO.FileAccess]::Read,
                           ([IO.FileShare]::Read -bor [IO.FileShare]::Delete))
    $replacementHandles.Add($read)
}

$resultPath = Safe-Path 'data/maintenance/names/results.json'
try {
    # Validate the complete batch and hold files against readers/writers before
    # the first move. ShareDelete permits Move-Item while preserving the lock.
    $sources = @{}
    foreach ($move in $moves) { $sources[$move.old_path] = $move.source_hash }
    foreach ($ref in $refs) {
        if ($sources.ContainsKey($ref.old_path) -and $sources[$ref.old_path] -ne $ref.before_sha256) {
            throw "Inventory/consumer hash mismatch: $($ref.old_path)"
        }
        if ((Hash-Bytes ([Convert]::FromBase64String($ref.after_base64))) -ne $ref.after_sha256 -or
            (Hash-Bytes ([Convert]::FromBase64String($ref.before_base64))) -ne $ref.before_sha256) { throw 'Corrupt consumer payload' }
        $sources[$ref.old_path] = $ref.before_sha256
    }
    foreach ($duplicate in $duplicates) {
        $sources[$duplicate.old_path] = $duplicate.source_hash
        $canonical = $duplicate.new_path
        foreach ($move in $moves) { if ($move.new_path -eq $canonical) { $canonical = $move.old_path; break } }
        if (-not $sources.ContainsKey($canonical)) { $sources[$canonical] = $duplicate.source_hash }
    }
    foreach ($old in $sources.Keys) {
        $source = Safe-Path $old
        if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "Source missing: $old" }
        if ((Hash-File $source) -ne $sources[$old]) { throw "Source changed since inventory: $old" }
        $handles[$old] = [IO.File]::Open($source, [IO.FileMode]::Open, [IO.FileAccess]::Read,
                                       ([IO.FileShare]::Read -bor [IO.FileShare]::Delete))
        if ((Hash-Stream $handles[$old]) -ne $sources[$old]) { throw "Source changed before lock: $old" }
    }
    foreach ($move in $moves) {
        $source = Safe-Path $move.old_path
        $destination = Safe-Path $move.new_path
        if ($source -ine $destination -and (Test-Path -LiteralPath $destination)) { throw "Occupied destination: $destination" }
    }
    foreach ($duplicate in $duplicates) {
        $canonicalOld = $duplicate.new_path
        foreach ($move in $moves) { if ($move.new_path -eq $canonicalOld) { $canonicalOld = $move.old_path; break } }
        $canonicalHash = if ($handles.ContainsKey($canonicalOld)) { Hash-Stream $handles[$canonicalOld] }
                         else { Hash-File (Safe-Path $canonicalOld) }
        if ($canonicalHash -ne $duplicate.source_hash) { throw 'Duplicate content mismatch' }
    }
    if ($Phase -eq 'Plan') {
        Write-Output "Ready: $($moves.Count) moves, $($refs.Count) consumers, $($duplicates.Count) exact duplicates; no changes"
        exit 0
    }
    if (Test-Path -LiteralPath $stageDirectory) { throw 'Staging directory occupied; inspect the earlier batch' }
    $null = New-Item -ItemType Directory -Path $stageDirectory
    foreach ($move in $moves) {
        $source = Safe-Path $move.old_path
        $destination = Safe-Path $move.new_path
        $parent = Split-Path $destination -Parent
        $null = New-Item -ItemType Directory -Path $parent -Force
        if ($source -ieq $destination) {
            $temporary = Safe-Path ($move.old_path + '.rename_tmp')
            if (Test-Path -LiteralPath $temporary) { throw 'Case-rename temporary path occupied' }
            Move-Item -LiteralPath $source -Destination $temporary
            try { Move-Item -LiteralPath $temporary -Destination $destination }
            catch { Move-Item -LiteralPath $temporary -Destination $source; throw }
        } else { Move-Item -LiteralPath $source -Destination $destination }
        $completed.Add($move)
    }
    foreach ($ref in $refs) {
        $written.Add($ref)
        Replace-Consumer $ref.new_path ([Convert]::FromBase64String($ref.after_base64))
    }
    foreach ($duplicate in $duplicates) {
        # Source and canonical bytes were checked before the batch; only exact
        # duplicates are removed, never another version or a document by size.
        Remove-Item -LiteralPath (Safe-Path $duplicate.old_path)
        $removed.Add($duplicate)
    }
    $null = New-Item -ItemType Directory -Path (Split-Path $resultPath -Parent) -Force
    @{ schema_version = 1; status = 'executed'; moved = $moves.Count; consumers = $refs.Count;
       manifest_sha256 = (Hash-File ([IO.Path]::GetFullPath($Manifest)));
       consolidated = $duplicates.Count; naming_verified = $false; scientific_acceptance = $false;
       created_at = [DateTime]::UtcNow.ToString('o') } | ConvertTo-Json -Depth 8 |
       Set-Content -LiteralPath $resultPath -Encoding UTF8
} catch {
    $failure = $_
    $rollbackErrors = [Collections.Generic.List[string]]::new()
    for ($i = $written.Count-1; $i -ge 0; $i--) {
        $ref = $written[$i]
        try {
            $currentHash = Hash-File (Safe-Path $ref.new_path)
            if ($currentHash -eq $ref.before_sha256) { continue }
            if ($currentHash -ne $ref.after_sha256) { throw 'Concurrent consumer edit during rollback' }
            Replace-Consumer $ref.new_path ([Convert]::FromBase64String($ref.before_base64))
        }
        catch { $rollbackErrors.Add("consumer $($ref.old_path): $_") }
    }
    foreach ($handle in $handles.Values) { $handle.Dispose() }
    $handles.Clear()
    foreach ($handle in $replacementHandles) { $handle.Dispose() }
    $replacementHandles.Clear()
    for ($i = $completed.Count-1; $i -ge 0; $i--) {
        $move = $completed[$i]
        try {
            $source = Safe-Path $move.new_path
            $destination = Safe-Path $move.old_path
            if ((Hash-File $source) -ne $move.source_hash) { throw 'Concurrent modification during rollback' }
            if ($source -ieq $destination) {
                $temporary = Safe-Path ($move.old_path + '.rename_tmp')
                if (Test-Path -LiteralPath $temporary) { throw 'Rollback temporary path occupied' }
                Move-Item -LiteralPath $source -Destination $temporary
                Move-Item -LiteralPath $temporary -Destination $destination
            } else {
                if (Test-Path -LiteralPath $destination) { throw 'Rollback destination occupied' }
                Move-Item -LiteralPath $source -Destination $destination
            }
        } catch { $rollbackErrors.Add("move $($move.old_path): $_") }
    }
    foreach ($duplicate in $removed) {
        try {
            $canonical = $duplicate.new_path
            foreach ($move in $completed) { if ($move.new_path -eq $canonical) { $canonical = $move.old_path; break } }
            $source = Safe-Path $canonical
            $destination = Safe-Path $duplicate.old_path
            if ((Hash-File $source) -ne $duplicate.source_hash -or (Test-Path -LiteralPath $destination)) {
                throw 'Duplicate rollback content/destination conflict'
            }
            Copy-Item -LiteralPath $source -Destination $destination
        } catch { $rollbackErrors.Add("duplicate $($duplicate.old_path): $_") }
    }
    if ($rollbackErrors.Count) { Write-Error ($rollbackErrors -join '; ') -ErrorAction Continue }
    throw $failure
} finally {
    foreach ($handle in $handles.Values) { $handle.Dispose() }
    foreach ($handle in $replacementHandles) { $handle.Dispose() }
    foreach ($temporary in $stageFiles.Keys) {
        if ((Test-Path -LiteralPath $temporary) -and (Hash-File $temporary) -eq $stageFiles[$temporary]) {
            Remove-Item -LiteralPath $temporary
        }
    }
    if ((Test-Path -LiteralPath $stageDirectory -PathType Container) -and
        @(Get-ChildItem -LiteralPath $stageDirectory -Force).Count -eq 0) {
        Remove-Item -LiteralPath $stageDirectory
    }
}
foreach ($relative in $map.cleanup_directories) {
    $directory = Safe-Path $relative
    if ((Test-Path -LiteralPath $directory -PathType Container) -and
        @(Get-ChildItem -LiteralPath $directory -Force).Count -eq 0) {
        Remove-Item -LiteralPath $directory
    }
}
Write-Output "Executed: $($moves.Count) moves, $($refs.Count) consumers, $($duplicates.Count) exact duplicates"
