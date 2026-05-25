# Configuración PostgreSQL con Docker

Este documento describe el proceso completo para configurar PostgreSQL utilizando Docker y preparar la base de datos para el backend desarrollado en Django.

---

# Objetivo

Automatizar:

- Instalación y despliegue de PostgreSQL mediante Docker.
- Creación automática de la base de datos del proyecto.
- Configuración de un usuario dedicado para Django.
- Persistencia de datos mediante volúmenes Docker.

---

# Requisitos Previos

Antes de ejecutar el proyecto, se debe instalar:

| Software | Descripción |
|---|---|
| Docker Desktop | Motor de contenedores |
| Git | Control de versiones |
| PowerShell | Ejecución de scripts `.ps1` |

---

# Instalación de Docker Desktop

## 1. Descargar Docker Desktop

Descargar desde:

```text
https://www.docker.com/products/docker-desktop/
```

---

## 2. Instalar Docker Desktop

Durante la instalación:

- Mantener las configuraciones por defecto.
- Habilitar WSL2 si Docker lo solicita.
- Reiniciar el sistema si es necesario.

---

## 3. Verificar instalación

Abrir PowerShell y ejecutar:

```powershell
docker --version
```

Resultado esperado:

```text
Docker version 29.4.3 o superior
```

Verificar Docker Compose:

```powershell
docker compose version
```

---

# Instalación de Python

Aunque PostgreSQL funciona independientemente de Python, el backend utiliza Django, por lo que Python es requerido posteriormente.


## 1. Descargar Python

Descargar desde:

```text
https://www.python.org/downloads/
```

---

## 2. Instalar Python

Durante la instalación:

- Activar la opción:

```text
Add Python to PATH
```

---

## 3. Verificar instalación

Abrir PowerShell:

```powershell
python --version
```

Resultado esperado:

```text
Python 3.14.X
```

---

# Estructura Relacionada

```text
project-backend/
│
├── docker/
│   └── docker-compose.yml
│
└── scripts/
    └── database/
        └── Docker_up.ps1
```

---

# Script de Inicialización PostgreSQL

Archivo:

```text
scripts/database/Docker_up.ps1
```

---

# Objetivo del Script

El script automatiza completamente la configuración inicial de PostgreSQL para el backend.

El proceso incluye:

1. Levantar el contenedor PostgreSQL mediante Docker.
2. Esperar la inicialización correcta del servicio.
3. Crear un usuario dedicado para Django.
4. Asignar permisos sobre la base de datos del proyecto.

---

# Credenciales Configuradas

| Parámetro | Valor |
|---|---|
| Base de datos | syslab_db |
| Usuario administrador | admin |
| Password administrador | 123456 |
| Usuario Django | django_user |
| Password Django | 12345 |

---

# Ejecución del Script

Desde la raíz del proyecto:

```powershell
.\scripts\database\Docker_up.ps1
```

---

# Siguiente Paso

Continuar con: [docs/ejecutar-backend.md](./ejecutar-backend.md)