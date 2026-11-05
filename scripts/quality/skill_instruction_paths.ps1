function Get-LocalSkillInstructionFiles {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][string]$Root)

    # Enumerate sources, never a browser session, dependency tree or binary cache.
    # Prune before descending; filtering files after -Recurse would still enter it.
    $extensions = @('.md', '.txt', '.py', '.ps1', '.sh', '.bat', '.cmd', '.yaml',
                    '.yml', '.toml', '.json', '.cfg', '.ini', '.js', '.ts', '.tsx', '.jsx', '.html', '.css')
    $queue = New-Object 'System.Collections.Generic.Queue[string]'
    $queue.Enqueue((Resolve-Path -LiteralPath $Root).Path)
    while ($queue.Count -gt 0) {
        $directory = $queue.Dequeue()
        foreach ($entry in Get-ChildItem -LiteralPath $directory -Force -ErrorAction Stop) {
            if ($entry.PSIsContainer) {
                if ($entry.Name -in @('__pycache__', '.git', 'node_modules', 'browser_state')) { continue }
                if ($entry.Name -eq 'data' -and (Split-Path -Leaf $directory) -eq 'notebooklm-mcp') { continue }
            }
            if (($entry.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "Linked instruction source is not allowed: $($entry.FullName)"
            }
            if ($entry.PSIsContainer) { $queue.Enqueue($entry.FullName) }
            elseif ($entry.Extension.ToLowerInvariant() -in $extensions) { Write-Output $entry }
        }
    }
}
