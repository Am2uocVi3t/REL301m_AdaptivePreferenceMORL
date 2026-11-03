$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'use_d_runtime.ps1')
$courseReportRepo = Split-Path -Parent $PSScriptRoot
Push-Location $courseReportRepo
try {
    $env:TECTONIC_CACHE_DIR = Join-Path $courseReportRepo 'artifacts/runtime/tectonic'
    $courseReportCompiler = Join-Path $courseReportRepo 'artifacts/latex-runtime/tectonic.exe'
    if (-not (Test-Path -LiteralPath $courseReportCompiler)) {
        throw 'Install the verified D-drive compiler described in docs/GPU_COURSE_RUNTIME.md first.'
    }
    & .venv/Scripts/python.exe scripts/reaudit_recovered_validation.py
    if ($LASTEXITCODE -ne 0) { throw 'Recovered numerical audit failed.' }
    & .venv/Scripts/python.exe scripts/analyze_envelope_feasibility.py --preserve-evidence
    if ($LASTEXITCODE -ne 0) { throw 'Envelope cohort is incomplete or failed numerical/source audit.' }
    & .venv/Scripts/python.exe scripts/plot_course_validation.py
    if ($LASTEXITCODE -ne 0) { throw 'Result figure/table generation failed.' }
    & .venv/Scripts/python.exe scripts/plot_onpolicy_confirmation.py
    if ($LASTEXITCODE -ne 0) { throw 'Minecart confirmation figure generation failed.' }
    & .venv/Scripts/python.exe scripts/plot_lunar_confirmation.py
    if ($LASTEXITCODE -ne 0) { throw 'Lunar confirmation figure generation failed.' }
    & .venv/Scripts/python.exe scripts/plot_preference_diagnosis.py
    if ($LASTEXITCODE -ne 0) { throw 'Preference diagnosis figure generation failed.' }
    & .venv/Scripts/python.exe scripts/audit_course_report.py
    if ($LASTEXITCODE -ne 0) { throw 'Report source/numeric/reference checks failed.' }
    $courseReportOutput = Join-Path $courseReportRepo 'outputs/course-report-latex'
    New-Item -ItemType Directory -Force $courseReportOutput | Out-Null
    & $courseReportCompiler -b https://data1b.fullyjustified.net/tlextras-2022.0r0.tar --keep-logs --keep-intermediates --outdir $courseReportOutput paper/REL301m/main.tex *> (Join-Path $courseReportOutput 'build.log')
    if ($LASTEXITCODE -ne 0) { throw 'LaTeX compilation failed; inspect outputs/course-report-latex/build.log.' }
    Copy-Item -LiteralPath (Join-Path $courseReportOutput 'main.pdf') -Destination (Join-Path $courseReportOutput 'REL301m_Course_Project_Report.pdf') -Force
    Write-Output (Join-Path $courseReportOutput 'REL301m_Course_Project_Report.pdf')
}
finally { Pop-Location }
