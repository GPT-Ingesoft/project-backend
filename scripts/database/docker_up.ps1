# ---- Variables ----
$ComposeFile = Resolve-Path (
    Join-Path $PSScriptRoot "../../docker/docker-compose.yml"
)

$DjangoUser = "django_user"
$DjangoPassword = "12345"

# ---- Script ----

Write-Host  "=================================="
Write-Host  "Configuracion de Contenedores Docker para PostgreSQL"
Write-Host  "==================================`n"

docker compose -f $ComposeFile up -d
write-host  "PostgreSQL levantado exitosamente.`n"

Write-Host  "=================================="
Write-Host  "Configuracion de un nuevo usuario y base de datos para Django"
Write-Host  "==================================`n"

# Dormir 5 segundos mientras inicializa el contenedor de PostgreSQL para evitar errores de conexión
Start-Sleep -Seconds 5

docker exec postgres_db psql -U admin -d postgres -c "CREATE USER $DjangoUser WITH PASSWORD '$DjangoPassword';"
docker exec postgres_db psql -U admin -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE syslab_db TO $DjangoUser;"
docker exec postgres_db psql -U admin -d syslab_db -c "GRANT ALL ON SCHEMA public TO $DjangoUser;"
write-host  "Usuario $DjangoUser para Django configurados exitosamente.`n"
