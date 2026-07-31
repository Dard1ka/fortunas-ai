<#
  start.ps1 - Nyalakan backend (FastAPI/uvicorn) + frontend (Flutter web) Fortunas.

  Pemakaian:
    powershell -ExecutionPolicy Bypass -File scripts\start.ps1
    powershell -ExecutionPolicy Bypass -File scripts\start.ps1 -Rebuild   # build ulang web dulu

  - Backend  : http://127.0.0.1:8000  (uvicorn app.main:app --reload)
  - Frontend : http://localhost:5200  (menyajikan mobile/build/web)

  PID + log disimpan di .run\ supaya stop.ps1 bisa mematikan dengan rapi.
#>
[CmdletBinding()]
param(
  [switch]$Rebuild,
  [int]$BackendPort = 8000,
  [int]$FrontendPort = 5200
)

$ErrorActionPreference = 'Stop'
$Root    = Split-Path -Parent $PSScriptRoot          # ...\fortunas-ai
$Python  = Join-Path $Root '.venv\Scripts\python.exe'
$WebDir  = Join-Path $Root 'mobile\build\web'
$RunDir  = Join-Path $Root '.run'
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null

function Free-Port([int]$Port, [string]$CmdPattern) {
  # Target proses lewat command line (uvicorn/http.server + port) lalu tree-kill:
  # andal terhadap uvicorn --reload yang meninggalkan worker anak + socket yatim.
  for ($try = 0; $try -lt 5; $try++) {
    $procs = Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
      Where-Object { $_.CommandLine -and $_.CommandLine -match $CmdPattern -and $_.CommandLine -match "\b$Port\b" }
    $listen = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if (-not $procs -and -not $listen) { break }
    foreach ($pr in $procs) {
      Write-Host "  membebaskan port $Port (menghentikan PID $($pr.ProcessId))..." -ForegroundColor DarkYellow
      cmd /c "taskkill /PID $($pr.ProcessId) /T /F >nul 2>nul"
    }
    foreach ($procId in ($listen.OwningProcess | Select-Object -Unique)) {
      if ($procId) { cmd /c "taskkill /PID $procId /T /F >nul 2>nul" }
    }
    Start-Sleep -Milliseconds 500
  }
}

if (-not (Test-Path $Python)) { throw "Python venv tidak ditemukan: $Python" }

# Rebuild web (opsional)
if ($Rebuild) {
  Write-Host "Membangun ulang Flutter web..." -ForegroundColor Cyan
  Push-Location (Join-Path $Root 'mobile')
  try { & flutter build web } finally { Pop-Location }
}
if (-not (Test-Path (Join-Path $WebDir 'main.dart.js'))) {
  Write-Host "Build web belum ada. Menjalankan 'flutter build web'..." -ForegroundColor Cyan
  Push-Location (Join-Path $Root 'mobile')
  try { & flutter build web } finally { Pop-Location }
}

# Bersihkan port bekas sesi lama
Write-Host "Menyiapkan port..." -ForegroundColor Cyan
Free-Port $BackendPort  'uvicorn'
Free-Port $FrontendPort 'http\.server'
Start-Sleep -Milliseconds 500

# Start backend
Write-Host "Menyalakan backend di :$BackendPort ..." -ForegroundColor Cyan
$backend = Start-Process -FilePath $Python `
  -ArgumentList @('-m','uvicorn','app.main:app','--host','127.0.0.1','--port',"$BackendPort",'--reload') `
  -WorkingDirectory $Root -PassThru -WindowStyle Hidden `
  -RedirectStandardOutput (Join-Path $RunDir 'backend.out.log') `
  -RedirectStandardError  (Join-Path $RunDir 'backend.err.log')
$backend.Id | Out-File -Encoding ascii (Join-Path $RunDir 'backend.pid')

# Start frontend
Write-Host "Menyalakan frontend di :$FrontendPort ..." -ForegroundColor Cyan
$frontend = Start-Process -FilePath $Python `
  -ArgumentList @('-m','http.server',"$FrontendPort",'--directory',$WebDir) `
  -WorkingDirectory $WebDir -PassThru -WindowStyle Hidden `
  -RedirectStandardOutput (Join-Path $RunDir 'frontend.out.log') `
  -RedirectStandardError  (Join-Path $RunDir 'frontend.err.log')
$frontend.Id | Out-File -Encoding ascii (Join-Path $RunDir 'frontend.pid')

# Tunggu backend siap (health check)
Write-Host "Menunggu backend siap..." -ForegroundColor Cyan
$ok = $false
for ($i = 0; $i -lt 20; $i++) {
  try {
    $r = Invoke-WebRequest "http://127.0.0.1:$BackendPort/health" -UseBasicParsing -TimeoutSec 3
    if ($r.StatusCode -eq 200) { $ok = $true; break }
  } catch { Start-Sleep -Seconds 2 }
}

Write-Host ""
if ($ok) { Write-Host "[OK] Backend  : http://127.0.0.1:$BackendPort" -ForegroundColor Green }
else     { Write-Host "[!]  Backend belum merespons - cek .run\backend.err.log" -ForegroundColor Yellow }
Write-Host "[OK] Frontend : http://localhost:$FrontendPort  (backend PID $($backend.Id), frontend PID $($frontend.Id))" -ForegroundColor Green
Write-Host ""
Write-Host "Buka http://localhost:$FrontendPort di browser (Ctrl+Shift+R kalau baru rebuild)." -ForegroundColor Gray
Write-Host "Matikan dengan: powershell -ExecutionPolicy Bypass -File scripts\stop.ps1" -ForegroundColor Gray
