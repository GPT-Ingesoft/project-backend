@echo off

:: --- Bloque 1: Preparación del Entorno Virtual ---
:: Crea el entorno virtual en la carpeta venv
python -m venv venv

:: Activa el entorno virtual
call venv\Scripts\activate

:: --- Bloque 2: Instalación de Dependencias ---
:: Instala los paquetes necesarios definidos en el manual
pip install django psycopg2-binary

:: --- Bloque 3: Ejecución Inicial ---
:: Levanta el contenedor de PostgreSQL en segundo plano
docker compose up -d

:: Sincroniza los modelos de Django con la BD de Docker
python manage.py makemigrations
python manage.py migrate

:: --- Bloque 4: Pruebas Básicas ---
:: Inicia el servidor de desarrollo
echo Preparacion completada. Iniciando servidor...
python manage.py runserver
