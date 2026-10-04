<#
.SYNOPSIS
  Stormy-drawing installer for Windows: puts the `plotting` skill where AI agents look for skills.

.DESCRIPTION
  Works in Windows PowerShell 5.1 and PowerShell 7 (also on macOS and Linux, where
  install.sh does the same job).

  Default (run inside a project folder)
      Copies the skill to .\.agents\skills\plotting and makes it visible to every
      harness in -Harness (default: all):
        codex / kimi / pi / opencode / agy / generic : .agents\skills\
        claude (Claude Code)                         : .claude\skills\
        qwen (Qwen Code)                             : .qwen\skills\
        zcode (ZCode)                                : .zcode\skills\ (project path unverified)
      If a harness folder already shows the skill (for example it is a link to
      .agents\skills), nothing more is done there. Otherwise the skill is copied
      into it too (copy mode) or linked (link mode). Copies need no administrator
      rights and no Developer Mode.

  -Global
      Installs into the user-level skill folder of each harness instead:
        claude ~\.claude\skills   codex $env:CODEX_HOME\skills (~\.codex\skills)
        qwen ~\.qwen\skills       zcode ~\.zcode\skills
        agy (Antigravity) ~\.gemini\config\skills
        kimi / pi / opencode / generic ~\.agents\skills

.PARAMETER Harness
  Comma-separated: claude, codex, qwen, zcode, kimi, pi, opencode, agy, generic, or all.
.PARAMETER Global
  Install for the current user instead of the current project.
