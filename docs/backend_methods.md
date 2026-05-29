# Backend HTTP Requests — Documentación de API

> **Proyecto:** GPT Ingesoft — Sistema de Gestión de Mantenimiento de Equipos  
> **Universidad Nacional de Colombia**  
> Base URL: `http://127.0.0.1:8000`

---

## Módulo 2: Gestión de Usuarios

### Registrar Usuario

---

#### Endpoint

```
POST /api/usuarios/registrar/
```

#### Headers

```
Content-Type: application/json
```

---

#### Body

Los campos requeridos varían según el rol:

**Docente / Laboratorista**

```json
{
  "nombre":     "Ana Torres",
  "correo":     "atorres@unal.edu.co",
  "contrasena": "Segura123!",
  "rol":        "docente"
}
```

**Técnico** — requiere dos campos adicionales

```json
{
  "nombre":       "Carlos Ruiz",
  "correo":       "cruiz@unal.edu.co",
  "contrasena":   "Segura123!",
  "rol":          "tecnico",
  "especialidad": "Redes y Servidores",
  "contacto":     "3101234567"
}
```

#### Campos

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `nombre` | string | Siempre | Nombre completo. Mínimo 2 caracteres. |
| `correo` | string | Siempre | Correo institucional. Debe ser único en el sistema. |
| `contrasena` | string | Siempre | Contraseña en texto plano. Mínimo 8 caracteres. Se almacena hasheada. |
| `rol` | string | Siempre | Uno de: `docente`, `laboratorista`, `tecnico`. |
| `especialidad` | string | Solo `tecnico` | Área de especialización del técnico. |
| `contacto` | string | Solo `tecnico` | Número de teléfono o información de contacto. |

---

#### Respuestas

**`201 Created` — Registro exitoso**

```json
{
  "mensaje": "Usuario registrado exitosamente.",
  "usuario": {
    "id":             1,
    "nombre":         "Ana Torres",
    "correo":         "atorres@unal.edu.co",
    "rol":            "docente",
    "activo":         true,
    "fecha_creacion": "2026-05-25T10:30:00"
  }
}
```

**`400 Bad Request` — Error de validación**

```json
{
  "error": "<mensaje descriptivo del error>"
}
```

**`500 Internal Server Error` — Error del servidor**

```json
{
  "error": "Error interno. Por favor, contáctese con el soporte."
}
```

---

#### Casos de error frecuentes

| Situación | Mensaje de error |
|---|---|
| Campo obligatorio vacío o ausente | `"El campo '<campo>' es obligatorio y no puede estar vacío."` |
| Nombre menor a 2 caracteres | `"El nombre debe tener al menos 2 caracteres."` |
| Contraseña menor a 8 caracteres | `"La contraseña debe tener al menos 8 caracteres."` |
| Rol no reconocido | `"Rol '<rol>' no reconocido. Roles válidos: docente, laboratorista, tecnico."` |
| Correo ya registrado | `"El correo '<correo>' ya está registrado en el sistema."` |
| Técnico sin `especialidad` | `"El campo 'especialidad' es obligatorio y no puede estar vacío."` |
| Técnico sin `contacto` | `"El campo 'contacto' es obligatorio y no puede estar vacío."` |
| JSON malformado | `"El cuerpo de la solicitud debe ser un JSON válido."` |
| Body no es un objeto JSON | `"Se esperaba un objeto JSON con los datos de usuario."` |

---
