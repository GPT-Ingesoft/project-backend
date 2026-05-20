# ---- Variables ----
$EnvName = "venv-SysLab"
$RequirementsFile = Resolve-Path (
    Join-Path $PSScriptRoot "/requirements.txt"
)
$RootDir = Resolve-Path (
    Join-Path $PSScriptRoot "../../"
)

Set-Location $RootDir
# ---- Script ----

Write-Host  "=================================="
Write-Host  "Configuracion del entorno virtual de python"
Write-Host  "==================================`n"

python -m venv $EnvName
./$EnvName/Scripts/Activate.ps1
pip install -r $RequirementsFile
write-host  "Entorno virtual '$EnvName' creado exitosamente.`n"

Write-Host  "=================================="
Write-Host  "Configuracion de las migraciones de Django"
Write-Host  "==================================`n"

