# Smoke test for install.ps1 and the plotting skill. Uses only temporary folders.
#   powershell -ExecutionPolicy Bypass -File tests\smoke_test.ps1
#   (also runs under pwsh on macOS and Linux)
# Set $env:PUBSTYLE_ALLOW_STANDIN = "1" on machines without Arial (draft font for the test).
$ErrorActionPreference = "Stop"
$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Installer = Join-Path $Repo "install.ps1"
$Tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("stormy-drawing-test-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $Tmp | Out-Null
$sep = [System.IO.Path]::DirectorySeparatorChar

function Fail([string]$m) { Write-Host "FAIL: $m"; Remove-Item -LiteralPath $Tmp -Recurse -Force; exit 1 }
function Ok([string]$m) { Write-Host "PASS: $m" }
function P([string[]]$parts) { $p = $parts[0]; foreach ($x in $parts[1..($parts.Count - 1)]) { $p = Join-Path $p $x }; return $p }
function Install([string]$dir, [hashtable]$installArgs) {
    Push-Location $dir
    try { $out = & $Installer @installArgs 6>&1 | Out-String } finally { Pop-Location }
    return $out
}
$Py = $null
foreach ($c in @("python", "python3", "py")) {
    if (Get-Command $c -ErrorAction SilentlyContinue) { $Py = $c; break }
}
if (-not $Py) { Fail "no python found" }

try {
    # 1. fresh project, all harnesses
    $P1 = P @($Tmp, "fresh"); New-Item -ItemType Directory -Path $P1 | Out-Null
    Install $P1 @{} | Out-Null
    foreach ($d in @(".agents", ".claude", ".qwen", ".zcode")) {
        if (-not (Test-Path (P @($P1, $d, "skills", "plotting", "SKILL.md")))) { Fail "fresh: $d" }
    }
    Ok "fresh project install"

    # 2. running again without -Force changes nothing
    $out = Install $P1 @{}
    if ($out -notmatch "skip:") { Fail "rerun should skip" }
    Ok "rerun skips existing install"

    # 3. -Force replaces, -AgentsMd adds the note once
    Install $P1 @{ Force = $true; AgentsMd = $true } | Out-Null
    Install $P1 @{ AgentsMd = $true } | Out-Null
    $n = ([regex]::Matches((Get-Content -Raw (P @($P1, "AGENTS.md"))), "Stormy-drawing")).Count
    if ($n -lt 1) { Fail "AGENTS.md note missing" }
    if ((Get-Content -Raw (P @($P1, "AGENTS.md"))) -match "(?s)## Figures.*## Figures") { Fail "AGENTS.md note added twice" }
    Ok "-Force and -AgentsMd"

    # 4. -Global with a fake home, link mode
    $H = P @($Tmp, "home"); New-Item -ItemType Directory -Path $H | Out-Null
    $oldHome = $HOME
    Set-Variable -Name HOME -Value $H -Force -Scope Global
    try {
        $env:CODEX_HOME = ""
        & $Installer -Global -Harness "claude,agy" -Mode link 6>&1 | Out-Null
    } finally { Set-Variable -Name HOME -Value $oldHome -Force -Scope Global }
    foreach ($d in @(@(".claude", "skills"), @(".gemini", "config", "skills"))) {
        $dest = P (@($H) + $d + @("plotting"))
        if (-not (Get-Item -LiteralPath $dest -Force).LinkType) { Fail "global link: $dest" }
        if (-not (Test-Path (Join-Path $dest "SKILL.md"))) { Fail "global link target: $dest" }
    }
    # -Force on a link removes only the link, not the repo checkout
    Set-Variable -Name HOME -Value $H -Force -Scope Global
    try { & $Installer -Global -Harness claude -Force 6>&1 | Out-Null }
    finally { Set-Variable -Name HOME -Value $oldHome -Force -Scope Global }
    if (-not (Test-Path (P @($Repo, "skills", "plotting", "SKILL.md")))) { Fail "repo skill deleted through a link" }
    if ((Get-Item -LiteralPath (P @($H, ".claude", "skills", "plotting")) -Force).LinkType) { Fail "-Force did not replace the link with a copy" }
    Ok "global install, link mode, -Force over a link"

    # 5. -Target and -DryRun
    & $Installer -Target (P @($Tmp, "custom")) 6>&1 | Out-Null
    if (-not (Test-Path (P @($Tmp, "custom", "plotting", "SKILL.md")))) { Fail "target" }
    $P2 = P @($Tmp, "dry"); New-Item -ItemType Directory -Path $P2 | Out-Null
    Install $P2 @{ DryRun = $true } | Out-Null
    if (Get-ChildItem -Force -LiteralPath $P2) { Fail "dry-run changed files" }
    Ok "-Target and -DryRun"

    # 6. the installed skill works: new figure folder + all demo figure types
    $skill = P @($P1, ".agents", "skills", "plotting")
    & $Py (P @($skill, "scripts", "init_figure.py")) $P1 "Test_figure" | Out-Null
    if (-not (Test-Path (P @($P1, "figures", "001_Test_figure", "plot.py")))) { Fail "init_figure" }
    $demo = P @($Tmp, "demo")
    $log = & $Py (P @($skill, "examples", "demo_all_types.py")) $demo 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) { Write-Host $log; Fail "demo_all_types" }
    if ($log -match "FAIL") { Write-Host $log; Fail "a demo figure failed its checks" }
    if ((Get-ChildItem -LiteralPath $demo -Filter "*.pdf").Count -ne 11) { Fail "expected 11 demo figures" }
    Ok "init_figure and all eleven demo figures"
} finally {
    if (Test-Path -LiteralPath $Tmp) { Remove-Item -LiteralPath $Tmp -Recurse -Force }
}
Write-Host "smoke test: all passed"