.PARAMETER Target
  Install into <Target>\plotting only (any other agent's skill folder).
.PARAMETER Mode
  copy (default): a fixed copy, so every project keeps the version it was installed
  with. link: a directory junction (Windows) or symlink (macOS/Linux) to this
  checkout, so `git pull` here updates every install at once.
.PARAMETER AgentsMd
  Also add a short routing note to .\AGENTS.md (skipped if already present or if
  AGENTS.md is a link).
.PARAMETER Force
  Replace an existing plotting skill.
.PARAMETER DryRun
  Print what would be done; change nothing.

.EXAMPLE
  cd C:\projects\Li6PS5Cl_doping; powershell -ExecutionPolicy Bypass -File C:\src\Stormy-drawing\install.ps1
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File C:\src\Stormy-drawing\install.ps1 -Global -Harness claude,codex
#>
[CmdletBinding()]
param(
    [string]$Harness = "all",
    [switch]$Global,
    [string]$Target = "",
    [ValidateSet("copy", "link")][string]$Mode = "copy",
    [switch]$AgentsMd,
    [switch]$Force,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Die([string]$msg) {
    Write-Host "ERROR: $msg" -ForegroundColor Red
    exit 1
}

$RepoDir = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$SkillSrc = Join-Path (Join-Path $RepoDir "skills") "plotting"
if (-not (Test-Path -LiteralPath (Join-Path $SkillSrc "SKILL.md"))) {
    Die "cannot find skills\plotting\SKILL.md next to install.ps1"
}
if ($Global -and $Target) { Die "use either -Global or -Target, not both" }

$AllHarnesses = @("claude", "codex", "qwen", "zcode", "kimi", "pi", "opencode", "agy", "generic")
if ($Harness -eq "all") {
    $HarnessList = $AllHarnesses
} else {
    $HarnessList = @($Harness -split "[,\s]+" | Where-Object { $_ } |
        ForEach-Object { if ($_ -eq "claudecode") { "claude" } else { $_.ToLower() } })
    foreach ($h in $HarnessList) {
        if ($AllHarnesses -notcontains $h) { Die "unknown harness: $h" }
    }
}
function Has([string]$h) { return ($HarnessList -contains $h) }

$OnWindows = ($env:OS -eq "Windows_NT")

function Step([string]$what, [scriptblock]$action) {
    if ($DryRun) { Write-Host "(dry-run) $what" } else { & $action }
}

function Remove-Existing([string]$path) {
    $item = Get-Item -LiteralPath $path -Force
    if ($item.LinkType) {
        # a junction or symlink: remove the link only, never the folder it points to
        if ($OnWindows) {
            Step "remove link $path" { [System.IO.Directory]::Delete($path, $false) }
        } else {
            Step "remove link $path" { Remove-Item -LiteralPath $path -Force }
        }
    } else {
        Step "remove $path" { Remove-Item -LiteralPath $path -Recurse -Force }
    }
}

function Test-Exists([string]$path) {
    return [bool](Get-Item -LiteralPath $path -Force -ErrorAction SilentlyContinue)
}

# Place-Skill <skills_dir>: put plotting into <skills_dir>\plotting by copy or link
function Place-Skill([string]$dir) {
    $dest = Join-Path $dir "plotting"
    if (Test-Exists $dest) {
        if ($Force) {
            Remove-Existing $dest
        } else {
            Write-Host "skip: $dest already exists (use -Force to replace)"
            return
        }
    }
    if (-not (Test-Path -LiteralPath $dir)) {
        Step "create $dir" { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    }
    if ($Mode -eq "link") {
        if ($OnWindows) {
            Step "junction $dest -> $SkillSrc" { New-Item -ItemType Junction -Path $dest -Target $SkillSrc | Out-Null }
        } else {
            Step "symlink $dest -> $SkillSrc" { New-Item -ItemType SymbolicLink -Path $dest -Target $SkillSrc | Out-Null }
        }
    } else {
        Step "copy $SkillSrc -> $dest" {
            Copy-Item -LiteralPath $SkillSrc -Destination $dest -Recurse
            Get-ChildItem -LiteralPath $dest -Recurse -Directory -Filter "__pycache__" |
                Remove-Item -Recurse -Force
        }
    }
    Write-Host "installed: $dest ($Mode)"
}

# ---------------------------------------------------------------- -Target
if ($Target) {
    Place-Skill ([System.IO.Path]::GetFullPath($Target))
    exit 0
}

# ---------------------------------------------------------------- -Global
if ($Global) {
    $done = @()
    $codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
    foreach ($h in $HarnessList) {
        switch ($h) {
            "claude" { $d = Join-Path $HOME ".claude\skills" }
            "codex"  { $d = Join-Path $codexHome "skills" }
            "qwen"   { $d = Join-Path $HOME ".qwen\skills" }
            "zcode"  { $d = Join-Path $HOME ".zcode\skills" }
            "agy"    { $d = Join-Path $HOME ".gemini\config\skills" }
            default  { $d = Join-Path $HOME ".agents\skills" }
        }
        $d = [System.IO.Path]::GetFullPath(($d -replace '\\', [System.IO.Path]::DirectorySeparatorChar))
        if ($done -contains $d) { continue }
        Place-Skill $d
        $done += $d
    }
    Write-Host "Next: restart or refresh your agent so it reloads its skills."
    exit 0
}

# ---------------------------------------------------------------- project (default)
$Project = (Get-Location).ProviderPath
if ($Project.TrimEnd('\', '/') -eq $RepoDir.TrimEnd('\', '/')) {
    Die "run this from inside a project folder, not from the Stormy-drawing checkout (or use -Global / -Target)"
}

$sep = [System.IO.Path]::DirectorySeparatorChar
Place-Skill (Join-Path $Project ".agents${sep}skills")

# Alias-Dir <harness dir relative to project, e.g. .claude\skills>
function Alias-Dir([string]$rel) {
    $abs = Join-Path $Project $rel
    if (Test-Path -LiteralPath (Join-Path $abs "plotting")) {
        if (-not $Force -or (Get-Item -LiteralPath $abs -Force).LinkType) {
            Write-Host "visible: $rel${sep}plotting"
            return
        }
    }
    Place-Skill $abs
}

if (Has "claude") { Alias-Dir ".claude${sep}skills" }
if (Has "qwen")   { Alias-Dir ".qwen${sep}skills" }
if (Has "zcode")  { Alias-Dir ".zcode${sep}skills" }

if ($AgentsMd) {
    $f = Join-Path $Project "AGENTS.md"
    $utf8 = New-Object System.Text.UTF8Encoding $false
    if ((Test-Exists $f) -and (Get-Item -LiteralPath $f -Force).LinkType) {
        Write-Host "NOTE: AGENTS.md is a link (probably AI-Computational-Chemist); not editing it."
    } elseif ((Test-Path -LiteralPath $f) -and
              ([System.IO.File]::ReadAllText($f, $utf8) -match "Stormy-drawing")) {
        Write-Host "AGENTS.md already mentions Stormy-drawing; unchanged."
    } else {
        $snippet = [System.IO.File]::ReadAllText((Join-Path $RepoDir "AGENTS_snippet.md"), $utf8)
        if ((Test-Path -LiteralPath $f) -and (Get-Item -LiteralPath $f).Length -gt 0) {
            $snippet = [Environment]::NewLine + $snippet
        }
        Step "append routing note to $f" { [System.IO.File]::AppendAllText($f, $snippet, $utf8) }
        Write-Host "updated: AGENTS.md (routing note for the plotting skill)"
    }
}

Write-Host ""
Write-Host "Done. Figures go in .\figures\, one folder per figure; start one with:"
Write-Host "  python .agents\skills\plotting\scripts\init_figure.py . <English_name>"
Write-Host "Next: restart or refresh your agent so it reloads its skills."
