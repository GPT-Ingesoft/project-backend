@echo off

REM ==================================
REM CONFIGURACION INICIAL DEL PROYECTO
REM ==================================

echo ==================================
echo INICIANDO CONFIGURACION DEL PROYECTO
echo ==================================

REM ----------------------------------
REM LEVANTAR CONTENEDORES DOCKER
REM ----------------------------------

echo.
echo Levantando PostgreSQL con Docker...
docker compose up -d

REM ----------------------------------
REM INGRESAR A LA CARPETA BACKEND
REM ----------------------------------

echo.
echo Entrando al backend...
cd backend

REM ----------------------------------
REM CREAR ENTORNO VIRTUAL
REM ----------------------------------

echo.
echo Creando entorno virtual...
python -m venv venv

REM ----------------------------------
REM ACTIVAR ENTORNO VIRTUAL
REM ----------------------------------

echo.
echo Activando entorno virtual...
call venv\Scripts\activate

REM ----------------------------------
REM INSTALAR DEPENDENCIAS
REM ----------------------------------

echo.
echo Instalando dependencias...
pip install -r requirements.txt

REM ----------------------------------
REM REALIZAR MIGRACIONES
REM ----------------------------------

echo.
echo Ejecutando migraciones...
python manage.py makemigrations
python manage.py migrate

REM ----------------------------------
REM EJECUTAR PRUEBAS BASICAS
REM ----------------------------------

echo.
echo Ejecutando pruebas...
python manage.py test

REM ----------------------------------
REM INICIAR SERVIDOR DJANGO
REM ----------------------------------

echo.
echo Iniciando servidor Django...
python manage.py runserver
