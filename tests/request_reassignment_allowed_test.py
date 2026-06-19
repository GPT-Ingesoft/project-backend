import importlib.util
import pathlib
import sys
import types
import unittest
from datetime import datetime, timezone
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
    "information_app.services.notification_services",
    "information_app.services.services_utils",
)

sys.modules["django.db"].transaction = _Transaction
sys.modules["information_app.repositories.request_repository"].RequestRepository = MagicMock
sys.modules[
    "information_app.services.notification_services"
].NotificationServices = MagicMock

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

def make_request(status="pendiente"):
    request = MagicMock()
    request.id = 1
    request.estado = status
    request.descripcion = "The microscope does not turn on."
    request.fecha_creacion = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return request

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

class TestRequestReassignmentAllowed(unittest.TestCase):

    def _service(self, request_status):
        repo = MagicMock()
        repo.get_by_id.return_value = make_request(status=request_status)
        repo.get_technicians_by_ids.return_value = [
            make_technician(10),
            make_technician(20),
        ]
        repo.get_available_technicians.return_value = repo.get_technicians_by_ids.return_value

        service = RequestServices()
        service.request_repository = repo

        return service, repo

    def test_reassign_technicians_when_request_is_pending(self):
        service, repo = self._service("pendiente")

        result = service.reassign_technicians(1, {"technician_ids": [10, 20]})

        self.assertEqual(result["request"]["status"], "pendiente")
        self.assertEqual(len(result["assigned_technicians"]), 2)

        repo.get_by_id.assert_called_once_with(1)
        repo.get_technicians_by_ids.assert_called_once_with([10, 20])
        repo.replace_assigned_technicians.assert_called_once()

    def test_reassign_technicians_when_request_is_in_process(self):
        service, repo = self._service("en_proceso")

        result = service.reassign_technicians(1, {"technician_ids": [10, 20]})

        self.assertEqual(result["request"]["status"], "en_proceso")
        self.assertEqual(result["assigned_technicians"][0]["id"], 10)
        repo.replace_assigned_technicians.assert_called_once()

    def test_reassign_technicians_returns_formatted_assignment_data(self):
        service, _ = self._service("pendiente")

        result = service.reassign_technicians(1, {"technician_ids": [10, 20]})

        self.assertEqual(result["request"]["id"], 1)
        self.assertEqual(result["request"]["description"], "The microscope does not turn on.")
        self.assertEqual(result["assigned_technicians"][0]["name"], "Technician 10")
        self.assertEqual(result["assigned_technicians"][1]["email"], "tech20@test.com")

if __name__ == "__main__":
    unittest.main(verbosity=2)
