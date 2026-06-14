import sys
import types
import importlib.util
import pathlib
from unittest.mock import MagicMock
from datetime import datetime, timezone


def create_modules(*names):
    for name in names:
        sys.modules.setdefault(name, types.ModuleType(name))


class _Transaction:
    @staticmethod
    def atomic(fn):
        return fn


create_modules(
    "django",
    "django.db",
    "django.utils",

    "information_app",
    "information_app.repositories",
    "information_app.repositories.Solicitud_repository",
)

sys.modules["django.db"].transaction = _Transaction
sys.modules["django.utils"].timezone = MagicMock()
sys.modules["information_app.repositories.Solicitud_repository"].SolicitudRepository = MagicMock

service_path = pathlib.Path(__file__).resolve().parent.parent / "information_app" / "services" / "solicitud_services.py"

spec = importlib.util.spec_from_file_location(
    "information_app.services.solicitud_services",
    service_path,
)

module = importlib.util.module_from_spec(spec)
module.__package__ = "information_app.services"
sys.modules["information_app.services.solicitud_services"] = module
spec.loader.exec_module(module)
SolicitudServices = module.SolicitudServices


def make_usuario(nombre="Ana Torres", correo="ana@test.com", rol="docente"):
    u = MagicMock()
    u.id = 1
    u.nombre = nombre
    u.correo = correo
    u.rol = rol
    return u


def make_equipo(nombre="Osciloscopio"):
    e = MagicMock()
    e.id = 1
    e.nombre = nombre
    return e


def make_solicitud(
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
    s.usuario = usuario or make_usuario()
    s.equipo = equipo or make_equipo()
    s.fecha_creacion = datetime(2024, 1, 1, tzinfo=timezone.utc)
    s.fecha_cierre = None
    return s


def make_adjunto(
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
    adjunto.anexo.solicitud.id = solicitud_id
    return adjunto
