<#
  start.ps1 - Nyalakan backend (FastAPI/uvicorn) + frontend (React/Vite) Fortunas.

  Pemakaian:
    powershell -ExecutionPolicy Bypass -File scripts\start.ps1
    powershell -ExecutionPolicy Bypass -File scripts\start.ps1 -Rebuild   # build ulang dist dulu

  - Backend  : http://127.0.0.1:8000  (uvicorn app.main:app --reload)
  - Frontend : http://localhost:5200  (vite preview menyajikan frontend/dist)

  Kenapa `vite preview`, bukan `python -m http.server`: React Router memakai
  path riil (/briefing, /checkout, ...). http.server tidak punya SPA fallback,
  jadi refresh/deep-link di rute mana pun balas 404. `vite preview` menyajikan
  dist/ persis seperti nginx produksi (fallback ke index.html).

  Untuk DEV harian dengan hot-reload, jangan pakai script ini —
  cukup `cd frontend && npm run dev` (port 3000, proxy /api).

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
$FrontDir = Join-Path $Root 'frontend'
$DistDir  = Join-Path $FrontDir 'dist'
$RunDir  = Join-Path $Root '.run'
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null

function Free-Port([int]$Port, [string]$ProcName, [string]$CmdPattern) {
  # Target proses lewat command line (uvicorn/vite + port) lalu tree-kill:
  # andal terhadap uvicorn --reload yang meninggalkan worker anak + socket
  # yatim, dan terhadap `npm run preview` yang membungkus node beranak-pinak.
  for ($try = 0; $try -lt 5; $try++) {
    $procs = Get-CimInstance Win32_Process -Filter "Name='$ProcName'" -ErrorAction SilentlyContinue |
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
$Npm = (Get-Command npm.cmd -ErrorAction SilentlyContinue).Source
if (-not $Npm) { throw "npm tidak ditemukan di PATH (butuh Node >= 20.19)" }

# Rebuild dist (opsional)
if ($Rebuild) {
  Write-Host "Membangun ulang React (vite build)..." -ForegroundColor Cyan
  Push-Location $FrontDir
  try { & $Npm run build; if ($LASTEXITCODE -ne 0) { throw "npm run build gagal (exit $LASTEXITCODE)" } }
  finally { Pop-Location }
}
if (-not (Test-Path (Join-Path $DistDir 'index.html'))) {
  Write-Host "Build dist belum ada. Menjalankan 'npm run build'..." -ForegroundColor Cyan
  Push-Location $FrontDir
  try {
    if (-not (Test-Path (Join-Path $FrontDir 'node_modules'))) {
      Write-Host "  node_modules belum ada -> npm ci dulu..." -ForegroundColor Cyan
      & $Npm ci; if ($LASTEXITCODE -ne 0) { throw "npm ci gagal (exit $LASTEXITCODE)" }
    }
    & $Npm run build; if ($LASTEXITCODE -ne 0) { throw "npm run build gagal (exit $LASTEXITCODE)" }
  } finally { Pop-Location }
}

# Bersihkan port bekas sesi lama
Write-Host "Menyiapkan port..." -ForegroundColor Cyan
Free-Port $BackendPort  'python.exe' 'uvicorn'
Free-Port $FrontendPort 'node.exe'   'vite'
Start-Sleep -Milliseconds 500

# Start backend
Write-Host "Menyalakan backend di :$BackendPort ..." -ForegroundColor Cyan
$backend = Start-Process -FilePath $Python `
  -ArgumentList @('-m','uvicorn','app.main:app','--host','127.0.0.1','--port',"$BackendPort",'--reload') `
  -WorkingDirectory $Root -PassThru -WindowStyle Hidden `
  -RedirectStandardOutput (Join-Path $RunDir 'backend.out.log') `
  -RedirectStandardError  (Join-Path $RunDir 'backend.err.log')
$backend.Id | Out-File -Encoding ascii (Join-Path $RunDir 'backend.pid')

# Start frontend (vite preview menyajikan dist/ dengan SPA fallback).
# ⚠ vite preview MENGUNCI file native di node_modules selama hidup —
#   `npm ci` akan gagal EPERM kalau preview masih jalan; stop.ps1 dulu.
Write-Host "Menyalakan frontend di :$FrontendPort ..." -ForegroundColor Cyan
$frontend = Start-Process -FilePath $Npm `
  -ArgumentList @('run','preview','--','--port',"$FrontendPort",'--strictPort') `
  -WorkingDirectory $FrontDir -PassThru -WindowStyle Hidden `
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
