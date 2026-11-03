param([int]$Port = 8765)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'use_d_runtime.ps1')
$courseDemoRepo = Split-Path -Parent $PSScriptRoot
$courseDemoPython = Join-Path $courseDemoRepo '.venv/Scripts/python.exe'
$courseDemoEntry = Join-Path $courseDemoRepo 'outputs/REL301m_Course_Submission_Review_20261103/launch.py'
if (-not (Test-Path -LiteralPath $courseDemoEntry)) {
    $courseDemoEntry = Join-Path $courseDemoRepo 'outputs/REL301m_Course_Project_20261103_LunarPPO/launch.py'
}
if (-not (Test-Path -LiteralPath $courseDemoEntry)) {
    $courseDemoEntry = Join-Path $courseDemoRepo 'outputs/REL301m_Course_Project_20261103/launch.py'
}
if (-not (Test-Path -LiteralPath $courseDemoEntry)) {
    $courseDemoEntry = Join-Path $courseDemoRepo 'outputs/REL301m_Course_Project_20261101_httpfix/launch.py'
}
if (-not (Test-Path -LiteralPath $courseDemoEntry)) {
    $courseDemoEntry = Join-Path $courseDemoRepo 'outputs/REL301m_Course_Project_20261101/launch.py'
}
if (-not (Test-Path -LiteralPath $courseDemoEntry)) {
    $courseDemoEntry = Join-Path $courseDemoRepo 'outputs/REL301m_Course_Recovery_20261101/launch.py'
}
if (-not (Test-Path -LiteralPath $courseDemoEntry)) { throw 'Build the course demo package first.' }
$courseDemoBusyPorts = @([System.Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties().GetActiveTcpListeners() | ForEach-Object { $_.Port })
$courseDemoRequestedPort = $Port
while ($Port -in $courseDemoBusyPorts -and $Port -lt ($courseDemoRequestedPort + 10)) { $Port++ }
if ($Port -in $courseDemoBusyPorts) { throw 'No free demo port in the requested range.' }
if ($Port -ne $courseDemoRequestedPort) { Write-Host "Port $courseDemoRequestedPort is busy; using $Port for this release." }
Write-Host "Open http://127.0.0.1:$Port ; Ctrl+C stops the inference server."
& $courseDemoPython $courseDemoEntry --port $Port
exit $LASTEXITCODE
