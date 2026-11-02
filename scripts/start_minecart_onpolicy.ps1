param([switch]$Resume)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'use_d_runtime.ps1')
$onpolicyRepo = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $onpolicyRepo
$onpolicyRoot = Join-Path $onpolicyRepo 'artifacts/minecart-onpolicy-specialist-v1'
New-Item -ItemType Directory -Force -Path $onpolicyRoot | Out-Null
$onpolicyName = 'minecart-v0_S_seed20264111'
$onpolicyRun = Join-Path $onpolicyRoot "runs/$onpolicyName"
if (Test-Path -LiteralPath (Join-Path $onpolicyRun 'complete.json')) { throw 'Completed study must not be restarted.' }
$onpolicyExisting = Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like '*run_minecart_onpolicy.py*' -and $_.CommandLine -notlike '*--engineering*' }
if ($onpolicyExisting) { throw 'A specialist worker already exists; inspect the native terminal.' }
if ((Test-Path -LiteralPath (Join-Path $onpolicyRun 'manifest.json')) -and -not $Resume) { throw 'Existing run requires explicit inspected resume.' }
if ($Resume -and -not (Test-Path -LiteralPath (Join-Path $onpolicyRun 'resume_latest.json'))) { throw 'No durable snapshot exists.' }
if ($Resume) {
    $onpolicyStamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    foreach ($onpolicyStream in @('stdout', 'stderr')) {
        $onpolicyLog = Join-Path $onpolicyRoot "$onpolicyName.$onpolicyStream.log"
        if (Test-Path -LiteralPath $onpolicyLog) {
            Move-Item -LiteralPath $onpolicyLog -Destination (Join-Path $onpolicyRoot "$onpolicyName.$onpolicyStream.$onpolicyStamp.log")
        }
    }
}
$onpolicyPython = Join-Path $onpolicyRepo 'artifacts/gpu-runtime/Scripts/python.exe'
$onpolicyEntry = Join-Path $onpolicyRepo 'scripts/run_minecart_onpolicy.py'
$onpolicyArgs = '"' + $onpolicyEntry + '" --device cuda'
if ($Resume) { $onpolicyArgs += ' --resume' }
$onpolicyProcess = Start-Process -FilePath $onpolicyPython -ArgumentList $onpolicyArgs -WorkingDirectory $onpolicyRepo -WindowStyle Hidden -RedirectStandardOutput (Join-Path $onpolicyRoot "$onpolicyName.stdout.log") -RedirectStandardError (Join-Path $onpolicyRoot "$onpolicyName.stderr.log") -PassThru
Write-Output "Minecart specialist process started: PID $($onpolicyProcess.Id). Check native terminal for liveness; this message is not a training-success claim."
