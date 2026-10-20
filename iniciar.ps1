param([int]$Port = 8765, [switch]$Background)
$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$venvPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
$bundledPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (Test-Path -LiteralPath $venvPython) { $liliPython = $venvPython }
elseif (Test-Path -LiteralPath $bundledPython) { $liliPython = $bundledPython }
else { $liliPython = (Get-Command python -ErrorAction Stop).Source }
$localPackages = Join-Path $projectRoot 'work\python-packages'
if (Test-Path -LiteralPath $localPackages) { $env:PYTHONPATH = $localPackages }
& $liliPython -c 'import imageio_ffmpeg, PIL' 2>$null
if ($LASTEXITCODE -ne 0) { throw 'Instale as dependências: python -m pip install -r requirements.txt' }
New-Item -ItemType Directory -Path (Join-Path $projectRoot 'work') -Force | Out-Null
if ($Background) {
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/health" -TimeoutSec 2
        if ($response.ok -and $response.version -eq '0.1.0') { Write-Output "Lili já está disponível em http://127.0.0.1:$Port"; exit 0 }
    } catch { }
    $process = Start-Process -FilePath $liliPython -ArgumentList @('-m','lili.server','--port',"$Port") -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $projectRoot 'work\lili-server.log') -RedirectStandardError (Join-Path $projectRoot 'work\lili-server-error.log')
    Set-Content -LiteralPath (Join-Path $projectRoot 'work\lili-server.pid') -Value $process.Id
    Write-Output "Lili iniciada (processo $($process.Id)): http://127.0.0.1:$Port"
} else {
    & $liliPython -m lili.server --port $Port
}
