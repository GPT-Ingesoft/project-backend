import sys, types, importlib.util, pathlib
from unittest.mock import MagicMock
from datetime import datetime, timezone
 
def create_modules(*names):
    for name in names:
        sys.modules.setdefault(name, types.ModuleType(name))

class _Transaction:
    @staticmethod
    def atomic(fn): return fn

class _Settings:
    SECRET_KEY = "clave-tests"

create_modules(
    "django",
    "django.conf",
    "django.db",
    "django.core",
    "django.core.cache",
    "users",
    "users.repositories",
    "users.repositories.UserRepository",
    "users.services"
)
 
sys.modules["django.conf"].settings    = _Settings
sys.modules["django.db"].transaction   = _Transaction
sys.modules["django.core.cache"].cache = MagicMock()
sys.modules["users.repositories.UserRepository"].UserRepository = MagicMock

service_path = pathlib.Path(__file__).resolve().parent.parent / "information_app" /"services" / "UserServices.py"

spec = importlib.util.spec_from_file_location(
    "users.services.UserServices",
    service_path
)

module = importlib.util.module_from_spec(spec)
module.__package__ = "users.services"
sys.modules["users.services.UserServices"] = module
spec.loader.exec_module(module)
UserServices = module.UserServices

def make_user(nombre="Ana Torres", correo="ana@test.com", rol="docente"):
    u = MagicMock()
    u.id = 1;  u.nombre = nombre;  u.correo = correo
    u.rol = rol;  u.activo = True
    u.fecha_creacion = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return u
 