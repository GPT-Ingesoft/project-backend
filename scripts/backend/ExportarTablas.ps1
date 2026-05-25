# ---- Variables ----
$EnvName = "venv-SysLab"

$RootDir = Resolve-Path (
    Join-Path $PSScriptRoot "../../"
)

$BackendPath = Resolve-Path (
    Join-Path $RootDir "./src/"
)

$ManagePy = Join-Path $BackendPath "manage.py"

$AppName = "information_app"

# ---- Script ----

Write-Host  "=================================="
Write-Host  "Inicializacion de migraciones Django"
Write-Host  "==================================`n"

Set-Location $RootDir

if (!(Test-Path $EnvName)) {
    Write-Host  "[ERROR] El entorno virtual '$EnvName' no existe.`n"
    exit 1
}

& ".\$EnvName\Scripts\Activate.ps1"
Write-Host  "[OK] Entorno virtual activado.`n"

if (!(Test-Path $ManagePy)) {
    Write-Host  "[ERROR] No se encontro manage.py en:"
    Write-Host  "$BackendPath`n"
    exit 1
}

Write-Host  "=================================="
Write-Host  "Generando migraciones"
Write-Host  "==================================`n"

Set-Location $BackendPath

python manage.py makemigrations $AppName
Write-Host  "`n[OK] Migraciones generadas correctamente.`n"

Write-Host  "=================================="
Write-Host  "Aplicando migraciones en PostgreSQL"
Write-Host  "==================================`n"

python manage.py migrate $AppName
Write-Host  "`n[OK] Las tablas fueron creadas/actualizadas correctamente en PostgreSQL.`n"