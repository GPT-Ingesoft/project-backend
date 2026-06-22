from datetime import time, timedelta
from io import StringIO

from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from information_app.models import (
    Asignacion,
    Equipo,
    HorarioAtencion,
    MantenimientoPreventivo,
    Notificacion,
    Solicitud,
    Tecnico,
    Usuario,
)
from information_app.services.auth_services import AuthServices
from information_app.services.preventive_services import PreventiveMaintenanceServices


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='syslab@test.local',
)
class MaintenanceRequirementsIntegrationTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.teacher = Usuario.objects.create(
            nombre='Docente RF',
            correo='docente.rf@unal.edu.co',
            rol='docente',
        )
        cls.admin = Usuario.objects.create(
            nombre='Laboratorista RF',
            correo='lab.rf@unal.edu.co',
            rol='laboratorista',
        )
        cls.tech_user_1 = Usuario.objects.create(
            nombre='Técnico Uno',
            correo='tecnico1.rf@unal.edu.co',
            rol='tecnico',
        )
        cls.tech_user_2 = Usuario.objects.create(
            nombre='Técnico Dos',
            correo='tecnico2.rf@unal.edu.co',
            rol='tecnico',
        )
        cls.tech_1 = Tecnico.objects.create(
            usuario=cls.tech_user_1,
            especialidad='Electrónica',
            contacto='100',
        )
        cls.tech_2 = Tecnico.objects.create(
            usuario=cls.tech_user_2,
            especialidad='Redes',
            contacto='200',
        )
        cls.equipment = Equipo.objects.create(
            nombre='Osciloscopio RF',
            codigo_inventario='RF-INV-001',
            modelo='RF-M1',
            marca='RF',
            numero_serie='RF-SER-001',
            ubicacion='Lab RF',
        )
        cls.schedule = HorarioAtencion.objects.create(
            laboratorio='Lab RF',
            dia='lunes',
            hora_inicio=time(8, 0),
            hora_fin=time(10, 0),
        )

    def authenticated_client(self, user):
        client = APIClient()
        token = AuthServices.generate_access_token(user)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        return client

    def test_create_request_sets_date_status_and_schedule(self):
        response = self.authenticated_client(self.teacher).post(
            '/api/solicitudes/',
            {
                'descripcion': 'El equipo no enciende',
                'equipo_id': self.equipment.id,
                'horario_id': self.schedule.id,
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        request = Solicitud.objects.get()
        self.assertEqual(request.estado, 'pendiente')
        self.assertIsNotNone(request.fecha_creacion)
        self.assertEqual(request.horario_agendado, self.schedule)
        self.assertEqual(response.data['solicitud']['estado'], 'pendiente')
        schedules = self.authenticated_client(self.teacher).get(
            '/api/solicitudes/horario/?laboratorio=Lab%20RF'
        )
        self.assertEqual(schedules.status_code, 200)
        self.assertEqual(schedules.data['horarios'][0]['id'], self.schedule.id)

    def test_available_technicians_and_multiple_assignment(self):
        target = Solicitud.objects.create(
            descripcion='Solicitud objetivo',
            usuario=self.teacher,
            equipo=self.equipment,
            horario_agendado=self.schedule,
        )
        other = Solicitud.objects.create(
            descripcion='Solicitud ocupada',
            usuario=self.teacher,
            equipo=self.equipment,
            horario_agendado=self.schedule,
        )
        Asignacion.objects.create(solicitud=other, tecnico=self.tech_1)
        client = self.authenticated_client(self.admin)

        available = client.get(
            f'/api/solicitudes/{target.id}/tecnicos-disponibles/'
        )
        self.assertEqual(available.status_code, 200)
        self.assertEqual(
            [item['id'] for item in available.data['tecnicos']],
            [self.tech_user_2.id],
        )
        denied = self.authenticated_client(self.teacher).get(
            f'/api/solicitudes/{target.id}/tecnicos-disponibles/'
        )
        self.assertEqual(denied.status_code, 403)

        assigned = client.patch(
            f'/api/solicitudes/{target.id}/tecnicos/',
            {'technician_ids': [self.tech_user_2.id]},
            format='json',
        )
        self.assertEqual(assigned.status_code, 200)
        self.assertTrue(
            Asignacion.objects.filter(
                solicitud=target,
                tecnico=self.tech_2,
                activa=True,
            ).exists()
        )

    def test_status_change_persists_notification_and_sends_email(self):
        request = Solicitud.objects.create(
            descripcion='Cambio de estado',
            usuario=self.teacher,
            equipo=self.equipment,
        )
        Asignacion.objects.create(solicitud=request, tecnico=self.tech_1)
        client = self.authenticated_client(self.admin)

        with self.captureOnCommitCallbacks(execute=True):
            response = client.patch(
                f'/api/solicitudes/{request.id}/estado/',
                {'estado': 'en_proceso', 'motivo': 'Diagnóstico iniciado'},
                format='json',
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Notificacion.objects.filter(tipo='cambio_estado').count(), 1)
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            {message.to[0] for message in mail.outbox},
            {self.teacher.correo, self.tech_user_1.correo},
        )
        with self.captureOnCommitCallbacks(execute=True):
            rejected = client.patch(
                f'/api/solicitudes/{request.id}/estado/',
                {'estado': 'en_proceso', 'motivo': 'Sin cambio'},
                format='json',
            )
        self.assertEqual(rejected.status_code, 400)
        self.assertEqual(Notificacion.objects.filter(tipo='cambio_estado').count(), 1)
        self.assertEqual(len(mail.outbox), 2)

    def test_preventive_notification_is_idempotent(self):
        maintenance = MantenimientoPreventivo.objects.create(
            equipo=self.equipment,
            descripcion='Revisión semestral',
            fecha_programada=timezone.now() + timedelta(hours=2),
            anticipacion_horas=4,
        )
        maintenance.tecnicos.add(self.tech_1)

        output = StringIO()
        with self.captureOnCommitCallbacks(execute=True):
            call_command('notificar_mantenimientos_preventivos', stdout=output)
        with self.captureOnCommitCallbacks(execute=True):
            call_command('notificar_mantenimientos_preventivos', stdout=output)

        maintenance.refresh_from_db()
        self.assertIsNotNone(maintenance.notificado_en)
        self.assertIn('Notificados: 1', output.getvalue())
        self.assertIn('Notificados: 0', output.getvalue())
        self.assertEqual(
            Notificacion.objects.filter(tipo='mantenimiento_preventivo').count(),
            1,
        )
        self.assertEqual(len(mail.outbox), 2)

    def test_preventive_notification_excludes_not_due_and_cancelled_items(self):
        future = MantenimientoPreventivo.objects.create(
            equipo=self.equipment,
            descripcion='Revisión futura',
            fecha_programada=timezone.now() + timedelta(days=5),
            anticipacion_horas=24,
        )
        cancelled = MantenimientoPreventivo.objects.create(
            equipo=self.equipment,
            descripcion='Revisión cancelada',
            fecha_programada=timezone.now() + timedelta(hours=1),
            anticipacion_horas=24,
            estado='cancelado',
        )

        with self.captureOnCommitCallbacks(execute=True):
            result = PreventiveMaintenanceServices().notify_upcoming()

        self.assertEqual(result['notified_ids'], [])
        future.refresh_from_db()
        cancelled.refresh_from_db()
        self.assertIsNone(future.notificado_en)
        self.assertIsNone(cancelled.notificado_en)
        self.assertEqual(len(mail.outbox), 0)
