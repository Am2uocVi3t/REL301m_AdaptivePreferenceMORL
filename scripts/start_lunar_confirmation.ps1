param([int]$ResumeSeed = 0)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'use_d_runtime.ps1')
$confirmationRepo = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $confirmationRepo
$confirmationRoot = Join-Path $confirmationRepo 'artifacts/lunar-onpolicy-confirmation-v1'
$confirmationPlan = Get-Content -LiteralPath 'configs/experiments/lunar_onpolicy_confirmation_v1.json' -Raw | ConvertFrom-Json
$confirmationSeeds = @($confirmationPlan.seeds)
$confirmationExisting = Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -match 'run_lunar_(onpolicy|confirmation)\.py' -and $_.CommandLine -notlike '*--engineering*' -and $_.CommandLine -like "*$confirmationRepo*" }
if ($confirmationExisting) { throw 'An on-policy worker already exists; inspect native terminal.' }
New-Item -ItemType Directory -Force -Path $confirmationRoot | Out-Null
if ($ResumeSeed -ne 0) {
    if ($ResumeSeed -notin $confirmationSeeds) { throw 'Resume seed outside frozen cohort.' }
    $confirmationSeeds = @($ResumeSeed)
} elseif (Test-Path -LiteralPath (Join-Path $confirmationRoot 'cohort_manifest.json')) {
    throw 'Existing cohort requires explicit inspected recovery; never relaunch completed runs.'
}
foreach ($confirmationSeed in $confirmationSeeds) {
    $confirmationRun = Join-Path $confirmationRoot "runs/mo-lunar-lander-v3_LG_seed$confirmationSeed"
    if (Test-Path -LiteralPath (Join-Path $confirmationRun 'complete.json')) { throw 'Completed run is immutable.' }
    if ($ResumeSeed -ne 0) {
        if (-not (Test-Path -LiteralPath (Join-Path $confirmationRun 'resume_latest.json'))) { throw 'No durable snapshot exists.' }
    } elseif (Test-Path -LiteralPath (Join-Path $confirmationRun 'manifest.json')) {
        throw 'Existing seed requires inspected resume.'
    }
}
if ($ResumeSeed -eq 0) {
    $confirmationManifest = @{ study_id = $confirmationPlan.study_id; seeds = $confirmationSeeds; source_commit = (git rev-parse HEAD); plan_sha256 = (Get-FileHash -LiteralPath 'configs/experiments/lunar_onpolicy_confirmation_v1.json' -Algorithm SHA256).Hash.ToLower(); launched_utc = (Get-Date).ToUniversalTime().ToString('o') }
    $confirmationTemporary = Join-Path $confirmationRoot 'cohort_manifest.json.tmp'
    $confirmationManifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $confirmationTemporary -Encoding utf8
    Move-Item -LiteralPath $confirmationTemporary -Destination (Join-Path $confirmationRoot 'cohort_manifest.json')
}
foreach ($confirmationSeed in $confirmationSeeds) {
    $confirmationName = "mo-lunar-lander-v3_LG_seed$confirmationSeed"
    if ($ResumeSeed -ne 0) {
        $confirmationStamp = Get-Date -Format 'yyyyMMdd-HHmmss'
        foreach ($confirmationStream in @('stdout', 'stderr')) {
            $confirmationLog = Join-Path $confirmationRoot "$confirmationName.$confirmationStream.log"
            if (Test-Path -LiteralPath $confirmationLog) { Move-Item -LiteralPath $confirmationLog -Destination (Join-Path $confirmationRoot "$confirmationName.$confirmationStream.$confirmationStamp.log") }
        }
    }
    $confirmationArguments = '"' + (Join-Path $confirmationRepo 'scripts/run_lunar_confirmation.py') + '" --device cuda --seed ' + $confirmationSeed
    if ($ResumeSeed -ne 0) { $confirmationArguments += ' --resume' }
    $confirmationProcess = Start-Process -FilePath (Join-Path $confirmationRepo 'artifacts/gpu-runtime/Scripts/python.exe') -ArgumentList $confirmationArguments -WorkingDirectory $confirmationRepo -WindowStyle Hidden -RedirectStandardOutput (Join-Path $confirmationRoot "$confirmationName.stdout.log") -RedirectStandardError (Join-Path $confirmationRoot "$confirmationName.stderr.log") -PassThru
    Write-Output "Started confirmation seed $confirmationSeed, PID $($confirmationProcess.Id); verify actual progress in native terminal."
}
