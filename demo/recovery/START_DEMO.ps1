param([int]$Port = 8765)
. (Join-Path $PSScriptRoot 'SET_D_ENV.ps1')
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path -LiteralPath '.venv/Scripts/python.exe')) {
    throw 'Run INSTALL_D.ps1 once before START_DEMO.bat. No install was started automatically.'
}
& .venv/Scripts/python.exe launch.py --port $Port
exit $LASTEXITCODE
