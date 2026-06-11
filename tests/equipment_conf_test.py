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

class _Settings:
    SECRET_KEY = "clave-tests"

create_modules(
    "django",
    "django.conf",
    "django.db",
    "django.core",
    "django.core.cache",

    "information_app",
    "information_app.repositories",
    "information_app.repositories.equipment_repository",
)

sys.modules["django.conf"].settings    = _Settings
sys.modules["django.db"].transaction = _Transaction
sys.modules["django.core.cache"].cache = MagicMock()
sys.modules["information_app.repositories.equipment_repository"].EquipmentRepository = MagicMock

service_path = pathlib.Path(__file__).resolve().parent.parent / "information_app" /"services" / "equipment_services.py"

spec   = importlib.util.spec_from_file_location(
    "information_app.services.equipment_services",
    service_path,
)

module = importlib.util.module_from_spec(spec)
module.__package__ = "information_app.services"
sys.modules["information_app.services.equipment_services"] = module
spec.loader.exec_module(module)
EquipmentServices = module.EquipmentServices

def make_equipment(
    nombre            = "Microscopio Olympus",
    codigo_inventario = "INV-001",
    modelo            = "CX23",
    marca             = "Olympus",
    numero_serie      = "SN-XYZ-001",
    ubicacion         = "Lab 301",
    estado            = "operativo",
    criticidad        = "media",
):
    e = MagicMock()
    e.id               = 1
    e.nombre           = nombre
    e.codigo_inventario = codigo_inventario
    e.modelo           = modelo
    e.marca            = marca
    e.numero_serie     = numero_serie
    e.ubicacion        = ubicacion
    e.estado           = estado
    e.criticidad       = criticidad
    e.motivo_baja      = None
    e.fecha_baja       = None
    e.fecha_creacion   = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return e
