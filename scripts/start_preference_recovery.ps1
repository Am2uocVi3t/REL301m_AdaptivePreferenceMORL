$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'use_d_runtime.ps1')
$diagnosisRepoRoot = Split-Path -Parent $PSScriptRoot
$diagnosisOutput = Join-Path $diagnosisRepoRoot 'artifacts/preference-recovery-p2-v1'
if (Test-Path -LiteralPath (Join-Path $diagnosisOutput 'execution_status.json')) { throw 'Inspect the existing diagnostic; do not launch it again.' }
New-Item -ItemType Directory -Force -Path $diagnosisOutput | Out-Null
$diagnosisBasePython = & (Join-Path $diagnosisRepoRoot 'artifacts/gpu-runtime/Scripts/python.exe') -c 'import sys; print(sys._base_executable)'
if ($LASTEXITCODE -ne 0) { throw 'Qualified Python resolution failed.' }
$diagnosisEnvironment = @(Get-ChildItem Env: | Where-Object { $_.Name -ne '__PYVENV_LAUNCHER__' } | ForEach-Object { $_.Name + '=' + $_.Value })
$diagnosisEnvironment += '__PYVENV_LAUNCHER__=' + (Join-Path $diagnosisRepoRoot 'artifacts/gpu-runtime/Scripts/python.exe')
$diagnosisStartup = New-CimInstance -ClassName Win32_ProcessStartup -ClientOnly -Property @{CreateFlags=[uint32]0x01000608; ShowWindow=[uint16]0; EnvironmentVariables=[string[]]$diagnosisEnvironment}
$diagnosisCommand = '"{0}" "{1}"' -f $diagnosisBasePython.Trim(), (Join-Path $diagnosisRepoRoot 'scripts/run_preference_recovery_cohort.py')
$diagnosisProcess = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine=$diagnosisCommand; CurrentDirectory=$diagnosisRepoRoot; ProcessStartupInformation=$diagnosisStartup}
if ($diagnosisProcess.ReturnValue -ne 0) { throw ('Independent diagnostic launch failed: ' + $diagnosisProcess.ReturnValue) }
Write-Output ('Independent diagnostic coordinator PID: ' + $diagnosisProcess.ProcessId)
