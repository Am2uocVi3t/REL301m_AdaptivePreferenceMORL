param([switch]$QualifyOnly, [switch]$ResumeExisting)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'use_d_runtime.ps1')
$recoveryLaunchRoot = Split-Path -Parent $PSScriptRoot
$recoveryLaunchDirectory = if ($QualifyOnly) { Join-Path $recoveryLaunchRoot 'artifacts/durable-launch-witness-v5' } else { Join-Path $recoveryLaunchRoot 'artifacts/credit-assignment-recovery-v1' }
$recoveryIdentityPath = Join-Path $recoveryLaunchDirectory 'worker_identity.json'
if (Test-Path -LiteralPath $recoveryIdentityPath) {
    $recoveryIdentity = Get-Content -LiteralPath $recoveryIdentityPath -Raw | ConvertFrom-Json
    $recoveryExistingProcess = Get-Process -Id $recoveryIdentity.pid -ErrorAction SilentlyContinue
    if (($null -ne $recoveryExistingProcess) -and ($recoveryExistingProcess.StartTime.ToFileTimeUtc().ToString() -eq $recoveryIdentity.birth)) {
        throw 'The recorded independent worker is still alive. Inspect status; do not launch a duplicate.'
    }
}
if ((Test-Path -LiteralPath (Join-Path $recoveryLaunchDirectory 'request.json')) -and (-not $ResumeExisting)) {
    throw 'A launch request already exists. Inspect process identity and status before another launch.'
}
New-Item -ItemType Directory -Force -Path $recoveryLaunchDirectory | Out-Null
$recoveryLaunchRequest = Join-Path $recoveryLaunchDirectory 'request.json'
$recoveryLaunchPayload = @{
    mode = $(if ($QualifyOnly) { 'qualification' } else { 'main' })
    directory = $recoveryLaunchDirectory
    token = [guid]::NewGuid().ToString()
    resume_existing = [bool]$ResumeExisting
} | ConvertTo-Json
[System.IO.File]::WriteAllText($recoveryLaunchRequest, $recoveryLaunchPayload, [System.Text.UTF8Encoding]::new($false))
$recoveryBaseInterpreter = & (Join-Path $recoveryLaunchRoot 'artifacts/gpu-runtime/Scripts/python.exe') -c 'import sys; print(sys._base_executable)'
if ($LASTEXITCODE -ne 0) { throw 'Could not resolve the qualified Python interpreter.' }
$recoveryLaunchCommand = '"{0}" "{1}" --request "{2}"' -f $recoveryBaseInterpreter.Trim(), (Join-Path $recoveryLaunchRoot 'scripts/launch_credit_recovery.py'), $recoveryLaunchRequest
if ($QualifyOnly) { $recoveryLaunchCommand += ' --test-parent' }
$recoveryEnvironment = @(Get-ChildItem Env: | Where-Object { $_.Name -ne '__PYVENV_LAUNCHER__' } | ForEach-Object { $_.Name + '=' + $_.Value })
$recoveryEnvironment += '__PYVENV_LAUNCHER__=' + (Join-Path $recoveryLaunchRoot 'artifacts/gpu-runtime/Scripts/python.exe')
$recoveryStartup = New-CimInstance -ClassName Win32_ProcessStartup -ClientOnly -Property @{CreateFlags=[uint32]0x01000608; ShowWindow=[uint16]0; EnvironmentVariables=[string[]]$recoveryEnvironment}
$recoveryLaunchResult = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine=$recoveryLaunchCommand; CurrentDirectory=$recoveryLaunchRoot; ProcessStartupInformation=$recoveryStartup}
if ($recoveryLaunchResult.ReturnValue -ne 0) { throw ('Independent Windows process creation failed: ' + $recoveryLaunchResult.ReturnValue) }
Write-Output ('Windows service-created bootstrap PID: ' + $recoveryLaunchResult.ProcessId + '; worker receipt: ' + (Join-Path $recoveryLaunchDirectory 'launch_receipt.json'))
