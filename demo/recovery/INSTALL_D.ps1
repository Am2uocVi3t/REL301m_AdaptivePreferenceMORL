$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
. (Join-Path $PSScriptRoot 'SET_D_ENV.ps1')
$recoveryPackageUv = Join-Path $PSScriptRoot 'tools/uv.exe'
& $recoveryPackageUv python install 3.11.18 --no-bin
if ($LASTEXITCODE -ne 0) { throw 'Python installation failed; inspect output. No retry was started.' }
if (-not (Test-Path -LiteralPath '.venv/Scripts/python.exe')) {
    & $recoveryPackageUv venv --python 3.11.18 .venv
    if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed.' }
}
& $recoveryPackageUv pip install --python .venv/Scripts/python.exe -r requirements-windows.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
& $recoveryPackageUv pip check --python .venv/Scripts/python.exe
if ($LASTEXITCODE -ne 0) { throw 'Dependency consistency check failed.' }
Write-Host 'Installed on D:. Use START_DEMO.bat to run inference. No training was launched.'
