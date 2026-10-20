param([ValidateSet('Preparar','Ativar','Desativar')][string]$Modo = 'Preparar')
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$remoteFolder = Join-Path $PSScriptRoot 'work\remote'
New-Item -ItemType Directory -Path $remoteFolder -Force | Out-Null
$gatewayPidFile = Join-Path $remoteFolder 'gateway.pid'
$tunnelPidFile = Join-Path $remoteFolder 'tunnel.pid'
$publicUrlFile = Join-Path $remoteFolder 'public-url.txt'
$tunnelBinary = Join-Path $PSScriptRoot 'work\tools\cloudflared.exe'

function Get-LiliManagedProcess([string]$PidFile, [string]$CommandPattern) {
    if (-not (Test-Path -LiteralPath $PidFile)) { return $null }
    $managedProcessId = [int](Get-Content -LiteralPath $PidFile)
    $managedProcess = Get-CimInstance Win32_Process -Filter "ProcessId = $managedProcessId"
    if ($managedProcess -and $managedProcess.CommandLine -match $CommandPattern) { return $managedProcess }
    return $null
}

if ($Modo -eq 'Desativar') {
    $tunnelProcess = Get-LiliManagedProcess $tunnelPidFile ([regex]::Escape($tunnelBinary))
    if ($tunnelProcess) { Stop-Process -Id $tunnelProcess.ProcessId }
    if (Test-Path -LiteralPath $publicUrlFile) { Remove-Item -LiteralPath $publicUrlFile }
    Write-Output 'Acesso externo desativado. O editor continua disponível neste computador.'
    exit 0
}

.\iniciar.ps1 -Background
$gatewayProcess = Get-LiliManagedProcess $gatewayPidFile '-m\s+lili\.remote'
if (-not $gatewayProcess) {
    $localPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
    $runtimePython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    if (Test-Path -LiteralPath $localPython) { $remotePython = $localPython }
    elseif (Test-Path -LiteralPath $runtimePython) { $remotePython = $runtimePython }
    else { $remotePython = (Get-Command python -ErrorAction Stop).Source }
    $gatewayProcess = Start-Process -FilePath $remotePython -ArgumentList @('-m','lili.remote') -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $remoteFolder 'gateway.log') -RedirectStandardError (Join-Path $remoteFolder 'gateway-error.log')
    Set-Content -LiteralPath $gatewayPidFile -Value $gatewayProcess.Id
}
if ($Modo -eq 'Preparar') {
    Write-Output 'Crie seu usuário e senha em http://127.0.0.1:8767/auth/setup'
    Write-Output 'Esta etapa é local. Nenhum acesso externo foi ativado.'
    exit 0
}
if (-not (Test-Path -LiteralPath (Join-Path $remoteFolder 'auth.json'))) {
    throw 'Crie primeiro o usuário e a senha em http://127.0.0.1:8767/auth/setup. Depois execute novamente com -Modo Ativar.'
}
$tunnelProcess = Get-LiliManagedProcess $tunnelPidFile ([regex]::Escape($tunnelBinary))
if ($tunnelProcess -and (Test-Path -LiteralPath $publicUrlFile)) {
    Write-Output "Estúdio remoto: $(Get-Content -LiteralPath $publicUrlFile)"
    exit 0
}
if (-not (Test-Path -LiteralPath $tunnelBinary)) {
    New-Item -ItemType Directory -Path (Split-Path $tunnelBinary) -Force | Out-Null
    $release = Invoke-RestMethod -Uri 'https://api.github.com/repos/cloudflare/cloudflared/releases/latest' -Headers @{ 'User-Agent' = 'Lili-local-editor' }
    $asset = $release.assets | Where-Object name -eq 'cloudflared-windows-amd64.exe' | Select-Object -First 1
    if (-not $asset -or $asset.digest -notmatch '^sha256:[a-f0-9]{64}$') { throw 'Não foi possível verificar o download oficial do cloudflared.' }
    $download = "$tunnelBinary.download"
    Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $download -UseBasicParsing
    $checksum = (Get-FileHash -LiteralPath $download -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($checksum -ne $asset.digest.Substring(7)) { throw 'O arquivo recebido não corresponde ao hash da publicação oficial.' }
    Move-Item -LiteralPath $download -Destination $tunnelBinary
    @{version=$release.tag_name;sha256=$checksum;source=$asset.browser_download_url} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $remoteFolder 'cloudflared-source.json')
}
$tunnelError = Join-Path $remoteFolder 'tunnel-error.log'
$tunnelProcess = Start-Process -FilePath $tunnelBinary -ArgumentList @('tunnel','--no-autoupdate','--url','http://127.0.0.1:8767') -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $remoteFolder 'tunnel.log') -RedirectStandardError $tunnelError
Set-Content -LiteralPath $tunnelPidFile -Value $tunnelProcess.Id
$deadline = (Get-Date).AddSeconds(45)
while ((Get-Date) -lt $deadline) {
    if ($tunnelProcess.HasExited) { throw 'O túnel não iniciou. Consulte work/remote/tunnel-error.log.' }
    if (Test-Path -LiteralPath $tunnelError) {
        $log = Get-Content -LiteralPath $tunnelError -Raw
        if ($log -match 'https://[a-z0-9-]+\.trycloudflare\.com') {
            $studioUrl = $Matches[0]
            Set-Content -LiteralPath $publicUrlFile -Value $studioUrl -Encoding ASCII
            Write-Output "Estúdio remoto: $studioUrl"
            Write-Output 'Abra no Safari e entre com seu usuário e senha. O endereço muda quando o túnel é recriado.'
            exit 0
        }
    }
    Start-Sleep -Milliseconds 250
}
Stop-Process -Id $tunnelProcess.Id
throw 'Não foi possível obter o endereço temporário. O acesso externo não foi ativado.'
