$ErrorActionPreference = 'Stop'
if ([IO.Path]::GetPathRoot($PSScriptRoot) -ne 'D:\') {
    throw 'Extract this entire package onto D: before running it. Nothing was downloaded.'
}
$recoveryPackageRuntime = Join-Path $PSScriptRoot '.runtime'
$recoveryPackageVariables = @{
    TEMP = 'tmp'; TMP = 'tmp'; TMPDIR = 'tmp'; UV_CACHE_DIR = 'uv-cache'
    UV_PYTHON_INSTALL_DIR = 'python'; UV_PYTHON_BIN_DIR = 'python-bin'
    UV_TOOL_DIR = 'uv-tools'; UV_TOOL_BIN_DIR = 'uv-bin'
    PIP_CACHE_DIR = 'pip-cache'; PYTHONPYCACHEPREFIX = 'pycache'
    MPLCONFIGDIR = 'matplotlib'; TORCH_HOME = 'torch'; XDG_CACHE_HOME = 'cache'
    PYTHONUSERBASE = 'python-user'; HF_HOME = 'huggingface'
}
foreach ($recoveryPackageVariable in $recoveryPackageVariables.GetEnumerator()) {
    $recoveryPackagePath = Join-Path $recoveryPackageRuntime $recoveryPackageVariable.Value
    New-Item -ItemType Directory -Force -Path $recoveryPackagePath | Out-Null
    [Environment]::SetEnvironmentVariable($recoveryPackageVariable.Key, $recoveryPackagePath, 'Process')
}
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:OMP_NUM_THREADS = '4'
$env:MKL_NUM_THREADS = '4'
$env:SDL_VIDEODRIVER = 'dummy'
$env:SDL_AUDIODRIVER = 'dummy'
