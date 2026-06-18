import importlib.util
import pathlib
import sys
import types
import unittest
from dataclasses import dataclass
from unittest.mock import MagicMock

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
    "information_app",
    "information_app.repositories",
    "information_app.repositories.request_repository",
    "information_app.services",
    "information_app.services.services_utils",
)

sys.modules["django.db"].transaction = _Transaction
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

def make_request():
    request = MagicMock()
    request.id = 1
    request.estado = "pendiente"
    request.descripcion = "The equipment needs diagnosis."
    return request

def make_technician(user_id):
    user = MagicMock()
    user.id = user_id
    user.nombre = f"Technician {user_id}"
    user.correo = f"tech{user_id}@test.com"

    technician = MagicMock()
    technician.usuario = user
    technician.especialidad = "Networks"
    technician.contacto = "555-1111"
    return technician

class TestRequestReassignmentValidation(unittest.TestCase):

    def test_validate_technician_ids_rejects_invalid_payloads(self):
        cases = [
            ({}, "technician_ids"),
            ({"technician_ids": []}, "non-empty"),
            ({"technician_ids": "10"}, "non-empty"),
            ({"technician_ids": [10, "20"]}, "integer"),
            ({"technician_ids": [10, 10]}, "duplicated"),
        ]

        for data, match in cases:
            with self.subTest(data=data):
                with self.assertRaises(ValueError) as cm:
                    RequestServices._validate_technician_ids(data)

                self.assertIn(match, str(cm.exception))

    def test_rejects_missing_technicians(self):
        repo = MagicMock()
        repo.get_by_id.return_value = make_request()
        repo.get_technicians_by_ids.return_value = [make_technician(10)]

        service = RequestServices()
        service.request_repository = repo

        with self.assertRaises(ValueError) as cm:
            service.reassign_technicians(1, {"technician_ids": [10, 20]})

        self.assertIn("20", str(cm.exception))
        repo.replace_assigned_technicians.assert_not_called()

    def test_rejects_missing_request(self):
        repo = MagicMock()
        repo.get_by_id.return_value = None

        service = RequestServices()
        service.request_repository = repo

        with self.assertRaises(ValueError) as cm:
            service.reassign_technicians(999, {"technician_ids": [10]})

        self.assertIn("Request not found", str(cm.exception))
        repo.get_technicians_by_ids.assert_not_called()

if __name__ == "__main__":
    unittest.main(verbosity=2)
