import sys
import types
import importlib.util
import pathlib
from unittest.mock import MagicMock
from datetime import datetime, timezone
from dataclasses import dataclass

def create_modules(*names):
    for name in names:
        sys.modules.setdefault(name, types.ModuleType(name))

class _Transaction:
    @staticmethod
    def atomic(fn):
        return fn

class _Timezone:
    @staticmethod
    def now():
        return datetime(2024, 1, 1, tzinfo=timezone.utc)

create_modules(
    "django",
    "django.db",
    "django.utils",

    "information_app",
    "information_app.repositories",
    "information_app.repositories.request_repository",
    "information_app.services",
    "information_app.services.services_utils",
)

sys.modules["django.db"].transaction = _Transaction
sys.modules["django.utils"].timezone = _Timezone()
sys.modules["information_app.repositories.request_repository"].RequestRepository = MagicMock

@dataclass
class _AttachmentData:
    archivo: object = None
    tipo: str = "otro"
    nombre: str = ""
    tamanio: int = 0
    descripcion: str = ""

sys.modules["information_app.repositories.request_repository"].AttachmentData = _AttachmentData

service_path = pathlib.Path(__file__).resolve().parent.parent / "information_app" / "services" / "request_services.py"

spec = importlib.util.spec_from_file_location(
    "information_app.services.request_services",
    service_path,
)

module = importlib.util.module_from_spec(spec)
module.__package__ = "information_app.services"
sys.modules["information_app.services.request_services"] = module
spec.loader.exec_module(module)
RequestServices = module.RequestServices

def make_user(nombre="Ana Torres", correo="ana@test.com", rol="docente"):
    u = MagicMock()
    u.id = 1
    u.nombre = nombre
    u.correo = correo
    u.rol = rol
    return u

def make_equipment(nombre="Osciloscopio"):
    e = MagicMock()
    e.id = 1
    e.nombre = nombre
    return e

def make_request(
    id=1,
    estado="pendiente",
    prioridad="media",
    descripcion="El equipo no enciende.",
    usuario=None,
    equipo=None,
):
    s = MagicMock()
    s.id = id
    s.estado = estado
    s.prioridad = prioridad
    s.descripcion = descripcion
    s.usuario = usuario or make_user()
    s.equipo = equipo or make_equipment()
    s.fecha_creacion = datetime(2024, 1, 1, tzinfo=timezone.utc)
    s.fecha_cierre = None
    return s

def make_technician(user_id=10):
    user = MagicMock()
    user.id = user_id
    user.nombre = f"Technician {user_id}"
    user.correo = f"tech{user_id}@test.com"

    technician = MagicMock()
    technician.usuario = user
    technician.especialidad = "Electronics"
    technician.contacto = "555-0000"
    return technician

def make_attachment(
    id=1,
    nombre_archivo="diagnostico.pdf",
    tipo="documento",
    tamanio_bytes=2048,
    solicitud_id=1,
):
    adjunto = MagicMock()
    adjunto.id = id
    adjunto.nombre_archivo = nombre_archivo
    adjunto.tipo = tipo
    adjunto.tamanio_bytes = tamanio_bytes
    adjunto.fecha_carga = datetime(2024, 1, 2, tzinfo=timezone.utc)
    anexo = MagicMock()
    anexo.solicitud = MagicMock()
    anexo.solicitud.id = solicitud_id
    adjunto.anexo = anexo
    return adjunto
