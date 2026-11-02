param([int]$Port = 8770, [switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'use_d_runtime.ps1')
$trainingMonitorRoot = Split-Path -Parent $PSScriptRoot
$trainingMonitorUrl = 'http://127.0.0.1:' + $Port
$trainingMonitorReady = $false
try {
    $trainingMonitorResponse = Invoke-WebRequest -Uri ($trainingMonitorUrl + '/api/state') -UseBasicParsing -TimeoutSec 4
    if ($trainingMonitorResponse.Headers['X-MORL-Monitor'] -ne 'read-only-v1') {
        throw 'This port belongs to another application. Choose another -Port.'
    }
    $trainingMonitorReady = $true
} catch [System.Net.WebException] {
    $trainingMonitorReady = $false
} catch [System.Net.Http.HttpRequestException] {
    $trainingMonitorReady = $false
} catch [System.OperationCanceledException] {
    $trainingMonitorReady = $false
}
if (-not $trainingMonitorReady) {
    $trainingMonitorVenv = Join-Path $trainingMonitorRoot '.venv/Scripts/python.exe'
    $trainingMonitorBase = & $trainingMonitorVenv -c 'import sys; print(sys._base_executable)'
    if ($LASTEXITCODE -ne 0) { throw 'Cannot resolve the local Python runtime.' }
    $trainingMonitorEnvironment = @(Get-ChildItem Env: | Where-Object { $_.Name -ne '__PYVENV_LAUNCHER__' } | ForEach-Object { $_.Name + '=' + $_.Value })
    $trainingMonitorEnvironment += '__PYVENV_LAUNCHER__=' + $trainingMonitorVenv
    $trainingMonitorStartup = New-CimInstance -ClassName Win32_ProcessStartup -ClientOnly -Property @{CreateFlags=[uint32]0x01000608; ShowWindow=[uint16]0; EnvironmentVariables=[string[]]$trainingMonitorEnvironment}
    $trainingMonitorCommand = '"{0}" "{1}" --port {2}' -f $trainingMonitorBase.Trim(), (Join-Path $trainingMonitorRoot 'monitor/server.py'), $Port
    $trainingMonitorProcess = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine=$trainingMonitorCommand; CurrentDirectory=$trainingMonitorRoot; ProcessStartupInformation=$trainingMonitorStartup}
    if ($trainingMonitorProcess.ReturnValue -ne 0) { throw ('Monitor launch failed: ' + $trainingMonitorProcess.ReturnValue) }
    Write-Host ('Monitor server PID: ' + $trainingMonitorProcess.ProcessId)
    for ($trainingMonitorAttempt = 0; $trainingMonitorAttempt -lt 20; $trainingMonitorAttempt++) {
        Start-Sleep -Milliseconds 400
        try {
            $trainingMonitorResponse = Invoke-WebRequest -Uri ($trainingMonitorUrl + '/api/state') -UseBasicParsing -TimeoutSec 5
            if ($trainingMonitorResponse.Headers['X-MORL-Monitor'] -eq 'read-only-v1') { $trainingMonitorReady = $true; break }
        } catch [System.Net.WebException] {
            continue
        } catch [System.Net.Http.HttpRequestException] {
            continue
        } catch [System.OperationCanceledException] {
            continue
        }
    }
    if (-not $trainingMonitorReady) { throw 'Monitor did not become ready. Inspect artifacts/training-monitor/server.log.' }
}
Write-Host ('Training console: ' + $trainingMonitorUrl)
Write-Host 'Read-only. Closing this window or dashboard does not stop training.'
if (-not $NoBrowser) { Start-Process $trainingMonitorUrl }
