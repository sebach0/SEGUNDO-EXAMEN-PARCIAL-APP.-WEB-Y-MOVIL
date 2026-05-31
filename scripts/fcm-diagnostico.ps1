param(
  [switch]$FixEnv = $false,
  [switch]$RebuildBackend = $false
)

$ErrorActionPreference = "Stop"

function Step($msg) {
  Write-Host ""
  Write-Host "==> $msg" -ForegroundColor Cyan
}

function Warn($msg) {
  Write-Host "WARN: $msg" -ForegroundColor Yellow
}

function Ok($msg) {
  Write-Host "OK: $msg" -ForegroundColor Green
}

function Fail($msg) {
  Write-Host "FAIL: $msg" -ForegroundColor Red
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repoRoot

Step "Verificando contenedores activos"
$psOutput = docker compose ps
$psOutput

if ($FixEnv) {
  Step "Ajustando variables FCM en .env (raiz)"
  $envPath = Join-Path $repoRoot ".env"
  if (-not (Test-Path $envPath)) {
    Warn ".env no existe. Creando uno nuevo en raiz."
    New-Item -Path $envPath -ItemType File | Out-Null
  }

  $content = Get-Content $envPath -Raw
  if ($content -notmatch "(?m)^FCM_ENABLED=") {
    Add-Content -Path $envPath -Value "`nFCM_ENABLED=true"
    Ok "Agregado FCM_ENABLED=true"
  } else {
    $content = [regex]::Replace($content, "(?m)^FCM_ENABLED=.*$", "FCM_ENABLED=true")
    Set-Content -Path $envPath -Value $content
    Ok "Actualizado FCM_ENABLED=true"
  }

  $content = Get-Content $envPath -Raw
  if ($content -notmatch "(?m)^FIREBASE_CREDENTIALS_PATH=") {
    Add-Content -Path $envPath -Value "FIREBASE_CREDENTIALS_PATH=/app/firebase-credentials.json"
    Ok "Agregado FIREBASE_CREDENTIALS_PATH=/app/firebase-credentials.json"
  } else {
    $content = [regex]::Replace($content, "(?m)^FIREBASE_CREDENTIALS_PATH=.*$", "FIREBASE_CREDENTIALS_PATH=/app/firebase-credentials.json")
    Set-Content -Path $envPath -Value $content
    Ok "Actualizado FIREBASE_CREDENTIALS_PATH=/app/firebase-credentials.json"
  }
}

if ($RebuildBackend) {
  Step "Rebuild backend para cargar variables nuevas"
  docker compose up -d --build backend
}

Step "Leyendo settings FCM dentro del backend"
$settingsOutput = docker compose exec backend sh -lc "python - <<'PY'
from app.core.config import settings
print('FCM_ENABLED=', settings.FCM_ENABLED)
print('FIREBASE_CREDENTIALS_PATH=', settings.FIREBASE_CREDENTIALS_PATH)
print('firebase_credentials_file=', settings.firebase_credentials_file)
PY"
$settingsOutput

if ($settingsOutput -match "FCM_ENABLED=\s*False") {
  Fail "FCM sigue desactivado en runtime."
} else {
  Ok "FCM activo en runtime."
}

Step "Validando que el archivo de credenciales exista dentro del contenedor"
docker compose exec backend sh -lc "ls -l /app/firebase-credentials.json"

Step "Mostrando llamadas recientes de registro de token"
docker compose logs backend --tail 300 | Select-String -Pattern "/dispositivos/fcm" -CaseSensitive:$false

Step "Conteo de notificaciones in-app generadas (ultimo bloque)"
docker compose logs backend --tail 300 | Select-String -Pattern "INSERT INTO notificaciones" -CaseSensitive:$false

Write-Host ""
Write-Host "Siguiente validacion manual (obligatoria):" -ForegroundColor Magenta
Write-Host "1) Inicia sesion en mobile cliente/tecnico" -ForegroundColor Magenta
Write-Host "2) Verifica en logs un POST /dispositivos/fcm 204" -ForegroundColor Magenta
Write-Host "3) Envía un mensaje técnico->cliente y revisa recepción push real en dispositivo" -ForegroundColor Magenta

