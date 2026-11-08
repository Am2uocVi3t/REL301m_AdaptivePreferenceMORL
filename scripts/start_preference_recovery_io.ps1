param([switch]$ResumeExisting)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'use_d_runtime.ps1')
if (-not $ResumeExisting) { throw 'This amendment only resumes the inspected existing cohort; pass -ResumeExisting.' }
$p2IoRoot = Split-Path -Parent $PSScriptRoot
$p2IoExisting = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { ($_.CommandLine -match 'run_preference_recovery(_io)?_cohort.py') -and ($_.CommandLine -like ('*' + $p2IoRoot + '*')) })
if ($p2IoExisting.Count -gt 0) { throw 'A P2 coordinator is already alive. Inspect it; do not launch a duplicate.' }
$p2IoStatus = Join-Path $p2IoRoot 'artifacts/preference-recovery-p2-v1/execution_status.json'
if (-not (Test-Path -LiteralPath $p2IoStatus)) { throw 'The existing P2 execution record is missing.' }
$p2IoPython = Join-Path $p2IoRoot 'artifacts/gpu-runtime/Scripts/python.exe'
$p2IoBase = & $p2IoPython -c 'import sys; print(sys._base_executable)'
if ($LASTEXITCODE -ne 0) { throw 'Cannot resolve the qualified GPU runtime.' }
$p2IoEnvironment = @(Get-ChildItem Env: | Where-Object { $_.Name -ne '__PYVENV_LAUNCHER__' } | ForEach-Object { $_.Name + '=' + $_.Value })
$p2IoEnvironment += '__PYVENV_LAUNCHER__=' + $p2IoPython
$p2IoStartup = New-CimInstance -ClassName Win32_ProcessStartup -ClientOnly -Property @{CreateFlags=[uint32]0x01000608; ShowWindow=[uint16]0; EnvironmentVariables=[string[]]$p2IoEnvironment}
$p2IoCommand = '"{0}" "{1}" --resume-existing' -f $p2IoBase.Trim(), (Join-Path $p2IoRoot 'scripts/run_preference_recovery_io_cohort.py')
$p2IoProcess = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine=$p2IoCommand; CurrentDirectory=$p2IoRoot; ProcessStartupInformation=$p2IoStartup}
if ($p2IoProcess.ReturnValue -ne 0) { throw ('Independent I/O recovery launch failed: ' + $p2IoProcess.ReturnValue) }
Write-Output ('P2 I/O recovery coordinator PID: ' + $p2IoProcess.ProcessId)
