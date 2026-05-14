#!/bin/bash

# ==================================
# CONFIGURACION INICIAL DEL PROYECTO
# ==================================

echo "=================================="
echo "INICIANDO CONFIGURACION DEL PROYECTO"
echo "=================================="

# ----------------------------------
# LEVANTAR CONTENEDORES DOCKER
# ----------------------------------

echo ""
echo "Levantando PostgreSQL con Docker..."
docker compose up -d

# ----------------------------------
# INGRESAR A LA CARPETA BACKEND
# ----------------------------------

echo ""
echo "Entrando al backend..."
cd backend

# ----------------------------------
# CREAR ENTORNO VIRTUAL
# ----------------------------------

echo ""
echo "Creando entorno virtual..."
python -m venv venv

# ----------------------------------
# ACTIVAR ENTORNO VIRTUAL
# ----------------------------------

echo ""
echo "Activando entorno virtual..."
source venv/bin/activate

# ----------------------------------
# INSTALAR DEPENDENCIAS
# ----------------------------------

echo ""
echo "Instalando dependencias..."
pip install -r requirements.txt

# ----------------------------------
# REALIZAR MIGRACIONES
# ----------------------------------

echo ""
echo "Ejecutando migraciones..."
python manage.py makemigrations
python manage.py migrate

# ----------------------------------
# EJECUTAR PRUEBAS BASICAS
# ----------------------------------

echo ""
echo "Ejecutando pruebas..."
python manage.py test

# ----------------------------------
# INICIAR SERVIDOR DJANGO
# ----------------------------------

echo ""
echo "Iniciando servidor Django..."
python manage.py runserver
