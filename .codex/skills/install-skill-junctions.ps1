param(
    [string]$CodexHome = $env:CODEX_HOME,
    [string[]]$SkillNames,
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not $CodexHome) {
    throw 'CODEX_HOME is not set. Set the CODEX_HOME environment variable or pass -CodexHome.'
}

$skillsRoot = $PSScriptRoot
$targetRoot = Join-Path $CodexHome 'skills'

if (-not (Test-Path $targetRoot)) {
    throw "Codex skills directory does not exist: $targetRoot"
}

$skillDirs = Get-ChildItem -Path $skillsRoot -Directory |
    Where-Object {
        $_.Name -ne '.system' -and (Test-Path (Join-Path $_.FullName 'SKILL.md'))
    }

if ($SkillNames) {
    $requested = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
    foreach ($skillName in $SkillNames) {
        [void]$requested.Add($skillName)
    }

    $skillDirs = $skillDirs | Where-Object { $requested.Contains($_.Name) }
}

if (-not $skillDirs) {
    throw 'No installable skills were found.'
}

foreach ($skillDir in $skillDirs) {
    $linkPath = Join-Path $targetRoot $skillDir.Name

    if (Test-Path $linkPath) {
        $existingItem = Get-Item $linkPath -Force

        if (-not $Force) {
            throw "Target already exists: $linkPath. Re-run with -Force to replace it."
        }

        Remove-Item $linkPath -Force -Recurse
    }

    New-Item -ItemType Junction -Path $linkPath -Target $skillDir.FullName | Out-Null
    Write-Host "Installed skill junction: $($skillDir.Name) -> $($skillDir.FullName)"
}

Write-Host "Installed $($skillDirs.Count) skill junction(s) into $targetRoot"
