param([switch]$Background)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$config = Join-Path $PSScriptRoot 'work\remote\portal-agent.json'
if (-not (Test-Path -LiteralPath $config)) { throw 'O portal ainda não foi vinculado a este notebook.' }
$python = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$venv = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (Test-Path -LiteralPath $venv) { $python = $venv }
if (-not (Test-Path -LiteralPath $python)) { $python = (Get-Command python).Source }
if ($Background) {
    $pidFile = Join-Path $PSScriptRoot 'work\remote\portal-agent.pid'
    if (Test-Path -LiteralPath $pidFile) {
        $managedId = [int](Get-Content -LiteralPath $pidFile)
        $managed = Get-CimInstance Win32_Process -Filter "ProcessId = $managedId"
        if ($managed -and $managed.CommandLine -match '-m\s+lili\.portal_agent') { Write-Output 'Conector da Lili já está ativo.'; exit 0 }
    }
    $process = Start-Process -FilePath $python -ArgumentList @('-m','lili.portal_agent') -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput 'work\remote\portal-agent.log' -RedirectStandardError 'work\remote\portal-agent-error.log'
    Set-Content -LiteralPath $pidFile -Value $process.Id
    Write-Output 'Conector do portal iniciado.'
} else { & $python -m lili.portal_agent }
