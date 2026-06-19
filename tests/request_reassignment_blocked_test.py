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

def make_request(status):
    request = MagicMock()
    request.id = 1
    request.estado = status
    request.descripcion = "The equipment is already resolved."
    return request

class TestRequestReassignmentBlocked(unittest.TestCase):

    def _service(self, request_status):
        repo = MagicMock()
        repo.get_by_id.return_value = make_request(request_status)

        service = RequestServices()
        service.request_repository = repo

        return service, repo

    def test_rejects_reassignment_when_request_is_completed(self):
        service, repo = self._service("completada")

        with self.assertRaises(ValueError) as cm:
            service.reassign_technicians(1, {"technician_ids": [10]})

        self.assertIn("pendiente", str(cm.exception))
        self.assertIn("en_proceso", str(cm.exception))
        repo.get_technicians_by_ids.assert_not_called()
        repo.replace_assigned_technicians.assert_not_called()

    def test_rejects_reassignment_when_request_is_cancelled(self):
        service, repo = self._service("cancelada")

        with self.assertRaises(ValueError) as cm:
            service.reassign_technicians(1, {"technician_ids": [10]})

        self.assertIn("Technicians can only be reassigned", str(cm.exception))
        repo.get_technicians_by_ids.assert_not_called()
        repo.replace_assigned_technicians.assert_not_called()

    def test_rejects_reassignment_when_request_has_unknown_final_status(self):
        service, repo = self._service("cerrada")

        with self.assertRaises(ValueError) as cm:
            service.reassign_technicians(1, {"technician_ids": [10]})

        self.assertIn("Technicians can only be reassigned", str(cm.exception))
        repo.get_technicians_by_ids.assert_not_called()
        repo.replace_assigned_technicians.assert_not_called()

if __name__ == "__main__":
    unittest.main(verbosity=2)
