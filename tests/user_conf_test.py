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
    def atomic(fn): return fn

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
    "information_app.repositories.user_repository",
    "information_app.services",
    "information_app.services.services_utils",
)

sys.modules["django.conf"].settings    = _Settings
sys.modules["django.db"].transaction   = _Transaction
sys.modules["django.core.cache"].cache = MagicMock()
sys.modules["information_app.repositories.user_repository"].UserRepository = MagicMock

services_utils_path = pathlib.Path(__file__).resolve().parent.parent / "information_app" / "services" / "services_utils.py"
spec_utils = importlib.util.spec_from_file_location(
    "information_app.services.services_utils",
    services_utils_path,
)
module_utils = importlib.util.module_from_spec(spec_utils)
module_utils.__package__ = "information_app.services"
sys.modules["information_app.services.services_utils"] = module_utils
spec_utils.loader.exec_module(module_utils)
format_user_data = module_utils.format_user_data
validate_required_fields = module_utils.validate_required_fields

service_path = pathlib.Path(__file__).resolve().parent.parent / "information_app" /"services" / "user_services.py"

spec = importlib.util.spec_from_file_location(
    "information_app.services.user_services",
    service_path
)

module = importlib.util.module_from_spec(spec)
module.__package__ = "information_app.services"
sys.modules["information_app.services.user_services"] = module
spec.loader.exec_module(module)
UserServices = module.UserServices

def make_user(nombre="Ana Torres", correo="ana@test.com", rol="docente"):
    u = MagicMock()
    u.id = 1
    u.nombre = nombre
    u.correo = correo
    u.rol = rol
    u.activo = True
    u.fecha_creacion = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return u
