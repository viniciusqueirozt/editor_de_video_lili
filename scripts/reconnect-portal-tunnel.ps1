$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$tunnelBinary = Join-Path $projectRoot 'work\tools\cloudflared.exe'
$pidFile = Join-Path $projectRoot 'work\remote\tunnel.pid'
if (Test-Path -LiteralPath $pidFile) {
    $managedId = [int](Get-Content -LiteralPath $pidFile)
    $managedProcess = Get-CimInstance Win32_Process -Filter "ProcessId = $managedId"
    if ($managedProcess -and $managedProcess.CommandLine -match [regex]::Escape($tunnelBinary)) {
        Stop-Process -Id $managedId
    }
}
& (Join-Path $projectRoot 'acesso-remoto.ps1') -Modo Ativar
