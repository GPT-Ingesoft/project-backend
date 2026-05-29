# Configuración e Inicialización del Backend

Este documento describe el proceso completo para configurar e inicializar el backend del proyecto SysLab, incluyendo PostgreSQL con Docker, el entorno Python, el proyecto Django y la exportación del modelo relacional a la base de datos.

---

# Objetivo

Automatizar completamente la inicialización del backend mediante un único script de configuración que cubre:

- Despliegue de PostgreSQL mediante Docker.
- Creación y configuración del usuario de base de datos para Django.
- Creación del entorno virtual de Python e instalación de dependencias.
- Generación del proyecto Django y la aplicación principal.
- Inicialización de la arquitectura monolítica por capas.
- Exportación del modelo relacional a PostgreSQL mediante migraciones.

---

# Requisitos Previos

| Software | Descripción |
|---|---|
| Docker Desktop | Motor de contenedores |
| Python 3.14+ | Entorno de ejecución del backend |
| Git | Control de versiones |

## Verificar instalaciones

```cmd
docker --version
docker compose version
python --version
```

---

# Estructura del Proyecto

```text
project-backend/
│
├── docker-compose.yml
├── requirements.txt
├── setup.bat               (Windows)
├── setup.sh                (Linux)
│
├── config/                 
│   └── settings.py
│
└── information_app/
    ├── controllers/
    ├── repositories/
    ├── services/
    ├── migrations/
    ├── models.py
    └── urls.py
```

---

# Credenciales Configuradas

| Parámetro | Valor |
|---|---|
| Base de datos | syslab_db |
| Usuario administrador | admin |
| Password administrador | 123456 |
| Usuario Django | django_user |
| Password Django | 12345 |
| Puerto PostgreSQL | 5434 |

---

# Script de Inicialización

Los scripts `setup.bat` (Windows) y `setup.sh` (Linux) unifican en un único flujo de ejecución las siguientes etapas: configuración de Docker, entorno virtual, proyecto Django y migraciones.

Ambos scripts son idempotentes: pueden ejecutarse múltiples veces sin generar duplicados, ya que verifican el estado actual antes de cada operación.

## Ejecución en Windows

```cmd
setup.bat
```

## Ejecución en Linux

```bash
chmod +x setup.sh
./setup.sh
```

---

# Flujo de Inicialización

## Etapa 1 — Docker y PostgreSQL

El script verifica el estado del contenedor `postgres_db` antes de realizar cualquier operación:

| Estado del contenedor | Acción |
|---|---|
| Corriendo | Se omite todo el bloque Docker |
| Detenido | Se reinicia con `docker start` |
| No existe | Se crea con `docker compose up` y se configura la base de datos |

Cuando el contenedor se crea por primera vez, el script espera 5 segundos para garantizar la inicialización correcta de PostgreSQL antes de ejecutar los comandos de configuración.

La configuración inicial de la base de datos incluye:

```sql
CREATE USER django_user WITH PASSWORD '12345';
GRANT ALL PRIVILEGES ON DATABASE syslab_db TO django_user;
GRANT ALL ON SCHEMA public TO django_user;
```

---

## Etapa 2 — Entorno Virtual de Python

El script verifica si el entorno virtual `venv-SysLab` existe:

| Estado | Acción |
|---|---|
| No existe | Se crea con `python -m venv` |
| Ya existe | Se activa directamente |

En ambos casos se ejecuta `pip install -r requirements.txt` para mantener las dependencias actualizadas ante cualquier cambio en el archivo.

### Dependencias instaladas

| Dependencia | Objetivo |
|---|---|
| Django | Framework principal del backend |
| psycopg | Conexión con PostgreSQL |
| Django REST Framework | Construcción de APIs REST |
| django-cors-headers | Configuración de políticas CORS |

---

## Etapa 3 — Proyecto Django

Si `manage.py` no existe en la raíz, el script inicializa el proyecto Django:

```cmd
django-admin startproject config .
python manage.py startapp information_app
```

Luego reemplaza la carpeta generada por Django con la arquitectura por capas del proyecto:

```text
information_app/
├── controllers/
├── repositories/
├── services/
├── migrations/
├── models.py
└── urls.py
```

Si `manage.py` ya existe, esta etapa se omite completamente.

---

## Etapa 4 — Migraciones

Esta etapa se ejecuta siempre, independientemente de las etapas anteriores. Permite aplicar cambios al modelo relacional sin necesidad de reinicializar el proyecto completo.

```cmd
python manage.py makemigrations information_app
python manage.py migrate
```

---

# Configuración de Django

## Conexión con PostgreSQL

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'syslab_db',
        'USER': 'django_user',
        'PASSWORD': '12345',
        'HOST': 'localhost',
        'PORT': '5434',
    }
}
```

## Aplicaciones habilitadas

```python
INSTALLED_APPS = [
    'rest_framework',
    'corsheaders',
    'information_app',
]
```

## CORS

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
]
```

---

# Arquitectura del Backend

El backend utiliza una arquitectura monolítica organizada por capas para separar responsabilidades y facilitar el mantenimiento.

| Componente | Responsabilidad |
|---|---|
| controllers | Manejo de endpoints HTTP y respuestas REST |
| services | Implementación de la lógica de negocio |
| repositories | Acceso y manipulación de datos en PostgreSQL |
| models.py | Definición de entidades y tablas ORM |
| migrations | Control de versiones de la base de datos |
| urls.py | Registro y organización de rutas |

![Arquitectura Backend](./images/Esquema-Arquitectura-Backend.png)

---

# Modelo Relacional

La estructura de la base de datos está definida en:

```text
information_app/models.py
```

Las entidades, relaciones y configuraciones ORM definidas en este archivo son transformadas automáticamente en tablas PostgreSQL durante la Etapa 4 del script.

![Diagrama Entidad-Relación](./images/Database_ER.png)

---

# Siguiente Paso

Continuar con: [docs/backend_execute.md](./backend_execute.md)