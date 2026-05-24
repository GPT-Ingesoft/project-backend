# ---- Variables ----
$EnvName = "venv-SysLab"

$RootDir = Resolve-Path (
    Join-Path $PSScriptRoot "../../"
)

$RequirementsFile = Resolve-Path (
    Join-Path $PSScriptRoot "requirements.txt"
)

$DjangoTemplateFile = Resolve-Path (
    Join-Path $PSScriptRoot "Django_settings.py"
)

$BackendPath = Resolve-Path (
    Join-Path $RootDir "./src/"
)

$DjangoSettings = Join-Path $BackendPath "config/settings.py"

$AppName = "information_app"

$AppPath = Join-Path $BackendPath $AppName

# ---- Script ----
Set-Location $RootDir

if (!(Test-Path $EnvName)) {
    Write-Host  "=================================="
    Write-Host  "Configuracion del entorno virtual de python"
    Write-Host  "==================================`n"


    python -m venv $EnvName
    & ".\$EnvName\Scripts\Activate.ps1"    
    pip install -r $RequirementsFile
    write-host  "Entorno virtual '$EnvName' creado exitosamente.`n"

} else {
    & ".\$EnvName\Scripts\Activate.ps1"    

    Write-Host  "=================================="
    Write-Host  "Entorno virtual '$EnvName' ya existe"
    Write-Host  "==================================`n"
}

Set-Location $BackendPath

if (!(Test-Path "manage.py")) {
    Write-Host  "=================================="
    Write-Host  "Configuracion del proyecto Django"
    Write-Host  "==================================`n"

    django-admin startproject config .
    python manage.py startapp $AppName
    Copy-Item -Path $DjangoTemplateFile -Destination $DjangoSettings -Force
    write-host  "Proyecto Django creado exitosamente.`n"

    if (Test-Path $AppPath) {

        Write-Host  "=================================="
        Write-Host  "Configuracion de la plantilla de carpetas"
        Write-Host  "==================================`n"

        Remove-Item "$AppPath\*" -Recurse -Force

        New-Item -Path "$AppPath\controllers" -ItemType Directory -Force
        New-Item -Path "$AppPath\models.py" -ItemType File -Force
        New-Item -Path "$AppPath\migrations" -ItemType Directory -Force
        New-Item -Path "$AppPath\repositories" -ItemType Directory -Force
        New-Item -Path "$AppPath\services" -ItemType Directory -Force

        New-Item -Path "$AppPath\urls.py" -ItemType File -Force
    }

} else {
    Write-Host  "=================================="
    Write-Host  "Proyecto Django ya existe"
    Write-Host  "==================================`n"
}


