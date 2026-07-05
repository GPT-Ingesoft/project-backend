from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from information_app.models import Equipo, Usuario
from information_app.services.auth_services import AuthServices


class EquipmentDashboardIntegrationSetup(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = Usuario.objects.create(
            nombre='Docente Panel',
            correo='docente.panel@unal.edu.co',
            rol='docente',
        )
        cls.eq_operativo = Equipo.objects.create(
            nombre='PC Sala 1',
            codigo_inventario='PNL-ACT-001',
            modelo='Dell OptiPlex',
            marca='Dell',
            numero_serie='PNL-SER-001',
            ubicacion='Laboratorio A',
            estado='operativo',
        )
        cls.eq_mantenimiento = Equipo.objects.create(
            nombre='Impresora Láser',
            codigo_inventario='PNL-MNT-001',
            modelo='LaserJet Pro',
            marca='HP',
            numero_serie='PNL-SER-002',
            ubicacion='Laboratorio B',
            estado='en_mantenimiento',
        )
        cls.eq_baja = Equipo.objects.create(
            nombre='Proyector antiguo',
            codigo_inventario='PNL-BJA-001',
            modelo='PJ-500',
            marca='Epson',
            numero_serie='PNL-SER-003',
            ubicacion='Aula 301',
            estado='dado_de_baja',
            motivo_baja='Obsolescencia tecnológica',
            fecha_baja=timezone.now() - timedelta(days=365),
        )

    def _client(self):
        client = APIClient()
        token = AuthServices.generate_access_token(self.user)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        return client


class TestActiveEquipmentPanel(EquipmentDashboardIntegrationSetup):

    def test_endpoint_returns_200(self):
        response = self._client().get('/api/panel/equipos-activos/')
        self.assertEqual(response.status_code, 200)

    def test_only_returns_operative_equipment(self):
        ids = [e['id'] for e in self._client().get('/api/panel/equipos-activos/').data['equipos']]
        self.assertIn(self.eq_operativo.id, ids)
        self.assertNotIn(self.eq_mantenimiento.id, ids)
        self.assertNotIn(self.eq_baja.id, ids)

    def test_response_includes_name_location_and_status(self):
        equipos = self._client().get('/api/panel/equipos-activos/').data['equipos']
        item = next(e for e in equipos if e['id'] == self.eq_operativo.id)
        self.assertEqual(item['nombre'],    self.eq_operativo.nombre)
        self.assertEqual(item['ubicacion'], self.eq_operativo.ubicacion)
        self.assertEqual(item['estado'],    'operativo')


class TestMaintenanceEquipmentPanel(EquipmentDashboardIntegrationSetup):

    def test_endpoint_returns_200(self):
        response = self._client().get('/api/panel/equipos-mantenimiento/')
        self.assertEqual(response.status_code, 200)

    def test_only_returns_equipment_in_maintenance(self):
        ids = [e['id'] for e in self._client().get('/api/panel/equipos-mantenimiento/').data['equipos']]
        self.assertIn(self.eq_mantenimiento.id, ids)
        self.assertNotIn(self.eq_operativo.id, ids)
        self.assertNotIn(self.eq_baja.id, ids)

    def test_active_and_maintenance_panels_are_independent(self):
        ids_activos = {e['id'] for e in self._client().get('/api/panel/equipos-activos/').data['equipos']}
        ids_mnt     = {e['id'] for e in self._client().get('/api/panel/equipos-mantenimiento/').data['equipos']}
        self.assertTrue(
            ids_activos.isdisjoint(ids_mnt),
            'Active and maintenance panels must not overlap',
        )

    def test_response_includes_name_location_and_status(self):
        equipos = self._client().get('/api/panel/equipos-mantenimiento/').data['equipos']
        item = next(e for e in equipos if e['id'] == self.eq_mantenimiento.id)
        self.assertEqual(item['nombre'],    self.eq_mantenimiento.nombre)
        self.assertEqual(item['ubicacion'], self.eq_mantenimiento.ubicacion)
        self.assertEqual(item['estado'],    'en_mantenimiento')


class TestDecommissionedEquipmentPanel(EquipmentDashboardIntegrationSetup):

    def test_endpoint_returns_200(self):
        response = self._client().get('/api/panel/equipos-dados-de-baja/')
        self.assertEqual(response.status_code, 200)

    def test_only_returns_decommissioned_equipment(self):
        ids = [e['id'] for e in self._client().get('/api/panel/equipos-dados-de-baja/').data['equipos']]
        self.assertIn(self.eq_baja.id, ids)
        self.assertNotIn(self.eq_operativo.id, ids)
        self.assertNotIn(self.eq_mantenimiento.id, ids)

    def test_response_includes_inactivity_reason(self):
        equipos = self._client().get('/api/panel/equipos-dados-de-baja/').data['equipos']
        item = next(e for e in equipos if e['id'] == self.eq_baja.id)
        self.assertIn('motivo_baja', item)
        self.assertEqual(item['motivo_baja'], 'Obsolescencia tecnológica')

    def test_response_includes_name_location_status_and_date(self):
        equipos = self._client().get('/api/panel/equipos-dados-de-baja/').data['equipos']
        item = next(e for e in equipos if e['id'] == self.eq_baja.id)
        for field in ('nombre', 'ubicacion', 'estado', 'motivo_baja', 'fecha_baja'):
            self.assertIn(field, item)
        self.assertEqual(item['estado'], 'dado_de_baja')


if __name__ == '__main__':
    import unittest
    unittest.main(verbosity=2)
