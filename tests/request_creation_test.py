import unittest
from datetime import time
from unittest.mock import MagicMock

from tests.request_conf_test import RequestServices, make_request, make_user


def make_equipment(equipment_id=1, status='operativo', location='Lab 101'):
    equipment = MagicMock()
    equipment.id = equipment_id
    equipment.nombre = 'Osciloscopio'
    equipment.estado = status
    equipment.ubicacion = location
    return equipment


def make_schedule(
    schedule_id=1,
    laboratory='Lab 101',
    available=True,
    start=time(8, 0),
    end=time(10, 0),
):
    schedule = MagicMock()
    schedule.id = schedule_id
    schedule.laboratorio = laboratory
    schedule.disponible = available
    schedule.hora_inicio = start
    schedule.hora_fin = end
    schedule.get_dia_display.return_value = 'Lunes'
    return schedule


class TestCreateMaintenanceRequest(unittest.TestCase):

    def _service(self, equipment=None, schedule=None):
        repo = MagicMock()
        repo.get_equipment_by_id.return_value = equipment or make_equipment()
        repo.get_schedule_by_id.return_value = schedule

        def create_request(**kwargs):
            request = make_request(
                estado='pendiente',
                prioridad=kwargs['prioridad'],
                descripcion=kwargs['descripcion'],
                usuario=kwargs['usuario'],
                equipo=kwargs['equipo'],
            )
            request.horario_agendado = kwargs['horario_agendado']
            return request

        repo.create_request.side_effect = create_request
        service = RequestServices()
        service.request_repository = repo
        return service, repo

    def test_creation_uses_automatic_pending_status_and_creation_date(self):
        service, repo = self._service()
        result = service.create_request(
            {'descripcion': '  No enciende  ', 'equipo_id': 1},
            make_user(),
        )

        self.assertEqual(result['estado'], 'pendiente')
        self.assertEqual(result['created_at'], '2024-01-01T00:00:00+00:00')
        self.assertEqual(result['descripcion'], 'No enciende')
        self.assertEqual(repo.create_request.call_args.kwargs['prioridad'], 'media')

    def test_creation_accepts_available_schedule_for_equipment_location(self):
        schedule = make_schedule()
        service, _ = self._service(schedule=schedule)

        result = service.create_request(
            {
                'descripcion': 'Revisión preventiva',
                'equipo_id': 1,
                'horario_id': 1,
                'prioridad': 'alta',
            },
            make_user(),
        )

        self.assertEqual(result['horario_agendado']['id'], 1)
        self.assertEqual(result['horario_agendado']['laboratorio'], 'Lab 101')

    def test_creation_rejects_server_managed_fields(self):
        service, repo = self._service()

        with self.assertRaises(ValueError):
            service.create_request(
                {'descripcion': 'Falla', 'equipo_id': 1, 'estado': 'completada'},
                make_user(),
            )

        repo.create_request.assert_not_called()

    def test_creation_rejects_decommissioned_equipment(self):
        service, repo = self._service(
            equipment=make_equipment(status='dado_de_baja')
        )

        with self.assertRaises(ValueError):
            service.create_request(
                {'descripcion': 'Falla', 'equipo_id': 1},
                make_user(),
            )

        repo.create_request.assert_not_called()

    def test_creation_rejects_unavailable_or_mismatched_schedule(self):
        cases = [
            make_schedule(available=False),
            make_schedule(laboratory='Lab 202'),
            make_schedule(start=time(10, 0), end=time(8, 0)),
        ]
        for schedule in cases:
            with self.subTest(schedule=schedule):
                service, repo = self._service(schedule=schedule)
                with self.assertRaises(ValueError):
                    service.create_request(
                        {
                            'descripcion': 'Falla',
                            'equipo_id': 1,
                            'horario_id': 1,
                        },
                        make_user(),
                    )
                repo.create_request.assert_not_called()


if __name__ == '__main__':
    unittest.main(verbosity=2)
