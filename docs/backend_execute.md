# Ejecución del Backend

Este documento describe el proceso de inicio del servidor de desarrollo Django del proyecto SysLab.

---

# Objetivo

Automatizar el arranque del backend Django utilizando el entorno virtual previamente configurado por `setup.bat`.

El script permite:

- Activar automáticamente el entorno virtual.
- Iniciar el servidor de desarrollo Django desde la raíz del proyecto.

---

# Requisitos Previos

Antes de ejecutar este script, el entorno debe estar inicializado correctamente:

| Requisito | Verificación |
|---|---|
| Entorno virtual `venv-SysLab` creado | Ejecutar `setup.bat` si no existe |
| Proyecto Django inicializado | `manage.py` debe existir en la raíz |
| Contenedor PostgreSQL corriendo | `docker ps` debe mostrar `postgres_db` |

---

# Estructura Relacionada

```text
project-backend/
│
├── run_backend.bat
├── manage.py
└── venv-SysLab/
    └── Scripts/
        └── activate.bat
```

---

# Ejecución

```cmd
run_backend.bat
```

---

# Flujo de Ejecución

## Etapa 1 — Activación del Entorno Virtual

El script activa el entorno virtual `venv-SysLab` desde la raíz del proyecto:

```cmd
call "%ROOT_DIR%\venv-SysLab\Scripts\activate.bat"
```

## Etapa 2 — Inicio del Servidor Django

Una vez activado el entorno, se inicia el servidor de desarrollo:

```cmd
python manage.py runserver
```

El servidor queda disponible en:

```text
http://127.0.0.1:8000/
```

---

# Siguiente Paso

Continuar con: [docs/backend_methods.md](./backend_methods.md)

---

## Ejecución de pruebas

La validación del backend se divide entre pruebas unitarias y pruebas de
integración Django:

```cmd
python -m pytest tests
python manage.py test tests.backend_requirements_integration tests.integration_tests
```

El primer comando ejecuta las pruebas unitarias aisladas. El segundo crea una
base temporal, aplica las migraciones y valida los endpoints, el ORM y las
notificaciones sin persistir datos de prueba.
