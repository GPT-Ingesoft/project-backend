# Configuración de la Estructura Django

Este documento describe el proceso de configuración automática del backend Django.

---

# Objetivo

Automatizar completamente la inicialización del backend del proyecto utilizando Django y PostgreSQL.

El script permite:

- Crear el entorno virtual de Python.
- Instalar dependencias automáticamente.
- Generar el proyecto Django.
- Configurar PostgreSQL como motor de base de datos.
- Crear la aplicación principal del backend.
- Inicializar una arquitectura monolítica organizada por capas.

---

# Archivos Relacionados

```text
project-backend/
│
├── scripts/
│   └── backend/
│       ├── django-database.ps1
│       ├── requirements.txt
│       └── Django_settings.py
│
└── src/
```

---

# Dependencias del Proyecto

Archivo:

```text
scripts/backend/requirements.txt
```

## Tecnologías Instaladas

| Dependencia | Objetivo |
|---|---|
| Django | Framework principal del backend |
| psycopg | Conexión PostgreSQL |
| Django REST Framework | Construcción de APIs REST |
| django-cors-headers | Configuración CORS |

---

# Script de Configuración

Archivo:

```text
scripts/backend/django-database.ps1
```

---

# Funcionalidades del Script

El script automatiza:

1. Creación del entorno virtual.
2. Activación del entorno virtual.
3. Instalación de dependencias.
4. Creación del proyecto Django.
5. Creación de la aplicación principal.
6. Configuración personalizada de Django.
7. Generación de la arquitectura base del backend.

---

# Ejecución del Script

Desde la raíz del proyecto:

```powershell
.\scripts\backend\django-database.ps1
```

---

# Flujo de Inicialización

El proceso de inicialización del backend fue automatizado mediante el script:

```text
scripts/backend/django-database.ps1
```

Su objetivo es preparar completamente el entorno de desarrollo del proyecto sin necesidad de realizar configuraciones manuales de Django o Python.

---

## Creación del Entorno Virtual

La primera tarea del script consiste en verificar si existe un entorno virtual previamente configurado, en caso de no existir, se crea automáticamente un nuevo entorno virtual llamado:

```text
venv-SysLab
```

Una vez creado, el script activa automáticamente el entorno virtual para continuar con la instalación de dependencias y configuración del backend.

---

## Instalación de Dependencias

Después de activar el entorno virtual, el script instala automáticamente todas las dependencias definidas en:

```text
requirements.txt
```

Estas dependencias incluyen:

- Django como framework principal.
- psycopg para la conexión con PostgreSQL.
- Django REST Framework para la construcción de APIs REST.
- django-cors-headers para la configuración de políticas CORS.

---

## Inicialización del Proyecto Django

Una vez configurado el entorno Python, el script inicializa automáticamente el backend Django dentro de:

```text
src/
```

Durante este proceso:

- Se crea el proyecto principal llamado `config`.
- Se genera la aplicación principal `information_app`.
- Se prepara la estructura base del backend.

Toda esta configuración se realiza automáticamente utilizando los comandos internos de Django.

---

## Configuración Personalizada de Django

Después de crear el proyecto, el script reemplaza automáticamente la configuración por defecto de Django utilizando el archivo personalizado:

```text
Django_settings.py
```

Este archivo es copiado automáticamente hacia:

```text
config/settings.py
```

La intención de este proceso es centralizar una configuración previamente adaptada para el proyecto SysLab, evitando configuraciones manuales posteriores.

---

### Configuración PostgreSQL

La configuración personalizada conecta automáticamente Django con PostgreSQL utilizando las credenciales configuradas previamente en Docker.

La conexión queda definida mediante:

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

---

### Configuración REST API

El backend incorpora soporte para APIs REST mediante Django REST Framework.

Para ello, la configuración habilita automáticamente las siguientes aplicaciones:

```python
INSTALLED_APPS = [
    'rest_framework',
    'corsheaders',
    'information_app'
]
```

Esto permite desarrollar endpoints RESTful y manejar serialización, validaciones y respuestas HTTP de forma estructurada.

---

### Configuración CORS

El backend también habilita soporte CORS para permitir la comunicación entre el frontend y Django durante el desarrollo local.

La configuración permite solicitudes desde:

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
]
```

# Arquitectura Base del Backend

El backend del proyecto fue diseñado utilizando una arquitectura monolítica organizada por capas, con el objetivo de separar responsabilidades y mantener una estructura modular, escalable y fácil de mantener.

La aplicación principal del sistema se encuentra en:

```text
information_app/
│
├── controllers/
├── repositories/
├── services/
├── migrations/
├── models.py
└── urls.py
```

Cada capa cumple una responsabilidad específica dentro del flujo del backend:

| Componente | Responsabilidad |
|---|---|
| controllers | Manejo de endpoints HTTP y respuestas REST |
| services | Implementación de lógica de negocio |
| repositories | Acceso y manipulación de datos en PostgreSQL |
| models.py | Definición de entidades y tablas ORM |
| migrations | Control de versiones de la base de datos |
| urls.py | Registro y organización de rutas |

Esta organización permite desacoplar la lógica de negocio del acceso a datos y de la capa HTTP, facilitando el mantenimiento y la evolución futura del sistema.

La arquitectura general del backend puede observarse con mayor detalle en el siguiente diagrama:

![Arquitectura-FrontEnd](./images/Esquema-Arquitectura-Backend.png)

---

# Siguiente Paso

Continuar con: [docs/backend-database.md](./docs/backend-database.md)