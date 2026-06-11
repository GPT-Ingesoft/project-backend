import sys, types, importlib.util, pathlib
import unittest
from unittest.mock import MagicMock
from datetime import datetime, timezone


def create_modules(*names):
    for name in names:
        sys.modules.setdefault(name, types.ModuleType(name))


create_modules(
    "information_app",
    "information_app.services",
    "information_app.repositories",
    "information_app.repositories.EquipmentRepository",
    "repositories",
    "repositories.equipment_repository",
)

sys.modules["information_app.repositories.EquipmentRepository"].EquipmentRepository = MagicMock
sys.modules["repositories.equipment_repository"].EquipmentRepository = MagicMock

service_path = pathlib.Path(__file__).resolve().parent.parent / "information_app" / "services" / "EquipmentServices.py"

spec = importlib.util.spec_from_file_location(
    "information_app.services.EquipmentServices",
    service_path
)

module = importlib.util.module_from_spec(spec)
module.__package__ = "information_app.services"
sys.modules["information_app.services.EquipmentServices"] = module
spec.loader.exec_module(module)
EquipmentServices = module.EquipmentServices


def make_equipment():
    equipment = MagicMock()
    equipment.id = 1
    equipment.nombre = "Osciloscopio"
    equipment.codigo_inventario = "EQ-001"
    equipment.modelo = "TBS1052B"
    equipment.marca = "Tektronix"
    equipment.numero_serie = "SN001"
    equipment.ubicacion = "Lab 101"
    equipment.estado = "en_mantenimiento"
    equipment.criticidad = "alta"
    equipment.motivo_baja = None
    equipment.fecha_baja = None
    equipment.fecha_creacion = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return equipment


def make_technician():
    user = MagicMock()
    user.id = 2
    user.nombre = "Técnico Prueba"
    user.correo = "tecnico@test.com"

    technician = MagicMock()
    technician.usuario = user
    technician.especialidad = "Electrónica"
    technician.contacto = "3001234567"
    return technician


def make_intervention():
    intervention = MagicMock()
    intervention.id = 1
    intervention.descripcion = "Se revisó la fuente de alimentación."
    intervention.observaciones = "Pendiente cambio de cable."
    intervention.fecha_intervencion = datetime(2024, 1, 2, tzinfo=timezone.utc)
    intervention.tecnico = make_technician()
    return intervention


def make_request():
    request = MagicMock()
    request.id = 1
    request.descripcion = "El equipo no enciende."
    request.prioridad = "alta"
    request.estado = "en_proceso"
    request.fecha_creacion = datetime(2024, 1, 1, tzinfo=timezone.utc)
    request.horario_agendado = None

    assignment = MagicMock()
    assignment.tecnico = make_technician()

    status_change = MagicMock()
    status_change.id = 1
    status_change.estado_anterior = "pendiente"
    status_change.estado_nuevo = "en_proceso"
    status_change.motivo = "Asignación inicial"
    status_change.fecha_cambio = datetime(2024, 1, 1, tzinfo=timezone.utc)
    status_change.usuario = None

    request.asignaciones.all.return_value = [assignment]
    request.historial_estados.all.return_value = [status_change]
    request.intervenciones.all.return_value = [make_intervention()]

    return request


class TestEquipmentHistory(unittest.TestCase):

    def _service(self, equipment):
        repo = MagicMock()
        repo.get_equipment_with_history.return_value = equipment

        service = EquipmentServices()
        service.equipment_repository = repo

        return service, repo

    def test_get_equipment_history_successfully(self):
        equipment = make_equipment()
        equipment.solicitudes.all.return_value = [make_request()]

        service, repo = self._service(equipment)

        result = service.get_equipment_history(1)

        self.assertIn("equipment", result)
        self.assertIn("maintenance_requests", result)

        self.assertEqual(result["equipment"]["id"], 1)
        self.assertEqual(len(result["maintenance_requests"]), 1)

        repo.get_equipment_with_history.assert_called_once_with(1)

    def test_equipment_history_includes_request_status(self):
        equipment = make_equipment()
        equipment.solicitudes.all.return_value = [make_request()]

        service, _ = self._service(equipment)

        result = service.get_equipment_history(1)
        request = result["maintenance_requests"][0]

        self.assertEqual(request["status"], "en_proceso")

    def test_equipment_history_includes_interventions(self):
        equipment = make_equipment()
        equipment.solicitudes.all.return_value = [make_request()]

        service, _ = self._service(equipment)

        result = service.get_equipment_history(1)
        request = result["maintenance_requests"][0]

        self.assertIn("interventions", request)
        self.assertEqual(len(request["interventions"]), 1)
        self.assertEqual(
            request["interventions"][0]["description"],
            "Se revisó la fuente de alimentación."
        )

    def test_get_equipment_history_rejects_non_existing_equipment(self):
        service, repo = self._service(None)

        with self.assertRaises(ValueError) as cm:
            service.get_equipment_history(999)

        self.assertIn("Equipment not found", str(cm.exception))
        repo.get_equipment_with_history.assert_called_once_with(999)


if __name__ == "__main__":
    unittest.main(verbosity=2)