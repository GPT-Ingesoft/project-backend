# Backend HTTP Requests — Documentación de API

> **Proyecto:** GPT Ingesoft — Sistema de Gestión de Mantenimiento de Equipos  
> **Universidad Nacional de Colombia**  
> Base URL: `http://127.0.0.1:8000`

---

## Autenticación y Renovación Automática de Tokens

Esta API utiliza JWT (JSON Web Tokens) para la autenticación. El sistema cuenta con un **middleware de renovación automática** que gestiona los tokens de acceso (access token) y actualización (refresh token) de forma transparente.

### Headers Requeridos para Endpoints Autenticados

Todos los endpoints que requieren autenticación deben incluir los siguientes headers:

| Header | Descripción |
|---|---|
| `Authorization` | El access token válido. Formato: `Bearer <access_token>` |
| `X-Refresh-Token` | El refresh token asociado. Se utiliza para renovar automáticamente el access token si este ha expirado. |

### Renovación Automática

Cuando un access token expira, el middleware intenta automáticamente generar uno nuevo utilizando el refresh token proporcionado en `X-Refresh-Token`. Si la renovación es exitosa:

1.  La solicitud se procesa normalmente con el nuevo access token.
2.  La respuesta incluirá un nuevo header `X-New-Access-Token` con el token renovado.

### Header de Respuesta: `X-New-Access-Token`

| Header | Descripción |
|---|---|
| `X-New-Access-Token` | Este header aparece en la respuesta cuando el middleware ha renovado automáticamente el access token. El cliente debe almacenar este nuevo token para usarlo en futuras solicitudes. |

### Flujo de Renovación Manual (Opcional)

Si el refresh token también ha expirado o es inválido, la renovación automática fallará y el cliente deberá utilizar el endpoint `POST /api/auth/refresh/` para renovar manualmente o iniciar un nuevo flujo de login.

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

### 3. Renovar Access Token (Manual)

> **Nota:** Este endpoint es opcional debido al middleware de renovación automática. Úsalo si el refresh token también ha expirado o si necesitas renovar tokens sin hacer una solicitud autenticada.

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
X-Refresh-Token: <refresh_token>
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
  "error": "Token expired. Include X-Refresh-Token header for automatic renewal."
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
X-Refresh-Token: <refresh_token>
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

