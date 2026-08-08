<#
  stop.ps1 - Matikan backend + frontend Fortunas dengan rapi.

  Pemakaian:
    powershell -ExecutionPolicy Bypass -File scripts\stop.ps1

  Urutan aman:
    1. Hentikan proses lewat PID yang dicatat start.ps1 (.run\*.pid),
       beserta anak-anaknya (uvicorn --reload dan npm run preview sama-sama
       memunculkan proses anak).
    2. Cadangan: target proses lewat command line (uvicorn/vite + port)
       lalu tree-kill sampai port 8000 + 5200 benar-benar bebas.
       (vite preview yang masih hidup juga bikin `npm ci` gagal EPERM —
       file native di node_modules terkunci.)
  Tidak ada state aplikasi yang rusak oleh penghentian ini (data akun/tenant
  di SQLite app/data/fortunas.db — atau Postgres bila DATABASE_URL di-set —
  dan server hanya melayani HTTP), jadi aman dijalankan kapan saja.
#>
[CmdletBinding()]
param(
  [int]$BackendPort = 8000,
  [int]$FrontendPort = 5200
)

$Root   = Split-Path -Parent $PSScriptRoot
$RunDir = Join-Path $Root '.run'

function Stop-FromPidFile([string]$name, [string]$label) {
  $file = Join-Path $RunDir "$name.pid"
  if (Test-Path $file) {
    $procId = (Get-Content $file -ErrorAction SilentlyContinue | Select-Object -First 1) -as [int]
    if ($procId -and (Get-Process -Id $procId -ErrorAction SilentlyContinue)) {
      cmd /c "taskkill /PID $procId /T /F >nul 2>nul"   # /T = ikut anak (worker uvicorn)
      Write-Host "  [stop] $label (PID $procId) dihentikan." -ForegroundColor DarkYellow
    }
    Remove-Item $file -ErrorAction SilentlyContinue
  }
}

function Free-Port([int]$Port, [string]$label, [string]$ProcName, [string]$CmdPattern) {
  # Get-NetTCPConnection sering menautkan socket ke PID reloader yang SUDAH mati
  # (uvicorn --reload), sementara worker anak yang benar-benar memegang port masih
  # hidup -> kill-by-owner tak pernah membebaskan port. Jadi target proses lewat
  # command line-nya (uvicorn/vite + nomor port), tree-kill, ulang.
  for ($try = 0; $try -lt 5; $try++) {
    $procs = Get-CimInstance Win32_Process -Filter "Name='$ProcName'" -ErrorAction SilentlyContinue |
      Where-Object { $_.CommandLine -and $_.CommandLine -match $CmdPattern -and $_.CommandLine -match "\b$Port\b" }
    $listen = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if (-not $procs -and -not $listen) { break }
    foreach ($pr in $procs) {
      cmd /c "taskkill /PID $($pr.ProcessId) /T /F >nul 2>nul"
      Write-Host "  [stop] $label (PID $($pr.ProcessId)) dihentikan." -ForegroundColor DarkYellow
    }
    foreach ($procId in ($listen.OwningProcess | Select-Object -Unique)) {
      if ($procId) { cmd /c "taskkill /PID $procId /T /F >nul 2>nul" }
    }
    Start-Sleep -Milliseconds 500
  }
}

Write-Host "Mematikan Fortunas..." -ForegroundColor Cyan
Stop-FromPidFile 'backend'  'Backend'
Stop-FromPidFile 'frontend' 'Frontend'
Start-Sleep -Milliseconds 400

# Cadangan berdasarkan command line (kalau pid file hilang / proses lepas).
Free-Port $BackendPort  'Backend'  'python.exe' 'uvicorn'
Free-Port $FrontendPort 'Frontend' 'node.exe'   'vite'

$stillBackend  = Get-NetTCPConnection -LocalPort $BackendPort  -State Listen -ErrorAction SilentlyContinue
$stillFrontend = Get-NetTCPConnection -LocalPort $FrontendPort -State Listen -ErrorAction SilentlyContinue

Write-Host ""
if ($stillBackend)  { Write-Host "[!] Port $BackendPort masih dipakai."  -ForegroundColor Yellow }
else                { Write-Host "[OK] Backend berhenti (port $BackendPort bebas)."  -ForegroundColor Green }
if ($stillFrontend) { Write-Host "[!] Port $FrontendPort masih dipakai." -ForegroundColor Yellow }
else                { Write-Host "[OK] Frontend berhenti (port $FrontendPort bebas)." -ForegroundColor Green }
