# Ejecución del Backend

Este documento describe el proceso de ejecución del backend Django del proyecto SysLab.

---

# Objetivo

Automatizar el inicio del servidor de desarrollo Django utilizando el entorno virtual previamente configurado.

El proceso permite:

- Activar automáticamente el entorno virtual.
- Posicionarse dentro del proyecto Django.
- Ejecutar el servidor backend localmente.

---

# Archivo Relacionado

```text
scripts/backend/EjecutarBackend.ps1
```

---

# Script de Ejecución

El backend se inicia mediante el script:

```powershell
.\scripts\backend\EjecutarBackend.ps1
```

---

# Flujo de Ejecución

El script automatiza completamente el proceso de arranque del backend.

Durante la ejecución:

1. Se accede a la raíz del proyecto.
2. Se activa automáticamente el entorno virtual `venv-SysLab`.
3. Se accede al directorio `src/`.
4. Se inicia el servidor de desarrollo Django.

Internamente el script ejecuta:

```powershell
python manage.py runserver
```

---

# Siguiente Paso

Continuar con: [docs/backend-http-request.md](./backend-http-request.md)