```json
{
  "error": "Token expired. Include X-Refresh-Token header for automatic renewal."
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

## Módulo 3: Gestión de Equipos
 
### 7. Registrar Equipo
 
> Requiere autenticación. Solo usuarios con rol `laboratorista` pueden acceder a este endpoint.
 
#### Endpoint
 
```
POST /api/equipment/register/
```
 
#### Headers
 
```
Content-Type: application/json
Authorization: Bearer <access_token>
X-Refresh-Token: <refresh_token>
```
 
#### Body
 
```json
{
  "name":           "Microscopio Óptico",
  "inventory_code": "EQ-001",
  "model":          "Axiostar Plus",
  "brand":          "Zeiss",
  "serial_number":  "SN-2024-001",
  "location":       "Laboratorio 3 - Piso 2",
  "status":         "operativo",
  "criticality":    "alta",
  "solicitud_id":   "3"
}
```
 
#### Campos
 
| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `name` | string | Sí | Nombre del equipo. |
| `inventory_code` | string | Sí | Código de inventario. Debe ser único en el sistema. |
| `model` | string | Sí | Modelo del equipo. |
| `brand` | string | Sí | Marca fabricante del equipo. |
| `serial_number` | string | Sí | Número de serie. Debe ser único en el sistema. |
| `location` | string | Sí | Ubicación física del equipo. |
| `status` | string | No | Estado inicial. Por defecto: `operativo`. Valores: `operativo`, `en_mantenimiento`, `fuera_de_servicio`. |
| `criticality` | string | No | Criticidad del equipo. Por defecto: `media`. Valores: `alta`, `media`, `baja`. |
 | `solicitud_id` | integer | **No** | **Nuevo:** ID de la solicitud de mantenimiento. Si se proporciona, el equipo se registra y se vincula automáticamente a esta solicitud, limpiando sus datos provisionales. |

---
 
#### Respuestas
 
**`201 Created` — Registro exitoso**
 
```json
{
  "message": "Equipment registered successfully.",
  "equipment": {
    "id":                  1,
    "name":                "Microscopio Óptico",
    "inventory_code":      "EQ-001",
    "model":               "Axiostar Plus",
    "brand":               "Zeiss",
    "serial_number":       "SN-2024-001",
    "location":            "Laboratorio 3 - Piso 2",
    "status":              "operativo",
    "criticality":         "alta",
    "decommission_reason": null,
    "decommission_date":   null,
    "created_at":          "2026-05-25T10:30:00"
  }
}
```
 
**`400 Bad Request` — Error de validación**
 
```json
{
  "error": "<mensaje de error descriptivo>"
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
  "error": "Token expired. Include X-Refresh-Token header for automatic renewal."
}
```

 
**`403 Forbidden` — Rol insuficiente**
 
```json
{
  "error": "Only lab technicians can register equipment."
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
| Estado no reconocido | `"Status '<status>' is not valid. Allowed values: en_mantenimiento, fuera_de_servicio, operativo."` |
| Criticidad no reconocida | `"Criticality '<criticality>' is not valid. Allowed values: alta, baja, media."` |
| Código de inventario ya registrado | `"Inventory code '<code>' is already registered. Please use a different code."` |
| Número de serie ya registrado | `"Serial number '<serial>' is already registered. Please verify the serial number."` |
| Body inválido o sin `Content-Type` | `"The request body must be a valid JSON object. Make sure to include the header Content-Type: application/json"` |
 
---
 
### 8. Registrar Equipo (Debug)
 
> ⚠️ **Solo para desarrollo.** Este endpoint no requiere autenticación.
 
#### Endpoint
 
```
POST /api/equipment/register_debug/
```
 
#### Headers
 
```
Content-Type: application/json
```
 
#### Body y Respuestas
 
Idénticos al endpoint `POST /api/equipment/register/`, sin los errores `403`.

---

### 9. Actualizar Equipo

> Requiere autenticación. Solo usuarios con rol `laboratorista` pueden acceder a este endpoint.

#### Endpoint

```
PATCH /api/equipment/{equipment_id}/update/
```

#### Parámetros de ruta

| Parámetro | Tipo | Descripción |
|---|---|---|
| `equipment_id` | integer | ID del equipo a actualizar |

#### Headers

```
Content-Type: application/json
Authorization: Bearer <access_token>
X-Refresh-Token: <refresh_token>
```

#### Body

Es una actualización parcial: solo se modifican los campos presentes en el body. Cualquier campo omitido conserva su valor actual.

```json
{
  "name":           "Microscopio Óptico Avanzado",
  "inventory_code": "EQ-001-A",
  "model":          "Axiostar Plus v2",
  "brand":          "Zeiss",
  "location":       "Laboratorio 4 - Piso 3",
  "status":         "en_mantenimiento",
  "criticality":    "alta"
}
```

#### Campos

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `name` | string | No | Nuevo nombre del equipo. No puede ser vacío si se envía. |
| `inventory_code` | string | No | Nuevo código de inventario. Debe ser único en el sistema (excluyendo el equipo actual). |
| `model` | string | No | Nuevo modelo del equipo. No puede ser vacío si se envía. |
| `brand` | string | No | Nueva marca del equipo. No puede ser vacío si se envía. |
| `location` | string | No | Nueva ubicación física. No puede ser vacío si se envía. |
| `status` | string | No | Nuevo estado. Valores permitidos: `operativo`, `en_mantenimiento`, `fuera_de_servicio`. |
| `criticality` | string | No | Nueva criticidad. Valores permitidos: `alta`, `media`, `baja`. |
| `serial_number` | — | ❌ Prohibido | El número de serie **no puede modificarse**. El sistema rechazará la solicitud si este campo está presente. |

---

#### Respuestas

**`200 OK` — Actualización exitosa**

```json
{
  "message": "Equipment updated successfully.",
  "equipment": {
    "id":                  1,
    "name":                "Microscopio Óptico Avanzado",
    "inventory_code":      "EQ-001-A",
    "model":               "Axiostar Plus v2",
    "brand":               "Zeiss",
    "serial_number":       "SN-2024-001",
    "location":            "Laboratorio 4 - Piso 3",
    "status":              "en_mantenimiento",
    "criticality":         "alta",
    "decommission_reason": null,
    "decommission_date":   null,
    "created_at":          "2026-05-25T10:30:00"
  }
}
```

**`400 Bad Request` — Error de validación**

```json
{
  "error": "<mensaje de error descriptivo>"
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
  "error": "Token expired. Include X-Refresh-Token header for automatic renewal."
}
```

**`403 Forbidden` — Rol insuficiente**

```json
{
  "error": "Only lab technicians can update equipment."
}
```

**`500 Internal Server Error`**

```json
{
  "error": "Internal error. Please contact support."
}
```

---

## Módulo 4: Gestión de Solicitudes

Este módulo permite a los docentes crear solicitudes de mantenimiento proporcionando datos provisionales de equipos que aún no están registrados en el inventario. El laboratorista revisa estos datos para registrar el equipo formalmente.

### 10. Crear Solicitud de Mantenimiento

> Requiere autenticación. Disponible para roles `docente` y `laboratorista`.

#### Endpoint

```
POST /api/solicitudes/crear/
```

#### Headers

```
Content-Type: application/json
Authorization: Bearer <access_token>
X-Refresh-Token: <refresh_token>
```

#### Body

El docente envía la descripción del problema y un objeto con los datos del equipo (provisionales).

```json
{
  "descripcion": "El equipo no enciende y hace ruidos extraños.",
  "prioridad": "alta",
  "datos_equipo": {
    "name": "PC Laboratorio A",
    "inventory_code": "INV-999",
    "model": "OptiPlex 9020",
    "brand": "Dell",
    "serial_number": "SN-PROVISIONAL-123",
    "location": "Laboratorio A"
  }
}
```

#### Campos

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `descripcion` | string | Sí | Descripción detallada del problema reportado. |
| `prioridad` | string | No | Prioridad de la solicitud. Por defecto: `media`. Valores: `alta`, `media`, `baja`. |
| `datos_equipo` | object | Sí | Objeto JSON con los datos del equipo. Debe contener al menos: `name`, `inventory_code`, `model`, `brand`, `serial_number`, `location`. |

---

#### Respuestas

**`201 Created` — Solicitud creada exitosamente**

```json
{
  "message": "Solicitud creada exitosamente. Pendiente de registro de equipo.",
  "solicitud": {
    "id": 1,
    "estado": "pendiente",
    "prioridad": "alta",
    "descripcion": "El equipo no enciende y hace ruidos extraños.",
    "equipo": null,
    "datos_equipo_solicitado": {
      "name": "PC Laboratorio A",
      "inventory_code": "INV-999",
      "model": "OptiPlex 9020",
      "brand": "Dell",
      "serial_number": "SN-PROVISIONAL-123",
      "location": "Laboratorio A"
    },
    "usuario": "Ana Torres",
    "created_at": "2026-05-25T10:30:00"
  }
}
```

**`400 Bad Request` — Error de validación**

```json
{
  "error": "Debe proporcionar los datos del equipo ('datos_equipo')."
}
```

**`401 Unauthorized`**

```json
{
  "error": "Token required..."
}
```

---

### 11. Ver Detalles de Solicitud

> Requiere autenticación. Solo para usuarios con rol `laboratorista`. Permite revisar la solicitud y los datos provisionales del equipo antes de registrar.

#### Endpoint

```
GET /api/solicitudes/<solicitud_id>/detalle/
```

#### Headers

```
Authorization: Bearer <access_token>
X-Refresh-Token: <refresh_token>
```

#### Respuestas

**`200 OK`**

```json
{
  "id": 1,
  "estado": "pendiente",
  "prioridad": "alta",
  "descripcion": "El equipo no enciende...",
  "equipo": null,
  "datos_equipo_solicitado": {
    "name": "PC Laboratorio A",
    "inventory_code": "INV-999",
    "model": "OptiPlex 9020",
    "brand": "Dell",
    "serial_number": "SN-PROVISIONAL-123",
    "location": "Laboratorio A"
  },
  "usuario": "Ana Torres",
  "created_at": "2026-05-25T10:30:00"
}
```

---

### 12. Crear Solicitud (Debug)

> ⚠️ **Solo para desarrollo.** No requiere autenticación.

#### Endpoint

```
POST /api/solicitudes/crear_debug/
```

#### Headers

```
Content-Type: application/json
```

#### Body y Respuestas

Idénticos al endpoint `POST /api/solicitudes/crear/`, sin la necesidad de enviar tokens JWT.

---

### 13. Ver Detalles de Solicitud (Debug)

> ⚠️ **Solo para desarrollo.** No requiere autenticación.

#### Endpoint

```
GET /api/solicitudes/<solicitud_id>/detalle_debug/
```

#### Respuestas

Idénticas al endpoint `GET /api/solicitudes/<id>/detalle/`, sin necesidad de enviar tokens JWT.
