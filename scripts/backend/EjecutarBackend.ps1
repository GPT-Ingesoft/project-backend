# ---- Variables ----
$EnvName = "venv-SysLab"

$RootDir = Resolve-Path (
    Join-Path $PSScriptRoot "../../"
)

$BackendPath = Resolve-Path (
    Join-Path $RootDir "./src/"
)

# ---- Script ----
Set-Location $RootDir

Write-Host  "=================================="
Write-Host  "Activando entorno virtual de python"
Write-Host  "==================================`n"

& ".\$EnvName\Scripts\Activate.ps1"    

Set-Location $BackendPath
Write-Host  "=================================="
Write-Host  "Iniciando Backend de Django"
Write-Host  "==================================`n"

python manage.py runserver