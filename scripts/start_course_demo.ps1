param([int]$Port = 8765)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'use_d_runtime.ps1')
$courseDemoRepo = Split-Path -Parent $PSScriptRoot
$courseDemoPython = Join-Path $courseDemoRepo '.venv/Scripts/python.exe'
$courseDemoEntry = Join-Path $courseDemoRepo 'outputs/REL301m_Course_Recovery_20261101/launch.py'
if (-not (Test-Path -LiteralPath $courseDemoEntry)) { throw 'Build the course demo package first.' }
Write-Host "Open http://127.0.0.1:$Port ; Ctrl+C stops the inference server."
& $courseDemoPython $courseDemoEntry --port $Port
exit $LASTEXITCODE
