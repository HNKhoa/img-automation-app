$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$env:UV_CACHE_DIR = Join-Path $root ".uv-cache"
$env:UV_PYTHON_INSTALL_DIR = Join-Path $root ".uv-python"

if (-not (Test-Path ".venv\Scripts\python.exe")) {
  uv venv .venv --python 3.13 --managed-python
}

& ".venv\Scripts\python.exe" -c "import webview, PyInstaller" 2>$null
if ($LASTEXITCODE -ne 0) {
  uv pip install --python ".venv\Scripts\python.exe" pywebview pyinstaller
}

& ".venv\Scripts\python.exe" "tools\build_specs.py"

& ".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean "Img automation App.spec"
& ".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean "Img automation App Portable.spec"
& ".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean "Img automation App Debug Portable.spec"
& ".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean "Img automation App Debug.spec"

Copy-Item -LiteralPath ".env.example" -Destination "dist\.env.example" -Force
Copy-Item -LiteralPath ".env.example" -Destination "dist\Img automation App Portable\.env.example" -Force
Copy-Item -LiteralPath ".env.example" -Destination "dist\Img automation App Debug Portable\.env.example" -Force

@"
@echo off
cd /d "%~dp0Img automation App Portable"
start "" "Img automation App Portable.exe"
"@ | Set-Content -LiteralPath "dist\Open Img automation App.bat" -Encoding ASCII

@"
@echo off
cd /d "%~dp0Img automation App Debug Portable"
"Img automation App Debug Portable.exe"
pause
"@ | Set-Content -LiteralPath "dist\Open Img automation App Debug.bat" -Encoding ASCII

Write-Host "Built: $root\dist\Img automation App.exe"
Write-Host "Built portable: $root\dist\Img automation App Portable\Img automation App Portable.exe"
Write-Host "Built debug: $root\dist\Img automation App Debug.exe"
Write-Host "Open via: $root\dist\Open Img automation App.bat"
