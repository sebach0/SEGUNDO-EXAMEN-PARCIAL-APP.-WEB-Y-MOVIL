# Prueba manual de endpoints Ciclo 4 — ejecutar desde raíz del repo:
#   powershell -File backend/scripts/test_ciclo4_endpoints.ps1
$ErrorActionPreference = "Stop"
$base = "http://localhost:8000/api"
$passed = 0
$failed = 0

function Step($name, [scriptblock]$action) {
    try {
        $result = & $action
        Write-Host "[OK] $name" -ForegroundColor Green
        if ($result) { Write-Host "     $result" }
        $script:passed++
    }
    catch {
        $msg = $_.Exception.Message
        if ($_.ErrorDetails.Message) { $msg = "$msg | $($_.ErrorDetails.Message)" }
        Write-Host "[FAIL] $name" -ForegroundColor Red
        Write-Host "     $msg" -ForegroundColor Red
        $script:failed++
    }
}

Write-Host "`n=== Ciclo 4 - verificacion de endpoints ===`n"

Step "GET /health" {
    $h = Invoke-RestMethod "http://localhost:8000/health"
    "status=$($h.status)"
}

Step "POST /auth/login (cliente)" {
    $script:loginC = Invoke-RestMethod -Method POST -Uri "$base/auth/login" `
        -ContentType "application/json" `
        -Body '{"email":"carlos.vega@sc-demo.test","password":"scdemo1"}'
    $script:hC = @{ Authorization = "Bearer $($script:loginC.access_token)" }
    "token OK"
}

Step "GET /app/cliente/mis-vehiculos" {
    $v = Invoke-RestMethod -Method GET -Uri "$base/app/cliente/mis-vehiculos" -Headers $script:hC
    if (-not $v -or $v.Count -eq 0) { throw "Sin vehiculos - ejecuta: docker compose exec backend python -m app.seeds" }
    $script:vid = $v[0].id
    "vehiculo_id=$($script:vid)"
}

Step "POST /incidents (crear)" {
    $body = @{
        vehiculo_id = $script:vid
        descripcion = "Prueba automatizada Ciclo 4"
        prioridad = "ALTA"
        tipo_incidente_id = 1
    } | ConvertTo-Json
    $script:inc = Invoke-RestMethod -Method POST -Uri "$base/incidents" `
        -Headers $script:hC -ContentType "application/json" -Body $body
    $script:iid = $script:inc.id
    "incident_id=$($script:iid) estado=$($script:inc.estado)"
}

Step "GET /incidents (listar)" {
    $list = Invoke-RestMethod -Method GET -Uri "$base/incidents" -Headers $script:hC
    "total=$($list.Count)"
}

Step "GET /incidents/{id} (detalle CU36)" {
    $det = Invoke-RestMethod -Method GET -Uri "$base/incidents/$($script:iid)" -Headers $script:hC
    "historial=$($det.historial_estados.Count) eventos=$($det.eventos_recientes.Count)"
}

Step "POST /auth/login (taller)" {
    $loginT = Invoke-RestMethod -Method POST -Uri "$base/auth/login" `
        -ContentType "application/json" `
        -Body '{"email":"luis.rivera@sc-demo.test","password":"scdemo1"}'
    $script:hT = @{ Authorization = "Bearer $($loginT.access_token)" }
    "token taller OK"
}

Step "PATCH /incidents/{id}/status (CU37)" {
    $body = @{ nuevo_estado = "EN_CAMINO"; comentario = "Prueba CU37" } | ConvertTo-Json
    $st = Invoke-RestMethod -Method PATCH -Uri "$base/incidents/$($script:iid)/status" `
        -Headers $script:hT -ContentType "application/json" -Body $body
    "estado=$($st.estado)"
}

Step "POST /incidents/{id}/tracking (CU37 GPS)" {
    $body = @{ latitud = -17.7612; longitud = -63.1944; velocidad_kmh = 40 } | ConvertTo-Json
    $tr = Invoke-RestMethod -Method POST -Uri "$base/incidents/$($script:iid)/tracking" `
        -Headers $script:hT -ContentType "application/json" -Body $body
    "tracking_id=$($tr.id)"
}

Step "GET /incidents/{id}/tracking (CU36)" {
    $trk = Invoke-RestMethod -Method GET -Uri "$base/incidents/$($script:iid)/tracking" -Headers $script:hC
    "puntos=$($trk.Count)"
}

Step "POST /sync/incidents (CU39 nuevo)" {
    $script:uuid = [guid]::NewGuid().ToString()
    $body = @{
        client_uuid = $script:uuid
        vehiculo_id = $script:vid
        descripcion = "Emergencia offline"
        prioridad = "MEDIA"
    } | ConvertTo-Json
    $script:sync1 = Invoke-RestMethod -Method POST -Uri "$base/sync/incidents" `
        -Headers $script:hC -ContentType "application/json" -Body $body
    if (-not $script:sync1.creado_nuevo) { throw "Se esperaba creado_nuevo=true" }
    "incidente_id=$($script:sync1.incidente_id)"
}

Step "POST /sync/incidents (CU39 anti-duplicado)" {
    $body = @{
        client_uuid = $script:uuid
        vehiculo_id = $script:vid
        descripcion = "Emergencia offline"
        prioridad = "MEDIA"
    } | ConvertTo-Json
    $sync2 = Invoke-RestMethod -Method POST -Uri "$base/sync/incidents" `
        -Headers $script:hC -ContentType "application/json" -Body $body
    if ($sync2.creado_nuevo) { throw "Se esperaba creado_nuevo=false (anti-duplicado)" }
    "creado_nuevo=false OK"
}

Step "GET /sync/status (CU40)" {
    $st = Invoke-RestMethod -Method GET -Uri "$base/sync/status" -Headers $script:hC
    "registros=$($st.Count)"
}

Step "POST /sync/web/events (CU41/CU42)" {
    $evUuid = [guid]::NewGuid().ToString()
    $body = @{
        eventos = @(
            @{
                client_uuid = $evUuid
                incidente_id = $script:iid
                tipo_evento = "ESTADO_CAMBIADO"
                payload = @{ nuevo_estado = "EN_ATENCION" }
            }
        )
    } | ConvertTo-Json -Depth 5
    $web = Invoke-RestMethod -Method POST -Uri "$base/sync/web/events" `
        -Headers $script:hC -ContentType "application/json" -Body $body
    if ($web.con_error -gt 0) { throw "con_error=$($web.con_error)" }
    "sincronizados=$($web.sincronizados)/$($web.total)"
}

Write-Host "`n=== RESULTADO: $passed OK, $failed FAIL ===`n"
if ($failed -gt 0) { exit 1 }
