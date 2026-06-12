@echo off
setlocal EnableDelayedExpansion

:: ============================================================
:: VARIABLES
:: ============================================================
set ENV_NAME=venv-SysLab
set DJANGO_USER=django_user
set DJANGO_PASSWORD=12345
set APP_NAME=information_app

set ROOT_DIR=%~dp0
if "%ROOT_DIR:~-1%"=="\" set ROOT_DIR=%ROOT_DIR:~0,-1%

set BACKEND_PATH=%ROOT_DIR%
set COMPOSE_FILE=%ROOT_DIR%\docker-compose.yml
set REQUIREMENTS_FILE=%ROOT_DIR%\requirements.txt
set APP_PATH=%ROOT_DIR%\%APP_NAME%
set MANAGE_PY=%ROOT_DIR%\manage.py

:: ============================================================
:: DOCKER - PostgreSQL container
:: ============================================================

:: Verify if the docker container "postgres_db" exists
docker ps -a | findstr /i "postgres_db" >nul 2>&1
if not errorlevel 1 (
    docker ps | findstr /i "postgres_db" >nul 2>&1
    if not errorlevel 1 (
        echo [INFO] Docker container postgres_db is already running.
        echo.
        goto :SKIP_DOCKER
    ) else (
        echo [INFO] Docker container postgres_db exists but is stopped. Restarting...
        docker start postgres_db
        if errorlevel 1 (
            echo [ERROR] Docker container postgres_db could not be restarted.
            pause
            exit /b 1
        )
        echo [OK] Docker container postgres_db restarted successfully.
        echo.
        goto :SKIP_DOCKER
    )
)

:: If docker container does not exist, create it using docker compose
echo [INFO] Docker container postgres_db does not exist. Creating with Docker Compose...

docker compose -f "%COMPOSE_FILE%" up -d
if errorlevel 1 (
    echo [ERROR] Docker Compose could not be started.
    pause
    exit /b 1
)
echo [OK] PostgreSQL started successfully.
echo.

timeout /t 5 /nobreak >nul

echo [INFO] Configuring PostgreSQL user and database for Django...
echo.

docker exec postgres_db psql -U admin -d postgres -c "CREATE USER %DJANGO_USER% WITH PASSWORD '%DJANGO_PASSWORD%';"
docker exec postgres_db psql -U admin -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE syslab_db TO %DJANGO_USER%;"
docker exec postgres_db psql -U admin -d syslab_db -c "GRANT ALL ON SCHEMA public TO %DJANGO_USER%;"
echo [OK] User %DJANGO_USER% configured successfully.
echo.

:SKIP_DOCKER

:: ============================================================
:: PYTHON - Virtual environment and dependencies
:: ============================================================

cd /d "%ROOT_DIR%"


py -m pip install -r "%REQUIREMENTS_FILE%"


:: ============================================================
:: DJANGO - Project setup and folder structure
:: ============================================================

cd /d "%BACKEND_PATH%"

if not exist "%MANAGE_PY%" (

    django-admin startproject config .
    py manage.py startapp %APP_NAME%
    echo [OK] Django project created successfully.
    echo.

    if exist "%APP_PATH%" (

        :: Limpiar carpeta generada por Django
        rd /s /q "%APP_PATH%"
        mkdir "%APP_PATH%"

        mkdir "%APP_PATH%\controllers"
        mkdir "%APP_PATH%\migrations"
        mkdir "%APP_PATH%\repositories"
        mkdir "%APP_PATH%\services"
        type nul > "%APP_PATH%\models.py"
        type nul > "%APP_PATH%\urls.py"

        echo [OK] Folder structure for app '%APP_NAME%' created successfully.
        echo.
    )

) else (
    echo [INFO] Django project already exists. Skipping project creation.
    echo.
)


:: ============================================================
:: DJANGO - Migrations
:: ============================================================

if not exist "%MANAGE_PY%" (
    echo [ERROR] Django project not found. Please run this setup script in the correct directory.
    pause
    exit /b 1
)

py -m manage makemigrations %APP_NAME%
echo.
echo [OK] Migrations generated successfully.
echo.


py -m manage migrate
echo.
echo [OK] Tables were created/updated successfully in PostgreSQL.
echo.

echo  Setup completed successfully
pause
endlocal