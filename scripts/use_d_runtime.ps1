# Dot-source this file before installs, tests, training, rendering or packaging.
$ErrorActionPreference = 'Stop'
$recoveryRepoRoot = Split-Path -Parent $PSScriptRoot
if ([System.IO.Path]::GetPathRoot($recoveryRepoRoot) -ne 'D:\') {
    throw 'This recovery workflow requires its workspace on D:.'
}
$recoveryCacheRoot = Join-Path $recoveryRepoRoot 'artifacts/runtime'
$recoveryStorageVariables = @{
    TEMP = 'tmp'; TMP = 'tmp'; TMPDIR = 'tmp'
    UV_CACHE_DIR = 'uv-cache'; PIP_CACHE_DIR = 'pip-cache'
    PYTHONPYCACHEPREFIX = 'pycache'; PYTHONUSERBASE = 'python-user'
    MPLCONFIGDIR = 'matplotlib'; TORCH_HOME = 'torch'
    HF_HOME = 'huggingface'; XDG_CACHE_HOME = 'cache'
    WANDB_DIR = 'wandb'; WANDB_CACHE_DIR = 'wandb-cache'
    WANDB_CONFIG_DIR = 'wandb-config'; WANDB_DATA_DIR = 'wandb-data'
    PLAYWRIGHT_BROWSERS_PATH = 'playwright'; npm_config_cache = 'npm-cache'
}
foreach ($recoveryVariable in $recoveryStorageVariables.GetEnumerator()) {
    $recoveryStoragePath = Join-Path $recoveryCacheRoot $recoveryVariable.Value
    New-Item -ItemType Directory -Force -Path $recoveryStoragePath | Out-Null
    [Environment]::SetEnvironmentVariable($recoveryVariable.Key, $recoveryStoragePath, 'Process')
}
$env:OMP_NUM_THREADS = '4'
$env:MKL_NUM_THREADS = '4'
$env:OPENBLAS_NUM_THREADS = '4'
$env:SDL_VIDEODRIVER = 'dummy'
$env:SDL_AUDIODRIVER = 'dummy'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
