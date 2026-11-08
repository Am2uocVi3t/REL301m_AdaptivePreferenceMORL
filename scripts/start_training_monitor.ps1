param([switch]$Once)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'use_d_runtime.ps1')
$trainingTerminalRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $trainingTerminalRoot
$trainingTerminalPython = Join-Path $trainingTerminalRoot '.venv/Scripts/python.exe'
$trainingTerminalEntry = Join-Path $trainingTerminalRoot 'scripts/training_terminal.py'
if ($Once) {
    & $trainingTerminalPython $trainingTerminalEntry --once
} else {
    & $trainingTerminalPython $trainingTerminalEntry
}
exit $LASTEXITCODE
