
@echo off
setlocal EnableDelayedExpansion
 
:: ---- Variables ----
set ENV_NAME=venv-SysLab
 
set ROOT_DIR=%~dp0
if "%ROOT_DIR:~-1%"=="\" set ROOT_DIR=%ROOT_DIR:~0,-1%
 
set BACKEND_PATH=%ROOT_DIR%
 
:: ---- Script ----
cd /d "%BACKEND_PATH%"
 
echo ==================================
echo  Activando entorno virtual de python
echo ==================================
echo.
 
call "%ROOT_DIR%\%ENV_NAME%\Scripts\activate.bat"
 
echo ==================================
echo  Iniciando Backend de Django
echo ==================================
echo.
 
python manage.py runserver
 