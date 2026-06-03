# Backend HTTP Requests — Documentación de API

> **Proyecto:** GPT Ingesoft — Sistema de Gestión de Mantenimiento de Equipos  
> **Universidad Nacional de Colombia**  
> Base URL: `http://127.0.0.1:8000`

---

## Módulo de Autenticación

### 1. Iniciar Login OAuth 2.0

#### Endpoint

```
GET /api/auth/login/{provider}/
```

#### Parámetros de ruta

| Parámetro | Valores soportados |
|---|---|
| `provider` | `google` |

#### Descripción

Redirige al proveedor OAuth para iniciar el flujo de autenticación. No requiere body ni headers adicionales. El servidor genera un `state` anti-CSRF y lo almacena en caché antes de redirigir.

#### Respuestas

**`302 Found` — Redirección al proveedor**

Redirige automáticamente a la página de login del proveedor (e.g. Google). No retorna body.

**`400 Bad Request` — Proveedor no soportado**

```json
{
  "error": "Provider \"<provider>\" is not supported. Available: ['google']"
}
```

---

### 2. Callback OAuth 2.0

#### Endpoint

```
GET /api/auth/callback/{provider}/
```

#### Descripción

Endpoint al que redirige el proveedor tras la autenticación. Valida el `state` anti-CSRF, intercambia el `code` por un token de acceso con el proveedor, verifica que el correo esté registrado en el sistema y retorna los tokens JWT.

#### Query Parameters (enviados automáticamente por el proveedor)

| Parámetro | Descripción |
|---|---|
| `code` | Código de autorización entregado por el proveedor |
| `state` | Token anti-CSRF generado en el paso anterior |

#### Respuestas

**`200 OK` — Login exitoso**

```json
{
  "message":    "Welcome, Ana Torres",
  "user": {
    "id":         1,
    "name":       "Ana Torres",
    "email":      "atorres@unal.edu.co",
    "role":       "docente",
    "active":     true,
    "created_at": "2026-05-25T10:30:00"
  },
  "access":     "<access_token>",
  "refresh":    "<refresh_token>",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

**`400 Bad Request` — Parámetros faltantes o state inválido**

```json
{
  "error": "Missing callback parameters (code, state)."
}
```

```json
{
  "error": "Invalid or expired OAuth state. Please restart the login process."
}
```

**`403 Forbidden` — Correo no registrado en el sistema**

```json
{
  "error": "Email <email> is not registered in the system. Contact the administrator to request access."
}
```

**`502 Bad Gateway` — Error de comunicación con el proveedor**

```json
{
  "error": "Could not communicate with Google for code exchange."
}
```

```json
{
  "error": "Could not retrieve user information from Google."
}
```

**`500 Internal Server Error`**

```json
{
  "error": "Internal error. Please contact support."
}
```

---

### 3. Renovar Access Token

#### Endpoint

```
POST /api/auth/refresh/
```

#### Headers

```
Content-Type: application/json
```

#### Body

```json
{
  "refresh": "<refresh_token>"
}
```

#### Respuestas

**`200 OK` — Token renovado exitosamente**

```json
{
  "access":     "<nuevo_access_token>",
  "token_type": "Bearer"
}
```

**`400 Bad Request` — Campo faltante o body inválido**

```json
{
  "error": "Field \"refresh\" is required."
}
```

```json
{
  "error": "The request body must be a valid JSON object. Make sure to include the header Content-Type: application/json"
}
```

**`401 Unauthorized` — Token inválido o expirado**

```json
{
  "error": "Refresh token expired. Please log in again."
}
```

```json
{
  "error": "Invalid refresh token."
}
```

---

### 4. Obtener Usuario Autenticado

#### Endpoint

```
GET /api/auth/me/
```

#### Headers

```
Authorization: Bearer <access_token>
```

#### Respuestas

**`200 OK`**

```json
{
  "id":         1,
  "name":       "Ana Torres",
  "email":      "atorres@unal.edu.co",
  "role":       "docente",
  "active":     true,
  "created_at": "2026-05-25T10:30:00"
}
```

**`401 Unauthorized` — Token ausente, inválido o expirado**

```json
{
  "error": "Token required. Include the header: Authorization: Bearer <token>"
}
```

```json
{
  "error": "Token expired. Renew it at POST /auth/refresh/"
}
```

```json
{
  "error": "User not found or inactive."
}
```

---

## Módulo 2: Gestión de Usuarios

### 5. Registrar Usuario

> Requiere autenticación. Solo usuarios con rol `laboratorista` pueden acceder a este endpoint.

#### Endpoint

```
POST /api/users/register/
```

#### Headers

```
Content-Type: application/json
Authorization: Bearer <access_token>
```

---

#### Body

Los campos requeridos varían según el rol:

**Docente / Laboratorista**

```json
{
  "name":  "Ana Torres",
  "email": "atorres@unal.edu.co",
  "role":  "docente"
}
```

**Técnico** — requiere dos campos adicionales

```json
{
  "name":      "Carlos Ruiz",
  "email":     "cruiz@unal.edu.co",
  "role":      "tecnico",
  "specialty": "Redes y Servidores",
  "contact":   "3101234567"
}
```

#### Campos

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `name` | string | Siempre | Nombre completo. Mínimo 2 caracteres. |
| `email` | string | Siempre | Correo institucional. Debe ser único en el sistema. |
| `role` | string | Siempre | Uno de: `docente`, `laboratorista`, `tecnico`. |
| `specialty` | string | Solo `tecnico` | Área de especialización del técnico. |
| `contact` | string | Solo `tecnico` | Número de teléfono o información de contacto. |

---

#### Respuestas

**`201 Created` — Registro exitoso**

```json
{
  "message": "User registered successfully.",
  "user": {
    "id":         1,
    "name":       "Ana Torres",
    "email":      "atorres@unal.edu.co",
    "role":       "docente",
    "active":     true,
    "created_at": "2026-05-25T10:30:00"
  }
}
```

**`400 Bad Request` — Error de validación**

```json
{
  "error": "<descriptive error message>"
}
```

**`401 Unauthorized` — Token ausente, inválido o expirado**

```json
{
  "error": "Token required. Include the header: Authorization: Bearer <token>"
}
```

**`403 Forbidden` — Rol insuficiente**

```json
{
  "error": "Only lab technician users can register new users."
}
```

**`500 Internal Server Error`**

```json
{
  "error": "Internal error. Please contact support."
}
```

---

#### Casos de error frecuentes

| Situación | Mensaje de error |
|---|---|
| Campo obligatorio vacío o ausente | `"Field '<field>' is required and cannot be empty."` |
| Nombre menor a 2 caracteres | `"Name must be at least 2 characters long."` |
| Rol no reconocido | `"Role '<role>' is not valid. Allowed roles: docente, laboratorista, tecnico."` |
| Correo ya registrado | `"Email '<email>' is already registered. Please choose another."` |
| Técnico sin `specialty` | `"Field 'specialty' is required and cannot be empty."` |
| Técnico sin `contact` | `"Field 'contact' is required and cannot be empty."` |
| Body inválido o sin `Content-Type` | `"The request body must be a valid JSON object. Make sure to include the header Content-Type: application/json"` |

---

### 6. Registrar Usuario (Debug)

> ⚠️ **Solo para desarrollo.** Este endpoint no requiere autenticación.

#### Endpoint

```
POST /api/users/register_debug/
```

#### Headers

```
Content-Type: application/json
```

#### Body y Respuestas

Idénticos al endpoint `POST /api/users/register/`, sin los errores `401` y `403`.

---