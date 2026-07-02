from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from information_app.models import (
    ConfiguracionSistema,
    Equipo,
    Notificacion,
    Solicitud,
    Usuario,
)
from information_app.services.auth_services import AuthServices


class AdminIntegrationSetup(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.admin = Usuario.objects.create(
            nombre='Laboratorista Admin',
            correo='lab.admin@unal.edu.co',
            rol='laboratorista',
        )
        cls.teacher = Usuario.objects.create(
            nombre='Docente Admin',
            correo='docente.admin@unal.edu.co',
            rol='docente',
        )
        cls.equipment = Equipo.objects.create(
            nombre='PC Sala Admin',
            codigo_inventario='ADM-ACT-001',
            modelo='Dell OptiPlex',
            marca='Dell',
            numero_serie='ADM-SER-001',
            ubicacion='Laboratorio Admin',
            estado='operativo',
        )

    def _client(self, user):
        client = APIClient()
        token = AuthServices.generate_access_token(user)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        return client


class TestRequestDeletionProtection(AdminIntegrationSetup):

    def test_deleting_user_with_requests_raises_protected_error(self):
        temp_user = Usuario.objects.create(
            nombre='Usuario Temporal',
            correo='temp.protection@unal.edu.co',
            rol='docente',
        )
        Solicitud.objects.create(
            descripcion='Solicitud protegida',
            usuario=temp_user,
            equipo=self.equipment,
        )
        with self.assertRaises(Exception) as cm:
            temp_user.delete()
        self.assertIn('Protected', type(cm.exception).__name__)

    def test_deleting_equipment_with_requests_raises_protected_error(self):
        temp_equipment = Equipo.objects.create(
            nombre='Equipo Temporal',
            codigo_inventario='ADM-TMP-001',
            modelo='T1',
            marca='X',
            numero_serie='ADM-TMP-SER-001',
            ubicacion='Lab X',
        )
        Solicitud.objects.create(
            descripcion='Solicitud sobre equipo',
            usuario=self.teacher,
            equipo=temp_equipment,
        )
        with self.assertRaises(Exception) as cm:
            temp_equipment.delete()
        self.assertIn('Protected', type(cm.exception).__name__)


class TestNotificationHistoryEndpoint(AdminIntegrationSetup):

    def test_notifications_are_returned_newest_first(self):
        ahora = timezone.now()
        n1 = Notificacion.objects.create(mensaje='Primera', tipo='otro')
        n2 = Notificacion.objects.create(mensaje='Segunda', tipo='otro')
        n3 = Notificacion.objects.create(mensaje='Tercera', tipo='otro')
        Notificacion.objects.filter(pk=n1.pk).update(fecha_envio=ahora - timedelta(days=2))
        Notificacion.objects.filter(pk=n2.pk).update(fecha_envio=ahora - timedelta(days=1))
        Notificacion.objects.filter(pk=n3.pk).update(fecha_envio=ahora)

        response = self._client(self.admin).get('/api/admin/notificaciones/')

        self.assertEqual(response.status_code, 200)
        ids = [n['id'] for n in response.data['notificaciones']]
        self.assertLess(ids.index(n3.id), ids.index(n2.id))
        self.assertLess(ids.index(n2.id), ids.index(n1.id))

    def test_response_includes_required_fields(self):
        Notificacion.objects.create(mensaje='Test campos', tipo='cambio_estado')
        response = self._client(self.admin).get('/api/admin/notificaciones/')
        self.assertEqual(response.status_code, 200)
        item = response.data['notificaciones'][0]
        for field in ('id', 'tipo', 'mensaje', 'fecha_envio', 'destinatarios'):
            self.assertIn(field, item)


class TestOutOfServiceThresholdEndpoint(AdminIntegrationSetup):

    def test_patch_saves_threshold_to_database(self):
        response = self._client(self.admin).patch(
            '/api/admin/reportes/fuera-de-servicio/umbral/',
            {'umbral_dias': 45},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['umbral_dias'], 45)
        config = ConfiguracionSistema.objects.get(
            clave=ConfiguracionSistema.CLAVE_UMBRAL_FUERA_DE_SERVICIO
        )
        self.assertEqual(int(config.valor), 45)

    def test_report_uses_stored_threshold_when_no_parameter_given(self):
        ConfiguracionSistema.objects.update_or_create(
            clave=ConfiguracionSistema.CLAVE_UMBRAL_FUERA_DE_SERVICIO,
            defaults={'valor': '50'},
        )
        response = self._client(self.admin).get('/api/admin/reportes/fuera-de-servicio/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['umbral_dias'], 50)

    def test_inline_parameter_overrides_stored_threshold(self):
        ConfiguracionSistema.objects.update_or_create(
            clave=ConfiguracionSistema.CLAVE_UMBRAL_FUERA_DE_SERVICIO,
            defaults={'valor': '50'},
        )
        response = self._client(self.admin).get(
            '/api/admin/reportes/fuera-de-servicio/?umbral_dias=10'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['umbral_dias'], 10)

    def test_invalid_threshold_returns_400(self):
        response = self._client(self.admin).get(
            '/api/admin/reportes/fuera-de-servicio/?umbral_dias=abc'
        )
        self.assertEqual(response.status_code, 400)


if __name__ == '__main__':
    import unittest
    unittest.main(verbosity=2)
