import unittest
from datetime import timedelta

from tests.admin_conf_test import NOW, make_equipment, make_admin_service


class TestActiveEquipmentDashboard(unittest.TestCase):

    def test_returns_only_operative_equipment(self):
        equipos = [
            make_equipment(1, 'PC Sala 1',  estado='operativo'),
            make_equipment(2, 'Impresora',  estado='operativo'),
        ]
        svc, repo, _ = make_admin_service(active=equipos)
        result = svc.get_active_equipment()
        self.assertEqual(len(result), 2)
        repo.get_active_equipment.assert_called_once()

    def test_response_includes_name_location_and_status(self):
        equipos = [make_equipment(1, 'Router', ubicacion='Lab Redes', estado='operativo')]
        svc, _, _ = make_admin_service(active=equipos)
        item = svc.get_active_equipment()[0]
        self.assertEqual(item['nombre'],    'Router')
        self.assertEqual(item['ubicacion'], 'Lab Redes')
        self.assertEqual(item['estado'],    'operativo')

    def test_returns_empty_list_when_no_operative_equipment(self):
        svc, _, _ = make_admin_service(active=[])
        self.assertEqual(svc.get_active_equipment(), [])


class TestMaintenanceEquipmentDashboard(unittest.TestCase):

    def test_calls_correct_repository_method(self):
        svc, repo, _ = make_admin_service(maintenance=[])
        svc.get_maintenance_equipment()
        repo.get_maintenance_equipment.assert_called_once()

    def test_does_not_reuse_active_equipment_method(self):
        svc, repo, _ = make_admin_service(maintenance=[])
        svc.get_maintenance_equipment()
        repo.get_active_equipment.assert_not_called()

    def test_response_includes_name_location_and_status(self):
        equipos = [make_equipment(5, 'CNC', ubicacion='Taller', estado='en_mantenimiento')]
        svc, _, _ = make_admin_service(maintenance=equipos)
        item = svc.get_maintenance_equipment()[0]
        self.assertEqual(item['nombre'],    'CNC')
        self.assertEqual(item['ubicacion'], 'Taller')
        self.assertEqual(item['estado'],    'en_mantenimiento')

    def test_returns_empty_list_when_no_equipment_in_maintenance(self):
        svc, _, _ = make_admin_service(maintenance=[])
        self.assertEqual(svc.get_maintenance_equipment(), [])


class TestDecommissionedEquipmentDashboard(unittest.TestCase):

    def test_calls_correct_repository_method(self):
        svc, repo, _ = make_admin_service(decommissioned=[])
        svc.get_decommissioned_equipment()
        repo.get_decommissioned_equipment.assert_called_once()

    def test_response_includes_inactivity_reason(self):
        equipos = [make_equipment(
            7, 'Servidor viejo', estado='dado_de_baja',
            motivo_baja='Obsolescencia tecnológica',
            fecha_baja=NOW - timedelta(days=200),
        )]
        svc, _, _ = make_admin_service(decommissioned=equipos)
        item = svc.get_decommissioned_equipment()[0]
        self.assertIn('motivo_baja', item)
        self.assertEqual(item['motivo_baja'], 'Obsolescencia tecnológica')

    def test_response_includes_name_location_and_status(self):
        equipos = [make_equipment(
            7, 'Servidor viejo', ubicacion='CPD', estado='dado_de_baja',
            motivo_baja='Fallo total', fecha_baja=NOW - timedelta(days=100),
        )]
        svc, _, _ = make_admin_service(decommissioned=equipos)
        item = svc.get_decommissioned_equipment()[0]
        self.assertEqual(item['nombre'],    'Servidor viejo')
        self.assertEqual(item['ubicacion'], 'CPD')
        self.assertEqual(item['estado'],    'dado_de_baja')

    def test_decommission_date_is_converted_to_isoformat(self):
        fecha = NOW - timedelta(days=90)
        equipos = [make_equipment(
            8, 'Equipo Z', estado='dado_de_baja',
            motivo_baja='Sin repuestos', fecha_baja=fecha,
        )]
        svc, _, _ = make_admin_service(decommissioned=equipos)
        item = svc.get_decommissioned_equipment()[0]
        self.assertEqual(item['fecha_baja'], fecha.isoformat())

    def test_null_decommission_date_returns_none(self):
        equipos = [make_equipment(
            9, 'Equipo sin fecha', estado='dado_de_baja',
            motivo_baja='Motivo', fecha_baja=None,
        )]
        svc, _, _ = make_admin_service(decommissioned=equipos)
        self.assertIsNone(svc.get_decommissioned_equipment()[0]['fecha_baja'])

    def test_returns_empty_list_when_no_decommissioned_equipment(self):
        svc, _, _ = make_admin_service(decommissioned=[])
        self.assertEqual(svc.get_decommissioned_equipment(), [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
