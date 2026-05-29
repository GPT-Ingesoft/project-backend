#!/bin/bash

# ============================================================
# VARIABLES
# ============================================================
ENV_NAME="venv-SysLab"
DJANGO_USER="django_user"
DJANGO_PASSWORD="12345"
APP_NAME="information_app"

ROOT_DIR="$(dirname "$(realpath "$0")")"

BACKEND_PATH="$ROOT_DIR"
COMPOSE_FILE="$ROOT_DIR/docker-compose.yml"
REQUIREMENTS_FILE="$ROOT_DIR/requirements.txt"
APP_PATH="$ROOT_DIR/$APP_NAME"
MANAGE_PY="$ROOT_DIR/manage.py"

# ============================================================
# DOCKER - PostgreSQL container
# ============================================================

if docker ps -a | grep -i "postgres_db" > /dev/null 2>&1; then

    if docker ps | grep -i "postgres_db" > /dev/null 2>&1; then
        echo "[INFO] Docker container postgres_db is already running."
        echo

    else
        echo "[INFO] Docker container postgres_db exists but is stopped. Restarting..."
        if ! docker start postgres_db; then
            echo "[ERROR] Docker container postgres_db could not be restarted."
            read -rp "Press any key to continue..." && exit 1
        fi
        echo "[OK] Docker container postgres_db restarted successfully."
        echo
    fi

else
    echo "[INFO] Docker container postgres_db does not exist. Creating with Docker Compose..."

    if ! docker compose -f "$COMPOSE_FILE" up -d; then
        echo "[ERROR] Docker Compose could not be started."
        read -rp "Press any key to continue..." && exit 1
    fi
    echo "[OK] PostgreSQL started successfully."
    echo

    echo "Waiting 5 seconds for PostgreSQL to initialize..."
    sleep 5

    echo "[INFO] Configuring PostgreSQL user and database for Django..."
    echo

    docker exec postgres_db psql -U admin -d postgres -c "CREATE USER $DJANGO_USER WITH PASSWORD '$DJANGO_PASSWORD';"
    docker exec postgres_db psql -U admin -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE syslab_db TO $DJANGO_USER;"
    docker exec postgres_db psql -U admin -d syslab_db -c "GRANT ALL ON SCHEMA public TO $DJANGO_USER;"
    echo "[OK] User $DJANGO_USER configured successfully."
    echo
fi

# ============================================================
# PYTHON - Virtual environment and dependencies
# ============================================================

cd "$ROOT_DIR" || exit 1

if [ ! -d "$ENV_NAME" ]; then

    if ! python3 -m venv "$ENV_NAME"; then
        echo "[ERROR] Could not create the virtual environment."
        read -rp "Press any key to continue..." && exit 1
    fi
    source "$ROOT_DIR/$ENV_NAME/bin/activate"
    pip install -r "$REQUIREMENTS_FILE"
    echo "[OK] Virtual environment '$ENV_NAME' created successfully."
    echo

else
    source "$ROOT_DIR/$ENV_NAME/bin/activate"
    pip install -r "$REQUIREMENTS_FILE"
    echo "[INFO] Virtual environment '$ENV_NAME' already exists."
    echo
fi

# ============================================================
# DJANGO - Project setup and folder structure
# ============================================================

cd "$BACKEND_PATH" || exit 1

if [ ! -f "$MANAGE_PY" ]; then

    django-admin startproject config .
    python manage.py startapp "$APP_NAME"
    echo "[OK] Django project created successfully."
    echo

    if [ -d "$APP_PATH" ]; then

        rm -rf "$APP_PATH"
        mkdir -p "$APP_PATH"

        mkdir -p "$APP_PATH/controllers"
        mkdir -p "$APP_PATH/migrations"
        mkdir -p "$APP_PATH/repositories"
        mkdir -p "$APP_PATH/services"
        touch "$APP_PATH/models.py"
        touch "$APP_PATH/urls.py"

        echo "[OK] Folder structure for app '$APP_NAME' created successfully."
        echo
    fi

else
    echo "[INFO] Django project already exists. Skipping project creation."
    echo
fi

# ============================================================
# DJANGO - Migrations
# ============================================================

if [ ! -f "$MANAGE_PY" ]; then
    echo "[ERROR] Django project not found. Please run this setup script in the correct directory."
    read -rp "Press any key to continue..." && exit 1
fi

python manage.py makemigrations "$APP_NAME"
echo
echo "[OK] Migrations generated successfully."
echo

python manage.py migrate
echo
echo "[OK] Tables were created/updated successfully in PostgreSQL."
echo

echo "Setup completed successfully"
read -rp "Press any key to continue..."