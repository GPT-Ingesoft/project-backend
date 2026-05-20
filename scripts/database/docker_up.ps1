# ---- Variables ----
$ComposeFile = Resolve-Path (
    Join-Path $PSScriptRoot "../../docker/docker-compose.yml"
)

# ---- Script ----

Write-Host  "=================================="
Write-Host  "Configuracion de Contenedores Docker para PostgreSQL"
Write-Host  "==================================`n"

docker compose -f $ComposeFile up -d
write-host  "PostgreSQL levantado exitosamente.`n"