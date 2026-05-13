#!/bin/bash

# --- Bloque 1: Preparación del Entorno Virtual ---
# Crea el entorno virtual para aislar las dependencias
python3 -m venv venv

# Activa el entorno virtual
source venv/bin/activate

# --- Bloque 2: Instalación de Dependencias ---
# Instala Django y el driver de PostgreSQL mencionado en el tutorial
pip install django psycopg2-binary

# --- Bloque 3: Ejecución Inicial ---
# Levanta la base de datos (requiere Docker instalado)
docker compose up -d

# Realiza las migraciones para preparar la base de datos
python manage.py makemigrations
python manage.py migrate

# --- Bloque 4: Pruebas Básicas ---
# Ejecuta el servidor para verificar que todo inicia correctamente
echo "Preparación completada. Iniciando servidor..."
python manage.py runserver
