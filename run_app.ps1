$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$env:UV_CACHE_DIR = Join-Path $root ".uv-cache"
$env:UV_PYTHON_INSTALL_DIR = Join-Path $root ".uv-python"

if (-not (Test-Path ".venv\Scripts\python.exe")) {
  uv venv .venv --python 3.13 --managed-python
}

& ".venv\Scripts\python.exe" -c "import webview" 2>$null
if ($LASTEXITCODE -ne 0) {
  uv pip install --offline --python ".venv\Scripts\python.exe" pywebview
  if ($LASTEXITCODE -ne 0) {
    uv pip install --python ".venv\Scripts\python.exe" pywebview
  }
}

& ".venv\Scripts\python.exe" app.py
